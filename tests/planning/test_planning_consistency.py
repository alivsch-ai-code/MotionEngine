import numpy as np
import pytest

from vdsim.framework.types import BehaviorCommand, ControllerStatus, EgoState, LongitudinalMode, Prediction
from vdsim.geometry import ReferenceLine
from vdsim.planning import FrenetNaivePlanner, WerlingPlanner
from vdsim.planning.simulation import constant_velocity_object, run_closed_loop

ROAD = ReferenceLine.straight(1000.0, ds=0.5)


def behavior(ref=ROAD, v=20.0, modes=None, **kw):
    kw.setdefault("d_min", -5.25)
    kw.setdefault("d_max", 5.25)
    return lambda t, e: BehaviorCommand(t=t, reference_line=ref, target_speed=v,
                                        modes=modes or [LongitudinalMode("velocity", {"v_ref": v})], **kw)


def consistency_error(log, horizon=4.0):
    # max world deviation between the plan of cycle k and the plan of cycle k+1 on the new plan's domain
    err = 0.0
    for a, b in zip(log.trajectories[:-1], log.trajectories[1:]):
        t = np.linspace(b.plan.t0, b.plan.t0 + horizon, 81)
        wa, wb = a.plan.world(t, dkappa=False), b.plan.world(t, dkappa=False)
        err = max(err, float(np.max(np.hypot(wa["x"] - wb["x"], wa["y"] - wb["y"]))),
                  float(np.max(np.abs(wa["v"] - wb["v"]))))
    return err


def test_bellman_consistency_lane_change_d_of_t():
    planner = WerlingPlanner()
    log = run_closed_loop(planner, behavior(ROAD.offset(3.5)), EgoState(x=0.0, y=0.0, vx=17.0), 8.0)
    assert all(not tr.reinitialized for tr in log.trajectories[1:])
    assert consistency_error(log) < 1e-6
    assert all(tr.lateral_mode == "time" and tr.reference_point == "cog" for tr in log.trajectories)


def test_bellman_consistency_following():
    lead = lambda t: Prediction(t0=t, objects=[constant_velocity_object(5, 45 + 12 * t, 0.0, 0.0, 12.0, t0=t)])  # noqa
    beh = behavior(v=20.0, modes=[LongitudinalMode("following", {"lead_id": 5})], d_min=-1.75, d_max=1.75)
    log = run_closed_loop(WerlingPlanner(), beh, EgoState(vx=16.0), 6.0, lead)
    assert consistency_error(log) < 1e-6


def test_bellman_consistency_slow_arc_mode():
    beh = behavior(v=2.0, d_min=-3.0, d_max=3.0)
    log = run_closed_loop(WerlingPlanner(), beh, EgoState(x=0.0, y=0.8, vx=2.0), 6.0)
    assert log.trajectories[-1].lateral_mode == "arc" and log.trajectories[-1].reference_point == "rear_axle"
    assert consistency_error(log) < 1e-6


def test_active_restriction_breaks_consistency_only_while_active():
    # narrow corridor: the envelope restriction pushes the solution away from the free optimum (3.2);
    # when it becomes inactive the plan jumps once, otherwise the cycles stay exactly consistent
    beh = behavior(v=2.0, d_min=-1.75, d_max=1.75)
    log = run_closed_loop(WerlingPlanner(), beh, EgoState(x=0.0, y=0.8, vx=2.0), 4.0)
    assert any("vehicle_envelope" in d.constraint_violations for d in log.debug[:5])
    errs = [consistency_error(type(log)(log.t[k:k + 2], log.ego[k:k + 2], log.trajectories[k:k + 2]))
            for k in range(len(log.t) - 1)]
    assert max(errs) > 1e-3
    assert np.mean(np.array(errs) < 1e-9) > 0.9


def test_cycle_time_independence():
    # consistent planner: the executed trajectory does not depend on the replanning period (Abb. 3.2)
    beh = behavior(ROAD.offset(3.5), v=15.0)
    runs = []
    for period in (0.1, 0.3):
        log = run_closed_loop(WerlingPlanner(), beh, EgoState(vx=15.0), 6.0, period=period)
        runs.append((np.array(log.t), log.array("y")))
    y_fast = np.interp(runs[1][0], *runs[0])
    assert np.max(np.abs(y_fast - runs[1][1])) < 1e-6


def test_naive_baseline_is_not_consistent():
    beh = behavior(ROAD.offset(3.5), v=15.0)
    log = run_closed_loop(FrenetNaivePlanner(), beh, EgoState(vx=15.0), 4.0)
    assert all(tr.reinitialized for tr in log.trajectories)
    assert consistency_error(log) > 1e-3


