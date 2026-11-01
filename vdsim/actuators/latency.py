"""Latency in the effect chain: planner -> gateway -> actuator -> vehicle -> odometry -> gateway -> planner."""

from collections import deque

#   dead_time:    command path, planner -> actuator
#   tau:          PT1 time constant of actuator + vehicle yaw response
#   sensor_delay: feedback path, odometry -> planner
LATENCY_CASES = {
    "none": {"dead_time": 0.00, "tau": 0.00, "sensor_delay": 0.00},
    # System architecture (see README): gateway 40 ms + actuator 5 ms, odometry 5 ms + gateway 40 ms
    "system": {"dead_time": 0.045, "tau": 0.00, "sensor_delay": 0.045},
    # What-if cases with slower communication and actuator dynamics (assumptions;
    # command-to-vehicle-reaction is typically 0.07-0.5 s, cf. steerActuatorDelay in openpilot/opendbc)
    "typical": {"dead_time": 0.06, "tau": 0.10, "sensor_delay": 0.02},
    "high": {"dead_time": 0.15, "tau": 0.20, "sensor_delay": 0.05},
}


class DeadTime:
    # Outputs the input delayed by `delay` seconds
    def __init__(self, delay, dt):
        self.buffer = deque([0.0] * round(delay / dt))

    def step(self, u):
        if not self.buffer:
            return u
        self.buffer.append(u)
        return self.buffer.popleft()


class PT1:
    # First-order lag with time constant tau (tau = 0: pass-through)
    def __init__(self, tau, dt):
        self.alpha = dt / (tau + dt)
        self.y = 0.0

    def step(self, u):
        self.y += self.alpha * (u - self.y)
        return self.y


class LatencyChain:
    # Actuator path (dead time + PT1) and sensor path (dead time)
    def __init__(self, dead_time, tau, sensor_delay, dt):
        self.actuator_delay = DeadTime(dead_time, dt)
        self.actuator_lag = PT1(tau, dt)
        self.sensor_delay = DeadTime(sensor_delay, dt)

    def actuate(self, k_sent):
        return self.actuator_lag.step(self.actuator_delay.step(k_sent))

    def sense(self, k):
        return self.sensor_delay.step(k)
