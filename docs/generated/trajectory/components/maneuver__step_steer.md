# Lenkwinkelsprung (ISO 7401)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/step_steer` · klassische Registry

**Sprungförmige Lenkeingabe bei konstanter Geschwindigkeit**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `step_steer` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.step_steer`](../../../../vdsim/trajectory/trajectory_generator.py#L321) |
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
| `steering_wheel_deg` | Lenkradwinkel | ° | 40 | – | – |
| `rise_time` | Anstiegszeit | s | 0.15 | – | – |
| `duration` | Dauer | s | 6 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Quellen

[ISO 7401:2011 (2011)](../../references.md#iso7401)

## Verwendung

Tests: [tests/stabilization/test_stabilization_models.py](../../../../tests/stabilization/test_stabilization_models.py), [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py), [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/scenarios/lenkwinkelsprung_80.json](../../../../configs/scenarios/lenkwinkelsprung_80.json)
