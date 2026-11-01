"""Numerical validation tests for MotionEngine.

These tests verify physical and mathematical correctness against known analytical
solutions. They serve as regression tests for the simulation's numerical accuracy.

References:
    - Rajamani (2012): Vehicle Dynamics and Control
    - Werling (2011): Optimal Trajectory Generation for Dynamic Street Scenarios
    - Pacejka (2012): Tire and Vehicle Dynamics
"""

import numpy as np
import pytest

from vdsim.core.parameters import load_vehicle_preset


class TestQuinticPolynomials:
    """Verify quintic polynomial coefficients match Werling (2011) eq. 3.6-3.8."""

    def test_boundary_conditions_satisfied(self):
        from vdsim.planning.polynomials import polyval, quintic_coefficients

        c = quintic_coefficients(0.0, 10.0, 0.0, 50.0, 15.0, 0.0, 5.0)
        vals_0 = polyval(c[None, :], np.array([[0.0]]))
        vals_T = polyval(c[None, :], np.array([[5.0]]))
        assert vals_0[0][0, 0] == pytest.approx(0.0, abs=1e-10)
        assert vals_0[1][0, 0] == pytest.approx(10.0, abs=1e-10)
        assert vals_0[2][0, 0] == pytest.approx(0.0, abs=1e-10)
        assert vals_T[0][0, 0] == pytest.approx(50.0, abs=1e-10)
        assert vals_T[1][0, 0] == pytest.approx(15.0, abs=1e-10)
        assert vals_T[2][0, 0] == pytest.approx(0.0, abs=1e-10)

    def test_jerk_integral_positive(self):
        from vdsim.planning.polynomials import jerk_integral, quintic_coefficients

        c = quintic_coefficients(0.0, 10.0, 0.0, 80.0, 20.0, 0.0, 8.0)
        cost = jerk_integral(c, 8.0)
        assert float(cost) > 0


class TestFrenetTransformConsistency:
    """Verify Frenet <-> Cartesian roundtrip (Werling 2011, Appendix A)."""

    def test_roundtrip_straight_road(self):
        from vdsim.geometry.reference_line import ReferenceLine

        line = ReferenceLine.straight(200.0, ds=0.5)
        x0, y0, theta0, v0, a0 = 80.0, 2.5, 0.03, 25.0, -0.5
        fs = line.to_frenet(x0, y0, theta0, 0.0, v0, a0)
        cart = line.to_cartesian(fs.s, fs.s_d, fs.s_dd, fs.d, fs.d_p, fs.d_pp)
        assert cart["x"] == pytest.approx(x0, abs=0.05)
        assert cart["y"] == pytest.approx(y0, abs=0.05)
        assert cart["v"] == pytest.approx(v0, abs=0.05)
        assert cart["a"] == pytest.approx(a0, abs=0.1)

    def test_roundtrip_curved_road(self):
        from vdsim.geometry.reference_line import ReferenceLine

        line = ReferenceLine.from_segments(
            [("straight", 50), ("arc", 100, 0.01), ("straight", 50)], ds=0.5
        )
        x_ref, y_ref, th_ref, _, _ = line.evaluate(100.0)
        d_offset = 1.5
        x0 = float(x_ref - d_offset * np.sin(th_ref))
        y0 = float(y_ref + d_offset * np.cos(th_ref))
        fs = line.to_frenet(x0, y0, th_ref, 0.01, 20.0, 0.0)
        assert fs.d == pytest.approx(d_offset, abs=0.1)
        cart = line.to_cartesian(fs.s, fs.s_d, fs.s_dd, fs.d, fs.d_p, fs.d_pp)
        assert cart["x"] == pytest.approx(x0, abs=0.1)
        assert cart["y"] == pytest.approx(y0, abs=0.1)


class TestLinearBicycleYawGain:
    """Verify steady-state yaw rate gain against Rajamani (2012) eq. 2.34."""

    def test_understeer_gradient(self):
        from vdsim.analysis import LinearSingleTrackAnalysis

        config = load_vehicle_preset("mid_size_sedan")
        analysis = LinearSingleTrackAnalysis(config)
        p, model = config.vehicle, analysis.model
        length, lf, lr = p.wheelbase, p.cg_to_front, p.cg_to_rear
        understeer = (p.mass / length) * (lr / model.c_front - lf / model.c_rear)
        assert understeer > 0
        v = 20.0
        A, B = model.state_space(v)
        _, yaw_rate = -np.linalg.solve(A, B[:, 0])
        assert yaw_rate == pytest.approx(v / (length + understeer * v**2), rel=1e-9)


