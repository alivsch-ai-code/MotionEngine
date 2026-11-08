"""FastAPI application of the MotionEngine REST service.

Configuration (environment variables):

    MOTIONENGINE_API_KEY          if set, every endpoint except /health requires the header X-API-Key
    MOTIONENGINE_MAX_CONCURRENCY  simultaneous compute requests (default: number of CPUs); further
                                  requests get 503 instead of queueing without bound
    MOTIONENGINE_MAX_SIM_TIME     upper bound of the simulated time per request, s (default 120)
    MOTIONENGINE_MAX_WALL_TIME    wall-clock budget per simulation, s (default 60)
    MOTIONENGINE_CORS_ORIGINS     comma separated list of allowed CORS origins (default: none)
    ANTHROPIC_API_KEY             enables the chat assistant (/chat, see vdsim/service/chat.py)

All compute endpoints are synchronous `def` handlers: FastAPI runs them in its thread pool, so the
event loop stays responsive. Only names listed by the catalog endpoints are accepted (vehicle
presets, scenarios, planner configurations); the service never opens a path given by a client.
"""

from __future__ import annotations

import math
import os
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import fields
from pathlib import Path

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse
from fastapi.security import APIKeyHeader

from .. import __version__
from .metrics import Metrics
from .schemas import (
    ChatRequest,
    ConnectRequest,
    EvaluateRequest,
    ExplainResponse,
    HealthResponse,
    KPIModel,
    ParameterInfo,
    PlanCycle,
    PlannedTrajectoryModel,
    PlanRequest,
    PlanResponse,
    PredictedObjectModel,
    PredictRequest,
    PredictResponse,
    RoadGeometry,
    SimulateRequest,
    SimulateResponse,
    TrainJob,
    TrainRequest,
    TrajectoryRequest,
    TrajectoryResponse,
    VehicleAnalysis,
    VehicleCatalog,
    VehicleResponse,
)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ----------------------------------------------------------------------------- helpers
def _finite(value):
    v = float(value)
    return v if math.isfinite(v) else None


def _list(values):
    return [_finite(v) for v in np.asarray(values, dtype=float).ravel()]


def _decimate_index(n, max_points):
    # indices of at most max_points samples, first and last included
    if n <= max_points:
        return np.arange(n)
    return np.unique(np.linspace(0, n - 1, max_points).round().astype(int))


# language-neutral codes of the simulator's stop reasons (the library reports German text)
STOP_CODES = {
    "Simulationsdauer erreicht": "duration_reached", "Ende der Trajektorie": "end_of_trajectory",
    "Fahrzeug steht": "vehicle_stopped", "Zielgeschwindigkeit erreicht": "target_speed_reached",
    "Kollision mit vorausfahrendem Fahrzeug": "collision_lead_vehicle", "numerisch instabil (NaN)": "numerical_instability",
    "Fahrzeug instabil (Schleudern/Überschlag)": "vehicle_unstable", "Rechenzeitlimit": "wall_time_limit",
}


KPI_GROUP_CODES = {
    "Fahrdynamik": "dynamics", "Bahnführung": "tracking", "Allgemein": "general", "Komfort": "comfort",
    "Energie": "energy", "Normtest": "standard_test", "Bremsen": "braking", "Beschleunigen": "acceleration",
    "Rennstrecke": "race_track", "Frequenzgang": "frequency_response", "Fahrerassistenz": "driver_assistance",
}
KPI_VALUE_CODES = {
    "ja": "yes", "nein": "no", "nicht unkomfortabel": "not_uncomfortable",
    "etwas unkomfortabel": "a_little_uncomfortable", "ziemlich unkomfortabel": "fairly_uncomfortable",
    "unkomfortabel": "uncomfortable", "sehr unkomfortabel": "very_uncomfortable",
    "extrem unkomfortabel": "extremely_uncomfortable",
}


def _kpi_model(k):
    d = k.to_dict()
    value = d["value"]
    code = KPI_VALUE_CODES.get(value, "other") if isinstance(value, str) else None
    return KPIModel(**{**d, "value": value if isinstance(value, str) or value is None else _finite(value),
                       "value_code": code, "group_code": KPI_GROUP_CODES.get(d["group"], "other")})


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


