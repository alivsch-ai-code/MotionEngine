"""Learned trajectory planner: a network proposes the trajectory, the planner verifies it.

Teacher is the Werling sampling planner (vdsim.planning). In every planning cycle it selects one
candidate: a lateral polynomial to the end offset delta in the time tau_lat and a longitudinal polynomial
to the end speed offset nu in the time tau_lon. The network learns this choice (imitation learning):

    situation (start state on the lane, target speed, corridor, curvature ahead, nearest objects)
        ->  (delta, tau_lat, nu, tau_lon)

`LearnedPlanner` uses the proposal as the center of a small local search: it builds only the candidates
next to the proposal (a few end offsets, end times and end speeds on the teacher's grid), and checks them
with the teacher's restrictions and collision check. So a trajectory from the network path is as safe as
one from the teacher. If no candidate of the local set is valid, the cycle falls back to the complete
search of the teacher. The share of cycles solved by the network path and the cost difference to the
teacher are the quality measures (`evaluate_planner`, `compare_closed_loop`).

Scope: fast driving (lateral motion over time) in the velocity mode, with static and moving objects, lane
offsets and curves. Slow driving (d(s) mode) and the modes following, merging and stopping use the teacher.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, replace

import numpy as np

from ..core.parameters import load_vehicle_preset, param
from ..framework import RunContext
from ..framework.knowledge import ComponentDoc
from ..framework.plugins import component
from ..framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
from ..geometry import ReferenceLine
from ..planning.planner import WerlingPlanner, WerlingPlannerParams, same_line
from ..planning.simulation import constant_velocity_object, ego_from_point
from .mlp import MLP

N_OBJECTS = 3
LOOKAHEAD = (0.0, 15.0, 30.0, 60.0)          # m ahead of the start point: curvature of the lane
FAR = 150.0                                  # m: "no object"
PLAN_FEATURES = (["d", "d_dot", "d_ddot", "s_dot", "s_ddot", "target_speed", "d_min", "d_max"]
                 + [f"kappa_{int(a)}" for a in LOOKAHEAD]
                 + [f"obj{i}_{k}" for i in range(N_OBJECTS) for k in ("present", "ds", "d", "dv")]
                 + ["prev_present", "prev_delta", "prev_lat_tau", "prev_nu", "prev_lon_tau", "phase_lat", "phase_lon"])
PLAN_TARGETS = ["lat_delta", "lat_tau", "lon_nu", "lon_tau"]
WINDOW = {"delta": 7, "lat_tau": 5, "nu": 7, "lon_tau": 5}     # grid values searched around the proposal


# ----------------------------------------------------------------------------- features
def previous_choice(ctx, old):
    """(delta, remaining lateral time, nu, remaining longitudinal time) of the plan of the last cycle, or None.

    The optimal trajectory of a cycle is usually the rest of the previous one (Bellman's principle, Werling
    3.4.2), so the previous choice is the most informative input of all cycles but the first.
    """
    if old is None or old.lateral_mode != "time" or old.lon_kind != "velocity" or not same_line(old.reference_line, ctx.reference_line):
        return None
    return (float(old.lat_delta), max(old.t0 + old.lat_tau - ctx.t_start, 0.0), float(old.lon_offset),
            max(old.t0 + old.lon_tau - ctx.t_start, 0.0))


def plan_features(ctx, old=None, sampling=None):
    """Feature vector of a planning cycle (None if the situation is outside the model's scope)."""
    if ctx.lateral_mode != "time" or ctx.direction < 0:
        return None
    f, ref = ctx.start.frenet, ctx.reference_line
    kappa = [ref.evaluate(f.s + a)[3] for a in LOOKAHEAD]
    objects = []
    for o in ctx.prediction.objects:
        x, y, psi, v = o.state_at(ctx.t_start)
        s, d = ref.project(x, y)[:2]
        ds = float(s - f.s)
        if -15.0 < ds < FAR - 30.0:
            theta = ref.evaluate(s)[2]
            objects.append((abs(ds), ds, float(d - ctx.d_ref), float(v * math.cos(psi - theta) - f.s_d)))
    objects.sort()
    obj = []
    for i in range(N_OBJECTS):
        obj += [1.0, *objects[i][1:]] if i < len(objects) else [0.0, FAR, 0.0, 0.0]
    clip = lambda v, lim: float(np.clip(v, -lim, lim))  # noqa: E731
    prev = previous_choice(ctx, old)
    lat_step, lon_step = (sampling.lat_tau_step, sampling.lon_tau_step) if sampling is not None else (0.5, 1.0)
    # position of the start time on the absolute end-time grids (the end times are k * step - t_start)
    phase = [(ctx.t_start % lat_step) / lat_step, (ctx.t_start % lon_step) / lon_step]
    return np.array([f.d - ctx.d_ref, f.d_d, f.d_dd, f.s_d, f.s_dd, ctx.target_speed,
                     clip(ctx.d_min - ctx.d_ref, 20.0), clip(ctx.d_max - ctx.d_ref, 20.0), *kappa, *obj,
                     *((1.0, *prev) if prev else (0.0, 0.0, 0.0, 0.0, 0.0)), *phase])


def plan_label(plan):
    """Teacher label of a cycle (None if the selected trajectory is outside the model's scope)."""
    if plan is None or not plan.valid or plan.lateral_mode != "time" or plan.lon_kind != "velocity":
        return None
    return np.array([plan.lat_delta, plan.lat_tau, plan.lon_offset, plan.lon_tau])


# ----------------------------------------------------------------------------- planner
@dataclass
class LearnedPlannerParams(WerlingPlannerParams):
    model: str = param("", "", "ID des gelernten Modells aus dem Modellspeicher (leer: nur Werling-Suche)")


@component
class LearnedPlanner(WerlingPlanner):
    """Werling planner whose search is guided by a learned proposal (see the module text)."""

    NAME, VERSION = "learned", "1.0.0"
    LABEL = "Trajektorienplaner (gelernt, mit Werling-Prüfung)"
    PARAMS = LearnedPlannerParams
    DOC = ComponentDoc(
        summary="Ein Netz schlägt die Trajektorie vor (Endversatz, Endgeschwindigkeit, Endzeiten); der Werling-Planer "
                "baut nur die Kandidaten neben dem Vorschlag und prüft sie mit seinen Restriktionen und der "
                "Kollisionsprüfung.",
        purpose="Gelernte Planung mit der Sicherheit des Werling-Planers: Ist kein lokaler Kandidat gültig oder liegt "
                "der beste am Rand der lokalen Menge, sucht der Zyklus vollständig.",
        theory="Imitationslernen der Auswahl des Werling-Planers; Merkmale: Startzustand, Aufgabe, Krümmung voraus, "
               "nächste Objekte, vorherige Wahl (Bellman-Prinzip).",
        assumptions=["Schnelle Fahrt mit d(t), Geschwindigkeitsmodus"],
        limitations=["Folgen, Einfädeln, Anhalten, langsame Fahrt und Rückwärtsfahrt plant der Werling-Planer",
                     "Kostenabstand zum Lehrer ist gemessen, nicht begrenzt"],
        references=["werling2011", "ross2011"],
        validation=["tests/planning/test_learned_planner.py", "tests/service/test_service_planner_model.py"],
        concepts=["imitation_learning"],
        expert="docs/learning/trajectory_model.md")

    def __init__(self, params=None, **overrides):
        super().__init__(params, **overrides)
        self.backend = None             # object with predict(x) -> (n, 4); None: teacher only
        self.window = dict(WINDOW)
        self.last_features = None
        self.proposal = None
        self.source = "teacher"
        self.stats = {"network": 0, "teacher": 0, "out_of_scope": 0, "infeasible": 0}
        self._guided = False
        self._previous = None
        self._local = {}
        self.edge_check = "offset"      # "": off, "offset": end offset and end speed, "all": also the end times
        self.relabel = False            # also compute the teacher's choice in every cycle (data collection)
        self.teacher_label = None

    def reset(self, context=None):
        super().reset(context)
        if self.params.model:
            from .store import ModelStore

            store = ModelStore()
            meta = store.get(self.params.model)
            if meta.get("kind") != "trajectory_planner":
                raise ValueError(f"model {self.params.model} is not a trajectory planner model")
            self.backend = planner_backend(meta, store.backend(self.params.model))
            self.window.update(meta.get("window") or {})
        self.stats = {"network": 0, "teacher": 0, "out_of_scope": 0, "infeasible": 0}
        self.last_features, self.proposal, self._previous = None, None, None

    def _lateral_focus(self, ctx):
        self.last_features = plan_features(ctx, self.plan, self.params.sampling)
        self.proposal = None
        self._previous = previous_choice(ctx, self.plan)
        if not self._guided or self.last_features is None:
            return None
        velocity_only = all(m.kind == "velocity" for m in ctx.behavior.modes)
        if not velocity_only:
            return None
        delta, lat_tau, nu, lon_tau = np.asarray(self.backend.predict(self.last_features[None, :]), dtype=float)[0]
        if not all(math.isfinite(v) for v in (delta, lat_tau, nu, lon_tau)):
            return None
        self.proposal = (float(delta), float(lat_tau), float(nu), float(lon_tau))
        # the lane center and the previous choice are always part of the local set
        include = (0.0, self._previous[0]) if self._previous else (0.0,)
        return self.proposal[0], self.proposal[1], self.window["delta"], self.window["lat_tau"], include

    def _longitudinal_focus(self, ctx, target):
        if self.proposal is None or target.kind != "velocity":
            return None
        include = (0.0, self._previous[2]) if self._previous else (0.0,)
        return self.proposal[2], self.proposal[3], self.window["nu"], self.window["lon_tau"], include

    def _run_mode(self, label, target, start, t_s, keep_lon, lon_limits, lat, ctx, sel):
        if self.proposal is not None:
            # small candidate set: check in small batches (the teacher starts with a larger one)
            sel = replace(sel, batch_min=min(sel.batch_min, max(sel.rerank_window, 4)))
        res = super()._run_mode(label, target, start, t_s, keep_lon, lon_limits, lat, ctx, sel)
        self._local[label] = (lat.open_edges, res.lon.info.get("open_edges", {}))
        return res

    def _at_open_edge(self):
        # the selected candidate lies on the border of the local set although the grid continues there
        plan = self.plan
        lat, lon = self._local.get(plan.lon_label, ({}, {}))
        near = lambda v, vals: any(abs(v - e) < 1e-6 for e in vals)  # noqa: E731
        checks = [(plan.lat_delta, lat.get("offset", ())), (plan.lon_offset, lon.get("offset", ()))]
        if self.edge_check == "all":
            checks += [(plan.lat_tau, lat.get("tau", ())), (plan.lon_tau, lon.get("tau", ()))]
        return any(near(v, vals) for v, vals in checks)

    def restart(self):
        """Forget the previous plan (new situation, same vehicle and parameters)."""
        self.plan, self.regime, self.last_trajectory, self.last_debug, self.cycle = None, None, None, None, 0
        self.stats = {"network": 0, "teacher": 0, "out_of_scope": 0, "infeasible": 0}
        self.last_features, self.proposal, self._previous = None, None, None

    def plan_cycle(self, t, ego, behavior, prediction=None, status=None):
        tic = time.perf_counter()
        saved = (self.plan, self.regime, self.last_trajectory, self.last_debug, self.cycle, dict(self.signals))
        self._guided = self.backend is not None
        self._local = {}
        traj, debug = super().plan_cycle(t, ego, behavior, prediction, status)
        if self.proposal is not None and not debug.fallback and traj.valid and not (self.edge_check and self._at_open_edge()):
            self.source = "network"
        else:
            if self.proposal is not None:
                # no valid candidate next to the proposal: complete search of the teacher, from the same state
                self.plan, self.regime, self.last_trajectory, self.last_debug, self.cycle, signals = saved
                self.signals.clear()
                self.signals.update(signals)
                self._guided = False
                traj, debug = super().plan_cycle(t, ego, behavior, prediction, status)
                # infeasible: the complete search finds no valid trajectory either (emergency trajectory)
                self.source = "teacher" if traj.valid and not debug.fallback else "infeasible"
            else:
                self.source = "out_of_scope" if self.backend is not None else "teacher"
        self._guided = False
        self.teacher_label = None
        if self.relabel:
            # what would the teacher select in this state? (DAgger: labels for the states the learner visits)
            if self.source == "network":
                result = (self.plan, self.regime, self.last_trajectory, self.last_debug, self.cycle, dict(self.signals))
                self.plan, self.regime, self.last_trajectory, self.last_debug, self.cycle, _ = saved
                super().plan_cycle(t, ego, behavior, prediction, status)
                self.teacher_label = plan_label(self.plan)
                self.plan, self.regime, self.last_trajectory, self.last_debug, self.cycle, signals = result
                self.signals.clear()
                self.signals.update(signals)
            else:
                self.teacher_label = plan_label(self.plan)
        self.stats[self.source] += 1
        debug.compute_time = time.perf_counter() - tic
        debug.info["source"] = self.source
        self.signals["network"] = float(self.source == "network")
        traj.metadata["source"] = self.source
        return traj, debug


def planner_for(backend=None, vehicle="mid_size_sedan", config="default", window=None):
    """LearnedPlanner with the parameters of a planner configuration (backend None: plain teacher)."""
    from ..planning.config import load_planner_config

    cfg = load_planner_config(config)
    planner = LearnedPlanner(cfg["params"])
    planner.backend = backend
    if window:
        planner.window.update(window)
    vehicle_cfg = load_vehicle_preset(vehicle) if isinstance(vehicle, str) else vehicle
    planner.reset(RunContext(vehicle=vehicle_cfg))
    return planner


# ----------------------------------------------------------------------------- situations
SITUATION_DEFAULTS = {"curve_share": 0.55, "max_objects": 3, "speed_min": 6.0, "speed_max": 33.0, "lane_change_share": 0.25}


def sample_situation(rng, settings=None):
    """Random planning situation in the form of the service's plan request (plain numbers).

    settings (all optional): curve_share (0..1), max_objects (0..3), speed_min / speed_max (m/s),
    lane_change_share (0..1, start on the neighbor lane).
    """
    cfg = {**SITUATION_DEFAULTS, **(settings or {})}
    curve = float(np.clip(cfg["curve_share"], 0.0, 1.0))
    kind = rng.choice(["straight", "curve", "s_curve"], p=[1.0 - curve, curve * 7 / 11, curve * 4 / 11])
    kappa = float(rng.uniform(1 / 400, 1 / 90) * rng.choice([-1, 1]))
    if kind == "straight":
        road = [{"kind": "straight", "length": 600.0}]
    elif kind == "curve":
        road = [{"kind": "straight", "length": float(rng.uniform(20, 80))}, {"kind": "arc", "length": 300.0, "curvature": kappa},
                {"kind": "straight", "length": 300.0}]
    else:
        road = [{"kind": "straight", "length": float(rng.uniform(20, 60))}, {"kind": "arc", "length": 120.0, "curvature": kappa},
                {"kind": "arc", "length": 120.0, "curvature": -kappa}, {"kind": "straight", "length": 300.0}]
    lanes_left, lanes_right = int(rng.integers(0, 2)), int(rng.integers(0, 2))
    d_min, d_max = -1.75 - 3.5 * lanes_right, 1.75 + 3.5 * lanes_left
    v_lo, v_hi = sorted((float(cfg["speed_min"]), float(cfg["speed_max"])))
    v = float(rng.uniform(max(v_lo, 4.0), max(v_hi, v_lo + 1.0)))
    target_speed = float(np.clip(v + rng.normal(0.0, 4.0), 5.0, 36.0))
    # start on the target lane, beside it (lane change) or anywhere in the corridor
    change = float(np.clip(cfg["lane_change_share"], 0.0, 0.75))
    mode = rng.choice(["on_lane", "lane_change", "anywhere"], p=[0.75 - change, change, 0.25])
    if mode == "on_lane":
        d0 = float(rng.normal(0.0, 0.25))
    elif mode == "lane_change" and (lanes_left or lanes_right):
        d0 = 3.5 * float(rng.choice([s for s, n in ((1, lanes_left), (-1, lanes_right)) if n])) + float(rng.normal(0.0, 0.2))
    else:
        d0 = float(rng.uniform(d_min + 1.0, d_max - 1.0))
    ego = {"s": float(rng.uniform(5.0, 40.0)), "d": d0, "dpsi": float(rng.normal(0.0, 0.02)), "vx": v, "ax": float(rng.normal(0.0, 0.5))}
    obstacles = []
    n_max = int(np.clip(cfg["max_objects"], 0, 3))
    weights = np.array([0.25, 0.35, 0.25, 0.15])[:n_max + 1]
    for i in range(int(rng.choice(np.arange(n_max + 1), p=weights / weights.sum()))):
        lane = float(rng.choice(np.arange(-lanes_right, lanes_left + 1))) * 3.5
        v_obj = float(rng.choice([0.0, rng.uniform(0.0, max(v, 8.0))], p=[0.3, 0.7]))
        # not closer than a braking distance at 4 m/s^2 (closer objects leave the planner no valid trajectory)
        gap = 12.0 + max(v - v_obj, 0.0) ** 2 / 8.0
        obstacles.append({"id": i + 1, "s": ego["s"] + float(rng.uniform(gap, gap + 100.0)), "d": lane + float(rng.normal(0.0, 0.3)),
                          "v": v_obj})
    return {"road": road, "ego": ego, "target_speed": target_speed, "d_min": d_min, "d_max": d_max, "obstacles": obstacles}


class Situation:
    """A situation as planner inputs: reference line, behavior command, prediction and start state."""

    def __init__(self, data, horizon=10.0):
        self.data = data
        self.ref = ReferenceLine.from_segments(
            [("straight", s["length"]) if s["kind"] == "straight" else ("arc", s["length"], s["curvature"]) for s in data["road"]],
            name="road")
        if data.get("target_offset"):
            self.ref = self.ref.offset(float(data["target_offset"]), name="target")
        e = data["ego"]
        if "x" in e:
            self.ego = EgoState(x=e["x"], y=e["y"], psi=e.get("psi", 0.0), vx=e["vx"], ax=e.get("ax", 0.0))
        else:
            x, y = self.ref.point(e["s"], e["d"])
            self.ego = EgoState(x=float(x), y=float(y), psi=float(self.ref.evaluate(e["s"])[2] + e.get("dpsi", 0.0)),
                                vx=e["vx"], ax=e.get("ax", 0.0))
        self.horizon = horizon
        self.objects = []
        for o in data["obstacles"]:
            if "x" in o:
                self.objects.append((o["id"], o["x"], o["y"], o.get("psi", 0.0), o["v"], o.get("length", 4.5), o.get("width", 1.8)))
            else:
                x, y = self.ref.point(o["s"], o["d"])
                self.objects.append((o["id"], float(x), float(y), float(self.ref.evaluate(o["s"])[2]), o["v"], 4.5, 1.8))

    def behavior(self, t):
        d = self.data
        return BehaviorCommand(t=t, reference_line=self.ref, target_speed=d["target_speed"], d_min=d["d_min"], d_max=d["d_max"],
                               modes=[LongitudinalMode("velocity", {"v_ref": d["target_speed"]})])

    def prediction(self, t):
        objs = [constant_velocity_object(i, x + v * t * math.cos(psi), y + v * t * math.sin(psi), psi, v, t0=t,
                                         horizon=self.horizon, length=length, width=width)
                for i, x, y, psi, v, length, width in self.objects]
        return Prediction(t0=t, objects=objs)

    def object_paths(self, t_end):
        return [{"id": i, "length": length, "width": width, "x": [x, x + v * t_end * math.cos(psi)],
                 "y": [y, y + v * t_end * math.sin(psi)], "psi": psi} for i, x, y, psi, v, length, width in self.objects]


def _box(x, y, psi, length, width):
    # corners of a rectangle with center (x, y) and heading psi
    c, s = math.cos(psi), math.sin(psi)
    return [(x + a * c - b * s, y + a * s + b * c) for a, b in ((length / 2, width / 2), (length / 2, -width / 2),
                                                                 (-length / 2, -width / 2), (-length / 2, width / 2))]


def _overlap(a, b):
    # separating axis test of two convex polygons (true contact of the outlines, no safety margin)
    for poly in (a, b):
        for i in range(len(poly)):
            nx, ny = poly[i][1] - poly[i - 1][1], poly[i - 1][0] - poly[i][0]
            pa, pb = [nx * x + ny * y for x, y in a], [nx * x + ny * y for x, y in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def rollout(planner, situation, cycles, dt=0.1, on_cycle=None, t0=0.0):
    """Closed loop with ideal tracking: the ego follows each planned trajectory for dt. Returns the log."""
    ego, t = situation.ego, float(t0)
    log = {"t": [], "x": [], "y": [], "v": [], "cost": [], "valid": [], "source": [], "compute_time": [], "collision": False}
    for _ in range(cycles):
        traj, debug = planner.plan_cycle(t, ego, situation.behavior(t), situation.prediction(t))
        for key, val in (("t", t), ("x", ego.x), ("y", ego.y), ("v", ego.vx), ("cost", float(traj.cost)), ("valid", bool(traj.valid)),
                         ("source", getattr(planner, "source", "teacher")), ("compute_time", float(debug.compute_time))):
            log[key].append(val)
        if on_cycle:
            on_cycle(planner, traj, debug)
        if traj.empty:
            break
        t = round(t + dt, 10)
        ego = ego_from_point(traj.sample(t), planner.geometry, traj.reference_point, t)
        front, rear = planner.geometry.extent("cog")            # bumpers relative to the center of gravity
        mid = 0.5 * (front - rear)
        ego_box = _box(ego.x + mid * math.cos(ego.psi), ego.y + mid * math.sin(ego.psi), ego.psi, front + rear,
                       planner.geometry.width)
        for _, x, y, psi, v, length, width in situation.objects:
            if _overlap(ego_box, _box(x + v * t * math.cos(psi), y + v * t * math.sin(psi), psi, length, width)):
                log["collision"] = True
    return log


# ----------------------------------------------------------------------------- data, training, evaluation
def sample_plan_dataset(n_samples, vehicle="mid_size_sedan", config="default", seed=0, max_cycles=8, progress=None,
                        should_stop=None, situations=None, backend=None):
    """Demonstrations (features, labels) from closed-loop rollouts of random situations.

    backend None: the teacher drives (behavior cloning). With a backend the learned planner drives and every
    state it visits is labeled with the teacher's choice (data aggregation, DAgger).
    """
    rng = np.random.default_rng(seed)
    teacher = planner_for(backend, vehicle, config)
    teacher.relabel = backend is not None
    xs, ys = [], []

    def collect(planner, _traj, _debug):
        y = planner.teacher_label if planner.relabel else plan_label(planner.plan)
        if y is not None and planner.last_features is not None:
            xs.append(planner.last_features)
            ys.append(y)

    while len(xs) < n_samples:
        if should_stop and should_stop():
            break
        teacher.restart()
        rollout(teacher, Situation(sample_situation(rng, situations)), int(rng.integers(1, max_cycles + 1)), on_cycle=collect,
                t0=round(float(rng.uniform(0.0, 1.0)), 1))
        if progress:
            progress(min(len(xs) / n_samples, 1.0))
    return np.array(xs[:n_samples]), np.array(ys[:n_samples])


def evaluate_planner(backend, vehicle="mid_size_sedan", config="default", n_situations=60, cycles=10, seed=10_000,
                     situations=None):
    """Network-guided planner against the teacher on held-out situations (closed loop, same start states)."""
    rng = np.random.default_rng(seed)
    learned, teacher = planner_for(backend, vehicle, config), planner_for(None, vehicle, config)
    n = {"network": 0, "teacher": 0, "out_of_scope": 0, "infeasible": 0}
    ratios, t_learned, t_teacher, same = [], [], [], 0
    collisions, invalid, collisions_teacher, invalid_teacher, total_learned, total_teacher = 0, 0, 0, 0, 0.0, 0.0
    for _ in range(n_situations):
        data = sample_situation(rng, situations)
        t0 = round(float(rng.uniform(0.0, 1.0)), 1)
        learned.restart()
        teacher.restart()
        a, b = rollout(learned, Situation(data), cycles, t0=t0), rollout(teacher, Situation(data), cycles, t0=t0)
        for k in n:
            n[k] += learned.stats[k]
        collisions += int(a["collision"])
        collisions_teacher += int(b["collision"])
        invalid += sum(1 for v in a["valid"] if not v)
        invalid_teacher += sum(1 for v in b["valid"] if not v)
        if all(a["valid"]) and all(b["valid"]):
            total_learned += float(np.sum(a["cost"]))
            total_teacher += float(np.sum(b["cost"]))
        t_learned += a["compute_time"]
        t_teacher += b["compute_time"]
        # first cycle: identical start state, so the costs are comparable
        if a["valid"][0] and b["valid"][0] and b["cost"][0] > 1e-9:
            ratios.append(a["cost"][0] / b["cost"][0])
            same += int(abs(a["cost"][0] - b["cost"][0]) <= 1e-6 * max(b["cost"][0], 1.0))
    total = max(sum(n.values()), 1)
    in_scope = max(n["network"] + n["teacher"], 1)       # cycles with a valid trajectory inside the model's scope
    return {"n_situations": n_situations, "cycles": total,
            "network_share": n["network"] / total, "acceptance": n["network"] / in_scope,
            "fallback_share": n["teacher"] / total, "out_of_scope_share": n["out_of_scope"] / total,
            "infeasible_share": n["infeasible"] / total,
            "cost_ratio_median": float(np.median(ratios)) if ratios else None,
            "within_5_percent_share": float(np.mean(np.array(ratios) <= 1.05)) if ratios else None,
            "cost_ratio_mean": float(np.mean(ratios)) if ratios else None,
            "cost_ratio_p90": float(np.percentile(ratios, 90)) if ratios else None,
            "same_choice_share": same / max(len(ratios), 1),
            "closed_loop_cost_ratio": total_learned / total_teacher if total_teacher > 0 else None,
            "collisions": collisions, "collisions_teacher": collisions_teacher,
            "invalid_cycles": invalid, "invalid_cycles_teacher": invalid_teacher,
            "time_learned_ms": 1e3 * float(np.mean(t_learned)), "time_teacher_ms": 1e3 * float(np.mean(t_teacher))}


APPROACHES = ("regression", "classification", "dagger")
DELTA_CLASSES = np.arange(-3.5, 3.51, 0.5)                                        # end offsets of the teacher's grid
NU_CLASSES = np.concatenate([np.arange(-34.0, -4.0, 2.0), np.arange(-4.0, 4.01, 1.0)])   # end speed offsets


class ChoiceBackend:
    """Network with class outputs for the end offset and the end speed offset, and two end times.

    predict(x) returns the four numbers of the proposal: the class with the largest score for delta and nu.
    A regression averages two valid choices (swerve left or right) to an invalid one between them; picking a
    class does not.
    """

    def __init__(self, net, delta_classes=DELTA_CLASSES, nu_classes=NU_CLASSES):
        self.net = net
        self.delta, self.nu = np.asarray(delta_classes, dtype=float), np.asarray(nu_classes, dtype=float)

    def predict(self, x):
        out = np.atleast_2d(self.net.predict(x))
        nd, nn = len(self.delta), len(self.nu)
        return np.column_stack([self.delta[np.argmax(out[:, :nd], axis=1)], out[:, nd + nn],
                                self.nu[np.argmax(out[:, nd:nd + nn], axis=1)], out[:, nd + nn + 1]])


def _one_hot(values, classes):
    idx = np.argmin(np.abs(np.asarray(values)[:, None] - classes[None, :]), axis=1)
    out = np.zeros((len(idx), len(classes)))
    out[np.arange(len(idx)), idx] = 1.0
    return out


def _class_targets(y):
    return np.column_stack([_one_hot(y[:, 0], DELTA_CLASSES), _one_hot(y[:, 2], NU_CLASSES), y[:, 1], y[:, 3]])


def planner_backend(meta, backend):
    """Backend that returns the four numbers of a proposal, whatever the model's output head is."""
    head = meta.get("head") or {}
    if head.get("kind") == "classification":
        return ChoiceBackend(backend.net if hasattr(backend, "net") else backend, head["delta_classes"], head["nu_classes"])
    return backend


def train_planner(vehicle="mid_size_sedan", config="default", n_samples=6000, hidden=(96, 96), epochs=200, lr=2e-3,
                  batch=128, seed=0, progress=None, should_stop=None, eval_situations=40, approach="regression",
                  situations=None, dagger_iterations=2):
    """Returns (net, meta). progress(phase, fraction, info) as in train_surrogate.

    approach
        regression      the network predicts the four numbers of the teacher's choice (behavior cloning)
        classification  end offset and end speed offset as classes of the teacher's grid, end times as numbers
        dagger          regression, then the learned planner drives and the teacher labels the states it visits;
                        the network is trained again on all data (Ross et al. 2011). Half of n_samples are
                        teacher demonstrations, the rest is collected in `dagger_iterations` rounds.
    """
    from .backends import MLPBackend

    if approach not in APPROACHES:
        raise ValueError(f"unknown approach '{approach}', available: {APPROACHES}")
    tic = time.perf_counter()
    report = (lambda phase, frac, info=None: progress(phase, frac, info or {})) if progress else (lambda *a, **k: None)
    report("sampling", 0.0)
    classify = approach == "classification"
    n_test = max(n_samples // 5, 50)
    n_first = n_samples // 2 if approach == "dagger" else n_samples
    share = n_first / n_samples
    x, y = sample_plan_dataset(n_first + n_test, vehicle, config, seed, progress=lambda f: report("sampling", share * f),
                               should_stop=should_stop, situations=situations)
    if len(x) < 100:
        raise ValueError("training was cancelled before enough demonstrations were collected")
    n_test = min(n_test, len(x) // 5)
    x_test, y_test, x, y = x[-n_test:], y[-n_test:], x[:-n_test], y[:-n_test]
    n_out = len(DELTA_CLASSES) + len(NU_CLASSES) + 2 if classify else len(PLAN_TARGETS)

    def fit(xs, ys, quiet=False):
        net = MLP(len(PLAN_FEATURES), n_out, hidden, seed)

        def on_epoch(epoch, total, train, val):
            if not quiet:
                report("training", epoch / total, {"epoch": epoch, "train": train, "val": val})

        history = net.fit(xs, _class_targets(ys) if classify else ys, epochs=epochs, batch=batch, lr=lr, seed=seed,
                          progress=on_epoch, should_stop=should_stop)
        return net, history

    rounds = []
    if approach == "dagger":
        per_round = max((n_samples - len(x)) // max(dagger_iterations, 1), 1)
        for k in range(max(dagger_iterations, 1)):
            net, _ = fit(x, y, quiet=True)
            done = share + (1.0 - share) * k / max(dagger_iterations, 1)
            xk, yk = sample_plan_dataset(per_round, vehicle, config, seed + 101 * (k + 1), backend=MLPBackend(net),
                                         progress=lambda f, d=done: report("sampling", d + (1.0 - share) * f / max(dagger_iterations, 1)),
                                         should_stop=should_stop, situations=situations)
            if len(xk):
                x, y = np.concatenate([x, xk]), np.concatenate([y, yk])
            rounds.append(int(len(xk)))
    t_data = time.perf_counter() - tic
    net, history = fit(x, y)
    backend = ChoiceBackend(net) if classify else MLPBackend(net)
    pred = np.atleast_2d(backend.predict(x_test))
    metrics = {}
    for k, name in enumerate(PLAN_TARGETS):
        err = pred[:, k] - y_test[:, k]
        var = float(np.var(y_test[:, k]))
        metrics[name] = {"rmse": float(np.sqrt(np.mean(err**2))), "max_abs": float(np.max(np.abs(err))),
                         "r2": float(1.0 - np.mean(err**2) / var) if var > 0 else None}
    report("evaluating", 1.0)
    planner_metrics = evaluate_planner(backend, vehicle, config, eval_situations, seed=seed + 10_000, situations=situations)
    meta = {"backend": "mlp", "kind": "trajectory_planner", "vehicle": vehicle, "teacher": f"werling ({config})",
            "planner_config": config, "approach": approach, "features": list(PLAN_FEATURES), "targets": list(PLAN_TARGETS),
            "head": {"kind": "classification", "delta_classes": DELTA_CLASSES.tolist(), "nu_classes": NU_CLASSES.tolist()}
            if classify else {"kind": "regression"},
            "situations": {**SITUATION_DEFAULTS, **(situations or {})}, "dagger_rounds": rounds,
            "hidden": list(hidden), "n_samples": int(len(x)), "epochs_run": len(history), "history": history,
            "test_metrics": metrics, "planner_metrics": planner_metrics, "window": dict(WINDOW),
            "time_data_s": t_data, "time_total_s": time.perf_counter() - tic,
            "n_parameters": int(sum(w.size for w in net.W) + sum(b.size for b in net.b))}
    return net, meta


def compare_closed_loop(backend, data, vehicle="mid_size_sedan", config="default", cycles=60):
    """One situation, driven by the network-guided planner and by the teacher. Returns both logs."""
    situation = Situation(data)
    learned, teacher = planner_for(backend, vehicle, config), planner_for(None, vehicle, config)
    a, b = rollout(learned, situation, cycles), rollout(teacher, Situation(data), cycles)
    n = max(len(a["t"]), 1)
    dist = [math.hypot(xa - xb, ya - yb) for xa, ya, xb, yb in zip(a["x"], a["y"], b["x"], b["y"])]
    ref = situation.ref
    step = max(1, len(ref.s) // 300)
    left, right = ref.offset(data["d_max"]), ref.offset(data["d_min"])
    return {
        "learned": {k: a[k] for k in ("t", "x", "y", "v", "cost", "source")},
        "teacher": {k: b[k] for k in ("t", "x", "y", "v", "cost")},
        "road": {"x": ref.x[::step].tolist(), "y": ref.y[::step].tolist(), "left_x": left.x[::step].tolist(),
                 "left_y": left.y[::step].tolist(), "right_x": right.x[::step].tolist(), "right_y": right.y[::step].tolist()},
        "objects": situation.object_paths(a["t"][-1] if a["t"] else 0.0),
        "summary": {"cycles": n, "network_share": learned.stats["network"] / n, "fallback_share": learned.stats["teacher"] / n,
                    "max_path_difference": max(dist) if dist else 0.0,
                    "cost_learned": float(np.sum(a["cost"])), "cost_teacher": float(np.sum(b["cost"])),
                    "collision_learned": a["collision"], "collision_teacher": b["collision"],
                    "time_learned_ms": 1e3 * float(np.mean(a["compute_time"])), "time_teacher_ms": 1e3 * float(np.mean(b["compute_time"]))},
    }
