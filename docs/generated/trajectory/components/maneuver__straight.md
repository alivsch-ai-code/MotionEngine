# Geradeausfahrt

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/straight` · klassische Registry

**Gerade Strecke mit konstanter Geschwindigkeit**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `straight` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.straight`](../../../../vdsim/trajectory/trajectory_generator.py#L164) |
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
| `length` | Länge | m | 300 | – | – |
| `speed_kmh` | Geschwindigkeit | km/h | 50 | – | – |

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py), [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/ad_scenarios/kreuzung_ampel_geradeaus.json](../../../../configs/ad_scenarios/kreuzung_ampel_geradeaus.json), [configs/scenarios/autobahn_acc.json](../../../../configs/scenarios/autobahn_acc.json), [configs/scenarios/komfort_strasse_klasse_c.json](../../../../configs/scenarios/komfort_strasse_klasse_c.json), [configs/scenarios/notbremsassistent_70.json](../../../../configs/scenarios/notbremsassistent_70.json)
