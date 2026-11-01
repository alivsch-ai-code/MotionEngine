"""Simulator: closes the loop reference -> controllers -> actuators -> chassis systems -> vehicle model.

One control step (dt_control):
    1. lateral controller      VehicleState + trajectory -> steering request
    2. longitudinal controller -> acceleration request -> powertrain/brakes -> wheel torques
    3. steering actuator       characteristic error, latency, feedback correction
    4. chassis systems         ABS, TCS, ESP, rear steering, torque vectoring, active suspension
    5. vehicle model           integrated with the solver in dt_model substeps
    6. logging                 all signals into a SimulationResult
"""

import time as _time

import numpy as np

from ..actuators import SteeringActuator
from ..controllers import enabled_systems
from ..core.logging_setup import get_logger
from ..core.registry import create
from ..powertrain import LongitudinalActuation
from .environment import Environment
from .results import SimulationResult
from .solver import create_solver
from .vehicle_state import ControlInput

log = get_logger("simulator")


class Simulator:
    def __init__(self, config, model, trajectory, lateral, longitudinal, environment=None, systems=(),
                 steering=None, dt_control=0.01, dt_model=None, solver="rk4", duration=None,
                 initial_speed=None, name="", metadata=None):
        self.config, self.model, self.trajectory = config, model, trajectory
        self.lateral, self.longitudinal = lateral, longitudinal
        self.env = environment or Environment()
        self.systems = list(systems)
        self.dt = dt_control
        self.dt_model = dt_model or getattr(model, "recommended_dt", dt_control)
        self.solver = create_solver(solver, self._substeps(self.dt_model))
        self.steering = SteeringActuator(steering or {}, config.vehicle.wheelbase, dt_control)
        self.actuation = LongitudinalActuation(config)
        self.duration = duration or self._auto_duration(initial_speed)
        self.initial_speed = initial_speed
        self.name = name
        self.metadata = metadata or {}
        self.reset()

    @classmethod
    def from_scenario(cls, scenario):
        config = scenario.build_config()
        trajectory = scenario.build_trajectory(config)
        model = create("vehicle_model", scenario.model, config)
        lateral_name = scenario.lateral_controller
        if trajectory.is_open_loop and lateral_name not in ("open_loop",):
            log.info("maneuver has a steering table, using open-loop steering")
            lateral_name = "open_loop"
        lateral = create("lateral_controller", lateral_name, config, **scenario.lateral_params)
        longitudinal = create("longitudinal_controller", scenario.longitudinal_controller, config,
                              **scenario.longitudinal_params)
        systems = [create("chassis_system", name, config) for name in enabled_systems(config)]
        initial_speed = scenario.initial_speed
        if initial_speed is None and "initial_speed" in trajectory.metadata:
            initial_speed = trajectory.metadata["initial_speed"]
        metadata = {"scenario": scenario.to_dict(), "vehicle": config.to_dict(), "trajectory": trajectory.to_dict(),
                    "model": scenario.model, "lateral_controller": lateral_name}
        return cls(config, model, trajectory, lateral, longitudinal, Environment.from_dict(scenario.environment),
                   systems, scenario.steering_actuator, scenario.dt_control, scenario.dt_model or None,
                   scenario.solver, scenario.duration or None, initial_speed, scenario.name, metadata)

    def _substeps(self, dt_model):
        return max(1, int(np.ceil(self.dt / dt_model - 1e-9)))

    def _auto_duration(self, initial_speed):
        traj = self.trajectory
        if "duration" in traj.metadata:
            return float(traj.metadata["duration"])
        if traj.metadata.get("maneuver") == "acceleration":
            return 25.0
        v_mean = max(float(np.mean(traj.v)), 1.0)
        return float(min(traj.length / v_mean * 1.2 + 5.0, 1200.0))

    # lifecycle
    def reset(self):
        traj = self.trajectory
        traj.reset_search()
        speed = self.initial_speed if self.initial_speed is not None else float(traj.v[0])
        psi0 = float(traj.psi[0])
        self.x = self.model.initial_state(float(traj.x[0]), float(traj.y[0]), psi0, speed)
        self.t = 0.0
        self._log_hint = 0
        self.u = ControlInput()
        for component in [self.lateral, self.longitudinal, *self.systems]:
            component.reset()
        self.actuation.reset()
        self.steering = SteeringActuator(self.steering.p, self.config.vehicle.wheelbase, self.dt)
        lead = self.env.lead_vehicle
        if lead is not None:
            lead.s = self.config.vehicle.length / 2 + lead.initial_gap
        _, self.outputs = self.model.derivatives(0.0, self.x, self.u, self.env, with_outputs=True)
        self.state = self._vehicle_state()
        self.result = SimulationResult(self.name, dict(self.metadata))
        self.finished = False
        self.stop_reason = ""
        self._log()

    def _vehicle_state(self):
        vs = self.model.vehicle_state(self.t, self.x, self.outputs)
        if "delta" not in self.outputs:
            vs.delta_f, vs.delta_r = self.u.steer_front, self.u.steer_rear
        return vs

    # one control step
    def step(self):
        if self.finished:
            return self.state
        t, vs, dt = self.t, self.state, self.dt
        steer_request = self.lateral.steer(t, vs, self.trajectory)
        ax_request = self.longitudinal.acceleration(t, vs, self.trajectory, self.env)

        u = ControlInput()
        u = self.actuation.actuate(ax_request, vs, u, dt, self.env)
        u.steer_front = self.steering.step(steer_request, vs.r / max(vs.vx, 1.0))
        vs.delta_f = u.steer_front
        for system in self.systems:
            u = system.apply(t, vs, u, dt)
        self.u = u

        model, env = self.model, self.env
        dt_model = self.dt_model
        if hasattr(model, "stable_dt"):
            dt_model = min(dt_model, model.stable_dt(self.x))
        self.x = self.solver.step(lambda tt, xx: model.derivatives(tt, xx, u, env), t, self.x, dt,
                                  self._substeps(dt_model))
        self.t = t + dt
        if self.env.lead_vehicle is not None:
            self.env.lead_vehicle.s += self.env.lead_vehicle.speed_at(self.t) * dt
        _, self.outputs = model.derivatives(self.t, self.x, u, env, with_outputs=True)
        self.state = self._vehicle_state()
        self._log(steer_request)
        self._check_stop()
        return self.state

    def _check_stop(self):
        vs, traj = self.state, self.trajectory
        if not np.all(np.isfinite(self.x)):
            self.finished, self.stop_reason = True, "numerisch instabil (NaN)"
            log.error("simulation diverged at t=%.3f s", self.t)
        elif self.t >= self.duration - 1e-9:
            self.finished, self.stop_reason = True, "Simulationsdauer erreicht"
        elif not traj.is_open_loop and self._s >= traj.length - 0.5:
            self.finished, self.stop_reason = True, "Ende der Trajektorie"
        elif traj.accel_table is not None and traj.accel_at(self.t) < 0 and vs.vx < 0.05:
            self.finished, self.stop_reason = True, "Fahrzeug steht"
        elif traj.metadata.get("target") and vs.vx >= traj.metadata["target"] - 0.05:
            self.finished, self.stop_reason = True, "Zielgeschwindigkeit erreicht"
        elif self.env.lead_vehicle is not None and                 self.env.lead_vehicle.s - self._s - self.config.vehicle.length / 2 <= 0:
            self.finished, self.stop_reason = True, "Kollision mit vorausfahrendem Fahrzeug"
        elif abs(vs.beta) > np.radians(60) or abs(vs.roll) > 0.35:
            self.finished, self.stop_reason = True, "Fahrzeug instabil (Schleudern/Überschlag)"

    def run(self, progress=None, max_wall_time=None):
        start = _time.perf_counter()
        n_total = max(int(self.duration / self.dt), 1)
        k = 0
        while not self.finished:
            self.step()
            k += 1
            if progress and k % 50 == 0:
                progress(min(k / n_total, 1.0))
            if max_wall_time and _time.perf_counter() - start > max_wall_time:
                self.finished, self.stop_reason = True, "Rechenzeitlimit"
        self.result.metadata.update(stop_reason=self.stop_reason, wall_time=_time.perf_counter() - start,
                                    energy_drive=self.actuation.powertrain.energy_drive,
                                    energy_regen=self.actuation.powertrain.energy_regen)
        log.info("'%s' finished after %.2f s simulated (%s), %.2f s wall time", self.name, self.t,
                 self.stop_reason, self.result.metadata["wall_time"])
        return self.result

    # logging
    def _log(self, steer_request=0.0):
        vs, out, u = self.state, self.outputs, self.u
        proj = self.trajectory.project(vs.x, vs.y, hint=self._log_hint)
        self._log_hint = proj.index
        self._s = proj.s
        row = {"t": self.t, "x": vs.x, "y": vs.y, "psi": vs.psi, "vx": vs.vx, "vy": vs.vy, "r": vs.r,
               "speed": vs.speed, "ax": vs.ax, "ay": vs.ay, "beta": vs.beta, "delta_f": u.steer_front,
               "delta_r": u.steer_rear, "steer_request": steer_request, "roll": vs.roll, "roll_rate": vs.roll_rate,
               "pitch": vs.pitch, "heave": vs.heave, "s": proj.s, "lateral_error": proj.lateral_error,
               "heading_error": float((vs.psi - proj.heading + np.pi) % (2 * np.pi) - np.pi), "v_ref": proj.speed,
               "kappa_ref": proj.kappa, "fx": vs.fx, "fy": vs.fy, "fz": vs.fz, "slip_angle": vs.slip_angle,
               "slip_ratio": vs.slip_ratio, "wheel_speed": vs.wheel_speed, "mu": vs.mu,
               "drive_torque": u.drive_torque, "brake_torque": u.brake_torque,
               "energy_drive": self.actuation.powertrain.energy_drive,
               "energy_regen": self.actuation.powertrain.energy_regen}
        for key in ("camber", "suspension_travel", "body_z", "body_az"):
            if key in out:
                row[key] = out[key]
        if self.env.lead_vehicle is not None:
            row["lead_s"] = self.env.lead_vehicle.s
            row["lead_speed"] = self.env.lead_vehicle.speed_at(self.t)
        for component in [self.lateral, self.longitudinal, self.steering, self.actuation, *self.systems]:
            for key, value in getattr(component, "signals", {}).items():
                row.setdefault(key, value)
        self.result.append(row)


def run_scenario(scenario, progress=None):
    return Simulator.from_scenario(scenario).run(progress)
