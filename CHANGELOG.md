# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **REST service** `vdsim.service` (FastAPI, OpenAPI 3.1, Swagger UI): `/simulate`, `/plan`, `/predict`,
  `/vehicle`, `/trajectory`, `/health`, `/metrics` (Prometheus); API key, concurrency and runtime limits.
  Optional extra `api`, console script `motion-engine-api`.
- Dockerfile, docker-compose, devcontainer, workflow `API` (service tests, OpenAPI export, Docker smoke test).
- Tests: physical plausibility and Monte Carlo (`tests/physics`), scenario regression against golden KPIs
  (`tests/regression`), REST service (`tests/service`), reporting and plots (`tests/reporting`).
- `benchmarks/run_benchmarks.py` with measured results in `benchmarks/README.md`.

### Changed

- Planning cycle 40-47 % faster: the per-cycle debug snapshot no longer builds a Python set of all candidates.
- `SimulationResult` stores scalar signals as floats (peak memory of a 60 s run 37 MiB -> 17 MiB).
- Collision settings: `max_circles_object` 5 -> 12, new `max_lateral_inflation` (0.3 m).

### Known issues

- `laengsparken_rueckwaerts` does not park in the full stack (standstill local optimum of the velocity mode
  at v_ref = 1 m/s), see review finding F2.
- `MOTIONENGINE_CONFIG_DIR` to locate `configs/` outside the source tree.
- Review report `docs/review/2026-11-08-full-review.md`.

### Fixed

- Planner collision check: long objects were covered by at most 5 circles (a 16.5 m truck had r = 2.07 m), so a
  truck in the adjacent lane collided with every candidate and the planner fell back; the library scenario
  `einfaedeln_lkw` ended in a collision after 2.5 s. The circle count now bounds the lateral inflation (0.3 m).
- Scenario success criteria (`reach_goal`, `parked`, `final_lane`, ...) are evaluated after every AD run
  (`metadata["mission"]`, KPI `mission_passed`); before they were never checked.
- MATLAB to Python converter: `any`/`all`/`logical` over a comparison produced a chained Python comparison.
- MATLAB interpreter: `str2num` accepts matrix literals, `str2func` anonymous functions.
- `vdsim.api.references`, `knowledge_graph`, `build_docs` and `matlab_convert` raised on every call; the REST
  endpoints `/matlab/convert` and `/knowledge/references` always returned 500.
- Pacejka tire: the combined-slip force exceeded the friction circle (up to 37 % at low mu); the resultant is
  now bounded by Kamm's circle.
- `Environment.wind_speed`: head wind > 0 as documented and labeled in the GUI (the models treated it as tail wind).
- Nonlinear single-track model: rolling resistance was missing in the longitudinal equation.
- `Scenario.vehicle_overrides` rejects unknown parameter names instead of ignoring them.
- Console script `motion-engine-scenario` pointed to a module outside the package (`vdsim.cli.scenario` now).
- Legacy REST server: finished jobs are evicted (unbounded memory growth), job lists are read under the lock,
  and the server refuses a non-loopback address without `--token`.
- Seven cited references were missing from `docs/references/`.

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
