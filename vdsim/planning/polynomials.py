"""Optimal polynomials of the integrator chain (Werling 2011, section 3.4).

The lateral motion d(t) (or d(s)) and the longitudinal motion s(t) are both modeled as the
output xi1 of the integrator chain (3.3) whose input u = xi1''' is the jerk. Minimizing

    J = int_0^tau 1/2 u^2 dt + h(xi(tau), tau)                                   (3.4)

gives (Satz 1) quintic polynomials if the end state is fixed and (Satz 2) quartic polynomials
(c5 = 0) if the end position is free and h does not depend on xi1. The coefficients follow in
closed form from (3.8); the jerk integral is evaluated in closed form as well (algorithm step 3).

PolynomialSet holds N such polynomials together with their continuation on the target
manifold after the end time tau (section 3.6: the optimal trajectory continues on the manifold,
so it is valid on an infinite horizon).
"""

from __future__ import annotations

import numpy as np

from ..framework.knowledge import trace


# ----------------------------------------------------------------------------- coefficients (3.8)
@trace("werling2011", section="3.4", equation="(3.6)-(3.8)", concept="quintic_polynomial",
       note="Satz 1: geschlossene Koeffizienten c012 = M1(0)^-1 xi(0), c345 = M2(tau)^-1 [xi(tau) - M1(tau) c012]")
def quintic_coefficients(x0, v0, a0, x1, v1, a1, tau):
    # vectorized q012 / q345: start (x0, v0, a0), end (x1, v1, a1) at tau -> coefficients (..., 6), ascending
    x0, v0, a0, x1, v1, a1, tau = np.broadcast_arrays(*[np.asarray(v, dtype=float)
                                                        for v in (x0, v0, a0, x1, v1, a1, tau)])
    t2 = tau * tau
    t3 = t2 * tau
    dp = x1 - (x0 + v0 * tau + 0.5 * a0 * t2)
    dv = v1 - (v0 + a0 * tau)
    da = a1 - a0
    c3 = (10.0 * dp - 4.0 * dv * tau + 0.5 * da * t2) / t3
    c4 = (-15.0 * dp + 7.0 * dv * tau - da * t2) / (t3 * tau)
    c5 = (6.0 * dp - 3.0 * dv * tau + 0.5 * da * t2) / (t3 * t2)
    return np.stack([x0, v0, 0.5 * a0, c3, c4, c5], axis=-1)


@trace("werling2011", section="3.4", equation="(3.8)", concept="quartic_polynomial",
       note="Satz 2: c34 = q34(xi2(tau), xi3(tau)) bei freier Endposition, c5 = 0")
def quartic_coefficients(x0, v0, a0, v1, a1, tau):
    # vectorized q012 / q34: free end position -> coefficients (..., 6) with c5 = 0
    x0, v0, a0, v1, a1, tau = np.broadcast_arrays(*[np.asarray(v, dtype=float) for v in (x0, v0, a0, v1, a1, tau)])
    dv = v1 - (v0 + a0 * tau)
    da = a1 - a0
    c3 = (3.0 * dv - da * tau) / (3.0 * tau * tau)
    c4 = (-2.0 * dv + da * tau) / (4.0 * tau ** 3)
    return np.stack([x0, v0, 0.5 * a0, c3, c4, np.zeros_like(c3)], axis=-1)


def coefficient_matrices(tau):
    # M1(tau), M2(tau) of (3.7) (used by the analysis functions and the tests)
    t = float(tau)
    m1 = np.array([[1.0, t, t * t], [0.0, 1.0, 2 * t], [0.0, 0.0, 2.0]])
    m2 = np.array([[t ** 3, t ** 4, t ** 5], [3 * t * t, 4 * t ** 3, 5 * t ** 4], [6 * t, 12 * t * t, 20 * t ** 3]])
    return m1, m2


# ----------------------------------------------------------------------------- jerk integral (step 3)
@trace("werling2011", section="3.5.5", equation="(3.4)", concept="jerk_integral",
       note="Ruckintegral int_0^tau (6c3 + 24c4 t + 60c5 t^2)^2 dt in geschlossener Form")
def jerk_integral(coeffs, tau):
    # int_0^tau xi1'''(t)^2 dt (without the factor 1/2 of (3.4))
    c = np.asarray(coeffs, dtype=float)
    c3, c4, c5 = c[..., 3], c[..., 4], c[..., 5]
    t = np.asarray(tau, dtype=float)
    t2 = t * t
    t3 = t2 * t
    return (36.0 * c3 * c3 * t + 144.0 * c3 * c4 * t2 + (192.0 * c4 * c4 + 240.0 * c3 * c5) * t3
            + 720.0 * c4 * c5 * t2 * t2 + 720.0 * c5 * c5 * t3 * t2)


