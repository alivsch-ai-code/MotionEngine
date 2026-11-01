import numpy as np
import pytest

from vdsim.planning.analysis import (
    continuous_solution,
    estimate_sampling_horizon,
    lock_in_check,
    lock_in_distance,
    optimal_end_time,
)
from vdsim.planning.cost import CostSettings
from vdsim.planning.polynomials import polyval
from vdsim.planning.sampling import SamplingParams


def test_continuous_solution_satisfies_manifold_and_transversality():
    sol = continuous_solution((2.0, 0.3, -0.1), 3.0, 50.0, (0.5, 0.0, 0.0))
    p, v, a, _ = polyval(sol["coeffs"][None, :], np.array([[3.0]]))
    assert v[0, 0] == pytest.approx(0.0, abs=1e-10) and a[0, 0] == pytest.approx(0.0, abs=1e-10)   # (3.9)
    assert p[0, 0] - 0.5 == pytest.approx(sol["end_deviation"])                                       # (3.11)
    assert sol["end_deviation"] == pytest.approx(-120 / 50.0 * sol["coeffs"][5])


def test_continuous_end_distance_equals_3_14():
    # remark 2: xi2(0) = xi3(0) = 0, constant reference -> d0 / (1 + k tau^5 / 720)
    for k, tau in ((10.0, 2.0), (200.0, 3.0), (5.0, 1.0)):
        sol = continuous_solution((1.3, 0.0, 0.0), tau, k, (0.0, 0.0, 0.0))
        assert sol["end_deviation"] == pytest.approx(lock_in_distance(1.3, k, tau), rel=1e-9)


def test_optimal_end_time_fulfills_3_13():
    opt = optimal_end_time((3.5, 0.0, 0.0), 5.0, 200.0, lambda t: (0.0, 0.0, 0.0), 12.0, 300)
    assert 2.0 < opt["tau"] < 8.0
    # necessary condition (3.13) at the optimum (relative to the magnitude of k_tau)
    assert abs(opt["residual_at_opt"]) < 0.05 * 5.0
    # and the scan minimum is a true minimum of J(tau)
    assert opt["cost"] <= np.min(opt["costs"]) + 1e-6


def test_transversality_sign_change_brackets_optimum():
    opt = optimal_end_time((1.0, 0.0, 0.0), 2.0, 30.0, lambda t: (0.0, 0.0, 0.0), 10.0, 400)
    i = int(np.argmin(np.abs(opt["taus"] - opt["tau"])))
    res = opt["residual"]
    assert np.sign(res[max(i - 5, 0)]) != np.sign(res[min(i + 5, len(res) - 1)])


def test_lock_in_check_detects_parallel_driving():
    sp, cs = SamplingParams(), CostSettings()
    ok = lock_in_check(sp, cs)
    assert ok["warnings"] == [] and ok["quer d(t)"]["locked_offsets"] == []
    assert ok["quer d(t)"]["continuous_end_distance"] < 0.5 * sp.lat_d_step
    cs.terminal_deviation.k_delta = 5.0          # far too weak end-offset penalty -> vehicle stays offset
    bad = lock_in_check(sp, cs)
    assert bad["quer d(t)"]["locked_offsets"] and bad["warnings"]


def test_sampling_horizon_estimate():
    sp, cs = SamplingParams(), CostSettings()
    est = estimate_sampling_horizon(sp, cs)
    assert est["tau_opt"]["lateral"] < sp.lat_tau_max and est["warnings"] == []
    sp.lat_tau_max = 1.0
    assert estimate_sampling_horizon(sp, cs)["warnings"]
