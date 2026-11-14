"""Development environment: the functions of the desktop workbench (run_gui.py) as REST endpoints.

    /workbench/catalog                 AD scenarios, components per stack layer with their parameters,
                                       default stack and its signal-flow graph
    /workbench/graph                   graph of an edited stack (architecture view), with validation
    /workbench/runs                    start a run of the full AD stack in the background; progress, cancel
    /workbench/runs/{id}/result        signals, road, actors, events, KPIs, mission, runtime profile
    /workbench/runs/{id}/snapshots/{k} one planning cycle: candidates, selected trajectory, costs, prediction
    /workbench/runs/{id}/download      the complete result as JSON (same format as ADResult.save)
    /workbench/experiments             research mode: compare components, parameter sweep, Monte Carlo
    /matlab/analyze, /matlab/convert   MATLAB source -> analysis, Python or C code
    /knowledge/...                     literature references, component documentation, knowledge graph

All of it runs on vdsim.api, the same facade the desktop application and the CLI use. Only names from
the catalogs are accepted (scenarios, components); the service never opens a path given by a client.
"""

from __future__ import annotations

import logging
import math
import threading
import time
import uuid
from collections import OrderedDict
from typing import Any, Literal

import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

LAYER_KINDS = {"world": "world", "perception": "perception", "prediction": "predictor",
               "behavior": "behavior_planner", "planner": "trajectory_planner", "controller": "tracking_controller",
               "dynamics": "vehicle_dynamics", "actuators": "actuator", "plant": "vehicle_plant"}
MAX_RUNS = 12
MAX_EXPERIMENT_JOBS = 40
MAX_LIVE = 3
LIVE_IDLE_SECONDS = 600.0


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LayerSpec(_Strict):
    component: str = Field(max_length=120)
    params: dict[str, Any] = Field(default_factory=dict)


class Connection(_Strict):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_: str = Field(alias="from", max_length=80, pattern=r"^[A-Za-z0-9_]+\.[A-Za-z0-9_]+$")
    to: str = Field(max_length=80, pattern=r"^[A-Za-z0-9_]+\.[A-Za-z0-9_]+$")


class RunRequest(_Strict):
    scenario: str
    seed: int | None = Field(None, ge=0, le=2**31 - 1)
    duration: float | None = Field(None, gt=0.0, le=300.0)
    stack: dict[str, LayerSpec] = Field(default_factory=dict)
    scenario_params: dict[str, float | int | bool | str] = Field(default_factory=dict)
    name: str = Field("", max_length=80)
    connections: list[Connection] | None = Field(None, max_length=200,
                                                 description="rewired stack: replaces the default connections")


class GraphRequest(_Strict):
    stack: dict[str, LayerSpec] = Field(default_factory=dict)
    connections: list[Connection] | None = Field(None, max_length=200)


class AdvanceRequest(_Strict):
    seconds: float | None = Field(None, gt=0.0, le=2.0, description="simulated time to advance")
    steps: int | None = Field(None, ge=1, le=200, description="base steps to advance (single step: 1)")
    known_snapshots: int = Field(0, ge=0, description="planner snapshots the client already has")


class ImportRequest(_Strict):
    meta: dict[str, Any]
    npz: str = Field(max_length=60_000_000, description="base64 of the .npz file")
    name: str = Field("", max_length=80)


class ExperimentRequest(_Strict):
    kind: Literal["compare", "sweep", "monte_carlo"]
    base: RunRequest
    layer: str | None = None                                             # compare
    variants: dict[str, LayerSpec] = Field(default_factory=dict)         # compare: label -> component
    grid: dict[str, list[float | int | bool | str]] = Field(default_factory=dict)   # sweep: dotted path -> values
    distributions: dict[str, list[float]] = Field(default_factory=dict)  # monte carlo: path -> [low, high]
    n: int = Field(10, ge=1, le=MAX_EXPERIMENT_JOBS)
    seed: int = 0


class MatlabRequest(_Strict):
    source: str = Field(min_length=1, max_length=200_000)
    target: Literal["python", "c"] = "python"


