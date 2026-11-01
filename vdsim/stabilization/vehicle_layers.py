"""Vehicle dynamics and actuator layers (contracts.md section 1).

vehicle_dynamics/split_range    Werling 5.1.2.2, Fig. 5.3: desired longitudinal force F_ld (or m a_d) plus
    compensation of the driving resistances F_W(v) (vdsim aero_drag + rolling_resistance) plus an integrator on
    the acceleration error (head wind, road grade) with anti-windup at actuator saturation; split into drive
    (powertrain limit, reverse gear for varsigma = -1) and brakes; gamma from the drive layout or 0.75 when
    braking; torque distribution to the wheels; optional ESP/ABS/TCS/TV from vdsim.controllers.
actuator/steering_powertrain   integrates delta_dot (or takes delta), steering angle limit, vdsim
    SteeringActuator (latency chain, characteristic error, rate limit), optional dead time / PT1 for drive and
    brake torques.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from ..actuators import SteeringActuator
from ..core.parameters import param
from ..core.registry import create
from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import ActuatorBase, VehicleDynamicsBase
from ..framework.plugins import component
from ..framework.types import ActuatorCommand
from ..powertrain import BrakeSystem, Powertrain
from ..simulation.vehicle_state import ControlInput, VehicleState
from ..vehicle_models.common import aero_drag, rolling_resistance
from .common import drive_share, vehicle_config


@dataclass
class SplitRangeParams:
    k_i: float = param(0.5, "1/s", "Integratorverstärkung k_I (Beschleunigungsfehler)", min=0.0)
    integrator_limit: float = param(0.3, "-", "Integratorgrenze (Anteil von m g)", min=0.0, max=1.0)
    compensate_resistance: bool = param(True, "", "Fahrwiderstand F_W(v) kompensieren")
    gamma_brake: float = param(0.75, "-", "Bremskraftverteilung vorne gamma", min=0.0, max=1.0)
    max_decel: float = param(10.0, "m/s²", "max. Verzögerung", min=0.0)
    regen: bool = param(False, "", "Rekuperation über den E-Antrieb (nur EV)")
    systems: list = param([], "", "Fahrdynamiksysteme (esp, abs, tcs, torque_vectoring)")
    integrator_min_speed: float = param(0.3, "m/s", "Integrator nur oberhalb |v| bzw. bei Sollbeschleunigung", min=0)


@component
class SplitRangeDynamics(VehicleDynamicsBase):
    NAME, VERSION = "split_range", "1.0.0"
    LABEL = "Split-Range-Längskraftumsetzung (Werling 5.1.2.2)"
    PARAMS = SplitRangeParams
    DOC = ComponentDoc(
        summary="Setzt die Solllängskraft bzw. Sollbeschleunigung über Antrieb oder Bremse in Radmomente um.",
        purpose="Die Entwurfsmodelle der Trackingregler vernachlässigen Roll- und Luftwiderstand; die Ebene "
                "kompensiert F_W(v) und regelt Restfehler (Gegenwind, Steigung) mit einem Integrator aus.",
        theory="$u=F_{ld}+F_W(v)+k_I\\int m(a_{exp}-a)\\,dt$; $u\\varsigma\\geq0$: Antrieb (Rückwärtsgang bei "
               "$\\varsigma=-1$), sonst Bremse. Anti-Windup: Integration angehalten, wenn das Stellglied gesättigt "
               "ist und der Fehler weiter in die Sättigung treibt (Werling Abb. 5.3).",
        assumptions=["Antriebsstrangdynamik vernachlässigt (Momente wirken unverzögert, Werling 5.1.2.2)",
                     "Bremskraftverteilung fest gamma (Standard 0.75)"],
        limitations=["Kein Motorkennfeld F_M^-1 / Getriebe-Schleppmoment (Momentenschnittstelle)"],
        references=["werling2011", "astrom2006"],
        equations=["werling2011:5.1.2.2", "werling2011:Abb. 5.3"],
        validation=["tests/stabilization/test_stabilization_layers.py"],
        concepts=["split_range", "anti_windup"],
        expert="Stationär (konstante Störung F_s) gilt mit aktivem Integrator $a\\to a_{exp}$, da der Integrator "
               "die Störung vollständig übernimmt; bei Sättigung bleibt sein Zustand begrenzt, sodass nach dem "
               "Verlassen der Sättigung kein Überschwingen entsteht.")

    def reset(self, context):
        super().reset(context)
        self.cfg = cfg = vehicle_config(context)
        self.vp = cfg.vehicle
        self.powertrain = Powertrain(cfg.powertrain, cfg.vehicle)
        self.brakes = BrakeSystem(cfg.brakes, cfg.vehicle)
        self.gamma_drive = drive_share(cfg)
        self.integrator = 0.0
        self.t_prev = None
        self.systems = [create("chassis_system", name, cfg) for name in self.params.systems]
        for s in self.systems:
            s.reset()

    @trace("werling2011", section="5.1.2.2", concept="split_range", note="Abb. 5.3")
    def step(self, t, inputs):
        cmd, ego = inputs.get("command"), inputs.get("ego")
        p, vp = self.params, self.vp
        if cmd is None or ego is None:
            return {"demand": ActuatorCommand(t=t, info={"steer_mode": "rate"})}
        dt = 0.0 if self.t_prev is None else max(t - self.t_prev, 0.0)
        self.t_prev = t
        m = vp.mass
        sg = 1 if cmd.direction >= 0 else -1
        if cmd.force is not None:
            F_ld = float(cmd.force)
            a_exp = float(cmd.info.get("a_expected", F_ld / m))
        else:
            a_exp = float(cmd.accel or 0.0) * (1.0 if cmd.accel is not None else 0.0)
            F_ld = m * a_exp
        v = ego.vx
        F_W = aero_drag(vp, v, 0.0) + rolling_resistance(vp, v) if p.compensate_resistance else 0.0
        u = F_ld + F_W + self.integrator
        u = max(u, -p.max_decel * m) if sg > 0 else min(u, p.max_decel * m)
        # split range: drive (signed with the gear) or brake
        speed = abs(v)
        drive_max = self.powertrain.max_drive_force(speed)
        drive = brake = 0.0
        sat = 0
        if sg * u >= 0.0:
            drive = sg * min(abs(u), drive_max)
            sat = sg if abs(u) > drive_max else 0
        else:
            brake = abs(u)
        gamma = self.gamma_drive if drive != 0.0 or brake == 0.0 else p.gamma_brake
        R = vp.wheel_radius
        drive_t = drive * R * self.powertrain.axle_shares
        if p.regen and brake > 0 and self.powertrain.motor is not None and speed > 1.0:
            regen = min(brake, self.powertrain.max_regen_force(speed))
            brake -= regen
            drive_t = -sg * regen * R * self.powertrain.axle_shares
        brake_t = self.brakes.axle_torques(p.gamma_brake * brake, (1 - p.gamma_brake) * brake)
        if brake > 0 and (brake_t[0] * 2 + brake_t[2] * 2) / R < brake * 0.999:
            sat = -sg
        # integrator on the acceleration error with anti-windup (conditional integration)
        a_meas = ego.ax + ego.r * ego.vy
        err = m * (a_exp - a_meas)
        active = speed > p.integrator_min_speed or abs(a_exp) > 0.05
        if dt > 0 and p.k_i > 0 and active and not (sat != 0 and np.sign(err) == np.sign(sat)):
            lim = p.integrator_limit * m * 9.81
            self.integrator = float(np.clip(self.integrator + p.k_i * err * dt, -lim, lim))
        steer_mode = "rate" if cmd.steer_angle is None else "angle"
        demand = ActuatorCommand(t=t, steer_angle=float(cmd.steer_angle if cmd.steer_angle is not None else ego.delta),
                                 steer_rate=float(cmd.steer_rate or 0.0), drive_torque=drive_t, brake_torque=brake_t,
                                 info={"steer_mode": steer_mode, "F_ld": F_ld, "F_W": F_W, "integrator": self.integrator,
                                       "u": u, "gamma": gamma, "saturated": sat, "direction": sg})
        if self.systems:
            demand = self._chassis_systems(t, ego, demand, dt)
        self.signals = {"F_ld": F_ld, "F_W": F_W, "integrator": self.integrator, "saturated": float(sat)}
        return {"demand": demand}

    def _chassis_systems(self, t, ego, demand, dt):
        vs = VehicleState(t=t, x=ego.x, y=ego.y, psi=ego.psi, vx=ego.vx, vy=ego.vy, r=ego.r, ax=ego.ax, ay=ego.ay,
                          delta_f=ego.delta)
        u = ControlInput(steer_front=demand.steer_angle, drive_torque=demand.drive_torque.copy(),
                         brake_torque=demand.brake_torque.copy())
        for s in self.systems:
            u = s.apply(t, vs, u, dt) or u
        demand.drive_torque, demand.brake_torque = u.drive_torque, u.brake_torque
        return demand


@dataclass
class ActuatorParams:
    steering: dict = field(default_factory=dict, metadata={"label": "Lenkaktor (SteeringActuatorParameters)",
                                                           "unit": ""})
    max_steer_angle: float = param(-1.0, "rad", "Lenkwinkelgrenze (<0: aus Fahrzeug)")
    drive_dead_time: float = param(0.0, "s", "Totzeit Antrieb", min=0.0)
    drive_tau: float = param(0.0, "s", "PT1 Antrieb", min=0.0)
    brake_dead_time: float = param(0.0, "s", "Totzeit Bremse", min=0.0)
    brake_tau: float = param(0.0, "s", "PT1 Bremse", min=0.0)


class _VectorDelay:
    # dead time + PT1 on a 4-vector (wheel torques)
    def __init__(self, dead_time, tau, dt):
        self.buffer = deque([np.zeros(4)] * int(round(dead_time / dt))) if dt > 0 else deque()
        self.alpha = dt / (tau + dt) if dt > 0 else 1.0
        self.y = np.zeros(4)

    def step(self, u):
        u = np.asarray(u, dtype=float)
        if self.buffer:
            self.buffer.append(u.copy())
            u = self.buffer.popleft()
        self.y = self.y + self.alpha * (u - self.y)
        return self.y.copy()


@component
class SteeringPowertrainActuator(ActuatorBase):
    NAME, VERSION = "steering_powertrain", "1.0.0"
    LABEL = "Lenkaktor und Antrieb/Bremse"
    PARAMS = ActuatorParams
    DOC = ComponentDoc(
        summary="Integriert die Lenkrate bzw. übernimmt den Lenkwinkel, bildet Lenkaktor (Latenz, Kennlinie, "
                "Ratenbegrenzung) sowie verzögerte Antriebs- und Bremsmomente nach.",
        purpose="Verbindet die Stellgrößen der Trajektorienregelung mit der Strecke; die Latenzkette der "
                "ursprünglichen Spurwechsel-Latenzstudie bleibt in der Wirkkette nutzbar.",
        assumptions=["Konstanter Schritt dt (Komponentenperiode bzw. Executor-Schritt)"],
        limitations=["Kennlinienfehler wirkt auf die Krümmung tan(delta)/l (wie vdsim.actuators)"],
        references=["werling2011"],
        equations=["werling2011:5.1.2.1"],
        validation=["tests/stabilization/test_stabilization_layers.py"],
        concepts=["steering_actuator"],
        expert="Die Integration von $\\dot\\delta$ erfolgt mit Begrenzung (Anti-Windup), damit der Integrator "
               "an der Lenkanschlaggrenze nicht wegläuft.")

    def reset(self, context):
        super().reset(context)
        cfg = vehicle_config(context)
        self.vp = cfg.vehicle
        p = self.params
        self.dt = self.PERIOD or (getattr(context, "dt", 0.01) if context is not None else 0.01)
        self.steering = SteeringActuator(dict(p.steering), cfg.vehicle.wheelbase, self.dt)
        self.limit = p.max_steer_angle if p.max_steer_angle > 0 else cfg.vehicle.max_steer_angle
        self.drive = _VectorDelay(p.drive_dead_time, p.drive_tau, self.dt)
        self.brake = _VectorDelay(p.brake_dead_time, p.brake_tau, self.dt)
        self.delta_int = None
        self.t_prev = None

    def step(self, t, inputs):
        demand, ego = inputs.get("demand"), inputs.get("ego")
        if demand is None:
            return {"control": ControlInput()}
        dt = self.dt if self.t_prev is None else max(t - self.t_prev, 0.0)
        self.t_prev = t
        if self.delta_int is None:
            self.delta_int = float(ego.delta) if ego is not None else 0.0
            self.steering.delta = self.delta_int
            self.steering.chain.actuator_lag.y = math.tan(self.delta_int) / self.vp.wheelbase
        if demand.info.get("steer_mode", "angle") == "rate":
            self.delta_int += demand.steer_rate * dt
        else:
            self.delta_int = demand.steer_angle
        self.delta_int = min(max(self.delta_int, -self.limit), self.limit)
        kappa_meas = ego.r / max(abs(ego.vx), 1.0) if ego is not None else 0.0
        delta = self.steering.step(self.delta_int, kappa_meas)
        delta = min(max(delta, -self.limit), self.limit)
        u = ControlInput(steer_front=delta, steer_rear=demand.steer_rear, drive_torque=self.drive.step(demand.drive_torque),
                         brake_torque=np.maximum(self.brake.step(demand.brake_torque), 0.0))
        self.signals = {"delta_cmd": self.delta_int, "delta_applied": delta}
        return {"control": u}
