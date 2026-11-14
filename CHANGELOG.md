# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Learning environment:**
  - **Controller lab** (page, `/control/catalog`, `/control/run`): several tracking controllers on the same path and
    plant, with KPIs, signals and the control law as a formula with the value of every term at the chosen time.
  - **Learn** page: nine lessons, each with a question, a prepared experiment on the real controllers and planner, and
    the answer.
  - **Conditions** for stack runs: friction and wind (`environment` in `api.run`, `friction` in `/workbench/runs`) and
    Workbench presets (ideal, realistic, wet road, ice and poor sensors) with the double-track model, actuator
    dynamics, sensor noise and latency.
  - **English texts of the stack library** in the web app: scenarios, KPIs, mission criteria, component labels,
    validation messages.
- **Validation against measured data** (`vdsim.validation`, `scripts/validate_measured.py`): the single-track model
  replayed with the measured steering angle and speed of four production cars (46 hours, commaSteeringControl) and
  public vehicle specifications. Without any fit it explains 40 to 95 % of the measured lateral acceleration, with
  the steering angle offset calibrated 88 to 97 %. Method, results and limits: `docs/validation/measured_data.md`.
- **Learned trajectory planner** (`vdsim.learning.trajectory`, stack component `trajectory_planner/learned`): a network
  learns from the Werling planner which trajectory it selects (end offset, end speed and end times). The planner
  builds only the candidates next to this proposal and checks them with the teacher's restrictions and collision
  check; without a valid candidate, or with the best one on the border of the local set, the cycle uses the complete
  search. Training and evaluation through `POST /models/train` (`kind: "trajectory_planner"`), a closed-loop
  comparison with the teacher (`POST /models/{id}/drive`), `model` in `POST /plan`, and the **Neural models** page.
  With 4000 demonstrations (108 s): 99 % of the solvable cycles come from the network path, 91 % select the teacher's
  trajectory, about 30 % less computing time. Method and results: `docs/learning/trajectory_model.md`.
- **Development environment in the web app** (the functions of the desktop workbench `run_gui.py`): pages
  **Workbench** (full AD stack on a scenario, stack editor per layer, animated planner view with candidates per cycle,
  cost terms, signals, KPIs, mission, events, runtime profile, result download), **Research** (compare components,
  parameter sweep, Monte Carlo), **Architecture** (stack graph, validation, component documentation), **MATLAB**
  (analysis, conversion to Python or C) and **Knowledge** (knowledge graph, references). Endpoints `/workbench/*`,
  `/matlab/*`, `/knowledge/*` on `vdsim.api`; runs and experiments are background jobs that survive page changes.
- **Remaining desktop functions in the web app:**
  - **Live mode** of the Workbench: play, pause, single step and 10 steps with live telemetry; a live run can be kept
    as a normal run (`vdsim.ad.live.LiveSession`, `api.live()`, `/workbench/live`).
  - **Load a saved result:** the download is now one file with metadata and arrays, and `/workbench/runs/import`
    loads it again (also the `.json` + `.npz` pair the library writes).
  - **Parameter dialog** per stack component, built from the component schema; only changed values are sent.
  - **Connection editor** on the Architecture page: remove and add connections; the server validates the wiring and
    the Workbench runs the rewired stack (`connections` in `api.run`, `/workbench/graph`, `/workbench/runs`).
  - **Trajectory editor** (new page): draggable waypoints, corner radii, speed profile limited by lateral
    acceleration, friction map; the path drives the simulation (`/trajectory/waypoints`, `waypoints` in `/simulate`).
  - **Run comparison and report** on the Simulate page: KPI table side by side, overlaid paths and signals, PDF
    report and Markdown summary (`/simulate/report`), save and load a run.
- **Parking planner** (`vdsim.planning.parking`, `POST /park`, web page **Parking**, assistant tool `plan_parking`):
  parallel, perpendicular and angled spots, forward or reverse, left or right; front, rear-only and four-wheel
  (counter-/in-phase) steering through the side-slip-free reference point of each configuration; Reeds-Shepp curves,
  Hybrid A* with a multi-maneuver way out of tight spots and shortcut smoothing; closed loop with the Samson
  rear-axle law, steering-rate speed profile and traction limits per drive layout. Research and results:
  `docs/planning/parking.md`.
