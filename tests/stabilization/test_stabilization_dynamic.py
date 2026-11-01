"""Exact I/O linearization on the DESM with isotropic tire (Werling 4.3, Satz 8, Satz 9, (4.70)-(4.75))."""

import math

import numpy as np
import pytest

from vdsim.controllers.esp_controller import understeer_gradient
from vdsim.framework.types import TrajectoryPoint
from vdsim.stabilization.simulate import run_closed_loop, run_design_loop
from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_lateral_offset
from vdsim.stabilization.werling_dynamic import (ZeroDynamicsReference, _required_point_acceleration,
                                                 lookahead_for_damping, minimum_phase_bound, point_kinematics,
                                                 solve_linearizing_input, zero_dynamics_coefficients)
from vdsim.stabilization.errors import frenet_errors
from vdsim.vehicle_models.werling_models import desm_forces, werling_parameters


@pytest.fixture
def P(sedan):
    return werling_parameters(sedan)


def evasive(v=30.0, duration=11.0):
    path = path_from_lateral_offset([(60, 50, 3.5), (140, 50, -3.5)], 30 * duration + 50)
    return build_trajectory(path, SpeedProfile([(0, v), (duration, v)]), reference_point="cog")


def test_lambda_formula_gives_constant_damping(P):
    for zeta in (0.75, 1.0, 1.25):
        lams = []
        for v in (15.0, 20.0, 30.0, 40.0):
            lam = lookahead_for_damping(zeta, v, P)
            assert math.isfinite(lam) and lam > minimum_phase_bound(P)
            assert zero_dynamics_coefficients(lam, v, P)[2] == pytest.approx(zeta, rel=1e-9)
            lams.append(lam)
        assert np.all(np.diff(lams) > 0)                  # look-ahead grows with the speed (Abb. 4.10)
    assert lookahead_for_damping(1.0, 30.0, P) == pytest.approx(11.0, abs=1.0)
    # low speed: the damping exceeds zeta already for lambda = 0 -> no (or a negative) solution
    lam = lookahead_for_damping(1.0, 3.0, P)
    assert not math.isfinite(lam) or lam < 0.0


def test_satz9_minimum_phase_condition(P):
    bound = minimum_phase_bound(P)
    assert bound == pytest.approx(max(-P.lh, -P.J / (P.lv * P.m)))
    for lam in (bound + 0.05, 0.0, 2.0, 15.0):
        p0, p1, _ = zero_dynamics_coefficients(lam, 25.0, P)
        assert p0 > 0 and p1 > 0
        assert np.all(np.real(np.linalg.eigvals([[0, 1], [-p0, -p1]])) < 0)
    p0, p1, _ = zero_dynamics_coefficients(bound - 0.1, 25.0, P)
    assert min(p0, p1) < 0


@pytest.mark.parametrize("lam,stable", [(3.0, True), (-1.45, False)])
def test_satz9_closed_loop_zero_dynamics(sedan, lam, stable):
    # errors held at zero by the controller, the yaw motion follows the zero dynamics (4.67)
    traj = build_trajectory(path_from_lateral_offset([], 500), SpeedProfile([(0, 20.0), (8, 20.0)]),
                            reference_point="cog")
    p0 = traj.sample(0)
    psi0 = 0.01
    x0 = np.array([p0.x - lam * math.cos(psi0) + lam, p0.y - lam * math.sin(psi0), psi0, 20.0, 0.0, 0.0, 0.0])
    log = run_design_loop("werling_dynamic", traj, sedan, duration=4.0, model="werling_desm", x0=x0,
                          controller_params={"lam_fixed": lam, "reference_transform": "none"})
    psi = log["psi"]
    if stable:
        assert abs(psi[-1]) < 0.2 * psi0
    else:
        assert not np.all(np.isfinite(psi)) or np.max(np.abs(psi)) > 10 * psi0


