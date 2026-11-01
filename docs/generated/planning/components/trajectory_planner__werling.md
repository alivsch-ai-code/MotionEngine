# Trajektorienplaner (Werling)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `trajectory_planner/werling` · Version 1.0.0

**Trajektorienplanung nach Werling: optimale Polynome in Frenet-Koordinaten, diskretisierte Zielmannigfaltigkeiten auf absolutem Zeitraster, zeitliche Konsistenz und Bi-level-Stabilisierung.**

## Zweck

Reaktive, zeitkritische Kollisionsvermeidung mit kombinierter Längs- und Queroptimierung, die bei inaktiven Restriktionen dank Bellman-Prinzip zeitlich konsistent ist (Werling 2011, Kap. 3).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_planner` |
| Name | `werling` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.planner.WerlingPlanner`](../../../../vdsim/planning/planner.py#L156) |
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

## Theorie

Quer- und Längsbewegung sind Ausgang einer Integratorkette; die ruckoptimalen Lösungen sind quintische (fester Endzustand) bzw. quartische Polynome (freie Endposition). Endzeitpunkte und Endversätze werden auf der Zielmannigfaltigkeit diskretisiert; die beste restriktionskonforme Kombination wird lazy in aufsteigender Kostenreihenfolge gesucht.

## Verfahren

[Absolutes Endzeitraster](../theory.md#absolute_time_grid), [Zeitliche Konsistenz (Bellman-Prinzip)](../theory.md#bellman_principle), [Bi-level-Stabilisierung (Planerseite)](../theory.md#bilevel_stabilization), [Querkandidaten d(t) und d(s)](../theory.md#lateral_sampling), [Lazy-Auswahl](../theory.md#lazy_selection), [Längskandidaten](../theory.md#longitudinal_sampling), [Quartische Optimalpolynome](../theory.md#quartic_polynomial), [Quintische Optimalpolynome](../theory.md#quintic_polynomial), [Ablösestrategie](../theory.md#replacement_strategy)

## Annahmen

- Schwimmwinkel am Referenzpunkt = 0 für die Kollisionsprüfung
- Vorderfahrzeuge mit konstanter Beschleunigung (geklemmt im Stillstand)
- Referenzkurve mit stetiger Krümmungsänderung (Bemerkung 4)

## Einschränkungen

- zeitliche Konsistenz nur bei inaktiven Restriktionen und rein konsistenten Kostentermen
- Funktionenklasse auf doppelte Kursänderung beschränkt (keine Labyrinth-Manöver)
- Richtungswechsel (ς) nur im Stillstand über die Verhaltensebene

## Validierung

- tests/planning/test_planning_consistency.py
- tests/planning/test_planning_modes.py
- tests/planning/test_planning_polynomials.py

## Umgesetzte Gleichungen

- `werling2011:(3.1)`
- `werling2011:(3.2)`
- `werling2011:(3.4)`
- `werling2011:(3.8)`
- `werling2011:(3.12)`
- `werling2011:(3.13)`
- `werling2011:(3.14)`
- `werling2011:(3.15)`
- `werling2011:Tab. 3.1`
- `werling2011:(A.1)-(A.8)`

## Quellen

[Werling et al. (2010)](../../references.md#werling2010icra), [Werling (2011)](../../references.md#werling2011), [Werling et al. (2012)](../../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../../references.md#ziegler2010iv)

## Designentscheidungen

- **decision:** Absolutes Endzeitraster + Schutz des alten Optimums; **reason:** Satz 3 (zeitliche Konsistenz); **alternatives:** relatives Raster (trajectory_planner/frenet_naive)
- **decision:** Exakte Polynom-Repräsentation im Plan; **reason:** Bellman exakt, keine Interpolation
- **decision:** Restriktionen, Kostenterme und Kollisionsprüfer als Plugins; **reason:** erweiterbar

## Erweiterungspunkte

- @component(kind='cost_term')
- @component(kind='constraint')
- @component(kind='collision_checker')

## Verwendung

Tests: [tests/gui_ad/test_gui_ad_workbench.py](../../../../tests/gui_ad/test_gui_ad_workbench.py), [tests/planning/test_planning_collision.py](../../../../tests/planning/test_planning_collision.py), [tests/planning/test_planning_consistency.py](../../../../tests/planning/test_planning_consistency.py), [tests/planning/test_planning_modes.py](../../../../tests/planning/test_planning_modes.py), [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)

Beispiele: [examples/planning/consistency.py](../../../../examples/planning/consistency.py), [examples/planning/evasion.py](../../../../examples/planning/evasion.py), [examples/planning/following.py](../../../../examples/planning/following.py), [examples/planning/lane_change.py](../../../../examples/planning/lane_change.py), [examples/planning/stopping.py](../../../../examples/planning/stopping.py)

Konfigurationen: [configs/planning/comfort.json](../../../../configs/planning/comfort.json), [configs/planning/default.json](../../../../configs/planning/default.json), [configs/planning/sporty.json](../../../../configs/planning/sporty.json)
