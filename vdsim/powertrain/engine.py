"""Drive units: combustion engine with full-load curve, electric motor with torque/power limits."""

import numpy as np

RPM_TO_RADS = 2 * np.pi / 60


class CombustionEngine:
    def __init__(self, rpm, torque, idle_rpm=None, max_rpm=None):
        self.rpm = np.asarray(rpm, dtype=float)
        self.torque = np.asarray(torque, dtype=float)
        self.idle_rpm = idle_rpm or self.rpm[0]
        self.max_rpm = max_rpm or self.rpm[-1]

    def max_torque(self, rpm):
        rpm = np.clip(rpm, self.idle_rpm, None)
        return np.where(rpm > self.max_rpm, 0.0, np.interp(rpm, self.rpm, self.torque))

    def max_power(self):
        rpm = np.linspace(self.rpm[0], self.rpm[-1], 200)
        return float(np.max(self.max_torque(rpm) * rpm * RPM_TO_RADS))


class Gearbox:
    def __init__(self, ratios, final_drive, upshift_rpm, downshift_rpm, efficiency=0.92):
        self.ratios = list(ratios)
        self.final_drive = final_drive
        self.upshift_rpm = upshift_rpm
        self.downshift_rpm = downshift_rpm
        self.efficiency = efficiency
        self.gear = 1

    def total_ratio(self, gear=None):
        return self.ratios[(gear or self.gear) - 1] * self.final_drive

    def engine_rpm(self, wheel_speed, gear=None):
        return abs(wheel_speed) * self.total_ratio(gear) / RPM_TO_RADS

    def update(self, wheel_speed):
        # simple automatic: shift up/down at fixed engine speeds
        rpm = self.engine_rpm(wheel_speed)
        if rpm > self.upshift_rpm and self.gear < len(self.ratios):
            self.gear += 1
        elif rpm < self.downshift_rpm and self.gear > 1:
            self.gear -= 1
        return self.gear


class ElectricMotor:
    def __init__(self, max_torque, max_power, gear_ratio, max_rpm, efficiency=0.9,
                 regen_max_torque=0.0, regen_max_power=0.0):
        self.max_torque_value = max_torque
        self.max_power = max_power
        self.gear_ratio = gear_ratio
        self.max_rpm = max_rpm
        self.efficiency = efficiency
        self.regen_max_torque = regen_max_torque
        self.regen_max_power = regen_max_power

    def motor_speed(self, wheel_speed):
        return abs(wheel_speed) * self.gear_ratio

    def max_torque(self, wheel_speed):
        # motor torque limit: constant torque, then constant power
        w = self.motor_speed(wheel_speed)
        if w / RPM_TO_RADS > self.max_rpm:
            return 0.0
        return min(self.max_torque_value, self.max_power / max(w, 1e-6))

    def max_regen(self, wheel_speed):
        w = self.motor_speed(wheel_speed)
        return min(self.regen_max_torque, self.regen_max_power / max(w, 1e-6))
