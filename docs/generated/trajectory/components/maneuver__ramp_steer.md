# Lenkwinkelrampe (ISO 4138)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/ramp_steer` · klassische Registry

**Langsam steigender Lenkwinkel bei konstanter Geschwindigkeit**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `ramp_steer` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.ramp_steer`](../../../../vdsim/trajectory/trajectory_generator.py#L330) |
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
| `steer_rate_deg` | Lenkradwinkelgeschwindigkeit | °/s | 8 | – | – |
| `duration` | Dauer | s | 20 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Quellen

[ISO 4138:2021 (2021)](../../references.md#iso4138)

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)
