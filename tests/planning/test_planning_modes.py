import numpy as np
import pytest

from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
from vdsim.geometry import ReferenceLine
from vdsim.planning import WerlingPlanner
from vdsim.planning.simulation import constant_velocity_object, run_closed_loop

ROAD = ReferenceLine.straight(1500.0, ds=0.5)


def beh(ref=ROAD, v=20.0, modes=None, **kw):
    kw.setdefault("d_min", -1.75)
    kw.setdefault("d_max", 1.75)
    return lambda t, e: BehaviorCommand(t=t, reference_line=ref, target_speed=v,
                                        modes=modes or [LongitudinalMode("velocity", {"v_ref": v})], **kw)


def test_velocity_keeping_reaches_v_ref():
    log = run_closed_loop(WerlingPlanner(), beh(v=25.0), EgoState(vx=15.0), 12.0)
    assert log.ego[-1].vx == pytest.approx(25.0, abs=1e-3)
    acc = np.array([tr.a[0] for tr in log.trajectories])
    assert acc.max() < 3.0 + 1e-6


def test_lane_change_straight_road():
    target = ROAD.offset(3.5)
    log = run_closed_loop(WerlingPlanner(), beh(target, d_min=-5.25, d_max=1.75), EgoState(vx=20.0), 9.0)
    y = log.array("y")
    assert y[-1] == pytest.approx(3.5, abs=1e-3)
    assert np.all(np.diff(y) > -1e-6)                    # no overshoot back
    ay = np.array([tr.v[0] ** 2 * tr.kappa[0] for tr in log.trajectories])
    assert np.max(np.abs(ay)) < 3.0
    assert all(tr.valid for tr in log.trajectories)


def test_lane_change_curved_road():
    road = ReferenceLine.from_segments([("straight", 40.0), ("arc", 300.0, 1 / 120.0), ("straight", 300.0)])
    target = road.offset(3.5)
    log = run_closed_loop(WerlingPlanner(), beh(target, v=18.0, d_min=-5.25, d_max=1.75), EgoState(vx=18.0), 12.0)
    tr = log.trajectories[-1]
    assert abs(tr.d[0]) < 1e-3
    s, d = target.project(log.ego[-1].x, log.ego[-1].y)
    assert abs(d) < 1e-3
    assert all(tr.valid for tr in log.trajectories)


def test_following_converges_to_desired_gap():
    planner = WerlingPlanner()
    k0, kv, v_lead = 5.0, 1.5, 12.0
    lead = lambda t: Prediction(t0=t, objects=[constant_velocity_object(7, 50 + v_lead * t, 0.0, 0.0, v_lead, t0=t)])  # noqa
    modes = [LongitudinalMode("velocity", {"v_ref": 25.0}),
             LongitudinalMode("following", {"lead_id": 7, "k0": k0, "kv": kv})]
    log = run_closed_loop(planner, beh(v=25.0, modes=modes), EgoState(vx=20.0), 30.0, lead)
    t = np.array(log.t)
    front = planner.geometry.extent("cog")[0]
    gap = (50 + v_lead * t - 2.25) - (log.array("x") + front)
    assert gap[-1] == pytest.approx(k0 + kv * v_lead, abs=1e-2)
    assert log.ego[-1].vx == pytest.approx(v_lead, abs=1e-3)
    assert log.debug[-1].mode == "following"


def test_following_braking_leader_clamped_at_standstill():
    def lead(t):
        tc = min(t, 5.0)           # leader brakes with -2 m/s^2 from 10 m/s and stands still at x = 65 from t = 5 s
        obj = constant_velocity_object(3, 40 + 10 * tc - tc * tc, 0.0, 0.0, 10 - 2 * tc, t0=t,
                                       a=-2.0 if t < 5 else 0.0)
        return Prediction(t0=t, objects=[obj])

    modes = [LongitudinalMode("following", {"lead_id": 3, "k0": 4.0, "kv": 1.0})]
    planner = WerlingPlanner()
    log = run_closed_loop(planner, beh(v=15.0, modes=modes), EgoState(vx=10.0), 16.0, lead)
    front = planner.geometry.extent("cog")[0]
    assert log.ego[-1].vx == pytest.approx(0.0, abs=0.05)
    gap = (65.0 - 2.25) - (log.ego[-1].x + front)
    assert gap == pytest.approx(4.0, abs=0.3)
    assert sum(d.fallback for d in log.debug) == 0


def test_stopping_exactly_at_stop_line():
    planner = WerlingPlanner()
    log = run_closed_loop(planner, beh(v=15.0, modes=[LongitudinalMode("stopping", {"s_stop": 120.0})]),
                          EgoState(vx=15.0), 25.0)
    ego = log.ego[-1]
    assert ego.vx == pytest.approx(0.0, abs=1e-6)
    assert ego.x + planner.geometry.extent("cog")[0] == pytest.approx(120.0, abs=1e-3)
    assert np.all(log.array("vx") >= -1e-9)


