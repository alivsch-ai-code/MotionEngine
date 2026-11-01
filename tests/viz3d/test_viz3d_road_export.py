"""Tests für den OpenDRIVE-Export und die HIL-Signale (ohne CARLA-Server)."""

import struct
import xml.etree.ElementTree as ET

import numpy as np

from vdsim.framework.types import ActuatorCommand, ControlCommand
from vdsim.viz3d.hil import control_to_can, ego_from_can, generate_dbc
from vdsim.viz3d.road_export import road_to_opendrive, suggest_carla_map


def _simple_road():
    from vdsim.world.road_builders import build_highway
    return build_highway(500.0, 2)


def test_opendrive_export_is_valid_xml():
    road = _simple_road()
    xodr = road_to_opendrive(road, ds=5.0)
    root = ET.fromstring(xodr)
    assert root.tag == "OpenDRIVE"
    assert root.find("header") is not None
    roads = root.findall("road")
    assert len(roads) >= 1
    for r in roads:
        pv = r.find("planView")
        assert pv is not None
        geos = pv.findall("geometry")
        assert len(geos) >= 1
        for g in geos:
            assert float(g.get("length")) > 0


def test_suggest_carla_map():
    road = _simple_road()
    assert suggest_carla_map(road) == "Town04"
    from vdsim.world.road_builders import build_rural_road
    rural = build_rural_road(500.0)
    assert suggest_carla_map(rural) in ("Town07", "Town04")


def test_control_to_can_roundtrip():
    cmd = ControlCommand(steer_angle=0.15, steer_rate=0.02, accel=1.5, direction=1)
    msgs = control_to_can(cmd)
    assert 0x100 in msgs
    assert len(msgs[0x100]) == 8
    d = msgs[0x100]
    steer = struct.unpack_from("<h", d, 0)[0] * 0.001
    assert abs(steer - 0.15) < 0.002


def test_actuator_to_can():
    cmd = ActuatorCommand(drive_torque=np.array([100, 100, 200, 200]),
                          brake_torque=np.array([0, 0, 50, 50]))
    msgs = control_to_can(cmd)
    assert 0x101 in msgs and 0x102 in msgs


def test_ego_from_can():
    msgs = {
        0x200: struct.pack("<ii", 12345, -67890),
        0x201: struct.pack("<hhhh", 31416, 2500, 100, 500),
    }
    ego = ego_from_can(msgs)
    assert abs(ego.x - 12.345) < 0.01
    assert abs(ego.psi - 3.1416) < 0.001
    assert abs(ego.vx - 25.0) < 0.1


def test_generate_dbc(tmp_path):
    path = tmp_path / "test.dbc"
    generate_dbc(str(path))
    text = path.read_text(encoding="utf-8")
    assert "BO_ 256" in text or "BO_ 0x100" in text.replace("256", "0x100")
    assert "steer_angle" in text
    assert "vdsim" in text


def test_sensor_presets_defined():
    from vdsim.viz3d.sensors import PRESETS
    assert "camera_front" in PRESETS
    assert "lidar_top" in PRESETS
    assert "radar_front" in PRESETS
    for name, spec in PRESETS.items():
        assert spec.type.startswith("sensor.")
        assert spec.fps > 0
