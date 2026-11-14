"""Controller lab: tracking controllers on reference paths, with the terms of each control law per time step.

    GET  /control/catalog     controllers (documentation, parameters), paths, plant models
    POST /control/run         closed loop of one or more controllers on the same path and plant

The chain is the one of the automated-driving stack (controller -> vehicle dynamics -> actuators -> plant,
vdsim.stabilization.simulate.run_closed_loop); the reference trajectory replaces the planner. So the page shows
what a controller does on its own: tracking errors, steering, and how each term of its law contributes.
"""

from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

CONTROLLERS = ["pure_pursuit", "stanley", "lqr", "mpc", "werling_bilevel"]
PLANTS = ["werling_desm", "bicycle_nonlinear", "double_track", "multibody"]
REALISTIC_ACTUATOR = {"steering": {"dead_time": 0.03, "tau": 0.05, "rate_limit": 0.6}, "drive_tau": 0.2, "brake_tau": 0.1}
PATHS = {
    "lane_change": {"offset": 3.5, "length": 50.0},
    "double_lane_change": {"offset": 3.5, "length": 40.0},
    "curve_entry": {"radius": 60.0, "transition": 20.0},
    "s_curve": {"radius": 80.0, "length": 60.0},
    "slalom": {"amplitude": 1.5, "wavelength": 60.0},
    "straight": {},
}
# scalar terms a controller reports per step (ControllerStatus.info), language neutral
INFO_SCALARS = ("lookahead", "alpha", "e_front", "heading", "feedback", "feedforward", "damping", "steer_rate_plan")
INFO_VECTORS = {"K": 4, "x": 4}


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ControllerSpec(_Strict):
    name: str = Field(max_length=60)
    params: dict[str, Any] = Field(default_factory=dict)
    label: str = Field("", max_length=60)


class Disturbance(_Strict):
    t: float = Field(3.0, ge=0.0, le=60.0)
    duration: float = Field(0.5, gt=0.0, le=10.0)
    fy: float = Field(0.0, ge=-20000.0, le=20000.0, description="lateral force at the center of gravity, N")
    mz: float = Field(0.0, ge=-20000.0, le=20000.0, description="yaw moment, Nm")


class ControlRunRequest(_Strict):
    controllers: list[ControllerSpec] = Field(min_length=1, max_length=6)
    path: Literal["lane_change", "double_lane_change", "curve_entry", "s_curve", "slalom", "straight"] = "lane_change"
    path_params: dict[str, float] = Field(default_factory=dict)
    speed: float = Field(15.0, ge=2.0, le=50.0, description="m/s")
    vehicle: str = "mid_size_sedan"
    plant: str = "werling_desm"
    mu: float = Field(1.0, ge=0.05, le=1.5)
    lateral_offset: float = Field(0.0, ge=-3.0, le=3.0, description="start beside the path, m")
    heading_offset_deg: float = Field(0.0, ge=-20.0, le=20.0)
    disturbance: Disturbance | None = None
    actuator: Literal["ideal", "realistic"] = Field("ideal", description="realistic: steering with 30 ms dead time, "
                                                    "50 ms lag and a rate limit of 0.6 rad/s at the wheels")
    duration: float | None = Field(None, gt=0.5, le=40.0)
    max_points: int = Field(600, ge=50, le=4000)


