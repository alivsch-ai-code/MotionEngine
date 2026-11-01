"""Lyapunov controllers on the extended KESM (Werling 4.2, Satz 4-7, appendix A.5)."""

import math

import numpy as np
import pytest

from vdsim.stabilization.common import Desired, desired_from_point
from vdsim.stabilization.simulate import run_closed_loop, run_design_loop
from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_curvature
from vdsim.stabilization.werling_kinematic import center_law, kin_tracking_with_orientation_stab, orientation_law
from vdsim.vehicle_models.werling_models import werling_model1, werling_parameters

K = dict(k1=0.5, k2=2.0, k3=2.0, k4=10.0)
KC = dict(k1=0.5, k3=2.0, k4=5.0)


@pytest.fixture
def P(sedan):
    return werling_parameters(sedan)


def stop_and_go(direction=1):
    # Werling 5.2-like stored trajectory: permanent curvature changes, stops of one second
    path = path_from_curvature(lambda s: 0.12 * math.sin(s / 6.0), 90)
    prof = SpeedProfile([(0, 0), (4, 3), (10, 3), (13, 0), (14, 0), (17, 2.5), (24, 2.5), (27, 0), (29, 0)])
    return build_trajectory(path, prof, direction=direction)


def circle_desired(t, R=12.0, v0=1.5, a=0.3, varsigma=1):
    # analytic reference on a circle with constant acceleration (rear axle)
    s = v0 * t + 0.5 * a * t * t
    v = v0 + a * t
    th = s / R
    psi = th if varsigma > 0 else th + math.pi
    return Desired(t=t, x=R * math.sin(th), y=R * (1 - math.cos(th)), psi=psi, kappa=varsigma / R, kappa_dot=0.0,
                   kappa_prime=0.0, v=varsigma * v, v_dot=varsigma * a, varsigma=varsigma, speed=v, theta=th, accel=a)


def test_a5_port_is_identical_to_structured_law(P):
    rng = np.random.default_rng(3)
    for _ in range(200):
        sg = rng.choice([-1, 1])
        d = Desired(x=rng.normal(), y=rng.normal(), psi=rng.uniform(-3, 3), kappa=rng.uniform(-0.15, 0.15),
                    kappa_dot=rng.uniform(-0.05, 0.05), v=sg * rng.uniform(0, 3), v_dot=rng.uniform(-1, 1),
                    varsigma=int(sg))
        d.speed = abs(d.v)
        x1, x2, psi = d.x + rng.normal(0, 0.3), d.y + rng.normal(0, 0.3), d.psi + rng.normal(0, 0.2)
        v, delta = d.v + rng.normal(0, 0.3), rng.uniform(-0.5, 0.5)
        res = orientation_law(d, x1, x2, psi, v, delta, P, **K, gamma_drive=0.3, gamma_brake=0.3, switch=10.0)
        a5 = kin_tracking_with_orientation_stab(d.x, d.y, d.psi, d.kappa, d.kappa_dot, d.v, d.v_dot, d.varsigma, x1,
                                                x2, psi, v, delta, P.lv, P.lh, P.m, P.J, 0.3, **K)
        assert a5[0] == pytest.approx(res["delta_dot"], rel=1e-12, abs=1e-12)
        assert a5[1] == pytest.approx(res["F_l"], rel=1e-12, abs=1e-9)


