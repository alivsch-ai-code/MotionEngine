"""Custom node (Python): Pure-Pursuit tracking controller with the ports of TrackingControllerBase.

Graph spec: "python:examples/custom_nodes/python/my_controller_node.py:PurePursuitController"

    inputs:  ego (EgoState), trajectory (PlannedTrajectory)
    outputs: command (ControlCommand: steer_angle + accel), status (ControllerStatus)

The same algorithm is implemented natively in ../rust/my_controller_node and
../cpp/my_controller_node; tests compare the three implementations.

Algorithm (rear-axle based pure pursuit, Coulter 1992):
    lookahead  L_d = L_d0 + k_v |v_x|
    target     first trajectory point after the nearest one with distance >= L_d from the rear axle
    steering   delta = atan2(2 l sin(alpha), L_d),  alpha = angle to the target in the vehicle frame
    speed      a = a_ref(t) + k_p (v_ref(t) - v_x)
"""

import math
from dataclasses import dataclass

from vdsim.core.parameters import param
from vdsim.framework.knowledge import ComponentDoc
from vdsim.framework.layers import TrackingControllerBase
from vdsim.framework.types import ControlCommand, ControllerStatus


def wrap(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


@dataclass
class PurePursuitParams:
    lookahead_min: float = param(4.0, "m", "Mindest-Vorausschau", min=0.5)
    lookahead_gain: float = param(0.8, "s", "Vorausschau je Geschwindigkeit", min=0.0)
    wheelbase: float = param(2.8, "m", "Radstand", min=1.0)
    cg_to_rear: float = param(1.4, "m", "Schwerpunkt - Hinterachse", min=0.0)
    speed_gain: float = param(1.0, "1/s", "Geschwindigkeitsverstärkung", min=0.0)
    max_steer: float = param(0.6, "rad", "Max. Lenkwinkel", min=0.01)


class PurePursuitController(TrackingControllerBase):
    NAME = "my_pure_pursuit"
    VERSION = "1.0.0"
    LABEL = "Pure Pursuit (Beispiel, Python)"
    PARAMS = PurePursuitParams
    DOC = ComponentDoc(summary="Geometrischer Querregler (Pure Pursuit) mit P-Geschwindigkeitsregler.",
                       purpose="Beispiel für einen Custom Node mit den Ports der Ebene Vehicle Control.",
                       limitations=["kinematisch, ohne Schräglauf; nur Vorwärtsfahrt"],
                       references=["coulter1992"])

    def reset(self, context):
        super().reset(context)
        self.calls = 0                # state (transferred on hot reload)

    def step(self, t, inputs):
        ego, traj = inputs["ego"], inputs["trajectory"]
        if ego is None:
            return {}
        p = self.params
        self.calls += 1
        c, s = math.cos(ego.psi), math.sin(ego.psi)
        xr, yr = ego.x - p.cg_to_rear * c, ego.y - p.cg_to_rear * s
        if traj is None or len(traj) == 0:
            cmd = ControlCommand(t=t, steer_angle=0.0, accel=-p.speed_gain * ego.vx, direction=1,
                                 controller="pure_pursuit")
            return {"command": cmd, "status": ControllerStatus(t=t, active_controller="pure_pursuit")}
        x, y, th = traj.x, traj.y, traj.theta
        n = len(traj)
        i0, best = 0, math.inf
        for i in range(n):
            dx, dy = x[i] - xr, y[i] - yr
            d2 = dx * dx + dy * dy
            if d2 < best:
                i0, best = i, d2
        ld = p.lookahead_min + p.lookahead_gain * abs(ego.vx)
        j = i0
        while j < n - 1:
            dx, dy = x[j] - xr, y[j] - yr
            if math.sqrt(dx * dx + dy * dy) >= ld:
                break
            j += 1
        alpha = wrap(math.atan2(y[j] - yr, x[j] - xr) - ego.psi)
        delta = math.atan2(2.0 * p.wheelbase * math.sin(alpha), ld)
        delta = min(max(delta, -p.max_steer), p.max_steer)
        ref = traj.sample(t)
        accel = ref.a + p.speed_gain * (ref.v - ego.vx)
        dx, dy = xr - x[i0], yr - y[i0]
        ct, st = math.cos(th[i0]), math.sin(th[i0])
        status = ControllerStatus(t=t, e_t=dx * ct + dy * st, e_n=-dx * st + dy * ct, e_theta=wrap(ego.psi - th[i0]),
                                  e_v=ego.vx - ref.v, lookahead=ld, active_controller="pure_pursuit")
        self.signals.update(delta=delta, e_n=status.e_n, lookahead=ld)
        cmd = ControlCommand(t=t, steer_angle=delta, accel=accel, direction=traj.direction, controller="pure_pursuit")
        return {"command": cmd, "status": status}
