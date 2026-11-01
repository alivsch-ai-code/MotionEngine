# Trajectory Planning

This document describes the trajectory planning architecture in MotionEngine.

## Overview

The planning module implements the Werling (2011) approach for optimal trajectory generation in curvilinear (Frenet) coordinates. The planner generates a set of candidate trajectories by sampling boundary conditions, evaluates them against cost functions and constraints, checks for collisions, and selects the optimal trajectory.

## Pipeline

```
Reference Line → Sampling → Polynomial Generation → Combination (Frenet→Cartesian)
    → Constraint Checking → Collision Detection → Cost Evaluation → Selection
```

## Key Components

### Lateral Planning (`lateral.py`)

Generates quintic polynomial trajectories in the Frenet d-coordinate:

```
d(t) = a₀ + a₁t + a₂t² + a₃t³ + a₄t⁴ + a₅t⁵
```

Boundary conditions: initial state `(d₀, ḋ₀, d̈₀)` and target state `(d₁, ḋ₁, d̈₁)` over horizon `T`.

Reference: Werling (2011), equations 3.6–3.8.

### Longitudinal Planning (`longitudinal.py`)

Three modes:
- **Velocity keeping**: Quartic polynomial to target speed
- **Following**: Quintic polynomial maintaining time gap to lead vehicle
- **Stopping**: Quintic polynomial to standstill at target position

Reference: Werling (2011), equations 3.9–3.12.

### Cost Function (`cost.py`)

Weighted sum of:
- Jerk integral (lateral and longitudinal)
- Terminal deviation from target
- Travel time
- Acceleration magnitude
- Curvature
- Collision risk
- Comfort (ISO 2631 weighted)
- Energy consumption

All weights are configurable via `configs/planning/`.

### Constraints (`constraints.py`)

- Maximum curvature
- Maximum lateral/longitudinal acceleration
- Maximum jerk
- Steering angle and rate limits
- Yaw rate limit
- Tire force utilization
- Vehicle stability envelope
- Speed range

### Collision Detection (`collision.py`)

Uses the circle-covering method (Ziegler & Stiller, 2010): the vehicle footprint is approximated by overlapping circles, and collision is detected when any ego circle overlaps with any obstacle circle, including a configurable safety margin.

### Reference Line (`geometry/reference_line.py`)

Cubic Hermite interpolation of waypoints with:
- Arc-length parameterization
- Curvature computation
- Projection (Cartesian → Frenet) via Newton refinement
- Support for closed (looped) reference lines

## Configuration

Planning parameters are stored in `configs/planning/`:
- `default.json` — balanced parameters
- `comfort.json` — comfort-optimized (lower jerk, larger margins)
- `sporty.json` — performance-optimized (tighter following, smaller margins)

## References

- Werling, M. (2011). *Optimal trajectory generation for dynamic street scenarios in a Frenet frame.* KIT Scientific Publishing. [DOI: 10.5445/KSP/1000021738](https://doi.org/10.5445/KSP/1000021738)
- Werling, M. et al. (2010). *Optimal trajectory generation for dynamic street scenarios in a Frenet frame.* IEEE ICRA 2010.
- Ziegler, J. & Stiller, C. (2010). *Fast collision checking for intelligent vehicle motion planning.* IEEE IV 2010.
