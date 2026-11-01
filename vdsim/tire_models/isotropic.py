"""Isotropic Pacejka tire (Werling 2011, 4.3.2) and its combined-slip inversion.

Slip vector s = [s_l, s_q] (longitudinal, lateral = sin(alpha)), the force acts exactly in the
direction of the slip (isotropic tire):

    F = A sin(B atan(C |s|)) s / |s|                                   (4.40)
    |F| = A sin(B atan(C |s|))                                         (4.42)
    c = A B C   cornering = longitudinal stiffness at s = 0            (4.41)

A is the peak force (mu * F_z), B the shape factor and C the stiffness factor. For B > 1 the
characteristic has its maximum at |s| = s_max = tan(pi / (2 B)) / C.

Combined slip with a prescribed longitudinal force F_l (the Werling plant and controllers use
F_l as input): the lateral force follows from the root of g(F_q) = 0 (4.43). Here the
equivalent root search over the longitudinal slip magnitude u = |s_l| is used,

    f(S) u / S = |F_l|,   S = sqrt(u^2 + s_q^2),   F_q = f(S) s_q / S,

which is monotone in u, free of the square-root singularity of (4.43) and needs no inverse
of the characteristic. Two saturation treatments:

    "plateau"   |F| = A for S >= s_max (Kamm's circle, used by the plant model)
    "modified"  f(S) [1 + tan(pi/2 (S/s_max)^n)]  (Werling footnote 17: vertical asymptote at
                the maximum, so the characteristic can always be inverted; used by the controller)

The scalar functions use the math module (fast in the controller loop); the TireModel class is
vectorized for the generic vehicle models.
"""

import math

import numpy as np

from ..core.interfaces import TireModel
from ..core.registry import register
from ..framework.knowledge import trace


def peak_slip(B, C):
    # slip magnitude of the force maximum, B atan(C s) = pi/2 (infinite for B <= 1)
    if B <= 1.0 or C <= 0.0:
        return math.inf
    return math.tan(math.pi / (2.0 * B)) / C


def _f(S, A, B, C):
    return A * math.sin(B * math.atan(C * S))


def _df(S, A, B, C):
    return A * math.cos(B * math.atan(C * S)) * B * C / (1.0 + (C * S) ** 2)


def _mod(S, s_max, n):
    # saturation factor [1 + tan(pi/2 (S/s_max)^n)] and its derivative (footnote 17)
    x = S / s_max
    arg = 0.5 * math.pi * x ** n
    g = 1.0 + math.tan(arg)
    dg = 0.5 * math.pi * n * x ** (n - 1) / s_max / math.cos(arg) ** 2 if S > 0.0 else 0.0
    return g, dg


def saturation_factor(S, B, C, n=16):
    # factor [1 + tan(pi/2 (S/s_max)^n)] of the modified characteristic (inf at and beyond the peak)
    s_max = peak_slip(B, C)
    return _mod(S, s_max, n)[0] if S < s_max else math.inf


@trace("werling2011", section="4.3.2", equation="(4.42)", concept="isotropic_tire",
       note="mode='modified': Faktor [1+tan(pi/2 (|s|/s_max)^n)] nach Fußnote 17")
def force_magnitude(S, A, B, C, mode="plateau", n=16):
    # |F|(|s|) of the isotropic tire with the selected saturation treatment
    s_max = peak_slip(B, C)
    if mode == "plateau":
        return A if S >= s_max else _f(S, A, B, C)
    if mode == "modified":
        if S >= s_max:
            return math.inf
        return _f(S, A, B, C) * _mod(S, s_max, n)[0]
    return _f(S, A, B, C)


def _force_and_slope(S, A, B, C, mode, n, s_max):
    if mode == "modified":
        f, df = _f(S, A, B, C), _df(S, A, B, C)
        g, dg = _mod(S, s_max, n)
        return f * g, df * g + f * dg
    if mode == "plateau" and S >= s_max:
        return A, 0.0
    return _f(S, A, B, C), _df(S, A, B, C)


