"""The planner must not emit a trajectory from a singular Frenet start state (vehicle sliding off its lane)."""

import numpy as np

from vdsim.framework import RunContext
from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode
from vdsim.geometry import ReferenceLine
from vdsim.planning import create_planner


def _planner():
    planner = create_planner("default")
    planner.reset(RunContext())
    return planner


def _behavior(ref, v=10.0):
    return BehaviorCommand(reference_line=ref, target_speed=v, d_min=-3.0, d_max=3.0, modes=[LongitudinalMode("velocity", {"v_ref": v})])


def test_emergency_stop_near_the_center_of_curvature():
    ref = ReferenceLine.circle(17.0)                       # roundabout: counter-clockwise, center (0, 0)
    planner = _planner()
    # the vehicle has slid 16 m to the inside: 1 - kappa d is almost 0
    ego = EgoState(x=0.0, y=-1.0, psi=0.0, vx=9.0)
    traj, debug = planner.plan_cycle(0.0, ego, _behavior(ref))
    assert not traj.valid and debug.fallback and debug.mode == "emergency" and "emergency" in debug.info
    assert np.all(np.isfinite(traj.x)) and np.all(np.isfinite(traj.v))
    assert traj.v[0] <= 9.0 + 1e-6 and traj.v[-1] == 0.0 and np.all(np.diff(traj.v) <= 1e-9)   # braking to standstill
    assert np.allclose(traj.theta, 0.0) and np.all(traj.kappa == 0.0)                           # straight ahead
    stop_distance = traj.x[-1] - traj.x[0]
    assert 0.0 < stop_distance < 9.0**2 / (2 * 6.0) + 1.0
    assert planner.plan is None                            # the next cycle starts again from the vehicle state


def test_emergency_stop_when_the_vehicle_is_across_the_lane():
    ref = ReferenceLine.straight(300.0)
    planner = _planner()
    traj, debug = planner.plan_cycle(0.0, EgoState(x=50.0, y=0.5, psi=np.radians(86.0), vx=12.0), _behavior(ref, 12.0))
    assert not traj.valid and debug.mode == "emergency" and float(np.max(np.abs(traj.v))) <= 12.0 + 1e-6


def test_normal_states_are_planned_and_recovery_works():
    ref = ReferenceLine.circle(17.0)
    planner = _planner()
    # 1 m inside the lane, heading along it: an ordinary state
    x, y = ref.point(10.0, 1.0)
    ego = EgoState(x=float(x), y=float(y), psi=float(ref.evaluate(10.0)[2]), vx=6.0)
    traj, debug = planner.plan_cycle(0.0, ego, _behavior(ref, 6.0))
    assert debug.mode != "emergency" and float(np.max(traj.v)) < 12.0
    # after an emergency cycle the planner plans again from a valid state
    # (the controller reports the large deviation, so the planner starts from the measured state)
    slide = _behavior(ref)
    slide.reinit = True
    _, debug = planner.plan_cycle(0.1, EgoState(x=0.0, y=-1.0, psi=0.0, vx=9.0), slide)
    assert debug.mode == "emergency"
    traj, debug = planner.plan_cycle(0.2, ego, _behavior(ref, 6.0))
    assert debug.mode != "emergency" and traj.reinitialized and traj.valid
