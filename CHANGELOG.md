# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-01

### Added

- **Vehicle models**: Kinematic, linear, and nonlinear single-track (bicycle) models; double-track model with roll dynamics and wheel rotation; multibody model with heave, roll, pitch, and unsprung masses
- **Tire models**: Linear with friction circle, Pacejka Magic Formula (load-dependent, combined slip, camber), brush model with parabolic pressure distribution
- **Controllers**: Stanley, Pure Pursuit, MPC; speed controller, ACC, AEB; lane keeping assist with driver model
- **Chassis systems**: ABS, TCS, ESP, rear axle steering, torque vectoring, active roll stabilization, skyhook damping
- **Powertrain**: ICE with torque map and automatic gearbox, electric motor with recuperation, FWD/RWD/AWD, torque vectoring, brake system with EBD
- **Actuators**: Latency chain (gateway, actuator, odometry), steering characteristic with error, curvature feedback correction
- **Trajectory generation**: ISO 3888-1/2, ISO 4138, ISO 7401, FMVSS 126, slalom, figure-eight, highway, city, race track with optimal speed profile
- **Trajectory import**: CSV, JSON, GPX, NMEA, MATLAB (.mat), ROS nav_msgs/Path, OpenDRIVE (.xodr)
- **Environment**: Friction maps (split-mu, patches), road profile (ISO 8608), bumps, wind, lead vehicle
- **Analysis**: Understeer gradient, yaw gain, eigenvalues, Bode diagram; wheel loads, roll gradient, roll axis
- **Reporting**: Automatic KPIs (dynamics, tracking, comfort per ISO 2631, energy, pass/fail criteria), run comparison, PDF report, engineering summary
- **Visualization**: Matplotlib plots (path, states, tires, Pacejka curves, GGV, Bode, heatmaps, energy), animation (GIF/MP4), real-time dashboard
- **GUI**: PySide6 desktop application with scenario/vehicle dashboards, live top view, signal scope, 3D view, analysis plots, KPI dashboard, run comparison, trajectory editor with friction map
- **Trajectory planning**: Werling planner (Frenet frame), sequential planner, collision checking, cost functions, constraints, trajectory stitching
- **Stabilization**: Classic lateral/longitudinal controllers, Werling kinematic/dynamic tracking, vehicle layer architecture, composite controllers
- **Research tools**: Benchmark framework, experiment runner, metrics collection
- **Runtime**: Block diagram executor, custom node support (Python/C++/Rust), hot reload, code generation
- **MATLAB bridge**: Parser, interpreter, code generation to Python/C++/Rust/native
- **22 pre-built scenarios** covering standard test maneuvers and real-world situations
- **4 vehicle presets**: Mid-size sedan (ICE/RWD), electric sedan (AWD), sports car, SUV
- **Lane change latency study**: Original study with latency chain and actuator characteristic error

[0.1.0]: https://github.com/alivsch-ai-code/MotionEngine/releases/tag/v0.1.0
