"""Bumpless controller switching (Werling 4.4), re-initialization trigger and motion prediction (4.5), robustness."""

import math

import numpy as np
import pytest

from vdsim.framework.types import ControllerStatus
from vdsim.stabilization.reinit import ReinitMonitor, elliptic_measure, predict_motion
from vdsim.stabilization.simulate import run_closed_loop
from vdsim.stabilization.switching import select_controller
from vdsim.stabilization.trajectories import (SpeedProfile, build_trajectory, path_from_curvature,
                                              path_from_lateral_offset, replan_from_prediction,
                                              transform_rear_to_point)


def test_select_controller_regimes():
    assert select_controller("rear_axle", -1, 2.0) == "orientation"
    assert select_controller("rear_axle", -1, 0.0) == "orientation"      # v_d = 0: varsigma decides
    assert select_controller("rear_axle", 1, 0.0) == "center"
    assert select_controller("rear_axle", 1, 2.5) == "center"
    assert select_controller("cog", 1, 10.0) == "dynamic"
    assert select_controller("cog", 1, 0.5) == "center"                  # fallback below v_min_dynamic


def test_switching_rear_axle_to_cog_without_jumps(sedan):
    lh = sedan.vehicle.cg_to_rear
    rear = build_trajectory(path_from_curvature(lambda s: 0.02 * math.sin(s / 15.0), 300),
                            SpeedProfile([(0, 0), (8, 6), (14, 6), (20, 1.0), (24, 1.0)]))
    cog = transform_rear_to_point(rear, lh)       # same kinematic motion for the CoG

    def planner(t, ego, status, traj):            # regime by the planned speed, v_s = 3 m/s
        return cog if rear.sample(t).v > 3.0 else rear
    p0 = rear.sample(0)
    ego0 = dict(x=p0.x + lh, y=p0.y, psi=p0.psi, v=0.0, delta=math.atan(sedan.vehicle.wheelbase * p0.kappa))
    log, comps = run_closed_loop("werling_bilevel", rear, sedan, duration=23.0, provider=planner, ego_initial=ego0)
    act = log["active"]
    idx = [i for i in range(1, len(act)) if act[i] != act[i - 1]]
    assert [act[i] for i in idx] == ["werling_dynamic", "werling_kinematic_center"]
    typical_dF = np.percentile(np.abs(np.diff(log["force_cmd"])), 99)
    for i in idx:
        assert abs(log["force_cmd"][i] - log["force_cmd"][i - 1]) < max(50.0, 2 * typical_dF)
        assert abs(log["steer_rate_cmd"][i] - log["steer_rate_cmd"][i - 1]) < 0.03
    assert np.max(np.abs(np.diff(log["delta"]))) < 0.003
    assert np.max(np.abs(log["e_n"])) < 0.03


def test_elliptic_measure_and_monitor():
    assert elliptic_measure(0.5, 0.0, 1.0, 0.5) == pytest.approx(0.25)
    assert elliptic_measure(0.0, 0.5, 1.0, 0.5) == pytest.approx(1.0)
    mon = ReinitMonitor(c_t=1.0, c_n=0.5, e_n_max=0.8, cooldown=0.3, max_hold=0.5)
    st = ControllerStatus(e_t_dot=0.3, e_n_dot=0.2)
    assert not mon.update(0.0, st)
    assert mon.update(0.1, ControllerStatus(e_n_dot=0.6))               # error rate (4.5.1)
    assert mon.update(0.2, ControllerStatus())                          # held until answered
    assert not mon.update(0.7, ControllerStatus())                      # max_hold elapsed
    assert not mon.update(0.8, ControllerStatus(e_n=1.0))               # cool-down
    assert mon.update(1.1, ControllerStatus(e_n=1.0)) and mon.reason == "e_n"   # absolute threshold e_max


def test_prediction_taylor_series_matches_exact_arc():
    v0, a, w, dt = 20.0, 1.0, 0.3, 0.3
    x, y, th, v = predict_motion(1.0, 2.0, 0.5, v0, w, a, dt)
    # exact solution for constant theta_dot and v_dot (numerical quadrature)
    tau = np.linspace(0, dt, 20001)
    vv, thth = v0 + a * tau, 0.5 + w * tau
    xe = 1.0 + np.trapezoid(vv * np.cos(thth), tau)
    ye = 2.0 + np.trapezoid(vv * np.sin(thth), tau)
    assert math.hypot(x - xe, y - ye) < 1e-4 and th == pytest.approx(0.5 + w * dt) and v == pytest.approx(v0 + a * dt)


