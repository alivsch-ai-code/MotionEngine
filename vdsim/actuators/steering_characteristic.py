"""Steering characteristic: requested curvature -> curvature the vehicle actually drives."""

import numpy as np


def steering_characteristic(k_full_lock_assumed, k_full_lock, error_at_zero=0.10):
    # Symmetric for left/right. The relative error rises quadratically from
    # error_at_zero (small curvature) to the full-lock error: requesting
    # k_full_lock_assumed steers to full lock, which actually gives k_full_lock.
    # Larger requests saturate at full lock.
    error_full_lock = k_full_lock / k_full_lock_assumed - 1.0

    def characteristic(k):
        k_abs = np.minimum(np.abs(k), k_full_lock_assumed)
        error = error_at_zero + (error_full_lock - error_at_zero) * (k_abs / k_full_lock_assumed) ** 2
        return np.sign(k) * k_abs * (1.0 + error)

    return characteristic


def correction_factor(characteristic, k_full_lock_assumed, k_des):
    # Theoretical correction factor k_sent / k_des, so that characteristic(k_sent) = k_des.
    # Inverted only up to full lock, where the characteristic is still rising.
    k_grid = np.linspace(0.0, k_full_lock_assumed, 20001)
    k_sent = np.interp(np.abs(k_des), characteristic(k_grid), k_grid)
    return k_sent / np.abs(k_des)
