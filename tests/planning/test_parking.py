"""Parking planner: Reeds-Shepp geometry, steering configurations, planning and closed loop."""

import math
import random

import numpy as np
import pytest

from vdsim.core.parameters import load_vehicle_preset
from vdsim.planning.parking import (
    DriveSettings,
    Footprint,
    ParkingPlanner,
    PlannerSettings,
    all_paths,
    build_scenario,
    center_to_reference,
    park,
    sample,
    shortest_path,
    steering_geometry,
)
from vdsim.planning.parking.tracking import _traction_limit


@pytest.fixture(scope="module")
def sedan():
    return load_vehicle_preset("mid_size_sedan")


# ----------------------------------------------------------------------------- Reeds-Shepp
def test_every_reeds_shepp_word_reaches_the_goal():
    rng = random.Random(4)
    words = set()
    for _ in range(600):
        s = (rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(-math.pi, math.pi))
        g = (rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(-math.pi, math.pi))
        r = rng.uniform(2, 7)
        paths = all_paths(s, g, r)
        assert paths
        for p in paths:
            words.add(p.types)
            m = sample(p, s, 0.1)
            assert math.hypot(m["x"][-1] - g[0], m["y"][-1] - g[1]) < 1e-6
            assert abs((m["theta"][-1] - g[2] + math.pi) % (2 * math.pi) - math.pi) < 1e-6
            # the path respects the turning radius
            assert np.all(np.abs(m["kappa"]) <= 1 / r + 1e-12)
    assert len(words) == 18          # all base words of the five families occur


def test_reeds_shepp_known_cases():
    assert shortest_path((0, 0, 0), (10, 0, 0), 5).word() == "S+"
    assert shortest_path((0, 0, 0), (-10, 0, 0), 5).word() == "S-"
    # a quarter turn left needs exactly one arc of length R pi/2
    p = shortest_path((0, 0, 0), (5, 5, math.pi / 2), 5)
    assert p.word() == "L+" and p.length == pytest.approx(5 * math.pi / 2)


# ----------------------------------------------------------------------------- steering geometry
@pytest.mark.parametrize("mode", ["front", "rear", "counter", "in_phase"])
def test_reference_point_is_the_instantaneous_center_foot(sedan, mode):
    g = steering_geometry(sedan, mode)
    kappa = 0.8 * g.max_curvature
    df, dr = g.angles(kappa)
    # intersection of the wheel normals (ICR)
    a = np.array([[-math.sin(df), math.sin(dr)], [math.cos(df), -math.cos(dr)]])
    t = np.linalg.solve(a, np.array([g.x_rear - g.x_front, 0.0]))
    x_c, y_c = g.x_front - t[0] * math.sin(df), t[0] * math.cos(df)
    assert x_c == pytest.approx(g.x_ref, abs=1e-9)
    assert 1 / y_c == pytest.approx(kappa, rel=1e-9)


def test_turning_radius_order(sedan):
    r = {m: steering_geometry(sedan, m).min_radius for m in ("front", "rear", "counter", "in_phase")}
    assert r["counter"] < r["front"] < r["in_phase"]
    assert r["rear"] == pytest.approx(r["front"])          # same angle limit, mirrored geometry
    assert steering_geometry(sedan, "front").x_ref == pytest.approx(-sedan.vehicle.cg_to_rear)
    assert steering_geometry(sedan, "rear").x_ref == pytest.approx(sedan.vehicle.cg_to_front)


def test_invalid_inputs(sedan):
    with pytest.raises(ValueError):
        steering_geometry(sedan, "diagonal")
    with pytest.raises(ValueError):
        steering_geometry(sedan, "counter", ratio=0.5)
    with pytest.raises(ValueError):
        build_scenario("diagonal")


# ----------------------------------------------------------------------------- planning
def _plan(sedan, kind, entry, mode, **kw):
    g = steering_geometry(sedan, mode)
    fp = Footprint.from_vehicle(sedan, g)
    sc = build_scenario(kind, entry, **kw)
    pl = ParkingPlanner(g, fp, sc.polygons, sc.bounds, PlannerSettings(time_limit=20.0))
    goal = center_to_reference(sc.goal, fp)
    res = pl.plan(center_to_reference(sc.start, fp), goal, sc.final_direction)
    return g, fp, sc, pl, goal, res


@pytest.mark.parametrize("kind,entry,mode", [
    ("perpendicular", "reverse", "front"),
    ("perpendicular", "forward", "rear"),
    ("angled", "forward", "counter"),
    ("parallel", "forward", "rear"),
])
def test_plans_are_exact_collision_free_and_drivable(sedan, kind, entry, mode):
    g, fp, sc, pl, goal, res = _plan(sedan, kind, entry, mode)
    assert res.success, res.message
    # ends exactly in the goal pose, with the required final direction
    assert math.hypot(res.x[-1] - goal[0], res.y[-1] - goal[1]) < 1e-6
    assert abs((res.theta[-1] - goal[2] + math.pi) % (2 * math.pi) - math.pi) < 1e-6
    assert res.segments[-1]["direction"] == sc.final_direction
    # keeps the margin (outline sampling: at least ~0.87 of it) and the planning curvature
    assert pl.check.min_clearance(res.x, res.y, res.theta).min() >= 0.12
    assert np.all(np.abs(res.kappa) <= g.max_curvature + 1e-9)
    # the segment bookkeeping covers the path
    assert res.segments[0]["start"] == 0 and res.segments[-1]["end"] == len(res.x) - 1


