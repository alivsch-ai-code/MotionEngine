"""Desired curvature for the lane change."""

import numpy as np


def lane_change_curvature(t, v, width=3.5, duration=6.0, t_start=1.0):
    # Sinusoidal curvature: heading returns to 0 and the lateral offset is ~width.
    # Peak lateral acceleration = 2*pi*width/duration^2 (0.61 m/s^2 for 3.5 m in 6 s).
    tau = t - t_start
    if tau < 0.0 or tau > duration:
        return 0.0
    return 2.0 * np.pi * width / (v**2 * duration**2) * np.sin(2.0 * np.pi * tau / duration)
