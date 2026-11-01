"""vdsim - vehicle dynamics and ADAS simulation platform.

Layers (see docs/ARCHITECTURE.md):
    core            parameters, interfaces, registry, logging
    tire_models     linear, Pacejka Magic Formula, brush model
    vehicle_models  single-track (kinematic / linear / nonlinear), double-track, multibody
    powertrain      engine, gearbox, electric motor, brakes, longitudinal actuation
    chassis         springs, dampers, anti-roll bars, axle kinematics
    actuators       latency chain, steering actuator, steering characteristic
    controllers     path tracking, ADAS functions, chassis control systems
    trajectory      trajectory model, maneuver generator, importers, waypoint editor
    simulation      solver, vehicle state, environment, simulator, scenarios, results
    analysis        quasi-static and linear (frequency domain) analysis
    reporting       KPI evaluation, PDF / Markdown reports
    visualization   matplotlib plots, animation, real-time dashboard widgets
    gui             PySide6 desktop application
"""

__version__ = "0.1.0"
