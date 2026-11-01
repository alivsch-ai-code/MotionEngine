import numpy as np
import pytest

from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
from vdsim.geometry import ReferenceLine
from vdsim.planning import WerlingPlanner
from vdsim.planning.collision import CircleCollisionChecker, CollisionSettings, circle_cover
from vdsim.planning.combination import PlanningContext, TrajectoryBatch
from vdsim.planning.kinematics import EgoGeometry
from vdsim.planning.simulation import constant_velocity_object, run_closed_loop

ROAD = ReferenceLine.straight(1000.0, ds=0.5)


def beh(v=15.0, **kw):
    kw.setdefault("d_min", -1.75)
    kw.setdefault("d_max", 5.25)
    return lambda t, e: BehaviorCommand(t=t, reference_line=ROAD, target_speed=v,
                                        modes=[LongitudinalMode("velocity", {"v_ref": v})], **kw)


def straight_batch(x0, v, t, y=0.0, direction=1):
    n = len(t)
    x = (x0 + v * (t - t[0]))[None, :]
    z = np.zeros((1, n))
    fr = {k: z for k in ("s", "s_d", "s_dd", "d", "d_d", "d_dd", "d_p", "d_pp")}
    w = {"x": x, "y": z + y, "theta": z + (0.0 if direction > 0 else np.pi), "kappa": z, "v": z + v, "a": z}
    return TrajectoryBatch(t, fr, w, ROAD, PlanningContext(direction=direction))


def test_circle_cover_contains_rectangle():
    offs, r = circle_cover(4.8, 1.85, 3)
    assert len(offs) == 3 and r == pytest.approx(np.hypot(0.8, 0.925))
    # every corner of the rectangle lies inside a circle
    for cx, cy in ((2.4, 0.925), (-2.4, -0.925)):
        assert np.min(np.hypot(cx - offs, cy)) <= r + 1e-12


def test_collision_time_and_safety_margin_ramp():
    geo = EgoGeometry()
    settings = CollisionSettings()
    settings.margin_ramp = 1.0
    t = np.arange(0.0, 3.0001, 0.1)
    obstacle = Prediction(objects=[constant_velocity_object(4, 30.0, 0.0, 0.0, 0.0, obj_type="static", length=4.0,
                                                            width=2.0, horizon=4.0)])
    chk = CircleCollisionChecker()
    chk.prepare(obstacle, t, geo, settings, PlanningContext(reference_point="cog"))
    res = chk.check(straight_batch(0.0, 10.0, t))
    assert res.collides[0] and res.object_id[0] == 4
    assert 2.0 < res.t_collision[0] < 3.0
    info = chk.geometry_info()
    assert info["margin_ramp"]["factor"][0] == 0.0 and info["margin_ramp"]["factor"][-1] == 1.0
    assert info["objects"]["4"]["margin"] == settings.margin_static
    # ramp: an obstacle closer than the margin at t = 0 is tolerated at first (Fig. 3.10)
    near = Prediction(objects=[constant_velocity_object(5, 0.0, 1.85 / 2 + 0.9 + 0.75 + 0.3, 0.0, 0.0,
                                                        obj_type="pedestrian", length=0.5, width=0.5)])
    chk.prepare(near, t, geo, settings, PlanningContext(reference_point="cog"))
    res = chk.check(straight_batch(0.0, 0.0, t))
    assert res.collides[0] and res.t_collision[0] > 0.0
    settings.margin_ramp = 0.0
    chk.prepare(near, t, geo, settings, PlanningContext(reference_point="cog"))
    assert chk.check(straight_batch(0.0, 0.0, t)).t_collision[0] == pytest.approx(0.0)


def test_dynamic_collision_with_oncoming_vehicle():
    geo = EgoGeometry()
    t = np.arange(0.0, 3.0001, 0.1)
    pred = Prediction(objects=[constant_velocity_object(8, 60.0, 0.0, np.pi, 10.0)])
    chk = CircleCollisionChecker()
    chk.prepare(pred, t, geo, CollisionSettings(), PlanningContext(reference_point="cog"))
    res = chk.check(straight_batch(0.0, 10.0, t))
    assert res.collides[0] and res.t_collision[0] == pytest.approx(2.75, abs=0.1)   # contact at 2.71 s (circles + 0.5 m)
    # other lane: free
    chk.prepare(Prediction(objects=[constant_velocity_object(8, 60.0, 3.5, np.pi, 10.0)]), t, geo,
                CollisionSettings(), PlanningContext(reference_point="cog"))
    assert not chk.check(straight_batch(0.0, 10.0, t)).collides[0]


def test_evasion_around_static_obstacle():
    planner = WerlingPlanner()
    obs = lambda t: Prediction(t0=t, objects=[constant_velocity_object(3, 60.0, 0.3, 0.0, 0.0, t0=t,  # noqa
                                                                         obj_type="static", length=4.0, width=2.0)])
    log = run_closed_loop(planner, beh(), EgoState(vx=15.0), 9.0, obs)
    x, y = log.array("x"), log.array("y")
    assert np.interp(60.0, x, y) > 2.5                  # passes the obstacle on the free left side
    assert log.array("vx").min() > 4.0                  # combined optimization: slows down and evades, no stop
    assert abs(y[-1]) < 1.5                             # and returns towards the lane center
    assert all(tr.valid for tr in log.trajectories)
    assert max(d.n_checked for d in log.debug) > 32     # the free optimum was blocked


def test_fallback_when_everything_is_blocked():
    planner = WerlingPlanner()
    wall = lambda t: Prediction(t0=t, objects=[constant_velocity_object(i, 14.0, -3.0 + 1.5 * i, np.pi / 2, 0.0, t0=t,  # noqa
                                                                          obj_type="static", length=2.0, width=2.0)
                                               for i in range(7)])
    log = run_closed_loop(planner, beh(), EgoState(vx=15.0), 0.6, wall)
    assert all(d.fallback for d in log.debug)
    assert all(not tr.valid for tr in log.trajectories)
    assert log.debug[-1].info["fallback_time"] is not None
    # the longest collision free trajectory = maximum admissible deceleration
    assert log.trajectories[-1].a[0] < -3.0
    assert log.array("vx")[-1] < 15.0 - 1.0


def test_reverse_orientation_used_for_collision():
    geo = EgoGeometry()
    t = np.arange(0.0, 1.0001, 0.1)
    # reversing towards -x with psi = theta + pi: the vehicle front points to +x
    pred = Prediction(objects=[constant_velocity_object(1, 3.2, 0.0, 0.0, 0.0, obj_type="static", length=1.0,
                                                        width=1.0)])
    chk = CircleCollisionChecker()
    settings = CollisionSettings()
    settings.margin_ramp = 0.0
    settings.margin_static = 0.0
    chk.prepare(pred, t, geo, settings, PlanningContext(reference_point="rear_axle", direction=-1))
    # rear axle at x = 0: front bumper at x = +3.8 -> touches the obstacle in front of the vehicle body
    assert chk.check(straight_batch(0.0, 0.0, t, direction=-1)).collides[0]
    chk.prepare(pred, t, geo, settings, PlanningContext(reference_point="rear_axle", direction=1))
    batch = straight_batch(0.0, 0.0, t, direction=1)
    batch.theta = batch.theta + np.pi                  # forward motion towards -x: body points to -x
    assert not chk.check(batch).collides[0]