# ----------------------------------------------------------------------------- evaluation
def polyval(coeffs, t):
    # value and the first three derivatives; coeffs (n, 6), t (n, k) or (k,) -> 4 arrays (n, k)
    c = np.asarray(coeffs, dtype=float)
    t = np.asarray(t, dtype=float)
    if t.ndim == 1:
        t = t[None, :]
    c0, c1, c2, c3, c4, c5 = (c[:, i:i + 1] for i in range(6))
    p = c0 + t * (c1 + t * (c2 + t * (c3 + t * (c4 + t * c5))))
    p1 = c1 + t * (2 * c2 + t * (3 * c3 + t * (4 * c4 + t * 5 * c5)))
    p2 = 2 * c2 + t * (6 * c3 + t * (12 * c4 + t * 20 * c5))
    p3 = 6 * c3 + t * (24 * c4 + t * 60 * c5)
    return p, p1, p2, p3


class ConstantReference:
    # reference trajectory xi_ref(t) = value (lateral d_ref, stopping position)
    kind = "constant"

    def __init__(self, value=0.0):
        self.value = float(value)

    def state(self, t_abs):
        t = np.asarray(t_abs, dtype=float)
        return np.full_like(t, self.value), np.zeros_like(t), np.zeros_like(t)

    def to_dict(self):
        return {"kind": self.kind, "value": self.value}


class PolynomialSet:
    """N optimal polynomials xi1 on [0, tau_i] plus their continuation on the target manifold.

    continuation "reference": xi1(t) = xi_ref(t) + offset_i after tau_i  (quintic, Tab. 3.1 d(t), s(t))
    continuation "velocity" : xi2(t) = xi2(tau_i) = const after tau_i     (quartic, Tab. 3.1 s_dot(t))

    The argument of evaluate() is the running variable relative to the start (time t - t0 for
    d(t)/s(t), arc length s - s0 for d(s)); `reference.state()` receives the absolute value
    t0 + t_rel, so following/merging references (functions of the absolute time) continue exactly.
    """

    def __init__(self, coeffs, tau, continuation="reference", reference=None, offset=None, t0=0.0):
        self.coeffs = np.atleast_2d(np.asarray(coeffs, dtype=float))
        self.tau = np.atleast_1d(np.asarray(tau, dtype=float))
        self.continuation = continuation
        self.reference = reference if reference is not None else ConstantReference(0.0)
        n = len(self.tau)
        self.offset = np.zeros(n) if offset is None else np.broadcast_to(np.asarray(offset, dtype=float), (n,)).copy()
        self.t0 = float(t0)
        if continuation == "velocity":
            p, v, _, _ = polyval(self.coeffs, self.tau[:, None])
            self._end_pos, self._end_vel = p[:, 0], v[:, 0]

    def __len__(self):
        return len(self.tau)

    def take(self, idx):
        idx = np.atleast_1d(idx)
        return PolynomialSet(self.coeffs[idx], self.tau[idx], self.continuation, self.reference, self.offset[idx],
                             self.t0)

    def evaluate(self, t_rel, idx=None):
        # (p, p', p'', p''') arrays (n, k); t_rel shape (k,) shared or (n, k) per row
        coeffs, tau, offset = self.coeffs, self.tau, self.offset
        if idx is not None:
            coeffs, tau, offset = coeffs[idx], tau[idx], offset[idx]
        t = np.asarray(t_rel, dtype=float)
        if t.ndim == 1:
            t = np.broadcast_to(t[None, :], (len(tau), len(t)))
        tc = np.minimum(t, tau[:, None])
        p, p1, p2, p3 = polyval(coeffs, tc)
        after = t > tau[:, None]
        if np.any(after):
            if self.continuation == "velocity":
                end_pos = self._end_pos if idx is None else self._end_pos[idx]
                end_vel = self._end_vel if idx is None else self._end_vel[idx]
                ep = np.broadcast_to(end_pos[:, None], t.shape)
                ev = np.broadcast_to(end_vel[:, None], t.shape)
                dt = t - tau[:, None]
                p = np.where(after, ep + ev * dt, p)
                p1 = np.where(after, ev, p1)
                p2 = np.where(after, 0.0, p2)
            else:
                rp, rv, ra = self.reference.state(self.t0 + t)
                p = np.where(after, rp + offset[:, None], p)
                p1 = np.where(after, rv, p1)
                p2 = np.where(after, ra, p2)
            p3 = np.where(after, 0.0, p3)
        return p, p1, p2, p3
