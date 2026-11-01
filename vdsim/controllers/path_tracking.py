"""Shared helpers for the path-tracking controllers."""

import numpy as np


def wrap(angle):
    return (angle + np.pi) % (2 * np.pi) - np.pi


def axle_point(state, distance):
    # point on the vehicle axis `distance` ahead of the CG (negative = behind)
    return state.x + distance * np.cos(state.psi), state.y + distance * np.sin(state.psi)


def clip_steer(delta, config):
    limit = config.vehicle.max_steer_angle
    return float(np.clip(delta, -limit, limit))
