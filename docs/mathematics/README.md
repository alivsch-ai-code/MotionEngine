# Mathematical Foundations

This document describes the core mathematical methods used in MotionEngine.

## Polynomial Trajectory Generation

### Quintic Polynomials

Boundary-value problem: given initial state `(x₀, ẋ₀, ẍ₀)` and final state `(x₁, ẋ₁, ẍ₁)` at time `T`, find coefficients `a₀...a₅` such that:

```
x(t) = a₀ + a₁t + a₂t² + a₃t³ + a₄t⁴ + a₅t⁵
```

Solution (Werling 2011, eq. 3.6–3.8):

```
a₀ = x₀
a₁ = ẋ₀
a₂ = ẍ₀ / 2
a₃ = ( 20(x₁−x₀) − (8ẋ₁+12ẋ₀)T − (3ẍ₀−ẍ₁)T² ) / (2T³)
a₄ = ( 30(x₀−x₁) + (14ẋ₁+16ẋ₀)T + (3ẍ₀−2ẍ₁)T² ) / (2T⁴)
a₅ = ( 12(x₁−x₀) − 6(ẋ₁+ẋ₀)T − (ẍ₀−ẍ₁)T² ) / (2T⁵)
```

### Jerk Integral (Closed Form)

The jerk integral `J = ∫₀ᵀ x⃛(t)² dt` has a closed-form solution for quintic polynomials:

```
J = 36a₃² T + 192a₃a₄ T² + (240a₃a₅ + 192a₄²) T³
  + 720a₄a₅ T⁴ + 720a₅² T⁵
```

This avoids numerical quadrature in the cost function evaluation.

## Frenet (Curvilinear) Coordinates

### Frenet-to-Cartesian Transform (Werling 2011, eq. A.1–A.4)

Given reference line point `(xᵣ(s), yᵣ(s))` with heading `θᵣ(s)` and curvature `κᵣ(s)`:

```
x = xᵣ(s) − d·sin(θᵣ(s))
y = yᵣ(s) + d·cos(θᵣ(s))
```

Velocity transformation:

```
ṡ = v·cos(Δθ) / (1 − d·κᵣ)
ḋ = v·sin(Δθ)
```

where `Δθ = θ − θᵣ` is the heading error relative to the reference line.

### Cartesian-to-Frenet Projection

Computed via Newton-refined projection onto the cubic Hermite-interpolated reference line:
1. Brute-force nearest segment as initial guess
2. Newton iteration on the projection function `f(s) = ⟨p − r(s), ṙ(s)⟩ = 0`
3. Lateral offset `d = sign · ‖p − r(s*)‖`

## Numerical Integration

### Solvers

| Solver | Order | Stability Region (real axis) | Use Case |
|---|---|---|---|
| Euler | 1 | \|λh\| ≤ 2 | Debug only |
| Heun | 2 | \|λh\| ≤ 2 | Fast, moderate accuracy |
| RK4 | 4 | \|λh\| ≤ 2.83 | Default — good accuracy/cost ratio |
| Adaptive (scipy) | Variable | Automatic | Stiff systems, variable step |

### Substep Strategy

Each vehicle model reports its maximum stable time step via `stable_dt(state)`. The simulator automatically subdivides the controller time step into substeps to maintain stability. The stiffest component is typically the wheel rotation dynamics at low speed.

## I/O Linearization (Werling 2011, Chapter 4)

The dynamic tracking controller uses exact input/output linearization of the vehicle model.

### Flat Output

The vehicle position at a preview point `P = (x + L·cos(ψ), y + L·sin(ψ))` serves as the flat output. Its second time derivative yields a linear relationship:

```
P̈ = f(state) + G(state) · u
```

where `u = [δ̇, aₓ]` are the control inputs.

### Newton Solver

The linearizing input is found by solving the 2D nonlinear equation `G·u = v − f` via Newton's method with backtracking line search (Werling 2011, eq. 4.60).

### Lyapunov-Based Tracking (Kinematic)

For the kinematic single-track model, the tracking error dynamics in Frenet coordinates admit a Lyapunov function:

```
V = ½(eₛ² + eₙ²) + (1/k₃)·(1 − cos(eθ))
```

The control law ensures `V̇ ≤ 0` globally (Werling 2011, Satz 4 and Satz 6).

## References

- Werling, M. (2011). *Optimal trajectory generation for dynamic street scenarios in a Frenet frame.* KIT.
- Rajamani, R. (2012). *Vehicle Dynamics and Control.* 2nd ed., Springer.
- Khalil, H.K. (2002). *Nonlinear Systems.* 3rd ed., Prentice Hall.
