"""Wheel-slip control: ABS (brake slip) and TCS (drive slip). Needs a model with wheel dynamics."""

import numpy as np

from ..core.interfaces import ChassisSystem
from ..core.registry import register


class _SlipModulation(ChassisSystem):
    # per-wheel torque modulation factor m in [0, 1] driven by a slip threshold with hysteresis
    release_time = 0.04
    apply_time = 0.25

    def __init__(self, config):
        self.config = config
        self.reset()

    def reset(self):
        self.factor = np.ones(4)
        self.signals = {}

    def _update(self, too_much, ok, dt):
        self.factor = np.where(too_much, self.factor - dt / self.release_time, self.factor)
        self.factor = np.where(ok, self.factor + dt / self.apply_time, self.factor)
        self.factor = np.clip(self.factor, 0.0, 1.0)


@register("chassis_system", "abs")
class AntiLockBraking(_SlipModulation):
    label = "ABS"

    def apply(self, t, state, u, dt):
        target = self.config.systems.abs_target_slip
        braking = u.brake_torque > 0
        too_much = braking & (state.slip_ratio < -target) & (state.vx > 2.0)
        ok = ~too_much & (state.slip_ratio > -0.5 * target)
        self._update(too_much, ok, dt)
        self.factor = np.where(braking, self.factor, 1.0)
        u.brake_torque = u.brake_torque * self.factor
        self.signals = {"abs_active": float(np.any(self.factor < 0.999)), "abs_factor_min": float(self.factor.min())}
        return u


@register("chassis_system", "tcs")
class TractionControl(_SlipModulation):
    label = "Antriebsschlupfregelung (ASR/TCS)"
    release_time = 0.08
    apply_time = 0.4

    def apply(self, t, state, u, dt):
        target = self.config.systems.tcs_target_slip
        driving = u.drive_torque > 0
        too_much = driving & (state.slip_ratio > target)
        ok = ~too_much & (state.slip_ratio < 0.5 * target)
        self._update(too_much, ok, dt)
        self.factor = np.where(driving, self.factor, 1.0)
        u.drive_torque = np.where(driving, u.drive_torque * self.factor, u.drive_torque)
        self.signals = {"tcs_active": float(np.any(self.factor < 0.999))}
        return u