def _clean(obj):
    """JSON-safe copy: numpy -> lists, NaN/inf -> None."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _clean(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, (np.integer, np.bool_)):
        return obj.item()
    if isinstance(obj, (str, int, bool)) or obj is None:
        return obj
    if hasattr(obj, "to_dict"):
        return _clean(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return _clean({k: v for k, v in vars(obj).items() if not k.startswith("_")})
    return str(obj)


def _decimate(n, max_points):
    if n <= max_points:
        return np.arange(n)
    return np.unique(np.linspace(0, n - 1, max_points).round().astype(int))


def _snapshot_view(snap, max_candidates=100):
    """One planning cycle with at most `max_candidates` candidates (the selected one is kept)."""
    s = dict(snap)
    n = len(s.get("candidates_cost", []))
    keep = _decimate(n, int(min(max(max_candidates, 10), 400))).tolist()
    best = int(s.get("best_index", -1))
    if 0 <= best < n and best not in keep:
        keep.append(best)
    for key in ("candidates_x", "candidates_y", "candidates_s", "candidates_d", "candidates_cost",
                "candidates_status"):
        if key in s and len(s[key]):
            s[key] = np.asarray(s[key])[keep]
    if s.get("candidates_reason"):
        s["candidates_reason"] = [s["candidates_reason"][i] for i in keep if i < len(s["candidates_reason"])]
    s["best_index"] = keep.index(best) if best in keep else -1
    return _clean(s)


def _connections(items):
    return None if items is None else [{"from": c.from_, "to": c.to} for c in items]


MAX_NPZ_BYTES = 300_000_000     # uncompressed size of an imported result


def _load_result(meta, npz_base64):
    """ADResult from the two files the library writes (meta JSON + arrays), without pickle."""
    import base64
    import binascii
    import io
    import json
    import tempfile
    import zipfile
    from pathlib import Path

    from ..ad.results import ADResult

    try:
        raw = base64.b64decode(npz_base64, validate=True)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if sum(i.file_size for i in z.infolist()) > MAX_NPZ_BYTES:
                raise ValueError("result too large")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result"
            path.with_suffix(".npz").write_bytes(raw)
            path.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")
            res = ADResult.load(path)
        if "t" not in res.signals or not len(res.t):
            raise ValueError("no time signal")
        if not isinstance(res.metadata, dict) or not isinstance(res.kpis, dict) or not isinstance(res.events, list):
            raise ValueError("unexpected metadata")
        return res
    except (binascii.Error, zipfile.BadZipFile, KeyError, ValueError, TypeError, IndexError, AttributeError,
            OSError) as exc:
        raise HTTPException(status_code=422, detail=f"not a result file: {type(exc).__name__}") from None


class _Jobs:
    """Background jobs (one worker thread), newest kept."""

    def __init__(self, capacity):
        self.items: OrderedDict[str, dict] = OrderedDict()
        self.lock = threading.Lock()
        self.capacity = capacity
        self.queue_lock = threading.Lock()      # one job computes at a time

    def add(self, kind, name, request):
        job = {"id": uuid.uuid4().hex[:12], "kind": kind, "name": name, "state": "queued", "progress": 0.0,
               "error": None, "created": time.time(), "finished": None, "request": request, "cancel": False,
               "result": None, "summary": None}
        with self.lock:
            self.items[job["id"]] = job
            done = [k for k, j in self.items.items() if j["state"] not in ("queued", "running")]
            while len(self.items) > self.capacity and done:
                del self.items[done.pop(0)]
        return job

    def get(self, job_id):
        with self.lock:
            job = self.items.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job")
        return job

    def view(self, job):
        return {k: _clean(job[k]) for k in ("id", "kind", "name", "state", "progress", "error", "created", "finished",
                                            "summary", "request")}

    def active(self):
        with self.lock:
            return sum(1 for j in self.items.values() if j["state"] in ("queued", "running"))


class _Cancelled(Exception):
    pass


def create_router(secured, limiter, max_sim_time, max_wall_time):
    from .. import api

    router = APIRouter(dependencies=secured)
    runs = _Jobs(MAX_RUNS)
    experiments = _Jobs(MAX_RUNS)
    scenario_names = {s["name"] for s in api.list_scenarios()}
    components = {f"{c['kind']}/{c['name']}": c for c in api.list_components()}
    cache: dict[str, Any] = {}

    def check_stack(stack):
        out = {}
        for layer, spec in stack.items():
            kind = LAYER_KINDS.get(layer)
            if kind is None:
                raise HTTPException(status_code=422, detail=f"unknown layer '{layer}', available: {sorted(LAYER_KINDS)}")
            comp = components.get(spec.component)
            if comp is None or comp["kind"] != kind:
                names = sorted(k for k, c in components.items() if c["kind"] == kind)
                raise HTTPException(status_code=422, detail=f"unknown component '{spec.component}' for layer "
                                                            f"'{layer}', available: {names}")
            out[layer] = {"component": spec.component, **({"params": spec.params} if spec.params else {})}
        return out

    def check_run(req: RunRequest):
        if req.scenario not in scenario_names:
            raise HTTPException(status_code=422, detail=f"unknown scenario '{req.scenario}', available: "
                                                        f"{sorted(scenario_names)}")
        duration = min(req.duration, max_sim_time) if req.duration else None
        stack = check_stack(req.stack)
        out = {"scenario": req.scenario, "seed": req.seed, "duration": duration, "stack": stack,
               "scenario_params": dict(req.scenario_params) or None}
        if req.connections is not None:
            out["connections"] = _connections(req.connections)
            issues = graph_issues({**api.build_graph(stack), "connections": out["connections"]})
            if issues:
                raise HTTPException(status_code=422, detail="invalid connections: " + "; ".join(issues[:5]))
        return out

    def graph_issues(g):
        try:
            return api.validate_graph(g)
        except Exception:  # the details stay in the server log
            logger.exception("graph validation failed")
            return ["the graph could not be validated"]

    # ------------------------------------------------------------------ catalog and architecture
    @router.get("/workbench/catalog", tags=["workbench"], summary="Scenarios, components per layer, default stack")
    def catalog():
        if "catalog" not in cache:
            layers = []
            default = api.default_stack()
            for layer, kind in LAYER_KINDS.items():
                opts = [{"spec": spec, "label": c.get("label") or c["name"], "version": c.get("version"),
                         "language": c.get("language"), "params": _clean(c.get("params") or []),
                         "inputs": sorted((c.get("inputs") or {}).keys()),
                         "outputs": sorted((c.get("outputs") or {}).keys())}
                        for spec, c in sorted(components.items()) if c["kind"] == kind]
                layers.append({"layer": layer, "kind": kind, "default": (default.get(layer) or {}).get("component"),
                               "components": opts})
            scenarios = [{k: s.get(k) for k in ("name", "type", "label", "description", "duration", "seed")}
                         for s in api.list_scenarios()]
            from ..research import KPI_INFO
            cache["catalog"] = _clean({"scenarios": scenarios, "layers": layers, "default_stack": default,
                                       "kpi_info": KPI_INFO, "limits": {"max_duration": max_sim_time}})
        return cache["catalog"]

    @router.post("/workbench/graph", tags=["workbench"], summary="Signal-flow graph of a stack, with validation")
    def graph(req: GraphRequest):
        g = api.build_graph(check_stack(req.stack))
        default = [dict(c) for c in g["connections"]]
        if req.connections is not None:
            g["connections"] = _connections(req.connections)
        issues = graph_issues(g)
        def port_types(node, side):
            return {k: {"type": v.get("type", ""), "optional": bool(v.get("optional"))}
                    for k, v in (components.get(node["component"], {}).get(side) or {}).items()}

        ports = {n["id"]: {"inputs": sorted(port_types(n, "inputs")), "outputs": sorted(port_types(n, "outputs")),
                           "input_types": port_types(n, "inputs"), "output_types": port_types(n, "outputs")}
                 for n in g["nodes"]}
        return _clean({**g, "issues": issues, "ports": ports, "default_connections": default})

    # ------------------------------------------------------------------ runs
    def store(job, result):
        job["result"] = result
        job["summary"] = {"duration": result.duration, "n_snapshots": len(result.snapshots),
                          "n_events": len(result.events), "mission": result.metadata.get("mission"),
                          "stop_reason": result.metadata.get("stop_reason"),
                          "wall_time": result.metadata.get("wall_time")}
        job.update(state="done", progress=1.0, finished=time.time())

    def execute(job):
        def progress(t, t_end):
            if job["cancel"]:
                raise _Cancelled
            job["progress"] = min(float(t) / max(float(t_end), 1e-9), 1.0)

        with runs.queue_lock:
            if job["cancel"]:
                job.update(state="cancelled", finished=time.time())
                return
            job["state"] = "running"
            try:
                r = job["request"]
                result = api.run(r["scenario"], stack=r["stack"] or None, seed=r["seed"], duration=r["duration"],
                                 scenario_params=r["scenario_params"], progress=progress,
                                 connections=r.get("connections"))
                store(job, result)
            except _Cancelled:
                job.update(state="cancelled", finished=time.time())
            except Exception as exc:  # reported to the client
                job.update(state="failed", error=f"{type(exc).__name__}: {exc}", finished=time.time())

    @router.post("/workbench/runs", status_code=202, tags=["workbench"], summary="Run the AD stack on a scenario")
    def start_run(req: RunRequest):
        request = check_run(req)
        if runs.active() >= 3:
            raise HTTPException(status_code=409, detail="too many runs waiting, wait for one to finish")
        job = runs.add("run", req.name or req.scenario, request)
        threading.Thread(target=execute, args=(job,), daemon=True).start()
        return runs.view(job)

    @router.get("/workbench/runs", tags=["workbench"], summary="Runs, most recent first")
    def list_runs():
        with runs.lock:
            jobs = sorted(runs.items.values(), key=lambda j: j["created"], reverse=True)
        return [runs.view(j) for j in jobs]

    @router.get("/workbench/runs/{job_id}", tags=["workbench"])
    def get_run(job_id: str):
        return runs.view(runs.get(job_id))

    @router.post("/workbench/runs/{job_id}/cancel", tags=["workbench"])
    def cancel_run(job_id: str):
        job = runs.get(job_id)
        job["cancel"] = True
        return runs.view(job)

    @router.delete("/workbench/runs/{job_id}", status_code=204, tags=["workbench"])
    def delete_run(job_id: str):
        job = runs.get(job_id)
        job["cancel"] = True
        with runs.lock:
            runs.items.pop(job_id, None)

    def result_of(job_id):
        job = runs.get(job_id)
        if job["result"] is None:
            raise HTTPException(status_code=409, detail=f"run is {job['state']}")
        return job, job["result"]

    @router.get("/workbench/runs/{job_id}/result", tags=["workbench"],
                summary="Signals, road, actors, events, KPIs, mission and runtime profile of a run")
    def run_result(job_id: str, max_points: int = 1500):
        job, res = result_of(job_id)
        max_points = int(min(max(max_points, 50), 10000))
        sig = res.signals
        idx = _decimate(len(res.t), max_points)
        signals = {k: np.asarray(v)[idx] for k, v in sig.items() if np.ndim(v) == 1 and len(v) == len(res.t)}
        objects = {}
        for oid, o in res.objects.items():
            n = len(o["t"])
            oi = _decimate(n, max_points)
            objects[str(oid)] = {"type": o.get("type"), "length": o.get("length"), "width": o.get("width"),
                                 **{k: np.asarray(o[k])[oi] for k in ("t", "x", "y", "psi", "v") if k in o
                                    and len(o[k]) == n}}
        ego = {"length": 4.8, "width": 1.85}
        try:
            from ..core.parameters import load_vehicle_preset
            v = load_vehicle_preset(str(res.metadata.get("vehicle") or "mid_size_sedan")).vehicle
            ego = {"length": float(v.length), "width": float(v.width)}
        except Exception:  # display only: fall back to the default outline
            pass
        return _clean({
            "id": job["id"], "name": job["name"], "request": job["request"], "signals": signals, "objects": objects,
            "road": res.road, "events": res.events, "kpis": res.kpis, "profile": res.profile,
            "mission": res.metadata.get("mission"), "stop_reason": res.metadata.get("stop_reason"),
            "wall_time": res.metadata.get("wall_time"), "duration": res.duration,
            "snapshots": [{"k": k, "t": s["t"], "mode": s.get("mode"), "fallback": s.get("fallback"),
                           "reinitialized": s.get("reinitialized"), "n_candidates": s.get("n_candidates"),
                           "compute_time": s.get("compute_time"),
                           "maneuver": (s.get("behavior") or {}).get("maneuver")}
                          for k, s in enumerate(res.snapshots)],
            "ego": ego,
            "provenance": getattr(res, "provenance", None),
        })

    @router.get("/workbench/runs/{job_id}/snapshots/{k}", tags=["workbench"],
                summary="One planning cycle: candidates, selected trajectory, cost terms, prediction")
    def run_snapshot(job_id: str, k: int, max_candidates: int = 100):
        _, res = result_of(job_id)
        if not 0 <= k < len(res.snapshots):
            raise HTTPException(status_code=404, detail="unknown snapshot")
        return _snapshot_view(res.snapshots[k], max_candidates)

    @router.get("/workbench/runs/{job_id}/download", tags=["workbench"],
                summary="Complete result as one JSON file (metadata + arrays), accepted by /workbench/runs/import")
    def run_download(job_id: str):
        import base64
        import json
        import tempfile
        from pathlib import Path

        job, res = result_of(job_id)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result"
            res.save(path)
            meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
            npz = base64.b64encode(path.with_suffix(".npz").read_bytes()).decode("ascii")
        return JSONResponse({"format": "motionengine-ad-result", "version": 1, "name": job["name"],
                             "meta": _clean(meta), "npz": npz},
                            headers={"Content-Disposition": f'attachment; filename="{job["id"]}.json"'})

    @router.post("/workbench/runs/import", status_code=201, tags=["workbench"],
                 summary="Load a saved result (download of this service, or the .json + .npz pair of the library)")
    def import_run(req: ImportRequest):
        res = _load_result(req.meta, req.npz)
        scenario = res.scenario.get("name") if isinstance(res.scenario, dict) else str(res.scenario)
        job = runs.add("import", req.name or str(res.name or scenario), {
            "scenario": str(scenario), "seed": res.seed, "duration": None, "scenario_params": None,
            "stack": {k: {"component": str(v["component"]), **({"params": v["params"]} if v.get("params") else {})}
                      for k, v in (res.stack or {}).items() if isinstance(v, dict) and "component" in v}})
        store(job, res)
        return runs.view(job)

    # ------------------------------------------------------------------ live mode
    live: OrderedDict[str, dict] = OrderedDict()
    live_lock = threading.Lock()

    def live_get(session_id):
        with live_lock:
            entry = live.get(session_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="unknown live session")
        entry["used"] = time.time()
        return entry

    def live_frame(entry, known_snapshots=0):
        session = entry["session"]
        frame = session.frame()
        snaps = session.result.snapshots
        frame["snapshot"] = _snapshot_view(snaps[-1], 60) if len(snaps) > known_snapshots else None
        frame["events"] = session.result.events[-20:]
        return _clean(frame)

    @router.post("/workbench/live", status_code=201, tags=["workbench"],
                 summary="Start a live session: the client advances the run (play, pause, single step)")
    def live_start(req: RunRequest):
        r = check_run(req)
        now = time.time()
        with live_lock:
            for key in [k for k, e in live.items() if now - e["used"] > LIVE_IDLE_SECONDS]:
                live.pop(key)
            if len(live) >= MAX_LIVE:
                live.popitem(last=False)
        try:
            session = api.live(r["scenario"], stack=r["stack"] or None, seed=r["seed"],
                               duration=r["duration"], scenario_params=r["scenario_params"],
                               connections=r.get("connections"))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"{type(exc).__name__}: could not start the run") from None
        session.t_end = min(session.t_end, max_sim_time)
        entry = {"id": uuid.uuid4().hex[:12], "session": session, "request": r, "name": req.name or req.scenario,
                 "used": now, "lock": threading.Lock()}
        with live_lock:
            live[entry["id"]] = entry
        ego = {"length": float(session.ego_dims["length"]), "width": float(session.ego_dims["width"])}
        return _clean({"id": entry["id"], "name": entry["name"], "base_dt": session.base_dt, "road": session.road,
                       "ego": ego, "frame": live_frame(entry)})

    @router.post("/workbench/live/{session_id}/advance", tags=["workbench"],
                 summary="Advance a live session by simulated seconds or base steps")
    def live_advance(session_id: str, req: AdvanceRequest):
        entry = live_get(session_id)
        session = entry["session"]
        with entry["lock"]:
            if session.finished:
                raise HTTPException(status_code=409, detail="the session is finished")
            if req.steps:
                for _ in range(req.steps):
                    if not session.step():
                        break
            else:
                session.advance(req.seconds or 0.1, max_wall_time=5.0)
            return live_frame(entry, req.known_snapshots)

    @router.post("/workbench/live/{session_id}/finish", tags=["workbench"],
                 summary="End a live session and keep its result as a run")
    def live_finish(session_id: str):
        entry = live_get(session_id)
        with entry["lock"]:
            result = entry["session"].finish()
        with live_lock:
            live.pop(session_id, None)
        job = runs.add("live", entry["name"], entry["request"])
        store(job, result)
        return runs.view(job)

    @router.delete("/workbench/live/{session_id}", status_code=204, tags=["workbench"])
    def live_delete(session_id: str):
        with live_lock:
            entry = live.pop(session_id, None)
        if entry is not None:
            with entry["lock"]:
                try:
                    entry["session"].executor.close()
                except Exception:  # nothing to keep
                    pass

    # ------------------------------------------------------------------ research
    def run_experiment(job, jobs_spec):
        from ..research import run_job

        with experiments.queue_lock:
            job["state"] = "running"
            records = []
            try:
                for i, spec in enumerate(jobs_spec):
                    if job["cancel"]:
                        raise _Cancelled
                    records.append(run_job(spec))
                    job["progress"] = (i + 1) / len(jobs_spec)
                    job["result"] = _records_view(records)
                job.update(state="done", finished=time.time())
            except _Cancelled:
                job.update(state="cancelled", finished=time.time())
            except Exception as exc:  # reported to the client
                job.update(state="failed", error=f"{type(exc).__name__}: {exc}", finished=time.time())

    def _records_view(records):
        return [{"label": r.get("label", ""), "ok": bool(r.get("ok")), "error": r.get("error"),
                 "kpis": r.get("kpis", {}), "overrides": r.get("overrides") or r.get("params") or {},
                 "wall_time": r.get("wall_time"), "mission": (r.get("mission") or {}).get("passed")
                 if isinstance(r.get("mission"), dict) else None} for r in records]

    @router.post("/workbench/experiments", status_code=202, tags=["workbench"],
                 summary="Research mode: compare components, parameter sweep or Monte Carlo")
    def start_experiment(req: ExperimentRequest):
        from ..research import compare_components, monte_carlo, parameter_sweep

        base = {k: v for k, v in check_run(req.base).items() if v is not None and k != "connections"}
        base["snapshots"] = False
        if req.kind == "compare":
            if not req.layer or not req.variants:
                raise HTTPException(status_code=422, detail="compare needs a layer and variants")
            variants = {label: spec[req.layer] for label, spec in
                        ((label, check_stack({req.layer: v})) for label, v in req.variants.items())}
            jobs_spec = compare_components(base, req.layer, variants)
        elif req.kind == "sweep":
            if not req.grid:
                raise HTTPException(status_code=422, detail="sweep needs a grid")
            jobs_spec = parameter_sweep(base, {k: list(v) for k, v in req.grid.items()})
        else:
            if not req.distributions or any(len(v) != 2 for v in req.distributions.values()):
                raise HTTPException(status_code=422, detail="monte_carlo needs distributions {path: [low, high]}")
            jobs_spec = monte_carlo(base, {k: ("uniform", v[0], v[1]) for k, v in req.distributions.items()},
                                    req.n, req.seed)
        jobs_spec = list(jobs_spec)
        for path in list(req.grid) + list(req.distributions):
            if not path.startswith(("stack.", "scenario_params.", "seed", "duration")):
                raise HTTPException(status_code=422, detail=f"path '{path}' must start with stack. or scenario_params.")
        if len(jobs_spec) > MAX_EXPERIMENT_JOBS:
            raise HTTPException(status_code=422, detail=f"{len(jobs_spec)} runs requested, at most "
                                                        f"{MAX_EXPERIMENT_JOBS}")
        if experiments.active() >= 2:
            raise HTTPException(status_code=409, detail="an experiment is already running")
        job = experiments.add(req.kind, f"{req.kind}: {req.base.scenario}", {"n_runs": len(jobs_spec),
                                                                             **req.model_dump()})
        job["result"] = []
        threading.Thread(target=run_experiment, args=(job, jobs_spec), daemon=True).start()
        return {**experiments.view(job), "records": []}

    @router.get("/workbench/experiments", tags=["workbench"])
    def list_experiments():
        with experiments.lock:
            jobs = sorted(experiments.items.values(), key=lambda j: j["created"], reverse=True)
        return [experiments.view(j) for j in jobs]

    @router.get("/workbench/experiments/{job_id}", tags=["workbench"])
    def get_experiment(job_id: str):
        job = experiments.get(job_id)
        return {**experiments.view(job), "records": _clean(job["result"] or [])}

    @router.post("/workbench/experiments/{job_id}/cancel", tags=["workbench"])
    def cancel_experiment(job_id: str):
        job = experiments.get(job_id)
        job["cancel"] = True
        return experiments.view(job)

    # ------------------------------------------------------------------ MATLAB
    @router.post("/matlab/analyze", tags=["matlab"], summary="Functions, variables and dependencies of MATLAB code")
    def matlab_analyze(req: MatlabRequest):
        with limiter.slot():
            try:
                info = api.matlab_analyze(req.source if "\n" in req.source else req.source + "\n")
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f"{type(exc).__name__}: {exc}") from None
        return _clean(info)

    @router.post("/matlab/convert", tags=["matlab"], summary="MATLAB code -> Python or C")
    def matlab_convert(req: MatlabRequest):
        with limiter.slot():
            try:
                out = api.matlab_convert(req.source if "\n" in req.source else req.source + "\n", req.target)
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f"{type(exc).__name__}: {exc}") from None
        return _clean(out)

    # ------------------------------------------------------------------ knowledge
    def kg():
        if "kg" not in cache:
            cache["kg"] = api.knowledge_graph()
        return cache["kg"]

    @router.get("/knowledge/references", tags=["knowledge"], summary="Literature references of the library")
    def references():
        if "refs" not in cache:
            cache["refs"] = _clean(api.references())
        return cache["refs"]

    @router.get("/knowledge/components/{kind}/{name}", tags=["knowledge"], summary="Documentation of a component")
    def component_doc(kind: str, name: str):
        comp = components.get(f"{kind}/{name}")
        if comp is None:
            raise HTTPException(status_code=404, detail="unknown component")
        return _clean(api.describe_component(f"{kind}/{name}"))

    @router.get("/knowledge/nodes", tags=["knowledge"], summary="Nodes of the knowledge graph (search)")
    def knowledge_nodes(q: str = "", type: str = "", limit: int = 200):
        ql = q.lower()
        out = []
        for node in kg().nodes.values():
            d = node.to_dict()
            if type and d["type"] != type:
                continue
            if ql and ql not in d["id"].lower() and ql not in str(d.get("label", "")).lower():
                continue
            out.append({"id": d["id"], "type": d["type"], "label": d.get("label", "")})
            if len(out) >= min(max(limit, 1), 1000):
                break
        return out

    @router.get("/knowledge/explain", tags=["knowledge"], summary="Everything linked to a node, as text and graph")
    def knowledge_explain(id: str):
        g = kg()
        info = g.explain(id)
        if not info.get("found"):
            raise HTTPException(status_code=404, detail="unknown node")
        hood = g.neighborhood(info["id"], depth=1, limit=80)
        return _clean({"info": info, "markdown": g.explain_markdown(id),
                       "nodes": [n.to_dict() for n in hood.nodes.values()],
                       "edges": [e.to_dict() for e in hood.edges]})

    return router
