"""Lane keeping assist (LKA) with an inattentive-driver model.

The driver follows the lane with Pure Pursuit, but from `drift_start` on adds a steering
bias (distraction). The LKA intervenes with a limited steering overlay as soon as the
vehicle's edge comes closer than `activation_margin` to the lane marking.
"""

import numpy as np

from ..core.interfaces import LateralController
from ..core.registry import register
from .path_tracking import axle_point, clip_steer, wrap
from .pure_pursuit import PurePursuitController


@register("lateral_controller", "lane_keeping")
class LaneKeepingAssist(LateralController):
    label = "Spurhalteassistent (LKA)"

    def __init__(self, config, lane_width=3.75, activation_margin=0.3, drift_start=2.0, drift_bias_deg=0.4,
                 gain=0.6, heading_gain=1.5, max_overlay_deg=3.0, enabled=True):
        self.config = config
        self.driver = PurePursuitController(config, lookahead_gain=1.2, lookahead_min=10.0)
        self.lane_width, self.margin = lane_width, activation_margin
        self.drift_start, self.drift_bias = drift_start, np.radians(drift_bias_deg)
        self.gain, self.heading_gain = gain, heading_gain
        self.max_overlay = np.radians(max_overlay_deg)
        self.enabled = enabled
        self.active = False
        self.signals = {}
        self._hint = 0

    def reset(self):
        self.active = False
        self._hint = 0
        self.driver.reset()

    def steer(self, t, state, ref):
        p = self.config.vehicle
        driver = self.driver.steer(t, state, ref)
        if t >= self.drift_start:
            driver += self.drift_bias
        fx, fy = axle_point(state, p.cg_to_front)
        proj = ref.project(fx, fy, hint=self._hint)
        self._hint = proj.index
        distance_to_line = self.lane_width / 2 - abs(proj.lateral_error) - p.width / 2
        if self.enabled and distance_to_line < self.margin:
            self.active = True
        elif distance_to_line > 2 * self.margin:
            self.active = False
        overlay = 0.0
        if self.active and self.enabled:
            heading_error = wrap(proj.heading - state.psi)
            overlay = -self.gain * proj.lateral_error / max(state.vx, 5.0) * 10 + self.heading_gain * heading_error
            overlay = float(np.clip(overlay, -self.max_overlay, self.max_overlay))
        self.signals = {"lateral_error": proj.lateral_error, "distance_to_line": distance_to_line,
                        "lka_active": float(self.active), "lka_overlay": overlay, "driver_steer": driver}
        return clip_steer(driver + overlay, self.config)
