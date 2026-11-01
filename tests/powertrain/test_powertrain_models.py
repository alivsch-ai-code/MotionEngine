"""Tests for powertrain components (engine, gearbox, motor, brake system)."""

import numpy as np
import pytest

from vdsim.powertrain.engine import CombustionEngine, ElectricMotor, Gearbox


class TestCombustionEngine:
    @pytest.fixture
    def engine(self):
        rpm = [1000, 2000, 3000, 4000, 5000, 6000]
        torque = [150, 200, 250, 260, 240, 200]
        return CombustionEngine(rpm, torque, idle_rpm=1000, max_rpm=6000)

    def test_max_torque_at_known_point(self, engine):
        assert engine.max_torque(3000) == pytest.approx(250.0)

    def test_interpolation_between_points(self, engine):
        t = engine.max_torque(2500)
        assert 200 < t < 250

    def test_zero_above_max_rpm(self, engine):
        assert engine.max_torque(7000) == pytest.approx(0.0)

    def test_clamp_below_idle(self, engine):
        t = engine.max_torque(500)
        assert t == pytest.approx(engine.max_torque(1000))

    def test_max_power_positive(self, engine):
        assert engine.max_power() > 0

    def test_vectorized_input(self, engine):
        rpms = np.array([1000, 3000, 5000])
        torques = engine.max_torque(rpms)
        assert torques.shape == (3,)


class TestGearbox:
    @pytest.fixture
    def gearbox(self):
        return Gearbox(
            ratios=[3.5, 2.2, 1.5, 1.0, 0.8],
            final_drive=3.7,
            upshift_rpm=5500,
            downshift_rpm=1500,
            efficiency=0.92,
        )

    def test_total_ratio_first_gear(self, gearbox):
        assert gearbox.total_ratio(1) == pytest.approx(3.5 * 3.7)

    def test_engine_rpm_calculation(self, gearbox):
        rpm = gearbox.engine_rpm(100.0, gear=1)
        assert rpm > 0

    def test_upshift(self, gearbox):
        gearbox.gear = 1
        wheel_speed = gearbox.upshift_rpm * 2 * np.pi / 60 / gearbox.total_ratio(1) * 1.1
        gearbox.update(wheel_speed)
        assert gearbox.gear == 2

    def test_downshift(self, gearbox):
        gearbox.gear = 3
        wheel_speed = gearbox.downshift_rpm * 2 * np.pi / 60 / gearbox.total_ratio(3) * 0.5
        gearbox.update(wheel_speed)
        assert gearbox.gear == 2

    def test_no_shift_below_first(self, gearbox):
        gearbox.gear = 1
        gearbox.update(0.1)
        assert gearbox.gear == 1

    def test_no_shift_above_max(self, gearbox):
        gearbox.gear = 5
        gearbox.update(1000.0)
        assert gearbox.gear == 5


class TestElectricMotor:
    @pytest.fixture
    def motor(self):
        return ElectricMotor(
            max_torque=300,
            max_power=150000,
            gear_ratio=9.0,
            max_rpm=12000,
            efficiency=0.9,
            regen_max_torque=200,
            regen_max_power=80000,
        )

    def test_constant_torque_region(self, motor):
        assert motor.max_torque(1.0) == pytest.approx(300.0)

    def test_constant_power_region(self, motor):
        t = motor.max_torque(100.0)
        assert t < 300.0
        assert t > 0.0

    def test_zero_above_max_rpm(self, motor):
        huge_speed = motor.max_rpm * 2 * np.pi / 60 / motor.gear_ratio * 2
        assert motor.max_torque(huge_speed) == pytest.approx(0.0)

    def test_regen_torque_limited(self, motor):
        assert motor.max_regen(1.0) <= 200.0
        assert motor.max_regen(1.0) > 0

    def test_motor_speed_calculation(self, motor):
        assert motor.motor_speed(10.0) == pytest.approx(90.0)
