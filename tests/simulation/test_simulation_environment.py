"""Tests for the simulation environment (friction, road profile, lead vehicle)."""

import numpy as np
import pytest

from vdsim.simulation.environment import (
    Environment,
    FrictionMap,
    FrictionPatch,
    LeadVehicle,
    RoadProfile,
)


class TestFrictionMap:
    def test_uniform_default(self):
        fm = FrictionMap()
        assert fm.mu_at(0.0, 0.0) == pytest.approx(1.0)

    def test_uniform_custom(self):
        fm = FrictionMap.uniform(0.7)
        assert fm.mu_at(10.0, 5.0) == pytest.approx(0.7)

    def test_patch_inside(self):
        fm = FrictionMap(
            base=1.0,
            patches=[FrictionPatch(10, 20, -5, 5, 0.3, "ice")],
        )
        assert fm.mu_at(15.0, 0.0) == pytest.approx(0.3)

    def test_patch_outside(self):
        fm = FrictionMap(
            base=1.0,
            patches=[FrictionPatch(10, 20, -5, 5, 0.3, "ice")],
        )
        assert fm.mu_at(5.0, 0.0) == pytest.approx(1.0)

    def test_split_mu(self):
        fm = FrictionMap.split_mu(mu_left=0.2, mu_right=1.0)
        assert fm.mu_at(50.0, 10.0) == pytest.approx(0.2)
        assert fm.mu_at(50.0, -10.0) == pytest.approx(1.0)

    def test_vectorized(self):
        fm = FrictionMap.uniform(0.8)
        x = np.array([0, 10, 20])
        y = np.array([0, 0, 0])
        mu = fm.mu_at(x, y)
        np.testing.assert_allclose(mu, 0.8)

    def test_serialization_roundtrip(self):
        fm = FrictionMap(base=0.9, patches=[FrictionPatch(0, 10, -5, 5, 0.5, "wet")])
        d = fm.to_dict()
        restored = FrictionMap.from_dict(d)
        assert restored.base == pytest.approx(0.9)
        assert len(restored.patches) == 1


class TestFrictionMapGrid:
    def test_grid_interpolation(self):
        gx = np.array([0.0, 10.0, 20.0])
        gy = np.array([0.0, 10.0])
        grid = np.array([[1.0, 0.8, 0.6], [0.9, 0.7, 0.5]])
        fm = FrictionMap(grid_x=gx, grid_y=gy, grid_mu=grid)
        mu = fm.mu_at(5.0, 5.0)
        assert 0.5 < mu < 1.0


class TestRoadProfile:
    def test_flat_by_default(self):
        rp = RoadProfile()
        assert rp.height(50.0) == pytest.approx(0.0)

    def test_single_bump(self):
        rp = RoadProfile(bumps=[{"x": 10.0, "height": 0.05, "length": 2.0}])
        z_peak = rp.height(11.0)
        assert z_peak == pytest.approx(0.05, abs=0.001)

    def test_bump_zero_outside(self):
        rp = RoadProfile(bumps=[{"x": 10.0, "height": 0.05, "length": 2.0}])
        assert rp.height(0.0) == pytest.approx(0.0)
        assert rp.height(50.0) == pytest.approx(0.0)

    def test_vectorized_height(self):
        rp = RoadProfile()
        z = rp.height(np.array([0, 10, 20]))
        assert z.shape == (3,)

    def test_roughness_class_generates_profile(self):
        rp = RoadProfile(roughness_class="B", length=100, seed=42)
        assert rp._z is not None
        z = rp.height(50.0)
        assert isinstance(z, float)


class TestLeadVehicle:
    def test_constant_speed(self):
        lv = LeadVehicle(speed=[20.0, 20.0], time=[0.0, 100.0])
        assert lv.speed_at(50.0) == pytest.approx(20.0)

    def test_interpolated_speed(self):
        lv = LeadVehicle(speed=[20.0, 10.0], time=[0.0, 10.0])
        assert lv.speed_at(5.0) == pytest.approx(15.0)


class TestEnvironment:
    def test_default_environment(self):
        env = Environment()
        assert env.mu_at(0.0, 0.0) == pytest.approx(1.0)
        assert env.road_height(0.0) == pytest.approx(0.0)
        assert env.wind_speed == 0.0

    def test_serialization_roundtrip(self):
        env = Environment(wind_speed=5.0)
        d = env.to_dict()
        restored = Environment.from_dict(d)
        assert restored.wind_speed == pytest.approx(5.0)

    def test_from_dict_empty(self):
        env = Environment.from_dict({})
        assert env.wind_speed == 0.0

    def test_from_dict_none(self):
        env = Environment.from_dict(None)
        assert env.wind_speed == 0.0
