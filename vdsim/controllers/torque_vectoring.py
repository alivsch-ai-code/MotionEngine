"""Torque vectoring: yaw moment from a left/right drive-torque difference."""

import numpy as np

from ..core.interfaces import ChassisSystem
from ..core.registry import register
from .esp_controller import reference_yaw_rate, understeer_gradient


@register("chassis_system", "torque_vectoring")
class TorqueVectoring(ChassisSystem):
    # yaw moment from left/right drive-torque difference on the driven axles
    label = "Torque Vectoring"

    def __init__(self, config):
        self.config = config
        self.eg = understeer_gradient(config)
        self.signals = {}

    def apply(self, t, state, u, dt):
        cfg, p = self.config, self.config.vehicle
        # target: more agile than the passive vehicle (understeer gradient scaled by the target factor)
        r_ref = reference_yaw_rate(cfg, state.vx, u.steer_front, float(np.mean(state.mu)),
                                   self.eg * cfg.systems.torque_vectoring_target)
        moment = cfg.systems.torque_vectoring_gain * (r_ref - state.r)
        shares = np.array([cfg.powertrain.front_torque_split, 1 - cfg.powertrain.front_torque_split])
        if cfg.powertrain.layout == "fwd":
            shares = np.array([1.0, 0.0])
        elif cfg.powertrain.layout == "rwd":
            shares = np.array([0.0, 1.0])
        diff_limit = cfg.powertrain.torque_vectoring_max_torque
        u.drive_torque = u.drive_torque.copy()
        for axle, (left, right, track) in enumerate(((0, 1, p.track_front), (2, 3, p.track_rear))):
            if shares[axle] <= 0:
                continue
            delta_t = np.clip(shares[axle] * moment * p.wheel_radius / (track / 2), -diff_limit, diff_limit)
            u.drive_torque[left] -= delta_t / 2
            u.drive_torque[right] += delta_t / 2
        self.signals = {"tv_moment": moment, "tv_r_ref": r_ref}
        return u
