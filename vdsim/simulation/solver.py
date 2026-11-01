"""Numerical integrators for the vehicle model ODE: Euler, Heun, RK4 and an adaptive scipy solver."""

from scipy.integrate import solve_ivp


class Solver:
    name = "base"

    def __init__(self, substeps=1):
        self.substeps = max(1, int(substeps))

    def step(self, f, t, x, dt, substeps=None):
        # Advance x(t) -> x(t + dt), using `substeps` internal steps
        n = substeps or self.substeps
        h = dt / n
        for _ in range(n):
            x = self._single_step(f, t, x, h)
            t += h
        return x

    def _single_step(self, f, t, x, h):
        raise NotImplementedError


class EulerSolver(Solver):
    name = "euler"

    def _single_step(self, f, t, x, h):
        return x + h * f(t, x)


class HeunSolver(Solver):
    name = "heun"

    def _single_step(self, f, t, x, h):
        k1 = f(t, x)
        k2 = f(t + h, x + h * k1)
        return x + h / 2 * (k1 + k2)


class RK4Solver(Solver):
    name = "rk4"

    def _single_step(self, f, t, x, h):
        k1 = f(t, x)
        k2 = f(t + h / 2, x + h / 2 * k1)
        k3 = f(t + h / 2, x + h / 2 * k2)
        k4 = f(t + h, x + h * k3)
        return x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


class AdaptiveSolver(Solver):
    # scipy solve_ivp (RK45/LSODA) over each step; accurate reference, slower
    name = "adaptive"

    def __init__(self, method="RK45", rtol=1e-6, atol=1e-8):
        super().__init__(1)
        self.method, self.rtol, self.atol = method, rtol, atol

    def step(self, f, t, x, dt, substeps=None):
        sol = solve_ivp(f, (t, t + dt), x, method=self.method, rtol=self.rtol, atol=self.atol)
        return sol.y[:, -1]


SOLVERS = {cls.name: cls for cls in (EulerSolver, HeunSolver, RK4Solver, AdaptiveSolver)}


def create_solver(name="rk4", substeps=1):
    if name == "adaptive":
        return AdaptiveSolver()
    return SOLVERS[name](substeps)
