"""Physical plausibility, regression and Monte Carlo tests across the vehicle and tire models.

Each test states the physical law it checks. Regressions covered:
  * nonlinear single-track model ignored the rolling resistance in vx_dot
  * Environment.wind_speed was documented as head wind > 0 but acted as tail wind
  * Pacejka combined slip exceeded the friction circle (up to 37 % at low mu)
  * Scenario.vehicle_overrides silently accepted unknown parameter names
"""

from dataclasses import asdict

import numpy as np
import pytest

from vdsim.analysis import LinearSingleTrackAnalysis
from vdsim.core.conventions import AIR_DENSITY, G
from vdsim.core.parameters import TireParameters, load_vehicle_preset
from vdsim.core.registry import create, get
from vdsim.planning import jerk_integral, quartic_coefficients, quintic_coefficients
from vdsim.planning.polynomials import polyval
from vdsim.simulation.environment import Environment
from vdsim.simulation.scenario import Scenario
from vdsim.simulation.solver import create_solver
from vdsim.simulation.vehicle_state import ControlInput

PLANAR_MODELS = ["bicycle_kinematic", "bicycle_linear", "bicycle_nonlinear", "double_track", "multibody"]
WHEEL_MODELS = {"double_track", "multibody"}
TIRES = ["linear", "pacejka", "brush", "isotropic"]


@pytest.fixture(scope="module")
def sedan():
    return load_vehicle_preset("mid_size_sedan")


def _resistance(p, v, wind=0.0):
    v_air = v + wind
    return 0.5 * AIR_DENSITY * p.drag_coefficient * p.frontal_area * v_air * abs(v_air) \
        + p.rolling_resistance * p.mass * G * np.tanh(v / 0.5)


def _coast(model, env, v0=30.0, t_end=2.0, dt=1e-3):
    s = model.initial_state(speed=v0)
    solver = create_solver("rk4")
    u = ControlInput()
    for k in range(int(round(t_end / dt))):
        s = solver.step(lambda t, x: model.derivatives(t, x, u, env), k * dt, s, dt)
    _, out = model.derivatives(t_end, s, u, env, with_outputs=True)
    return s, out


# ----------------------------------------------------------------------------- driving resistances
@pytest.mark.parametrize("name", PLANAR_MODELS)
def test_coastdown_deceleration_equals_driving_resistance(sedan, name):
    # m_eff a = -(F_aero + F_roll); rotating wheels add 4 J_w / R^2 to the translational mass
    model = create("vehicle_model", name, sedan)
    s, out = _coast(model, Environment())
    p = sedan.vehicle
    v = s[3]
    m_eff = p.mass + (4 * p.wheel_inertia / p.wheel_radius ** 2 if name in WHEEL_MODELS else 0.0)
    assert out["ax"] == pytest.approx(-_resistance(p, v) / m_eff, rel=0.01)


@pytest.mark.parametrize("name", PLANAR_MODELS)
def test_head_wind_is_positive_wind_speed(sedan, name):
    # Environment.wind_speed > 0 is head wind: air speed vx + w, more drag than in still air
    model = create("vehicle_model", name, sedan)
    a = {}
    for wind in (-10.0, 0.0, 10.0):
        _, out = _coast(model, Environment(wind_speed=wind), t_end=0.5)
        a[wind] = out["ax"]
    assert a[10.0] < a[0.0] < a[-10.0] < 0.0


@pytest.mark.parametrize("name", PLANAR_MODELS)
def test_coasting_never_gains_kinetic_energy(sedan, name):
    model = create("vehicle_model", name, sedan)
    s = model.initial_state(speed=25.0)
    solver = create_solver("rk4")
    u = ControlInput(steer_front=0.02)
    env = Environment()
    speeds = []
    for k in range(1500):
        s = solver.step(lambda t, x: model.derivatives(t, x, u, env), k * 2e-3, s, 2e-3)
        speeds.append(np.hypot(s[3], s[4]) if len(s) > 4 else s[3])
    speeds = np.array(speeds)
    assert np.all(np.isfinite(speeds)) and np.all(np.diff(speeds) <= 1e-6)