def _require(name, allowed, what):
    # Returns the catalog's own string, never the client's: names that reach a file path (presets,
    # scenarios, planner configurations) come from the directory listing, not from the request.
    canonical = {str(a): a for a in allowed}.get(str(name))
    if canonical is None:
        raise HTTPException(status_code=422, detail=f"unknown {what} '{name}', available: {sorted(allowed)}")
    return canonical


class _Limiter:
    # non-blocking concurrency limit for the CPU bound endpoints
    def __init__(self, n, metrics):
        self._sem = threading.BoundedSemaphore(max(int(n), 1))
        self._metrics = metrics

    @contextmanager
    def slot(self):
        if not self._sem.acquire(blocking=False):
            self._metrics.reject()
            raise HTTPException(status_code=503, detail="server busy, retry later",
                                headers={"Retry-After": "1"})
        try:
            yield
        finally:
            self._sem.release()


# ----------------------------------------------------------------------------- catalogs
def _catalog():
    from ..core.parameters import default_config_dir
    from ..core.registry import available
    from ..planning.config import available_configs
    from ..simulation.scenario import ScenarioManager

    vehicles = sorted(p.stem for p in (default_config_dir() / "vehicles").glob("*.json"))
    scenarios = ScenarioManager().names()
    return {"presets": vehicles, "scenarios": scenarios, "planner_configs": available_configs(),
            "vehicle_model": available("vehicle_model"), "tire_model": available("tire_model"),
            "lateral_controller": available("lateral_controller"),
            "longitudinal_controller": available("longitudinal_controller"), "maneuver": available("maneuver")}


