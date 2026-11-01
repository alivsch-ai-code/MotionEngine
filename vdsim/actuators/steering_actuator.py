"""Steering actuator for the platform simulator.

Steering request (road-wheel angle) -> optional feedback correction -> actuator characteristic
error -> latency chain (gateway/actuator dead time, PT1) -> rate limit -> applied angle.
The characteristic and the correction work on curvature k = tan(delta) / L, like the
lane-change latency study.
"""

from dataclasses import asdict, dataclass

import numpy as np

from ..controllers.curvature_feedback import CurvatureCorrection
from .latency import LatencyChain
from .steering_characteristic import steering_characteristic


@dataclass
class SteeringActuatorParameters:
    dead_time: float = 0.0             # s, command path (gateway + actuator)
    tau: float = 0.0                   # s, PT1 of the actuator
    sensor_delay: float = 0.0          # s, feedback path (odometry + gateway)
    rate_limit: float = 0.0            # rad/s road-wheel angle, 0 = unlimited
    characteristic_error: bool = False
    k_full_lock: float = 0.3           # 1/m, true curvature at full lock
    k_full_lock_assumed: float = 0.2   # 1/m, end of the distorted characteristic
    error_at_zero: float = 0.10
    feedback_correction: bool = False

    def to_dict(self):
        return asdict(self)


class SteeringActuator:
    def __init__(self, params, wheelbase, dt):
        self.p = params if isinstance(params, SteeringActuatorParameters) else SteeringActuatorParameters(**(params or {}))
        self.wheelbase, self.dt = wheelbase, dt
        self.chain = LatencyChain(self.p.dead_time, self.p.tau, self.p.sensor_delay, dt)
        self.model = LatencyChain(self.p.dead_time, self.p.tau, self.p.sensor_delay, dt)
        self.characteristic = (steering_characteristic(self.p.k_full_lock_assumed, self.p.k_full_lock, self.p.error_at_zero)
                               if self.p.characteristic_error else (lambda k: k))
        self.correction = CurvatureCorrection(dt) if self.p.feedback_correction else None
        self.delta = 0.0
        self.signals = {}

    def step(self, delta_request, measured_curvature):
        # measured_curvature: yaw rate / speed seen by the planner (before the feedback delay)
        L = self.wheelbase
        k_request = np.tan(delta_request) / L
        k_sent = self.correction.correct(k_request) if self.correction else k_request
        k_applied = float(self.characteristic(self.chain.actuate(k_sent)))
        k_meas = self.chain.sense(measured_curvature)
        if self.correction:
            self.correction.update(self.model.sense(self.model.actuate(k_sent)), k_meas)
        delta = np.arctan(k_applied * L)
        if self.p.rate_limit > 0:
            max_step = self.p.rate_limit * self.dt
            delta = float(np.clip(delta, self.delta - max_step, self.delta + max_step))
        self.delta = delta
        self.signals = {"steer_request": delta_request, "steer_applied": delta, "k_sent": k_sent,
                        "k_meas_delayed": k_meas,
                        "error_factor_est": self.correction.gain if self.correction else 1.0}
        return delta