@pytest.mark.parametrize("varsigma", [1, -1])
def test_lyapunov_satz4_numeric(P, varsigma):
    # V_c_dot along the closed loop equals -s_d_dot k2 e_psi^2 - k3 e_v^2 - k4 e_delta^2 <= 0
    rng = np.random.default_rng(7)
    for _ in range(40):
        t0 = rng.uniform(0, 3)
        d = circle_desired(t0, varsigma=varsigma)
        x0 = np.array([d.x + rng.normal(0, 0.4), d.y + rng.normal(0, 0.4), d.psi + rng.normal(0, 0.3),
                       rng.uniform(-0.4, 0.4), d.v + rng.normal(0, 0.5)])
        law = orientation_law

        def V_at(dtau):
            dd = circle_desired(t0 + dtau, varsigma=varsigma)
            return orientation_law(dd, x[0], x[1], x[2], x[4], x[3], P, **K)["V"]

        res = law(d, x0[0], x0[1], x0[2], x0[4], x0[3], P, **K)
        vals = []
        for h in (-1e-5, 1e-5):
            x = np.array(x0)
            f = lambda xx: werling_model1(xx, res["delta_dot"], res["F_l"], res["gamma"], P)  # noqa: E731
            k1 = f(x)
            k2 = f(x + h / 2 * k1)
            k3 = f(x + h / 2 * k2)
            k4 = f(x + h * k3)
            x = x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            vals.append(V_at(h))
        V_dot = (vals[1] - vals[0]) / 2e-5
        assert V_dot == pytest.approx(res["V_dot"], abs=1e-4 + 1e-4 * abs(res["V_dot"]))
        assert V_dot <= 1e-4


@pytest.mark.parametrize("variant", ["proof", "printed"])
def test_lyapunov_satz6_sign_of_431(P, variant):
    # with the sign of the proof V~_dot = -k4 e_th^2 - k3 e_v^2 <= 0; the printed sign adds 2 k1 e_v e_n sin(e_th),
    # which is indefinite for (k1 e_n)^2 > k3 k4 (here e_n > 6.3 m)
    rng = np.random.default_rng(11)
    pos = 0.5 if variant == "proof" else 8.0
    lam = P.l / 2
    worst = -np.inf
    for _ in range(60):
        t0 = rng.uniform(0, 3)
        d = circle_desired(t0)
        x0 = np.array([d.x + rng.normal(0, pos), d.y + rng.normal(0, pos), d.psi + rng.normal(0, 0.4),
                       rng.uniform(-0.3, 0.3), d.v + rng.normal(0, 0.8)])
        res = center_law(d, x0[0], x0[1], x0[2], x0[4], x0[3], P, **KC, lam=lam, sign_variant=variant)
        vals = []
        for h in (-1e-5, 1e-5):
            x = np.array(x0)
            f = lambda xx: werling_model1(xx, res["delta_dot"], res["F_l"], res["gamma"], P)  # noqa: E731
            k1 = f(x)
            k2 = f(x + h / 2 * k1)
            k3 = f(x + h / 2 * k2)
            k4 = f(x + h * k3)
            x = x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            vals.append(center_law(circle_desired(t0 + h), x[0], x[1], x[2], x[4], x[3], P, **KC, lam=lam,
                                   sign_variant=variant)["V"])
        V_dot = (vals[1] - vals[0]) / 2e-5
        if variant == "proof":
            assert V_dot == pytest.approx(res["V_dot"], abs=1e-4 + 1e-4 * abs(res["V_dot"]))
        worst = max(worst, V_dot)
    if variant == "proof":
        assert worst <= 1e-4
    else:
        assert worst > 1e-2


@pytest.mark.parametrize("controller,direction", [("werling_kinematic_orientation", 1),
                                                  ("werling_kinematic_orientation", -1),
                                                  ("werling_kinematic_center", 1)])
def test_nominal_zero_tracking_error_on_design_model(sedan, controller, direction):
    traj = stop_and_go(direction)
    log = run_design_loop(controller, traj, sedan, duration=28.0, model="werling_kesm")
    assert np.max(np.abs(log["e_n"])) < 0.01 and np.max(np.abs(log["e_t"])) < 0.01
    assert np.max(np.abs(log["e_theta"])) < 0.005


@pytest.mark.parametrize("controller", ["werling_kinematic_orientation", "werling_kinematic_center"])
@pytest.mark.parametrize("curved", [False, True])
def test_convergence_from_initial_errors(sedan, controller, curved):
    path = path_from_curvature((lambda s: 0.06) if curved else (lambda s: 0.0), 80)
    traj = build_trajectory(path, SpeedProfile([(0, 2.0), (25, 2.0)]))
    p0 = traj.sample(0)
    x0 = np.array([p0.x - 0.4, p0.y + 0.8, p0.psi + 0.25, 0.0, 1.5])
    log = run_design_loop(controller, traj, sedan, duration=25.0, model="werling_kesm", x0=x0)
    late = log["t"] > 20
    assert np.max(np.abs(log["e_n"][late])) < 0.02 and np.max(np.abs(log["e_t"][late])) < 0.02
    assert abs(log["e_n"][0]) > 0.5


