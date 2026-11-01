# Beschleunigen (0-100 km/h)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/acceleration` · klassische Registry

**Volllastbeschleunigung aus dem Stand**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `acceleration` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.acceleration`](../../../../vdsim/trajectory/trajectory_generator.py#L286) |
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
| `target_kmh` | Zielgeschwindigkeit | km/h | 100 | – | – |
| `request` | Angeforderte Beschleunigung | m/s² | 12 | – | – |

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/beschleunigen_0_100_ev.json](../../../../configs/scenarios/beschleunigen_0_100_ev.json)
