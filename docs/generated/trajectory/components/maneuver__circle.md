# Kreisfahrt (ISO 4138)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/circle` · klassische Registry

**Stationäre Kreisfahrt mit langsam steigender Geschwindigkeit (Eigenlenkgradient)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `circle` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.circle`](../../../../vdsim/trajectory/trajectory_generator.py#L239) |
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
| `radius` | Radius | m | 40 | – | – |
| `laps` | Runden | - | 3 | – | – |
| `speed_start_kmh` | Startgeschwindigkeit | km/h | 20 | – | – |
| `speed_end_kmh` | Endgeschwindigkeit | km/h | 70 | – | – |

## Verfahren

[Pfadkonstruktion aus Krümmungssegmenten](../theory.md#path_construction)

## Quellen

[ISO 4138:2021 (2021)](../../references.md#iso4138)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/kreisfahrt_r40.json](../../../../configs/scenarios/kreisfahrt_r40.json)
