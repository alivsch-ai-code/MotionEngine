# Roadmap

This document outlines the planned development stages for vdsim.

## Current: v0.1 — Foundation

- [x] Core vehicle dynamics models (single-track, double-track, multibody)
- [x] Tire models (linear, Pacejka, brush)
- [x] Path tracking controllers (Stanley, Pure Pursuit, MPC)
- [x] ADAS functions (ACC, AEB, LKA, ESP, ABS, TCS)
- [x] Trajectory planning (Werling, sequential)
- [x] PySide6 desktop GUI
- [x] 22 pre-built scenarios
- [x] KPI evaluation and PDF reporting

## Next: v0.2 — Maturity

- [ ] Pacejka Magic Formula 6.2 with TIR file import
- [ ] Tire relaxation length (transient behavior)
- [ ] Temperature and pressure effects on tire forces
- [ ] EPS torque control model
- [ ] Aerodynamics with downforce
- [ ] OpenSCENARIO import
- [ ] Sensor models (camera/radar with latency and noise) via `Sensor` interface
- [ ] Full English localization of all user-facing strings (web app done: English/German; desktop GUI and CLI open)
- [ ] Type annotations for all public APIs
- [ ] 90%+ test coverage

## Future: v0.3 — Integration

- [ ] FMI/FMU export and import (co-simulation)
- [ ] ROS 2 bridge
- [ ] OSI (Open Simulation Interface) support
- [ ] Kinematics & compliance (K&C) lookup tables per axle
- [ ] Design of Experiments (DoE) and parameter optimization
- [ ] Parallel batch runs
- [ ] Numba/C acceleration for equations of motion
- [ ] SIL/HIL real-time operation

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved. Feature requests and discussion of roadmap priorities are welcome in [GitHub Discussions](https://github.com/alivsch-ai-code/MotionEngine/discussions).
