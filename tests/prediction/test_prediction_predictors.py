import numpy as np
import pytest

from vdsim.framework import RunContext, create_component
from vdsim.framework.types import ObjectList, ObjectState, WorldState
from vdsim.prediction import ca_motion
from vdsim.world.road_builders import build_highway


def _predict(spec, objs, t0=2.0, road=None):
    comp = create_component(spec)
    comp.reset(RunContext(road=road))
    return comp.step(t0, {"objects": ObjectList(t=t0, objects=objs), "world": WorldState(t=t0, road=road)})["prediction"]


def test_ca_exact_and_clamped():
    tau = np.linspace(0, 6, 61)
    s, v = ca_motion(10.0, 20.0, 1.0, tau)
    assert np.allclose(s, 10 + 20 * tau + 0.5 * tau ** 2) and np.allclose(v, 20 + tau)
    s, v = ca_motion(0.0, 10.0, -4.0, tau)                      # stops after 2.5 s at 12.5 m
    assert np.allclose(s[tau >= 2.5], 12.5) and np.all(v >= 0) and v[-1] == 0.0


def test_ca_frenet_along_lane():
    road = build_highway(2000.0, 2)
    lane = road.lanes["hw_1"]
    x, y, th = lane.pose(100.0)
    obj = ObjectState(id=7, x=x, y=y, psi=th, v=20.0, a=1.0, lane_id="hw_1", s=100.0, d=0.0)
    pr = _predict("predictor/constant_acceleration", [obj], road=road).by_id(7)
    tau = pr.t - pr.t[0]
    assert pr.t[0] == pytest.approx(2.0) and pr.t[-1] == pytest.approx(8.0) and len(pr.t) == 61
    assert np.allclose(pr.s, 100 + 20 * tau + 0.5 * tau ** 2) and np.allclose(pr.s_dot, 20 + tau)
    assert pr.lane_id == "hw_1" and np.allclose(pr.x, x + pr.s - 100.0)
    braking = ObjectState(id=8, x=x, y=y, psi=th, v=6.0, a=-3.0, lane_id="hw_1", s=100.0, d=0.0)
    pr = _predict("predictor/constant_acceleration", [braking], road=road).by_id(8)
    assert np.allclose(pr.s[-10:], 106.0) and pr.s_dot[-1] == 0.0


def test_cv_and_lane_following():
    obj = ObjectState(id=1, x=0.0, y=0.0, psi=np.pi / 2, v=1.5, type="pedestrian")
    pr = _predict("predictor/constant_velocity", [obj]).by_id(1)
    assert np.allclose(pr.y, 1.5 * (pr.t - 2.0)) and np.allclose(pr.x, 0.0)
    road = build_highway(2000.0, 2)
    lane = road.lanes["hw_1"]
    x, y, th = lane.pose(100.0, 2.0)
    cutin = ObjectState(id=2, x=x, y=y, psi=th - 0.05, v=20.0, lane_id="hw_1", s=100.0, d=2.0)
    pr = _predict("predictor/lane_following", [cutin], road=road).by_id(2)
    d_end = lane.center.project(pr.x[-1], pr.y[-1])[1]
    assert abs(d_end) < 0.3                                         # converges to the lane center
