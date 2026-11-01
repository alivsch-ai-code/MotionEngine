import numpy as np

from vdsim.framework.types import ObjectState
from vdsim.world import build_scenario
from vdsim.world.collision import pairwise_collisions, rect_corners, sat_overlap
from vdsim.world.road import TrafficLight


def test_sat():
    a = rect_corners(0, 0, 0, 4, 2)[0]
    b = rect_corners([3.9, 4.1, 0.0, 3.5], [0, 0, 1.9, 2.5], [0, 0, 0, np.pi / 4], 4, 2)
    assert sat_overlap(a, b).tolist() == [True, False, True, False]


def test_traffic_light_cycle():
    tl = TrafficLight("A", cycle=36.0, green_start=0.0, green=12.0, yellow=3.0, red_yellow=1.0)
    seq = [tl.phase(t) for t in (0.0, 11.9, 12.0, 14.9, 15.0, 34.9, 35.0, 36.0)]
    assert seq == ["green", "green", "yellow", "yellow", "red", "red", "red_yellow", "green"]
    assert tl.state(35.5) == "red"


def test_density_no_collisions_60s():
    inst = build_scenario({"type": "traffic_density", "params": {"radius": 250.0, "density": 22.0}}, seed=3)
    sim = inst.simulator(max_dt=0.1)
    for k in range(600):
        sim.step(0.1 * k, 0.1)
        assert not pairwise_collisions(sim.object_states(include_hidden=True)), f"collision at t={0.1 * k:.1f}"
    assert sum(1 for a in sim.actors if a.last_lc > 0) > 0
    assert min(a.v for a in sim.actors) >= 0.0


def _run_triggers(name, ego_v, seed=0, steps=200):
    inst = build_scenario(name, seed=seed)
    sim = inst.simulator()
    e = inst.ego_initial
    events = []
    for k in range(steps):
        t = 0.1 * k
        ego = ObjectState(id=0, x=e["x"] + ego_v * t, y=e["y"], psi=e["psi"], v=ego_v, length=4.8, width=1.85)
        events += sim.step(t, 0.1, ego)
    return events, sim


def test_cut_in_trigger_deterministic():
    ev1, sim = _run_triggers("cut_in", 25.0)
    ev2, _ = _run_triggers("cut_in", 25.0)
    assert ev1 == ev2 and len(ev1) == 1 and ev1[0]["action"] == "lane_change"
    assert sim.actors[0].lane_id == "hw_1"


def test_pedestrian_trigger():
    ev, sim = _run_triggers("urban_driving", 8.0, steps=150)
    starts = [e for e in ev if e["action"] == "start"]
    assert len(starts) == 2 and starts[1]["t"] - starts[0]["t"] >= 0.55
    ev2, _ = _run_triggers("urban_driving", 8.0, steps=150)
    assert ev == ev2
    peds = [a for a in sim.actors if a.TYPE == "pedestrian"]
    assert all(p.visible and p.pos > 0 for p in peds)


def test_vehicles_stop_at_red_light():
    inst = build_scenario({"type": "intersection", "params": {"cross_traffic": 2, "oncoming": 0, "light_offset": 0.0}})
    sim = inst.simulator()
    for k in range(150):
        sim.step(0.1 * k, 0.1)
    # N/S group is red during the first 18 s of the cycle: cross traffic waits before the stop line
    for a in sim.actors:
        lane = inst.road.lanes[a.lane_id]
        assert a.lane_id.endswith("_in") and a.s + 0.5 * a.length <= lane.length + 0.1
