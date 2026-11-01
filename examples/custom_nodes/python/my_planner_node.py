"""Custom node (Python): simple lane-keeping trajectory planner with the ports of TrajectoryPlannerBase.

Graph spec: "python:examples/custom_nodes/python/my_planner_node.py:LaneKeepingPlanner"

    inputs:  ego (EgoState), behavior (BehaviorCommand), prediction (Prediction),
             status (ControllerStatus, feedback port: value of the previous step)
    outputs: trajectory (PlannedTrajectory, absolute time), debug (PlannerDebug)

One candidate only (no optimization): the lateral offset d moves from the current value to
d_ref with a quintic smoothstep (zero lateral velocity/acceleration at both ends) and the
speed approaches the target speed exponentially. The trajectory follows the reference line
of the behavior command (straight line along the ego heading if there is none).
"""

import math
from dataclasses import dataclass

import numpy as np

from vdsim.core.parameters import param
from vdsim.framework.knowledge import ComponentDoc
from vdsim.framework.layers import TrajectoryPlannerBase
from vdsim.framework.types import PlannedTrajectory, PlannerDebug
from vdsim.geometry import ReferenceLine


@dataclass
class LaneKeepingParams:
    horizon: float = param(5.0, "s", "Planungshorizont", min=0.5)
    dt: float = param(0.1, "s", "Zeitraster", min=0.01)
    t_lateral: float = param(3.0, "s", "Dauer Querüberführung", min=0.2)
    tau_speed: float = param(2.0, "s", "Zeitkonstante Geschwindigkeit", min=0.1)
    default_speed: float = param(10.0, "m/s", "Zielgeschwindigkeit ohne Vorgabe", min=0.0)


class LaneKeepingPlanner(TrajectoryPlannerBase):
    NAME = "my_lane_keeping"
    VERSION = "1.0.0"
    LABEL = "Spurhalte-Planer (Beispiel, Python)"
    PARAMS = LaneKeepingParams
    DOC = ComponentDoc(summary="Einfacher Spurhalte-Planer: ein Kandidat mit quintischer Querüberführung.",
                       purpose="Beispiel für einen Custom Node mit den Ports der Ebene Trajectory Planning.",
                       limitations=["keine Kollisionsprüfung, keine Optimierung, keine Prädiktion"],
                       references=["werling2011"])

    def reset(self, context):
        super().reset(context)
        self.cycles = 0
        self.reinit_count = 0

    def step(self, t, inputs):
        ego, behavior, status = inputs["ego"], inputs["behavior"], inputs.get("status")
        if ego is None:
            return {}
        p = self.params
        self.cycles += 1
        if status is not None and status.reinit_request:
            self.reinit_count += 1
        line = getattr(behavior, "reference_line", None) if behavior is not None else None
        if line is None:
            line = ReferenceLine.straight(500.0, ego.x, ego.y, ego.psi)
        s0, d0 = line.project(ego.x, ego.y)
        d_ref = float(getattr(behavior, "d_ref", 0.0) or 0.0)
        v_target = float(getattr(behavior, "target_speed", 0.0) or p.default_speed)
        v0 = max(float(ego.vx), 0.0)

        tau = np.arange(0.0, p.horizon + 1e-9, p.dt)
        decay = np.exp(-tau / p.tau_speed)
        v = v_target + (v0 - v_target) * decay
        a = -(v0 - v_target) / p.tau_speed * decay
        s = s0 + v_target * tau + (v0 - v_target) * p.tau_speed * (1.0 - decay)
        u = np.clip(tau / p.t_lateral, 0.0, 1.0)
        d = d0 + (d_ref - d0) * (10 * u**3 - 15 * u**4 + 6 * u**5)
        x, y = line.point(s, d)
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        dx, dy = np.gradient(x), np.gradient(y)
        theta = np.unwrap(np.arctan2(dy, dx))
        ds = np.maximum(np.hypot(dx, dy), 1e-6)
        kappa = np.gradient(theta) / ds
        dkappa = np.gradient(kappa) / ds
        traj = PlannedTrajectory(t=t + tau, x=x, y=y, theta=theta, kappa=kappa, dkappa=dkappa, v=v, a=a, s=s, d=d,
                                 direction=1, reference_point="cog", lateral_mode="time",
                                 longitudinal_mode="velocity", cost=float(abs(d_ref - d0)), valid=True,
                                 reference_line=line)
        debug = PlannerDebug(t=t, n_candidates=1, n_checked=1, best_index=0, mode="lane_keeping",
                             start_state={"s": float(s0), "d": float(d0), "v": v0},
                             cost_terms={"lateral_offset": float(abs(d_ref - d0))},
                             info={"reinit_requests": self.reinit_count})
        self.signals.update(d0=float(d0), v_target=v_target)
        if math.isfinite(d0):
            return {"trajectory": traj, "debug": debug}
        return {"debug": debug}