@trace("werling2011", section="4.3.2", equation="(4.43)", concept="isotropic_tire",
       note="äquivalente Nullstellensuche über den Längsschlupfbetrag statt über F_q")
def lateral_force(s_q, F_l, A, B, C, mode="plateau", n=16, tol=1e-10, max_iter=60):
    """Lateral force F_q of the isotropic tire for lateral slip s_q and longitudinal force F_l.

    Returns (F_q, S, saturated). In saturation (no solution of (4.43)) the force lies on Kamm's
    circle: F_q = sign(s_q) sqrt(A^2 - F_l^2).
    """
    if A <= 0.0:
        return 0.0, abs(s_q), True
    q, L = abs(s_q), abs(F_l)
    sign = 1.0 if s_q >= 0.0 else -1.0
    s_max = peak_slip(B, C)
    if L >= A:
        return 0.0, s_max, True
    circle = sign * math.sqrt(A * A - L * L)
    if q >= s_max:
        return circle, q, True
    if mode == "plateau" and L >= A * math.sqrt(1.0 - (q / s_max) ** 2):
        return circle, s_max, True
    if L == 0.0:
        S = q
        f = force_magnitude(S, A, B, C, mode, n)
        return sign * f if q > 0 else 0.0, S, False
    # monotone root search over u = |s_l| in [0, u_max)
    u_max = math.sqrt(max(s_max * s_max - q * q, 0.0)) if math.isfinite(s_max) else 1e3
    lo, hi = 0.0, u_max
    u = min(L / (A * B * C), 0.5 * u_max)
    for _ in range(max_iter):
        S = math.hypot(u, q)
        f, df = _force_and_slope(S, A, B, C, mode, n, s_max)
        h = f * u / S - L
        if h > 0.0:
            hi = u
        else:
            lo = u
        if abs(h) <= tol * A:
            break
        dh = df * (u / S) ** 2 + f * q * q / S ** 3
        u_new = u - h / dh if dh > 0.0 else 0.5 * (lo + hi)
        if not (lo < u_new < hi):
            u_new = 0.5 * (lo + hi)
        if abs(u_new - u) < 1e-15:
            u = u_new
            break
        u = u_new
    S = math.hypot(u, q)
    f = force_magnitude(S, A, B, C, mode, n)
    return (f * s_q / S if S > 0.0 else 0.0), S, False


def slip_for_force(F, A, B, C):
    # inverse of the unmodified characteristic below the peak: |s|(|F|), |F| < A
    F = min(abs(F), A * (1.0 - 1e-12))
    return math.tan(math.asin(F / A) / B) / C


@register("tire_model", "isotropic")
class IsotropicPacejkaTire(TireModel):
    """Isotropic Magic Formula tire for the generic vehicle models (per wheel, vectorized).

    A = mu F_z, B = shape factor, C = c_alpha / (F_z0 B) (cornering stiffness proportional to
    the load, identical in longitudinal and lateral direction). Longitudinal slip kappa and
    lateral slip sin(alpha) form the slip vector.
    """

    def __init__(self, cornering_stiffness, nominal_load, shape_lateral=1.3, pneumatic_trail=0.04, **_):
        self.c_alpha = np.asarray(cornering_stiffness, dtype=float)
        self.fz0 = nominal_load
        self.B = shape_lateral
        self.trail = pneumatic_trail

    def forces(self, alpha, kappa, fz, mu=1.0, camber=0.0):
        fz = np.maximum(fz, 0.0)
        A = mu * fz + 1e-9
        C = self.c_alpha / (self.fz0 * np.maximum(mu, 1e-3) * self.B)
        s_l = np.asarray(kappa, dtype=float)
        s_q = np.sin(alpha)
        S = np.hypot(s_l, s_q)
        F = A * np.sin(self.B * np.arctan(C * S))
        scale = np.where(S > 1e-12, F / np.maximum(S, 1e-12), A * self.B * C)
        fx, fy = scale * s_l, scale * s_q
        trail = self.trail * np.cos(1.2 * np.arctan(C * self.B * np.abs(alpha)))
        return fx, fy, -trail * fy
