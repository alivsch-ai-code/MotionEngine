# Architecture Overview

This document provides a high-level overview of the MotionEngine architecture. For the complete architecture documentation with UML diagrams, see [../ARCHITECTURE.md](../ARCHITECTURE.md).

## Design Principles

1. **Layered architecture** — Dependencies point strictly downward; each layer only depends on the layers below it.
2. **Interface-driven** — All exchangeable components implement abstract interfaces defined in `vdsim.core.interfaces`.
3. **Plugin registry** — Components register via `@register(kind, name)` and are instantiated by name at runtime.
4. **Separation of concerns** — Physics, control, planning, visualization, and GUI are fully decoupled.
5. **Data-driven configuration** — Vehicle parameters, scenarios, and planning settings are JSON-serializable dataclasses.

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  GUI Layer                    PySide6 desktop application   │
├─────────────────────────────────────────────────────────────┤
│  Visualization │ Reporting    Plots, animation, PDF, KPIs   │
├─────────────────────────────────────────────────────────────┤
│  Simulation Core              Simulator, Scenario, Results  │
├─────────────────────────────────────────────────────────────┤
│  Controllers │ Actuators │ Planning   Control + planning    │
├─────────────────────────────────────────────────────────────┤
│  Vehicle Models │ Tire Models │ Powertrain    Physics       │
├─────────────────────────────────────────────────────────────┤
│  Solver                       RK4, Heun, Euler, adaptive   │
├─────────────────────────────────────────────────────────────┤
│  Core                         Interfaces, registry, params  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Scenario (JSON) + Vehicle Preset (JSON) + Trajectory
                     ↓
               ┌─────────────────────┐
               │     Simulator       │
               │                     │
               │  Lateral Controller ──→ Steering Actuator
               │  Longit. Controller ──→ Powertrain + Brakes
               │         ↓                    ↓
               │  Chassis Systems (ESP, ABS, TCS, ...)
               │         ↓
               │  Vehicle Model + Tire Model + Environment
               │         ↓
               │  Solver (RK4 with auto substeps)
               │         ↓
               │  VehicleState → Results
               └─────────────────────┘
                     ↓
          KPI Evaluation → PDF Report
          Visualization → Plots / Animation
```

## Extension Points

| What to Add | Interface | Registration |
|---|---|---|
| Vehicle model | `VehicleModel` | `@register("vehicle_model", "name")` |
| Tire model | `TireModel` | `@register("tire_model", "name")` |
| Lateral controller | `LateralController` | `@register("lateral_controller", "name")` |
| Longitudinal controller | `LongitudinalController` | `@register("longitudinal_controller", "name")` |
| Chassis system | `ChassisSystem` | `@register("chassis_system", "name")` |
| Maneuver | — | `@maneuver("key", "Label", ...)` |
| Trajectory loader | — | `@register("trajectory_loader", "name")` |

See [examples/custom_nodes/](../../examples/custom_nodes/) for complete examples.
