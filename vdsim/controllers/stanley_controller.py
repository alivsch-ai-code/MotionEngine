"""Stanley path-tracking controller (Hoffmann et al. 2007) with curvature feedforward.

Heading error is taken between the path tangent and the velocity direction at the CG
(yaw + side slip), so steady-state cornering needs no cross-track error; the feedforward
covers the steady-state steering angle including understeer (L kappa + EG v^2 kappa).
"""

import numpy as np

from ..core.interfaces import LateralController
from ..core.registry import register
from .esp_controller import understeer_gradient
from .path_tracking import axle_point, clip_steer, wrap


@register("lateral_controller", "stanley")
class StanleyController(LateralController):
    label = "Stanley"

    def __init__(self, config, gain=1.2, softening=2.0, yaw_damping=0.05, feedforward=True):
        self.config = config
        self.gain, self.softening, self.yaw_damping, self.feedforward = gain, softening, yaw_damping, feedforward
        self.eg = understeer_gradient(config)
        self.signals = {}
        self.reset()

    def reset(self):
        self._hint = 0
        self._hint_cg = 0

    def steer(self, t, state, ref):
        p = self.config.vehicle
        fx, fy = axle_point(state, p.cg_to_front)
        front = ref.project(fx, fy, hint=self._hint)
        self._hint = front.index
        cg = ref.project(state.x, state.y, hint=self._hint_cg)
        self._hint_cg = cg.index
        v = max(state.vx, 0.0)
        heading_error = wrap(cg.heading - (state.psi + state.beta))
        cross_term = np.arctan2(-self.gain * front.lateral_error, self.softening + v)
        delta_ff = np.arctan(p.wheelbase * cg.kappa) + self.eg * v**2 * cg.kappa if self.feedforward else 0.0
        damping = -self.yaw_damping * (state.r - v * cg.kappa)
        delta = heading_error + cross_term + delta_ff + damping
        self.signals = {"lateral_error_front": front.lateral_error, "heading_error": heading_error, "s": cg.s}
        return clip_steer(delta, self.config)
