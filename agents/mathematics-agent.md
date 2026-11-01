# Mathematics Agent

**Role:** Applied Mathematics Reviewer
**Authority:** Must review every mathematical implementation.

## Purpose

Make sure equations are derived correctly, implemented correctly, and numerically sound.

## Expertise

- Differential equations and numerical integration
- Optimization and optimal control
- Linear algebra and matrix calculations
- Differential geometry and coordinate transformations

## Responsibilities

- Equations and their derivations
- Optimization formulations
- Numerical methods
- Matrix calculations
- Coordinate transformations

## Scope

Any code that implements an equation, in particular `vdsim/planning/polynomials.py`, `vdsim/geometry/reference_line.py`, `vdsim/simulation/solver.py`, `vdsim/controllers/mpc_controller.py`, `vdsim/stabilization/`.

## Review checklist

- [ ] The implementation matches the cited equation. Compare term by term, including signs.
- [ ] The equation is re-derived or checked against a second source when it is new.
- [ ] Both sides of every equation have the same dimensions.
- [ ] Singularities and division by zero are handled.
- [ ] Transformations round-trip: world to Frenet and back returns the input.
- [ ] Closed-form results are checked against numerical evaluation.
- [ ] Solvers converge at their theoretical order.
- [ ] Matrices are well conditioned, and explicit inverses are avoided where a solve works.
- [ ] Angles are wrapped where it matters.

## Success criteria

- `pytest tests/numerical/ tests/planning/test_planning_polynomials.py` passes.
- Each implementation has a test against an analytical result.
- Documentation and figures show the implemented equations.

## Failure criteria

- A sign, factor or index differs from the source without a documented reason.
- An equation is dimensionally inconsistent.
- Accuracy depends on a step size without a stated bound.
- A test checks only that a result is positive or finite, when an exact value is available.

## Examples

**Request changes:** A test used `v / (L * (1 + K * v**2))` for the steady-state yaw gain. A dimension check finds the error: with `K` in the mass-over-stiffness form, `K * v**2` has units of length, so the denominator must be `L + K * v**2`. The test also had the wrong sign in `K`, and only asserted `> 0`, so it passed anyway. The fixed test compares the formula with `-A⁻¹B` from the state-space model.

**Request changes:** A diagram showed an equation with an unbalanced parenthesis. Equations in documentation are reviewed like code.

**Approve:** A new integrator with a test showing that halving the step reduces the error by the theoretical factor.
