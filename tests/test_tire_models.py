import numpy as np
import pytest

from vdsim.tire_models import BrushTire, LinearTire, PacejkaTire, create_tires

KW = dict(cornering_stiffness=80000.0, longitudinal_stiffness=100000.0, nominal_load=4000.0)


@pytest.mark.parametrize("cls", [LinearTire, PacejkaTire, BrushTire])
def test_small_slip_stiffness_equals_parameter(cls):
    tire = cls(**KW)
    _, fy, _ = tire.forces(1e-4, 0.0, 4000.0)
    fx, _, _ = tire.forces(0.0, 1e-4, 4000.0)
    assert fy / 1e-4 == pytest.approx(80000.0, rel=2e-3)
    assert fx / 1e-4 == pytest.approx(100000.0, rel=2e-3)


@pytest.mark.parametrize("cls", [LinearTire, PacejkaTire, BrushTire])
def test_forces_are_odd_and_saturate(cls):
    tire = cls(**KW)
    _, fy_pos, _ = tire.forces(0.05, 0.0, 4000.0)
    _, fy_neg, _ = tire.forces(-0.05, 0.0, 4000.0)
    assert fy_pos == pytest.approx(-fy_neg)
    _, fy_big, _ = tire.forces(0.6, 0.0, 4000.0)
    assert 0.6 * 4000 < fy_big <= 1.0 * 4000 * 1.001


def test_pacejka_load_degressive_stiffness():
    tire = PacejkaTire(**KW)
    assert tire.cornering_stiffness(8000.0) < 2 * tire.cornering_stiffness(4000.0)
    assert tire.cornering_stiffness(4000.0) == pytest.approx(80000.0)


def test_combined_slip_reduces_lateral_force():
    tire = PacejkaTire(**KW)
    _, fy_pure, _ = tire.forces(0.05, 0.0, 4000.0)
    _, fy_comb, _ = tire.forces(0.05, 0.1, 4000.0)
    assert fy_comb < 0.8 * fy_pure


def test_zero_load_gives_zero_force():
    for cls in (LinearTire, PacejkaTire, BrushTire):
        fx, fy, mz = cls(**KW).forces(0.1, 0.1, 0.0)
        assert abs(fx) < 1e-6 and abs(fy) < 1e-6


def test_vectorized_and_factory(sedan):
    front, rear = create_tires(sedan.tires)
    fx, fy, _ = front.forces(np.array([0.01, 0.02]), np.array([0.0, 0.0]), np.array([4000.0, 4000.0]))
    assert fy.shape == (2,) and fy[1] > fy[0] > 0