# ----------------------------------------------------------------------------- application
def create_app(api_key=None, max_concurrency=None, max_sim_time=None, max_wall_time=None, cors_origins=None,
               model_dir=None, web_dir=None, chat_client=None):
    api_key = api_key if api_key is not None else os.environ.get("MOTIONENGINE_API_KEY") or None
    max_concurrency = max_concurrency or int(_env_float("MOTIONENGINE_MAX_CONCURRENCY", os.cpu_count() or 2))
    max_sim_time = max_sim_time or _env_float("MOTIONENGINE_MAX_SIM_TIME", 120.0)
    max_wall_time = max_wall_time or _env_float("MOTIONENGINE_MAX_WALL_TIME", 60.0)
    if cors_origins is None:
        cors_origins = [o.strip() for o in os.environ.get("MOTIONENGINE_CORS_ORIGINS", "").split(",") if o.strip()]

    metrics = Metrics()
    limiter = _Limiter(max_concurrency, metrics)
    catalog = _catalog()
    from ..learning import ModelStore
    models = ModelStore(model_dir)
    train_jobs = {}
    train_lock = threading.Lock()
    train_pool = ThreadPoolExecutor(max_workers=1)
    allowed_model_hosts = {h.strip().lower() for h in os.environ.get("MOTIONENGINE_ALLOWED_MODEL_HOSTS", "").split(",")
                           if h.strip()}

    def check_key(key: str | None = Security(_api_key_header)):
        if api_key and not (key and secrets.compare_digest(key, api_key)):
            raise HTTPException(status_code=401, detail="invalid or missing API key",
                                headers={"WWW-Authenticate": "APIKey"})

    app = FastAPI(
        title="MotionEngine API",
        version=__version__,
        description="Vehicle dynamics simulation, Werling trajectory planning and motion prediction. "
                    "SI units, ISO 8855 axes (x forward, y left, z up).",
        openapi_tags=[{"name": "service"}, {"name": "vehicle"}, {"name": "trajectory"}, {"name": "simulation"},
                      {"name": "planning"}, {"name": "prediction"}],
    )
    app.state.metrics = metrics
    app.state.limits = {"max_concurrency": max_concurrency, "max_sim_time": max_sim_time,
                        "max_wall_time": max_wall_time}
    if cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_methods=["GET", "POST"],
                           allow_headers=["*"])

    @app.middleware("http")
    async def record(request: Request, call_next):
        metrics.change_in_flight(1)
        tic = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            metrics.change_in_flight(-1)
            route = request.scope.get("route")
            path = getattr(route, "path", "unmatched")
            metrics.observe(request.method, path, status, time.perf_counter() - tic)

    secured = [Depends(check_key)]

    # ------------------------------------------------------------------------- service
    @app.get("/health", response_model=HealthResponse, tags=["service"])
    def health():
        return HealthResponse(name="motion-engine", version=__version__, uptime_s=time.time() - metrics.started)

    @app.get("/metrics", response_class=PlainTextResponse, tags=["service"], dependencies=secured,
             summary="Prometheus metrics")
    def prometheus_metrics():
        return metrics.render()

    # ------------------------------------------------------------------------- vehicle
    @app.get("/vehicle", response_model=VehicleCatalog, tags=["vehicle"], dependencies=secured)
    def vehicle_catalog():
        return VehicleCatalog(presets=catalog["presets"], vehicle_models=catalog["vehicle_model"],
                              tire_models=catalog["tire_model"], lateral_controllers=catalog["lateral_controller"],
                              longitudinal_controllers=catalog["longitudinal_controller"])

    @app.get("/vehicle/{preset}", response_model=VehicleResponse, tags=["vehicle"], dependencies=secured,
             summary="Parameters and linear single-track analysis of a vehicle preset")
    def vehicle(preset: str):
        from ..analysis import LinearSingleTrackAnalysis
        from ..core.parameters import load_vehicle_preset

        config = load_vehicle_preset(_require(preset, catalog["presets"], "vehicle preset"))
        summary = LinearSingleTrackAnalysis(config).summary()
        lin = LinearSingleTrackAnalysis(config)
        analysis = VehicleAnalysis(
            understeer_gradient=lin.understeer_gradient,
            understeer_gradient_deg_per_g=summary["understeer_gradient_deg_per_g"],
            characteristic_speed=_finite(lin.characteristic_speed), critical_speed=_finite(lin.critical_speed),
            cornering_stiffness_front=summary["cornering_stiffness_front"],
            cornering_stiffness_rear=summary["cornering_stiffness_rear"],
            per_speed=summary["per_speed"])
        schema = []
        for group in fields(config):
            obj = getattr(config, group.name)
            for f in fields(obj):
                meta = f.metadata or {}
                schema.append(ParameterInfo(key=f"{group.name}.{f.name}", value=getattr(obj, f.name),
                                            unit=meta.get("unit", ""), min=meta.get("min"), max=meta.get("max")))
        return VehicleResponse(name=preset, parameters=config.to_dict(), schema=schema, analysis=analysis)

    # ------------------------------------------------------------------------- trajectory
    @app.get("/trajectory/maneuvers", tags=["trajectory"], dependencies=secured,
             summary="Available maneuvers with their parameters")
    def maneuvers():
        from ..trajectory import MANEUVER_INFO
        return MANEUVER_INFO

    @app.post("/trajectory", response_model=TrajectoryResponse, tags=["trajectory"], dependencies=secured,
              summary="Generate the reference trajectory of a maneuver")
    def trajectory(req: TrajectoryRequest):
        from ..simulation.scenario import Scenario

        maneuver = _require(req.maneuver, catalog["maneuver"], "maneuver")
        preset = _require(req.vehicle, catalog["presets"], "vehicle preset")
        with limiter.slot():
            sc = Scenario(vehicle=preset, maneuver=maneuver, maneuver_params=dict(req.params))
            try:
                traj = sc.build_trajectory(sc.build_config())
            except TypeError as exc:
                raise HTTPException(status_code=422, detail=f"invalid maneuver parameters: {exc}") from None
        idx = _decimate_index(len(traj.s), req.max_points)
        return TrajectoryResponse(name=traj.name or req.maneuver, length=float(traj.length),
                                  open_loop=bool(traj.is_open_loop), n_points=len(idx),
                                  **{k: _list(getattr(traj, k)[idx]) for k in ("s", "x", "y", "psi", "kappa", "v")})

    # ------------------------------------------------------------------------- simulation
    @app.post("/simulate", response_model=SimulateResponse, tags=["simulation"], dependencies=secured,
              summary="Closed-loop vehicle dynamics simulation of a maneuver")
    def simulate(req: SimulateRequest):
        from ..reporting.kpi_evaluator import evaluate
        from ..simulation.scenario import Scenario, ScenarioManager
        from ..simulation.simulator import Simulator

        if req.scenario is not None:
            scenario = ScenarioManager().load(_require(req.scenario, catalog["scenarios"], "scenario"))
            if scenario.trajectory_file:
                raise HTTPException(status_code=422, detail="scenarios with trajectory files are not served")
        else:
            scenario = Scenario(name="api")
        for key in ("vehicle", "vehicle_overrides", "model", "maneuver", "maneuver_params", "lateral_controller",
                    "lateral_params", "longitudinal_controller", "longitudinal_params", "environment", "duration",
                    "dt_control", "solver", "initial_speed"):
            value = getattr(req, key)
            if value is not None:
                setattr(scenario, key, value)
        if not isinstance(scenario.vehicle, str):
            raise HTTPException(status_code=422, detail="vehicle must be a preset name")
        scenario.vehicle = _require(scenario.vehicle, catalog["presets"], "vehicle preset")
        if str(scenario.model).startswith("neural_"):
            try:
                scenario.model = models.activate(models.get(scenario.model[len("neural_"):])["id"])
            except KeyError:
                raise HTTPException(status_code=422, detail=f"unknown neural model '{scenario.model}'") from None
        else:
            scenario.model = _require(scenario.model, catalog["vehicle_model"], "vehicle model")
        _require(scenario.maneuver, catalog["maneuver"], "maneuver")
        _require(scenario.lateral_controller, catalog["lateral_controller"], "lateral controller")
        _require(scenario.longitudinal_controller, catalog["longitudinal_controller"], "longitudinal controller")
        for dotted in scenario.vehicle_overrides:
            if dotted.count(".") != 1:
                raise HTTPException(status_code=422, detail=f"override '{dotted}' must be 'group.field'")

        with limiter.slot():
            try:
                sim = Simulator.from_scenario(scenario)
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail=f"invalid scenario: {exc}") from None
            sim.duration = min(sim.duration, max_sim_time)
            result = sim.run(max_wall_time=max_wall_time)
            kpis = [_kpi_model(k) for k in evaluate(result)]
        n = len(result["t"])
        idx = _decimate_index(n, req.max_points)
        signals = {}
        for key in req.signals:
            if key in result:
                arr = np.asarray(result[key], dtype=float)[idx]
                signals[key] = [_list(row) if np.ndim(row) else _finite(row) for row in arr]
        return SimulateResponse(name=scenario.name, model=scenario.model, stop_reason=sim.stop_reason,
                                stop_code=STOP_CODES.get(sim.stop_reason, "other"),
                                simulated_time=float(sim.t), wall_time=float(result.metadata["wall_time"]),
                                n_samples=n, kpis=kpis, signals=signals)

    # ------------------------------------------------------------------------- prediction
    @app.post("/predict", response_model=PredictResponse, tags=["prediction"], dependencies=secured,
              summary="Motion prediction of an object list")
    def predict(req: PredictRequest):
        from ..framework import RunContext, create_component
        from ..framework.types import ObjectList, ObjectState

        spec = "predictor/constant_velocity" if req.predictor == "ctrv" else f"predictor/{req.predictor}"
        params: dict[str, float | bool] = {"horizon": req.horizon, "dt": req.dt, "use_lanes": False}
        if req.predictor == "ctrv":
            params["use_yaw_rate"] = True
        objs = [ObjectState(**o.model_dump()) for o in req.objects]
        with limiter.slot():
            comp = create_component(spec, params)
            comp.reset(RunContext())
            pred = comp.step(req.t0, {"objects": ObjectList(t=req.t0, objects=objs)})["prediction"]
        out = [PredictedObjectModel(id=o.id, type=o.type, length=o.length, width=o.width,
                                    **{k: _list(getattr(o, k)) for k in ("t", "x", "y", "psi", "v")})
               for o in pred.objects]
        return PredictResponse(t0=req.t0, predictor=req.predictor, objects=out)

    # ------------------------------------------------------------------------- planning
    def _plan_setup(req):
        from ..core.parameters import load_vehicle_preset
        from ..framework import RunContext
        from ..framework.types import BehaviorCommand, LongitudinalMode, Prediction
        from ..geometry import ReferenceLine
        from ..planning import create_planner
        from ..planning.simulation import constant_velocity_object

        config_name = _require(req.config, catalog["planner_configs"], "planner configuration")
        vehicle_cfg = load_vehicle_preset(_require(req.vehicle, catalog["presets"], "vehicle preset"))
        road = ReferenceLine.from_segments([("straight", s.length) if s.kind == "straight"
                                           else ("arc", s.length, s.curvature) for s in req.road], name="road")
        target = road.offset(req.target_offset, name="target") if req.target_offset else road
        modes = [LongitudinalMode("velocity", {"v_ref": req.target_speed})]
        if req.stop_at is not None:
            modes.append(LongitudinalMode("stopping", {"s_stop": float(req.stop_at)}))
        horizon = 10.0

        def prediction(t):
            objs = []
            for o in req.obstacles:
                # constant acceleration along psi from t = 0 on, re-anchored at the planning time t
                tau = t
                if o.a < 0 and o.v > 0:
                    tau = min(t, o.v / -o.a)
                dist = o.v * tau + 0.5 * o.a * tau * tau
                v = max(o.v + o.a * tau, 0.0)
                objs.append(constant_velocity_object(o.id, o.x + dist * math.cos(o.psi), o.y + dist * math.sin(o.psi),
                                                     o.psi, v, t0=t, horizon=horizon, length=o.length,
                                                     width=o.width, obj_type=o.type, a=o.a))
            return Prediction(t0=t, objects=objs)

        def behavior(t, ego):
            return BehaviorCommand(t=t, reference_line=target, target_speed=req.target_speed, d_min=req.d_min,
                                   d_max=req.d_max, modes=modes)

        planner = create_planner(config_name)
        planner.reset(RunContext(vehicle=vehicle_cfg))
        return planner, vehicle_cfg, road, target, behavior, prediction

    def _road_geometry(road, target, req):
        step = max(1, len(road.s) // 400)
        left, right = road.offset(req.d_max + req.target_offset), road.offset(req.d_min + req.target_offset)
        return RoadGeometry(x=_list(road.x[::step]), y=_list(road.y[::step]), left_x=_list(left.x[::step]),
                            left_y=_list(left.y[::step]), right_x=_list(right.x[::step]),
                            right_y=_list(right.y[::step]), target_x=_list(target.x[::step]),
                            target_y=_list(target.y[::step]))

    @app.post("/plan", response_model=PlanResponse, tags=["planning"], dependencies=secured,
              summary="Werling trajectory planning on a road given as segments")
    def plan(req: PlanRequest):
        from ..framework.types import EgoState
        from ..planning.simulation import ego_from_point

        with limiter.slot():
            planner, _, road, target, behavior, prediction = _plan_setup(req)
            ego = EgoState(x=req.ego.x, y=req.ego.y, psi=req.ego.psi, vx=req.ego.vx, ax=req.ego.ax)
            first, first_dbg = planner.plan_cycle(0.0, ego, behavior(0.0, ego), prediction(0.0))
            traj, dbg, cycles = first, first_dbg, []
            t = 0.0
            for k in range(req.cycles):
                if k > 0:
                    traj, dbg = planner.plan_cycle(t, ego, behavior(t, ego), prediction(t))
                cycles.append(PlanCycle(t=t, x=ego.x, y=ego.y, v=ego.vx, valid=bool(traj.valid),
                                        n_candidates=int(dbg.n_candidates), compute_time=float(dbg.compute_time)))
                if k + 1 < req.cycles and not traj.empty:
                    t = round(t + 0.1, 10)
                    ego = ego_from_point(traj.sample(t), planner.geometry, traj.reference_point, t)
        idx = _decimate_index(len(first.t), req.max_points)
        out = PlannedTrajectoryModel(valid=bool(first.valid), cost=_finite(first.cost),
                                     longitudinal_mode=str(first.longitudinal_mode),
                                     reference_point=str(first.reference_point),
                                     **{k: _list(getattr(first, k)[idx]) if len(first.t) else []
                                        for k in ("t", "x", "y", "theta", "kappa", "v", "a")})
        return PlanResponse(road=_road_geometry(road, target, req), trajectory=out,
                            n_candidates=int(first_dbg.n_candidates), fallback=bool(first_dbg.fallback),
                            compute_time=float(first_dbg.compute_time), cycles=cycles)

    @app.post("/plan/explain", response_model=ExplainResponse, tags=["planning"], dependencies=secured,
              summary="Step-by-step derivation of one planning cycle (formulas with the planner's numbers)")
    def plan_explain(req: PlanRequest):
        from ..framework.types import EgoState
        from .explain import explain_cycle

        with limiter.slot():
            planner, vehicle_cfg, road, target, behavior, prediction = _plan_setup(req)
            ego = EgoState(x=req.ego.x, y=req.ego.y, psi=req.ego.psi, vx=req.ego.vx, ax=req.ego.ax)
            beh = behavior(0.0, ego)
            traj, dbg = planner.plan_cycle(0.0, ego, beh, prediction(0.0))
            if traj.plan is None or traj.empty:
                raise HTTPException(status_code=422, detail="no trajectory found for this situation")
            data = explain_cycle(planner, None, dbg, traj, beh, vehicle_cfg)
        return ExplainResponse(road=_road_geometry(road, target, req), obstacles=list(req.obstacles),
                               compute_time=float(dbg.compute_time), **data)

    # ------------------------------------------------------------------------- neural models
    def _public(meta):
        return {k: v for k, v in meta.items() if k != "history"}

    @app.get("/models", tags=["learning"], dependencies=secured, summary="Trained and connected neural models")
    def list_models():
        return [_public(m) for m in models.list()]

    @app.get("/models/{model_id}", tags=["learning"], dependencies=secured, summary="Model metadata and metrics")
    def get_model(model_id: str):
        try:
            return models.get(model_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="unknown model") from None

    @app.delete("/models/{model_id}", tags=["learning"], dependencies=secured, status_code=204)
    def delete_model(model_id: str):
        try:
            models.delete(model_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="unknown model") from None

    def _job_view(job):
        # caller holds train_lock; copies the history so the response is not mutated by the training thread
        return TrainJob.model_validate({k: (list(v) if k == "history" else v) for k, v in job.items() if k != "cancel"})

    @app.post("/models/train", response_model=TrainJob, status_code=202, tags=["learning"], dependencies=secured,
              summary="Train a neural surrogate of the vehicle dynamics on data from a physics model")
    def train_model(req: TrainRequest):
        from ..learning import train_surrogate

        vehicle_name = _require(req.vehicle, catalog["presets"], "vehicle preset")
        if any(h < 2 or h > 512 for h in req.hidden):
            raise HTTPException(status_code=422, detail="hidden layer sizes must be within 2..512")
        with train_lock:
            if any(j["state"] in ("queued", "running") for j in train_jobs.values()):
                raise HTTPException(status_code=409, detail="a training job is already running")
            job_id = models.new_id()
            train_jobs[job_id] = {"id": job_id, "state": "queued", "phase": "", "progress": 0.0, "history": [],
                                  "model_id": None, "error": None, "cancel": False}

        def progress(phase, frac, info):
            with train_lock:
                job = train_jobs[job_id]
                job.update(phase=phase, progress=0.1 * frac if phase == "sampling" else 0.1 + 0.9 * frac)
                if "epoch" in info:
                    job["history"].append({"epoch": info["epoch"], "train": info["train"], "val": info["val"]})

        def run():
            with train_lock:
                train_jobs[job_id]["state"] = "running"
            try:
                net, meta = train_surrogate(vehicle_name, req.teacher, req.n_samples, tuple(req.hidden), req.epochs,
                                            req.learning_rate, seed=req.seed, progress=progress,
                                            should_stop=lambda: train_jobs[job_id]["cancel"])
                meta["name"] = req.name or f"{req.teacher} surrogate ({vehicle_name})"
                saved = models.save(meta, net.to_bytes())
                with train_lock:
                    cancelled = train_jobs[job_id]["cancel"]
                    train_jobs[job_id].update(state="cancelled" if cancelled else "done", progress=1.0,
                                              model_id=saved["id"])
            except Exception as exc:  # reported to the client
                with train_lock:
                    train_jobs[job_id].update(state="failed", error=str(exc))

        train_pool.submit(run)
        with train_lock:
            return _job_view(train_jobs[job_id])

    @app.get("/models/jobs/{job_id}", response_model=TrainJob, tags=["learning"], dependencies=secured)
    def train_job(job_id: str):
        with train_lock:
            job = train_jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="unknown job")
            return _job_view(job)

    @app.post("/models/jobs/{job_id}/cancel", response_model=TrainJob, tags=["learning"], dependencies=secured)
    def cancel_job(job_id: str):
        with train_lock:
            job = train_jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="unknown job")
            job["cancel"] = True
            return _job_view(job)

    @app.post("/models/connect", tags=["learning"], dependencies=secured, status_code=201,
              summary="Connect an external model (ONNX graph or HTTP endpoint) with the surrogate interface")
    def connect_model(req: ConnectRequest):
        import base64
        from urllib.parse import urlparse

        from ..learning import FEATURES, TARGETS, load_backend

        vehicle_name = _require(req.vehicle, catalog["presets"], "vehicle preset")
        meta = {"name": req.name, "kind": "vehicle_dynamics", "vehicle": vehicle_name, "features": list(FEATURES),
                "targets": list(TARGETS)}
        blob = None
        if req.backend == "onnx":
            if not req.onnx_base64:
                raise HTTPException(status_code=422, detail="onnx_base64 is required")
            try:
                blob = base64.b64decode(req.onnx_base64, validate=True)
            except ValueError:
                raise HTTPException(status_code=422, detail="onnx_base64 is not valid base64") from None
            if len(blob) > 20 * 2 ** 20:
                raise HTTPException(status_code=413, detail="ONNX graph larger than 20 MB")
            meta["backend"] = "onnx"
        else:
            parsed = urlparse(req.url or "")
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise HTTPException(status_code=422, detail="url must be an http(s) URL")
            # the server would call this URL: only hosts the operator allowed (no SSRF into the network)
            if parsed.hostname.lower() not in allowed_model_hosts:
                raise HTTPException(status_code=403, detail="host not in MOTIONENGINE_ALLOWED_MODEL_HOSTS")
            meta.update(backend="http", url=req.url)
        try:
            backend = load_backend(meta, blob)
            out = np.asarray(backend.predict([[20.0, 0.0, 0.0, 0.0, 0.0]]))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"model check failed: {exc}") from None
        if out.shape != (1, len(TARGETS)):
            raise HTTPException(status_code=422, detail=f"model must map 5 inputs to 3 outputs, got {out.shape}")
        return _public(models.save(meta, blob))

    @app.post("/models/{model_id}/evaluate", tags=["learning"], dependencies=secured,
              summary="Closed-loop comparison of the neural model with its physics teacher")
    def evaluate_model(model_id: str, req: EvaluateRequest):
        from ..learning import evaluate_closed_loop

        try:
            meta = models.get(model_id)
            name = models.activate(model_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="unknown model") from None
        maneuver = _require(req.maneuver, catalog["maneuver"], "maneuver")
        with limiter.slot():
            try:
                return evaluate_closed_loop(name, meta.get("teacher", "bicycle_nonlinear"),
                                            meta.get("vehicle", "mid_size_sedan"), maneuver,
                                            dict(req.maneuver_params), req.duration)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from None

    # ------------------------------------------------------------------------- chat assistant
    from .chat import ChatTools, ConversationStore, chat_events

    def _chat_catalog():
        from ..trajectory import MANEUVER_INFO

        neural = [{"id": f"neural_{m['id']}", "name": m.get("name"), "vehicle": m.get("vehicle")} for m in models.list()]
        return {"vehicles": catalog["presets"], "vehicle_models": catalog["vehicle_model"], "neural_models": neural,
                "maneuvers": {name: {"label": info.get("label"), "params": {p: unit for p, (_, unit) in
                                                                            info.get("params", {}).items()}}
                              for name, info in MANEUVER_INFO.items()},
                "lateral_controllers": catalog["lateral_controller"],
                "longitudinal_controllers": catalog["longitudinal_controller"], "scenarios": catalog["scenarios"],
                "planner_configs": catalog["planner_configs"], "tire_models": catalog["tire_model"],
                "limits": {"max_simulated_time_s": max_sim_time}}

    chat_tools = ChatTools(simulate=simulate, plan=plan, predict=predict, catalog=_chat_catalog)
    conversations = ConversationStore()
    chat_state = {"client": chat_client}

    def _chat_client():
        if chat_state["client"] is None:
            try:
                import anthropic
            except ImportError:
                raise HTTPException(status_code=503, detail="chat needs the 'anthropic' package "
                                                            "(pip install motion-engine[chat])") from None
            chat_state["client"] = anthropic.Anthropic()
        return chat_state["client"]

    @app.get("/chat/status", tags=["chat"], dependencies=secured, summary="Whether the chat assistant is available")
    def chat_status():
        import importlib.util

        from .chat import DEFAULT_MODEL

        installed = chat_state["client"] is not None or importlib.util.find_spec("anthropic") is not None
        credential = chat_state["client"] is not None or any(
            os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE",
                                        "ANTHROPIC_FEDERATION_RULE_ID")) or (Path.home() / ".config" / "anthropic").is_dir()
        return {"available": bool(installed and credential), "installed": installed, "credential": bool(credential),
                "model": os.environ.get("MOTIONENGINE_CHAT_MODEL", DEFAULT_MODEL)}

    @app.post("/chat", tags=["chat"], dependencies=secured, response_class=StreamingResponse,
              summary="Ask the assistant; it runs simulations and plans and streams its answer (server-sent events)")
    def chat(req: ChatRequest):
        client = _chat_client()
        conv = conversations.get_or_create(req.conversation_id)
        return StreamingResponse(chat_events(client, conv, req.message, chat_tools), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.delete("/chat/{conversation_id}", tags=["chat"], dependencies=secured, status_code=204)
    def chat_delete(conversation_id: str):
        conversations.delete(conversation_id)

    # ------------------------------------------------------------------------- web application
    web = Path(web_dir) if web_dir else Path(os.environ.get("MOTIONENGINE_WEB_DIR", "")) if \
        os.environ.get("MOTIONENGINE_WEB_DIR") else None
    if web is not None and (web / "index.html").exists():
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles

        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")
        index = web / "index.html"
        web_root_dir = web.resolve()
        # static files of the build (favicon, brand/, screenshots/), collected once: a request path is only
        # looked up in this table and never joined to a filesystem path, so ".." or absolute paths cannot escape
        web_files = {
            p.relative_to(web_root_dir).as_posix(): p
            for p in web_root_dir.rglob("*")
            if p.is_file() and web_root_dir in p.resolve().parents
        }

        @app.get("/", include_in_schema=False)
        def web_root():
            return FileResponse(index)

        @app.get("/{path:path}", include_in_schema=False)
        def web_spa(path: str):
            static = web_files.get(path)
            if static is not None:
                return FileResponse(static)
            # client routes get the app
            if path.split("/")[0] in ("app", "docs-ui", ""):
                return FileResponse(index)
            raise HTTPException(status_code=404, detail="not found")

    return app


app = create_app()


def main(argv=None):
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="MotionEngine REST service (FastAPI)")
    parser.add_argument("--host", default=os.environ.get("MOTIONENGINE_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MOTIONENGINE_PORT", "8000")))
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    uvicorn.run("vdsim.service.app:app", host=args.host, port=args.port, workers=args.workers)


if __name__ == "__main__":
    main()
