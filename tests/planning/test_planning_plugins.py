from dataclasses import dataclass

import numpy as np
import pytest

from vdsim.core.parameters import load_vehicle_preset, param
from vdsim.framework.plugins import available_components, component, create_component, get_component
from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, PlannerDebug, Prediction
from vdsim.geometry import ReferenceLine
from vdsim.planning import WerlingPlanner, create_planner
from vdsim.planning.combination import PlanningContext, TrajectoryBatch
from vdsim.planning.constraints import BUILTIN_CONSTRAINTS, Constraint
from vdsim.planning.kinematics import EgoGeometry
from vdsim.planning.simulation import constant_velocity_object, run_closed_loop

ROAD = ReferenceLine.straight(1000.0, ds=0.5)
EXAMPLES = "examples/custom_nodes/python"


def beh(ref=ROAD, v=20.0, **kw):
    kw.setdefault("d_min", -5.25)
    kw.setdefault("d_max", 5.25)
    return lambda t, e: BehaviorCommand(t=t, reference_line=ref, target_speed=v,
                                        modes=[LongitudinalMode("velocity", {"v_ref": v})], **kw)


def synthetic_batch(v, kappa, a, d=0.0, ctx=None):
    t = np.arange(0.0, 3.0001, 0.1)
    n = len(t)
    full = lambda val: np.broadcast_to(np.asarray(val, dtype=float), (1, n)).copy()  # noqa: E731
    fr = {k: full(0.0) for k in ("s", "s_d", "s_dd", "d_d", "d_dd", "d_p", "d_pp")}
    fr["d"] = full(d)
    w = {"x": full(0.0), "y": full(d), "theta": full(0.0), "kappa": full(kappa), "v": full(v), "a": full(a)}
    return TrajectoryBatch(t, fr, w, ROAD, ctx or PlanningContext())


def test_components_registered_and_described():
    for spec in ("trajectory_planner/werling@^1", "trajectory_planner/frenet_naive", "trajectory_planner/sequential",
                 "collision_checker/circles", "cost_term/jerk", "cost_term/comfort"):
        cls = get_component(spec)
        d = cls.describe()
        assert d["label"] and d["doc"]["summary"]
    names = {c["name"] for c in available_components("constraint")}
    assert set(BUILTIN_CONSTRAINTS) <= names
    assert {c["name"] for c in available_components("cost_term")} >= {
        "jerk", "terminal_time", "terminal_deviation", "acceleration", "lane_deviation", "travel_time", "energy",
        "comfort", "curvature", "safety_distance", "collision_risk"}
    planner = create_component("trajectory_planner/werling", {"cost": {"k_lon": 2.0}})
    assert planner.params.cost.k_lon == 2.0 and planner.PERIOD == 0.1
    assert any(p["name"] == "sampling" for p in WerlingPlanner.describe()["params"])


@pytest.mark.parametrize("name, batch_args, params", [
    ("max_lateral_acceleration", (20.0, 0.02, 0.0), {}),               # 8 m/s^2
    ("max_longitudinal_acceleration", (10.0, 0.0, -9.0), {}),
    ("max_longitudinal_acceleration", (10.0, 0.0, 3.5), {}),
    ("max_curvature", (2.0, 0.3, 0.0), {}),
    ("max_steering_angle", (2.0, 0.3, 0.0), {}),
    ("max_yaw_rate", (20.0, 0.08, 0.0), {}),
    ("tire_force", (20.0, 0.015, -7.0), {}),                     # sqrt(6^2 + 7^2) > 0.9 g
    ("vehicle_stability", (30.0, 0.008, 0.0), {"ay_linear_max": 0.5}),
    ("speed_range", (70.0, 0.0, 0.0), {}),
    ("speed_range", (-1.0, 0.0, 0.0), {}),
])
def test_constraint_plugins_detect_violations(name, batch_args, params):
    vehicle = load_vehicle_preset("mid_size_sedan")
    geo = EgoGeometry.from_vehicle(vehicle)
    c = get_component("constraint", name)(params or None)
    c.setup(vehicle, geo)
    res = c.check(synthetic_batch(*batch_args))
    assert not res.valid[0] and res.t_violation[0] == 0.0 and res.name == name
    ok = c.check(synthetic_batch(10.0, 0.0, 0.0))
    assert ok.valid[0] and np.isinf(ok.t_violation[0])


def test_jerk_steering_rate_and_envelope_constraints():
    vehicle = load_vehicle_preset("mid_size_sedan")
    geo = EgoGeometry.from_vehicle(vehicle)
    b = synthetic_batch(10.0, 0.0, 0.0)
    b.a = b.a + np.where(b.t > 1.0, -5.0, 0.0)[None, :]               # acceleration step -> jerk 25 m/s^3
    jc = get_component("constraint", "max_jerk")({"j_max": 10.0})
    r = jc.check(b)
    assert not r.valid[0] and r.t_violation[0] == pytest.approx(1.0, abs=0.11)
    b = synthetic_batch(10.0, 0.0, 0.0)
    b.kappa = b.kappa + 0.05 * b.t[None, :]                           # kappa_dot 0.05 1/(m s): delta_dot ~ 0.14
    sc = get_component("constraint", "max_steering_velocity")({"rate_max": 0.1})
    sc.setup(vehicle, geo)
    assert not sc.check(b).valid[0]
    ctx = PlanningContext(d_min=-1.75, d_max=1.75, reference_point="cog")
    env = get_component("constraint", "vehicle_envelope")()
    env.setup(vehicle, geo)
    assert env.check(synthetic_batch(10.0, 0.0, 0.0, d=0.0, ctx=ctx)).valid[0]
    assert not env.check(synthetic_batch(10.0, 0.0, 0.0, d=0.9, ctx=ctx)).valid[0]       # 0.9 + 0.925 > 1.75


