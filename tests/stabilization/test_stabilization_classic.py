"""Classical trajectory tracking controllers on the DESM chain (comparison controllers)."""

import numpy as np
import pytest

from vdsim.framework.plugins import create_component
from vdsim.stabilization.simulate import run_closed_loop
from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_lateral_offset


@pytest.fixture(scope="module")
def lane_change():
    path = path_from_lateral_offset([(40, 50, 3.5), (120, 50, -3.5)], 300)
    return build_trajectory(path, SpeedProfile([(0, 15), (3, 15), (8, 20), (12, 20)]), reference_point="cog")


def _run(spec, traj, sedan, params=None, duration=11.0):
    p0 = traj.sample(0)
    return run_closed_loop(spec, traj, sedan, duration=duration, controller_params=params,
                           ego_initial=dict(x=p0.x, y=p0.y + 0.3, psi=p0.theta, v=15.0))


@pytest.mark.parametrize("spec,limit", [("pure_pursuit", 0.6), ("stanley", 0.2), ("lqr", 0.15), ("mpc", 0.2)])
def test_lateral_controllers_follow_trajectory(sedan, lane_change, spec, limit):
    log, comps = _run(spec, lane_change, sedan)
    late = log["t"] > 3.0
    assert np.all(np.isfinite(log["x"]))
    assert np.max(np.abs(log["e_n"][late])) < limit
    assert np.max(np.abs(log["e_t"][late])) < 0.3 and np.max(np.abs(log["e_v"][late])) < 0.3
    assert abs(log["e_n"][-1]) < 0.5 * limit         # converging after the maneuver


def test_mpc_horizon_and_constraints(sedan, lane_change):
    log, comps = _run("mpc", lane_change, sedan, params={"max_rate": 0.25})
    st = log["status"][500]
    assert st.horizon_x is not None and len(st.horizon_x) == comps["controller"].params.horizon
    assert np.all(np.isfinite(st.horizon_y))
    rates = np.abs(np.diff(log["steer_angle_cmd"])) / 0.01
    assert np.max(rates) <= 0.25 * 1.02


@pytest.mark.parametrize("longitudinal", ["pid", "pi", "ff_fb", "speed_pi"])
def test_longitudinal_controllers_in_composite(sedan, lane_change, longitudinal):
    log, comps = _run("composite", lane_change, sedan, {"lateral": "stanley", "longitudinal": longitudinal})
    late = log["t"] > 3.0
    assert np.max(np.abs(log["e_n"][late])) < 0.25
    ev = np.abs(log["e_v"][late])
    assert np.max(ev) < 2.0 and ev[-1] < 0.5 and ev[-1] < max(0.05, 0.5 * np.max(ev))    # PI(D) without feedforward: overshoot decays
    assert log["active"][-1] == f"stanley+{longitudinal}"
    if longitudinal in ("ff_fb", "speed_pi"):
        assert np.max(np.abs(log["e_v"][late])) < 0.3


def test_acc_keeps_time_gap(sedan):
    traj = build_trajectory(path_from_lateral_offset([], 600), SpeedProfile([(0, 25), (30, 25)]), reference_point="cog")
    params = {"lateral": "lqr", "longitudinal": "acc",
              "longitudinal_params": {"lead_gap0": 60.0, "lead_speed": 18.0, "time_gap": 1.8, "standstill_gap": 5.0}}
    log, comps = run_closed_loop("composite", traj, sedan, duration=25.0, controller_params=params,
                                 ego_initial=dict(x=0.0, y=0.0, psi=0.0, v=25.0))
    acc = comps["controller"].lon
    gap, v = acc.signals["gap"], log["vx"][-1]
    assert v == pytest.approx(18.0, abs=0.3)
    assert gap == pytest.approx(5.0 + 1.8 * v, abs=1.5)


def test_classic_components_have_docs():
    for name in ("pure_pursuit", "stanley", "lqr", "mpc", "pid", "pi", "ff_fb", "acc", "speed_pi", "composite"):
        c = create_component(f"tracking_controller/{name}")
        assert c.LABEL and c.DOC.summary and c.DOC.references and c.DOC.expert
        assert set(c.output_ports()) == {"command", "status"}
