"""Rear-axle steering: speed-dependent ratio to the front steering angle."""

import numpy as np

from ..core.interfaces import ChassisSystem
from ..core.registry import register


@register("chassis_system", "rear_steering")
class RearAxleSteering(ChassisSystem):
    # speed-dependent ratio: counter-phase at low speed (agility), in-phase at high speed (stability)
    label = "Hinterachslenkung"

    def __init__(self, config):
        self.config = config
        self.signals = {}

    def apply(self, t, state, u, dt):
        s = self.config.systems
        ratio = float(np.interp(state.vx, [s.rear_steering_speed_low, s.rear_steering_speed_high],
                                [s.rear_steering_ratio_low, s.rear_steering_ratio_high]))
        u.steer_rear = float(np.clip(ratio * u.steer_front, -0.1, 0.1))
        self.signals = {"rws_ratio": ratio, "steer_rear": u.steer_rear}
        return u
