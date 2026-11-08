"""Supervised data for a vehicle dynamics surrogate, generated from a physics model ("teacher").

Features x = [v_x, v_y, r, delta, F_x]   (m/s, m/s, rad/s, rad, N: total longitudinal wheel force request)
Targets  y = [dv_x/dt, dv_y/dt, dr/dt]   (body-frame accelerations of the planar single-track state)

States are drawn uniformly over the driving envelope (Monte Carlo): side slip |beta| <= beta_max,
yaw rate within the friction limit |r| <= 1.2 mu g / v_x, steering |delta| <= delta_max, F_x between
full braking and the drive limit. The teacher's derivatives are exact, so the dataset carries no
integration error.
"""

from __future__ import annotations

import numpy as np

from ..core.conventions import G
from ..core.registry import create
from ..simulation.environment import Environment
from ..simulation.vehicle_state import ControlInput

FEATURES = ("vx", "vy", "r", "delta", "fx")
TARGETS = ("vx_dot", "vy_dot", "r_dot")
TEACHERS = ("bicycle_nonlinear", "bicycle_linear")


def control_for(delta, fx, wheel_radius):
    # equal torque on all four wheels: drive for fx > 0, brake for fx < 0
    u = ControlInput(steer_front=float(delta))
    torque = abs(fx) * wheel_radius / 4.0
    if fx >= 0:
        u.drive_torque = np.full(4, torque)
    else:
        u.brake_torque = np.full(4, torque)
    return u


def sample_dataset(config, teacher="bicycle_nonlinear", n=20000, seed=0, v_range=(3.0, 40.0), beta_max=0.12,
                   delta_max=0.2):
    if teacher not in TEACHERS:
        raise ValueError(f"teacher must be one of {TEACHERS}")
    model = create("vehicle_model", teacher, config)
    p = config.vehicle
    rng = np.random.default_rng(seed)
    mu = config.tires.mu
    vx = rng.uniform(*v_range, n)
    vy = vx * np.tan(rng.uniform(-beta_max, beta_max, n))
    r = rng.uniform(-1.2, 1.2, n) * mu * G / vx
    delta = rng.uniform(-delta_max, delta_max, n) * np.clip(10.0 / vx, 0.25, 1.0)
    fx = rng.uniform(-0.9, 0.5, n) * mu * p.mass * G
    env = Environment()
    x = np.column_stack([vx, vy, r, delta, fx])
    y = np.empty((n, 3))
    for i in range(n):
        s = np.array([0.0, 0.0, 0.0, vx[i], vy[i], r[i]])
        ds = model.derivatives(0.0, s, control_for(delta[i], fx[i], p.wheel_radius), env)
        y[i] = ds[3:6]
    return x, y
