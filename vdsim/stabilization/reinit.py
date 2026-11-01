"""High-level part of the bi-level stabilization, controller side (Werling 2.3, 4.5).

    elliptic_measure       (4.5.1) (e_t_dot / c_t)^2 + (e_n_dot / c_n)^2 >= 1 triggers a re-initialization
    ReinitMonitor          trigger with optional absolute error thresholds e_max (Werling 2.3), request held
                           until the planner answers with a re-initialized trajectory, then a cool-down
    predict_motion         (4.5.2) model-independent Taylor series for x1, x2, theta, v over the planning latency
    predict_reference_point  prediction of the trajectory reference point (rear axle or CoG) from the ego state;
                           theta_dot from the KESM via delta at low speed, from a_q / v at high speed (footnote 20)
"""

from __future__ import annotations

import math

from ..framework.knowledge import trace


@trace("werling2011", section="4.5.1", concept="reinitialization_trigger")
def elliptic_measure(e_t_dot, e_n_dot, c_t, c_n):
    return (e_t_dot / c_t) ** 2 + (e_n_dot / c_n) ** 2


class ReinitMonitor:
    def __init__(self, c_t=1.0, c_n=0.5, e_t_max=0.0, e_n_max=0.0, e_theta_max=0.0, cooldown=0.3, max_hold=0.5):
        self.c_t, self.c_n = c_t, c_n
        self.e_max = (e_t_max, e_n_max, e_theta_max)
        self.cooldown, self.max_hold = cooldown, max_hold
        self.reset()

    def reset(self):
        self.request = False
        self.t_request = None
        self.t_block = -math.inf
        self.reason = ""
        self.events = []
        self.measure = 0.0

    def update(self, t, status, trajectory=None):
        self.measure = elliptic_measure(status.e_t_dot, status.e_n_dot, self.c_t, self.c_n)
        if self.request:
            answered = trajectory is not None and trajectory.reinitialized and \
                trajectory.metadata.get("replanned_at", trajectory.t_start) >= self.t_request - 1e-9
            if answered or t - self.t_request >= self.max_hold:
                self.request = False
                self.t_block = t + self.cooldown
            return self.request
        if t < self.t_block:
            return False
        reason = ""
        if self.measure >= 1.0:
            reason = "error_rate"
        else:
            for name, value, limit in zip(("e_t", "e_n", "e_theta"), (status.e_t, status.e_n, status.e_theta),
                                          self.e_max):
                if limit > 0 and abs(value) > limit:
                    reason = name
                    break
        if reason:
            self.request, self.t_request, self.reason = True, t, reason
            self.events.append((t, reason))
        return self.request


@trace("werling2011", section="4.5.2", concept="motion_prediction")
def predict_motion(x0, y0, theta0, v0, theta_dot, v_dot, dt):
    # Taylor series of the motion with constant v_dot and theta_dot (local frame, then rotated back)
    x1 = v0 * dt + v_dot / 2 * dt**2 - v0 * theta_dot**2 / 6 * dt**3 - v_dot * theta_dot**2 / 8 * dt**4
    x2 = v0 * theta_dot / 2 * dt**2 + v_dot * theta_dot / 3 * dt**3 - v0 * theta_dot**3 / 24 * dt**4
    c, s = math.cos(theta0), math.sin(theta0)
    return x0 + c * x1 - s * x2, y0 + s * x1 + c * x2, theta0 + theta_dot * dt, v0 + v_dot * dt


def predict_reference_point(ego, P, reference_point="cog", dt=0.1, v_switch=3.0, direction=1):
    """Predicted state (dict t, x, y, theta, v, reference_point, ...) of the trajectory reference point."""
    l, lh = P.l, P.lh
    sg = -1 if (ego.vx < -0.05 or (abs(ego.vx) <= 0.05 and direction < 0)) else 1
    speed = math.hypot(ego.vx, ego.vy)
    kappa_kin = math.tan(ego.delta) / l
    if reference_point == "rear_axle":
        x0, y0 = ego.rear_axle(lh)
        theta0 = ego.psi if sg > 0 else ego.psi + math.pi
        v0 = abs(ego.vx)
        theta_dot = ego.vx * kappa_kin
        v_dot = sg * (ego.ax + ego.r * ego.vy)
        source = "kesm"
    else:
        x0, y0 = ego.x, ego.y
        if speed <= v_switch:
            # KESM relations: course of the CoG from the steering angle, rate v tan(delta)/l
            theta0 = ego.psi + math.atan(lh * math.tan(ego.delta) / l) + (0.0 if sg > 0 else math.pi)
            theta_dot = ego.vx * kappa_kin
            source = "kesm"
        else:
            beta = math.atan2(ego.vy, ego.vx)
            theta0 = ego.psi + beta
            a_q = -ego.ax * math.sin(beta) + ego.ay * math.cos(beta)
            theta_dot = a_q / speed                                     # footnote 20
            source = "a_q/v"
        v0 = speed
        beta = math.atan2(ego.vy, ego.vx) if speed > 0.1 else 0.0
        v_dot = sg * (ego.ax * math.cos(beta) + ego.ay * math.sin(beta))
    x, y, theta, v = predict_motion(x0, y0, theta0, v0, theta_dot, v_dot, dt)
    return {"t": ego.t + dt, "x": x, "y": y, "theta": theta, "v": max(v, 0.0), "reference_point": reference_point,
            "a": v_dot, "kappa": theta_dot / v0 if v0 > 0.1 else sg * kappa_kin, "direction": sg,
            "psi": theta if sg > 0 else theta - math.pi, "delta": ego.delta, "source": source}
