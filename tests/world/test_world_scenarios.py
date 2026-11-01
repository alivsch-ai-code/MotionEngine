import matplotlib
import pytest

matplotlib.use("Agg")

from vdsim.framework import RunContext, create_component  # noqa: E402
from vdsim.framework.types import EgoState  # noqa: E402
from vdsim.world import (  # noqa: E402
    ADScenario,
    build_scenario,
    list_ad_scenarios,
    list_scenario_types,
    load_ad_scenario,
)
from vdsim.world.render import render_scenario  # noqa: E402

NAMES = [s["name"] for s in list_ad_scenarios()]


def test_library_complete():
    types = {t["name"] for t in list_scenario_types()}
    assert {"highway_driving", "urban_driving", "intersection", "roundabout", "highway_merge", "highway_exit",
            "parking", "overtaking", "emergency_evasion", "cut_in", "cut_out", "traffic_density",
            "werling_highway"} <= types
    assert types <= {s["type"] for s in list_ad_scenarios()}


@pytest.mark.parametrize("name", NAMES)
def test_scenario_builds_and_renders(name, tmp_path):
    import matplotlib.pyplot as plt
    inst = build_scenario(name)
    assert {"x", "y", "psi", "v"} <= set(inst.ego_initial) and inst.duration > 0
    assert inst.road.lane_at(inst.ego_initial["x"], inst.ego_initial["y"]) is not None
    sim = inst.simulator()
    for k in range(20):
        sim.step(0.1 * k, 0.1)
    fig, _ = render_scenario(inst, sim.object_states(True), t=2.0)
    fig.savefig(tmp_path / f"{name}.png", dpi=50)
    plt.close(fig)


def test_spec_roundtrip_and_seed(tmp_path):
    spec = load_ad_scenario("autobahn_ueberholen")
    spec.save(tmp_path / "x.json")
    assert ADScenario.load(tmp_path / "x.json").to_dict() == spec.to_dict()
    a = build_scenario(spec, seed=5)
    b = build_scenario(spec, seed=5)
    assert [(x.lane_id, x.s, x.v) for x in a.actors] == [(x.lane_id, x.s, x.v) for x in b.actors]


def test_engine_collision_offroad_events():
    inst = build_scenario("emergency_evasion")
    eng = create_component("world/scenario_engine")
    eng.reset(RunContext(dt=0.1, scenario=inst))
    lane, s = inst.actors[0]._spec[3], inst.actors[0]._spec[4]
    x, y, _ = inst.road.lanes[lane].pose(s)
    w = eng.step(0.0, {"ego": EgoState(x=x - 80.0, y=y, vx=20.0)})["world"]
    assert not w.objects and w.info["hidden"] == [1]          # hidden obstacle is not in the ground truth
    w = eng.step(0.1, {"ego": EgoState(x=x - 3.0, y=y, vx=20.0)})["world"]
    assert w.collision and w.collision_with == 1 and any(e["type"] == "collision" for e in w.events)
    w = eng.step(0.2, {"ego": EgoState(x=x - 30.0, y=y + 12.0, vx=20.0)})["world"]
    assert w.off_road and not w.collision


def test_lateral_impulse_event():
    inst = build_scenario({"type": "werling_highway", "params": {"gust_t": 0.3}})
    eng = create_component("world/scenario_engine")
    eng.reset(RunContext(dt=0.1, scenario=inst))
    e = inst.ego_initial
    events = []
    for k in range(6):
        events += eng.step(0.1 * k, {"ego": EgoState(x=e["x"], y=e["y"], psi=e["psi"], vx=12.5)})["world"].events
    gust = [ev for ev in events if ev["type"] == "lateral_impulse"]
    assert len(gust) == 1 and gust[0]["force_y"] > 0
