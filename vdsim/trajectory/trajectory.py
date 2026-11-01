"""Reference trajectory: path (x, y, psi, kappa over arc length s) plus speed profile.

Also holds optional decorations for plots (cones, lane boundaries) and, for open-loop
maneuvers, a steering-angle time table instead of a path to follow.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Projection:
    s: float
    index: int
    lateral_error: float  # > 0: vehicle left of the path
    heading: float
    kappa: float
    speed: float
    x: float
    y: float


@dataclass
class Trajectory:
    x: np.ndarray
    y: np.ndarray
    v: np.ndarray = None
    name: str = ""
    cones: list = field(default_factory=list)          # [(x, y), ...] for plots and cone-hit KPIs
    boundaries: list = field(default_factory=list)     # polylines [(xs, ys), ...]
    metadata: dict = field(default_factory=dict)
    steer_table: tuple = None                          # open loop: (time, road-wheel angle)
    accel_table: tuple = None                          # open loop: (time, acceleration request)

    def __post_init__(self):
        x = np.asarray(self.x, dtype=float)
        y = np.asarray(self.y, dtype=float)
        v = np.asarray(10.0 if self.v is None else self.v, dtype=float)
        v = np.full(x.shape, float(v)) if v.ndim == 0 else v
        keep = np.concatenate([[True], np.hypot(np.diff(x), np.diff(y)) > 1e-6])  # drop duplicate points
        self.x, self.y, self.v = x[keep], y[keep], v[keep]
        self._update_geometry()
        self._hint = 0

    def _update_geometry(self):
        dx, dy = np.diff(self.x), np.diff(self.y)
        n = len(self.x)
        self.s = np.concatenate([[0.0], np.cumsum(np.hypot(dx, dy))])
        if n < 2:
            self.psi, self.kappa = np.zeros(n), np.zeros(n)
            return
        segment = np.unwrap(np.arctan2(dy, dx))
        # heading at the points: mean of the adjacent segment headings
        self.psi = np.concatenate([segment[:1], (segment[:-1] + segment[1:]) / 2, segment[-1:]])
        self.kappa = np.gradient(self.psi, self.s) if n > 2 else np.zeros(n)

    # construction
    @classmethod
    def from_curvature(cls, s, kappa, v=None, x0=0.0, y0=0.0, psi0=0.0, **kwargs):
        # Integrate heading and position from a curvature profile (trapezoidal, fine s grid)
        s = np.asarray(s, dtype=float)
        kappa = np.asarray(kappa, dtype=float)
        ds = np.diff(s)
        psi = psi0 + np.concatenate([[0.0], np.cumsum(ds * (kappa[1:] + kappa[:-1]) / 2)])
        psi_mid = (psi[1:] + psi[:-1]) / 2
        x = x0 + np.concatenate([[0.0], np.cumsum(ds * np.cos(psi_mid))])
        y = y0 + np.concatenate([[0.0], np.cumsum(ds * np.sin(psi_mid))])
        traj = cls(x, y, v, **kwargs)
        traj.kappa = np.interp(traj.s, s - s[0], kappa)
        traj.psi = np.interp(traj.s, s - s[0], psi)
        return traj

    @property
    def length(self):
        return float(self.s[-1])

    @property
    def is_open_loop(self):
        return self.steer_table is not None

    def steer_at(self, t):
        return float(np.interp(t, *self.steer_table))

    def accel_at(self, t):
        return float(np.interp(t, *self.accel_table))

    def resample(self, ds=0.5):
        s_new = np.arange(0.0, self.length, ds)
        s_new = np.append(s_new, self.length)
        traj = Trajectory(np.interp(s_new, self.s, self.x), np.interp(s_new, self.s, self.y),
                          np.interp(s_new, self.s, self.v), self.name, self.cones, self.boundaries,
                          dict(self.metadata), self.steer_table, self.accel_table)
        traj.kappa = np.interp(traj.s, self.s, self.kappa)
        return traj

    def smooth(self, window=5):
        # moving-average smoothing of x/y (useful for noisy GPS data)
        if window < 2 or len(self.x) <= window:
            return self
        kernel = np.ones(window) / window
        pad = window // 2
        xs = np.convolve(np.pad(self.x, pad, mode="edge"), kernel, mode="valid")[:len(self.x)]
        ys = np.convolve(np.pad(self.y, pad, mode="edge"), kernel, mode="valid")[:len(self.y)]
        return Trajectory(xs, ys, self.v, self.name, self.cones, self.boundaries, dict(self.metadata))

    # queries
    def at(self, s):
        s = np.clip(s, 0.0, self.length)
        return {"x": np.interp(s, self.s, self.x), "y": np.interp(s, self.s, self.y),
                "psi": np.interp(s, self.s, self.psi), "kappa": np.interp(s, self.s, self.kappa),
                "v": np.interp(s, self.s, self.v)}

    def project(self, x, y, hint=None, window=60):
        # Closest point on the polyline, searched around `hint` (index of the last result of the
        # same caller, fast for sequential calls). A global jump only happens when the vehicle
        # has lost the path, so start/finish points of closed tracks are not confused.
        n = len(self.x)
        hint = self._hint if hint is None else hint
        lo, hi = max(hint - window, 0), min(hint + window, n - 1)
        idx = self._closest_segment(x, y, lo, hi)
        dist = self._distance(x, y, idx)
        if dist > 3.0:
            candidate = self._closest_segment(x, y, 0, n - 1)
            if self._distance(x, y, candidate) < dist - 1.0:
                idx = candidate
        self._hint = idx
        x0, y0 = self.x[idx], self.y[idx]
        dx, dy = self.x[idx + 1] - x0, self.y[idx + 1] - y0
        seg_len2 = dx * dx + dy * dy
        tau = np.clip(((x - x0) * dx + (y - y0) * dy) / seg_len2, 0.0, 1.0)
        px, py = x0 + tau * dx, y0 + tau * dy
        seg_len = np.sqrt(seg_len2)
        lateral = (dx * (y - py) - dy * (x - px)) / seg_len
        s = self.s[idx] + tau * seg_len
        return Projection(s=float(s), index=int(idx), lateral_error=float(lateral),
                          heading=float(self.psi[idx] + tau * (self.psi[idx + 1] - self.psi[idx])),
                          kappa=float(np.interp(s, self.s, self.kappa)),
                          speed=float(np.interp(s, self.s, self.v)), x=float(px), y=float(py))

    def _distance(self, x, y, idx):
        x0, y0 = self.x[idx], self.y[idx]
        dx, dy = self.x[idx + 1] - x0, self.y[idx + 1] - y0
        tau = np.clip(((x - x0) * dx + (y - y0) * dy) / max(dx * dx + dy * dy, 1e-12), 0.0, 1.0)
        return float(np.hypot(x0 + tau * dx - x, y0 + tau * dy - y))

    def _closest_segment(self, x, y, lo, hi):
        xs, ys = self.x[lo:hi + 1], self.y[lo:hi + 1]
        dx, dy = np.diff(xs), np.diff(ys)
        seg_len2 = np.maximum(dx * dx + dy * dy, 1e-12)
        tau = np.clip(((x - xs[:-1]) * dx + (y - ys[:-1]) * dy) / seg_len2, 0.0, 1.0)
        dist2 = (xs[:-1] + tau * dx - x) ** 2 + (ys[:-1] + tau * dy - y) ** 2
        return lo + int(np.argmin(dist2))

    def reset_search(self):
        self._hint = 0

    # serialization
    def to_dict(self):
        data = {"name": self.name, "x": self.x.tolist(), "y": self.y.tolist(), "v": self.v.tolist(),
                "cones": [list(c) for c in self.cones],
                "boundaries": [[list(b[0]), list(b[1])] for b in self.boundaries], "metadata": self.metadata}
        for key in ("steer_table", "accel_table"):
            table = getattr(self, key)
            if table is not None:
                data[key] = [list(map(float, table[0])), list(map(float, table[1]))]
        return data

    @classmethod
    def from_dict(cls, data):
        tables = {key: (np.asarray(data[key][0]), np.asarray(data[key][1])) if data.get(key) else None
                  for key in ("steer_table", "accel_table")}
        return cls(data["x"], data["y"], data.get("v"), data.get("name", ""),
                   [tuple(c) for c in data.get("cones", [])],
                   [(np.asarray(b[0]), np.asarray(b[1])) for b in data.get("boundaries", [])],
                   data.get("metadata", {}), **tables)

    def save(self, path):
        path = Path(path)
        if path.suffix.lower() == ".csv":
            np.savetxt(path, np.column_stack([self.s, self.x, self.y, self.psi, self.kappa, self.v]),
                       delimiter=",", header="s,x,y,psi,kappa,v", comments="", fmt="%.6f")
        else:
            path.write_text(json.dumps(self.to_dict()), encoding="utf-8")
