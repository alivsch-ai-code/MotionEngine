"""Werling design models (KESM, DESM) as vdsim vehicle models and the isotropic tire (Werling 4.2.1, 4.3.1, 4.3.2)."""

import math

import numpy as np
import pytest

from vdsim.analysis import LinearSingleTrackAnalysis
from vdsim.core.registry import available, create
from vdsim.simulation.environment import Environment
from vdsim.simulation.vehicle_state import ControlInput
from vdsim.tire_models.isotropic import force_magnitude, lateral_force, peak_slip, slip_for_force
from vdsim.vehicle_models.werling_models import desm_forces, werling_model1, werling_model4, werling_parameters


@pytest.fixture
def P(sedan):
    return werling_parameters(sedan)


def test_models_registered():
    assert {"werling_kesm", "werling_desm"} <= set(available("vehicle_model"))
    assert "isotropic" in available("tire_model")


def test_kesm_lagrange_and_singularity_free(P):
    # Euler-Lagrange equation of the derivation: s_dd (m + M tan^2 delta) + 2 M v delta_dot tan(delta)/cos^2 = Q,
    # i.e. power balance E_dot = Q v - M v^2 tan(delta) delta_dot / cos^2 (rheonomic steering constraint)
    rng = np.random.default_rng(1)
    for _ in range(50):
        delta, v = rng.uniform(-0.5, 0.5), rng.uniform(-3, 3)
        u1, u2, gam = rng.uniform(-0.3, 0.3), rng.uniform(-3000, 3000), rng.uniform(0, 1)
        x = np.array([0.0, 0.0, 0.3, delta, v])
        dx = werling_model1(x, u1, u2, gam, P)
        t = math.tan(delta)
        E_dot = v * dx[4] * (P.m + P.M * t * t) + 0.5 * v * v * 2 * P.M * t / math.cos(delta) ** 2 * u1
        Q = u2 * (1 + gam * (1 / math.cos(delta) - 1))
        assert E_dot == pytest.approx(Q * v - P.M * v * v * t * u1 / math.cos(delta) ** 2, rel=1e-9, abs=1e-6)
    dx = werling_model1(np.array([0, 0, 0, 0.4, 0.0]), 0.2, 1000.0, 0.0, P)
    assert np.all(np.isfinite(dx)) and dx[4] == pytest.approx(1000.0 / (P.m + P.M * math.tan(0.4) ** 2))


def test_kesm_plant_reverses_and_holds_at_standstill(sedan):
    m = create("vehicle_model", "werling_kesm", sedan)
    env = Environment()
    x = m.initial_state(0, 0, 0, 0.0)
    u = ControlInput(steer_front=0.3, drive_torque=np.array([0, 0, -300.0, -300.0]))
    for _ in range(300):
        x = x + 0.01 * m.derivatives(0, x, u, env)
    assert x[4] < -0.5 and x[0] < 0                      # drives backwards
    x[4] = 0.0
    u = ControlInput(steer_front=0.3, brake_torque=np.full(4, 500.0))
    for _ in range(100):
        x = x + 0.01 * m.derivatives(0, x, u, env)
    assert abs(x[4]) < 1e-9                                # brakes hold, no creeping


def test_desm_matches_model4_and_linear_gain(run, sedan, P):
    # vx/vy plant form equals model 4 in (beta, v) coordinates
    x4 = np.array([0, 0, 0.2, 0.15, 0.02, 20.0])
    d4 = werling_model4(x4, 0.03, 500.0, 0.0, P)
    vx, vy = 20 * math.cos(0.02), 20 * math.sin(0.02)
    Fx, Fy, Mz, _ = desm_forces(vx, vy, 0.15, 0.03, 0.0, 500.0, P)
    beta_dot = ((Fy / P.m - 0.15 * vx) * math.cos(0.02) - (Fx / P.m + 0.15 * vy) * math.sin(0.02)) / 20.0
    assert d4[3] == pytest.approx(Mz / P.J) and d4[4] == pytest.approx(beta_dot, rel=1e-9)
    # old simulator, step steer in the linear range: yaw gain of the linear single-track model
    result, _ = run(model="werling_desm", maneuver="step_steer",
                    maneuver_params={"steering_wheel_deg": 15, "speed_kmh": 80})
    tail = result["t"] > result["t"][-1] - 1.0
    gain = np.mean(result["r"][tail]) / np.mean(result["delta_f"][tail])
    assert gain == pytest.approx(LinearSingleTrackAnalysis(sedan).steady_state_gains(80 / 3.6)["yaw_rate"], rel=0.03)


