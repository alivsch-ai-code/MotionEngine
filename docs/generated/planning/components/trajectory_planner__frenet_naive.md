# Frenet-Planer (naiv, ohne Konsistenz)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `trajectory_planner/frenet_naive` · Version 1.0.0

**Vergleichsplaner: Frenet-Sampling mit relativem Endzeitraster und Neuplanung vom Messzustand.**

## Zweck

Zeigt den Nutzen der zeitlichen Konsistenz (Werling Abb. 3.2) in Planer-Vergleichen.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_planner` |
| Name | `frenet_naive` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.baselines.FrenetNaivePlanner`](../../../../vdsim/planning/baselines.py#L56) |
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
| `sampling` | Sampling (relatives Raster) | – | {…} | – | – |
| `longitudinal` | Längsmodi | – | {…} | – | – |
| `cost` | Kostenfunktion | – | {…} | – | – |
| `constraints` | Restriktionen | – | {…} | – | – |
| `collision` | Kollisionsprüfung | – | {…} | – | – |
| `timing` | Zeitverhalten | – | {…} | – | – |
| `stabilization` | Stabilisierung (immer vom Messzustand) | – | {…} | – | – |
| `search` | Suche | – | {…} | – | – |

## Verfahren

[Absolutes Endzeitraster](../theory.md#absolute_time_grid), [Zeitliche Konsistenz (Bellman-Prinzip)](../theory.md#bellman_principle)

## Einschränkungen

- keine zeitliche Konsistenz: Ergebnis hängt von der Neuplanungsfrequenz ab
- Regelfehler werden in jedem Zyklus zu Null gesetzt (keine Low-level-Robustheit)

## Umgesetzte Gleichungen

- `werling2011:Tab. 3.1`

## Quellen

[Werling et al. (2010)](../../references.md#werling2010icra), [Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_consistency.py](../../../../tests/planning/test_planning_consistency.py), [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)

Beispiele: [examples/planning/consistency.py](../../../../examples/planning/consistency.py)