# ----------------------------------------------------------------------------- symmetry
@pytest.mark.parametrize("name", PLANAR_MODELS)
def test_left_right_mirror_symmetry(sedan, name):
    # mirroring y -> -y must mirror the lateral states (ISO 8855: steer left > 0, yaw left > 0)
    model = create("vehicle_model", name, sedan)
    s0 = model.initial_state(speed=20.0)
    env = Environment()
    d_left = model.derivatives(0.0, s0, ControlInput(steer_front=0.05), env)
    d_right = model.derivatives(0.0, s0, ControlInput(steer_front=-0.05), env)
    lateral = [1, 2] + ([4, 5] if len(s0) > 4 else [])
    assert d_left[2] > 0.0 or name != "bicycle_kinematic"
    assert np.allclose(d_left[lateral], -d_right[lateral], rtol=1e-9, atol=1e-9)
    assert d_left[0] == pytest.approx(d_right[0], rel=1e-9, abs=1e-12)


# ----------------------------------------------------------------------------- tires
def _tire(name):
    kw = asdict(TireParameters())
    kw.pop("model")
    kw["cornering_stiffness"] = kw.pop("cornering_stiffness_front")
    kw.pop("cornering_stiffness_rear")
    return get("tire_model", name)(**kw)


@pytest.mark.parametrize("name", TIRES)
def test_tire_force_within_friction_circle_monte_carlo(name):
    # |F| <= mu_eff(Fz) Fz for random combined slip, load and friction (Kamm's circle)
    rng = np.random.default_rng(42)
    n = 100_000
    alpha, kappa = rng.uniform(-0.6, 0.6, n), rng.uniform(-1.0, 1.0, n)
    fz, mu = rng.uniform(300.0, 9000.0, n), rng.uniform(0.1, 1.3, n)
    tire = _tire(name)
    fx, fy, _ = tire.forces(alpha, kappa, fz, mu)
    if name in ("pacejka", "brush"):
        grip = mu * np.maximum(1.0 + tire.p_mu * (fz - tire.fz0) / tire.fz0, 0.2) * fz
    else:
        grip = mu * fz
    assert np.max(np.hypot(fx, fy) / grip) <= 1.0 + 1e-9


@pytest.mark.parametrize("name", TIRES)
def test_tire_sign_convention_and_odd_symmetry(name):
    # conventions.py: positive slip angle -> positive lateral force; positive kappa (driving) -> positive Fx
    tire = _tire(name)
    a = np.linspace(-0.3, 0.3, 61)
    _, fy_p, mz_p = tire.forces(a, 0.0 * a, 4000.0)
    _, fy_n, mz_n = tire.forces(-a, 0.0 * a, 4000.0)
    assert np.allclose(fy_p, -fy_n) and np.allclose(mz_p, -mz_n)
    assert np.all(fy_p[a > 0] > 0)
    fx, _, _ = tire.forces(np.zeros(5), np.array([0.01, 0.05, 0.1, -0.05, -0.1]), 4000.0)
    assert np.all(fx[:3] > 0) and np.all(fx[3:] < 0)
    # aligning moment opposes the slip angle in the linear range
    assert np.all(mz_p[(a > 0) & (a < 0.05)] < 0)


@pytest.mark.parametrize("name", ["pacejka", "brush", "isotropic", "linear"])
def test_tire_small_slip_stiffness(name):
    # dFy/dalpha at alpha = 0 and nominal load equals the cornering stiffness parameter
    tire = _tire(name)
    h = 1e-6
    _, fy, _ = tire.forces(h, 0.0, tire_nominal_load(), 1.0)
    assert float(fy) / h == pytest.approx(TireParameters().cornering_stiffness_front, rel=1e-3)


def tire_nominal_load():
    return TireParameters().nominal_load


# ----------------------------------------------------------------------------- Monte Carlo on parameters
def test_monte_carlo_linear_model_matches_theory():
    # randomized vehicles (+-20 %): the simulated steady state equals the closed-form linear gains
    rng = np.random.default_rng(7)
    base = load_vehicle_preset("mid_size_sedan")
    for _ in range(8):
        cfg = load_vehicle_preset("mid_size_sedan")
        for attr in ("mass", "inertia_z"):
            setattr(cfg.vehicle, attr, getattr(base.vehicle, attr) * rng.uniform(0.8, 1.2))
        cfg.vehicle.cg_to_front = base.vehicle.wheelbase * rng.uniform(0.40, 0.55)
        cfg.tires.cornering_stiffness_rear = base.tires.cornering_stiffness_rear * rng.uniform(0.9, 1.2)
        lin = LinearSingleTrackAnalysis(cfg)
        v = rng.uniform(10.0, 35.0)
        if lin.understeer_gradient < 0 and v > 0.8 * lin.critical_speed:
            continue
        model = create("vehicle_model", "bicycle_linear", cfg)
        s = model.initial_state(speed=v)
        u = ControlInput(steer_front=0.01)
        a, b = model.state_space(v)
        vy_r = -np.linalg.solve(a, b[:, 0] * u.steer_front)
        # steady state of the lateral subsystem: derivatives vanish at the closed-form solution
        s[4], s[5] = vy_r
        ds = model.derivatives(0.0, s, u, Environment())
        assert abs(ds[4]) < 1e-9 and abs(ds[5]) < 1e-9
        assert vy_r[1] / u.steer_front == pytest.approx(lin.steady_state_gains(v)["yaw_rate"], rel=1e-9)
        assert np.all(np.linalg.eigvals(a).real < 0)


