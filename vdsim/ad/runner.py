"""Scenario runner: scenario spec + stack -> graph -> executor -> ADResult.

    result = run_scenario("highway_cut_in", stack={"controller": "tracking_controller/stanley_pi"})

Steps
    1. build the ScenarioInstance (vdsim.world) and the vehicle configuration
    2. merge the stack (default <- scenario <- caller), build and validate the graph
    3. run the deterministic executor; a step listener records signals, actor histories,
       planner snapshots (timeline) and events; scenario impulse disturbances are applied
       to the plant (kick)
    4. stop on duration, collision, goal, numerical failure or wall-time limit
    5. evaluate the research metrics and attach profile + provenance
"""

from __future__ import annotations

import copy
import math
import time

import numpy as np

from ..core.logging_setup import get_logger
from ..core.parameters import load_vehicle_preset
from ..framework.context import RunContext
from ..framework.provenance import manifest
from ..framework.types import ControlCommand, ControllerStatus, PlannedTrajectory, PlannerDebug, WorldState
from .results import ADResult
from .stack import build_graph, merge_stack

log = get_logger("ad.runner")


def _spec_dict(scenario, scenario_params=None):
    # scenario name / ADScenario / dict -> spec dict with merged parameters
    from .. import world
    if isinstance(scenario, str):
        loader = getattr(world, "load_ad_scenario", None)
        spec = loader(scenario) if loader else scenario
    else:
        spec = scenario
    if hasattr(spec, "to_dict"):
        spec = spec.to_dict()
    if isinstance(spec, dict):
        spec = copy.deepcopy(spec)
        if scenario_params:
            spec.setdefault("params", {}).update(scenario_params)
    elif scenario_params:
        spec = {"type": spec, "name": spec, "params": dict(scenario_params)}
    return spec


def _road_geometry(road, ds=1.0):
    # RoadNetwork -> polylines for drawing (center + boundaries per lane)
    out = {"lanes": [], "stop_lines": [], "traffic_lights": [], "parking": []}
    if road is None:
        return out
    lanes = getattr(road, "lanes", {})
    for lane in (lanes.values() if isinstance(lanes, dict) else lanes):
        ref = getattr(lane, "center", None) or getattr(lane, "reference_line", None)
        if ref is None:
            continue
        s = np.arange(ref.s[0], ref.s[-1] + 1e-9, ds)
        x, y, th, _, _ = ref.evaluate(s)
        w = float(getattr(lane, "width", 3.5)) / 2
        nx, ny = -np.sin(th), np.cos(th)
        out["lanes"].append({"id": getattr(lane, "id", ""), "type": getattr(lane, "type", "driving"),
                             "center": [x.round(3).tolist(), y.round(3).tolist()],
                             "left": [(x + w * nx).round(3).tolist(), (y + w * ny).round(3).tolist()],
                             "right": [(x - w * nx).round(3).tolist(), (y - w * ny).round(3).tolist()],
                             "marking_left": str(getattr(lane, "marking_left", "dashed")),
                             "marking_right": str(getattr(lane, "marking_right", "dashed"))})
    for sl in getattr(road, "stop_lines", []) or []:
        try:
            lane = lanes[sl.lane_id] if isinstance(lanes, dict) else None
            ref = getattr(lane, "center", None) or getattr(lane, "reference_line", None)
            x, y, th, _, _ = ref.evaluate(sl.s)
            out["stop_lines"].append({"x": x, "y": y, "theta": th, "width": float(getattr(lane, "width", 3.5)),
                                      "kind": getattr(sl, "kind", "stop")})
        except Exception:
            continue
    for tl in (getattr(road, "traffic_lights", {}) or {}).values() if isinstance(getattr(road, "traffic_lights", {}), dict) \
            else getattr(road, "traffic_lights", []) or []:
        out["traffic_lights"].append({"id": getattr(tl, "id", ""), "x": float(getattr(tl, "x", 0.0)),
                                      "y": float(getattr(tl, "y", 0.0)), "states": []})
    for p in getattr(road, "parking", None) or getattr(road, "parking_spots", None) or []:
        out["parking"].append({k: float(getattr(p, k, 0.0)) for k in ("x", "y", "theta", "length", "width")})
    return out


