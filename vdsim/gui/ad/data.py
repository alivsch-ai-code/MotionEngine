"""Tolerant access to an ADResult for the views: time lookup, snapshots, objects, names, geometry.

Every field of the data contract is optional; all accessors return None / empty values when data is missing.
"""

from __future__ import annotations

import numpy as np

from .style import sig


def arr(value, dtype=float):
    if value is None:
        return None
    try:
        a = np.asarray(value, dtype=dtype)
    except (TypeError, ValueError):
        return None
    return a if a.size else None


def rect(x, y, psi, length, width):
    # closed outline (5 points) of an oriented rectangle centered at (x, y)
    c, s = np.cos(psi), np.sin(psi)
    hl, hw = length / 2, width / 2
    px = np.array([hl, hl, -hl, -hl, hl])
    py = np.array([hw, -hw, -hw, hw, hw])
    return x + c * px - s * py, y + s * px + c * py


def circle(x, y, r, n=28):
    a = np.linspace(0, 2 * np.pi, n)
    return x + r * np.cos(a), y + r * np.sin(a)


def join(polylines):
    # list of (xs, ys) -> NaN separated arrays for one PlotDataItem (connect="finite")
    xs, ys = [], []
    for px, py in polylines:
        xs += [np.asarray(px, dtype=float), [np.nan]]
        ys += [np.asarray(py, dtype=float), [np.nan]]
    if not xs:
        return np.zeros(0), np.zeros(0)
    return np.concatenate(xs), np.concatenate(ys)


def object_circles(length, width, n=None):
    # covering circles of a rectangle along its length (offsets from the center, radius)
    n = n or max(int(np.ceil(length / max(width, 0.1))), 1)
    seg = length / n
    offsets = -length / 2 + seg * (np.arange(n) + 0.5)
    return offsets, float(np.hypot(seg / 2, width / 2))


class Polyline:
    # arc-length parametrized polyline with a vectorized Frenet projection
    def __init__(self, xs, ys):
        self.x, self.y = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
        seg = np.hypot(np.diff(self.x), np.diff(self.y))
        self.s = np.concatenate([[0.0], np.cumsum(seg)])

    def project(self, px, py):
        px, py = np.atleast_1d(np.asarray(px, dtype=float)), np.atleast_1d(np.asarray(py, dtype=float))
        ax, ay = self.x[:-1], self.y[:-1]
        bx, by = self.x[1:] - ax, self.y[1:] - ay
        l2 = np.maximum(bx ** 2 + by ** 2, 1e-12)
        u = np.clip(((px[:, None] - ax) * bx + (py[:, None] - ay) * by) / l2, 0, 1)
        qx, qy = ax + u * bx, ay + u * by
        dist = (px[:, None] - qx) ** 2 + (py[:, None] - qy) ** 2
        k = np.argmin(dist, axis=1)
        rows = np.arange(len(px))
        s = self.s[k] + u[rows, k] * np.sqrt(l2[k])
        cross = bx[k] * (py - ay[k]) - by[k] * (px - ax[k])
        d = np.sign(cross) * np.sqrt(dist[rows, k])
        return s, d


