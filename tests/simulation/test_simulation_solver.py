"""Tests for numerical solvers (Euler, Heun, RK4, Adaptive).

Validates each integrator against analytically solvable ODEs.
"""

import numpy as np
import pytest

from vdsim.simulation.solver import (
    SOLVERS,
    AdaptiveSolver,
    EulerSolver,
    HeunSolver,
    RK4Solver,
    create_solver,
)


def exponential_decay(t, x):
    return -x


def harmonic_oscillator(t, x):
    return np.array([x[1], -x[0]])


class TestSolverCreation:
    def test_create_rk4(self):
        s = create_solver("rk4")
        assert isinstance(s, RK4Solver)

    def test_create_euler(self):
        s = create_solver("euler")
        assert isinstance(s, EulerSolver)

    def test_create_heun(self):
        s = create_solver("heun")
        assert isinstance(s, HeunSolver)

    def test_create_adaptive(self):
        s = create_solver("adaptive")
        assert isinstance(s, AdaptiveSolver)

    def test_solvers_dict_completeness(self):
        assert set(SOLVERS.keys()) == {"euler", "heun", "rk4", "adaptive"}


class TestEulerSolver:
    def test_exponential_decay(self):
        s = EulerSolver(substeps=100)
        x = np.array([1.0])
        result = s.step(exponential_decay, 0.0, x, dt=1.0)
        expected = np.exp(-1.0)
        assert result[0] == pytest.approx(expected, abs=0.02)

    def test_first_order_accurate(self):
        s1 = EulerSolver(substeps=100)
        s2 = EulerSolver(substeps=200)
        x = np.array([1.0])
        e1 = abs(s1.step(exponential_decay, 0.0, x, 1.0)[0] - np.exp(-1.0))
        e2 = abs(s2.step(exponential_decay, 0.0, x, 1.0)[0] - np.exp(-1.0))
        ratio = e1 / max(e2, 1e-15)
        assert ratio > 1.5


class TestHeunSolver:
    def test_exponential_decay(self):
        s = HeunSolver(substeps=10)
        x = np.array([1.0])
        result = s.step(exponential_decay, 0.0, x, dt=1.0)
        expected = np.exp(-1.0)
        assert result[0] == pytest.approx(expected, abs=0.005)

    def test_higher_order_than_euler(self):
        euler = EulerSolver(substeps=10)
        heun = HeunSolver(substeps=10)
        x = np.array([1.0])
        exact = np.exp(-1.0)
        e_euler = abs(euler.step(exponential_decay, 0.0, x, 1.0)[0] - exact)
        e_heun = abs(heun.step(exponential_decay, 0.0, x, 1.0)[0] - exact)
        assert e_heun < e_euler


class TestRK4Solver:
    def test_exponential_decay(self):
        s = RK4Solver(substeps=1)
        x = np.array([1.0])
        result = s.step(exponential_decay, 0.0, x, dt=0.1)
        expected = np.exp(-0.1)
        assert result[0] == pytest.approx(expected, abs=1e-6)

    def test_harmonic_oscillator_energy_conservation(self):
        s = RK4Solver(substeps=1)
        x = np.array([1.0, 0.0])
        dt = 0.01
        for _ in range(1000):
            x = s.step(harmonic_oscillator, 0.0, x, dt)
        energy = 0.5 * (x[0] ** 2 + x[1] ** 2)
        assert energy == pytest.approx(0.5, abs=1e-4)

    def test_fourth_order_convergence(self):
        s1 = RK4Solver(substeps=10)
        s2 = RK4Solver(substeps=20)
        x = np.array([1.0])
        exact = np.exp(-1.0)
        e1 = abs(s1.step(exponential_decay, 0.0, x, 1.0)[0] - exact)
        e2 = abs(s2.step(exponential_decay, 0.0, x, 1.0)[0] - exact)
        ratio = e1 / max(e2, 1e-15)
        assert ratio > 10


class TestAdaptiveSolver:
    def test_exponential_decay_accurate(self):
        s = AdaptiveSolver()
        x = np.array([1.0])
        result = s.step(exponential_decay, 0.0, x, dt=1.0)
        expected = np.exp(-1.0)
        assert result[0] == pytest.approx(expected, abs=1e-5)

    def test_harmonic_oscillator(self):
        s = AdaptiveSolver()
        x = np.array([1.0, 0.0])
        result = s.step(harmonic_oscillator, 0.0, x, dt=2 * np.pi)
        assert result[0] == pytest.approx(1.0, abs=1e-4)
        assert result[1] == pytest.approx(0.0, abs=1e-4)


class TestSubsteps:
    def test_substep_override(self):
        s = RK4Solver(substeps=1)
        x = np.array([1.0])
        r1 = s.step(exponential_decay, 0.0, x, 1.0, substeps=1)
        r10 = s.step(exponential_decay, 0.0, x, 1.0, substeps=10)
        exact = np.exp(-1.0)
        assert abs(r10[0] - exact) < abs(r1[0] - exact)
