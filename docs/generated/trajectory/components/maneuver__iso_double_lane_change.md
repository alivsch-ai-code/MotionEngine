# ISO-Doppelspurwechsel (ISO 3888-1)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/iso_double_lane_change` · klassische Registry

**Doppelter Spurwechsel mit Pylonengassen nach ISO 3888-1 (Versatz 3,5 m)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `iso_double_lane_change` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.iso_double_lane_change`](../../../../vdsim/trajectory/trajectory_generator.py#L189) |
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
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `vehicle_width` | Fahrzeugbreite | m | 1.85 | – | – |

## Verfahren

[Pfadkonstruktion aus Krümmungssegmenten](../theory.md#path_construction)

## Quellen

[ISO 3888-1:2018 (2018)](../../references.md#iso3888_1)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py), [tests/stabilization/test_stabilization_models.py](../../../../tests/stabilization/test_stabilization_models.py), [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/iso_doppelspurwechsel_80.json](../../../../configs/scenarios/iso_doppelspurwechsel_80.json), [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../../configs/scenarios/iso_doppelspurwechsel_mpc.json)