def test_merging_into_gap_center():
    planner = WerlingPlanner()
    target = ROAD.offset(3.5)
    cars = lambda t: Prediction(t0=t, objects=[constant_velocity_object(1, 30 + 18 * t, 3.5, 0, 18, t0=t),  # noqa
                                               constant_velocity_object(2, -15 + 18 * t, 3.5, 0, 18, t0=t)])
    modes = [LongitudinalMode("velocity", {"v_ref": 25.0}), LongitudinalMode("merging", {"front_id": 1, "rear_id": 2})]
    log = run_closed_loop(planner, beh(target, v=25.0, modes=modes, d_min=-5.25, d_max=1.75), EgoState(vx=18.0),
                          14.0, cars)
    t = log.t[-1]
    center = log.ego[-1].x + planner.geometry.center_offset("cog")
    gap_mid = 0.5 * ((30 + 18 * t - 2.25) + (-15 + 18 * t + 2.25))
    assert center == pytest.approx(gap_mid, abs=1e-2)
    assert log.ego[-1].y == pytest.approx(3.5, abs=1e-3)


def test_replacement_strategy_selects_conservative_mode():
    planner = WerlingPlanner()
    lead = Prediction(objects=[constant_velocity_object(9, 35.0, 0.0, 0.0, 10.0)])
    modes = [LongitudinalMode("velocity", {"v_ref": 25.0}), LongitudinalMode("following", {"lead_id": 9})]
    tr, dbg = planner.plan_cycle(0.0, EgoState(vx=20.0), beh(v=25.0, modes=modes)(0, None), lead)
    jerk = {k: v["initial_jerk"] for k, v in dbg.modes.items()}
    assert dbg.modes["velocity"]["valid"] and dbg.modes["following"]["valid"]
    assert dbg.mode == "following" and jerk["following"] < jerk["velocity"]
    assert tr.longitudinal_mode == "following"
    # danger indicator (3.6): best cost per mode
    assert dbg.modes["following"]["danger"] == pytest.approx(dbg.modes["following"]["best_cost"])
    assert set(tr.metadata["danger"]) == {"velocity", "following"}


def test_slow_driving_uses_arc_mode_and_rear_axle():
    planner = WerlingPlanner()
    log = run_closed_loop(planner, beh(v=2.0, d_min=-3, d_max=3), EgoState(y=1.0, vx=1.5), 10.0)
    tr = log.trajectories[-1]
    assert tr.lateral_mode == "arc" and tr.reference_point == "rear_axle"
    assert abs(tr.d[0]) < 1e-3
    # lateral motion only while moving along the road: d(s) start from standstill
    p2 = WerlingPlanner()
    tr, _ = p2.plan_cycle(0.0, EgoState(y=1.0, vx=0.0), beh(v=0.0, d_min=-3, d_max=3)(0, None))
    assert tr.lateral_mode == "arc" and np.ptp(tr.d) < 1e-9 and np.all(np.isfinite(tr.kappa))


def test_reverse_driving():
    planner = WerlingPlanner()
    rev = ReferenceLine.straight(100.0).reversed()            # driving towards -x
    b = beh(rev, v=2.0, direction=-1)
    log = run_closed_loop(planner, b, EgoState(x=60.0, y=0.5, psi=0.0, vx=0.0, gear=-1), 10.0)
    tr = log.trajectories[-1]
    assert tr.direction == -1 and tr.reference_point == "rear_axle" and tr.lateral_mode == "arc"
    assert np.all(tr.v >= -1e-9)
    p = tr.sample(tr.t[0])
    assert np.cos(p.psi) == pytest.approx(1.0, abs=1e-3)       # vehicle still faces +x
    assert p.v_signed < 0 and log.ego[-1].x < 50.0
    assert abs(log.ego[-1].y) < 0.05


def test_output_fields_and_dkappa_robust():
    planner = WerlingPlanner()
    tr, dbg = planner.plan_cycle(0.0, EgoState(y=0.6, vx=12.0), beh(v=12.0, d_min=-3, d_max=3)(0, None))
    dt = planner.params.timing.dt_out
    assert np.allclose(np.diff(tr.t), dt)
    assert tr.t[-1] == pytest.approx(planner.params.timing.output_horizon)
    for name in ("x", "y", "theta", "kappa", "dkappa", "v", "a", "s", "d"):
        assert np.all(np.isfinite(getattr(tr, name)))
    # dkappa = dkappa/dl against finite differences of kappa over the path length
    ell = np.concatenate([[0], np.cumsum(np.hypot(np.diff(tr.x), np.diff(tr.y)))])
    num = np.gradient(tr.kappa, ell)
    assert np.max(np.abs(num[2:-2] - tr.dkappa[2:-2])) < 1e-3
    assert tr.plan is not None and tr.reference_line is ROAD
    stop = WerlingPlanner()
    log = run_closed_loop(stop, beh(v=5.0, modes=[LongitudinalMode("stopping", {"s_stop": 30.0})]),
                          EgoState(vx=5.0), 14.0)
    assert all(np.all(np.isfinite(t.dkappa)) for t in log.trajectories)
