# Spurwechsel

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/lane_change` · klassische Registry

**Einfacher Spurwechsel mit sinusförmiger Krümmung (Kurswinkel am Ende 0)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `lane_change` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.lane_change`](../../../../vdsim/trajectory/trajectory_generator.py#L173) |
| Schnittstelle | – |
| Sprache | python |

## Ports

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 120 | – | – |
| `width` | Querversatz | m | 3.5 | – | – |
| `duration` | Dauer | s | 6 | – | – |
| `pre_length` | Vorlauf | m | 40 | – | – |
| `post_length` | Nachlauf | m | 150 | – | – |

## Verfahren

[Krümmungsprofil des Spurwechsels](../../lane_change/theory.md#lane_change_curvature_profile), [Pfadkonstruktion aus Krümmungssegmenten](../theory.md#path_construction)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/spurwechsel_latenzkette.json](../../../../configs/scenarios/spurwechsel_latenzkette.json)
