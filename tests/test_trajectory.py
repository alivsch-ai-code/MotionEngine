import json

import numpy as np
import pytest

from vdsim.core.registry import available
from vdsim.trajectory import (
    PathBuilder,
    Trajectory,
    Waypoint,
    WaypointEditor,
    generate,
    lap_time,
    load_trajectory,
    speed_profile,
)


def test_all_maneuvers_generate():
    for name in available("maneuver"):
        traj = generate(name)
        assert len(traj.x) > 10 and np.all(np.isfinite(traj.kappa)), name


def test_lane_change_geometry():
    traj = generate("lane_change", speed_kmh=120, width=3.5, duration=6.0)
    assert traj.y[-1] == pytest.approx(3.5, abs=0.01)
    assert abs(traj.psi[-1]) < 1e-3
    assert np.max(np.abs(traj.kappa)) * (120 / 3.6) ** 2 == pytest.approx(2 * np.pi * 3.5 / 36, rel=0.02)


def test_iso_dlc_reference_stays_inside_gates():
    traj = generate("iso_double_lane_change")
    b = traj.metadata["vehicle_width"]
    for x0, x1, center, width in traj.metadata["gates"]:
        xs = np.linspace(x0, x1, 30)
        assert np.all(np.abs(np.interp(xs, traj.x, traj.y) - center) <= (width - b) / 2)


def test_path_builder_circle_and_closed_track():
    traj = PathBuilder().turn(30.0, 360.0).build()
    assert np.hypot(traj.x[-1] - traj.x[0], traj.y[-1] - traj.y[0]) < 1e-3
    assert np.mean(1 / np.abs(traj.kappa[10:-10])) == pytest.approx(30.0, rel=1e-3)


def test_speed_profile_respects_limits():
    traj = generate("city")
    v = speed_profile(traj.s, traj.kappa, 50 / 3.6, ay_max=2.5, ax_max=1.5, ax_min=-2.5)
    assert np.all(v**2 * np.abs(traj.kappa) <= 2.5 + 1e-6)
    accel = np.diff(v**2) / (2 * np.diff(traj.s))
    assert accel.max() <= 1.5 + 1e-6 and accel.min() >= -2.5 - 1e-6
    assert lap_time(traj.s, v) > traj.length / (50 / 3.6)


def test_projection_sign_and_closed_track_start():
    traj = Trajectory(np.linspace(0, 100, 101), np.zeros(101), 10.0)
    proj = traj.project(50.0, 1.5)
    assert proj.lateral_error == pytest.approx(1.5) and proj.s == pytest.approx(50.0)
    loop = PathBuilder().turn(20.0, 360.0).build()
    # a point just behind the start of a closed loop must not jump to the end
    assert loop.project(loop.x[0] - 1.0, loop.y[0], hint=0).s < 5.0


@pytest.mark.parametrize("name,length", [("iso_doppelspurwechsel.csv", 214.9), ("kreisbahn_gps.gpx", 407.0),
                                         ("slalom_ros_path.yaml", 254.1), ("testzyklus.mat", 396.1),
                                         ("landstrasse.xodr", 423.15)])
def test_importers(samples, name, length):
    traj = load_trajectory(samples / name)
    assert traj.length == pytest.approx(length, rel=0.01)
    assert np.all(traj.v > 0)


def test_opendrive_lanes(samples):
    ref = load_trajectory(samples / "landstrasse.xodr", lane_id=0)
    right = load_trajectory(samples / "landstrasse.xodr", lane_id=-1)
    assert ref.length == pytest.approx(420.0, abs=0.05)
    assert right.length - ref.length == pytest.approx(1.75 * 1.8, abs=0.05)
    assert ref.v[0] == pytest.approx(80 / 3.6)


def test_csv_json_roundtrip(tmp_path):
    traj = generate("slalom")
    traj.save(tmp_path / "t.csv")
    traj.save(tmp_path / "t.json")
    for f in ("t.csv", "t.json"):
        loaded = load_trajectory(tmp_path / f)
        assert loaded.length == pytest.approx(traj.length, rel=1e-4)
    assert json.loads((tmp_path / "t.json").read_text())["cones"]


def test_waypoint_editor_fillet_radius():
    editor = WaypointEditor([Waypoint(0, 0, 50), Waypoint(100, 0, 50, 20.0), Waypoint(100, 100, 50)])
    traj = editor.to_trajectory(ds=0.25)
    arc = np.abs(traj.kappa) > 0.01
    assert np.median(1 / np.abs(traj.kappa[arc])) == pytest.approx(20.0, rel=0.05)
    editor.move(1, 120, 0)
    editor.undo()
    assert editor.waypoints[1].x == 100