def test_reverse_driving_satz4_on_plant(sedan):
    traj = stop_and_go(-1)
    p0 = traj.sample(0)
    lh = sedan.vehicle.cg_to_rear
    ego0 = dict(x=p0.x + lh * math.cos(p0.psi), y=p0.y + lh * math.sin(p0.psi), psi=p0.psi, v=0.0,
                delta=-math.atan(sedan.vehicle.wheelbase * p0.kappa))
    log, comps = run_closed_loop("werling_bilevel", traj, sedan, duration=28.0, plant="werling_kesm", ego_initial=ego0)
    assert set(log["active"]) == {"werling_kinematic_orientation"}
    assert np.min(log["vx"]) < -2.0
    assert np.max(np.abs(log["e_n"])) < 0.05 and np.max(np.abs(log["e_t"])) < 0.15


@pytest.mark.parametrize("controller", ["werling_kinematic_orientation", "werling_kinematic_center"])
def test_stop_to_standstill_without_steering_jump(sedan, controller):
    path = path_from_curvature(lambda s: 0.1, 40)
    traj = build_trajectory(path, SpeedProfile([(0, 2.5), (3, 2.5), (8, 0.0), (14, 0.0)]))
    p0 = traj.sample(0)
    x0 = np.array([p0.x, p0.y, p0.psi, math.atan(sedan.vehicle.wheelbase * 0.1), 2.5])
    log = run_design_loop(controller, traj, sedan, duration=14.0, model="werling_kesm", x0=x0)
    assert np.all(np.isfinite(log["steer_rate"])) and np.max(np.abs(log["steer_rate"])) < 0.3
    assert np.max(np.abs(np.diff(log["delta"]))) < 0.003
    still = log["t"] > 11
    assert np.max(np.abs(log["v"][still])) < 1e-3
    assert np.ptp(log["delta"][still]) < 1e-3                 # no drift of the steering at standstill


def test_zero_dynamics_satz7_and_jack_knife(P):
    lam = P.l / 2

    def run(vd, kd, e0, T=40.0, h=0.01):
        e = e0
        for _ in range(int(T / h)):
            e += h * (-vd / lam * (math.sin(e) + lam * kd * (1 - math.cos(e))))      # (4.36)
        return e
    for kd in (-0.3, 0.0, 0.3):
        assert abs(run(2.0, kd, 1.4)) < 1e-3 and abs(run(2.0, kd, -1.4)) < 1e-3
        beta0 = -1.4 - math.atan(lam * kd)
        assert abs(beta0) < 0.75 * math.pi
    assert abs(run(-2.0, 0.0, 0.05, T=5.0)) > 1.0              # reverse: unstable (jack-knife effect)


def test_center_controller_orientation_converges(sedan):
    # Satz 7: only the position is stabilized, the orientation converges through the zero dynamics
    traj = build_trajectory(path_from_curvature(lambda s: 0.03, 80), SpeedProfile([(0, 2.0), (30, 2.0)]))
    p0 = traj.sample(0)
    P = werling_parameters(sedan)
    lam = P.l / 2
    e_psi0 = 0.6
    psi = p0.psi + e_psi0
    # geometric center on the reference, orientation wrong
    pc = (p0.x + lam * math.cos(p0.psi), p0.y + lam * math.sin(p0.psi))
    x0 = np.array([pc[0] - lam * math.cos(psi), pc[1] - lam * math.sin(psi), psi, 0.0, 2.0])
    log = run_design_loop("werling_kinematic_center", traj, sedan, duration=30.0, model="werling_kesm", x0=x0)
    assert abs(log["e_n"][-1]) < 0.02
    psi_d = desired_from_point(traj.sample(log["t"][-1])).psi
    assert abs(math.remainder(log["psi"][-1] - psi_d, 2 * math.pi)) < 0.02
    assert abs(math.remainder(log["psi"][0] - desired_from_point(p0).psi, 2 * math.pi)) > 0.5
