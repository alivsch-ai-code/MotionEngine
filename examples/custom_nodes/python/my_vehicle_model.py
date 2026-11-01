"""Custom node (Python): kinematic single-track vehicle with the ports of VehiclePlantBase.

Graph spec: "python:examples/custom_nodes/python/my_vehicle_model.py:KinematicBicyclePlant"

    input:  control (ControlInput: steer_front, drive/brake torque per wheel)
    output: ego (EgoState at the CoG)
    no direct feedthrough: output(t) from the state, update(t, inputs, dt) integrates

The file also contains CommandToControl, a simplified stand-in for the layers Vehicle
Dynamics + Actuators (ControlCommand -> ControlInput), so the example chain can be closed
with Python custom nodes only.
"""

import math
from dataclasses import dataclass

import numpy as np

from vdsim.core.parameters import param
from vdsim.framework.component import Component, Port
from vdsim.framework.knowledge import ComponentDoc
from vdsim.framework.layers import VehiclePlantBase
from vdsim.framework.types import ControlInput, EgoState


@dataclass
class KinematicPlantParams:
    wheelbase: float = param(2.8, "m", "Radstand", min=1.0)
    cg_to_rear: float = param(1.4, "m", "Schwerpunkt - Hinterachse", min=0.0)
    mass: float = param(1600.0, "kg", "Masse", min=100.0)
    wheel_radius: float = param(0.32, "m", "Radradius", min=0.1)
    rolling_resistance: float = param(0.01, "-", "Rollwiderstandsbeiwert", min=0.0)
    x0: float = param(0.0, "m", "Startposition x")
    y0: float = param(0.0, "m", "Startposition y")
    psi0: float = param(0.0, "rad", "Start-Gierwinkel")
    v0: float = param(10.0, "m/s", "Startgeschwindigkeit", min=0.0)
    substeps: int = param(4, "", "Teilschritte", min=1, max=100)


class KinematicBicyclePlant(VehiclePlantBase):
    NAME = "my_kinematic_bicycle"
    VERSION = "1.0.0"
    LABEL = "Kinematisches Einspurmodell (Beispiel, Python)"
    PARAMS = KinematicPlantParams
    DOC = ComponentDoc(summary="Kinematisches Einspurmodell mit Längsdynamik aus Radmomenten.",
                       purpose="Beispiel für eine Strecke ohne Durchgriff (output/update).",
                       limitations=["kein Schräglauf, gültig für kleine Querbeschleunigungen"])

    def reset(self, context):
        super().reset(context)
        p = self.params
        init = getattr(getattr(context, "scenario", None), "ego_initial", None) or {}
        self.x = float(init.get("x", p.x0))
        self.y = float(init.get("y", p.y0))
        self.psi = float(init.get("psi", p.psi0))
        self.v = float(init.get("v", p.v0))
        self.delta = 0.0
        self.delta_rate = 0.0
        self.ax = 0.0

    def output(self, t):
        p = self.params
        beta = math.atan(p.cg_to_rear * math.tan(self.delta) / p.wheelbase)
        r = self.v * math.cos(beta) * math.tan(self.delta) / p.wheelbase
        ego = EgoState(t=t, x=self.x, y=self.y, psi=self.psi, vx=self.v * math.cos(beta), vy=self.v * math.sin(beta),
                       r=r, ax=self.ax, ay=self.v * r, delta=self.delta, delta_rate=self.delta_rate, gear=1)
        return {"ego": ego}

    def update(self, t, inputs, dt):
        u = inputs["control"]
        p = self.params
        steer = float(u.steer_front) if u is not None else self.delta
        drive = float(np.sum(u.drive_torque)) if u is not None else 0.0
        brake = float(np.sum(u.brake_torque)) if u is not None else 0.0
        self.delta_rate = (steer - self.delta) / dt
        self.delta = steer
        force = (drive - (brake if self.v > 0.0 else 0.0)) / p.wheel_radius
        h = dt / p.substeps
        for _ in range(p.substeps):
            resist = p.rolling_resistance * p.mass * 9.81 if self.v > 0.0 else 0.0
            self.ax = (force - resist) / p.mass
            beta = math.atan(p.cg_to_rear * math.tan(self.delta) / p.wheelbase)
            self.x += h * self.v * math.cos(self.psi + beta)
            self.y += h * self.v * math.sin(self.psi + beta)
            self.psi += h * self.v * math.cos(beta) * math.tan(self.delta) / p.wheelbase
            self.v = max(0.0, self.v + h * self.ax)


@dataclass
class CommandToControlParams:
    mass: float = param(1600.0, "kg", "Masse", min=100.0)
    wheel_radius: float = param(0.32, "m", "Radradius", min=0.1)
    max_steer: float = param(0.6, "rad", "Max. Lenkwinkel", min=0.01)


class CommandToControl(Component):
    KIND, NAME, VERSION = "node", "my_command_to_control", "1.0.0"
    LABEL, CATEGORY = "Stellbefehl → Stellgrößen (Beispiel)", "Beispiele"
    INPUTS = {"command": Port("ControlCommand")}
    OUTPUTS = {"control": Port("ControlInput")}
    PARAMS = CommandToControlParams
    DOC = ComponentDoc(summary="Vereinfachte Fahrdynamik-/Aktorebene: Lenkwinkel direkt, a → Radmomente (4 Räder).")

    def reset(self, context):
        super().reset(context)
        self.steer = 0.0

    def step(self, t, inputs):
        cmd = inputs["command"]
        p = self.params
        if cmd is None:
            return {"control": ControlInput()}
        dt = getattr(self, "sample_time", None) or 0.01
        if cmd.steer_angle is not None:
            self.steer = cmd.steer_angle
        elif cmd.steer_rate is not None:
            self.steer += cmd.steer_rate * dt
        self.steer = min(max(self.steer, -p.max_steer), p.max_steer)
        force = cmd.force if cmd.force is not None else p.mass * (cmd.accel or 0.0)
        torque = force * p.wheel_radius / 4.0
        drive = np.full(4, max(torque, 0.0))
        brake = np.full(4, max(-torque, 0.0))
        return {"control": ControlInput(steer_front=self.steer, drive_torque=drive, brake_torque=brake)}