class TestTireModelSaturation:
    """Verify tire models saturate at the friction limit."""

    def test_linear_tire_friction_circle(self):
        from vdsim.tire_models import create_tire_set

        config = load_vehicle_preset("mid_size_sedan")
        tires = create_tire_set(config.tires)
        fz = np.array([4000.0, 4000.0, 3000.0, 3000.0])
        mu = np.ones(4)
        alpha = np.array([0.3, 0.3, 0.3, 0.3])
        kappa = np.zeros(4)
        camber = np.zeros(4)
        fx, fy, _ = tires.forces(alpha, kappa, fz, mu, camber)
        total_force = np.sqrt(fx**2 + fy**2)
        max_force = mu * fz
        assert np.all(total_force <= max_force * 1.01)

    def test_combined_slip_within_friction_ellipse(self):
        from vdsim.tire_models import create_tire_set

        config = load_vehicle_preset("mid_size_sedan")
        tires = create_tire_set(config.tires)
        fz = np.full(4, 5000.0)
        mu = np.ones(4)
        alpha = np.full(4, 0.1)
        kappa = np.full(4, 0.08)
        camber = np.zeros(4)
        fx, fy, _ = tires.forces(alpha, kappa, fz, mu, camber)
        total_force = np.sqrt(fx**2 + fy**2)
        max_force = mu * fz
        assert np.all(total_force <= max_force * 1.05)


class TestSolverConvergence:
    """Verify that reducing the step size improves accuracy (order of convergence)."""

    def test_rk4_fourth_order(self):
        from vdsim.simulation.solver import RK4Solver

        def f(t, x):
            return -x

        exact = np.exp(-1.0)
        x0 = np.array([1.0])
        errors = []
        for n in [10, 20, 40, 80]:
            s = RK4Solver(substeps=n)
            result = s.step(f, 0.0, x0, 1.0)
            errors.append(abs(result[0] - exact))

        for i in range(1, len(errors)):
            ratio = errors[i - 1] / max(errors[i], 1e-16)
            assert ratio > 12


class TestSpeedHolding:
    """Verify the closed loop holds the requested speed through a lane change."""

    @pytest.mark.slow
    def test_kinematic_model_holds_maneuver_speed(self):
        from vdsim.simulation.scenario import Scenario
        from vdsim.simulation.simulator import Simulator

        scenario = Scenario(
            name="constant_speed_test",
            model="bicycle_kinematic",
            maneuver_params={"speed_kmh": 72.0},
            initial_speed=20.0,
            duration=5.0,
        )
        sim = Simulator.from_scenario(scenario)
        result = sim.run()
        assert np.all(np.abs(np.asarray(result["vx"]) - 20.0) < 0.5)


class TestDimensionalConsistency:
    """Verify physical dimensions are consistent (no unit errors in equations)."""

    def test_tire_force_dimensions(self):
        from vdsim.tire_models import create_tire_set

        config = load_vehicle_preset("mid_size_sedan")
        tires = create_tire_set(config.tires)
        fz = np.array([5000.0, 5000.0, 4000.0, 4000.0])
        mu = np.ones(4)
        alpha = np.array([0.05, 0.05, 0.05, 0.05])
        kappa = np.zeros(4)
        fx, fy, mz = tires.forces(alpha, kappa, fz, mu, np.zeros(4))
        assert np.all(np.abs(fx) < 1e5)
        assert np.all(np.abs(fy) < 1e5)
        assert np.all(np.abs(mz) < 1e4)

    def test_vehicle_state_units(self):
        config = load_vehicle_preset("mid_size_sedan")
        p = config.vehicle
        assert 500 < p.mass < 5000
        assert 1 < p.wheelbase < 5
        assert 0.2 < p.wheel_radius < 0.6
        assert 0.1 < p.cg_height < 1.5
