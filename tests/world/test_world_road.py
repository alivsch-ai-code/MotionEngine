import numpy as np
import pytest

from vdsim.world.road_builders import (
    build_highway,
    build_intersection,
    build_parking_street,
    build_ring_road,
    build_roundabout,
    build_rural_road,
    build_urban_street,
    ring_route,
)

BUILDERS = [lambda: build_highway(merge={}, exit={}), build_ring_road,
            lambda: build_rural_road(solid_sections=[(500, 800)]), lambda: build_urban_street(junction_x=200.0),
            build_parking_street, build_intersection, lambda: build_intersection(control="yield"), build_roundabout]


def _max_dkappa_jump(line):
    return float(np.max(np.abs(np.diff(line.dkappa))))


@pytest.mark.parametrize("builder", BUILDERS)
def test_connections_continuous(builder):
    net = builder()
    assert net.validate() == []                         # position, heading, kappa, dkappa at all joints
    for lane in net.lanes.values():
        assert _max_dkappa_jump(lane.center) < 0.05     # C1 curvature inside every lane


def test_routes_are_single_continuous_lines():
    net = build_roundabout()
    route = ring_route(net, "W", "E")
    line = net.route_line(route)
    assert line.lane_ids == tuple(route)
    assert _max_dkappa_jump(line) < 0.05
    assert np.max(np.hypot(np.diff(line.x), np.diff(line.y))) < 0.3      # no gaps
    assert net.route_line(route) is line                                 # cached: stable reference object
    inter = build_intersection()
    for turn in ("N", "E", "S"):
        line = inter.route_line(["W_in", f"W>{turn}", f"{turn}_out"])
        assert _max_dkappa_jump(line) < 0.05
        assert np.max(np.abs(line.kappa)) < 0.2


def test_corridor_markings():
    net = build_rural_road(solid_sections=[(500, 800)])
    assert net.corridor("fwd", 100.0) == pytest.approx((-1.75, 5.25))      # dashed: oncoming lane usable
    assert net.corridor("fwd", 600.0) == pytest.approx((-1.75, 1.75))      # solid: own lane only
    assert net.corridor("fwd", 100.0, include_opposite=False) == pytest.approx((-1.75, 1.75))
    hw = build_highway(merge={"s": 200.0, "length": 300.0})
    assert hw.corridor("hw_2", 300.0)[0] == pytest.approx(-5.625)          # acceleration lane next to it
    assert hw.corridor("hw_2", 1000.0)[0] == pytest.approx(-1.875)
    assert hw.corridor("hw_0", 1000.0) == pytest.approx((-9.375, 1.875))      # median: solid


def test_lane_at_and_drivable():
    net = build_highway(merge={"s": 200.0, "length": 300.0})
    loc = net.lane_at(300.0, -3.75 * 3.5)
    assert loc.lane_id == "merge" and abs(loc.d) < 1e-6
    assert net.drivable([100.0, 100.0], [-1.0, 20.0]).tolist() == [True, False]
