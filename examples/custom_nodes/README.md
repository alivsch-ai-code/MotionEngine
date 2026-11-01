# Custom Nodes – Beispiele

Custom Nodes haben dieselben Schnittstellen wie native Komponenten (Ports der Ebene aus `vdsim.framework.layers`, Parameter, `reset/step` bzw. `output/update`, `get_state/set_state`). Sie werden im Graphen über einen Spec-String eingebunden.

| Datei | Ebene | Spec |
|---|---|---|
| `python/my_controller_node.py` | tracking_controller (Pure Pursuit) | `python:examples/custom_nodes/python/my_controller_node.py:PurePursuitController` |
| `python/my_planner_node.py` | trajectory_planner (Spurhalten) | `python:.../my_planner_node.py:LaneKeepingPlanner` |
| `python/my_vehicle_model.py` | vehicle_plant (kinematisch, ohne Durchgriff) + Adapter `CommandToControl` | `python:.../my_vehicle_model.py:KinematicBicyclePlant` |
| `python/my_behavior_planner.py` | behavior_planner | `python:.../my_behavior_planner.py:SimpleBehaviorPlanner` |
| `python/my_sensor_fusion_module.py` | perception (Fusion zweier verrauschter Objektlisten) | `python:.../my_sensor_fusion_module.py:TwoSensorFusion` |
| `rust/my_controller_node/` | derselbe Pure-Pursuit-Regler in Rust | `rust:examples/custom_nodes/rust/my_controller_node` |
| `cpp/my_controller_node/` | derselbe Regler in C++17 | `cpp:examples/custom_nodes/cpp/my_controller_node` |

Die komplette Kette aus Python-Nodes: `configs/graphs/examples/custom_nodes_kette.json`.

```python
from vdsim.runtime import Graph, Executor
g = Graph.load("configs/graphs/examples/custom_nodes_kette.json")
ex = Executor(g)
ex.run(10.0)
print(ex.value("plant.ego"), ex.profiler.table())
ex.check_reload()        # nach dem Speichern einer Node-Datei: Hot Reload mit Zustandsübernahme
```

## Neues Gerüst erzeugen

```python
from vdsim.runtime import create_custom_node
create_custom_node("python", "mein_regler", "tracking_controller", "custom_nodes")
create_custom_node("rust", "mein_regler", "tracking_controller", "custom_nodes")   # Cargo-Crate (cdylib, nur std)
create_custom_node("cpp", "meine_strecke", "vehicle_plant", "custom_nodes")       # C++17, Header vdsim_node.h
```

Das Gerüst liest alle Eingänge typisiert und schreibt Standardwerte auf alle Ausgänge; es baut bzw. lädt sofort.

## Native Nodes (Rust/C++)

- `vdsim_node.rs` bzw. `vdsim_node.h` werden aus `vdsim.framework.types` erzeugt (nicht von Hand ändern): `python -c "from vdsim.runtime.codegen import write_headers; write_headers('ziel')"`.
- vdsim baut beim Laden automatisch (`cargo build --release` bzw. MSVC `cl /LD`, sonst g++/clang++) in ein Build-Verzeichnis außerhalb des Quellbaums (`<temp>/vdsim_native`, änderbar über `VDSIM_BUILD_DIR`).
- Die Schnittstelle (C-ABI, Version 1) ist in `vdsim/runtime/native.py` und `vdsim/runtime/docs/theory.md` beschrieben.
- Windows: Für C++ wird das Windows SDK benötigt (Visual Studio Installer → „Windows 11 SDK“). Rust funktioniert auch ohne SDK (vdsim erzeugt dann Import-Bibliotheken aus den System-DLLs).