# ----------------------------------------------------------------------------- polynomials (Werling 3.4)
def test_monte_carlo_quintic_boundary_conditions_and_jerk_integral():
    rng = np.random.default_rng(3)
    n = 500
    x0, v0, a0, x1, v1, a1 = (rng.uniform(-20, 20, n) for _ in range(6))
    tau = rng.uniform(0.5, 8.0, n)
    c = quintic_coefficients(x0, v0, a0, x1, v1, a1, tau)
    p, p1, p2, _ = polyval(c, np.stack([np.zeros(n), tau], axis=1))
    assert np.allclose(p[:, 0], x0) and np.allclose(p1[:, 0], v0) and np.allclose(p2[:, 0], a0)
    assert np.allclose(p[:, 1], x1) and np.allclose(p1[:, 1], v1) and np.allclose(p2[:, 1], a1)
    # closed-form jerk integral against Gauss-Legendre quadrature (exact for the degree-4 integrand)
    xg, wg = np.polynomial.legendre.leggauss(5)
    tg = 0.5 * tau[:, None] * (xg[None, :] + 1.0)
    _, _, _, j = polyval(c, tg)
    numeric = 0.5 * tau * np.sum(wg[None, :] * j ** 2, axis=1)
    assert np.allclose(jerk_integral(c, tau), numeric, rtol=1e-9, atol=1e-9)


def test_quintic_is_jerk_optimal():
    # Werling Satz 1: adding any perturbation that vanishes with its first two derivatives at both
    # ends (t^3 (tau - t)^3) increases int jerk^2; the integrals are evaluated exactly
    from numpy.polynomial import Polynomial as P
    tau = 4.0
    c = quintic_coefficients(0.0, 10.0, 0.0, 3.5, 10.0, 0.0, tau)
    base = float(jerk_integral(c[None], tau)[0])
    bump = P([0, 0, 0, 1]) * P([tau, -1]) ** 3
    for eps in (-0.1, -1e-3, 1e-3, 0.1):
        jerk = (P(c) + eps * bump).deriv(3)
        cost = float((jerk ** 2).integ()(tau))
        assert cost > base
    assert float((P(c).deriv(3) ** 2).integ()(tau)) == pytest.approx(base, rel=1e-12)


def test_quartic_end_velocity_and_acceleration():
    rng = np.random.default_rng(5)
    n = 300
    x0, v0, a0, v1, a1 = (rng.uniform(-10, 10, n) for _ in range(5))
    tau = rng.uniform(0.5, 8.0, n)
    c = quartic_coefficients(x0, v0, a0, v1, a1, tau)
    _, p1, p2, _ = polyval(c, tau[:, None])
    assert np.allclose(p1[:, 0], v1) and np.allclose(p2[:, 0], a1) and np.all(c[:, 5] == 0.0)


# ----------------------------------------------------------------------------- configuration safety
def test_unknown_vehicle_override_is_rejected():
    with pytest.raises(AttributeError):
        Scenario(vehicle_overrides={"tires.mue": 0.5}).build_config()
    cfg = Scenario(vehicle_overrides={"tires.mu": 0.5}).build_config()
    assert cfg.tires.mu == 0.5


def test_config_dir_override(monkeypatch, tmp_path):
    from vdsim.core.parameters import default_config_dir
    monkeypatch.setenv("MOTIONENGINE_CONFIG_DIR", str(tmp_path))
    assert default_config_dir() == tmp_path
    monkeypatch.delenv("MOTIONENGINE_CONFIG_DIR")
    assert (default_config_dir() / "vehicles" / "mid_size_sedan.json").exists()
