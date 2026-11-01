"""Open-loop steering from the maneuver's steering table and pure curvature feedforward."""

import numpy as np

from ..core.interfaces import LateralController
from ..core.registry import register
from .path_tracking import clip_steer


@register("lateral_controller", "open_loop")
class OpenLoopSteering(LateralController):
    label = "Lenkung nach Tabelle (open loop)"

    def __init__(self, config):
        self.config = config
        self.signals = {}
        self._hint = 0

    def steer(self, t, state, ref):
        if not ref.is_open_loop:
            raise ValueError("open_loop steering needs a maneuver with a steering table (e.g. step_steer)")
        return clip_steer(ref.steer_at(t), self.config)


@register("lateral_controller", "curvature_feedforward")
class CurvatureFeedforward(LateralController):
    # Steers the kinematic angle of the path curvature at the current position, no feedback
    label = "Krümmungsvorsteuerung (ohne Rückführung)"

    def __init__(self, config):
        self.config = config
        self.signals = {}
        self._hint = 0

    def steer(self, t, state, ref):
        proj = ref.project(state.x, state.y, hint=self._hint)
        self._hint = proj.index
        self.signals = {"lateral_error": proj.lateral_error, "s": proj.s}
        return clip_steer(np.arctan(self.config.vehicle.wheelbase * proj.kappa), self.config)
