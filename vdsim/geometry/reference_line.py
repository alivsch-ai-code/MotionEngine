"""Reference curve r(s) with projection and Frenet <-> world transformations.

Implements Werling (2011), appendix A:
    A.1  closed-form transformation [s, s_dot, s_ddot, d, d', d''] <-> [x1, x2, theta, kappa, v, a]
         without numerical differentiation (eqs. A.1 - A.8)
    A.2  continuous projection onto a sampled 2d curve: linear interpolation of
         [x, y, theta] between the samples plus a 1d root search (secant method),
         refined here with Newton steps on the Hermite-interpolated curve

The curve is stored as samples (s, x, y, theta, kappa, dkappa). Between samples x, y are
cubic Hermite interpolated with the exact tangent (dx/ds = cos theta), theta with its
derivative kappa and kappa with dkappa, so position, heading and curvature are smooth.
Remark 4 of Werling (3.5.3): the trajectory acceleration and curvature are only continuous
if the reference curve has a continuous curvature derivative dkappa - the builders below
guarantee that (smoothstep curvature transitions, quintic smoothing splines).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..framework.knowledge import trace


def wrap_angle(a):
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


@dataclass
class FrenetState:
    # Frenet coordinates of a point moving relative to the reference curve
    s: float = 0.0
    s_d: float = 0.0       # ds/dt
    s_dd: float = 0.0      # d2s/dt2
    d: float = 0.0
    d_d: float = 0.0       # dd/dt
    d_dd: float = 0.0      # d2d/dt2
    d_p: float = 0.0       # dd/ds   (d')
    d_pp: float = 0.0      # d2d/ds2 (d'')


def _hermite(p0, p1, m0, m1, u):
    u2, u3 = u * u, u * u * u
    return ((2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1)


def _hermite_d(p0, p1, m0, m1, u):
    # derivative w.r.t. u
    u2 = u * u
    return ((6 * u2 - 6 * u) * p0 + (3 * u2 - 4 * u + 1) * m0 + (-6 * u2 + 6 * u) * p1 + (3 * u2 - 2 * u) * m1)


class ReferenceLine:
    def __init__(self, s, x, y, theta, kappa, dkappa=None, closed=False, name=""):
        self.s = np.asarray(s, dtype=float)
        self.x = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.theta = np.unwrap(np.asarray(theta, dtype=float))
        self.kappa = np.asarray(kappa, dtype=float)
        self.dkappa = (np.gradient(self.kappa, self.s) if dkappa is None and len(self.s) > 1
                       else np.zeros_like(self.s) if dkappa is None else np.asarray(dkappa, dtype=float))
        if len(self.s) < 2:
            raise ValueError("a reference line needs at least two samples")
        if np.any(np.diff(self.s) <= 0):
            raise ValueError("arc length samples must be strictly increasing")
        self.closed = closed
        self.name = name
        ds = np.diff(self.s)
        self._uniform = bool(np.allclose(ds, ds[0], rtol=1e-6, atol=1e-9))
        self._ds = float(ds[0])

    # ------------------------------------------------------------------ basics
    @property
    def length(self):
        return float(self.s[-1] - self.s[0])

    @property
    def s0(self):
        return float(self.s[0])

    def __len__(self):
        return len(self.s)

    def to_dict(self):
        return {"name": self.name, "closed": self.closed,
                **{k: getattr(self, k).tolist() for k in ("s", "x", "y", "theta", "kappa", "dkappa")}}

    @classmethod
    def from_dict(cls, data):
        return cls(data["s"], data["x"], data["y"], data["theta"], data["kappa"], data.get("dkappa"),
                   data.get("closed", False), data.get("name", ""))

    def _wrap_s(self, s):
        s = np.asarray(s, dtype=float)
        if self.closed:
            return self.s[0] + np.mod(s - self.s[0], self.length)
        return s

    def _index(self, s):
        # segment index i with s[i] <= s < s[i+1] (clamped) and the normalized position u
        n = len(self.s)
        if self._uniform:
            i = np.floor((s - self.s[0]) / self._ds).astype(int)
        else:
            i = np.searchsorted(self.s, s, side="right") - 1
        i = np.clip(i, 0, n - 2)
        h = self.s[i + 1] - self.s[i]
        u = (s - self.s[i]) / h
        return i, u, h

    def evaluate(self, s):
        # (x, y, theta, kappa, dkappa) at arc length s; linear extrapolation beyond the ends
        scalar = np.ndim(s) == 0
        s = self._wrap_s(np.atleast_1d(np.asarray(s, dtype=float)))
        i, u, h = self._index(s)
        before = s < self.s[0]
        after = s > self.s[-1]
        uc = np.clip(u, 0.0, 1.0)
        th0, th1 = self.theta[i], self.theta[i + 1]
        x = _hermite(self.x[i], self.x[i + 1], np.cos(th0) * h, np.cos(th1) * h, uc)
        y = _hermite(self.y[i], self.y[i + 1], np.sin(th0) * h, np.sin(th1) * h, uc)
        theta = _hermite(th0, th1, self.kappa[i] * h, self.kappa[i + 1] * h, uc)
        kappa = _hermite(self.kappa[i], self.kappa[i + 1], self.dkappa[i] * h, self.dkappa[i + 1] * h, uc)
        dkappa = self.dkappa[i] + uc * (self.dkappa[i + 1] - self.dkappa[i])
        if np.any(before | after):
            # straight continuation outside the curve (keeps projections well defined)
            for mask, j in ((before, 0), (after, -1)):
                if np.any(mask):
                    ds = s[mask] - self.s[j]
                    x[mask] = self.x[j] + ds * np.cos(self.theta[j])
                    y[mask] = self.y[j] + ds * np.sin(self.theta[j])
                    theta[mask] = self.theta[j]
                    kappa[mask] = 0.0
                    dkappa[mask] = 0.0
        if scalar:
            return float(x[0]), float(y[0]), float(theta[0]), float(kappa[0]), float(dkappa[0])
        return x, y, theta, kappa, dkappa

    def point(self, s, d=0.0):
        x, y, th, _, _ = self.evaluate(s)
        return x - d * np.sin(th), y + d * np.cos(th)

    # ------------------------------------------------------------------ projection (A.2)
    @trace("werling2011", section="A.2", concept="curve_projection",
           note="Interpolation von [x, y, theta] zwischen Stützstellen + Sekantenverfahren, Newton-Verfeinerung")
    def project(self, x, y, hint=None, window=40, max_jump=None):
        # Foot point (s, d) of the position (x, y); hint = sample index of a previous projection
        n = len(self.s)
        if hint is not None and not self.closed:
            lo, hi = max(int(hint) - window, 0), min(int(hint) + window + 1, n)
            idx = np.arange(lo, hi)
        elif hint is not None:
            idx = np.arange(int(hint) - window, int(hint) + window + 1) % n
        else:
            idx = np.arange(n)
        dist2 = (self.x[idx] - x) ** 2 + (self.y[idx] - y) ** 2
        k = int(idx[int(np.argmin(dist2))])
        if hint is not None and max_jump is not None and np.sqrt(dist2.min()) > max_jump:
            return self.project(x, y, None)
        best = None
        for seg in (k - 1, k):
            if self.closed:
                seg %= n - 1
            if seg < 0 or seg > n - 2:
                continue
            alpha = self._secant(x, y, seg)
            if alpha is None:
                continue
            if -1e-9 <= alpha <= 1 + 1e-9 or best is None:
                best = (seg, alpha)
                if -1e-9 <= alpha <= 1 + 1e-9:
                    break
        seg, alpha = best if best is not None else (min(k, n - 2), 0.0)
        if not self.closed:
            if seg == 0:
                alpha = min(alpha, 1.0)
            elif seg == n - 2:
                alpha = max(alpha, 0.0)
            else:
                alpha = float(np.clip(alpha, 0.0, 1.0))
        s = self.s[seg] + alpha * (self.s[seg + 1] - self.s[seg])
        s, d = self._newton(x, y, s)
        self.last_index = seg
        return s, d

    def _secant(self, x, y, seg):
        # root of f(alpha) = (p - xc(alpha)) . t(alpha) with linearly interpolated [x, y, theta]
        x0, x1, y0, y1 = self.x[seg], self.x[seg + 1], self.y[seg], self.y[seg + 1]
        t0, t1 = self.theta[seg], self.theta[seg + 1]

        def f(a):
            xc, yc, th = x0 + a * (x1 - x0), y0 + a * (y1 - y0), t0 + a * (t1 - t0)
            return (x - xc) * np.cos(th) + (y - yc) * np.sin(th)

        a0, a1 = 0.0, 1.0
        f0, f1 = f(a0), f(a1)
        for _ in range(8):
            if abs(f1 - f0) < 1e-14:
                break
            a2 = a1 - f1 * (a1 - a0) / (f1 - f0)
            a0, f0, a1, f1 = a1, f1, a2, f(a2)
            if abs(f1) < 1e-10:
                break
        return float(a1)

    def _newton(self, x, y, s, iterations=3):
        # polish the foot point on the Hermite-interpolated curve: (p - r(s)) . t(s) = 0
        d = 0.0
        for _ in range(iterations):
            xr, yr, th, ka, _ = self.evaluate(s)
            dx, dy = x - xr, y - yr
            along = dx * np.cos(th) + dy * np.sin(th)
            d = -dx * np.sin(th) + dy * np.cos(th)
            denom = 1.0 - ka * d
            if abs(denom) < 1e-3:
                break
            s = s + along / denom
            if not self.closed:
                s = float(np.clip(s, self.s[0] - 50.0, self.s[-1] + 50.0))
            if abs(along) < 1e-9:
                break
        xr, yr, th, _, _ = self.evaluate(s)
        d = -(x - xr) * np.sin(th) + (y - yr) * np.cos(th)
        return float(self._wrap_s(s)) if self.closed else float(s), float(d)

    def project_many(self, x, y, chunk=512):
        # vectorized projection of many points (obstacles, envelopes); returns arrays (s, d)
        x = np.atleast_1d(np.asarray(x, dtype=float))
        y = np.atleast_1d(np.asarray(y, dtype=float))
        k = np.empty(len(x), dtype=int)
        for start in range(0, len(x), chunk):
            xs, ys = x[start:start + chunk, None], y[start:start + chunk, None]
            k[start:start + chunk] = np.argmin((self.x[None, :] - xs) ** 2 + (self.y[None, :] - ys) ** 2, axis=1)
        s = self.s[k].copy()
        for _ in range(4):
            xr, yr, th, ka, _ = self.evaluate(s)
            dx, dy = x - xr, y - yr
            along = dx * np.cos(th) + dy * np.sin(th)
            d = -dx * np.sin(th) + dy * np.cos(th)
            denom = np.where(np.abs(1 - ka * d) < 1e-3, 1.0, 1 - ka * d)
            s = s + along / denom
        xr, yr, th, _, _ = self.evaluate(s)
        d = -(x - xr) * np.sin(th) + (y - yr) * np.cos(th)
        return self._wrap_s(s), d

    # ------------------------------------------------------------------ Frenet transformations (A.1)
    @trace("werling2011", section="A.1", equation="(A.1)-(A.8)", concept="frenet_transformation",
           note="Weltkoordinaten -> Bahnkoordinaten in geschlossener Form")
    def to_frenet(self, x, y, theta, kappa=0.0, v=0.0, a=0.0, hint=None):
        # world state of a point (theta = direction of motion) -> FrenetState
        s, d = self.project(x, y, hint)
        _, _, th_r, k_r, dk_r = self.evaluate(s)
        dth = float(wrap_angle(theta - th_r))
        one_m = 1.0 - k_r * d
        c, tn = np.cos(dth), np.tan(dth)
        d_p = one_m * tn                                                       # (A.3)
        d_pp = -(dk_r * d + k_r * d_p) * tn + one_m / c**2 * (kappa * one_m / c - k_r)   # (A.5)
        s_d = v * c / one_m                                                    # (A.1)
        bracket = one_m * tn * (kappa * one_m / c - k_r) - (dk_r * d + k_r * d_p)
        s_dd = (a - s_d**2 / c * bracket) * c / one_m                          # (A.6)
        d_d = s_d * d_p                                                        # (A.7)
        d_dd = s_dd * d_p + s_d**2 * d_pp                                      # (A.8)
        return FrenetState(s, s_d, s_dd, d, d_d, d_dd, d_p, d_pp)

    @trace("werling2011", section="A.1", equation="(A.1)-(A.6)", concept="frenet_transformation",
           note="Bahnkoordinaten -> Weltkoordinaten in geschlossener Form, singularitätsfrei für v = 0")
    def to_cartesian(self, s, s_d, s_dd, d, d_p, d_pp):
        # Frenet motion (arc-length derivatives of d) -> dict of world quantities (arrays)
        s = np.asarray(s, dtype=float)
        x_r, y_r, th_r, k_r, dk_r = self.evaluate(s)
        d = np.asarray(d, dtype=float)
        d_p = np.asarray(d_p, dtype=float)
        one_m = 1.0 - k_r * d
        dth = np.arctan2(d_p, one_m)                      # (A.3): d' = (1 - kappa_r d) tan(dtheta)
        c, tn = np.cos(dth), np.tan(dth)
        kappa = ((d_pp + (dk_r * d + k_r * d_p) * tn) * c**2 / one_m + k_r) * c / one_m   # (A.5)
        v = s_d * one_m / c                               # (A.1), (A.2)
        bracket = one_m * tn * (kappa * one_m / c - k_r) - (dk_r * d + k_r * d_p)
        a = s_dd * one_m / c + s_d**2 / c * bracket       # (A.6)
        return {"x": x_r - d * np.sin(th_r), "y": y_r + d * np.cos(th_r), "theta": th_r + dth,
                "kappa": kappa, "v": v, "a": a}

    @staticmethod
    def time_to_arc(s_d, s_dd, d_d, d_dd, eps=1e-6):
        # (A.7), (A.8) solved for d', d'' (fast driving, s_dot != 0)
        s_d = np.where(np.abs(s_d) < eps, eps, s_d)
        d_p = d_d / s_d
        d_pp = (d_dd - s_dd * d_p) / s_d**2
        return d_p, d_pp

    @staticmethod
    def arc_to_time(s_d, s_dd, d_p, d_pp):
        return s_d * d_p, s_dd * d_p + s_d**2 * d_pp

    # ------------------------------------------------------------------ derived curves
    def offset(self, d0, name=None):
        # parallel curve at lateral distance d0 (lane centers / boundaries)
        nx, ny = -np.sin(self.theta), np.cos(self.theta)
        x, y = self.x + d0 * nx, self.y + d0 * ny
        f = 1.0 - self.kappa * d0
        if np.any(f <= 0.05):
            raise ValueError("offset larger than the curve radius")
        s_new = np.concatenate([[0.0], np.cumsum(0.5 * (f[1:] + f[:-1]) * np.diff(self.s))]) + self.s[0]
        kappa = self.kappa / f
        dkappa = self.dkappa / f**3
        line = ReferenceLine(s_new, x, y, self.theta, kappa, dkappa, self.closed, name or f"{self.name}{d0:+.2f}")
        return line.resample(self._ds if self._uniform else 0.25)

    def resample(self, ds=0.25):
        n = max(int(np.ceil(self.length / ds)), 1)
        s = np.linspace(self.s[0], self.s[-1], n + 1)
        x, y, th, k, dk = self.evaluate(s)
        return ReferenceLine(s, x, y, th, k, dk, self.closed, self.name)

    def segment(self, s_from, s_to, ds=None):
        # sub-curve [s_from, s_to] (re-based to start at s = 0)
        ds = ds or (self._ds if self._uniform else 0.25)
        n = max(int(np.ceil((s_to - s_from) / ds)), 1)
        s = np.linspace(s_from, s_to, n + 1)
        x, y, th, k, dk = self.evaluate(s)
        return ReferenceLine(s - s_from, x, y, th, k, dk, False, self.name)

    def reversed(self, name=None):
        # same curve traversed in the opposite direction (reverse driving / opposite lane)
        s = self.s[-1] - self.s[::-1]
        return ReferenceLine(s, self.x[::-1], self.y[::-1], self.theta[::-1] + np.pi, -self.kappa[::-1],
                             self.dkappa[::-1], self.closed, name or f"{self.name}_rev")

    # ------------------------------------------------------------------ builders
    @classmethod
    def from_curvature(cls, kappa_fn, length, x0=0.0, y0=0.0, theta0=0.0, ds=0.25, dkappa_fn=None,
                       closed=False, name=""):
        # integrate a curvature profile kappa(s) (vectorized callable) into a curve
        fine = max(int(np.ceil(length / 0.02)), 2)
        sf = np.linspace(0.0, length, fine + 1)
        kf = np.asarray(kappa_fn(sf), dtype=float)
        th = theta0 + np.concatenate([[0.0], np.cumsum(0.5 * (kf[1:] + kf[:-1]) * np.diff(sf))])
        # positions with the midpoint heading (second order accurate)
        th_mid = 0.5 * (th[1:] + th[:-1])
        xf = x0 + np.concatenate([[0.0], np.cumsum(np.cos(th_mid) * np.diff(sf))])
        yf = y0 + np.concatenate([[0.0], np.cumsum(np.sin(th_mid) * np.diff(sf))])
        n = max(int(np.ceil(length / ds)), 1)
        s = np.linspace(0.0, length, n + 1)
        k = np.asarray(kappa_fn(s), dtype=float)
        dk = np.asarray(dkappa_fn(s), dtype=float) if dkappa_fn is not None else np.gradient(k, s)
        return cls(s, np.interp(s, sf, xf), np.interp(s, sf, yf), np.interp(s, sf, th), k, dk, closed, name)

    @classmethod
    def straight(cls, length, x0=0.0, y0=0.0, theta0=0.0, ds=0.5, name=""):
        n = max(int(np.ceil(length / ds)), 1)
        s = np.linspace(0.0, length, n + 1)
        return cls(s, x0 + s * np.cos(theta0), y0 + s * np.sin(theta0), np.full_like(s, theta0),
                   np.zeros_like(s), np.zeros_like(s), False, name)

    @classmethod
    def from_segments(cls, segments, x0=0.0, y0=0.0, theta0=0.0, transition=10.0, ds=0.25, name="", closed=False):
        # Road geometry from segments with C1 curvature transitions (continuous dkappa):
        #   ("straight", length) | ("arc", length, curvature) | ("turn", angle_rad, radius)
        # Curvature changes are smoothstep ramps of length `transition`, centered on the segment
        # boundaries, so the heading change of every arc is exactly curvature * length.
        lengths, curvatures = [], []
        for seg in segments:
            kind = seg[0]
            if kind == "straight":
                lengths.append(float(seg[1]))
                curvatures.append(0.0)
            elif kind == "arc":
                lengths.append(float(seg[1]))
                curvatures.append(float(seg[2]))
            elif kind == "turn":
                angle, radius = float(seg[1]), float(seg[2])
                lengths.append(abs(angle) * radius)
                curvatures.append(np.sign(angle) / radius)
            else:
                raise ValueError(f"unknown segment type '{kind}'")
        bounds = np.concatenate([[0.0], np.cumsum(lengths)])
        total = float(bounds[-1])
        kappa_fn, dkappa_fn = curvature_profile(bounds, curvatures, transition)
        return cls.from_curvature(kappa_fn, total, x0, y0, theta0, ds, dkappa_fn, closed, name)

    @classmethod
    def from_points(cls, x, y, ds=0.5, smoothing=0.0, name=""):
        # quintic smoothing spline through (noisy) points -> curve with continuous dkappa
        from scipy.interpolate import splev, splprep
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        keep = np.concatenate([[True], np.hypot(np.diff(x), np.diff(y)) > 1e-6])
        x, y = x[keep], y[keep]
        k = min(5, len(x) - 1)
        tck, _ = splprep([x, y], s=smoothing, k=k)
        u = np.linspace(0, 1, max(len(x) * 40, 400))
        xd, yd = splev(u, tck)
        x1, y1 = splev(u, tck, der=1)
        x2, y2 = splev(u, tck, der=2)
        speed = np.hypot(x1, y1)
        sd = np.concatenate([[0.0], np.cumsum(0.5 * (speed[1:] + speed[:-1]) * np.diff(u))])
        kap = (x1 * y2 - y1 * x2) / speed**3
        th = np.unwrap(np.arctan2(y1, x1))
        n = max(int(np.ceil(sd[-1] / ds)), 1)
        s = np.linspace(0.0, sd[-1], n + 1)
        ks = np.interp(s, sd, kap)
        return cls(s, np.interp(s, sd, xd), np.interp(s, sd, yd), np.interp(s, sd, th), ks,
                   np.gradient(ks, s), False, name)

    @classmethod
    def circle(cls, radius, x_center=0.0, y_center=0.0, start_angle=-np.pi / 2, ccw=True, ds=0.25, name=""):
        # closed circular curve (roundabout ring), starting at start_angle
        length = 2 * np.pi * radius
        n = max(int(np.ceil(length / ds)), 8)
        s = np.linspace(0.0, length, n + 1)
        sign = 1.0 if ccw else -1.0
        phi = start_angle + sign * s / radius
        x = x_center + radius * np.cos(phi)
        y = y_center + radius * np.sin(phi)
        theta = phi + sign * np.pi / 2
        return cls(s, x, y, theta, np.full_like(s, sign / radius), np.zeros_like(s), True, name)


def curvature_profile(bounds, curvatures, transition):
    # piecewise constant curvature with smoothstep ramps centered at the inner boundaries
    bounds = np.asarray(bounds, dtype=float)
    curvatures = np.asarray(curvatures, dtype=float)
    lengths = np.diff(bounds)

    def ramp_width(i):
        # ramp at boundary i (between segment i-1 and i), limited by the neighboring lengths
        return min(transition, 0.9 * lengths[i - 1], 0.9 * lengths[i])

    def kappa_fn(s):
        s = np.asarray(s, dtype=float)
        idx = np.clip(np.searchsorted(bounds, s, side="right") - 1, 0, len(curvatures) - 1)
        k = curvatures[idx].copy()
        for i in range(1, len(curvatures)):
            w = ramp_width(i)
            if w <= 0 or curvatures[i] == curvatures[i - 1]:
                continue
            u = (s - (bounds[i] - w / 2)) / w
            m = (u > 0) & (u < 1)
            uu = u[m]
            k[m] = curvatures[i - 1] + (curvatures[i] - curvatures[i - 1]) * (3 * uu**2 - 2 * uu**3)
        return k

    def dkappa_fn(s):
        s = np.asarray(s, dtype=float)
        dk = np.zeros_like(s)
        for i in range(1, len(curvatures)):
            w = ramp_width(i)
            if w <= 0 or curvatures[i] == curvatures[i - 1]:
                continue
            u = (s - (bounds[i] - w / 2)) / w
            m = (u > 0) & (u < 1)
            uu = u[m]
            dk[m] += (curvatures[i] - curvatures[i - 1]) * (6 * uu - 6 * uu**2) / w
        return dk

    return kappa_fn, dkappa_fn
