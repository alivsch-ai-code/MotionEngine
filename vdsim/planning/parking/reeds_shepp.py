"""Reeds-Shepp paths: shortest paths of a car that drives forward and backward with a bounded curvature.

Reeds and Shepp (1990) showed that the shortest path between two poses of a car with minimum turning
radius R, which may reverse, is one of 48 words of at most five segments: arcs to the left (L), arcs to
the right (R) and straight lines (S), each driven forward (+) or backward (-), in the families
CSC, CCC, CCCC, CCSC, CCSCC. The formulas below follow the closed-form solutions of the paper as
corrected and organized by the OMPL implementation (Sucan, Moll and Kavraki 2012): every family is
solved for the base word and obtained for the other words by the symmetries "timeflip" (reverse all
directions: x -> -x, phi -> -phi) and "reflect" (swap left and right: y -> -y, phi -> -phi), and the CCC
and CCSC families also by "backwards" (traverse the word in reverse order).

All lengths are in units of R (arc angle for L/R, distance / R for S); the sign is the direction of
travel. `all_paths` returns every admissible word, `shortest_path` the shortest, and `sample` turns
a path into poses with the exact arc geometry, so the end pose matches the goal to rounding error.

References:
    J. A. Reeds, L. A. Shepp: Optimal paths for a car that goes both forwards and backwards.
        Pacific Journal of Mathematics 145(2), 1990.
    I. A. Sucan, M. Moll, L. E. Kavraki: The Open Motion Planning Library. IEEE RAM 19(4), 2012
        (ReedsSheppStateSpace).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

ZERO = 10 * np.finfo(float).eps
PI = math.pi
HALF_PI = 0.5 * math.pi

# segment types of the 18 base words (OMPL reedsSheppPathType); N = unused
_TYPES = [
    "LRL", "RLR", "LRLR", "RLRL", "LRSL", "RLSR", "LSRL", "RSLR", "LRSR", "RLSL",
    "RSRL", "LSLR", "LSR", "RSL", "LSL", "RSR", "LRSLR", "RLSRL",
]


@dataclass
class RSPath:
    """A Reeds-Shepp word: segment types and signed lengths (in units of the turning radius)."""
    types: str
    lengths: tuple[float, ...]
    radius: float = 1.0
    segments: list = field(default_factory=list)  # [(type, signed length in m)] without zero-length segments

    def __post_init__(self):
        self.segments = [(c, float(s) * self.radius) for c, s in zip(self.types, self.lengths, strict=True)
                         if abs(s) > 1e-10]

    @property
    def length(self) -> float:
        """Total path length in m."""
        return sum(abs(s) for _, s in self.segments)

    @property
    def cusps(self) -> int:
        """Number of direction changes (gear switches)."""
        signs = [1 if s > 0 else -1 for _, s in self.segments]
        return sum(1 for a, b in zip(signs, signs[1:], strict=False) if a != b)

    @property
    def reverse_length(self) -> float:
        return sum(-s for _, s in self.segments if s < 0)

    def word(self) -> str:
        return " ".join(f"{c}{'+' if s > 0 else '-'}" for c, s in self.segments)


def _mod2pi(x):
    v = math.fmod(x, 2 * PI)
    if v < -PI:
        v += 2 * PI
    elif v > PI:
        v -= 2 * PI
    return v


def _polar(x, y):
    return math.hypot(x, y), math.atan2(y, x)


def _tau_omega(u, v, xi, eta, phi):
    delta = _mod2pi(u - v)
    a = math.sin(u) - math.sin(delta)
    b = math.cos(u) - math.cos(delta) - 1.0
    t1 = math.atan2(eta * a - xi * b, xi * a + eta * b)
    t2 = 2.0 * (math.cos(delta) - math.cos(v) - math.cos(u)) + 3.0
    tau = _mod2pi(t1 + PI) if t2 < 0 else _mod2pi(t1)
    omega = _mod2pi(tau - u + v - phi)
    return tau, omega


# ----------------------------------------------------------------------------- base words (Reeds-Shepp, 8.1 - 8.11)
def _lp_sp_lp(x, y, phi):  # 8.1
    u, t = _polar(x - math.sin(phi), y - 1.0 + math.cos(phi))
    if t >= -ZERO:
        v = _mod2pi(phi - t)
        if v >= -ZERO:
            return t, u, v
    return None


def _lp_sp_rp(x, y, phi):  # 8.2
    u1, t1 = _polar(x + math.sin(phi), y - 1.0 - math.cos(phi))
    u1 = u1 * u1
    if u1 >= 4.0:
        u = math.sqrt(u1 - 4.0)
        theta = math.atan2(2.0, u)
        t = _mod2pi(t1 + theta)
        v = _mod2pi(t - phi)
        if t >= -ZERO and v >= -ZERO:
            return t, u, v
    return None


def _lp_rm_l(x, y, phi):  # 8.3 / 8.4
    xi, eta = x - math.sin(phi), y - 1.0 + math.cos(phi)
    u1, theta = _polar(xi, eta)
    if u1 <= 4.0:
        u = -2.0 * math.asin(0.25 * u1)
        t = _mod2pi(theta + 0.5 * u + PI)
        v = _mod2pi(phi - t + u)
        if t >= -ZERO and u <= ZERO:
            return t, u, v
    return None


def _lp_rup_lum_rm(x, y, phi):  # 8.7
    xi, eta = x + math.sin(phi), y - 1.0 - math.cos(phi)
    rho = 0.25 * (2.0 + math.hypot(xi, eta))
    if rho <= 1.0:
        u = math.acos(rho)
        t, v = _tau_omega(u, -u, xi, eta, phi)
        if t >= -ZERO and v <= ZERO:
            return t, u, v
    return None


def _lp_rum_lum_rp(x, y, phi):  # 8.8
    xi, eta = x + math.sin(phi), y - 1.0 - math.cos(phi)
    rho = (20.0 - xi * xi - eta * eta) / 16.0
    if 0.0 <= rho <= 1.0:
        u = -math.acos(rho)
        if u >= -HALF_PI:
            t, v = _tau_omega(u, u, xi, eta, phi)
            if t >= -ZERO and v >= -ZERO:
                return t, u, v
    return None


def _lp_rm_sm_lm(x, y, phi):  # 8.9 (ends with a left arc: center of the final circle at x - sin, y - 1 + cos)
    xi, eta = x - math.sin(phi), y - 1.0 + math.cos(phi)
    rho, theta = _polar(xi, eta)
    if rho >= 2.0:
        r = math.sqrt(rho * rho - 4.0)
        u = 2.0 - r
        t = _mod2pi(theta + math.atan2(r, -2.0))
        v = _mod2pi(phi - HALF_PI - t)
        if t >= -ZERO and u <= ZERO and v <= ZERO:
            return t, u, v
    return None


def _lp_rm_sm_rm(x, y, phi):  # 8.10
    xi, eta = x + math.sin(phi), y - 1.0 - math.cos(phi)
    rho, theta = _polar(-eta, xi)
    if rho >= 2.0:
        t = theta
        u = 2.0 - rho
        v = _mod2pi(t + HALF_PI - phi)
        if t >= -ZERO and u <= ZERO and v <= ZERO:
            return t, u, v
    return None


def _lp_rm_slm_rp(x, y, phi):  # 8.11
    xi, eta = x + math.sin(phi), y - 1.0 - math.cos(phi)
    rho, _ = _polar(xi, eta)
    if rho >= 2.0:
        u = 4.0 - math.sqrt(rho * rho - 4.0)
        if u <= ZERO:
            t = _mod2pi(math.atan2((4.0 - u) * xi - 2.0 * eta, -2.0 * xi + (u - 4.0) * eta))
            v = _mod2pi(t - phi)
            if t >= -ZERO and v >= -ZERO:
                return t, u, v
    return None


# ----------------------------------------------------------------------------- families with symmetries
def _csc(x, y, phi, out):
    for fn, base, refl in ((_lp_sp_lp, 14, 15), (_lp_sp_rp, 12, 13)):
        r = fn(x, y, phi)
        if r:
            out.append((base, r))
        r = fn(-x, y, -phi)                      # timeflip
        if r:
            out.append((base, tuple(-a for a in r)))
        r = fn(x, -y, -phi)                      # reflect
        if r:
            out.append((refl, r))
        r = fn(-x, -y, phi)                      # timeflip + reflect
        if r:
            out.append((refl, tuple(-a for a in r)))


def _ccc(x, y, phi, out):
    for xx, yy, pp, typ, neg in ((x, y, phi, 0, False), (-x, y, -phi, 0, True), (x, -y, -phi, 1, False),
                                 (-x, -y, phi, 1, True)):
        r = _lp_rm_l(xx, yy, pp)
        if r:
            out.append((typ, tuple(-a for a in r) if neg else r))
    # backwards
    xb = x * math.cos(phi) + y * math.sin(phi)
    yb = x * math.sin(phi) - y * math.cos(phi)
    for xx, yy, pp, typ, neg in ((xb, yb, phi, 0, False), (-xb, yb, -phi, 0, True), (xb, -yb, -phi, 1, False),
                                 (-xb, -yb, phi, 1, True)):
        r = _lp_rm_l(xx, yy, pp)
        if r:
            t, u, v = r
            w = (v, u, t)
            out.append((typ, tuple(-a for a in w) if neg else w))


def _cccc(x, y, phi, out):
    for xx, yy, pp, typ, neg in ((x, y, phi, 2, False), (-x, y, -phi, 2, True), (x, -y, -phi, 3, False),
                                 (-x, -y, phi, 3, True)):
        r = _lp_rup_lum_rm(xx, yy, pp)
        if r:
            t, u, v = r
            w = (t, u, -u, v)
            out.append((typ, tuple(-a for a in w) if neg else w))
        r = _lp_rum_lum_rp(xx, yy, pp)
        if r:
            t, u, v = r
            w = (t, u, u, v)
            out.append((typ, tuple(-a for a in w) if neg else w))


def _ccsc(x, y, phi, out):
    for xx, yy, pp, k, neg in ((x, y, phi, 0, False), (-x, y, -phi, 0, True), (x, -y, -phi, 1, False),
                               (-x, -y, phi, 1, True)):
        r = _lp_rm_sm_lm(xx, yy, pp)
        if r:
            t, u, v = r
            w = (t, -HALF_PI, u, v)
            out.append((4 + k, tuple(-a for a in w) if neg else w))
        r = _lp_rm_sm_rm(xx, yy, pp)
        if r:
            t, u, v = r
            w = (t, -HALF_PI, u, v)
            out.append((8 + k, tuple(-a for a in w) if neg else w))
    xb = x * math.cos(phi) + y * math.sin(phi)
    yb = x * math.sin(phi) - y * math.cos(phi)
    for xx, yy, pp, k, neg in ((xb, yb, phi, 0, False), (-xb, yb, -phi, 0, True), (xb, -yb, -phi, 1, False),
                               (-xb, -yb, phi, 1, True)):
        r = _lp_rm_sm_lm(xx, yy, pp)
        if r:
            t, u, v = r
            w = (v, u, -HALF_PI, t)
            out.append((6 + k, tuple(-a for a in w) if neg else w))
        r = _lp_rm_sm_rm(xx, yy, pp)
        if r:
            t, u, v = r
            w = (v, u, -HALF_PI, t)
            out.append((10 + k, tuple(-a for a in w) if neg else w))


def _ccscc(x, y, phi, out):
    for xx, yy, pp, typ, neg in ((x, y, phi, 16, False), (-x, y, -phi, 16, True), (x, -y, -phi, 17, False),
                                 (-x, -y, phi, 17, True)):
        r = _lp_rm_slm_rp(xx, yy, pp)
        if r:
            t, u, v = r
            w = (t, -HALF_PI, u, -HALF_PI, v)
            out.append((typ, tuple(-a for a in w) if neg else w))


# ----------------------------------------------------------------------------- public API
def all_paths(start, goal, radius: float) -> list[RSPath]:
    """Every admissible Reeds-Shepp word from start (x, y, theta) to goal for the turning radius in m."""
    x0, y0, th0 = start
    dx, dy = goal[0] - x0, goal[1] - y0
    c, s = math.cos(th0), math.sin(th0)
    x = (c * dx + s * dy) / radius
    y = (-s * dx + c * dy) / radius
    phi = _mod2pi(goal[2] - th0)
    raw: list = []
    _csc(x, y, phi, raw)
    _ccc(x, y, phi, raw)
    _cccc(x, y, phi, raw)
    _ccsc(x, y, phi, raw)
    _ccscc(x, y, phi, raw)
    return [RSPath(_TYPES[typ], tuple(float(v) for v in lengths), radius) for typ, lengths in raw]


def shortest_path(start, goal, radius: float) -> RSPath | None:
    paths = all_paths(start, goal, radius)
    return min(paths, key=lambda p: p.length) if paths else None


def sample(path: RSPath, start, step: float = 0.1):
    """Poses along the path: arrays x, y, theta (vehicle heading), direction (+1/-1), kappa (signed curvature
    of the path w.r.t. the vehicle heading, left > 0) and s (travelled distance). Arcs are integrated exactly."""
    x, y, th = (float(v) for v in start)
    xs, ys, ths, dirs, kas, ss = [np.array([x])], [np.array([y])], [np.array([th])], [], [], [np.array([0.0])]
    s_tot = 0.0
    for kind, seg in path.segments:
        sign = 1.0 if seg > 0 else -1.0
        length = abs(seg)
        kappa = {"L": 1.0, "R": -1.0, "S": 0.0}[kind] / path.radius
        n = max(int(math.ceil(length / step)), 1)
        d = sign * length * np.arange(1, n + 1) / n          # signed arc length along the vehicle axis
        if kappa == 0.0:
            px, py, pth = x + d * math.cos(th), y + d * math.sin(th), np.full(n, th)
        else:
            pth = th + d * kappa
            px = x + (np.sin(pth) - math.sin(th)) / kappa
            py = y - (np.cos(pth) - math.cos(th)) / kappa
        if not dirs:
            dirs.append(np.array([sign]))
            kas.append(np.array([kappa]))
        xs.append(px)
        ys.append(py)
        ths.append(pth)
        dirs.append(np.full(n, sign))
        kas.append(np.full(n, kappa))
        ss.append(s_tot + length * np.arange(1, n + 1) / n)
        x, y, th = float(px[-1]), float(py[-1]), float(pth[-1])
        s_tot += length
    if not dirs:
        dirs, kas = [np.array([1.0])], [np.array([0.0])]
    return {"x": np.concatenate(xs), "y": np.concatenate(ys), "theta": np.concatenate(ths),
            "direction": np.concatenate(dirs), "kappa": np.concatenate(kas), "s": np.concatenate(ss)}