def test_output_composition_old_trajectory_until_start():
    planner = WerlingPlanner()
    beh = behavior(ROAD.offset(3.5))
    tr0, _ = planner.plan_cycle(0.0, EgoState(vx=20.0), beh(0, None))
    tr1, dbg = planner.plan_cycle(0.1, EgoState(t=0.1, x=2.0, vx=20.0), beh(0.1, None))
    t_s = 0.1 + planner.params.timing.t_comp
    assert dbg.start_state["exact"] and dbg.start_state["source"] == "plan"
    pre = tr1.t < t_s - 1e-9
    w = tr0.plan.world(tr1.t[pre], dkappa=False)
    np.testing.assert_allclose(tr1.x[pre], w["x"], atol=1e-12)
    assert tr1.t[0] == pytest.approx(0.1) and tr1.t[-1] == pytest.approx(0.1 + planner.params.timing.output_horizon)
    assert tr1.plan.t0 == pytest.approx(t_s)


def test_reinitialization_from_controller_request_and_prediction():
    planner = WerlingPlanner()
    beh = behavior(ROAD.offset(3.5))
    tr0, _ = planner.plan_cycle(0.0, EgoState(vx=20.0), beh(0, None))
    t_s = 0.1 + planner.params.timing.t_comp
    old = tr0.plan.world(np.array([t_s]), dkappa=False)
    pred = {"t": t_s, "x": 3.5, "y": 0.4, "theta": 0.02, "v": 19.0}
    status = ControllerStatus(t=0.1, reinit_request=True, prediction=pred)
    tr1, dbg = planner.plan_cycle(0.1, EgoState(t=0.1, x=2.0, y=0.4, vx=19.0), beh(0.1, None), status=status)
    st = dbg.start_state
    assert tr1.reinitialized and dbg.reinitialized and "Regler" in st["reasons"]
    assert st["source"] == "controller_prediction"
    assert (st["x"], st["y"], st["v"]) == pytest.approx((3.5, 0.4, 19.0))
    # curvature and acceleration from the current desired trajectory (bumpless, 4.5.2)
    assert st["kappa"] == pytest.approx(float(old["kappa"][0])) and st["a"] == pytest.approx(float(old["a"][0]))
    # own Taylor prediction from the ego state if the controller provides none
    status = ControllerStatus(t=0.2, reinit_request=True)
    _, dbg = planner.plan_cycle(0.2, EgoState(t=0.2, x=5.0, y=0.5, vx=19.0), beh(0.2, None), status=status)
    assert dbg.start_state["source"] == "ego_prediction"
    assert dbg.start_state["x"] == pytest.approx(5.0 + 19.0 * planner.params.timing.t_comp, abs=1e-6)


def test_stabilization_strategies():
    beh = behavior()
    req = ControllerStatus(reinit_request=True)
    low = WerlingPlanner({"stabilization": {"strategy": "low_level"}})
    low.plan_cycle(0.0, EgoState(vx=20.0), beh(0, None))
    tr, _ = low.plan_cycle(0.1, EgoState(t=0.1, x=2.0, vx=20.0), beh(0.1, None), status=req)
    assert not tr.reinitialized
    high = WerlingPlanner({"stabilization": {"strategy": "high_level"}})
    high.plan_cycle(0.0, EgoState(vx=20.0), beh(0, None))
    tr, _ = high.plan_cycle(0.1, EgoState(t=0.1, x=2.0, vx=20.0), beh(0.1, None))
    assert tr.reinitialized
    bi = WerlingPlanner()
    bi.plan_cycle(0.0, EgoState(vx=20.0), beh(0, None))
    tr, _ = bi.plan_cycle(0.1, EgoState(t=0.1, x=2.0, vx=20.0), beh(0.1, None))
    assert not tr.reinitialized
    b2 = beh(0.2, None)
    b2.reinit = True
    tr, dbg = bi.plan_cycle(0.2, EgoState(t=0.2, x=4.0, vx=20.0), b2)
    assert tr.reinitialized and "Verhaltensebene" in dbg.start_state["reasons"]


def test_regime_hysteresis_and_reference_point_switch():
    planner = WerlingPlanner()
    stop = behavior(v=6.0, modes=[LongitudinalMode("stopping", {"s_stop": 60.0})], d_min=-1.75, d_max=1.75)
    log = run_closed_loop(planner, stop, EgoState(vx=6.0), 15.0)
    modes = [(tr.reference_point, tr.lateral_mode) for tr in log.trajectories]
    assert modes[0] == ("cog", "time") and modes[-1] == ("rear_axle", "arc")
    v_switch = [tr.v[0] for tr, prev in zip(log.trajectories[1:], log.trajectories[:-1])
                if tr.reference_point != prev.reference_point]
    assert len(v_switch) == 1 and v_switch[0] < 3.0 - 0.5 + 0.2
