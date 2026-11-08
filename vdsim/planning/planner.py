"""Werling trajectory planner (Werling 2011, chapters 2-3, appendix A).

One planning cycle (3.5.5):

    1  start state: evaluate the previous trajectory exactly at t0 + t_comp (low-level stabilization,
       temporal consistency) or, on re-initialization (system start, controller request, behavior
       request), the predicted vehicle state of 4.5.2 with curvature and acceleration of the
       current desired trajectory (bumpless)
    2  lateral mode d(t) / d(s) and reference point (CoG / rear axle) from the start speed with
       hysteresis, projection onto the reference curve (A.2) and Frenet start state (A.1)-(A.8)
    3  lateral and longitudinal candidate sets with closed-form costs (Tab. 3.1), Frenet pre-filter
    4  combination (3.2), lazy world transformation (3.1, A.1) in ascending cost order
    5  restrictions and collision check, the first valid trajectory is the best
    6  replacement strategy over the longitudinal modes (smallest initial jerk), fallback

Output: old trajectory on [t, t0 + t_comp] followed by the new one, sampled with dt_out and
continued on the target manifold up to the output horizon; plus the exact plan.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from ..core.logging_setup import get_logger
from ..core.parameters import load_vehicle_preset, param
from ..framework.context import RunContext
from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import TrajectoryPlannerBase
from ..framework.plugins import component, create_component
from ..framework.types import LongitudinalMode, PlannedTrajectory, PlannerDebug, Prediction
from ..geometry.reference_line import FrenetState
from .analysis import estimate_sampling_horizon, lock_in_check
from .collision import CollisionSettings
from .combination import CandidateEvaluator, PlanningContext
from .constraints import ConstraintSet, ConstraintSettings, MaxCurvature, group, limits_for_prefilter
from .cost import CostModel, CostSettings
from .kinematics import EgoGeometry, convert_reference, ego_reference_state, taylor_prediction
from .lateral import build_lateral_set
from .longitudinal import LongitudinalParams, VelocityTarget, build_longitudinal_set, make_target
from .plan import TrajectoryPlan
from .sampling import SamplingParams
from .selection import STATUS_CONSTRAINT, STATUS_UNCHECKED, SelectionSettings, choose_fallback, choose_mode, select_mode

log = get_logger("planning")


# ----------------------------------------------------------------------------- parameters
@dataclass
class TimingParams:
    t_comp: float = param(0.05, "s", "Konservative Rechenzeit t_comp (Startzeit t0 + t_comp)", min=0.0, max=1.0)
    dt_out: float = param(0.05, "s", "Abtastung der Ausgabetrajektorie", min=0.005, max=0.5)
    output_horizon: float = param(6.0, "s", "Ausgabehorizont (auf der Mannigfaltigkeit verlängert)", min=0.5, max=30.0)


@dataclass
class StabilizationParams:
    strategy: str = field(default="bilevel", metadata={"label": "Stabilisierungsstrategie", "unit": "",
                                                       "choices": ["bilevel", "low_level", "high_level"]})
    v_switch: float = param(3.0, "m/s", "Umschaltgeschwindigkeit v_s langsam/schnell", min=0.0, max=20.0)
    hysteresis: float = param(0.5, "m/s", "Hysterese der Umschaltung", min=0.0, max=5.0)
    use_controller_prediction: bool = param(True, "", "Prädiktion des Reglers (ControllerStatus.prediction) nutzen")
    reinit_distance: float = param(0.0, "m", "Zusätzliche Reinitialisierung ab Positionsfehler (0 = aus)", min=0.0,
                                   max=50.0)


@dataclass
class SearchParams:
    batch_min: int = param(32, "", "Erste Batchgröße der Lazy-Prüfung", min=1, max=4096)
    batch_max: int = param(1024, "", "Max. Batchgröße", min=1, max=8192)
    max_checks: int = param(15000, "", "Max. geprüfte Kandidaten je Modus", min=1, max=200000)
    brake_candidates: int = param(8, "", "Zusätzlich geprüfte Bremskandidaten (Fallback)", min=0, max=100)
    debug_candidates: int = param(150, "", "Kandidaten in PlannerDebug", min=0, max=2000)
    arc_grid_step: float = param(0.5, "m", "Prüfraster d(s) für den Vorfilter", min=0.05, max=5.0)


@dataclass
class WerlingPlannerParams:
    sampling: SamplingParams = group(SamplingParams, "Sampling (Zielmannigfaltigkeiten)")
    longitudinal: LongitudinalParams = group(LongitudinalParams, "Längsmodi")
    cost: CostSettings = group(CostSettings, "Kostenfunktion")
    constraints: ConstraintSettings = group(ConstraintSettings, "Restriktionen")
    collision: CollisionSettings = group(CollisionSettings, "Kollisionsprüfung")
    timing: TimingParams = group(TimingParams, "Zeitverhalten")
    stabilization: StabilizationParams = group(StabilizationParams, "Bi-level-Stabilisierung")
    search: SearchParams = group(SearchParams, "Suche")


@dataclass
class StartState:
    t: float
    world: dict                     # x, y, theta, kappa, v, a of the reference point
    frenet: FrenetState
    reference_point: str
    lateral_mode: str
    direction: int
    source: str                     # "plan" / "controller_prediction" / "ego_prediction"
    reinitialized: bool
    reasons: list
    exact: bool                     # Frenet state evaluated exactly from the previous polynomials

    def to_dict(self):
        f = self.frenet
        return {"t": self.t, **{k: float(v) for k, v in self.world.items() if k != "reference_point"},
                "s": f.s, "s_d": f.s_d, "s_dd": f.s_dd, "d": f.d, "d_d": f.d_d, "d_dd": f.d_dd, "d_p": f.d_p,
                "d_pp": f.d_pp, "reference_point": self.reference_point, "lateral_mode": self.lateral_mode,
                "direction": self.direction, "source": self.source, "reinitialized": self.reinitialized,
                "reasons": list(self.reasons), "exact": self.exact}


def same_line(a, b):
    # identical reference curve (object identity or identical samples)
    if a is b:
        return True
    if a is None or b is None or len(a.s) != len(b.s):
        return False
    return bool(np.array_equal(a.s, b.s) and np.array_equal(a.x, b.x) and np.array_equal(a.y, b.y))


DOC = ComponentDoc(
    summary="Trajektorienplanung nach Werling: optimale Polynome in Frenet-Koordinaten, diskretisierte "
            "Zielmannigfaltigkeiten auf absolutem Zeitraster, zeitliche Konsistenz und Bi-level-Stabilisierung.",
    purpose="Reaktive, zeitkritische Kollisionsvermeidung mit kombinierter Längs- und Queroptimierung, die bei "
            "inaktiven Restriktionen dank Bellman-Prinzip zeitlich konsistent ist (Werling 2011, Kap. 3).",
    theory="Quer- und Längsbewegung sind Ausgang einer Integratorkette; die ruckoptimalen Lösungen sind "
           "quintische (fester Endzustand) bzw. quartische Polynome (freie Endposition). Endzeitpunkte und "
           "Endversätze werden auf der Zielmannigfaltigkeit diskretisiert; die beste restriktionskonforme "
           "Kombination wird lazy in aufsteigender Kostenreihenfolge gesucht.",
    assumptions=["Schwimmwinkel am Referenzpunkt = 0 für die Kollisionsprüfung",
                 "Vorderfahrzeuge mit konstanter Beschleunigung (geklemmt im Stillstand)",
                 "Referenzkurve mit stetiger Krümmungsänderung (Bemerkung 4)"],
    limitations=["zeitliche Konsistenz nur bei inaktiven Restriktionen und rein konsistenten Kostentermen",
                 "Funktionenklasse auf doppelte Kursänderung beschränkt (keine Labyrinth-Manöver)",
                 "Richtungswechsel (ς) nur im Stillstand über die Verhaltensebene"],
    design_decisions=[
        {"decision": "Absolutes Endzeitraster + Schutz des alten Optimums", "reason": "Satz 3 (zeitliche Konsistenz)",
         "alternatives": "relatives Raster (trajectory_planner/frenet_naive)"},
        {"decision": "Exakte Polynom-Repräsentation im Plan", "reason": "Bellman exakt, keine Interpolation"},
        {"decision": "Restriktionen, Kostenterme und Kollisionsprüfer als Plugins", "reason": "erweiterbar"}],
    references=["werling2011", "werling2010icra", "werling2012ijrr", "ziegler2010iv"],
    equations=["werling2011:(3.1)", "werling2011:(3.2)", "werling2011:(3.4)", "werling2011:(3.8)",
               "werling2011:(3.12)", "werling2011:(3.13)", "werling2011:(3.14)", "werling2011:(3.15)",
               "werling2011:Tab. 3.1", "werling2011:(A.1)-(A.8)"],
    validation=["tests/planning/test_planning_consistency.py", "tests/planning/test_planning_modes.py",
                "tests/planning/test_planning_polynomials.py"],
    extension_points=["@component(kind='cost_term')", "@component(kind='constraint')",
                      "@component(kind='collision_checker')"],
    concepts=["quintic_polynomial", "quartic_polynomial", "absolute_time_grid", "bellman_principle",
              "lateral_sampling", "longitudinal_sampling", "lazy_selection", "replacement_strategy",
              "bilevel_stabilization"])


@component
class WerlingPlanner(TrajectoryPlannerBase):
    NAME, VERSION = "werling", "1.0.0"
    LABEL = "Trajektorienplaner (Werling)"
    PARAMS = WerlingPlannerParams
    PERIOD = 0.1
    DOC = DOC

    def __init__(self, params=None, **overrides):
        super().__init__(params, **overrides)
        self.plan = None
        self.regime = None
        self.last_trajectory = None
        self.last_debug = None
        self.cycle = 0
        self.config_report = {}

    # ------------------------------------------------------------------ lifecycle
    def reset(self, context=None):
        context = context or RunContext()
        super().reset(context)
        self.vehicle = context.vehicle if context.vehicle is not None else load_vehicle_preset("mid_size_sedan")
        p = self.params
        self.geometry = EgoGeometry.from_vehicle(self.vehicle, p.collision.front_overhang, p.collision.rear_overhang)
        self.cost_model = CostModel(p.cost, self.vehicle, self.geometry)
        self.constraint_set = ConstraintSet(p.constraints, self.vehicle, self.geometry)
        self.checker = create_component(p.collision.checker, p.collision.checker_params or None)
        self.plan, self.regime, self.last_trajectory, self.last_debug, self.cycle = None, None, None, None, 0
        lock = lock_in_check(p.sampling, p.cost)
        horizon = estimate_sampling_horizon(p.sampling, p.cost)
        self.config_report = {"lock_in": lock, "sampling_horizon": horizon,
                              "warnings": lock["warnings"] + horizon["warnings"]}
        if not self.cost_model.consistent_only:
            self.config_report["warnings"].append("nicht-konsistente Kostenterme aktiv: Bellman-Garantie entfällt")
        for w in self.config_report["warnings"]:
            log.warning("planner %s: %s", self.instance_name, w)

    def step(self, t, inputs):
        ego, behavior = inputs.get("ego"), inputs.get("behavior")
        if self.context is None:
            self.reset(RunContext())
        if ego is None or behavior is None or behavior.reference_line is None:
            return {"trajectory": self.last_trajectory, "debug": PlannerDebug(t=t, info={"error": "keine Eingänge"})}
        traj, debug = self.plan_cycle(t, ego, behavior, inputs.get("prediction"), inputs.get("status"))
        return {"trajectory": traj, "debug": debug}

    # ------------------------------------------------------------------ cycle
    def plan_cycle(self, t, ego, behavior, prediction=None, status=None):
        if self.context is None:
            self.reset(RunContext())
        tic = time.perf_counter()
        p = self.params
        prediction = prediction if prediction is not None else Prediction(t0=t)
        ref = behavior.reference_line
        direction = 1 if behavior.direction >= 0 else -1
        t_s = float(t) + p.timing.t_comp
        old = self.plan
        start = self._start_state(t, t_s, ego, behavior, status, direction)
        timings = {"start": time.perf_counter() - tic}
        ctx = PlanningContext(t=float(t), t_start=t_s, reference_line=ref, behavior=behavior, prediction=prediction,
                              geometry=self.geometry, vehicle=self.vehicle, reference_point=start.reference_point,
                              lateral_mode=start.lateral_mode, direction=direction, d_ref=float(behavior.d_ref),
                              d_min=float(behavior.d_min), d_max=float(behavior.d_max),
                              target_speed=float(behavior.target_speed),
                              t_grid=np.arange(0.0, p.collision.horizon + 1e-9, p.collision.dt), dt=p.collision.dt,
                              start=start)
        self.checker.prepare(prediction, t_s + ctx.t_grid, self.geometry, p.collision, ctx)
        # ---- step 3: candidate sets
        line_kept = old is not None and same_line(old.reference_line, ref) and old.direction == direction
        keep_lat = old.lat_k if line_kept and old.lateral_mode == start.lateral_mode else None
        keep_lon = old.lon_k if line_kept else None
        lon_limits, lat_limit = limits_for_prefilter(p.constraints, p.sampling.prefilter_factor)
        if not p.sampling.prefilter:
            lon_limits, lat_limit = (-np.inf, np.inf, np.inf), np.inf
        if start.lateral_mode == "arc":
            kappa_lim = np.inf
            if p.sampling.prefilter:
                mc = MaxCurvature(p.constraints.max_curvature)
                mc.setup(self.vehicle, self.geometry)
                kappa_lim = 2.0 * p.sampling.prefilter_factor * mc.limit()
            length = max(p.sampling.arc_s_max, max(start.frenet.s_d, 1.0) * p.collision.horizon) + 1.0
            lat_grid = np.arange(0.0, length + 1e-9, p.search.arc_grid_step)
            lat_limit = kappa_lim
        else:
            lat_grid = ctx.t_grid
        lat = build_lateral_set(start.frenet, start.lateral_mode, t_s, behavior.d_ref, behavior.d_min, behavior.d_max,
                                0.5 * self.geometry.width, p.sampling, lat_grid, keep_lat, lat_limit)
        self.cost_model.lateral(lat, ctx)
        modes = list(behavior.modes) or [LongitudinalMode("velocity", {"v_ref": behavior.target_speed})]
        sel = SelectionSettings(p.search.batch_min, p.search.batch_max, p.search.max_checks,
                                p.cost.rerank_window if self.cost_model.combined_terms else 1,
                                p.search.brake_candidates)
        results, mode_info, labels = [], {}, {}
        for mode in modes:
            label = mode.kind if mode.kind not in labels else f"{mode.kind}#{labels[mode.kind] + 1}"
            labels[mode.kind] = labels.get(mode.kind, 0) + 1
            target, why = make_target(mode, behavior, prediction, ref, t_s, self.geometry, start.reference_point,
                                      direction, p.longitudinal)
            if target is None:
                mode_info[label] = {"kind": mode.kind, "active": False, "reason": why}
                continue
            results.append(self._run_mode(label, target, start, t_s, keep_lon, lon_limits, lat, ctx, sel))
        if not results:
            # no realizable mode: plan a stop with the velocity set (emergency behavior)
            results.append(self._run_mode("velocity(Notfall)", VelocityTarget(0.0), start, t_s, keep_lon, lon_limits,
                                          lat, ctx, sel))
        timings["search"] = time.perf_counter() - tic - timings["start"]
        # ---- step 6: replacement strategy / fallback
        chosen, fallback = choose_mode(results), False
        if chosen is None:
            chosen, fallback = choose_fallback(results), True
        if chosen is None:
            # nothing could be checked at all: keep the cheapest candidate of the first mode
            chosen, fallback = results[0], True
            chosen.fallback = int(chosen.order[0]) if len(chosen.order) else 0
        c = chosen.fallback if fallback else chosen.best
        plan = self._make_plan(chosen, c, start, ref, direction, behavior, fallback)
        traj = self._compose_output(t, t_s, plan, start, old, ego, behavior)
        traj.reinitialized = start.reinitialized
        timings["output"] = time.perf_counter() - tic - timings["start"] - timings["search"]
        debug = self._debug(t, start, chosen, c, results, mode_info, fallback, ctx, plan)
        debug.compute_time = time.perf_counter() - tic
        debug.info["timings"] = {k: float(v) for k, v in timings.items()}
        traj.metadata.update({"danger": {k: v.get("best_cost") for k, v in debug.modes.items()},
                              "t_start": t_s, "compute_time": debug.compute_time, "mode": chosen.label})
        self.plan, self.last_trajectory, self.last_debug = plan, traj, debug
        self.cycle += 1
        self.signals.update({"cost": float(plan.cost), "valid": float(plan.valid),
                             "reinit": float(start.reinitialized), "compute_time": debug.compute_time})
        return traj, debug

    # ------------------------------------------------------------------ step 1/2: start state
    def _reinit_reasons(self, t, ego, behavior, status, direction):
        p = self.params.stabilization
        if self.plan is None:
            return ["Systemstart"]
        if self.plan.direction != direction:
            return ["Richtungswechsel"]
        if p.strategy == "high_level":
            return ["high_level"]
        if p.strategy == "low_level":
            return []
        reasons = []
        if status is not None and getattr(status, "reinit_request", False):
            reasons.append("Regler")
        if behavior.reinit:
            reasons.append("Verhaltensebene")
        if p.reinit_distance > 0 and ego is not None:
            w = self.plan.world(np.array([float(ego.t)]), dkappa=False)
            w_cog = convert_reference({"x": float(w["x"][0]), "y": float(w["y"][0]), "theta": float(w["theta"][0])},
                                      self.plan.reference_point, "cog", self.geometry, self.plan.direction)
            if np.hypot(w_cog["x"] - ego.x, w_cog["y"] - ego.y) > p.reinit_distance:
                reasons.append("Positionsfehler")
        return reasons

    @trace("werling2011", section="4.5.2", concept="bilevel_stabilization",
           note="Reinitialisierung: Position, Richtung, Geschwindigkeit prädiziert; Krümmung, Beschleunigung von der "
                "aktuellen Solltrajektorie (stoßfrei)")
    def _start_state(self, t, t_s, ego, behavior, status, direction):
        p = self.params
        old = self.plan
        reasons = self._reinit_reasons(t, ego, behavior, status, direction)
        reinit = bool(reasons)
        if not reinit:
            w = old.world(np.array([t_s]), dkappa=False)
            world = {k: float(w[k][0]) for k in ("x", "y", "theta", "kappa", "v", "a")}
            src_point, source = old.reference_point, "plan"
        else:
            world, src_point, source = self._predicted_state(t_s, ego, status, direction)
        regime = self._regime(world["v"], direction)
        ref_point, lat_mode = ("rear_axle", "arc") if regime == "slow" else ("cog", "time")
        world = convert_reference(world, src_point, ref_point, self.geometry, direction)
        ref = behavior.reference_line
        exact = (not reinit and same_line(old.reference_line, ref) and old.reference_point == ref_point
                 and old.lateral_mode == lat_mode)
        if exact:
            f = old.frenet(np.array([t_s]))
            fs = FrenetState(*(float(f[k][0]) for k in ("s", "s_d", "s_dd", "d", "d_d", "d_dd", "d_p", "d_pp")))
        else:
            hint = None
            if old is not None and same_line(old.reference_line, ref):
                s_old = float(old.frenet(np.array([t_s]))["s"][0])
                hint = int(np.clip(np.searchsorted(ref.s, s_old), 0, len(ref.s) - 1))
            fs = ref.to_frenet(world["x"], world["y"], world["theta"], world["kappa"], world["v"], world["a"], hint)
        self.regime = regime
        return StartState(t_s, world, fs, ref_point, lat_mode, direction, source, reinit, reasons, exact)

    def _predicted_state(self, t_s, ego, status, direction):
        # reference point state at t_s for a re-initialization (Werling 4.5.2)
        sp = self.params.stabilization
        old = self.plan
        old_ok = old is not None and old.direction == direction
        guess = "rear_axle" if direction < 0 or (self.regime == "slow") or \
            (self.regime is None and abs(ego.vx) <= sp.v_switch) else "cog"
        pred = status.prediction if (sp.use_controller_prediction and status is not None
                                     and isinstance(getattr(status, "prediction", None), dict)) else None
        if pred is not None and all(k in pred for k in ("x", "y", "theta", "v")):
            point = pred.get("reference_point", old.reference_point if old is not None else guess)
            base = {"x": float(pred["x"]), "y": float(pred["y"]), "theta": float(pred["theta"]),
                    "v": abs(float(pred["v"]))}
            t_pred = float(pred.get("t", t_s))
            source = "controller_prediction"
        else:
            point = guess
            e = ego_reference_state(ego, point, self.geometry, sp.v_switch)
            base = {k: e[k] for k in ("x", "y", "theta", "v")}
            t_pred = float(ego.t)
            source = "ego_prediction"
            pred = e
        if old_ok:
            ow = old.world(np.array([t_s]), dkappa=False)
            kappa, accel = float(ow["kappa"][0]), float(ow["a"][0])
        else:
            kappa = float(pred.get("kappa", 0.0))
            accel = float(pred.get("a", pred.get("v_dot", 0.0)))
        theta_dot = float(pred.get("theta_dot", kappa * base["v"]))
        v_dot = float(pred.get("v_dot", accel))
        dt = t_s - t_pred
        if abs(dt) > 1e-9:
            x, y, th, v = taylor_prediction(base["x"], base["y"], base["theta"], base["v"], v_dot, theta_dot, dt)
            base = {"x": float(x), "y": float(y), "theta": float(th), "v": max(float(v), 0.0)}
        base.update({"kappa": kappa, "a": accel})
        if not old_ok and base["v"] < 1e-3 and accel < 0:
            base["a"] = 0.0
        return base, point, source

    def _regime(self, v, direction):
        sp = self.params.stabilization
        if direction < 0:
            return "slow"
        if self.regime is None:
            return "fast" if v > sp.v_switch else "slow"
        if self.regime == "fast" and v < sp.v_switch - sp.hysteresis:
            return "slow"
        if self.regime == "slow" and v > sp.v_switch + sp.hysteresis:
            return "fast"
        return self.regime

    # ------------------------------------------------------------------ steps 3-5 per mode
    def _run_mode(self, label, target, start, t_s, keep_lon, lon_limits, lat, ctx, sel):
        p = self.params
        lon = build_longitudinal_set(start.frenet, target, t_s, p.sampling, ctx.t_grid, keep_lon, lon_limits, label)
        self.cost_model.longitudinal(lon, ctx)
        evaluator = CandidateEvaluator(ctx.reference_line, lat, lon, ctx)
        res = select_mode(label, lat, lon, evaluator, self.cost_model, self.constraint_set, self.checker, ctx, sel,
                          p.cost.k_lat, p.cost.k_lon)
        res.target = target
        return res

    def _make_plan(self, res, c, start, ref, direction, behavior, fallback):
        i, j = res.split(c)
        lat, lon = res.lat, res.lon
        cost = res.best_cost if not fallback else float(res.total[c])
        return TrajectoryPlan(t0=start.t, reference_line=ref, reference_point=start.reference_point,
                              lateral_mode=start.lateral_mode, direction=direction, lat=lat.poly.take(i),
                              lon=lon.poly.take(j), lat_s0=lat.s0, lat_k=int(lat.k[i]), lon_k=int(lon.k[j]),
                              lat_delta=float(lat.delta[i]), lat_tau=float(lat.tau[i]),
                              lon_offset=float(lon.offset[j]), lon_tau=float(lon.tau[j]), lon_kind=lon.kind,
                              lon_label=res.label, d_ref=float(behavior.d_ref), cost=float(cost), valid=not fallback,
                              info={"combined_costs": res.combined_costs})

    # ------------------------------------------------------------------ output
    @trace("werling2011", section="3.5.5", equation="Schritt 1", concept="bellman_principle",
           note="Ausgabe = alte Trajektorie auf [t, t0 + t_comp], danach die neue")
    def _compose_output(self, t, t_s, plan, start, old, ego, behavior):
        p = self.params.timing
        n = int(round(p.output_horizon / p.dt_out))
        t_out = float(t) + np.arange(n + 1) * p.dt_out
        if t_s - t > 1e-9 and not np.any(np.isclose(t_out, t_s, atol=1e-9)):
            t_out = np.sort(np.append(t_out, t_s))
        pre = t_out < t_s - 1e-9
        new = plan.world(t_out[~pre])
        keys = ("x", "y", "theta", "kappa", "dkappa", "v", "a", "s", "d")
        if np.any(pre):
            tp = t_out[pre]
            if not start.reinitialized and old is not None:
                w = old.world(tp)
                if old.reference_point != plan.reference_point:
                    w.update(convert_reference(w, old.reference_point, plan.reference_point, self.geometry,
                                               plan.direction))
                if not same_line(old.reference_line, plan.reference_line):
                    w["s"], w["d"] = plan.reference_line.project_many(w["x"], w["y"])
            else:
                # re-initialization: predicted motion from the current state up to the new start (4.5.2)
                sw = start.world
                x, y, th, v = taylor_prediction(sw["x"], sw["y"], sw["theta"], sw["v"], sw["a"], sw["kappa"] * sw["v"],
                                                tp - t_s)
                w = {"x": x, "y": y, "theta": th, "v": np.maximum(v, 0.0), "kappa": np.full_like(tp, sw["kappa"]),
                     "a": np.full_like(tp, sw["a"]), "dkappa": np.zeros_like(tp)}
                w["s"], w["d"] = plan.reference_line.project_many(x, y)
            arrays = {k: np.concatenate([np.asarray(w[k], dtype=float), np.asarray(new[k], dtype=float)]) for k in keys}
        else:
            arrays = {k: np.asarray(new[k], dtype=float) for k in keys}
        arrays["theta"] = np.unwrap(arrays["theta"])
        return PlannedTrajectory(t=t_out, **arrays, direction=plan.direction, reference_point=plan.reference_point,
                                 lateral_mode=plan.lateral_mode, longitudinal_mode=plan.lon_kind, cost=plan.cost,
                                 valid=plan.valid, reinitialized=start.reinitialized, plan=plan,
                                 reference_line=plan.reference_line, metadata={"mode_label": plan.lon_label})

    # ------------------------------------------------------------------ debug
    def _debug(self, t, start, chosen, c_sel, results, mode_info, fallback, ctx, plan):
        n_max = self.params.search.debug_candidates
        order = chosen.order
        picks = list(order[:min(50, len(order))])
        rest = order[len(picks):]
        n_even = max(n_max - len(picks) - 20, 0)
        if len(rest) and n_even:
            picks += list(rest[np.linspace(0, len(rest) - 1, min(n_even, len(rest))).astype(int)])
        # boolean membership mask instead of setdiff1d + a Python set over all ~1e4 ordered candidates:
        # the debug snapshot took about half of the planning cycle (benchmarks/README.md, hotspots)
        in_order = np.zeros(len(chosen.total), dtype=bool)
        in_order[np.asarray(order, dtype=int)] = True
        infeasible = np.flatnonzero(~in_order)
        if len(infeasible):
            picks += list(infeasible[np.linspace(0, len(infeasible) - 1, min(20, len(infeasible))).astype(int)])
        picks = [int(c) for c in dict.fromkeys(picks) if int(c) != int(c_sel)][:n_max]
        picks.append(int(c_sel))
        ci = np.array(picks, dtype=int)
        n_lon = len(chosen.lon)
        batch = chosen.evaluator.batch(ci // n_lon, ci % n_lon) if len(ci) else None
        status, reasons = [], []
        for c in picks:
            if chosen.status[c] != STATUS_UNCHECKED:
                status.append(int(chosen.status[c]))
                reasons.append(chosen.reason.get(c, ""))
            elif not in_order[c]:
                status.append(STATUS_CONSTRAINT)
                reasons.append("Vorfilter (straßenrelative Beschleunigung)")
            else:
                status.append(STATUS_UNCHECKED)
                reasons.append("")
        violations = {}
        for r in results:
            for k, v in r.violations.items():
                violations[k] = violations.get(k, 0) + v
        modes = dict(mode_info)
        for r in results:
            modes[r.label] = {"kind": r.kind, "active": True, "valid": r.best is not None,
                              "best_cost": float(r.best_cost) if r.best is not None else None,
                              "initial_jerk": float(r.initial_jerk) if np.isfinite(r.initial_jerk) else None,
                              "n_candidates": int(r.n_candidates), "n_feasible": int(r.n_feasible),
                              "n_checked": len(r.checked),
                              "fallback_time": float(r.fallback_time) if np.isfinite(r.fallback_time) else None,
                              "danger": float(r.best_cost) if r.best is not None else float("inf"),
                              "target": getattr(r.target, "to_dict", lambda: {})(), "note": r.note,
                              "selected": r is chosen}
        i, j = chosen.split(c_sel)
        terms = self.cost_model.breakdown(chosen.lat, i, chosen.lon, j, chosen.combined_costs)
        f32 = np.float32
        dbg = PlannerDebug(
            t=float(t), start_state=start.to_dict(),
            candidates_x=batch.x.astype(f32) if batch is not None else np.zeros((0, 0), f32),
            candidates_y=batch.y.astype(f32) if batch is not None else np.zeros((0, 0), f32),
            candidates_s=batch.s.astype(f32) if batch is not None else np.zeros((0, 0), f32),
            candidates_d=batch.d.astype(f32) if batch is not None else np.zeros((0, 0), f32),
            candidates_cost=np.array([chosen.total[c] for c in picks], dtype=float),
            candidates_status=np.array(status, dtype=np.int8), candidates_reason=reasons,
            best_index=len(picks) - 1, cost_terms=terms, constraint_violations=violations,
            n_candidates=int(sum(r.n_candidates for r in results)),
            n_checked=int(sum(len(r.checked) for r in results)), mode=chosen.label, modes=modes,
            reinitialized=start.reinitialized, fallback=bool(fallback),
            collision_circles=self.checker.geometry_info(),
            info={"reference_point": start.reference_point, "lateral_mode": start.lateral_mode,
                  "regime": self.regime, "reinit_reasons": list(start.reasons), "start_source": start.source,
                  "exact_start": start.exact, "t_start": start.t, "plan": plan.summary(),
                  "fallback_time": float(chosen.fallback_time) if fallback and np.isfinite(chosen.fallback_time)
                  else None, "warnings": list(self.config_report.get("warnings", [])),
                  "n_lateral": len(chosen.lat), "n_longitudinal": {r.label: len(r.lon) for r in results}})
        return dbg
