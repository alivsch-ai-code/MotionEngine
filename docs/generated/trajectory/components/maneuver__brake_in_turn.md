# Bremsen in der Kurve (ISO 7975)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/brake_in_turn` · klassische Registry

**Stationäre Kreisfahrt, dann Bremsung mit konstanter Verzögerung**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `brake_in_turn` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.brake_in_turn`](../../../../vdsim/trajectory/trajectory_generator.py#L297) |
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
| `radius` | Radius | m | 100 | – | – |
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `deceleration` | Verzögerung | m/s² | 4 | – | – |
| `brake_time` | Bremsbeginn | s | 6 | – | – |

## Quellen

[ISO 7975:2019 (2019)](../../references.md#iso7975)

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/bremsen_in_der_kurve.json](../../../../configs/scenarios/bremsen_in_der_kurve.json)
