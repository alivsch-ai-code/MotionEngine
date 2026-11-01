"""Waypoint editor (data model): edit waypoints, corner radii and speeds, build a trajectory.

The GUI's interactive editor manipulates this model; it can also be scripted.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .speed_profile import speed_profile
from .trajectory import Trajectory


@dataclass
class Waypoint:
    x: float
    y: float
    v_kmh: float = 50.0
    radius: float = 0.0  # corner radius (fillet) at this waypoint, 0 = sharp corner


class WaypointEditor:
    def __init__(self, waypoints=None):
        self.waypoints = list(waypoints or [])
        self._history = []

    def _snapshot(self):
        self._history.append([Waypoint(**asdict(w)) for w in self.waypoints])
        self._history = self._history[-50:]

    def undo(self):
        if self._history:
            self.waypoints = self._history.pop()

    def add(self, x, y, v_kmh=50.0, radius=0.0):
        self._snapshot()
        self.waypoints.append(Waypoint(x, y, v_kmh, radius))

    def insert(self, index, x, y, v_kmh=50.0, radius=0.0):
        self._snapshot()
        self.waypoints.insert(index, Waypoint(x, y, v_kmh, radius))

    def move(self, index, x, y):
        self._snapshot()
        self.waypoints[index].x, self.waypoints[index].y = x, y

    def remove(self, index):
        self._snapshot()
        del self.waypoints[index]

    def set_speed(self, index, v_kmh):
        self._snapshot()
        self.waypoints[index].v_kmh = v_kmh

    def set_radius(self, index, radius):
        self._snapshot()
        self.waypoints[index].radius = max(radius, 0.0)

    def set_all_radii(self, radius):
        self._snapshot()
        for w in self.waypoints[1:-1]:
            w.radius = radius

    def nearest(self, x, y):
        if not self.waypoints:
            return None
        d = [np.hypot(w.x - x, w.y - y) for w in self.waypoints]
        return int(np.argmin(d))

    def to_trajectory(self, ds=0.5, ay_max=None, name="waypoints"):
        # Polyline with circular fillets at the waypoints; speeds interpolated between waypoints
        if len(self.waypoints) < 2:
            raise ValueError("at least two waypoints are needed")
        pts = np.array([[w.x, w.y] for w in self.waypoints])
        xs, ys, vs = [pts[0, 0]], [pts[0, 1]], [self.waypoints[0].v_kmh]
        current = pts[0]
        for i in range(1, len(pts)):
            target = pts[i]
            v_i = self.waypoints[i].v_kmh
            if 0 < i < len(pts) - 1 and self.waypoints[i].radius > 0:
                arc_start, arc_pts = self._fillet(pts[i - 1], pts[i], pts[i + 1], self.waypoints[i].radius,
                                                  current, ds)
                if arc_pts is not None:
                    self._line(xs, ys, vs, current, arc_start, v_i, ds)
                    for p in arc_pts:
                        xs.append(p[0]); ys.append(p[1]); vs.append(v_i)
                    current = arc_pts[-1]
                    continue
            self._line(xs, ys, vs, current, target, v_i, ds)
            current = target
        traj = Trajectory(xs, ys, np.array(vs) / 3.6, name=name)
        if ay_max:
            traj.v = speed_profile(traj.s, traj.kappa, traj.v, ay_max, 2.0, -3.0)
        traj.metadata["source"] = "waypoint_editor"
        return traj

    @staticmethod
    def _line(xs, ys, vs, a, b, v_kmh, ds):
        length = np.hypot(*(b - a))
        n = max(int(np.ceil(length / ds)), 1)
        v0 = vs[-1]
        for k in range(1, n + 1):
            p = a + (b - a) * k / n
            xs.append(p[0]); ys.append(p[1]); vs.append(v0 + (v_kmh - v0) * k / n)

    @staticmethod
    def _fillet(p_prev, p, p_next, radius, current, ds):
        d1 = (p - p_prev) / max(np.hypot(*(p - p_prev)), 1e-9)
        d2 = (p_next - p) / max(np.hypot(*(p_next - p)), 1e-9)
        turn = np.arctan2(d1[0] * d2[1] - d1[1] * d2[0], d1 @ d2)
        if abs(turn) < 1e-3:
            return None, None
        tangent = radius * np.tan(abs(turn) / 2)
        tangent = min(tangent, 0.5 * np.hypot(*(p - current)), 0.5 * np.hypot(*(p_next - p)))
        r_eff = tangent / np.tan(abs(turn) / 2)
        a = p - d1 * tangent
        normal = np.array([-d1[1], d1[0]]) * np.sign(turn)
        center = a + normal * r_eff
        start = np.arctan2(*(a - center)[::-1])
        n = max(int(np.ceil(r_eff * abs(turn) / ds)), 2)
        angles = start + np.sign(turn) * np.linspace(0, abs(turn), n + 1)[1:]
        arc = center + r_eff * np.column_stack([np.cos(angles), np.sin(angles)])
        return a, arc

    @classmethod
    def from_trajectory(cls, traj, n_points=30):
        idx = np.linspace(0, len(traj.x) - 1, n_points).astype(int)
        return cls([Waypoint(float(traj.x[i]), float(traj.y[i]), float(traj.v[i] * 3.6)) for i in idx])

    def to_dict(self):
        return {"waypoints": [asdict(w) for w in self.waypoints]}

    @classmethod
    def from_dict(cls, data):
        return cls([Waypoint(**w) for w in data["waypoints"]])

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
