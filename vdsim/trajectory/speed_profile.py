"""GGV-limited speed profile along a path (forward/backward pass with a friction ellipse)."""

import numpy as np


def speed_profile(s, kappa, v_max, ay_max=4.0, ax_max=2.5, ax_min=-4.0, v_start=None, v_end=None):
    s = np.asarray(s, dtype=float)
    kappa = np.abs(np.asarray(kappa, dtype=float))
    v_limit = np.minimum(np.sqrt(ay_max / np.maximum(kappa, 1e-9)), v_max)
    v = v_limit.copy()
    if v_start is not None:
        v[0] = min(v[0], v_start)
    if v_end is not None:
        v[-1] = min(v[-1], v_end)
    ds = np.diff(s)

    def available(v_now, k, a_lim):
        # longitudinal acceleration left over by the lateral demand (friction ellipse)
        usage = min((v_now**2 * k / ay_max) ** 2, 1.0)
        return abs(a_lim) * np.sqrt(1.0 - usage)

    for i in range(len(ds)):
        v[i + 1] = min(v[i + 1], np.sqrt(v[i] ** 2 + 2 * available(v[i], kappa[i], ax_max) * ds[i]))
    for i in range(len(ds) - 1, -1, -1):
        v[i] = min(v[i], np.sqrt(v[i + 1] ** 2 + 2 * available(v[i + 1], kappa[i + 1], ax_min) * ds[i]))
    return v


def lap_time(s, v):
    v_mid = np.maximum((v[1:] + v[:-1]) / 2, 0.1)
    return float(np.sum(np.diff(s) / v_mid))
