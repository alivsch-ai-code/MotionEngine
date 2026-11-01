"""ESP: yaw-rate control by single-wheel braking, plus the reference yaw-rate model."""

import numpy as np

from ..core.conventions import G
from ..core.interfaces import ChassisSystem
from ..core.registry import register
from ..tire_models import create_tires
from ..vehicle_models.common import axle_cornering_stiffness


def understeer_gradient(config):
    # rad/(m/s^2) from the linear single-track model at static loads
    p = config.vehicle
    tire_f, tire_r = create_tires(config.tires)
    fz_f, fz_r = p.static_axle_loads
    c_f = axle_cornering_stiffness(tire_f, fz_f / 2)
    c_r = axle_cornering_stiffness(tire_r, fz_r / 2)
    return (fz_f / c_f - fz_r / c_r) / G


def reference_yaw_rate(config, speed, steer, mu=1.0, eg=None):
    # steady-state yaw rate of the linear model, limited by the friction (0.85 mu g / v)
    p = config.vehicle
    eg = understeer_gradient(config) if eg is None else eg
    v = max(speed, 1.0)
    r_ref = v * steer / (p.wheelbase + eg * v**2)
    limit = 0.85 * mu * G / v
    return float(np.clip(r_ref, -limit, limit))


@register("chassis_system", "esp")
class ElectronicStabilityProgram(ChassisSystem):
    # yaw-rate control by single-wheel braking (oversteer: outer front, understeer: inner rear)
    label = "ESP"

    def __init__(self, config):
        self.config = config
        self.eg = understeer_gradient(config)
        self.signals = {}

    def apply(self, t, state, u, dt):
        sys, p = self.config.systems, self.config.vehicle
        r_ref = reference_yaw_rate(self.config, state.vx, u.steer_front, float(np.mean(state.mu)), self.eg)
        error = r_ref - state.r
        moment = 0.0
        if abs(error) > sys.esp_deadband and state.vx > 5.0:
            moment = sys.esp_gain * (error - np.sign(error) * sys.esp_deadband)
            oversteer = abs(state.r) > abs(r_ref) and np.sign(state.r) == np.sign(r_ref)
            if moment > 0:   # yaw left: brake a left wheel
                wheel = 0 if oversteer else 2
            else:            # yaw right: brake a right wheel
                wheel = 1 if oversteer else 3
            track = p.track_front if wheel < 2 else p.track_rear
            limit = self.config.brakes.max_torque_front if wheel < 2 else self.config.brakes.max_torque_rear
            extra = min(abs(moment) * p.wheel_radius / (track / 2), limit)
            u.brake_torque = u.brake_torque.copy()
            u.brake_torque[wheel] = min(u.brake_torque[wheel] + extra, limit)
            u.drive_torque = u.drive_torque * 0.7  # engine torque reduction while intervening
        self.signals = {"esp_r_ref": r_ref, "esp_moment": moment, "esp_active": float(moment != 0.0)}
        return u
