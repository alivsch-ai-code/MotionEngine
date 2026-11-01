"""Ego geometry, reference points and the motion prediction of the high-level stabilization.

    EgoGeometry          vehicle outline relative to the trajectory reference point
                         ("cog" fast driving, "rear_axle" slow driving, Werling 3.5.4)
    convert_reference    moves a trajectory state between the two reference points
    taylor_prediction    vehicle model independent prediction of the reference point motion
                         with constant acceleration and course rate (Werling 4.5.2, Fig. 4.14)
    ego_reference_state  state of the reference point from a measured EgoState
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..framework.knowledge import trace


@dataclass
class EgoGeometry:
    length: float = 4.8
    width: float = 1.85
    wheelbase: float = 2.8
    cg_to_front: float = 1.25
    front_overhang: float = 1.0
    rear_overhang: float = 1.0

    @property
    def cg_to_rear(self):
        return self.wheelbase - self.cg_to_front

    @classmethod
    def from_vehicle(cls, vehicle_config, front_overhang=-1.0, rear_overhang=-1.0):
        # VehicleConfig (or VehicleParameters) -> geometry; negative overhangs = split the rest evenly
        v = getattr(vehicle_config, "vehicle", vehicle_config)
        rest = max(v.length - v.wheelbase, 0.0)
        fo = front_overhang if front_overhang >= 0 else 0.5 * rest
        ro = rear_overhang if rear_overhang >= 0 else rest - fo
        return cls(length=fo + v.wheelbase + ro, width=v.width, wheelbase=v.wheelbase, cg_to_front=v.cg_to_front,
                   front_overhang=fo, rear_overhang=ro)

    def extent(self, reference_point):
        # (distance to the front bumper, distance to the rear bumper) along the vehicle axis
        if reference_point == "rear_axle":
            return self.wheelbase + self.front_overhang, self.rear_overhang
        return self.cg_to_front + self.front_overhang, self.cg_to_rear + self.rear_overhang

    def center_offset(self, reference_point):
        # geometric center relative to the reference point (along the vehicle axis, forward > 0)
        front, rear = self.extent(reference_point)
        return 0.5 * (front - rear)

    def leading_extent(self, reference_point, direction=1):
        # distance from the reference point to the vehicle end leading in the direction of motion
        front, rear = self.extent(reference_point)
        return front if direction > 0 else rear


@trace("werling2011", section="3.5.4", concept="reference_point",
       note="Schwerpunkt bei schneller Fahrt, Hinterachsmitte bei langsamer Fahrt; kinematische Umrechnung")
def convert_reference(state, from_point, to_point, geometry, direction=1):
    # state dict x, y, theta (direction of motion), kappa, v, a -> same dict for the other reference point.
    # Planning assumption: zero side slip at the trajectory reference point, i.e. the vehicle axis psi
    # equals theta (theta + pi when reversing). theta, kappa, v and a are kept (the yaw rate
    # psi_dot = v kappa is preserved); the neglected CoG side slip l_r kappa causes a small jump.
    if from_point == to_point:
        return dict(state)
    out = dict(state)
    psi = state["theta"] + (0.0 if direction > 0 else np.pi)
    lr = geometry.cg_to_rear
    sign = -1.0 if to_point == "rear_axle" else 1.0
    out["x"] = state["x"] + sign * lr * np.cos(psi)
    out["y"] = state["y"] + sign * lr * np.sin(psi)
    return out


@trace("werling2011", section="4.5.2", equation="Abb. 4.14", concept="motion_prediction",
       note="Taylor-Reihen der Bewegung mit konstanter Beschleunigung und Kurswinkelrate, singularitätsfrei")
def taylor_prediction(x, y, theta, v, v_dot, theta_dot, dt):
    # predicted (x, y, theta, v) of the reference point after dt (dt may be an array)
    dt = np.asarray(dt, dtype=float)
    w = theta_dot
    x1 = v * dt + 0.5 * v_dot * dt**2 - v * w**2 / 6.0 * dt**3 - v_dot * w**2 / 8.0 * dt**4
    x2 = 0.5 * v * w * dt**2 + v_dot * w / 3.0 * dt**3 - v * w**3 / 24.0 * dt**4
    c, s = np.cos(theta), np.sin(theta)
    return x + c * x1 - s * x2, y + s * x1 + c * x2, theta + w * dt, v + v_dot * dt


def ego_reference_state(ego, reference_point, geometry, slow_speed=3.0):
    # Reference point state (x, y, theta, v, v_dot, theta_dot, kappa, a) from a measured EgoState (CoG)
    psi = ego.psi
    if reference_point == "rear_axle":
        px, py = ego.rear_axle(geometry.cg_to_rear)
        vx, vy = ego.vx, ego.vy - geometry.cg_to_rear * ego.r
    else:
        px, py = ego.x, ego.y
        vx, vy = ego.vx, ego.vy
    speed = float(np.hypot(vx, vy))
    reverse = ego.vx < -0.05 or (abs(ego.vx) <= 0.05 and ego.gear < 0)
    if speed > 0.05:
        theta = psi + np.arctan2(vy, vx)
    else:
        theta = psi + (np.pi if reverse else 0.0)
    # tangential acceleration of the reference point (vehicle frame accelerations)
    dirx, diry = (vx / speed, vy / speed) if speed > 0.05 else ((-1.0 if reverse else 1.0), 0.0)
    v_dot = ego.ax * dirx + ego.ay * diry
    theta_dot = ego.r
    if speed < slow_speed:
        # low speed: course rate from the kinematic single-track model (Werling 4.5.2, KESM)
        kappa_kin = np.tan(ego.delta) / geometry.wheelbase
        theta_dot = (-1.0 if reverse else 1.0) * speed * kappa_kin if reference_point == "rear_axle" else theta_dot
        kappa = kappa_kin * (-1.0 if reverse else 1.0)
    else:
        kappa = theta_dot / speed
    return {"x": float(px), "y": float(py), "theta": float(theta), "v": speed, "v_dot": float(v_dot),
            "theta_dot": float(theta_dot), "kappa": float(kappa), "a": float(v_dot),
            "direction": -1 if reverse else 1}
