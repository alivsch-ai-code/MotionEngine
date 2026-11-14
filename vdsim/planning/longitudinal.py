"""Longitudinal operating modes and candidate sets (Werling 2011, 3.5.2, Tab. 3.1).

    velocity   s_dot(t): quartic polynomials q34(s_dot_ref + nu_i, 0, tau_j)          (Satz 2)
               end cost k_tau tau_j + 1/2 k_nu nu_i^2
    following  s(t): s_ref = s_v - [k0 + kv s_dot_v], s_dot_ref = s_dot_v - kv s_ddot_v,
               s_ddot_ref = s_ddot_v, leader predicted with constant acceleration
    merging    s(t): s_ref = 1/2 [s_a + s_b]  (3.15), center of the gap between two vehicles
    stopping   s(t): s_ref = s_stop, s_dot_ref = s_ddot_ref = 0
    position modes: q345(s_ref(tau_j) + sigma_i, s_dot_ref(tau_j), s_ddot_ref(tau_j), tau_j),
               end cost k_tau tau_j + 1/2 k_sigma sigma_i^2

Geometry: s of the planner is the foot point of the trajectory reference point (CoG or rear
axle). Gaps are measured bumper to bumper, the stop position refers to the vehicle end leading
in the direction of motion (front bumper when driving forward).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..core.parameters import param
from ..framework.knowledge import trace
from .polynomials import PolynomialSet, jerk_integral, quartic_coefficients, quintic_coefficients
from .sampling import EndGrid, end_grid, nearest, offsets, open_edges


@dataclass
class LongitudinalParams:
    k0: float = param(5.0, "m", "Folgen: Mindestabstand k0 (Stoßstange zu Stoßstange)", min=0.0, max=50.0)
    kv: float = param(1.5, "s", "Folgen: Zeitlücke kv", min=0.0, max=5.0)
    prediction_window: float = param(1.0, "s", "Schätzfenster s, ṡ, s̈ der Objekte", min=0.1, max=5.0)
    v_max: float = param(60.0, "m/s", "Max. Geschwindigkeit (Vorfilter)", min=1.0, max=100.0)


# ----------------------------------------------------------------------------- reference motions
class ObjectMotion:
    # 1d motion along the reference curve with constant acceleration, clamped at standstill
    def __init__(self, s0, v0, a0, t0, length=4.5, obj_id=None):
        self.s0, self.v0, self.a0, self.t0 = float(s0), float(v0), float(a0), float(t0)
        self.length = float(length)
        self.id = obj_id
        if self.v0 <= 0.0 and self.a0 <= 0.0:
            self.v0, self.a0, self.t_stop = 0.0, 0.0, -np.inf
        elif self.a0 < 0.0:
            self.t_stop = self.v0 / -self.a0
        else:
            self.t_stop = np.inf

    @trace("werling2011", section="3.5.2", concept="following_mode",
           note="s_v(t) = s_v(0) + s_dot_v(0) t + 1/2 s_ddot_v(0) t^2, nach Stillstand geklemmt")
    def state(self, t_abs):
        t = np.asarray(t_abs, dtype=float) - self.t0
        tc = np.minimum(t, self.t_stop) if np.isfinite(self.t_stop) else t
        s = self.s0 + self.v0 * tc + 0.5 * self.a0 * tc * tc
        v = self.v0 + self.a0 * tc
        a = np.where(t < self.t_stop, self.a0, 0.0)
        return s, v, np.broadcast_to(a, np.shape(s)).astype(float)


class VelocityTarget:
    kind = "velocity"

    def __init__(self, v_ref):
        self.v_ref = max(float(v_ref), 0.0)

    def to_dict(self):
        return {"kind": self.kind, "v_ref": self.v_ref}


class StoppingTarget:
    kind = "stopping"

    def __init__(self, s_stop, leading_extent):
        self.s_stop = float(s_stop)
        self.leading_extent = float(leading_extent)
        self.value = self.s_stop - self.leading_extent

    def state(self, t_abs):
        t = np.asarray(t_abs, dtype=float)
        return np.full_like(t, self.value), np.zeros_like(t), np.zeros_like(t)

    def to_dict(self):
        return {"kind": self.kind, "s_stop": self.s_stop, "s_ref": self.value}


class FollowingTarget:
    kind = "following"

    def __init__(self, lead, k0, kv, leading_extent):
        self.lead, self.k0, self.kv = lead, float(k0), float(kv)
        # bumper to bumper: rear bumper of the leader minus the front extent of the ego vehicle
        self.offset = 0.5 * lead.length + float(leading_extent)

    @trace("werling2011", section="3.5.2", equation="s_ref = s_v - [k0 + kv s_dot_v]", concept="following_mode",
           note="geschwindigkeitsabhängiger Sollabstand; s_dot_ref = s_dot_v - kv s_ddot_v, s_ddot_ref = s_ddot_v")
    def state(self, t_abs):
        sv, vv, av = self.lead.state(t_abs)
        return sv - self.offset - (self.k0 + self.kv * vv), vv - self.kv * av, av

    def to_dict(self):
        return {"kind": self.kind, "lead_id": self.lead.id, "k0": self.k0, "kv": self.kv,
                "s_v": self.lead.s0, "v_v": self.lead.v0, "a_v": self.lead.a0}


class MergingTarget:
    kind = "merging"

    def __init__(self, front, rear, center_offset):
        self.front, self.rear = front, rear
        self.center_offset = float(center_offset)

    @trace("werling2011", section="3.5.2", equation="(3.15)", concept="merging_mode",
           note="s_ref = 1/2 [s_a + s_b] (Lückenmitte, Stoßstangen); Ego-Mitte auf der Lückenmitte")
    def state(self, t_abs):
        sa, va, aa = self.front.state(t_abs)
        sb, vb, ab = self.rear.state(t_abs)
        mid = 0.5 * ((sa - 0.5 * self.front.length) + (sb + 0.5 * self.rear.length))
        return mid - self.center_offset, 0.5 * (va + vb), 0.5 * (aa + ab)

    def to_dict(self):
        return {"kind": self.kind, "front_id": self.front.id, "rear_id": self.rear.id}


# ----------------------------------------------------------------------------- object projection
def object_motion(obj, reference_line, t_start, lane_id=None, window=1.0):
    # Frenet motion (s, s_dot, s_ddot at t_start) of a predicted object along the reference curve.
    # PredictedObject.s is used if given and its lane matches, otherwise the predicted (x, y)
    # samples are projected onto the curve (Werling 3.5.2: s_v(t)).
    t = np.asarray(obj.t, dtype=float)
    if len(t) == 0:
        return None
    if obj.s is not None and len(obj.s) == len(t) and (lane_id is None or obj.lane_id == lane_id):
        s = np.asarray(obj.s, dtype=float)
    else:
        s, _ = reference_line.project_many(obj.x, obj.y)
    if len(t) == 1:
        th = reference_line.evaluate(float(s[0]))[2]
        v0 = float(obj.v[0] * np.cos(obj.psi[0] - th)) if len(obj.v) else 0.0
        return ObjectMotion(s[0], v0, 0.0, t_start, obj.length, obj.id)
    sel = (t >= t_start - 0.5) & (t <= t_start + window + 1e-9)
    if np.count_nonzero(sel) < 2:
        # outside the prediction horizon: nearest two samples
        i = int(np.clip(np.searchsorted(t, t_start), 1, len(t) - 1))
        sel = np.zeros(len(t), dtype=bool)
        sel[i - 1:i + 1] = True
    tt, ss = t[sel] - t_start, s[sel]
    deg = 2 if len(tt) >= 3 else 1
    c = np.polyfit(tt, ss, deg)
    if deg == 2:
        a0, v0, s0 = 2.0 * c[0], c[1], c[2]
    else:
        a0, v0, s0 = 0.0, c[0], c[1]
    if obj.s_dot is not None and obj.s is not None and len(obj.s_dot) == len(t) and np.array_equal(s, obj.s):
        v0 = float(np.interp(t_start, t, obj.s_dot))
    speeds = np.asarray(obj.v, dtype=float)
    if len(speeds) == len(t) and np.max(np.abs(speeds[sel])) < 0.05:
        v0, a0 = 0.0, 0.0
    return ObjectMotion(s0, v0, a0, t_start, obj.length, obj.id)


# ----------------------------------------------------------------------------- candidate sets
@dataclass
class LongitudinalSet:
    kind: str                       # velocity / following / merging / stopping
    label: str                      # display name of the mode
    target: object
    poly: PolynomialSet
    offset: np.ndarray              # sigma_i (position modes) or nu_i (velocity)
    tau: np.ndarray
    k: np.ndarray                   # absolute grid index
    jerk: np.ndarray                # int u^2 (closed form)
    t0: float
    grid: np.ndarray                # t_rel
    s: np.ndarray                   # (n, k)
    sd: np.ndarray
    sdd: np.ndarray
    feasible: np.ndarray
    info: dict = field(default_factory=dict)
    costs: dict = field(default_factory=dict)
    total: np.ndarray = None

    def __len__(self):
        return len(self.tau)


def _prefilter(sd, sdd, limits):
    a_min, a_max, v_max = limits
    return (np.min(sd, axis=1) >= -0.05) & (np.max(sd, axis=1) <= v_max) & \
        (np.min(sdd, axis=1) >= a_min) & (np.max(sdd, axis=1) <= a_max)


@trace("werling2011", section="3.5.2", equation="Tab. 3.1", concept="longitudinal_sampling",
       note="s(t): sigma_i x tau_j, q345(s_ref(tau_j)+sigma_i, s_dot_ref(tau_j), s_ddot_ref(tau_j)); s_dot(t): q34")
def build_longitudinal_set(start, target, t_start, sampling, grid, keep_k=None, limits=(-np.inf, np.inf, np.inf),
                           label=None, focus=None):
    # focus: optional (offset, tau, n_offset, n_tau, include), see build_lateral_set
    g = end_grid(t_start, sampling.lon_tau_step, sampling.lon_tau_min, sampling.lon_tau_max, sampling.absolute_grid,
                 keep_k)
    edges = {}
    if focus is not None:
        keep = np.sort(np.argsort(np.abs(g.tau - focus[1]), kind="stable")[:max(int(focus[3]), 1)])
        if keep_k is not None and int(keep_k) in set(g.k.tolist()):
            keep = np.union1d(keep, np.flatnonzero(g.k == int(keep_k)))
        edges["tau"] = open_edges(g.tau, g.tau[keep])
        g = EndGrid(g.tau[keep], g.k[keep], g.absolute)
    s0, v0, a0 = start.s, start.s_d, start.s_dd
    if target.kind == "velocity":
        nus = offsets(sampling.lon_nu_step, -sampling.lon_nu_range, sampling.lon_nu_range)
        nus = nus[target.v_ref + nus >= -1e-9]
        if sampling.lon_nu_coarse_step > 0:
            # coarse end speeds between standstill and the fine grid: the velocity mode can adapt to slower
            # traffic instead of offering only stop candidates (relevant for the replacement strategy)
            low = np.arange(-sampling.lon_nu_range - sampling.lon_nu_coarse_step, -target.v_ref - 1e-9,
                            -sampling.lon_nu_coarse_step)
            nus = np.unique(np.concatenate([nus, low]))
        if sampling.include_stop_candidates and target.v_ref > 0:
            nus = np.unique(np.append(nus, -target.v_ref))
        if focus is not None:
            local = nearest(nus, focus[0], focus[2], focus[4])
            edges["offset"] = open_edges(nus, local)
            nus = local
        oo, tt = np.meshgrid(nus, g.tau, indexing="ij")
        kk = np.broadcast_to(g.k[None, :], oo.shape)
        off, tau, k = oo.ravel(), tt.ravel(), kk.ravel().copy()
        coeffs = quartic_coefficients(s0, v0, a0, np.maximum(target.v_ref + off, 0.0), 0.0, tau)
        poly = PolynomialSet(coeffs, tau, "velocity", None, off, t_start)
    else:
        upper = sampling.lon_sigma_range
        if target.kind == "stopping" and not sampling.stop_allow_overshoot:
            upper = 0.0
        sig = offsets(sampling.lon_sigma_step, -sampling.lon_sigma_range, upper)
        if focus is not None:
            local = nearest(sig, focus[0], focus[2], focus[4])
            edges["offset"] = open_edges(sig, local)
            sig = local
        oo, tt = np.meshgrid(sig, g.tau, indexing="ij")
        kk = np.broadcast_to(g.k[None, :], oo.shape)
        off, tau, k = oo.ravel(), tt.ravel(), kk.ravel().copy()
        rs, rv, ra = target.state(t_start + tau)
        coeffs = quintic_coefficients(s0, v0, a0, rs + off, rv, ra, tau)
        poly = PolynomialSet(coeffs, tau, "reference", target, off, t_start)
    s, sd, sdd, _ = poly.evaluate(grid)
    feasible = _prefilter(sd, sdd, limits)
    return LongitudinalSet(kind=target.kind, label=label or target.kind, target=target, poly=poly, offset=off,
                           tau=tau, k=k, jerk=jerk_integral(poly.coeffs, tau), t0=float(t_start),
                           grid=np.asarray(grid, dtype=float), s=s, sd=sd, sdd=sdd, feasible=feasible,
                           info={"open_edges": edges})


def make_target(mode, behavior, prediction, reference_line, t_start, geometry, reference_point, direction, lon_params):
    # LongitudinalMode -> target object (or (None, reason) if the mode cannot be realized)
    p = dict(mode.params or {})
    lane = behavior.lane_id
    if mode.kind == "velocity":
        return VelocityTarget(p.get("v_ref", behavior.target_speed)), ""
    if mode.kind == "stopping":
        if "s_stop" not in p:
            return None, "s_stop fehlt"
        return StoppingTarget(p["s_stop"], geometry.leading_extent(reference_point, direction)), ""

    def motion(obj_id):
        obj = prediction.by_id(obj_id) if prediction is not None else None
        if obj is None:
            return None
        return object_motion(obj, reference_line, t_start, lane, lon_params.prediction_window)

    if mode.kind == "following":
        lead = motion(p.get("lead_id"))
        if lead is None:
            return None, f"Vorderfahrzeug {p.get('lead_id')} nicht in der Prädiktion"
        return FollowingTarget(lead, p.get("k0", lon_params.k0), p.get("kv", lon_params.kv),
                               geometry.leading_extent(reference_point, direction)), ""
    if mode.kind == "merging":
        front, rear = motion(p.get("front_id")), motion(p.get("rear_id"))
        if front is None or rear is None:
            return None, "Lückenfahrzeuge nicht in der Prädiktion"
        return MergingTarget(front, rear, direction * geometry.center_offset(reference_point)), ""
    return None, f"unbekannter Längsmodus '{mode.kind}'"
