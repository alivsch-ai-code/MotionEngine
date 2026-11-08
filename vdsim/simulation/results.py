"""Simulation result: time series of all signals plus metadata; CSV/JSON/NPZ export and import."""

import json
from pathlib import Path

import numpy as np

from ..core.conventions import WHEEL_NAMES


class SimulationResult:
    def __init__(self, name="", metadata=None):
        self.name = name
        self.metadata = metadata or {}
        self.kpis = {}
        self._rows = 0
        self._data = {}
        self._arrays = None

    # recording
    def append(self, values):
        # scalars are kept as Python floats: a 0-d numpy array costs ~5x the memory of a float
        # (60 s single-track run: 37 MiB peak before, see benchmarks/README.md)
        for key, value in values.items():
            value = np.asarray(value, dtype=float)
            if value.ndim == 0:
                value = float(value)
            if key not in self._data:
                fill = np.nan if np.ndim(value) == 0 else np.full(np.shape(value), np.nan)
                self._data[key] = [fill] * self._rows
            self._data[key].append(value)
        self._rows += 1
        for key, column in self._data.items():
            if len(column) < self._rows:
                column.append(np.nan if np.ndim(column[-1]) == 0 else np.full(np.shape(column[-1]), np.nan))
        self._arrays = None

    def _finalize(self):
        if self._arrays is None:
            self._arrays = {key: np.array(column) for key, column in self._data.items()}
        return self._arrays

    # access
    def __getitem__(self, key):
        return self._finalize()[key]

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._finalize().get(key, default)

    @property
    def names(self):
        return list(self._data)

    @property
    def time(self):
        return self["t"]

    def __len__(self):
        return self._rows

    def wheel(self, key, wheel):
        return self[key][:, WHEEL_NAMES.index(wheel.upper())]

    # export / import
    def flat_columns(self):
        columns = {}
        for key, arr in self._finalize().items():
            if arr.ndim == 2 and arr.shape[1] == 4:
                for i, w in enumerate(WHEEL_NAMES):
                    columns[f"{key}_{w}"] = arr[:, i]
            elif arr.ndim == 1:
                columns[key] = arr
        return columns

    def to_csv(self, path):
        columns = self.flat_columns()
        np.savetxt(path, np.column_stack(list(columns.values())), delimiter=",",
                   header=",".join(columns), comments="", fmt="%.6g")

    def save(self, path):
        path = Path(path)
        if path.suffix.lower() == ".csv":
            return self.to_csv(path)
        meta = json.dumps({"name": self.name, "metadata": self.metadata, "kpis": self.kpis}, default=_json_default)
        if path.suffix.lower() == ".json":
            data = {key: arr.tolist() for key, arr in self._finalize().items()}
            path.write_text(json.dumps({"meta": json.loads(meta), "signals": data}), encoding="utf-8")
        else:
            np.savez_compressed(path, __meta__=np.array(meta), **self._finalize())

    @classmethod
    def load(cls, path):
        path = Path(path)
        if path.suffix.lower() == ".json":
            content = json.loads(path.read_text(encoding="utf-8"))
            meta, signals = content["meta"], {k: np.asarray(v) for k, v in content["signals"].items()}
        else:
            with np.load(path, allow_pickle=False) as npz:
                meta = json.loads(str(npz["__meta__"]))
                signals = {k: npz[k] for k in npz.files if k != "__meta__"}
        result = cls(meta.get("name", ""), meta.get("metadata", {}))
        result.kpis = meta.get("kpis", {})
        result._data = {k: list(v) for k, v in signals.items()}
        result._rows = len(next(iter(signals.values()))) if signals else 0
        return result


def _json_default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    return str(obj)
