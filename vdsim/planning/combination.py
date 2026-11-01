"""Combination of lateral and longitudinal candidates and the transformation into world coordinates.

Algorithm step 4 (Werling 2011, 3.5.5): every longitudinal candidate of a mode is combined with
every lateral candidate, the total cost follows (3.2) as J = k_lat J_d + k_lon J_s. The world
trajectories are computed lazily, in batches and in ascending cost order, with the closed-form
back transformation of appendix A.1 (ReferenceLine.to_cartesian), i.e. without numerical
differentiation:

    d(t) mode:  [s, s_dot, s_ddot, d, d_dot, d_ddot] -> (A.7), (A.8) -> d', d'' -> (A.1)-(A.6)
    d(s) mode:  [s, s_dot, s_ddot] and d(s(t)), d'(s(t)), d''(s(t)) -> (A.1)-(A.6) (no singularity at v = 0)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..framework.knowledge import trace
from ..geometry.reference_line import ReferenceLine, wrap_angle

ARC_EPS = 0.05     # m/s, guard of d' = d_dot / s_dot in the d(t) mode


@dataclass
class PlanningContext:
    # everything cost terms, constraints and collision checkers may need about the current cycle
    t: float = 0.0                    # current time
    t_start: float = 0.0              # start time of the new polynomials (t + t_comp)
    reference_line: object = None
    behavior: object = None
    prediction: object = None
    geometry: object = None
    vehicle: object = None
    reference_point: str = "cog"
    lateral_mode: str = "time"
    direction: int = 1
    d_ref: float = 0.0
    d_min: float = -1e9
    d_max: float = 1e9
    target_speed: float = 0.0
    t_grid: np.ndarray = field(default_factory=lambda: np.zeros(0))   # check horizon, relative to t_start
    dt: float = 0.1
    start: object = None              # StartState
    info: dict = field(default_factory=dict)


@trace("werling2011", section="A.1", equation="(A.7), (A.8)", concept="frenet_transformation",
       note="d' = d_dot/s_dot, d'' = (d_ddot - s_ddot d')/s_dot^2 mit Schutz bei s_dot -> 0")
def time_to_arc(s_d, s_dd, d_d, d_dd, eps=ARC_EPS):
    return ReferenceLine.time_to_arc(s_d, s_dd, d_d, d_dd, eps)


def frenet_to_world(reference_line, s, s_d, s_dd, d, d_p, d_pp):
    # vectorized A.1 on arrays of any shape
    shape = np.shape(s)
    flat = [np.ravel(np.asarray(a, dtype=float)) for a in (s, s_d, s_dd, d, d_p, d_pp)]
    out = reference_line.to_cartesian(*flat)
    return {k: np.reshape(v, shape) for k, v in out.items()}


class TrajectoryBatch:
    """B candidate trajectories sampled on the common check horizon (arrays of shape (B, K))."""

    def __init__(self, t, frenet, world, reference_line, ctx, lat_idx=None, lon_idx=None):
        self.t = np.asarray(t, dtype=float)                # absolute time (K,)
        self.t_rel = self.t - self.t[0]
        self.dt = float(self.t[1] - self.t[0]) if len(self.t) > 1 else 0.1
        for key in ("s", "s_d", "s_dd", "d", "d_d", "d_dd", "d_p", "d_pp"):
            setattr(self, key, frenet[key])
        for key in ("x", "y", "theta", "kappa", "v", "a"):
            setattr(self, key, world[key])
        self.reference_line = reference_line
        self.ctx = ctx
        self.lat_idx, self.lon_idx = lat_idx, lon_idx
        self._cache = {}

    def __len__(self):
        return self.x.shape[0]

    def subset(self, mask):
        # rows selected by a boolean mask or an index array
        out = TrajectoryBatch.__new__(TrajectoryBatch)
        out.t, out.t_rel, out.dt = self.t, self.t_rel, self.dt
        for key in ("s", "s_d", "s_dd", "d", "d_d", "d_dd", "d_p", "d_pp", "x", "y", "theta", "kappa", "v", "a"):
            setattr(out, key, getattr(self, key)[mask])
        out.reference_line, out.ctx = self.reference_line, self.ctx
        out.lat_idx = self.lat_idx[mask] if self.lat_idx is not None else None
        out.lon_idx = self.lon_idx[mask] if self.lon_idx is not None else None
        out._cache = {k: (tuple(a[mask] for a in v) if isinstance(v, tuple) else v[mask])
                      for k, v in self._cache.items()}
        return out

    @property
    def direction(self):
        return self.ctx.direction

    @property
    def psi(self):
        # vehicle orientation: zero side slip at the reference point (Werling 3.5.4), +pi when reversing
        return self.theta if self.ctx.direction > 0 else self.theta + np.pi

    @property
    def a_lat(self):
        return self.v * self.v * self.kappa

    def _grad(self, key, arr):
        if key not in self._cache:
            self._cache[key] = np.gradient(arr, self.dt, axis=1) if arr.shape[1] > 1 else np.zeros_like(arr)
        return self._cache[key]

    @property
    def jerk(self):
        return self._grad("jerk", self.a)

    @property
    def kappa_dot(self):
        return self._grad("kappa_dot", self.kappa)

    @property
    def reference(self):
        # (theta_r, kappa_r) of the foot points
        if "ref" not in self._cache:
            _, _, th, ka, _ = self.reference_line.evaluate(np.ravel(self.s))
            self._cache["ref"] = (np.reshape(th, self.s.shape), np.reshape(ka, self.s.shape))
        return self._cache["ref"]

    @property
    def heading_error(self):
        # vehicle axis relative to the road
        return wrap_angle(self.psi - self.reference[0])


class CandidateEvaluator:
    """Lazy evaluation of combined candidates (lateral index i, longitudinal index j)."""

    def __init__(self, reference_line, lat, lon, ctx):
        self.ref = reference_line
        self.lat, self.lon = lat, lon
        self.ctx = ctx
        self.t_abs = ctx.t_start + ctx.t_grid
        self._ref = None

    def frenet(self, i, j):
        lat, lon = self.lat, self.lon
        s, s_d, s_dd = lon.s[j], lon.sd[j], lon.sdd[j]
        if lat.mode == "arc":
            d, d_p, d_pp, _ = lat.poly.evaluate(np.maximum(s - lat.s0, 0.0), idx=i)
            d_d, d_dd = s_d * d_p, s_dd * d_p + s_d * s_d * d_pp
        else:
            d, d_d, d_dd = lat.d[i], lat.d1[i], lat.d2[i]
            d_p, d_pp = time_to_arc(s_d, s_dd, d_d, d_dd)
        return {"s": s, "s_d": s_d, "s_dd": s_dd, "d": d, "d_d": d_d, "d_dd": d_dd, "d_p": d_p, "d_pp": d_pp}

    @trace("werling2011", section="3.5.5", equation="(3.1), (3.2)", concept="candidate_combination",
           note="x(s(t), d(t)) = r(s(t)) + d(t) n_r(s(t)), lazy und vektorisiert in Batches")
    def batch(self, i, j):
        i = np.atleast_1d(i)
        j = np.atleast_1d(j)
        fr = self.frenet(i, j)
        world = frenet_to_world(self.ref, fr["s"], fr["s_d"], fr["s_dd"], fr["d"], fr["d_p"], fr["d_pp"])
        batch = TrajectoryBatch(self.t_abs, fr, world, self.ref, self.ctx, i, j)
        th, ka = self.reference_of_lon()
        batch._cache["ref"] = (th[j], ka[j])
        return batch

    def reference_of_lon(self):
        # theta_r, kappa_r at the foot points of all longitudinal candidates (evaluated once per set)
        if self._ref is None:
            _, _, th, ka, _ = self.ref.evaluate(np.ravel(self.lon.s))
            self._ref = (np.reshape(th, self.lon.s.shape), np.reshape(ka, self.lon.s.shape))
        return self._ref