def _f(v):
    return float(v) if v is not None and np.isfinite(v) else np.nan


class _Recorder:
    # step listener collecting everything the GUI timeline and the metrics need
    def __init__(self, result, ex, record_snapshots, vehicle):
        self.res, self.ex, self.record_snapshots = result, ex, record_snapshots
        self.vehicle = vehicle
        self.last_debug = None
        self.last_traj = None
        self.last_behavior_maneuver = None
        self.last_mode = None
        self.last_controller = None
        self.seen_events = set()
        self.controllers, self.modes, self.maneuvers = [], [], []
        self.collision = False
        self.collision_with = None
        self.goal = False
        self.plant_kicks = []
        self.objects_every = 5         # actor history at 20 Hz
        self.k = 0

    @staticmethod
    def _index(lst, name):
        if name not in lst:
            lst.append(name)
        return lst.index(name)

    def __call__(self, ex):
        t = ex.t
        v = ex.values
        ego = v.get("plant.ego")
        traj = v.get("planner.trajectory")
        cmd = v.get("controller.command")
        status = v.get("controller.status")
        debug = v.get("planner.debug")
        behavior = v.get("behavior.behavior")
        world = v.get("world.world")
        control = v.get("actuators.control")
        row = {"t": t}
        if ego is not None:
            row.update(ego_x=ego.x, ego_y=ego.y, ego_psi=ego.psi, ego_vx=ego.vx, ego_vy=ego.vy, ego_v=ego.speed,
                       ego_r=ego.r, ego_ax=ego.ax, ego_ay=ego.ay, delta=ego.delta, delta_rate=ego.delta_rate)
        if isinstance(traj, PlannedTrajectory) and not traj.empty:
            p = traj.sample(t)
            row.update(des_x=p.x, des_y=p.y, des_theta=p.theta, des_kappa=p.kappa, des_v=p.v, des_a=p.a,
                       plan_cost=_f(traj.cost), plan_valid=float(traj.valid), plan_reinit=float(traj.reinitialized),
                       plan_mode_id=self._index(self.modes, traj.longitudinal_mode))
            if traj.longitudinal_mode != self.last_mode:
                if self.last_mode is not None:
                    self.res.add_event(t, "mode_switch", mode=traj.longitudinal_mode, previous=self.last_mode)
                self.last_mode = traj.longitudinal_mode
        if isinstance(cmd, ControlCommand):
            row.update(cmd_steer_rate=_f(cmd.steer_rate), cmd_steer_angle=_f(cmd.steer_angle),
                       cmd_force=_f(cmd.force), cmd_accel=_f(cmd.accel))
        if isinstance(status, ControllerStatus):
            row.update(e_t=status.e_t, e_n=status.e_n, e_theta=status.e_theta, e_v=status.e_v,
                       e_t_dot=status.e_t_dot, e_n_dot=status.e_n_dot, lookahead=status.lookahead,
                       reinit_request=float(bool(status.reinit_request)),
                       controller_id=self._index(self.controllers, status.active_controller or "-"))
            if status.active_controller != self.last_controller:
                if self.last_controller is not None:
                    self.res.add_event(t, "controller_switch", controller=status.active_controller,
                                       previous=self.last_controller)
                self.last_controller = status.active_controller
        if control is not None:
            row.update(act_steer=control.steer_front, act_drive=float(np.sum(control.drive_torque)),
                       act_brake=float(np.sum(control.brake_torque)))
        if behavior is not None:
            row.update(target_speed=behavior.target_speed, maneuver_id=self._index(self.maneuvers, behavior.maneuver))
            if behavior.maneuver != self.last_behavior_maneuver:
                self.res.add_event(t, "maneuver", maneuver=behavior.maneuver,
                                   reason=str(behavior.info.get("reason", "")) if behavior.info else "")
                self.last_behavior_maneuver = behavior.maneuver
        if isinstance(debug, PlannerDebug) and debug is not self.last_debug:
            self.last_debug = debug
            row["plan_time"] = debug.compute_time
            if debug.reinitialized or (isinstance(traj, PlannedTrajectory) and traj.reinitialized and traj is not self.last_traj):
                self.res.add_event(t, "reinit", fallback=bool(debug.fallback))
            if debug.fallback:
                self.res.add_event(t, "fallback")
            if self.record_snapshots:
                self.res.add_snapshot(debug, traj, behavior)
                snap = self.res.snapshots[-1]
                snap["t"] = float(debug.t or t)
                pred = v.get("prediction.prediction")
                if pred is not None:
                    snap["prediction"] = [{"id": o.id, "t": np.asarray(o.t, np.float32)[::5],
                                           "x": np.asarray(o.x, np.float32)[::5], "y": np.asarray(o.y, np.float32)[::5],
                                           "psi": np.asarray(o.psi, np.float32)[::5], "length": o.length,
                                           "width": o.width} for o in pred.objects]
                if isinstance(status, ControllerStatus):
                    snap["controller"] = {"horizon_x": status.horizon_x, "horizon_y": status.horizon_y,
                                          "active": status.active_controller, "lookahead": status.lookahead}
        self.last_traj = traj
        if isinstance(world, WorldState):
            row.update(collision=float(world.collision), off_road=float(world.off_road))
            if world.collision and not self.collision:
                self.collision, self.collision_with = True, world.collision_with
                self.res.add_event(t, "collision", object=world.collision_with)
            if self.k % self.objects_every == 0:
                self.res.add_objects(t, world.objects)
            for ev in world.events or []:
                key = (ev.get("type"), round(float(ev.get("t", t)), 6), str(ev.get("id", ""))) if isinstance(ev, dict) \
                    else (str(ev), round(t, 6), "")
                if key in self.seen_events:
                    continue
                self.seen_events.add(key)
                info = ev if isinstance(ev, dict) else {"name": str(ev)}
                kind = info.get("type", "scenario_event")
                self.res.add_event(t, kind if kind in ("goal_reached",) else "scenario_event",
                                   **{k: val for k, val in info.items() if k != "t"})
                if kind == "goal_reached":
                    self.goal = True
                if kind in ("lateral_impulse", "impulse"):
                    self.plant_kicks.append(info)
        self.res.append(row)
        self.k += 1


