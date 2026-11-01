"""Vehicle state seen by controllers/sensors and the control input sent to the vehicle model."""

from dataclasses import dataclass, field

import numpy as np


def _zeros4():
    return np.zeros(4)


@dataclass
class VehicleState:
    # Common, model-independent view of the vehicle (earth frame position, vehicle frame velocities)
    t: float = 0.0
    x: float = 0.0
    y: float = 0.0
    psi: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    r: float = 0.0            # yaw rate
    ax: float = 0.0           # longitudinal acceleration (vehicle frame)
    ay: float = 0.0           # lateral acceleration (vehicle frame)
    delta_f: float = 0.0      # front road-wheel angle
    delta_r: float = 0.0      # rear road-wheel angle
    roll: float = 0.0
    roll_rate: float = 0.0
    pitch: float = 0.0
    pitch_rate: float = 0.0
    heave: float = 0.0
    heave_rate: float = 0.0
    wheel_speed: np.ndarray = field(default_factory=_zeros4)  # rad/s
    slip_ratio: np.ndarray = field(default_factory=_zeros4)
    slip_angle: np.ndarray = field(default_factory=_zeros4)
    fx: np.ndarray = field(default_factory=_zeros4)
    fy: np.ndarray = field(default_factory=_zeros4)
    fz: np.ndarray = field(default_factory=_zeros4)
    mu: np.ndarray = field(default_factory=lambda: np.ones(4))  # road friction at each wheel

    @property
    def speed(self):
        return float(np.hypot(self.vx, self.vy))

    @property
    def beta(self):
        # side slip angle at the center of gravity
        return float(np.arctan2(self.vy, max(abs(self.vx), 0.1)))

    @property
    def friction_utilization(self):
        # |F| / (mu Fz) per wheel, 1 = at the friction limit
        return np.hypot(self.fx, self.fy) / np.maximum(self.mu * self.fz, 1.0)


@dataclass
class ControlInput:
    steer_front: float = 0.0                                       # road-wheel angle, rad
    steer_rear: float = 0.0                                        # rad
    drive_torque: np.ndarray = field(default_factory=_zeros4)      # N m per wheel
    brake_torque: np.ndarray = field(default_factory=_zeros4)      # N m per wheel (>= 0)
    roll_moment: float = 0.0                                       # active anti-roll moment, N m
    damper_force: np.ndarray = field(default_factory=_zeros4)      # active damper force per wheel, N

    def copy(self):
        return ControlInput(self.steer_front, self.steer_rear, self.drive_torque.copy(),
                            self.brake_torque.copy(), self.roll_moment, self.damper_force.copy())