def build_path(kind, params, speed):
    from ..stabilization.trajectories import path_from_curvature, path_from_lateral_offset

    p = {**PATHS[kind], **{k: float(v) for k, v in params.items() if k in PATHS[kind]}}
    lead = max(2.0 * speed, 20.0)                 # straight run-in: the controller settles before the maneuver
    if kind == "straight":
        return path_from_lateral_offset([], lead + 12.0 * speed), lead
    if kind == "lane_change":
        return path_from_lateral_offset([(lead, p["length"], p["offset"])], lead + p["length"] + 6.0 * speed), lead
    if kind == "double_lane_change":
        gap = max(1.5 * speed, 20.0)
        segs = [(lead, p["length"], p["offset"]), (lead + p["length"] + gap, p["length"], -p["offset"])]
        return path_from_lateral_offset(segs, lead + 2 * p["length"] + gap + 5.0 * speed), lead
    if kind == "curve_entry":
        kappa, ramp = 1.0 / max(p["radius"], 8.0), max(p["transition"], 1.0)

        def k_fn(s):
            u = min(max((s - lead) / ramp, 0.0), 1.0)
            return kappa * u * u * (3.0 - 2.0 * u)
        return path_from_curvature(k_fn, lead + ramp + min(8.0 * speed, 1.5 * math.pi * p["radius"]), ds=0.05), lead
    if kind == "s_curve":
        kappa, length = 1.0 / max(p["radius"], 8.0), max(p["length"], 10.0)

        def k_fn(s):
            u = (s - lead) / length
            return kappa * math.sin(math.pi * u) if 0.0 <= u <= 2.0 else 0.0
        return path_from_curvature(k_fn, lead + 2 * length + 4.0 * speed, ds=0.05), lead
    amp, lam = p["amplitude"], max(p["wavelength"], 15.0)
    n = 3
    segs = [(lead + i * lam / 2, lam / 2, (amp if i == 0 else 2 * amp) * (-1) ** i) for i in range(2 * n)]
    segs.append((lead + n * lam, lam / 2, amp))
    return path_from_lateral_offset(segs, lead + (n + 0.5) * lam + 4.0 * speed), lead


def _kpis(log, dt):
    e, t = np.abs(log["e_n"]), log["t"]
    steer = log["delta"]
    rate = np.abs(np.diff(steer)) / dt if len(steer) > 1 else np.zeros(1)
    outside = np.flatnonzero(e > 0.05)
    return {"max_e_n": float(e.max()), "rms_e_n": float(np.sqrt(np.mean(e**2))), "final_e_n": float(e[-1]),
            "max_e_theta_deg": float(np.degrees(np.max(np.abs(log["e_theta"])))),
            "max_steer_deg": float(np.degrees(np.max(np.abs(steer)))),
            "max_steer_rate_deg_s": float(np.degrees(rate.max())),
            "max_ay": float(np.max(np.abs(log["ay"]))),
            "settled_after": float(t[outside[-1]] + dt) if len(outside) and outside[-1] < len(t) - 1 else
            (0.0 if not len(outside) else None),
            "compute_time_ms": float(1e3 * np.mean(log["compute_time"]))}


