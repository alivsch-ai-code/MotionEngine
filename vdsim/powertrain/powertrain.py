"""Powertrain, brakes and the longitudinal actuation (acceleration request -> wheel torques)."""

import numpy as np

from ..core.conventions import G
from ..vehicle_models.common import aero_drag, rolling_resistance
from .engine import CombustionEngine, ElectricMotor, Gearbox


class Powertrain:
    # Maps a requested total drive force to wheel torques (layout, limits) and tracks energy
    def __init__(self, params, vehicle):
        self.p, self.vehicle = params, vehicle
        self.front_share = {"fwd": 1.0, "rwd": 0.0}.get(params.layout, params.front_torque_split)
        if params.type == "ice":
            self.engine = CombustionEngine(params.engine_speed_rpm, params.engine_torque_nm)
            self.gearbox = Gearbox(params.gear_ratios, params.final_drive, params.upshift_rpm,
                                   params.downshift_rpm, params.driveline_efficiency)
            self.motor = None
        else:
            self.engine = self.gearbox = None
            # one motor per driven axle, sized by the axle's torque share
            self.motor = ElectricMotor(params.motor_max_torque, params.motor_max_power, params.motor_gear_ratio,
                                       params.motor_max_rpm, params.motor_efficiency,
                                       params.regen_max_torque, params.regen_max_power)
        self.energy_drive = 0.0   # J taken from the battery / fuel energy
        self.energy_regen = 0.0   # J recovered
        self.signals = {}

    @property
    def axle_shares(self):
        return np.array([self.front_share, self.front_share, 1 - self.front_share, 1 - self.front_share]) / 2

    def max_drive_force(self, speed):
        wheel_speed = speed / self.vehicle.wheel_radius
        if self.motor is not None:
            torque = self.motor.max_torque(wheel_speed) * self.p.motor_gear_ratio * self.p.driveline_efficiency
        else:
            self.gearbox.update(wheel_speed)
            rpm = max(self.gearbox.engine_rpm(wheel_speed), self.engine.idle_rpm)
            torque = float(self.engine.max_torque(rpm)) * self.gearbox.total_ratio() * self.gearbox.efficiency
        return torque / self.vehicle.wheel_radius

    def max_regen_force(self, speed):
        if self.motor is None:
            return 0.0
        wheel_speed = speed / self.vehicle.wheel_radius
        return self.motor.max_regen(wheel_speed) * self.p.motor_gear_ratio / self.vehicle.wheel_radius

    def wheel_torques(self, force):
        return force * self.vehicle.wheel_radius * self.axle_shares

    def account_energy(self, drive_force, regen_force, speed, dt):
        mech_drive = max(drive_force * speed, 0.0)
        mech_regen = max(regen_force * speed, 0.0)
        if self.motor is not None:
            p_batt = mech_drive / (self.p.motor_efficiency * self.p.driveline_efficiency) \
                - mech_regen * self.p.motor_efficiency * self.p.driveline_efficiency + self.p.auxiliary_power
        else:
            p_batt = mech_drive / 0.30 + self.p.auxiliary_power  # fuel energy, ~30 % engine efficiency
        self.energy_drive += max(p_batt, 0.0) * dt
        self.energy_regen += max(-p_batt, 0.0) * dt
        self.signals = {"power_battery": p_batt, "power_drive": mech_drive, "power_regen": mech_regen}
        if self.gearbox is not None:
            wheel_speed = speed / self.vehicle.wheel_radius
            self.signals.update(gear=self.gearbox.gear, engine_rpm=self.gearbox.engine_rpm(wheel_speed))
        return p_batt


class BrakeSystem:
    def __init__(self, params, vehicle):
        self.p, self.vehicle = params, vehicle

    def front_share(self, force):
        # EBV: follow the ideal distribution (axle loads during braking) to keep the rear stable
        if not self.p.ebd_enabled:
            return self.p.brake_balance
        v = self.vehicle
        decel = force / (v.mass * G)
        ideal = (v.cg_to_rear + decel * v.cg_height) / v.wheelbase
        return float(np.clip(ideal + 0.03, self.p.brake_balance, 0.85))

    def axle_torques(self, front_force, rear_force):
        R = self.vehicle.wheel_radius
        t_front = min(front_force * R / 2, self.p.max_torque_front)
        t_rear = min(rear_force * R / 2, self.p.max_torque_rear)
        return np.array([t_front, t_front, t_rear, t_rear])

    def wheel_torques(self, force, front_share=None):
        # Total braking force (>= 0) -> brake torque per wheel, split by the brake balance
        share = self.front_share(force) if front_share is None else front_share
        torque = force * self.vehicle.wheel_radius
        t_front = min(torque * share / 2, self.p.max_torque_front)
        t_rear = min(torque * (1 - share) / 2, self.p.max_torque_rear)
        return np.array([t_front, t_front, t_rear, t_rear])


class LongitudinalActuation:
    # Acceleration request -> drive/brake torques (feedforward of driving resistances, regen blending)
    def __init__(self, config):
        self.vehicle = config.vehicle
        self.powertrain = Powertrain(config.powertrain, config.vehicle)
        self.brakes = BrakeSystem(config.brakes, config.vehicle)
        self.signals = {}

    def reset(self):
        self.powertrain.energy_drive = self.powertrain.energy_regen = 0.0

    def actuate(self, ax_request, state, u, dt, env):
        v = max(state.vx, 0.0)
        p = self.vehicle
        force = p.mass * ax_request + aero_drag(p, v, env.wind_speed) + rolling_resistance(p, v)
        force = float(np.clip(force, -1.3 * p.mass * G, None))
        drive = regen = friction = 0.0
        if force >= 0:
            drive = min(force, self.powertrain.max_drive_force(v))
            u.drive_torque = self.powertrain.wheel_torques(drive)
            u.brake_torque = np.zeros(4)
        else:
            # braking demand per axle from the brake distribution (EBV); regen first on driven axles
            total = -force
            share = self.brakes.front_share(total)
            need = np.array([share, 1 - share]) * total
            pt_share = np.array([self.powertrain.front_share, 1 - self.powertrain.front_share])
            regen_cap = self.powertrain.max_regen_force(v) if v > 1.0 else 0.0
            regen_axle = np.minimum(need, regen_cap * pt_share)
            friction_axle = need - regen_axle
            regen, friction = float(regen_axle.sum()), float(friction_axle.sum())
            R = self.vehicle.wheel_radius
            u.drive_torque = -np.repeat(regen_axle, 2) * R / 2
            u.brake_torque = self.brakes.axle_torques(*friction_axle)
        self.powertrain.account_energy(drive, regen, v, dt)
        self.signals = {"ax_request": ax_request, "force_drive": drive, "force_regen": regen,
                        "force_brake": friction, **self.powertrain.signals}
        return u
