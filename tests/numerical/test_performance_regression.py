"""Performance regression tests for MotionEngine.

These tests verify that core operations complete within acceptable time limits.
They are NOT benchmarks (those are in benchmarks/) — these are CI gates that
catch severe performance regressions early.

Marked with @pytest.mark.benchmark so they can be run separately.
"""

import time

import numpy as np
import pytest

from vdsim.core.parameters import load_vehicle_preset


@pytest.mark.benchmark
class TestTrajectoryPerformance:
    """Trajectory generation must stay under real-time limits."""

    def test_quintic_polynomial_batch(self):
        from vdsim.planning.polynomials import quintic_coefficients

        start = time.perf_counter()
        for _ in range(1000):
            quintic_coefficients(0, 10, 0, 50, 15, 0, 5.0)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"1000 quintic coefficients took {elapsed:.2f}s (limit: 1.0s)"

    def test_polynomial_evaluation_vectorized(self):
        from vdsim.planning.polynomials import polyval, quintic_coefficients

        c = quintic_coefficients(
            np.zeros(500), np.full(500, 10.0), np.zeros(500),
            np.full(500, 50.0), np.full(500, 15.0), np.zeros(500), np.full(500, 5.0),
        )
        t = np.linspace(0, 5, 100)[None, :].repeat(500, axis=0)
        start = time.perf_counter()
        for _ in range(100):
            polyval(c, t)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"Polynomial evaluation took {elapsed:.2f}s (limit: 2.0s)"


@pytest.mark.benchmark
class TestCollisionPerformance:
    """Collision checking must handle typical traffic densities."""

    def test_sat_overlap_batch(self):
        from vdsim.world.collision import rect_corners, sat_overlap

        ego = rect_corners(0, 0, 0, 4.5, 2.0)[0]
        n = 200
        x = np.random.default_rng(42).uniform(-50, 50, n)
        y = np.random.default_rng(42).uniform(-20, 20, n)
        psi = np.random.default_rng(42).uniform(-np.pi, np.pi, n)
        obstacles = rect_corners(x, y, psi, 4.5, 2.0)

        start = time.perf_counter()
        for _ in range(100):
            sat_overlap(ego, obstacles)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"100x SAT with 200 obstacles took {elapsed:.2f}s (limit: 1.0s)"


@pytest.mark.benchmark
class TestReferencLinePerformance:
    """Reference line operations must be fast for real-time planning."""

    def test_projection_speed(self):
        from vdsim.geometry.reference_line import ReferenceLine

        line = ReferenceLine.from_segments(
            [("straight", 200), ("arc", 100, 0.01), ("straight", 200)], ds=0.5
        )
        start = time.perf_counter()
        for i in range(500):
            x = float(i) * 0.8
            line.project(x, 2.0 * np.sin(x / 20))
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"500 projections took {elapsed:.2f}s (limit: 2.0s)"

    def test_project_many_speed(self):
        from vdsim.geometry.reference_line import ReferenceLine

        line = ReferenceLine.straight(500, ds=0.5)
        x = np.linspace(10, 490, 1000)
        y = np.sin(x / 30) * 3

        start = time.perf_counter()
        for _ in range(10):
            line.project_many(x, y)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"10x project_many(1000) took {elapsed:.2f}s (limit: 2.0s)"


@pytest.mark.benchmark
class TestSolverPerformance:
    """Numerical integration must keep up with real-time simulation."""

    def test_rk4_step_throughput(self):
        from vdsim.simulation.solver import RK4Solver

        def f(t, x):
            return -0.1 * x

        s = RK4Solver(substeps=1)
        x = np.ones(24)

        start = time.perf_counter()
        for i in range(10000):
            x = s.step(f, i * 0.001, x, 0.001)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"10000 RK4 steps (24 states) took {elapsed:.2f}s (limit: 2.0s)"


@pytest.mark.benchmark
class TestTireModelPerformance:
    """Tire force computation is called per substep and must be fast."""

    def test_tire_force_batch(self):
        from vdsim.tire_models import create_tire_set

        config = load_vehicle_preset("mid_size_sedan")
        tires = create_tire_set(config.tires)
        n = 4
        alpha = np.full(n, 0.05)
        kappa = np.full(n, 0.02)
        fz = np.full(n, 5000.0)
        mu = np.ones(n)
        camber = np.zeros(n)

        start = time.perf_counter()
        for _ in range(10000):
            tires.forces(alpha, kappa, fz, mu, camber)
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"10000 tire force calls took {elapsed:.2f}s (limit: 2.0s)"
