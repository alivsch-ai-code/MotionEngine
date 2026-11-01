"""Pacejka Magic Formula tire model (reduced parameter set).

Pure slip:      F = D sin(C atan(B s - E (B s - atan(B s))))
Peak:           D = mu(Fz) Fz,  mu(Fz) = mu (1 + p_mu dFz),  dFz = (Fz - Fz0) / Fz0
Stiffness:      K_alpha(Fz) degressive (Pacejka 2006: sin(2 atan(Fz / (p_Ky2 Fz0)))),
                K_kappa proportional to Fz,  B = K / (C D)
Camber:         camber thrust as an equivalent slip-angle shift
Combined slip:  cosine weighting functions G_xa = cos(atan(B_xa alpha)), G_yk = cos(atan(B_yk kappa))
Aligning moment: pneumatic trail decaying with slip angle
"""

import numpy as np

from ..core.interfaces import TireModel
from ..core.registry import register


def magic_formula(slip, B, C, D, E):
    bs = B * slip
    return D * np.sin(C * np.arctan(bs - E * (bs - np.arctan(bs))))


@register("tire_model", "pacejka")
class PacejkaTire(TireModel):
    def __init__(self, cornering_stiffness, longitudinal_stiffness, nominal_load,
                 shape_lateral=1.3, curvature_lateral=-0.5, shape_longitudinal=1.65, curvature_longitudinal=0.0,
                 combined_lateral_reduction=10.0, combined_longitudinal_reduction=12.0,
                 load_sensitivity_stiffness=2.0, load_sensitivity_mu=-0.1,
                 camber_stiffness=5000.0, pneumatic_trail=0.04, **_):
        self.c_alpha = cornering_stiffness
        self.c_kappa = longitudinal_stiffness
        self.fz0 = nominal_load
        self.C_y, self.E_y = shape_lateral, curvature_lateral
        self.C_x, self.E_x = shape_longitudinal, curvature_longitudinal
        self.B_yk = combined_lateral_reduction
        self.B_xa = combined_longitudinal_reduction
        self.p_ky2 = load_sensitivity_stiffness
        self.p_mu = load_sensitivity_mu
        self.camber_stiffness = camber_stiffness
        self.trail = pneumatic_trail
        self._norm = np.sin(2 * np.arctan(1 / self.p_ky2))

    def cornering_stiffness(self, fz):
        # Degressive load dependency, equals c_alpha at the nominal load
        shape = np.sin(2 * np.arctan(np.maximum(fz, 0.0) / (self.p_ky2 * self.fz0)))
        return self.c_alpha * shape / self._norm

    def friction(self, fz, mu=1.0):
        dfz = (np.maximum(fz, 0.0) - self.fz0) / self.fz0
        return mu * np.maximum(1.0 + self.p_mu * dfz, 0.2)

    def forces(self, alpha, kappa, fz, mu=1.0, camber=0.0):
        fz = np.maximum(fz, 0.0)
        D = self.friction(fz, mu) * fz + 1e-9
        k_y = self.cornering_stiffness(fz) + 1e-9
        k_x = self.c_kappa * fz / self.fz0 + 1e-9
        B_y = k_y / (self.C_y * D)
        B_x = k_x / (self.C_x * D)

        alpha_eff = alpha + self.camber_stiffness * (fz / self.fz0) * camber / k_y
        fy0 = magic_formula(alpha_eff, B_y, self.C_y, D, self.E_y)
        fx0 = magic_formula(kappa, B_x, self.C_x, D, self.E_x)

        fx = fx0 * np.cos(np.arctan(self.B_xa * alpha))
        fy = fy0 * np.cos(np.arctan(self.B_yk * kappa))
        trail = self.trail * np.cos(1.2 * np.arctan(B_y * alpha))
        return fx, fy, -trail * fy0
