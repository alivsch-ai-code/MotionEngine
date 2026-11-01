# Vehicle Dynamics Models

This document describes the vehicle dynamics models implemented in MotionEngine.

## Model Hierarchy

MotionEngine provides five vehicle models at increasing fidelity:

| Model | States | Module | Key Physics |
|---|---|---|---|
| Kinematic bicycle | 4 | `bicycle_model.KinematicBicycleModel` | Ackermann geometry, no tire slip |
| Linear bicycle | 6 | `bicycle_model.LinearBicycleModel` | Linear tire, state-space (A, B) |
| Nonlinear bicycle | 6 | `bicycle_model.NonlinearBicycleModel` | Nonlinear tire, friction ellipse |
| Double-track | 12 | `double_track_model.DoubleTrackModel` | Roll, wheel spin, per-wheel forces |
| Multibody | 24 | `multibody_model.MultibodyModel` | Heave/roll/pitch, unsprung masses |

## Kinematic Bicycle Model

The simplest model, valid at low lateral acceleration where tire slip can be neglected.

**States:** `[x, y, ψ, v]` — position, heading, speed

**Equations:**
```
ẋ = v·cos(ψ + β)
ẏ = v·sin(ψ + β)
ψ̇ = v·cos(β)·κ
v̇ = aₓ
```

where `β = arctan((lᵣ·tan(δf) + lf·tan(δr)) / L)` is the sideslip angle and `κ` the path curvature.

## Linear Bicycle Model

The standard linear single-track model for controller design and stability analysis.

**States:** `[x, y, ψ, v, β, r]` — position, heading, speed, sideslip angle, yaw rate

**State-space form:**

```
[β̇]   [-（cf+cr)/(mv)    (cr·lr-cf·lf)/(mv²) - 1] [β]   [cf/(mv) ] 
[ṙ ] = [(cr·lr-cf·lf)/Iz  -(cf·lf²+cr·lr²)/(Iz·v)] [r] + [cf·lf/Iz] · δ
```

Reference: Rajamani (2012), Chapter 2.

## Nonlinear Bicycle Model

Uses the full tire model (Pacejka, brush, or linear) with friction ellipse coupling:

```
αf = δ − arctan((v·sin(β) + lf·r) / (v·cos(β)))
αr =   − arctan((v·sin(β) − lr·r) / (v·cos(β)))
```

Longitudinal load transfer included: `ΔFz = m·aₓ·h / L`.

## Double-Track Model (12 DOF)

Separate treatment of left and right wheels with roll dynamics:

**Additional physics:**
- Roll angle and roll rate
- Individual wheel rotation (4 wheels)
- Dynamic load transfer (geometric + suspension)
- Camber effects from roll
- Roll steer
- Per-wheel friction coefficient (split-mu)

## Multibody Model (24 DOF)

Full vehicle body dynamics with suspension:

**Additional physics:**
- Heave, roll, pitch of sprung mass
- 4 unsprung masses with vertical dynamics
- Spring/damper forces (nonlinear characteristics)
- Anti-roll bars
- Tire spring (road → wheel contact)
- Road profile excitation (ISO 8608)
- Anti-dive / anti-squat geometry

## Tire Models

### Linear Tire
`Fy = -Cα · α`, with friction circle saturation: `Fy = min(Fy, μ·Fz)`.

### Pacejka Magic Formula
Reduced parameter set with:
- Load-degressive stiffness: `Kα = Kα₀ · Fz/Fz₀ · (1 − ε·(Fz/Fz₀ − 1))`
- Load-dependent friction: `μ = μ₀ · (1 − κμ·(Fz/Fz₀ − 1))`
- Combined slip via weighting functions
- Camber thrust
- Pneumatic trail and aligning torque

### Brush Model
Parabolic pressure distribution, isotropic combined slip:
- Theoretical slip: `σ = √(σₓ² + σᵧ²)`
- Three regimes: linear, transition, full sliding

## Conventions

All models follow ISO 8855:
- x forward, y left, z up
- Positive steer angle → turn left
- Positive slip angle → positive lateral force
- Wheel order: FL, FR, RL, RR

## References

- Rajamani, R. (2012). *Vehicle Dynamics and Control.* 2nd ed., Springer.
- Pacejka, H.B. (2012). *Tire and Vehicle Dynamics.* 3rd ed., Butterworth-Heinemann.
- Schramm, D. et al. (2018). *Vehicle Dynamics: Modeling and Simulation.* 2nd ed., Springer.
- Mitschke, M. & Wallentowitz, H. (2014). *Dynamik der Kraftfahrzeuge.* 5th ed., Springer.
- ISO 8855:2011. *Road vehicles — Vehicle dynamics and road-holding ability — Vocabulary.*