def test_tight_parallel_spot_needs_several_moves(sedan):
    _, _, sc, _, _, res = _plan(sedan, "parallel", "reverse", "rear")
    assert sc.info["gap_length"] == pytest.approx(6.2)       # vehicle length + 1.4 m
    assert res.success and res.cusps >= 2


def test_spot_too_small_is_reported(sedan):
    g = steering_geometry(sedan, "front")
    fp = Footprint.from_vehicle(sedan, g)
    sc = build_scenario("parallel", "reverse", gap_length=4.0)        # shorter than the car
    pl = ParkingPlanner(g, fp, sc.polygons, sc.bounds, PlannerSettings(time_limit=3.0))
    res = pl.plan(center_to_reference(sc.start, fp), center_to_reference(sc.goal, fp), -1)
    assert not res.success and "collides" in res.message


def test_left_side_mirrors_right_side(sedan):
    right = build_scenario("perpendicular", "reverse", "right")
    left = build_scenario("perpendicular", "reverse", "left")
    assert left.goal == pytest.approx((right.goal[0], -right.goal[1], -right.goal[2]))


# ----------------------------------------------------------------------------- closed loop
def test_closed_loop_reaches_the_spot(sedan):
    out = park(sedan, "perpendicular", "reverse", steering="front", layout="fwd")
    assert out.path.success and out.driven.success
    k = out.driven.kpis
    assert k["final_position_error"] < 0.15 and k["final_heading_error_deg"] < 3.0
    assert k["max_lateral_error"] < 0.15 and k["min_clearance"] > 0.0
    assert k["gear_changes"] == out.path.cusps


@pytest.mark.parametrize("mode", ["rear", "counter"])
def test_closed_loop_other_steering_modes(sedan, mode):
    out = park(sedan, "angled", "forward", steering=mode)
    assert out.driven.success
    assert out.driven.kpis["final_position_error"] < 0.15
    if mode == "rear":
        assert out.driven.kpis["max_front_angle_deg"] == 0.0 and out.driven.kpis["max_rear_angle_deg"] > 0


def test_drive_layout_decides_traction_uphill_on_snow(sedan):
    g = steering_geometry(sedan, "front")
    # uphill along the heading: load moves to the rear axle
    fwd = _traction_limit(sedan, g, DriveSettings(layout="fwd", mu=0.2, slope=0.1), 0.0, 1, 0.0)
    rwd = _traction_limit(sedan, g, DriveSettings(layout="rwd", mu=0.2, slope=0.1), 0.0, 1, 0.0)
    awd = _traction_limit(sedan, g, DriveSettings(layout="awd", mu=0.2, slope=0.1), 0.0, 1, 0.0)
    m, grav = sedan.vehicle.mass, 9.81
    need = m * grav * (math.sin(math.atan(0.1)) + 0.015)          # slope + rolling resistance
    assert max(fwd, rwd) < need < awd
    # uphill the load moves to the rear axle: rwd gains, fwd loses compared with the flat road
    flat = DriveSettings(mu=0.2, slope=0.0)
    flat.layout = "rwd"
    assert rwd > _traction_limit(sedan, g, flat, 0.0, 1, 0.0)
    flat.layout = "fwd"
    assert fwd < _traction_limit(sedan, g, flat, 0.0, 1, 0.0)
    out = park(sedan, "perpendicular", "reverse", steering="front", layout="fwd",
               drive_settings=DriveSettings(mu=0.2, slope=0.1))
    assert not out.driven.success and "traction" in out.driven.message
    out = park(sedan, "perpendicular", "reverse", steering="front", layout="awd",
               drive_settings=DriveSettings(mu=0.2, slope=0.1))
    assert out.driven.success


@pytest.mark.slow
@pytest.mark.parametrize("kind,entry,mode", [
    ("parallel", "reverse", "front"), ("parallel", "reverse", "counter"), ("parallel", "forward", "front"),
    ("perpendicular", "forward", "front"), ("perpendicular", "reverse", "rear"), ("angled", "reverse", "front"),
    ("angled", "reverse", "counter"), ("parallel", "reverse", "in_phase"),
])
def test_matrix_plans_and_drives(sedan, kind, entry, mode):
    out = park(sedan, kind, entry, steering=mode, planner_settings=PlannerSettings(time_limit=30.0))
    assert out.path.success, out.path.message
    assert out.driven.success and out.driven.kpis["final_position_error"] < 0.2
