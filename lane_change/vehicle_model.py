"""Kinematic single-track model with curvature as input."""

import numpy as np


def vehicle_step(x, y, psi, v, k, dt):
    # One Euler step: x' = v*cos(psi), y' = v*sin(psi), psi' = v*k
    return (
        x + v * np.cos(psi) * dt,
        y + v * np.sin(psi) * dt,
        psi + v * k * dt,
    )
