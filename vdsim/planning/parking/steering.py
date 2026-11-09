"""Steering configurations for low-speed maneuvering: which wheels steer, where the vehicle turns about.

At parking speed the tires roll without side slip, so the vehicle moves like a rigid body about an
instantaneous center of rotation (ICR) where the normals of all wheel planes meet (Ackermann condition;
Rajamani 2012, 2.2; Mitschke and Wallentowitz 2014, ch. 23). With steering angles delta_f at the front
axle (x_f ahead of the CoG) and delta_r at the rear axle (x_r = -l_r), the ICR lies at

    x_c = (x_f tan(delta_r) - x_r tan(delta_f)) / (tan(delta_r) - tan(delta_f)),
    y_c = (x_f - x_c) / tan(delta_f)

in body coordinates. The point P = (x_c, 0) on the vehicle axis moves exactly along the axis (no side
slip), with path curvature

    kappa = (tan(delta_f) - tan(delta_r)) / L,    L = x_f - x_r (wheelbase).

If the rear angle is coupled to the front angle by a constant ratio of the tangents,
tan(delta_r) = k tan(delta_f), then x_c = (k x_f - x_r) / (k - 1) does not depend on the steering angle:
P is a fixed point of the body that moves like the rear axle of a car with front steering. The
Reeds-Shepp / Hybrid A* planner therefore plans P with the minimum turning radius 1/kappa_max, and the
same planner covers every configuration:

    front   k = 0         P at the rear axle (conventional car)
    rear    delta_f = 0   P at the front axle (rear-wheel steering only: forklift, some special vehicles)
    counter k < 0         P between the axles, smaller turning circle (four-wheel steering, counter-phase)
    in      0 < k < 1     P behind the rear axle, larger turning circle (four-wheel steering, in-phase)

The drive layout (front, rear, all-wheel drive) does not change this geometry; it matters in the
closed-loop simulation, where the drive force acts at the driven axle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

STEERING_MODES = ("front", "rear", "counter", "in_phase")


@dataclass(frozen=True)
class SteeringGeometry:
    """Planning reference point and turning limit of one steering configuration."""
    mode: str
    wheelbase: float          # m
    x_front: float            # front axle, ahead of the CoG, m
    x_rear: float             # rear axle (negative), m
    max_front: float          # rad, maximum road-wheel angle at the front axle (0 if it does not steer)
    max_rear: float           # rad, maximum road-wheel angle at the rear axle (0 if it does not steer)
    ratio: float              # k = tan(delta_r) / tan(delta_f) for the coupled modes

    @property
    def x_ref(self) -> float:
        """Body x coordinate (from the CoG, forward > 0) of the side-slip-free reference point P."""
        if self.mode == "rear":
            return self.x_front
        k = self.ratio
        return (k * self.x_front - self.x_rear) / (k - 1.0)

    @property
    def max_curvature(self) -> float:
        """1/m, curvature of P at full steering lock."""
        if self.mode == "rear":
            return math.tan(self.max_rear) / self.wheelbase
        tf = math.tan(self.max_front)
        if self.mode != "front":
            # the rear axle may limit first: |k tan(delta_f)| <= tan(max_rear)
            tf = min(tf, math.tan(self.max_rear) / abs(self.ratio)) if self.ratio else tf
        return tf * (1.0 - self.ratio) / self.wheelbase

    @property
    def min_radius(self) -> float:
        return 1.0 / self.max_curvature

    def angles(self, kappa: float) -> tuple[float, float]:
        """(delta_f, delta_r) in rad that drive P on a path with curvature kappa (left > 0)."""
        if self.mode == "rear":
            # front wheels straight; the ICR is on the front axle line: tan(delta_r) = -kappa L
            return 0.0, math.atan(-kappa * self.wheelbase)
        tf = kappa * self.wheelbase / (1.0 - self.ratio)
        return math.atan(tf), math.atan(self.ratio * tf)

    def to_dict(self) -> dict:
        return {"mode": self.mode, "wheelbase": self.wheelbase, "x_ref": self.x_ref,
                "reference_from_rear_axle": self.x_ref - self.x_rear, "max_curvature": self.max_curvature,
                "min_radius": self.min_radius, "max_front_deg": math.degrees(self.max_front),
                "max_rear_deg": math.degrees(self.max_rear), "ratio": self.ratio}


def steering_geometry(vehicle, mode: str = "front", ratio: float | None = None,
                      max_rear_angle: float | None = None) -> SteeringGeometry:
    """Geometry for a VehicleConfig (or VehicleParameters) and a steering mode.

    ratio: k = tan(delta_r) / tan(delta_f); default -0.3 for counter-phase, +0.3 for in-phase.
    max_rear_angle: rad; default 0.17 rad (~10 deg, production rear-axle steering) for four-wheel steering
    and the front limit for rear-wheel steering only.
    """
    if mode not in STEERING_MODES:
        raise ValueError(f"unknown steering mode '{mode}', available: {STEERING_MODES}")
    v = getattr(vehicle, "vehicle", vehicle)
    lf = float(v.cg_to_front)
    lr = float(v.wheelbase) - lf
    max_f = float(v.max_steer_angle)
    if mode == "front":
        return SteeringGeometry(mode, float(v.wheelbase), lf, -lr, max_f, 0.0, 0.0)
    if mode == "rear":
        return SteeringGeometry(mode, float(v.wheelbase), lf, -lr, 0.0,
                                float(max_rear_angle) if max_rear_angle is not None else max_f, 0.0)
    k = ratio if ratio is not None else (-0.3 if mode == "counter" else 0.3)
    if mode == "counter" and not -1.0 <= k < 0.0:
        raise ValueError("counter-phase ratio must be in [-1, 0)")
    if mode == "in_phase" and not 0.0 < k < 1.0:
        raise ValueError("in-phase ratio must be in (0, 1)")
    max_r = float(max_rear_angle) if max_rear_angle is not None else 0.17
    return SteeringGeometry(mode, float(v.wheelbase), lf, -lr, max_f, max_r, float(k))
