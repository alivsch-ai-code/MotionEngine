"""Lateral candidate sets (Werling 2011, 3.5.1, Tab. 3.1 row d(t)).

    d(t)  fast driving: quintic polynomials over time,
          end state q345(d_ref + delta_i, 0, 0, tau_j), end cost k_tau tau_j + 1/2 k_delta delta_i^2
    d(s)  slow driving: quintic polynomials over the arc length of the foot point. Dot quantities
          become prime quantities, k_tau tau becomes k_s [s(tau) - s(0)] and the cost integral runs
          over s; the motion follows from d(t) = d(s(t)), so lateral motion only happens while
          the vehicle moves along the road (non-holonomic constraint at low speed).

Lane changes: the reference curve is the center of the target lane (BehaviorCommand.reference_line),
d_ref shifts the target offset and [d_min, d_max] is the box restriction of the corridor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..framework.knowledge import trace
from .polynomials import ConstantReference, PolynomialSet, jerk_integral, quintic_coefficients
from .sampling import end_grid, offsets


@dataclass
class LateralSet:
    mode: str                      # "time" = d(t), "arc" = d(s)
    poly: PolynomialSet
    delta: np.ndarray              # end offsets relative to d_ref
    tau: np.ndarray                # durations (s) or arc lengths (m)
    k: np.ndarray                  # absolute grid index of the end time / end position
    target: np.ndarray             # d_ref + delta
    jerk: np.ndarray               # int u^2 (closed form, without 1/2)
    t0: float                      # absolute start time
    s0: float                      # start arc length (d(s) mode)
    d_ref: float
    grid: np.ndarray               # evaluation grid relative to the start (t or s)
    d: np.ndarray                  # (n, k) values on the grid
    d1: np.ndarray                 # d_dot (time) or d' (arc)
    d2: np.ndarray                 # d_ddot (time) or d'' (arc)
    feasible: np.ndarray           # passed the Frenet pre-filter
    costs: dict = field(default_factory=dict)   # cost term name -> (n,) weighted values
    total: np.ndarray = None

    def __len__(self):
        return len(self.tau)


def lateral_targets(d_ref, d_step, d_range, d_min, d_max, half_width):
    # delta_i relative to d_ref, pruned to end positions whose footprint fits into the corridor
    deltas = offsets(d_step, -d_range, d_range)
    lo, hi = d_min + half_width, d_max - half_width
    ok = (d_ref + deltas >= lo - 1e-9) & (d_ref + deltas <= hi + 1e-9)
    if not np.any(ok):
        # corridor narrower than the vehicle: keep the offset closest to the corridor center
        center = 0.5 * (max(d_min, -1e6) + min(d_max, 1e6))
        return deltas[[int(np.argmin(np.abs(d_ref + deltas - center)))]]
    return deltas[ok]


@trace("werling2011", section="3.5.1", equation="Tab. 3.1", concept="lateral_sampling",
       note="d(t): delta_i x tau_j, q345(d_ref + delta_i, 0, 0, tau_j); d(s): Strichgrößen, k_s [s(tau)-s(0)]")
def build_lateral_set(start, mode, t_start, d_ref, d_min, d_max, half_width, sampling, grid, keep_k=None,
                      prefilter_limit=np.inf):
    # start: FrenetState-like (d, d_d, d_dd, d_p, d_pp, s); grid: evaluation grid (t_rel or s_rel)
    if mode == "arc":
        g = end_grid(start.s, sampling.arc_s_step, sampling.arc_s_min, sampling.arc_s_max, sampling.absolute_grid,
                     keep_k)
        x0, x1, x2 = start.d, start.d_p, start.d_pp
        origin = start.s
    else:
        g = end_grid(t_start, sampling.lat_tau_step, sampling.lat_tau_min, sampling.lat_tau_max,
                     sampling.absolute_grid, keep_k)
        x0, x1, x2 = start.d, start.d_d, start.d_dd
        origin = t_start
    deltas = lateral_targets(d_ref, sampling.lat_d_step, sampling.lat_d_range, d_min, d_max, half_width)
    dd, tt = np.meshgrid(deltas, g.tau, indexing="ij")
    kk = np.broadcast_to(g.k[None, :], dd.shape)
    delta, tau, k = dd.ravel(), tt.ravel(), kk.ravel().copy()
    target = d_ref + delta
    coeffs = quintic_coefficients(x0, x1, x2, target, 0.0, 0.0, tau)
    poly = PolynomialSet(coeffs, tau, "reference", ConstantReference(d_ref), delta, origin)
    d, d1, d2, _ = poly.evaluate(grid)
    feasible = np.max(np.abs(d2), axis=1) <= prefilter_limit
    return LateralSet(mode=mode, poly=poly, delta=delta, tau=tau, k=k, target=target,
                      jerk=jerk_integral(coeffs, tau), t0=float(t_start), s0=float(start.s), d_ref=float(d_ref),
                      grid=np.asarray(grid, dtype=float), d=d, d1=d1, d2=d2, feasible=feasible)
