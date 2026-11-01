"""Brush tire model with parabolic pressure distribution (Pacejka, Tyre and Vehicle Dynamics, ch. 3).

Theoretical slip:  sigma_x = kappa / (1 + kappa),  sigma_y = tan(alpha) / (1 + kappa)
Combined slip:     phi = sqrt((theta_x sigma_x)^2 + (theta_y sigma_y)^2),  theta = C / (3 mu Fz)
Force magnitude:   F = mu Fz (3 phi - 3 phi^2 + phi^3) for phi < 1, else mu Fz (full sliding)
Aligning moment:   Mz = -a mu Fz theta_y sigma_y (1 - phi)^3, contact half length a = 3 * trail
"""

import numpy as np

from ..core.interfaces import TireModel
from ..core.registry import register


@register("tire_model", "brush")
class BrushTire(TireModel):
    def __init__(self, cornering_stiffness, longitudinal_stiffness, nominal_load,
                 load_sensitivity_stiffness=2.0, load_sensitivity_mu=-0.1,
                 camber_stiffness=5000.0, pneumatic_trail=0.04, **_):
        self.c_alpha = cornering_stiffness
        self.c_kappa = longitudinal_stiffness
        self.fz0 = nominal_load
        self.p_ky2 = load_sensitivity_stiffness
        self.p_mu = load_sensitivity_mu
        self.camber_stiffness = camber_stiffness
        self.half_length = 3.0 * pneumatic_trail

    def forces(self, alpha, kappa, fz, mu=1.0, camber=0.0):
        fz = np.maximum(fz, 0.0)
        mu_eff = mu * np.maximum(1.0 + self.p_mu * (fz - self.fz0) / self.fz0, 0.2)
        shape = np.sin(2 * np.arctan(fz / (self.p_ky2 * self.fz0))) / np.sin(2 * np.arctan(1 / self.p_ky2))
        c_y = self.c_alpha * shape + 1e-9
        c_x = self.c_kappa * fz / self.fz0 + 1e-9
        limit = mu_eff * fz + 1e-9

        alpha_eff = alpha + self.camber_stiffness * (fz / self.fz0) * camber / c_y
        denom = np.maximum(1.0 + kappa, 1e-3)
        sx = kappa / denom
        sy = np.tan(alpha_eff) / denom
        theta_x = c_x / (3 * limit)
        theta_y = c_y / (3 * limit)
        phi = np.hypot(theta_x * sx, theta_y * sy)

        phi_c = np.minimum(phi, 1.0)
        magnitude = limit * (3 * phi_c - 3 * phi_c**2 + phi_c**3)
        safe_phi = np.maximum(phi, 1e-12)
        fx = magnitude * theta_x * sx / safe_phi
        fy = magnitude * theta_y * sy / safe_phi
        mz = -self.half_length * limit * theta_y * sy * (1 - phi_c) ** 3
        return fx, fy, mz
