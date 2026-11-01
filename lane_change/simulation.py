"""Simulation loop: planner (desired curvature + correction) -> gateway -> actuator (with error) -> vehicle -> odometry -> gateway -> planner."""

import numpy as np

from .correction import CurvatureCorrection
from .latency import LatencyChain
from .vehicle_model import vehicle_step


def simulate(v, k_des_fn, characteristic, latency, t_end=10.0, dt=0.01,
             use_correction=False, yaw_rate_noise_deg=0.0, seed=0):
    rng = np.random.default_rng(seed)
    noise_k = np.radians(yaw_rate_noise_deg) / v  # yaw-rate noise as curvature noise

    chain = LatencyChain(**latency, dt=dt)  # real system
    model = LatencyChain(**latency, dt=dt)  # model for time alignment (latency assumed known)
    correction = CurvatureCorrection(dt)

    t = np.arange(0.0, t_end + dt / 2, dt)
    keys = ("x", "y", "psi", "k_des", "k_sent", "k_applied", "k_meas", "error_factor", "error_factor_est")
    out = {key: np.zeros(len(t)) for key in keys}

    x = y = psi = 0.0
    for i, ti in enumerate(t):
        k_des = k_des_fn(ti)
        k_sent = correction.correct(k_des) if use_correction else k_des
        k_applied = characteristic(chain.actuate(k_sent))  # the actuator's error acts after the command latency
        k_meas = chain.sense(k_applied) + noise_k * rng.standard_normal()
        if use_correction:
            correction.update(model.sense(model.actuate(k_sent)), k_meas)

        out["x"][i] = x
        out["y"][i] = y
        out["psi"][i] = psi
        out["k_des"][i] = k_des
        out["k_sent"][i] = k_sent
        out["k_applied"][i] = k_applied
        out["k_meas"][i] = k_meas
        out["error_factor"][i] = characteristic(k_sent) / k_sent if k_sent != 0.0 else np.nan
        out["error_factor_est"][i] = correction.gain

        x, y, psi = vehicle_step(x, y, psi, v, k_applied, dt)

    out["t"] = t
    out["a_y"] = v**2 * out["k_applied"]
    return out
