# Bremsen (Geradeaus)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/braking` · klassische Registry

**Bremsung aus konstanter Geschwindigkeit**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `braking` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.braking`](../../../../vdsim/trajectory/trajectory_generator.py#L275) |
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
| `speed_kmh` | Anfangsgeschwindigkeit | km/h | 100 | – | – |
| `deceleration` | Verzögerung | m/s² | 10 | – | – |
| `brake_time` | Bremsbeginn | s | 1 | – | – |

## Verwendung

Tests: [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py), [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/scenarios/bremsen_100_abs.json](../../../../configs/scenarios/bremsen_100_abs.json), [configs/scenarios/bremsen_split_mu.json](../../../../configs/scenarios/bremsen_split_mu.json)