- Web app: animated playback of the driven path (Simulate page, assistant cards, Parking page); training jobs
  are followed app-wide (`GET /models/jobs`, progress badge in the header) and survive page changes and reloads;
  the last simulation stays when the Simulate page is left.
- **Assistant** (`/app/assistant`, `POST /chat`): a chat in the web app where you describe a simulation or a
  planning situation in plain English or German. Claude calls the service's own simulation, planning, prediction and
  catalog functions as tools (inputs validated with the REST schemas, server limits unchanged), streams its answer as
  server-sent events, and the web app shows every tool result as a card with KPIs and plots. Optional extra `chat`;
  configured with `ANTHROPIC_API_KEY`, `MOTIONENGINE_CHAT_MODEL`, `MOTIONENGINE_CHAT_EFFORT`.
- **Web app** (`web/`, React 19 + TypeScript + Vite): Simulate, Trajectory inspector, Neural models, Predict,
  Vehicles, Settings, landing page and live style guide; English (default) and German via i18next with a
  header switcher (stored choice → browser language → English); dark and light theme; served by the API with
  `MOTIONENGINE_WEB_DIR` and included in the Docker image. Workflow `Web` (typecheck, i18n tests, build,
  locale drift check, Playwright end-to-end run with screenshots).
- `POST /plan/explain`: step-by-step derivation of one planning cycle (polynomial coefficients re-derived and
  checked against the planner, cost terms, candidates, Frenet transform, restrictions, single-track physics).
- `vdsim.learning`: NumPy MLP surrogate of a vehicle model (training with Adam and early stopping), ONNX and
  HTTP backends, registration as vehicle model `neural_<id>`, closed-loop evaluation; endpoints under `/models`.
  Optional extra `ml` (onnxruntime).
- Brand assets in `docs/brand/` (mark, logos for light and dark backgrounds, app icon, favicons, GitHub avatar,
  two alternative logo options) and the design system `docs/design-system.md`.
- KPI and stop reasons carry language-neutral codes (`value_code`, `group_code`, `stop_code`).
- **REST service** `vdsim.service` (FastAPI, OpenAPI 3.1, Swagger UI): `/simulate`, `/plan`, `/predict`,
  `/vehicle`, `/trajectory`, `/health`, `/metrics` (Prometheus); API key, concurrency and runtime limits.
  Optional extra `api`, console script `motion-engine-api`.
- Dockerfile, docker-compose, devcontainer, workflow `API` (service tests, OpenAPI export, Docker smoke test).
- Tests: physical plausibility and Monte Carlo (`tests/physics`), scenario regression against golden KPIs
  (`tests/regression`), REST service (`tests/service`), reporting and plots (`tests/reporting`).
- `benchmarks/run_benchmarks.py` with measured results in `benchmarks/README.md`.

### Changed

- README rewritten: product overview, web app screenshots, features, measured performance, comparison, citation.
- Trajectory inspector: international axle symbols (f/r, understeer gradient K) instead of v/h and EG; English source
  references (Theorem, Table).
- Planning cycle 40-47 % faster: the per-cycle debug snapshot no longer builds a Python set of all candidates.
- `SimulationResult` stores scalar signals as floats (peak memory of a 60 s run 37 MiB -> 17 MiB).
- Collision settings: `max_circles_object` 5 -> 12, new `max_lateral_inflation` (0.3 m).

### Known issues

- `MOTIONENGINE_CONFIG_DIR` to locate `configs/` outside the source tree.
- Review report `docs/review/2026-11-08-full-review.md`.

### Fixed

- `laengsparken_rueckwaerts` parks (review finding F2): the behavior layer hands the parking maneuver to the parking
  planner (`trajectory_planner/werling_parking`, now the default planner of the AD stack; it delegates to the Werling
  planner for everything else) instead of running the Werling velocity mode on the reversed lane line.
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
