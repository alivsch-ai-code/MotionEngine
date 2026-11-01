# Scientific References

This directory contains the scientific references organized by topic. Each YAML file lists the papers, books, and standards that the corresponding module implementation is based on.

## Reference Files

| File | Module | Topics |
|---|---|---|
| [vehicle_dynamics.yaml](vehicle_dynamics.yaml) | `vdsim.vehicle_models` | Bicycle model, double-track, multibody, state-space form |
| [planning.yaml](planning.yaml) | `vdsim.planning` | Werling planner, Frenet frame, polynomial trajectories |
| [stabilization.yaml](stabilization.yaml) | `vdsim.stabilization` | Tracking controllers, I/O linearization, Lyapunov stability |
| [werling.yaml](werling.yaml) | Multiple | Werling dissertation — the primary reference |
| [research.yaml](research.yaml) | `vdsim.research` | Benchmarking, metrics, experiment design |
| [runtime.yaml](runtime.yaml) | `vdsim.runtime` | Block diagram execution, code generation |

## How to Cite

If you use MotionEngine in your research, please cite the primary references:

```bibtex
@phdthesis{werling2011,
  author    = {Moritz Werling},
  title     = {Ein neues Konzept f{\"u}r die Trajektoriengenerierung und -stabilisierung in zeitkritischen Verkehrsszenarien},
  school    = {Karlsruhe Institute of Technology (KIT)},
  year      = {2011},
  doi       = {10.5445/KSP/1000021738},
}

@book{rajamani2012,
  author    = {Rajesh Rajamani},
  title     = {Vehicle Dynamics and Control},
  edition   = {2nd},
  publisher = {Springer},
  year      = {2012},
  doi       = {10.1007/978-1-4614-1433-9},
}

@book{pacejka2012,
  author    = {Hans B. Pacejka},
  title     = {Tire and Vehicle Dynamics},
  edition   = {3rd},
  publisher = {Butterworth-Heinemann},
  year      = {2012},
  doi       = {10.1016/C2010-0-68548-8},
}
```