def test_linearizing_feedback_achieves_w(P):
    # e_dd = w~ for the circle reference (equivalent formulation of (4.60)), checked by finite differences
    R, V, lam = 150.0, 25.0, 6.0

    def ref(t):
        th = V * t / R
        return {"y1": R * math.sin(th), "y2": R * (1 - math.cos(th)), "theta": th, "kappa": 1 / R, "v": V,
                "v_dot": 0.0}
    x = np.array([2.0, 1.2, 0.03, 24.0, 0.3, 0.17])     # x, y, psi, vx, vy, r
    w = (0.4, -0.8)                                       # (w~2, w~1)

    def errors(xx, t):
        bt = math.atan((xx[4] + lam * xx[5]) / xx[3])
        r_ = ref(t)
        e = frenet_errors(xx[0] + lam * math.cos(xx[2]), xx[1] + lam * math.sin(xx[2]), xx[2] + bt,
                          xx[3] / math.cos(bt), r_["y1"], r_["y2"], r_["theta"], r_["v"], r_["kappa"])
        return e
    e = errors(x, 0.0)
    a_req = _required_point_acceleration(ref(0.0), (e["e_t"], e["e_n"]), (e["e_t_dot"], e["e_n_dot"]), w,
                                         V / R, 0.0, x[2])
    delta, F, info = solve_linearizing_input(x[3], x[4], x[5], lam, a_req, P, (0.0, 0.75))
    assert info["converged"] and not info["saturated"]

    def f(xx):
        g = 0.0 if F >= 0 else 0.75
        Fx, Fy, Mz, _ = desm_forces(xx[3], xx[4], xx[5], delta, g * F, (1 - g) * F, P)
        c, s = math.cos(xx[2]), math.sin(xx[2])
        return np.array([xx[3] * c - xx[4] * s, xx[3] * s + xx[4] * c, xx[5], Fx / P.m + xx[5] * xx[4],
                         Fy / P.m - xx[5] * xx[3], Mz / P.J])

    def step(xx, h):
        k1 = f(xx)
        k2 = f(xx + h / 2 * k1)
        k3 = f(xx + h / 2 * k2)
        k4 = f(xx + h * k3)
        return xx + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    h = 1e-3
    ep, em = errors(step(x, h), h), errors(step(x, -h), -h)
    for key, wk in (("e_t", w[0]), ("e_n", w[1])):
        assert (ep[key] - 2 * e[key] + em[key]) / h**2 == pytest.approx(wk, abs=2e-3)


def test_tire_inversion_with_saturation(P):
    vx, vy, r = 20.0, 0.0, 0.0
    # moderate demand: exact inversion
    delta, F, info = solve_linearizing_input(vx, vy, r, 0.0, (0.5, 3.0), P, (0.0, 0.75))
    assert info["converged"] and not info["saturated"] and info["residual"] < 1e-6
    # demand far beyond the friction limit: steering angle at the lateral force optimum
    delta, F, info = solve_linearizing_input(vx, vy, r, 0.0, (0.0, 25.0), P, (0.0, 0.75))
    assert info["saturated"]
    s_opt = P.s_max_v * math.sqrt(1 - (info["gamma"] * F / P.Av) ** 2)
    assert abs(math.sin(info["alpha_v"])) == pytest.approx(s_opt, rel=1e-6)
    assert abs(info["F_vq"]) == pytest.approx(math.sqrt(P.Av**2 - (info["gamma"] * F) ** 2), rel=1e-3)


def test_point_kinematics_consistency():
    v, beta, r, lam = 20.0, 0.02, 0.2, 5.0
    bt, vt, _, _ = point_kinematics(v, beta, r, lam)
    assert vt * math.cos(bt) == pytest.approx(v * math.cos(beta))                # (4.51)
    assert vt * math.sin(bt) == pytest.approx(v * math.sin(beta) + lam * r)        # rigid body


def test_zero_dynamics_reference_steady_state_circle(sedan, P):
    # reference vehicle on a circle: r0 -> v kappa, delta0 -> l kappa + EG v^2 kappa (linear range)
    zd = ZeroDynamicsReference(P, (0.0, 0.75))
    zd.initialize(0.0, 0.0, 0.0)
    v, kappa = 20.0, 1 / 200.0
    pt = TrajectoryPoint(x=0, y=0, theta=0.0, kappa=kappa, v=v)
    for _ in range(600):
        r_dot, b_dot, *_ = zd.derivatives(pt, zd.r0, zd.beta0)
        zd.r0 += 0.005 * r_dot
        zd.beta0 += 0.005 * b_dot
    ref = zd.reference(pt, 0.0)
    assert zd.r0 == pytest.approx(v * kappa, rel=1e-3)
    eg = understeer_gradient(sedan)
    assert ref["delta0"] == pytest.approx(P.l * kappa + eg * v * v * kappa, rel=0.05)


def test_nominal_tracking_on_design_model(sedan):
    log = run_design_loop("werling_dynamic", evasive(), sedan, duration=10.0, model="werling_desm")
    assert np.max(np.abs(log["e_n"])) < 0.03 and np.max(np.abs(log["e_t"])) < 0.03


def test_reference_transformation_removes_lag_error_at_30ms(sedan):
    traj = evasive()
    p0 = traj.sample(0)
    res = {}
    for mode in ("dynamic", "static", "none"):
        log, comps = run_closed_loop("werling_dynamic", traj, sedan, duration=10.0, plant="werling_desm",
                                     controller_params={"reference_transform": mode},
                                     ego_initial=dict(x=p0.x, y=p0.y, psi=p0.theta, v=30.0))
        res[mode] = (np.max(np.abs(log["e_n"])), np.max(np.abs(log["lookahead"])))
    assert res["dynamic"][0] < 0.1
    assert res["dynamic"][1] > 8.0                     # large look-ahead at 30 m/s (4.70)
    assert res["static"][0] > 2.0 * res["dynamic"][0]
    assert res["none"][0] > 4.0 * res["dynamic"][0]
