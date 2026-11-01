# Sequentieller Planer (erst längs, dann quer)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `trajectory_planner/sequential` · Version 1.0.0

**Vergleichsplaner: Längsbewegung ohne Kenntnis der Querbewegung, danach Querbewegung (Werling 3.1).**

## Zweck

Zeigt den Vorteil der kombinierten Quer-/Längsoptimierung (Ausweichen mit abgestimmtem Bremsen).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_planner` |
| Name | `sequential` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.baselines.SequentialPlanner`](../../../../vdsim/planning/baselines.py#L70) |
| Schnittstelle | – |
| Sprache | python |
| Periode | 0.1 s |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `behavior` | `BehaviorCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |
| `prediction` | `Prediction` | – | – | – |
| `status` | `ControllerStatus` | – | Trackingfehler / Reinitialisierung | optional, Rückführung |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `debug` | `PlannerDebug` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `sampling` | Sampling (Zielmannigfaltigkeiten) | – | {…} | – | – |
| `longitudinal` | Längsmodi | – | {…} | – | – |
| `cost` | Kostenfunktion | – | {…} | – | – |
| `constraints` | Restriktionen | – | {…} | – | – |
| `collision` | Kollisionsprüfung | – | {…} | – | – |
| `timing` | Zeitverhalten | – | {…} | – | – |
| `stabilization` | Bi-level-Stabilisierung | – | {…} | – | – |
| `search` | Suche | – | {…} | – | – |

## Einschränkungen

- Längskandidaten lexikographisch vor Querkandidaten sortiert

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_consistency.py](../../../../tests/planning/test_planning_consistency.py), [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)

Beispiele: [examples/planning/evasion.py](../../../../examples/planning/evasion.py)