def test_kesm_runs_in_old_simulator(run):
    result, sim = run(model="werling_kesm", maneuver="iso_double_lane_change", maneuver_params={"speed_kmh": 30})
    assert np.all(np.isfinite(result["x"])) and np.max(np.abs(result["lateral_error"])) < 0.5


def test_desm_standstill_and_low_speed(sedan):
    m = create("vehicle_model", "werling_desm", sedan)
    env = Environment()
    x = m.initial_state(0, 0, 0, 0.0, delta=0.4)
    u = ControlInput(steer_front=0.4)
    dx = m.derivatives(0, x, u, env)
    assert np.allclose(dx[:6], 0.0, atol=1e-9)          # steering at standstill: no motion
    u = ControlInput(steer_front=0.4, drive_torque=np.array([0, 0, 200.0, 200.0]))
    for _ in range(400):
        x = x + 0.005 * m.derivatives(0, x, u, env)
    assert np.all(np.isfinite(x)) and x[3] > 0.5
    assert x[5] == pytest.approx(x[3] * math.tan(x[6]) / m.P.l, rel=0.1)   # kinematic at low speed


def test_isotropic_tire_inversion(P):
    A, B, C = P.Av, P.Bv, P.Cv
    s_max = peak_slip(B, C)
    assert force_magnitude(s_max, A, B, C, "none") == pytest.approx(A)
    assert A * B * C == pytest.approx(P.cv)
    # forward (4.40) -> inverse g(F_q) = 0 (4.43)
    for s_l, s_q in ((0.0, 0.05), (0.03, 0.04), (-0.05, -0.02), (0.08, 0.06)):
        S = math.hypot(s_l, s_q)
        F = A * math.sin(B * math.atan(C * S))
        Fq, S_found, sat = lateral_force(s_q, F * s_l / S, A, B, C, "plateau")
        assert not sat and Fq == pytest.approx(F * s_q / S, rel=1e-8) and S_found == pytest.approx(S, rel=1e-6)
    assert slip_for_force(force_magnitude(0.05, A, B, C, "none"), A, B, C) == pytest.approx(0.05)
    # longitudinal force weakens the lateral force (Abb. 4.8b)
    assert abs(lateral_force(0.05, 0.6 * A, A, B, C)[0]) < abs(lateral_force(0.05, 0.0, A, B, C)[0])


def test_isotropic_tire_saturation(P):
    A, B, C = P.Av, P.Bv, P.Cv
    s_max = peak_slip(B, C)
    # plateau (plant): Kamm's circle beyond the peak
    Fq, _, sat = lateral_force(1.5 * s_max, 0.5 * A, A, B, C, "plateau")
    assert sat and Fq == pytest.approx(math.sqrt(A * A - 0.25 * A * A))
    # footnote 17: modified characteristic always invertible below s_max, any F_l < A
    Fq, S, sat = lateral_force(0.9 * s_max, 0.95 * A, A, B, C, "modified")
    assert not sat and S < s_max and Fq > 0
    assert force_magnitude(0.999 * s_max, A, B, C, "modified") > 10 * A
    assert force_magnitude(0.3 * s_max, A, B, C, "modified") == pytest.approx(force_magnitude(0.3 * s_max, A, B, C,
                                                                                                "none"), rel=1e-6)
