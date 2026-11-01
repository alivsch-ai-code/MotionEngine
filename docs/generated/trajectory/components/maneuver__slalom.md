# Slalom

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/slalom` · klassische Registry

**cones at x_i = pre + spacing * (i + 0.5); full lateral amplitude from half a spacing before the first to half a spacing after the last cone, smooth ramps outside**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `slalom` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.slalom`](../../../../vdsim/trajectory/trajectory_generator.py#L221) |
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
| `speed_kmh` | Geschwindigkeit | km/h | 45 | – | – |
| `spacing` | Pylonenabstand | m | 18 | – | – |
| `n_cones` | Anzahl Pylonen | - | 8 | – | – |
| `amplitude` | Seitlicher Abstand | m | 1.3 | – | – |

## Verwendung

Tests: [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/slalom_45.json](../../../../configs/scenarios/slalom_45.json)
