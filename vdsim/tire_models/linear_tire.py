"""Linear tire: forces proportional to slip and load, limited by the friction circle."""

import numpy as np

from ..core.interfaces import TireModel
from ..core.registry import register


@register("tire_model", "linear")
class LinearTire(TireModel):
    def __init__(self, cornering_stiffness, longitudinal_stiffness, nominal_load,
                 camber_stiffness=0.0, pneumatic_trail=0.04, saturate=True, **_):
        self.cornering_stiffness = cornering_stiffness
        self.longitudinal_stiffness = longitudinal_stiffness
        self.nominal_load = nominal_load
        self.camber_stiffness = camber_stiffness
        self.pneumatic_trail = pneumatic_trail
        self.saturate = saturate

    def forces(self, alpha, kappa, fz, mu=1.0, camber=0.0):
        fz = np.maximum(fz, 0.0)
        load = fz / self.nominal_load
        fy = (self.cornering_stiffness * alpha + self.camber_stiffness * camber) * load
        fx = self.longitudinal_stiffness * kappa * load
        if self.saturate:
            scale = np.minimum(1.0, mu * fz / np.maximum(np.hypot(fx, fy), 1e-9))
            fx, fy = fx * scale, fy * scale
        return fx, fy, -self.pneumatic_trail * fy
