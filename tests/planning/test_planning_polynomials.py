import numpy as np
import pytest

from vdsim.planning.cost import CostModel, CostSettings
from vdsim.planning.lateral import build_lateral_set
from vdsim.planning.longitudinal import StoppingTarget, VelocityTarget, build_longitudinal_set
from vdsim.planning.polynomials import (ConstantReference, PolynomialSet, coefficient_matrices, jerk_integral, polyval,
                                        quartic_coefficients, quintic_coefficients)
from vdsim.planning.sampling import SamplingParams, end_grid
from vdsim.geometry.reference_line import FrenetState


def test_quintic_boundary_conditions_and_matrix_form():
    rng = np.random.default_rng(1)
    x0, v0, a0, x1, v1, a1 = rng.normal(size=(6, 20))
    tau = rng.uniform(0.3, 6.0, 20)
    c = quintic_coefficients(x0, v0, a0, x1, v1, a1, tau)
    p0 = polyval(c, np.zeros((20, 1)))
    p1 = polyval(c, tau[:, None])
    np.testing.assert_allclose([p0[0][:, 0], p0[1][:, 0], p0[2][:, 0]], [x0, v0, a0], atol=1e-10)
    np.testing.assert_allclose([p1[0][:, 0], p1[1][:, 0], p1[2][:, 0]], [x1, v1, a1], atol=1e-8)
    # (3.8): c345 = M2(tau)^-1 [xi(tau) - M1(tau) c012]
    m1, m2 = coefficient_matrices(tau[0])
    c345 = np.linalg.solve(m2, np.array([x1[0], v1[0], a1[0]]) - m1 @ c[0, :3])
    np.testing.assert_allclose(c[0, 3:], c345, rtol=1e-9, atol=1e-10)


def test_quartic_boundary_conditions_free_end_position():
    c = quartic_coefficients(1.0, 10.0, 0.5, 15.0, 0.0, 4.0)
    p, v, a, _ = polyval(c[None, :], np.array([[0.0, 4.0]]))
    assert c[5] == 0.0                                   # Satz 2: c5 = 0
    assert v[0, 0] == pytest.approx(10.0) and a[0, 0] == pytest.approx(0.5)
    assert v[0, 1] == pytest.approx(15.0) and a[0, 1] == pytest.approx(0.0, abs=1e-12)


def test_jerk_integral_closed_form_matches_numeric():
    rng = np.random.default_rng(2)
    for _ in range(10):
        c = quintic_coefficients(*rng.normal(size=6), rng.uniform(0.5, 5))
        tau = rng.uniform(0.5, 5)
        t = np.linspace(0, tau, 20001)
        j = 6 * c[3] + 24 * c[4] * t + 60 * c[5] * t ** 2
        numeric = np.trapezoid(j ** 2, t)
        assert float(jerk_integral(c, tau)) == pytest.approx(numeric, rel=1e-6)


def test_rest_to_rest_jerk_values():
    # used by the lock-in analysis: quintic 720 d^2 / tau^5, quartic 12 dv^2 / tau^3
    c = quintic_coefficients(0, 0, 0, 2.0, 0, 0, 3.0)
    assert float(jerk_integral(c, 3.0)) == pytest.approx(720 * 4 / 3 ** 5)
    c = quartic_coefficients(0, 5.0, 0, 8.0, 0, 2.0)
    assert float(jerk_integral(c, 2.0)) == pytest.approx(12 * 9 / 8)


def test_continuation_on_target_manifold():
    c = quintic_coefficients(0.0, 0.0, 0.0, 1.5, 0.0, 0.0, 2.0)
    ps = PolynomialSet(c[None, :], [2.0], "reference", ConstantReference(1.0), [0.5])
    p, v, a, j = ps.evaluate(np.array([1.0, 2.0, 3.0, 10.0]))
    assert p[0, 2] == pytest.approx(1.5) and p[0, 3] == pytest.approx(1.5)
    assert v[0, 3] == 0.0 and a[0, 3] == 0.0 and j[0, 3] == 0.0
    cv = quartic_coefficients(0.0, 10.0, 0.0, 12.0, 0.0, 2.0)
    ps = PolynomialSet(cv[None, :], [2.0], "velocity")
    p, v, a, _ = ps.evaluate(np.array([2.0, 4.0]))
    assert v[0, 1] == pytest.approx(12.0) and p[0, 1] == pytest.approx(p[0, 0] + 24.0)


def test_absolute_time_grid_and_consistency_guard():
    g = end_grid(0.37, 0.5, 0.05, 2.0)
    np.testing.assert_allclose(g.k * 0.5 - 0.37, g.tau)
    assert np.all(g.tau >= 0.05 - 1e-12)
    # the absolute end time of an old optimum stays in the set even below tau_min
    g2 = end_grid(0.98, 0.5, 0.05, 2.0, keep_k=2)
    assert 2 in g2.k.tolist() and g2.tau[g2.k == 2][0] == pytest.approx(0.02)
    rel = end_grid(0.37, 0.5, 0.05, 2.0, absolute=False)
    np.testing.assert_allclose(rel.tau, [0.5, 1.0, 1.5, 2.0])


def test_costs_follow_table_3_1():
    sp = SamplingParams()
    cs = CostSettings()
    model = CostModel(cs)
    start = FrenetState(s=10.0, s_d=15.0, s_dd=0.0, d=1.0, d_d=0.2, d_dd=0.0)
    grid = np.arange(0, 3.0001, 0.1)
    lat = build_lateral_set(start, "time", 0.0, 0.0, -1e9, 1e9, 0.9, sp, grid)
    model.lateral(lat, None)
    kj, kt, kd = cs.jerk.k_lat, cs.terminal_time.k_tau_lat, cs.terminal_deviation.k_delta
    expected = kj * 0.5 * jerk_integral(lat.poly.coeffs, lat.tau) + kt * lat.tau + 0.5 * kd * lat.delta ** 2
    np.testing.assert_allclose(lat.total, expected)
    # end states q345(d_ref + delta, 0, 0, tau)
    p, v, a, _ = lat.poly.evaluate(lat.tau[:, None])
    np.testing.assert_allclose(p[:, 0], lat.delta, atol=1e-8)
    lon = build_longitudinal_set(start, VelocityTarget(20.0), 0.0, sp, grid)
    model.longitudinal(lon, None)
    exp = cs.jerk.k_lon * 0.5 * lon.jerk + cs.terminal_time.k_tau_lon * lon.tau + 0.5 * cs.terminal_deviation.k_nu * \
        lon.offset ** 2
    np.testing.assert_allclose(lon.total, exp)
    _, v, a, _ = lon.poly.evaluate(lon.tau[:, None])
    np.testing.assert_allclose(v[:, 0], 20.0 + lon.offset, atol=1e-8)
    stop = build_longitudinal_set(start, StoppingTarget(100.0, 2.25), 0.0, sp, grid)
    model.longitudinal(stop, None)
    p, v, _, _ = stop.poly.evaluate(stop.tau[:, None])
    np.testing.assert_allclose(p[:, 0], 100.0 - 2.25 + stop.offset, atol=1e-7)
    assert np.all(stop.offset <= 0)                              # no overshoot of the stop line by default
    np.testing.assert_allclose(stop.total, cs.jerk.k_lon * 0.5 * stop.jerk + cs.terminal_time.k_tau_lon * stop.tau
                               + 0.5 * cs.terminal_deviation.k_sigma * stop.offset ** 2)