def create_router(secured, limiter, presets, max_wall_time):
    from ..framework.plugins import get_component

    router = APIRouter(dependencies=secured)

    def describe(name):
        d = get_component(f"tracking_controller/{name}").describe()
        doc = d.get("doc") or {}
        return {"name": name, "label": d.get("label") or name, "params": d.get("params") or [],
                "doc": {k: doc.get(k) for k in ("summary", "purpose", "theory", "assumptions", "limitations", "expert",
                                                "references")}}

    @router.get("/control/catalog", tags=["control"], summary="Controllers, reference paths and plant models")
    def catalog():
        from .workbench import _clean

        return _clean({"controllers": [describe(n) for n in CONTROLLERS], "paths": PATHS, "plants": PLANTS,
                       "info_terms": list(INFO_SCALARS)})

    @router.post("/control/run", tags=["control"],
                 summary="Closed loop of one or more tracking controllers on the same reference path")
    def run(req: ControlRunRequest):
        from ..core.parameters import load_vehicle_preset
        from ..simulation.environment import Environment
        from ..stabilization.simulate import run_closed_loop
        from ..stabilization.trajectories import SpeedProfile, build_trajectory
        from .workbench import _clean, _decimate

        if req.vehicle not in presets:
            raise HTTPException(status_code=422, detail=f"unknown vehicle preset '{req.vehicle}'")
        if req.plant not in PLANTS:
            raise HTTPException(status_code=422, detail=f"unknown plant '{req.plant}', available: {PLANTS}")
        for c in req.controllers:
            if c.name not in CONTROLLERS:
                raise HTTPException(status_code=422, detail=f"unknown controller '{c.name}', available: {CONTROLLERS}")
        cfg = load_vehicle_preset(req.vehicle)
        path, lead = build_path(req.path, req.path_params, req.speed)
        duration = min(req.duration or 40.0, (path.length - 5.0) / req.speed)
        dt = 0.01
        traj = build_trajectory(path, SpeedProfile([(0.0, req.speed), (duration + 1.0, req.speed)]), duration=duration + 1.0,
                                dt=dt, reference_point="cog")
        p0 = traj.sample(0.0)
        start = dict(x=p0.x - req.lateral_offset * math.sin(p0.theta), y=p0.y + req.lateral_offset * math.cos(p0.theta),
                     psi=p0.theta + math.radians(req.heading_offset_deg), v=req.speed)
        plant_params = {}
        if req.disturbance and (req.disturbance.fy or req.disturbance.mz):
            d = req.disturbance
            plant_params["disturbances"] = [{"t": d.t, "duration": d.duration, "fx": 0.0, "fy": d.fy, "mz": d.mz}]
        env = Environment.from_dict({"friction": {"base": req.mu}})
        runs = []
        with limiter.slot():
            for spec in req.controllers:
                try:
                    log, _ = run_closed_loop(spec.name, traj, cfg, duration=duration, dt=dt, plant=req.plant,
                                             plant_params=plant_params, controller_params=dict(spec.params),
                                             actuator_params=REALISTIC_ACTUATOR if req.actuator == "realistic" else None,
                                             environment=env, ego_initial=start)
                except (TypeError, ValueError, KeyError, AttributeError) as exc:
                    raise HTTPException(status_code=422, detail=f"{spec.name}: invalid parameters "
                                                                f"({type(exc).__name__})") from None
                finite = np.all(np.isfinite(log["x"]))
                idx = _decimate(len(log["t"]), req.max_points)
                series = {k: log[k][idx] for k in ("t", "x", "y", "vx", "ay", "r", "e_n", "e_t", "e_v", "compute_time")}
                series["e_theta_deg"] = np.degrees(log["e_theta"][idx])
                series["delta_deg"] = np.degrees(log["delta"][idx])
                series["delta_cmd_deg"] = np.degrees(log["steer_angle_cmd"][idx])
                terms = {}
                infos = [log["status"][i].info for i in idx]
                for key in INFO_SCALARS:
                    if any(key in info for info in infos):
                        terms[key] = [float(info[key]) if key in info else None for info in infos]
                for key, n in INFO_VECTORS.items():
                    if any(key in info for info in infos):
                        for j in range(n):
                            terms[f"{key}{j + 1}"] = [float(info[key][j]) if key in info else None for info in infos]
                kpis = _kpis(log, dt) if finite else None
                # on_path: the vehicle stays within 3 m of the reference (beyond that it has left any lane)
                runs.append({"name": spec.name, "label": spec.label or spec.name, "params": spec.params, "stable": bool(finite),
                             "on_path": bool(finite and kpis["max_e_n"] < 3.0),
                             "kpis": kpis, "signals": series, "terms": terms,
                             "active": [log["active"][i] for i in idx][-1]})
        step = max(1, len(path.s) // 500)
        s_end = req.speed * duration
        keep = path.s <= s_end + 5.0
        return _clean({"path": {"kind": req.path, "x": path.x[keep][::step], "y": path.y[keep][::step],
                                "kappa": path.kappa[keep][::step], "s": path.s[keep][::step], "maneuver_start": lead},
                       "speed": req.speed, "duration": duration, "plant": req.plant, "mu": req.mu, "actuator": req.actuator,
                       "vehicle": {"wheelbase": float(cfg.vehicle.wheelbase), "length": float(cfg.vehicle.length),
                                   "width": float(cfg.vehicle.width)},
                       "runs": runs})

    return router
