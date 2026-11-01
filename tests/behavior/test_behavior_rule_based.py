import numpy as np
import pytest

from vdsim.behavior.closed_loop import run_closed_loop
from vdsim.framework import RunContext, create_component
from vdsim.framework.types import EgoState, ObjectList, PlannedTrajectory, Prediction, WorldState
from vdsim.world import build_scenario


def _modes(cmd):
    return {m.kind: m.params for m in cmd.modes}


def test_following_after_cut_in():
    hist = run_closed_loop("cut_in", duration=20.0)
    leads = [_modes(h["behavior"]).get("following", {}).get("lead_id") for h in hist]
    assert leads[0] is None and leads[-1] == 1
    assert not any(h["world"].collision for h in hist)


def test_merge_selects_gap_and_moves_reference():
    hist = run_closed_loop("einfaedeln_lkw", duration=20.0)
    merged = [h for h in hist if "merging" in _modes(h["behavior"])]
    assert merged, "merging mode never active"
    m = _modes(merged[0]["behavior"])["merging"]
    objs = merged[0]["world"].objects
    front, rear = (next(o for o in objs if o.id == m[k]) for k in ("front_id", "rear_id"))
    assert front.lane_id == rear.lane_id == "hw_1" and front.s > rear.s           # consecutive vehicles
    switched = [h for h in hist if h["behavior"].lane_id == "hw_1" and h["behavior"].info.get("d", 0) < -2.0]
    assert switched, "reference curve was not moved while still on the acceleration lane"
    assert not any(h["world"].collision for h in hist)
    assert hist[-1]["world"].info["ego_lane"] in ("hw_0", "hw_1")


def test_stop_at_red_light():
    hist = run_closed_loop("kreuzung_ampel_geradeaus", duration=20.0)
    red = [h for h in hist if h["world"].traffic_lights["TL_W"] == "red"]
    stops = [_modes(h["behavior"]).get("stopping") for h in red]
    assert all(s is not None and s["source"] == "stop_W" for s in stops)
    assert stops[0]["s_stop"] == pytest.approx(119.0 - 1.0)
    inst = build_scenario("kreuzung_ampel_geradeaus")
    lane = inst.road.lanes["W_in"]
    s_front = [lane.center.project(h["ego"].x, h["ego"].y)[0] + 2.25 for h in red]
    assert max(s_front) <= 119.0 and min(abs(h["ego"].vx) for h in red) < 0.05


def _single_step(scenario, ego_s, lane="fwd"):
    inst = build_scenario(scenario)
    ctx = RunContext(scenario=inst, road=inst.road)
    beh = create_component("behavior_planner/rule_based")
    beh.reset(ctx)
    x, y, th = inst.road.lanes[lane].pose(ego_s)
    return beh.step(0.0, {"ego": EgoState(x=x, y=y, psi=th, vx=20.0), "objects": ObjectList(), "prediction":
                          Prediction(), "world": WorldState(road=inst.road)})["behavior"]


def test_box_restriction_markings():
    dashed = _single_step("landstrasse_ueberholen", 200.0)
    solid = _single_step("landstrasse_ueberholen", 1700.0)
    assert dashed.d_max == pytest.approx(5.25) and dashed.d_min == pytest.approx(-1.75)
    assert solid.d_max == pytest.approx(1.75) and solid.d_min == pytest.approx(-1.75)


def test_parking_direction_change_only_at_standstill():
    hist = run_closed_loop("laengsparken_rueckwaerts", duration=40.0)
    dirs = [h["behavior"].direction for h in hist]
    k = dirs.index(-1)
    assert all(d == 1 for d in dirs[:k]) and all(d == -1 for d in dirs[k:])
    assert abs(hist[k]["ego"].vx) < 0.1 and hist[k]["behavior"].reinit
    assert hist[k - 1]["behavior"].maneuver == "park_hold"
    assert hist[-1]["behavior"].maneuver == "parked"
    rev = hist[k]["behavior"].reference_line
    assert rev.theta[0] == pytest.approx(np.pi, abs=1e-6)          # reversed parking-lane reference


def test_hazard_indicator_postpones_lane_change():
    bad = PlannedTrajectory(t=np.array([0.0, 1.0]), x=np.zeros(2), y=np.zeros(2), theta=np.zeros(2),
                            kappa=np.zeros(2), dkappa=np.zeros(2), v=np.zeros(2), a=np.zeros(2), s=np.zeros(2),
                            d=np.zeros(2), valid=False)
    inst = build_scenario("autobahn_ueberholen")
    beh = create_component("behavior_planner/rule_based")
    beh.reset(RunContext(scenario=inst, road=inst.road))
    world = create_component("world/scenario_engine")
    world.reset(RunContext(scenario=inst, road=inst.road))
    lane = inst.road.lanes["hw_2"]
    x, y, th = lane.pose(inst.actors[0].s - 40.0)
    ego = EgoState(x=x, y=y, psi=th, vx=27.0)
    w = world.step(0.0, {"ego": ego})["world"]
    pred = create_component("predictor/constant_acceleration")
    pred.reset(RunContext(road=inst.road))
    pr = pred.step(0.0, {"objects": ObjectList(t=0.0, objects=w.objects), "world": w})["prediction"]
    inputs = {"ego": ego, "objects": ObjectList(objects=w.objects), "prediction": pr, "world": w}
    cmd = beh.step(0.0, {**inputs, "trajectory": bad})["behavior"]
    assert cmd.info["hazard"] and cmd.maneuver == "lane_keeping"
    beh2 = create_component("behavior_planner/rule_based")
    beh2.reset(RunContext(scenario=inst, road=inst.road))
    cmd = beh2.step(0.0, {**inputs, "trajectory": None})["behavior"]
    assert cmd.maneuver == "lane_change_left" and cmd.lane_id == "hw_1"
