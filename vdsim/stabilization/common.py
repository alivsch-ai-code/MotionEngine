"""Shared helpers of the trajectory tracking controllers.

Sign conventions (Werling 4.2.3): the planner delivers theta = direction of motion, v >= 0, kappa =
d theta / d s and direction varsigma = +-1. Werling's controller quantities follow from

    psi_d = theta (+ pi when reversing)       vehicle orientation of the reference point
    v_d   = varsigma v,  v_d_dot = varsigma a  signed speed / acceleration
    kappa_d = psi_d_dot / v_d = varsigma kappa, kappa_d' = d kappa_d / d s_d = varsigma dkappa,
    kappa_d_dot = d kappa_d / dt = varsigma dkappa v
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ..core.parameters import VehicleConfig
from ..framework.types import ControlCommand, ControllerStatus, PlannedTrajectory, TrajectoryPoint
from ..vehicle_models.werling_models import werling_parameters

V_SWITCH = 3.0       # m/s, controller switching speed v_s (contracts.md section 7)


def wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def vehicle_config(context):
    cfg = getattr(context, "vehicle", None) if context is not None else None
    return cfg if cfg is not None else VehicleConfig()


def environment_mu(context):
    env = context.service("environment") if context is not None else None
    if env is None:
        return 1.0
    try:
        return float(env.friction.base)
    except AttributeError:
        return 1.0


def design_parameters(context, mu=-1.0):
    # WerlingParameters of the vehicle in the context; mu < 0: tire mu times the road base friction
    cfg = vehicle_config(context)
    if mu is None or mu < 0:
        mu = cfg.tires.mu * environment_mu(context)
    return werling_parameters(cfg, mu)


def drive_share(config):
    # force ratio gamma = F_vl / F_l when driving (Werling 5.1.2.2: front-wheel drive -> 1.0)
    pt = config.powertrain
    return {"fwd": 1.0, "rwd": 0.0}.get(pt.layout, pt.front_torque_split)


def force_ratio(F_l, varsigma, gamma_drive, gamma_brake):
    # driving when the force acts in the direction of travel, braking otherwise
    return gamma_drive if varsigma * F_l >= 0.0 else gamma_brake


@dataclass
class Desired:
    # desired values of the reference point in Werling's notation (signed)
    t: float = 0.0
    x: float = 0.0
    y: float = 0.0
    psi: float = 0.0          # orientation psi_d (rear axle) / course theta_d (CoG)
    kappa: float = 0.0        # kappa_d
    kappa_dot: float = 0.0    # d kappa_d / dt
    kappa_prime: float = 0.0  # d kappa_d / d s_d
    v: float = 0.0            # v_d (signed)
    v_dot: float = 0.0
    varsigma: int = 1
    speed: float = 0.0        # s_d_dot >= 0
    theta: float = 0.0        # direction of motion
    accel: float = 0.0


def desired_from_point(pt: TrajectoryPoint) -> Desired:
    sg = 1 if pt.direction >= 0 else -1
    return Desired(t=pt.t, x=pt.x, y=pt.y, psi=pt.psi, kappa=sg * pt.kappa, kappa_dot=sg * pt.dkappa * pt.v,
                   kappa_prime=sg * pt.dkappa, v=sg * pt.v, v_dot=sg * pt.a, varsigma=sg, speed=pt.v,
                   theta=pt.theta, accel=pt.a)


def cog_point_as_rear_axle(pt: TrajectoryPoint, lh):
    # quasi-static conversion of a CoG trajectory point to the rear-axle center (kinematic model,
    # circular motion: sin(beta) = l_h kappa_cog); fallback for "cog" trajectories at very low speed
    sg = 1 if pt.direction >= 0 else -1
    s = max(min(lh * pt.kappa, 0.95), -0.95)
    beta = math.asin(s)
    cb = math.cos(beta)
    theta_r = pt.theta - beta
    psi_r = theta_r if sg > 0 else theta_r + math.pi
    return TrajectoryPoint(t=pt.t, x=pt.x - lh * math.cos(psi_r), y=pt.y - lh * math.sin(psi_r), theta=theta_r,
                           kappa=pt.kappa / cb, dkappa=pt.dkappa / cb, v=pt.v * cb, a=pt.a * cb, s=pt.s, d=pt.d,
                           direction=pt.direction)


def sample(traj: PlannedTrajectory, t):
    return traj.sample(t)


def hold_command(t, ego, name, varsigma=1):
    # no trajectory: keep the steering, brake gently to standstill
    return ControlCommand(t=t, steer_rate=0.0, steer_angle=float(ego.delta), force=0.0, accel=0.0,
                          direction=varsigma, controller=name, info={"hold": True})


def empty_status(t, name):
    return ControllerStatus(t=t, active_controller=name)


@dataclass
class StepTimer:
    # wall-clock time of the controller steps (diagnostics only, never used in the control logic)
    samples: list = field(default_factory=list)

    def add(self, dt):
        self.samples.append(dt)
        if len(self.samples) > 5000:
            self.samples = self.samples[-5000:]

    @property
    def mean(self):
        return float(np.mean(self.samples)) if self.samples else 0.0