class ResultData:
    def __init__(self, result):
        self.result = result
        self.signals = getattr(result, "signals", None) or {}
        self.t = sig(result, "t")
        if self.t is None:
            self.t = np.zeros(0)
        self.snapshots = list(getattr(result, "snapshots", None) or [])
        self.snap_t = np.array([s.get("t", np.nan) for s in self.snapshots], dtype=float)
        self.metadata = getattr(result, "metadata", None) or {}
        self.road = getattr(result, "road", None) or {}
        self.objects = getattr(result, "objects", None) or {}
        self.events = sorted([e for e in (getattr(result, "events", None) or []) if "t" in e], key=lambda e: e["t"])
        dims = self.metadata.get("ego_dims") or {}
        self.ego_length = float(dims.get("length", 4.8))
        self.ego_width = float(dims.get("width", 1.85))
        self.center_offset = float(dims.get("center_offset", 0.15))
        self.cg_to_rear = float(dims.get("cg_to_rear", 1.5))
        self._obj_cache = {}
        self._lanes = {}
        for lane in self.road.get("lanes", []) or []:
            c = lane.get("center")
            if c is not None and len(c) == 2 and len(c[0]) > 1:
                self._lanes[str(lane.get("id"))] = Polyline(c[0], c[1])

    # ------------------------------------------------------------------ time
    @property
    def t0(self):
        if len(self.t):
            return float(self.t[0])
        return float(np.nanmin(self.snap_t)) if len(self.snap_t) else 0.0

    @property
    def t1(self):
        if len(self.t):
            return float(self.t[-1])
        return float(np.nanmax(self.snap_t)) if len(self.snap_t) else 0.0

    @property
    def plan_period(self):
        if len(self.snap_t) > 1:
            d = np.diff(self.snap_t)
            d = d[np.isfinite(d) & (d > 0)]
            if len(d):
                return float(np.median(d))
        if len(self.t) > 1:
            return float(np.median(np.diff(self.t)))
        return 0.1

    def index(self, t):
        if not len(self.t):
            return None
        return int(np.clip(np.searchsorted(self.t, t + 1e-9, side="right") - 1, 0, len(self.t) - 1))

    def value(self, key, t, default=np.nan):
        a = sig(self.result, key)
        i = self.index(t)
        if a is None or i is None or i >= len(a):
            return default
        return float(a[i])

    def snapshot_index(self, t):
        if not len(self.snap_t):
            return None
        i = int(np.searchsorted(self.snap_t, t + 1e-9, side="right") - 1)
        return i if i >= 0 else None

    def snapshot(self, t):
        i = self.snapshot_index(t)
        return self.snapshots[i] if i is not None else None

    def name(self, kind, idx):
        # metadata name lists: controllers, modes, maneuvers
        names = self.metadata.get(kind) or []
        try:
            i = int(idx)
        except (TypeError, ValueError):
            return "-"
        return str(names[i]) if 0 <= i < len(names) else (str(i) if np.isfinite(idx) else "-")

    # ------------------------------------------------------------------ objects
    def object_state(self, oid, t):
        rec = self.objects.get(oid)
        if rec is None:
            return None
        if oid not in self._obj_cache:
            ot = arr(rec.get("t"))
            cache = {"t": ot}
            for k in ("x", "y", "psi", "v"):
                a = arr(rec.get(k))
                cache[k] = np.unwrap(a) if (k == "psi" and a is not None) else a
            self._obj_cache[oid] = cache
        c = self._obj_cache[oid]
        ot = c["t"]
        if ot is None or c["x"] is None or c["y"] is None or t < ot[0] - 1e-6 or t > ot[-1] + 1e-6:
            return None
        out = {k: float(np.interp(t, ot, c[k])) if c[k] is not None else 0.0 for k in ("x", "y", "psi", "v")}
        out.update(type=rec.get("type", "car"), length=float(rec.get("length", 4.5)),
                   width=float(rec.get("width", 1.8)))
        return out

    # ------------------------------------------------------------------ ego
    def ego_pose(self, t):
        x, y, psi = self.value("ego_x", t), self.value("ego_y", t), self.value("ego_psi", t, 0.0)
        if not np.isfinite(x) or not np.isfinite(y):
            snap = self.snapshot(t)
            st = (snap or {}).get("start_state") or {}
            x, y, psi = st.get("x", np.nan), st.get("y", np.nan), st.get("psi", st.get("theta", 0.0))
        return float(x), float(y), float(psi if np.isfinite(psi) else 0.0)

    def ego_center(self, x, y, psi):
        return x + self.center_offset * np.cos(psi), y + self.center_offset * np.sin(psi)

    # ------------------------------------------------------------------ geometry
    def lane(self, lane_id):
        return self._lanes.get(str(lane_id)) if lane_id is not None else None

    def reference(self, snap):
        # reference polyline of a snapshot (behavior lane), falls back to the first lane
        lane_id = ((snap or {}).get("behavior") or {}).get("lane_id")
        ref = self.lane(lane_id)
        if ref is None and self._lanes:
            ref = next(iter(self._lanes.values()))
        return ref
