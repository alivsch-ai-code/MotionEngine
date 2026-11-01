"""Result of one automated-driving simulation run.

    signals     time series at the executor rate (ego state, commands, tracking errors, planner/behavior info)
    objects     ground-truth history of every actor (for replay, safety metrics)
    snapshots   PlannerDebug per planning cycle + the selected trajectory (interactive timeline)
    events      reinitializations, collisions, mode switches, maneuver changes, scenario events
    road        lane geometry for drawing (center lines and boundaries as polylines)
    kpis        research metrics (vdsim.research.metrics)
    profile     per-node runtime statistics
    provenance  reproducibility manifest (versions, seed, configuration hash)
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

import numpy as np

from ..framework.types import PlannerDebug

SNAPSHOT_ARRAYS = ("candidates_x", "candidates_y", "candidates_s", "candidates_d", "candidates_cost",
                   "candidates_status")


def _jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer, np.bool_)):
        return obj.item()
    if is_dataclass(obj) and not isinstance(obj, type):
        return _jsonable(asdict(obj))
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


class ADResult:
    def __init__(self, name="", scenario=None, stack=None, seed=0):
        self.name = name
        self.scenario = scenario or {}
        self.stack = stack or {}
        self.seed = seed
        self._rows = []                 # list of dicts while recording
        self._signals = None            # dict of arrays after finalize()
        self.objects = {}               # id -> {"type", "length", "width", "t": [], "x": [], ...}
        self.snapshots = []             # list of dicts (PlannerDebug fields + selected trajectory)
        self.events = []
        self.road = {}
        self.kpis = {}
        self.profile = {}
        self.provenance = {}
        self.metadata = {}

    # ------------------------------------------------------------------ recording
    def append(self, row):
        self._rows.append(row)
        self._signals = None

    def add_event(self, t, kind, **info):
        self.events.append({"t": float(t), "type": kind, **_jsonable(info)})

    def add_objects(self, t, objects):
        for o in objects:
            rec = self.objects.get(o.id)
            if rec is None:
                rec = self.objects[o.id] = {"type": o.type, "length": float(o.length), "width": float(o.width),
                                            "t": [], "x": [], "y": [], "psi": [], "v": [], "a": []}
            rec["t"].append(float(t))
            rec["x"].append(float(o.x))
            rec["y"].append(float(o.y))
            rec["psi"].append(float(o.psi))
            rec["v"].append(float(o.v))
            rec["a"].append(float(o.a))

    def add_snapshot(self, debug, trajectory=None, behavior=None):
        snap = {}
        if isinstance(debug, PlannerDebug):
            for key, value in debug.__dict__.items():
                if key in SNAPSHOT_ARRAYS:
                    arr = np.asarray(value)
                    snap[key] = arr.astype(np.float32) if arr.dtype.kind == "f" else arr
                else:
                    snap[key] = _jsonable(value)
        if trajectory is not None and not trajectory.empty:
            snap["trajectory"] = {k: np.asarray(getattr(trajectory, k), dtype=np.float32)
                                  for k in ("t", "x", "y", "theta", "kappa", "v", "a", "s", "d")}
            snap["trajectory_info"] = {"mode": trajectory.longitudinal_mode, "lateral_mode": trajectory.lateral_mode,
                                       "reference_point": trajectory.reference_point, "direction": trajectory.direction,
                                       "cost": float(trajectory.cost), "valid": bool(trajectory.valid),
                                       "reinitialized": bool(trajectory.reinitialized)}
            ref = trajectory.reference_line
            if ref is not None:
                snap["reference_line"] = getattr(ref, "name", "")
        if behavior is not None:
            snap["behavior"] = {"maneuver": behavior.maneuver, "target_speed": float(behavior.target_speed),
                                "modes": [m.kind for m in behavior.modes], "lane_id": behavior.lane_id,
                                "d_min": float(behavior.d_min), "d_max": float(behavior.d_max),
                                "direction": int(behavior.direction), "info": _jsonable(behavior.info)}
        self.snapshots.append(snap)

    def finalize(self):
        if self._signals is not None or not self._rows:
            return self
        keys = []
        for row in self._rows:
            for k in row:
                if k not in keys:
                    keys.append(k)
        out = {}
        for k in keys:
            vals = [row.get(k, np.nan) for row in self._rows]
            try:
                out[k] = np.asarray(vals, dtype=float)
            except (TypeError, ValueError):
                out[k] = np.asarray([str(v) for v in vals])
        self._signals = out
        return self

    # ------------------------------------------------------------------ access
    @property
    def signals(self):
        if self._signals is None:
            self.finalize()
        return self._signals or {}

    def __getitem__(self, key):
        return self.signals[key]

    def __contains__(self, key):
        return key in self.signals

    @property
    def t(self):
        return self.signals.get("t", np.zeros(0))

    @property
    def duration(self):
        t = self.t
        return float(t[-1] - t[0]) if len(t) > 1 else 0.0

    def object_arrays(self, obj_id):
        rec = self.objects[obj_id]
        return {k: (np.asarray(v) if isinstance(v, list) else v) for k, v in rec.items()}

    def snapshot_at(self, t):
        # last planner snapshot at or before t (timeline)
        best = None
        for snap in self.snapshots:
            if snap.get("t", -1e9) <= t + 1e-9:
                best = snap
            else:
                break
        return best

    def events_of(self, kind):
        return [e for e in self.events if e["type"] == kind]

    # ------------------------------------------------------------------ persistence
    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {f"sig__{k}": v for k, v in self.signals.items()}
        for oid, rec in self.objects.items():
            for k, v in rec.items():
                if isinstance(v, list):
                    arrays[f"obj__{oid}__{k}"] = np.asarray(v)
        snap_meta = []
        for i, snap in enumerate(self.snapshots):
            meta = {}
            for k, v in snap.items():
                if isinstance(v, np.ndarray):
                    arrays[f"snap__{i}__{k}"] = v
                elif k == "trajectory":
                    for tk, tv in v.items():
                        arrays[f"snap__{i}__traj__{tk}"] = tv
                else:
                    meta[k] = v
            snap_meta.append(meta)
        meta = {"name": self.name, "scenario": self.scenario, "stack": self.stack, "seed": self.seed,
                "objects": {str(oid): {k: v for k, v in rec.items() if not isinstance(v, list)}
                            for oid, rec in self.objects.items()},
                "snapshots": snap_meta, "events": self.events, "road": self.road, "kpis": self.kpis,
                "profile": self.profile, "provenance": self.provenance, "metadata": self.metadata}
        np.savez_compressed(path.with_suffix(".npz"), **arrays)
        path.with_suffix(".json").write_text(json.dumps(_jsonable(meta), indent=1), encoding="utf-8")
        return path.with_suffix(".npz")

    @classmethod
    def load(cls, path):
        path = Path(path)
        meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        res = cls(meta["name"], meta["scenario"], meta["stack"], meta["seed"])
        for key in ("events", "road", "kpis", "profile", "provenance", "metadata"):
            setattr(res, key, meta.get(key, getattr(res, key)))
        data = np.load(path.with_suffix(".npz"), allow_pickle=False)
        signals, objects = {}, {}
        snaps = [dict(m) for m in meta.get("snapshots", [])]
        for key in data.files:
            parts = key.split("__")
            if parts[0] == "sig":
                signals[parts[1]] = data[key]
            elif parts[0] == "obj":
                oid = int(parts[1])
                objects.setdefault(oid, dict(meta["objects"].get(parts[1], {})))[parts[2]] = data[key].tolist()
            elif parts[0] == "snap":
                i = int(parts[1])
                if parts[2] == "traj":
                    snaps[i].setdefault("trajectory", {})[parts[3]] = data[key]
                else:
                    snaps[i][parts[2]] = data[key]
        res._signals, res.objects, res.snapshots = signals, objects, snaps
        return res

    def summary(self):
        return {"name": self.name, "duration": self.duration, "n_snapshots": len(self.snapshots),
                "n_events": len(self.events), "kpis": self.kpis}
