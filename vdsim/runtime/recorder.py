"""Recorder: time series of selected ports and component signals, plus events.

    rec = Recorder(ports=["plant.ego", "pid.y"], signals=True)
    ex = Executor(graph, recorder=rec)
    ex.run(10.0)
    t, y = rec.series("pid.y")
    t, vx = rec.series("plant.ego.vx")      # dataclass values are expanded into scalar fields

Column names:
    "node.port"            scalar / vector port value
    "node.port.field"      scalar field of a dataclass value (EgoState, ControlCommand, ...)
    "node:signal"          entry of component.signals
Missing samples are NaN (columns that appear later are padded).
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass

import numpy as np

SCALAR_TYPES = ("float", "bool")
_NUM = (int, float, bool, np.integer, np.floating, np.bool_)


@dataclass
class Event:
    t: float
    kind: str              # "breakpoint", "stop", "reload", "error", "info", custom kinds of components
    message: str
    node: str | None = None
    data: dict = field(default_factory=dict)

    def to_dict(self):
        return {"t": self.t, "kind": self.kind, "message": self.message, "node": self.node, "data": dict(self.data)}


def flatten(name, value, out):
    # value -> scalar columns (dataclasses expanded one level)
    if value is None:
        out[name] = np.nan
    elif isinstance(value, _NUM):
        out[name] = float(value)
    elif isinstance(value, np.ndarray):
        out[name] = value.astype(float, copy=True) if value.dtype.kind in "biuf" else value.copy()
    elif is_dataclass(value) and not isinstance(value, type):
        for f in fields(value):
            v = getattr(value, f.name)
            if isinstance(v, _NUM):
                out[f"{name}.{f.name}"] = float(v)
            elif v is None:
                out[f"{name}.{f.name}"] = np.nan
    else:
        out[name] = value


class Recorder:
    def __init__(self, ports="scalars", signals=True, decimation=1, max_samples=None):
        # ports: "scalars" (all float/bool ports), "all", None/[] (none) or list of "node.port"
        # signals: True (component.signals of all nodes), False, or list of node ids
        self.ports_spec = ports
        self.signals_spec = signals
        self.decimation = max(1, int(decimation))
        self.max_samples = max_samples
        self.clear()

    def clear(self):
        self.times = []
        self.columns = {}
        self.events = []
        self._keys = []
        self._nodes = []

    # ------------------------------------------------------------------ binding (executor compile)
    def bind(self, executor):
        graph = executor.graph
        spec = self.ports_spec
        keys = []
        if spec in ("scalars", "all"):
            for nid in graph.nodes:
                _, outs = graph.ports(nid)
                for pname, port in outs.items():
                    if spec == "all" or port.type in SCALAR_TYPES:
                        keys.append(f"{nid}.{pname}")
        elif spec:
            keys = [k for k in spec]
        self._keys = keys
        if self.signals_spec is True:
            self._nodes = [nid for nid, n in graph.nodes.items() if n.instance is not None]
        elif self.signals_spec:
            self._nodes = [n for n in self.signals_spec if n in graph.nodes]
        else:
            self._nodes = []

    # ------------------------------------------------------------------ sampling
    def sample(self, executor):
        if executor.tick % self.decimation:
            return
        if self.max_samples is not None and len(self.times) >= self.max_samples:
            return
        values = executor.values
        row = {}
        for key in self._keys:
            node, _, rest = key.partition(".")
            port, _, fld = rest.partition(".")
            v = values.get(f"{node}.{port}")
            if fld:
                v = getattr(v, fld, None) if v is not None else None
            flatten(key, v, row)
        nodes = executor.graph.nodes
        for nid in self._nodes:
            node = nodes.get(nid)
            sig = getattr(node.instance, "signals", None) if node is not None else None
            if sig:
                for name, v in sig.items():
                    flatten(f"{nid}:{name}", v, row)
        n = len(self.times)
        self.times.append(executor.t)
        cols = self.columns
        for name, v in row.items():
            col = cols.get(name)
            if col is None:
                col = cols[name] = [np.nan] * n
            elif len(col) < n:
                col.extend([np.nan] * (n - len(col)))
            col.append(v)
        for name, col in cols.items():
            if len(col) < n + 1:
                col.append(np.nan)

    def event(self, t, kind, message, node=None, **data):
        ev = Event(float(t), kind, message, node, data)
        self.events.append(ev)
        return ev

    # ------------------------------------------------------------------ access
    def names(self):
        return list(self.columns)

    @property
    def t(self):
        return np.asarray(self.times, dtype=float)

    def series(self, name):
        if name not in self.columns:
            raise KeyError(f"Signal '{name}' wurde nicht aufgezeichnet (vorhanden: {', '.join(self.columns)})")
        return self.t, _to_array(self.columns[name])

    def __getitem__(self, name):
        return self.series(name)[1]

    def __contains__(self, name):
        return name in self.columns

    def to_arrays(self):
        out = {"t": self.t}
        for name, col in self.columns.items():
            out[name] = _to_array(col)
        return out

    def events_of(self, kind=None, node=None):
        return [e for e in self.events if (kind is None or e.kind == kind) and (node is None or e.node == node)]

    def save_npz(self, path):
        arrays = {k: v for k, v in self.to_arrays().items() if v.dtype != object}
        np.savez_compressed(path, **arrays)
        return path

    def __len__(self):
        return len(self.times)


def _to_array(col):
    try:
        arr = np.asarray(col, dtype=float)
        return arr
    except (TypeError, ValueError):
        pass
    try:
        if col and all(isinstance(c, np.ndarray) for c in col) and len({c.shape for c in col}) == 1:
            return np.stack(col)
    except ValueError:
        pass
    out = np.empty(len(col), dtype=object)
    for i, c in enumerate(col):
        out[i] = c
    return out
