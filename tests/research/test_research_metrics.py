import numpy as np
import pytest

from vdsim.ad.results import ADResult
from vdsim.framework.types import ObjectState, PlannedTrajectory, PlannerDebug
from vdsim.research.experiments import BatchResult, get_path, monte_carlo, parameter_sweep, set_path
from vdsim.research.metrics import (_rect_corners, consistency_deviation, cost_analysis, evaluate,
                                    rectangle_distance, safety_metrics)


def _following_result(gap0=30.0, v_ego=20.0, v_lead=15.0, T=4.0, dt=0.01):
    # ego approaches a slower lead vehicle on a straight road
    res = ADResult("follow")
    res.metadata["ego_dims"] = {"length": 4.8, "width": 1.8, "center_offset": 0.0}
    t = np.arange(0, T + 1e-9, dt)
    x_ego = v_ego * t
    x_lead = gap0 + 4.8 + v_lead * t      # center distance = gap + half lengths (both 4.8 m long)
    for k, tk in enumerate(t):
        res.append({"t": tk, "ego_x": x_ego[k], "ego_y": 0.0, "ego_psi": 0.0, "ego_vx": v_ego, "ego_v": v_ego,
                    "ego_ax": 0.0, "ego_ay": 0.0, "e_n": 0.01 * np.sin(tk), "e_t": 0.0, "collision": 0.0})
        res.add_objects(tk, [ObjectState(id=1, x=x_lead[k], y=0.0, v=v_lead, length=4.8, width=1.8)])
    return res, t, x_ego, x_lead


def test_rectangle_distance_and_overlap():
    a = _rect_corners(np.array([0.0, 0.0]), np.array([0.0, 0.0]), np.array([0.0, 0.0]), 4.0, 2.0)
    b = _rect_corners(np.array([7.0, 3.0]), np.array([0.0, 0.5]), np.array([0.0, 0.3]), 4.0, 2.0)
    d = rectangle_distance(a, b)
    assert d[0] == pytest.approx(3.0)
    assert d[1] == 0.0


def test_ttc_thw_and_min_distance():
    res, t, x_ego, x_lead = _following_result()
    m = safety_metrics(res)
    gap = x_lead - x_ego - 4.8
    assert m["min_distance"] == pytest.approx(gap.min(), abs=1e-6)
    assert m["min_ttc"] == pytest.approx(gap.min() / 5.0, rel=1e-3)
    assert m["min_thw"] == pytest.approx(gap.min() / 20.0, rel=1e-3)
    assert m["max_drac"] == pytest.approx(25.0 / (2 * gap.min()), rel=1e-3)


def test_consistency_deviation_detects_replanning_jumps():
    res = ADResult("plans")
    for k in range(5):
        t0 = 0.1 * k
        tt = np.arange(t0, t0 + 3.0, 0.05)
        traj = PlannedTrajectory(t=tt, x=10 * tt, y=np.zeros_like(tt) + (0.2 if k == 3 else 0.0),
                                 theta=np.zeros_like(tt), kappa=np.zeros_like(tt), dkappa=np.zeros_like(tt),
                                 v=np.full_like(tt, 10.0), a=np.zeros_like(tt), s=10 * tt, d=np.zeros_like(tt))
        res.add_snapshot(PlannerDebug(t=t0, cost_terms={"jerk": 1.0, "time": 2.0 + k}), traj)
    dev = consistency_deviation(res)
    assert len(dev) == 4
    assert dev[0] < 1e-6 and dev[2] == pytest.approx(0.2, abs=1e-6)
    costs = cost_analysis(res)
    assert costs["mean"]["time"] == pytest.approx(4.0)
    assert costs["share"]["jerk"] == pytest.approx(1 / 5)


def test_evaluate_and_save_load_roundtrip(tmp_path):
    res, *_ = _following_result(T=1.0)
    res.add_event(0.5, "reinit", reason="test")
    kpis = evaluate(res)
    assert kpis["reinit_count"] == 1 and kpis["distance"] == pytest.approx(20.0, rel=1e-6)
    res.save(tmp_path / "r")
    loaded = ADResult.load(tmp_path / "r")
    assert np.allclose(loaded["ego_x"], res["ego_x"])
    assert loaded.kpis["distance"] == pytest.approx(kpis["distance"])
    assert loaded.objects[1]["length"] == 4.8


def test_sweep_and_monte_carlo_jobs_are_deterministic():
    base = {"scenario": "x", "stack": {"planner": {"params": {"cost": {"k_jerk": 1.0}}}}}
    jobs = parameter_sweep(base, {"stack.planner.params.cost.k_jerk": [0.5, 2.0], "seed": [1, 2]})
    assert len(jobs) == 4 and get_path(jobs[3], "stack.planner.params.cost.k_jerk") == 2.0
    assert base["stack"]["planner"]["params"]["cost"]["k_jerk"] == 1.0   # base job untouched
    dist = {"scenario_params.speed": {"dist": "normal", "mean": 20, "std": 2}}
    a, b = monte_carlo(base, dist, 5, seed=3), monte_carlo(base, dist, 5, seed=3)
    assert [j["sample"] for j in a] == [j["sample"] for j in b]
    assert [j["seed"] for j in a] == [j["seed"] for j in b]
    assert set_path({}, "a.b.c", 1) == {"a": {"b": {"c": 1}}}


def test_batch_statistics_and_sensitivity():
    rng = np.random.default_rng(0)
    records = []
    for i in range(30):
        p = rng.uniform(0, 1)
        records.append({"label": f"r{i}", "ok": True, "job": {"sample": {"p": p}},
                        "kpis": {"max_e_n": 2 * p + 0.01 * rng.normal(), "collision": 0.0}})
    batch = BatchResult(records)
    stats = batch.statistics()
    assert stats["_runs"]["n"] == 30 and stats["max_e_n"]["n"] == 30
    sens = batch.sensitivity("max_e_n")
    assert sens["p"] > 0.95
    assert batch.best("max_e_n")["kpis"]["max_e_n"] == min(r["kpis"]["max_e_n"] for r in records)
