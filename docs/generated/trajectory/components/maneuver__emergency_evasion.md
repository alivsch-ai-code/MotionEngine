# Notausweichen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/emergency_evasion` · klassische Registry

**Schnelles Ausweichen um ein Hindernis und Rückkehr in die Spur**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `emergency_evasion` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.emergency_evasion`](../../../../vdsim/trajectory/trajectory_generator.py#L263) |
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
| `speed_kmh` | Geschwindigkeit | km/h | 60 | – | – |
| `offset` | Ausweichversatz | m | 3 | – | – |
| `evade_length` | Ausweichstrecke | m | 22 | – | – |
| `hold_length` | Haltestrecke | m | 8 | – | – |
| `return_length` | Rückkehrstrecke | m | 28 | – | – |

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/notausweichen_60.json](../../../../configs/scenarios/notausweichen_60.json)
