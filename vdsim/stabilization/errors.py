"""Invariant tracking errors in the Frenet frame of the desired trajectory (Werling 4.1.3, 4.2, 4.3).

    rear_axle_errors          (4.9)    e_t, e_n, e_psi, kappa_delta of the rear-axle center
    rear_axle_error_rates     (4.10a-c) time derivatives (Remark 6: evaluated, not differentiated)
    taylor_terms              (A.10)-(A.13) series of (cos x - 1)/x, sin x / x and their derivatives
    series_terms              exact expressions away from 0, Taylor series near 0 (Remark 5)
    flat_reference_transform  (4.20)-(4.24) flatness based transformation to a point lambda ahead
    center_errors             (4.25) errors of the geometric vehicle center
    frenet_errors             (4.48), (4.58), (4.59) generic point errors and their rates
"""

from __future__ import annotations

import math

from ..framework.knowledge import trace
from .common import wrap


@trace("werling2011", section="4.2.3.1", equation="(4.9)", concept="invariant_tracking_error")
def rear_axle_errors(y1, y2, psi, delta, y1_d, y2_d, psi_d, l):
    c, s = math.cos(psi_d), math.sin(psi_d)
    dx, dy = y1 - y1_d, y2 - y2_d
    return c * dx + s * dy, -s * dx + c * dy, wrap(psi - psi_d), math.tan(delta) / l


@trace("werling2011", section="4.2.3.1", equation="(4.10a)-(4.10c)", concept="invariant_tracking_error")
def rear_axle_error_rates(e_t, e_n, e_psi, v, kappa_delta, v_d, kappa_d):
    return (v * math.cos(e_psi) - v_d * (1.0 - kappa_d * e_n),
            v * math.sin(e_psi) - v_d * kappa_d * e_t,
            v * kappa_delta - v_d * kappa_d)


@trace("werling2011", section="A.3", equation="(A.10)-(A.13)", concept="lyapunov_orientation")
def taylor_terms(x):
    # (cos x - 1)/x, sin x / x, d/dx (cos x - 1)/x, d/dx sin x / x  (Taylor series, Werling A.3)
    x2 = x * x
    return (-x / 2 + x * x2 / 24 - x * x2 * x2 / 720,
            1 - x2 / 6 + x2 * x2 / 120 - x2 * x2 * x2 / 5040,
            -0.5 + x2 / 8 - x2 * x2 / 144 + x2 * x2 * x2 / 5760,
            -x / 3 + x * x2 / 30 - x * x2 * x2 / 840)


def series_terms(x, switch=0.5):
    # removable singularities (Remark 5): Taylor series for |x| < switch, exact expressions otherwise
    if abs(x) < switch:
        return taylor_terms(x)
    c, s = math.cos(x), math.sin(x)
    return (c - 1) / x, s / x, (-x * s - (c - 1)) / (x * x), (x * c - s) / (x * x)


@trace("werling2011", section="4.2.4.1", equation="(4.20)-(4.24)", concept="flat_reference_transform")
def flat_reference_transform(y1_d, y2_d, psi_d, kappa_d, kappa_d_dot, kappa_d_prime, v_d, v_d_dot, lam):
    """Desired motion of the point lambda ahead of the rear axle (Satz 5, proof in A.4).

    Returns y1, y2, theta (course), v, v_dot, kappa of the transformed reference.
    """
    q = math.sqrt(1.0 + (lam * kappa_d) ** 2)
    return {"y1": y1_d + lam * math.cos(psi_d), "y2": y2_d + lam * math.sin(psi_d),        # (4.20)
            "v": v_d * q,                                                               # (4.21)
            "theta": psi_d + math.atan(lam * kappa_d),                                  # (4.22)
            "v_dot": v_d_dot * q + v_d * lam**2 * kappa_d * kappa_d_dot / q,            # (4.23)
            "kappa": kappa_d / q + lam * kappa_d_prime / q**3}                          # (4.24)


@trace("werling2011", section="4.2.4.2", equation="(4.25)", concept="lyapunov_center")
def center_errors(x1, x2, psi, v, delta, ref, lam, l):
    # errors of the point lambda ahead of the rear axle w.r.t. the transformed reference `ref`
    yt1, yt2 = x1 + lam * math.cos(psi), x2 + lam * math.sin(psi)
    c, s = math.cos(ref["theta"]), math.sin(ref["theta"])
    dx, dy = yt1 - ref["y1"], yt2 - ref["y2"]
    beta_t = math.atan(lam / l * math.tan(delta))
    return {"e_t": c * dx + s * dy, "e_n": -s * dx + c * dy, "e_theta": wrap(psi + beta_t - ref["theta"]),
            "v": v * math.sqrt(1.0 + (lam / l * math.tan(delta)) ** 2), "beta": beta_t, "x": yt1, "y": yt2}


@trace("werling2011", section="4.3.3.1", equation="(4.48), (4.58), (4.59)", concept="invariant_tracking_error")
def frenet_errors(px, py, course, speed, ref_x, ref_y, ref_theta, ref_v, ref_kappa):
    # errors of a moving point (position, course, speed) w.r.t. a reference point and their rates
    c, s = math.cos(ref_theta), math.sin(ref_theta)
    dx, dy = px - ref_x, py - ref_y
    e_t, e_n = c * dx + s * dy, -s * dx + c * dy
    e_th = wrap(course - ref_theta)
    return {"e_t": e_t, "e_n": e_n, "e_theta": e_th,
            "e_t_dot": speed * math.cos(e_th) - ref_v * (1.0 - ref_kappa * e_n),
            "e_n_dot": speed * math.sin(e_th) - ref_v * ref_kappa * e_t}
