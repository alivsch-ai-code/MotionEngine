"""Active suspension: roll stabilization and skyhook damping."""

import numpy as np

from ..core.interfaces import ChassisSystem
from ..core.registry import register


@register("chassis_system", "active_roll")
class ActiveRollStabilization(ChassisSystem):
    # counteracts the roll moment of the lateral acceleration (gain 1 = full compensation)
    label = "Aktive Wankstabilisierung"

    def __init__(self, config):
        self.config = config
        p, ch = config.vehicle, config.chassis
        self.m_s = p.mass - 2 * (p.unsprung_mass_front + p.unsprung_mass_rear)
        h_axis = ch.roll_center_height_front + (ch.roll_center_height_rear - ch.roll_center_height_front) \
            * p.cg_to_front / p.wheelbase
        self.h_arm = p.cg_height - h_axis
        self.signals = {}

    def apply(self, t, state, u, dt):
        gain = self.config.systems.active_roll_gain
        u.roll_moment = -gain * self.m_s * state.ay * self.h_arm - 3000.0 * state.roll_rate
        self.signals = {"active_roll_moment": u.roll_moment}
        return u


@register("chassis_system", "active_damping")
class SkyhookDamping(ChassisSystem):
    # skyhook: damper force proportional to the absolute body velocity at each corner
    label = "Aktive Dämpfung (Skyhook)"

    def __init__(self, config):
        self.config = config
        p = config.vehicle
        self.x_w = np.array([p.cg_to_front, p.cg_to_front, -p.cg_to_rear, -p.cg_to_rear])
        self.y_w = np.array([p.track_front, -p.track_front, p.track_rear, -p.track_rear]) / 2
        self.signals = {}

    def apply(self, t, state, u, dt):
        body_velocity = state.heave_rate + self.y_w * state.roll_rate - self.x_w * state.pitch_rate
        u.damper_force = -self.config.systems.skyhook_gain * body_velocity
        self.signals = {"skyhook_force_max": float(np.max(np.abs(u.damper_force)))}
        return u
