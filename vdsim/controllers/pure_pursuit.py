"""Pure Pursuit path tracking (geometric, rear-axle reference, speed-dependent look-ahead)."""

import numpy as np

from ..core.interfaces import LateralController
from ..core.registry import register
from .path_tracking import axle_point, clip_steer, wrap


@register("lateral_controller", "pure_pursuit")
class PurePursuitController(LateralController):
    label = "Pure Pursuit"

    def __init__(self, config, lookahead_gain=0.6, lookahead_min=4.0):
        self.config = config
        self.lookahead_gain, self.lookahead_min = lookahead_gain, lookahead_min
        self.signals = {}
        self._hint = 0

    def steer(self, t, state, ref):
        p = self.config.vehicle
        rx, ry = axle_point(state, -p.cg_to_rear)
        proj = ref.project(rx, ry, hint=self._hint)
        self._hint = proj.index
        lookahead = max(self.lookahead_min, self.lookahead_gain * state.vx)
        target = ref.at(proj.s + lookahead)
        alpha = wrap(np.arctan2(target["y"] - ry, target["x"] - rx) - state.psi)
        delta = np.arctan2(2 * p.wheelbase * np.sin(alpha), lookahead)
        self.signals = {"lateral_error": proj.lateral_error, "lookahead": lookahead, "s": proj.s}
        return clip_steer(delta, self.config)
