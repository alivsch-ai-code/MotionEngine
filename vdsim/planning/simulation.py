"""Minimal closed loop for planner tests and examples (ideal trajectory tracking).

The vehicle state equals the desired trajectory state at the next planning instant (perfect
low-level stabilization), optionally disturbed by a callback. Controllers are developed in
vdsim.stabilization; this loop only serves to exercise the planner (Werling 2011, Abb. 3.6-3.8).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..framework.types import EgoState, PredictedObject, Prediction


def ego_from_point(point, geometry, reference_point, t=None):
    # TrajectoryPoint of the reference point -> EgoState at the CoG (zero side slip at the reference point)
    psi = point.psi
    x, y = point.x, point.y
    if reference_point == "rear_axle":
        x, y = x + geometry.cg_to_rear * np.cos(psi), y + geometry.cg_to_rear * np.sin(psi)
    v = point.v_signed
    return EgoState(t=point.t if t is None else t, x=float(x), y=float(y), psi=float(psi), vx=float(v),
                    r=float(point.v * point.kappa), ax=float(point.a_signed), ay=float(point.v ** 2 * point.kappa),
                    delta=float(np.arctan(geometry.wheelbase * point.kappa)), gear=int(point.direction))


def constant_velocity_object(obj_id, x0, y0, psi, v, t0=0.0, horizon=8.0, dt=0.1, length=4.5, width=1.8,
                             obj_type="car", a=0.0):
    # predicted object with constant acceleration along a straight line (speed clamped at 0)
    t = t0 + np.arange(0.0, horizon + 1e-9, dt)
    tr = t - t0
    if a < 0 and v > 0:
        tr_c = np.minimum(tr, v / -a)
    else:
        tr_c = tr
    dist = v * tr_c + 0.5 * a * tr_c ** 2
    speed = np.maximum(v + a * tr_c, 0.0)
    return PredictedObject(id=obj_id, type=obj_type, length=length, width=width, t=t, x=x0 + dist * np.cos(psi),
                           y=y0 + dist * np.sin(psi), psi=np.full_like(t, psi), v=speed)


@dataclass
class ClosedLoopLog:
    t: list = field(default_factory=list)
    ego: list = field(default_factory=list)
    trajectories: list = field(default_factory=list)
    debug: list = field(default_factory=list)

    def array(self, name):
        return np.array([getattr(e, name) for e in self.ego])


def run_closed_loop(planner, behavior_fn, ego0, t_end, prediction_fn=None, disturbance=None, period=None,
                    keep_trajectories=True):
    # behavior_fn(t, ego) -> BehaviorCommand; prediction_fn(t) -> Prediction; disturbance(t, ego) -> EgoState
    if planner.context is None:
        planner.reset(None)
    period = period or planner.PERIOD or 0.1
    log = ClosedLoopLog()
    ego, t = ego0, float(ego0.t)
    n = int(round((t_end - t) / period))
    for _ in range(n + 1):
        pred = prediction_fn(t) if prediction_fn is not None else Prediction(t0=t)
        traj, dbg = planner.plan_cycle(t, ego, behavior_fn(t, ego), pred)
        log.t.append(t)
        log.ego.append(ego)
        if keep_trajectories:
            log.trajectories.append(traj)
        log.debug.append(dbg)
        t = t + period
        ego = ego_from_point(traj.sample(t), planner.geometry, traj.reference_point, t)
        if disturbance is not None:
            ego = disturbance(t, ego) or ego
    return log
