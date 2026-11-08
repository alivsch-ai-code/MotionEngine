"""FastAPI application of the MotionEngine REST service.

Configuration (environment variables):

    MOTIONENGINE_API_KEY          if set, every endpoint except /health requires the header X-API-Key
    MOTIONENGINE_MAX_CONCURRENCY  simultaneous compute requests (default: number of CPUs); further
                                  requests get 503 instead of queueing without bound
    MOTIONENGINE_MAX_SIM_TIME     upper bound of the simulated time per request, s (default 120)
    MOTIONENGINE_MAX_WALL_TIME    wall-clock budget per simulation, s (default 60)
    MOTIONENGINE_CORS_ORIGINS     comma separated list of allowed CORS origins (default: none)

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
from contextlib import contextmanager

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import APIKeyHeader

from .. import __version__
from .metrics import Metrics
from .schemas import (
    HealthResponse,
    KPIModel,
    PlanCycle,
    PlannedTrajectoryModel,
    PlanRequest,
    PlanResponse,
    PredictedObjectModel,
    PredictRequest,
    PredictResponse,
    SimulateRequest,
    SimulateResponse,
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
def create_app(api_key=None, max_concurrency=None, max_sim_time=None, max_wall_time=None, cors_origins=None):
    api_key = api_key if api_key is not None else os.environ.get("MOTIONENGINE_API_KEY") or None
    max_concurrency = max_concurrency or int(_env_float("MOTIONENGINE_MAX_CONCURRENCY", os.cpu_count() or 2))
    max_sim_time = max_sim_time or _env_float("MOTIONENGINE_MAX_SIM_TIME", 120.0)
    max_wall_time = max_wall_time or _env_float("MOTIONENGINE_MAX_WALL_TIME", 60.0)
    if cors_origins is None:
        cors_origins = [o.strip() for o in os.environ.get("MOTIONENGINE_CORS_ORIGINS", "").split(",") if o.strip()]

    metrics = Metrics()
    limiter = _Limiter(max_concurrency, metrics)
    catalog = _catalog()

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
        return VehicleResponse(name=preset, parameters=config.to_dict(), analysis=analysis)

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
        _require(scenario.model, catalog["vehicle_model"], "vehicle model")
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
            kpis = [KPIModel(**{**k.to_dict(), "value": k.value if isinstance(k.value, str) or k.value is None
                                else _finite(k.value)}) for k in evaluate(result)]
        n = len(result["t"])
        idx = _decimate_index(n, req.max_points)
        signals = {}
        for key in req.signals:
            if key in result:
                arr = np.asarray(result[key], dtype=float)[idx]
                signals[key] = [_list(row) if np.ndim(row) else _finite(row) for row in arr]
        return SimulateResponse(name=scenario.name, model=scenario.model, stop_reason=sim.stop_reason,
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
    @app.post("/plan", response_model=PlanResponse, tags=["planning"], dependencies=secured,
              summary="Werling trajectory planning on a road given as segments")
    def plan(req: PlanRequest):
        from ..framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
        from ..geometry import ReferenceLine
        from ..planning import create_planner
        from ..planning.simulation import constant_velocity_object, ego_from_point

        config_name = _require(req.config, catalog["planner_configs"], "planner configuration")
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

        with limiter.slot():
            planner = create_planner(config_name)
            planner.reset(None)
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
        return PlanResponse(trajectory=out, n_candidates=int(first_dbg.n_candidates),
                            fallback=bool(first_dbg.fallback), compute_time=float(first_dbg.compute_time),
                            cycles=cycles)

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