def _apply_kicks(ex, rec):
    # impulse disturbances of the scenario (e.g. a strong side wind gust, Werling 5.3.2)
    plant = ex.graph.instance("plant") if "plant" in ex.graph.nodes else None
    while rec.plant_kicks:
        info = rec.plant_kicks.pop(0)
        kick = getattr(plant, "kick", None)
        if kick is None:
            continue
        deltas = {k: float(info[k]) for k in ("vy", "r", "psi", "vx", "x", "y") if k in info}
        if not deltas and "dvy" in info:
            deltas = {"vy": float(info["dvy"])}
        if deltas:
            kick(**deltas)


def run_scenario(scenario, stack=None, seed=None, duration=None, scenario_params=None, record_snapshots=True,
                 vehicle=None, graph=None, progress=None, stop_on_collision=True, stop_on_goal=True,
                 max_wall_time=None, name=None):
    from ..runtime import Executor, Graph
    from ..world import build_scenario

    spec = _spec_dict(scenario, scenario_params)
    seed = int(seed if seed is not None else (spec.get("seed", 0) if isinstance(spec, dict) else 0))
    inst = build_scenario(spec, seed=seed)
    vehicle_name = vehicle or (spec.get("vehicle") if isinstance(spec, dict) else None) \
        or getattr(inst, "metadata", {}).get("vehicle") or "mid_size_sedan"
    vehicle_cfg = load_vehicle_preset(vehicle_name) if isinstance(vehicle_name, str) else vehicle_name
    scen_stack = (spec.get("stack") if isinstance(spec, dict) else None) or getattr(inst, "metadata", {}).get("stack")
    full_stack = merge_stack(scen_stack, stack)
    graph_dict = graph or build_graph(full_stack, name=f"stack_{spec.get('name', 'scenario') if isinstance(spec, dict) else spec}")
    g = Graph.from_dict(graph_dict)
    report = g.validate()
    report.raise_for_errors()

    context = RunContext(dt=g.base_dt, seed=seed, vehicle=vehicle_cfg, road=inst.road, scenario=inst)
    ex = Executor(g, context, recorder=False)
    sc_name = name or (spec.get("name") if isinstance(spec, dict) else str(spec))
    res = ADResult(sc_name, spec if isinstance(spec, dict) else {"name": str(spec)}, full_stack, seed)
    p = vehicle_cfg.vehicle
    res.metadata["ego_dims"] = {"length": p.length, "width": p.width, "wheelbase": p.wheelbase,
                                "cg_to_rear": p.cg_to_rear,
                                "center_offset": (p.cg_to_front - p.cg_to_rear) / 2}
    res.metadata["vehicle"] = vehicle_name if isinstance(vehicle_name, str) else "custom"
    rec = _Recorder(res, ex, record_snapshots, vehicle_cfg)
    ex.add_listener(step=rec)
    t_end = float(duration or getattr(inst, "duration", None) or 30.0)

    wall0 = time.perf_counter()
    stop_reason = "Simulationsdauer erreicht"
    ex.reset()
    n_total = max(int(t_end / g.base_dt), 1)
    k = 0
    try:
        while ex.t < t_end - 1e-9:
            ex.step()
            _apply_kicks(ex, rec)
            k += 1
            ego = ex.values.get("plant.ego")
            if ego is not None and not all(math.isfinite(getattr(ego, f)) for f in ("x", "y", "vx", "psi")):
                stop_reason = "numerisch instabil (NaN)"
                break
            if stop_on_collision and rec.collision:
                stop_reason = "Kollision"
                break
            if stop_on_goal and rec.goal:
                stop_reason = "Ziel erreicht"
                break
            if max_wall_time and time.perf_counter() - wall0 > max_wall_time:
                stop_reason = "Rechenzeitlimit"
                break
            if progress and k % 50 == 0:
                progress(ex.t, t_end)
    except Exception as exc:
        log.exception("scenario '%s' failed at t=%.2f s", sc_name, ex.t)
        stop_reason = f"Fehler: {exc}"
        res.add_event(ex.t, "error", message=str(exc))
    finally:
        ex.close()
    wall = time.perf_counter() - wall0
    res.metadata.update(stop_reason=stop_reason, wall_time=wall, controllers=rec.controllers, modes=rec.modes,
                        maneuvers=rec.maneuvers, collision_with=rec.collision_with,
                        success=getattr(inst, "success", None) if isinstance(getattr(inst, "success", None), (dict, list)) else None)
    res.road = _road_geometry(inst.road)
    res.profile = {node: {"calls": s.get("calls", 0), "mean": s.get("mean_us", 0) * 1e-6,
                          "p95": s.get("p95_us", 0) * 1e-6, "max": s.get("max_us", 0) * 1e-6,
                          "total": s.get("total_ms", 0) * 1e-3}
                   for node, s in ex.profiler.report().items()}
    components = {nid: f"{n.component}" for nid, n in g.nodes.items()}
    res.provenance = manifest(config={"scenario": res.scenario, "stack": full_stack}, components=components, seed=seed)
    res.finalize()
    from ..research.metrics import evaluate
    evaluate(res)
    if progress:
        progress(t_end, t_end)
    log.info("'%s': %.1f s simuliert in %.1f s (%s)", sc_name, res.duration, wall, stop_reason)
    return res