def _gust_run(sedan, replan, fy=6000.0):
    traj = build_trajectory(path_from_curvature(lambda s: 0.0, 400), SpeedProfile([(0, 30), (12, 30)]),
                            reference_point="cog")

    def planner(t, ego, status, tr):
        if replan and status is not None and status.reinit_request and \
                not (tr.reinitialized and tr.metadata.get("replanned_at", -1) >= status.prediction["t"] - 0.2):
            return replan_from_prediction(tr, status.prediction)
        return tr
    return run_closed_loop("werling_bilevel", traj, sedan, duration=6.0, provider=planner,
                           ego_initial=dict(x=0.0, y=0.0, psi=0.0, v=30.0),
                           plant_params={"disturbances": [{"t": 2.0, "duration": 0.3, "fy": fy, "mz": 2000.0}]})


def test_reinitialization_on_side_wind_gust(sedan):
    log, comps = _gust_run(sedan, replan=True)
    events = comps["controller"].monitor.events
    assert events and 2.0 < events[0][0] < 2.4
    assert np.all(log["reinit"][log["t"] < 2.0] == 0)
    log_ll, comps_ll = _gust_run(sedan, replan=False)
    # with re-initialization the low-level errors stay small (the planner takes over the impulse)
    after = log["t"] > events[0][0] + 0.3
    assert np.max(np.abs(log["e_n"][after])) < 0.5 * np.max(np.abs(log_ll["e_n"][after]))
    # no permanent disturbance: re-initialization does not repeat endlessly
    assert len(events) <= 3


def test_reinitialization_on_lateral_impulse(sedan):
    traj = build_trajectory(path_from_curvature(lambda s: 0.0, 300), SpeedProfile([(0, 20), (8, 20)]),
                            reference_point="cog")

    def kick(t, comps):
        if abs(t - 1.5) < 1e-9:
            comps["plant"].kick(vy=0.8)
    log, comps = run_closed_loop("werling_bilevel", traj, sedan, duration=2.0, on_step=kick,
                                 ego_initial=dict(x=0.0, y=0.0, psi=0.0, v=20.0))
    assert comps["controller"].monitor.events and comps["controller"].monitor.events[0][0] == pytest.approx(1.5,
                                                                                                         abs=0.02)


@pytest.mark.parametrize("ref,v", [("cog", 25.0), ("rear_axle", 2.0)])
def test_prediction_accuracy(sedan, ref, v):
    R = 120.0 if ref == "cog" else 15.0
    path = path_from_curvature(lambda s: 1.0 / R, 400)
    traj = build_trajectory(path, SpeedProfile([(0, v), (12, v)]), reference_point=ref)
    p0 = traj.sample(0)
    lh = sedan.vehicle.cg_to_rear
    ego0 = dict(x=p0.x, y=p0.y, psi=p0.theta, v=v) if ref == "cog" else \
        dict(x=p0.x + lh, y=p0.y, psi=p0.psi, v=v, delta=math.atan(sedan.vehicle.wheelbase / R))
    log, comps = run_closed_loop("werling_bilevel", traj, sedan, duration=6.0, ego_initial=ego0,
                                 controller_params={"prediction_dt": 0.3})
    k = int(4.0 / 0.01)
    pred = log["status"][k].prediction
    k2 = k + 30
    if ref == "cog":
        x_true, y_true = log["x"][k2], log["y"][k2]
    else:
        x_true = log["x"][k2] - lh * math.cos(log["psi"][k2])
        y_true = log["y"][k2] - lh * math.sin(log["psi"][k2])
    assert pred["t"] == pytest.approx(log["t"][k2])
    assert math.hypot(pred["x"] - x_true, pred["y"] - y_true) < 0.02
    assert pred["v"] == pytest.approx(math.hypot(log["vx"][k2], log["vy"][k2]), abs=0.05)
    assert pred["reference_point"] == ref


def test_robustness_double_track_plant(sedan):
    # model error: Werling controller designed on the DESM, plant = vdsim double-track model
    path = path_from_lateral_offset([(30, 45, 3.5), (100, 45, -3.5)], 200)
    traj = build_trajectory(path, SpeedProfile([(0, 20), (8, 20)]), reference_point="cog")
    p0 = traj.sample(0)
    log, comps = run_closed_loop("werling_bilevel", traj, sedan, duration=7.0, plant="double_track",
                                 ego_initial=dict(x=p0.x, y=p0.y, psi=0.0, v=20.0))
    assert np.all(np.isfinite(log["x"]))
    assert np.max(np.abs(log["e_n"])) < 0.2 and np.max(np.abs(log["e_t"])) < 0.3