@dataclass
class _NoLeftParams:
    enabled: bool = param(True, "", "aktiv")
    d_max: float = param(0.5, "m", "max. d")


@component
class _NoLeftConstraint(Constraint):
    NAME, VERSION, LABEL = "test_no_left", "1.0.0", "Test: nicht nach links"
    PARAMS = _NoLeftParams

    def violation(self, batch):
        return batch.d - self.params.d_max


def test_custom_constraint_and_disable_builtin():
    target = ROAD.offset(3.5)
    p = WerlingPlanner({"constraints": {"custom": [{"spec": "constraint/test_no_left", "params": {"d_max": -2.0}}]}})
    tr, dbg = p.plan_cycle(0.0, EgoState(vx=20.0), beh(target)(0, None))
    assert "test_no_left" in p.constraint_set.names
    # restrictions act on the common check horizon (3.5.4)
    in_horizon = (tr.t >= p.plan.t0) & (tr.t <= p.plan.t0 + p.params.collision.horizon)
    assert not dbg.fallback and np.max(tr.d[in_horizon]) <= -2.0 + 1e-6
    q = WerlingPlanner({"constraints": {"max_jerk": {"enabled": False}}})
    q.reset(None)
    assert "max_jerk" not in q.constraint_set.names


def test_cost_weights_change_the_selection():
    target = ROAD.offset(3.5)
    taus = []
    for k_tau in (1.0, 20.0):
        p = WerlingPlanner({"cost": {"terminal_time": {"k_tau_lat": k_tau}}})
        tr, dbg = p.plan_cycle(0.0, EgoState(vx=20.0), beh(target)(0, None))
        taus.append(tr.plan.lat_tau)
        assert dbg.cost_terms["quer.terminal_time"] == pytest.approx(k_tau * tr.plan.lat_tau)
    assert taus[1] < taus[0]
    # an additional (non-separable) term enters via the re-ranking window and the breakdown
    p = WerlingPlanner({"cost": {"comfort": {"weight": 1.0}, "rerank_window": 5}})
    tr, dbg = p.plan_cycle(0.0, EgoState(vx=20.0), beh(target)(0, None))
    assert "comfort" in dbg.cost_terms and dbg.cost_terms["comfort"] > 0
    assert dbg.cost_terms["gesamt"] == pytest.approx(tr.cost, rel=1e-9)
    assert not p.cost_model.consistent_only


def test_example_cost_term_and_collision_checker():
    p = WerlingPlanner({"cost": {"custom": [{"spec": f"python:{EXAMPLES}/my_cost_function.py:KeepRightCost",
                                             "params": {"weight": 50.0, "d_right": -3.0}}]}})
    tr, dbg = p.plan_cycle(0.0, EgoState(vx=20.0), beh()(0, None))
    assert "quer.keep_right" in dbg.cost_terms and tr.plan.lat_delta < 0
    obs = lambda t: Prediction(t0=t, objects=[constant_velocity_object(3, 50.0, 0.0, 0.0, 0.0, t0=t,  # noqa
                                                                         obj_type="static", length=4.0, width=2.0)])
    q = WerlingPlanner({"collision": {"checker": f"python:{EXAMPLES}/my_collision_checker.py:BoxCollisionChecker"}})
    log = run_closed_loop(q, beh(v=15.0, d_min=-1.75), EgoState(vx=15.0), 6.0, obs)
    x, y = log.array("x"), log.array("y")
    assert np.interp(50.0, x, y) > 2.0 and all(tr.valid for tr in log.trajectories)


def test_planner_configs():
    lat_tau = {}
    for name in ("default", "comfort", "sporty"):
        p = create_planner(name)
        p.reset(None)
        tr, _ = p.plan_cycle(0.0, EgoState(vx=20.0), beh(ROAD.offset(3.5))(0, None))
        lat_tau[name] = tr.plan.lat_tau
        if name != "comfort":
            assert p.config_report["warnings"] == []
    assert lat_tau["sporty"] < lat_tau["default"] < lat_tau["comfort"]


def test_debug_snapshot_and_runtime():
    p = WerlingPlanner()
    obs = Prediction(objects=[constant_velocity_object(3, 50.0, 0.0, 0.0, 0.0, obj_type="static")])
    tr, dbg = p.plan_cycle(0.0, EgoState(vx=15.0), beh(v=15.0)(0, None), obs)
    assert isinstance(dbg, PlannerDebug)
    n = len(dbg.candidates_cost)
    assert 1 < n <= p.params.search.debug_candidates + 1
    assert dbg.candidates_x.shape == dbg.candidates_s.shape == (n, len(np.arange(0, 3.0001, 0.1)))
    assert dbg.candidates_status[dbg.best_index] == 0 and len(dbg.candidates_reason) == n
    assert set(np.unique(dbg.candidates_status)) <= {0, 1, 2, 3}
    assert dbg.collision_circles["ego_radius"] > 0 and "3" in dbg.collision_circles["objects"]
    assert dbg.modes["velocity"]["valid"] and dbg.n_checked > 0 and dbg.compute_time > 0
    # typical planning cycle (free road, one mode) below 50 ms
    log = run_closed_loop(WerlingPlanner(), beh(ROAD.offset(3.5)), EgoState(vx=20.0), 5.0)
    times = np.array([d.compute_time for d in log.debug])
    assert np.median(times) < 0.05


def test_sequential_baseline_runs():
    p = create_component("trajectory_planner/sequential")
    tr, dbg = p.plan_cycle(0.0, EgoState(vx=15.0), beh(v=15.0)(0, None))
    assert tr.valid and len(tr.t) > 10
