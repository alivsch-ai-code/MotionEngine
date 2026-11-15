"""Live run of the AD stack: the caller advances the simulation step by step.

    session = LiveSession("highway_cut_in")
    session.advance(0.5)        # half a second of simulated time
    session.step()              # one base step
    session.step_node()         # one block of the current base step (debugger single step)
    frame = session.frame()     # current state for a view
    blocks = session.inspect()  # inputs and outputs of every block at this moment
    result = session.finish()   # ADResult with metrics, as from run_scenario

Same setup, recording and evaluation as `run_scenario`. The desktop workbench and the REST service
(`/workbench/live`) use it for the live mode with pause and single step.
"""

from __future__ import annotations

import dataclasses
import math
import time

import numpy as np

from ..core.parameters import load_vehicle_preset
from ..framework.context import RunContext
from .results import ADResult
from .runner import _apply_kicks, _finish, _Recorder, _road_geometry, _services, _spec_dict
from .stack import build_graph, merge_stack


def signal_tree(value, depth=0, max_items=6):
    """A signal value as a tree of plain numbers, texts, lists and dicts for a view.

    Objects become {field: value}; long arrays and lists are reduced to their size, range and first elements,
    so the tree stays small for any signal. Unknown objects are named by their class."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, float, np.integer, np.floating)):
        v = float(value)
        return (int(v) if isinstance(value, (int, np.integer)) else v) if math.isfinite(v) else None
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "fiub":
            return f"array{value.shape}"
        flat = value.astype(float).ravel()
        if flat.size <= max_items and value.ndim <= 1:
            return [signal_tree(x) for x in flat]
        finite = flat[np.isfinite(flat)]
        return {"_kind": "array", "shape": list(value.shape), "min": float(finite.min()) if finite.size else None,
                "max": float(finite.max()) if finite.size else None, "first": [signal_tree(x) for x in flat[:max_items]],
                "last": signal_tree(flat[-1]) if flat.size else None}
    if depth >= 4:
        return type(value).__name__
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: signal_tree(getattr(value, f.name), depth + 1, max_items) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        items = list(value.items())
        out = {str(k): signal_tree(v, depth + 1, max_items) for k, v in items[:40]}
        if len(items) > 40:
            out["_more"] = len(items) - 40
        return out
    if isinstance(value, (list, tuple)):
        if len(value) <= max_items:
            return [signal_tree(v, depth + 1, max_items) for v in value]
        return {"_kind": "list", "count": len(value), "items": [signal_tree(v, depth + 1, max_items) for v in value[:max_items]]}
    return type(value).__name__


class LiveSession:
    def __init__(self, scenario, stack=None, seed=None, duration=None, scenario_params=None, vehicle=None,
                 graph=None, connections=None, environment=None):
        from ..runtime import Executor, Graph
        from ..world import build_scenario

        spec = _spec_dict(scenario, scenario_params)
        self.seed = int(seed if seed is not None else (spec.get("seed", 0) if isinstance(spec, dict) else 0))
        self.inst = build_scenario(spec, seed=self.seed)
        vehicle_name = vehicle or (spec.get("vehicle") if isinstance(spec, dict) else None) \
            or getattr(self.inst, "metadata", {}).get("vehicle") or "mid_size_sedan"
        vehicle_cfg = load_vehicle_preset(vehicle_name) if isinstance(vehicle_name, str) else vehicle_name
        scen_stack = (spec.get("stack") if isinstance(spec, dict) else None) or \
            getattr(self.inst, "metadata", {}).get("stack")
        self.stack = merge_stack(scen_stack, stack)
        graph_dict = graph or build_graph(self.stack)
        if connections is not None:
            graph_dict = {**graph_dict, "connections": [dict(c) for c in connections]}
        self.graph = Graph.from_dict(graph_dict)
        self.graph.validate().raise_for_errors()

        context = RunContext(dt=self.graph.base_dt, seed=self.seed, vehicle=vehicle_cfg, road=self.inst.road,
                             scenario=self.inst, services=_services(environment))
        self.executor = Executor(self.graph, context, recorder=False, profile=True)
        name = spec.get("name") if isinstance(spec, dict) else str(spec)
        self.result = ADResult(name, spec if isinstance(spec, dict) else {"name": str(spec)}, self.stack, self.seed)
        p = vehicle_cfg.vehicle
        self.ego_dims = {"length": p.length, "width": p.width, "wheelbase": p.wheelbase, "cg_to_rear": p.cg_to_rear,
                         "center_offset": (p.cg_to_front - p.cg_to_rear) / 2}
        self.result.metadata["ego_dims"] = self.ego_dims
        self.result.metadata["vehicle"] = vehicle_name if isinstance(vehicle_name, str) else "custom"
        self.recorder = _Recorder(self.result, self.executor, True, vehicle_cfg)
        self.executor.add_listener(step=self.recorder)
        self.t_end = float(duration or getattr(self.inst, "duration", None) or 30.0)
        self.road = _road_geometry(self.inst.road)
        self.result.road = self.road
        self.stopped = False
        self.stop_reason = ""
        self.finished = False
        self.wall = 0.0
        self.executor.reset()

    @property
    def t(self):
        return float(self.executor.t)

    @property
    def base_dt(self):
        return float(self.graph.base_dt)

    def step(self):
        """One base step. Returns False once the run has stopped."""
        if self.stopped:
            return False
        wall0 = time.perf_counter()
        try:
            self.executor.step()
            _apply_kicks(self.executor, self.recorder)
        except Exception as exc:
            self.stopped, self.stop_reason = True, f"Fehler: {exc}"
            self.result.add_event(self.t, "error", message=str(exc))
            return False
        finally:
            self.wall += time.perf_counter() - wall0
        self._check_stop()
        return not self.stopped

    def step_node(self):
        """Debugger single step: one block of the current base step. Returns {"node", "phase"} or None.

        The base step is complete once `mid_step` is False again; stop conditions are checked then."""
        if self.stopped:
            return None
        wall0 = time.perf_counter()
        try:
            res = self.executor.step_node()
            if not self.executor.mid_step:
                _apply_kicks(self.executor, self.recorder)
        except Exception as exc:
            self.stopped, self.stop_reason = True, f"Fehler: {exc}"
            self.result.add_event(self.t, "error", message=str(exc))
            return None
        finally:
            self.wall += time.perf_counter() - wall0
        if not self.executor.mid_step:
            self._check_stop()
        node = getattr(res, "node", None)
        return {"node": node, "phase": getattr(res, "phase", None)} if node else None

    @property
    def mid_step(self):
        return bool(self.executor.mid_step)

    def inspect(self, node=None):
        """Inputs and outputs of the blocks at this moment: {node: {inputs: {port: {from, value}}, outputs: {port: value},
        summary: {port: text}, profile: {...}}}. `node` limits the result to one block."""
        from ..framework.types import summarize

        ex = self.executor
        sources = {}
        for c in self.graph.to_dict().get("connections", []):
            sources[c["to"]] = c["from"]
        profile = ex.profiler.report() if ex.profiler.enabled else {}
        out = {}
        for nid in ([node] if node else list(self.graph.nodes)):
            if nid not in self.graph.nodes:
                continue
            try:
                inputs = ex.inputs_of(nid)
            except Exception:  # a block that cannot gather its inputs yet (before its first step)
                inputs = {}
            outputs = ex.outputs(nid)
            out[nid] = {
                "inputs": {p: {"from": sources.get(f"{nid}.{p}"), "value": signal_tree(v)} for p, v in inputs.items()},
                "outputs": {p: signal_tree(v) for p, v in outputs.items()},
                "summary": {p: summarize(v) for p, v in outputs.items()},
                "profile": profile.get(nid),
            }
        return out

    def advance(self, sim_dt, max_wall_time=None):
        """Simulate `sim_dt` seconds (at least one step). Returns the number of steps."""
        target = min(self.t + max(float(sim_dt), 0.0), self.t_end)
        wall0 = time.perf_counter()
        n = 0
        while not self.stopped and (n == 0 or self.t < target - 1e-9):
            self.step()
            n += 1
            if max_wall_time and time.perf_counter() - wall0 > max_wall_time:
                break
        return n

    def _check_stop(self):
        ego = self.executor.values.get("plant.ego")
        if ego is not None and not all(math.isfinite(getattr(ego, f)) for f in ("x", "y", "vx", "psi")):
            self.stopped, self.stop_reason = True, "numerisch instabil (NaN)"
        elif self.recorder.collision:
            self.stopped, self.stop_reason = True, "Kollision"
        elif self.recorder.goal:
            self.stopped, self.stop_reason = True, "Ziel erreicht"
        elif self.t >= self.t_end - 1e-9:
            self.stopped, self.stop_reason = True, "Simulationsdauer erreicht"

    def frame(self):
        """Current state for a view: time, last signal row, actors, index of the latest planner snapshot."""
        rows = self.result._rows
        objects = {}
        for oid, rec in self.result.objects.items():
            if rec.get("t"):
                objects[str(oid)] = {"type": rec.get("type"), "length": rec.get("length"), "width": rec.get("width"),
                                     **{k: rec[k][-1] for k in ("t", "x", "y", "psi", "v") if rec.get(k)}}
        return {"t": self.t, "t_end": self.t_end, "stopped": self.stopped, "stop_reason": self.stop_reason,
                "row": dict(rows[-1]) if rows else {}, "objects": objects, "n_steps": len(rows),
                "n_snapshots": len(self.result.snapshots), "n_events": len(self.result.events),
                "wall": self.wall, "mid_step": self.mid_step}

    def finish(self):
        """Close the executor and evaluate the run. Returns the ADResult."""
        if not self.finished:
            self.finished = True
            self.stopped = True
            try:
                self.executor.close()
            except Exception:  # the result is still valid
                pass
            _finish(self.result, self.executor, self.graph, self.inst, self.recorder, self.stack, self.seed,
                    self.stop_reason or "abgebrochen", self.wall)
        return self.result
