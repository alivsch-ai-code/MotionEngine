# Acht

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/figure_eight` · klassische Registry

**Liegende Acht aus zwei Kreisen**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `figure_eight` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.figure_eight`](../../../../vdsim/trajectory/trajectory_generator.py#L250) |
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
| `radius` | Radius | m | 20 | – | – |
| `speed_kmh` | Geschwindigkeit | km/h | 30 | – | – |
| `laps` | Durchgänge | - | 1 | – | – |

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/acht_30.json](../../../../configs/scenarios/acht_30.json)
