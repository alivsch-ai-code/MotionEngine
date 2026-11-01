# Frequenzgang (Sinus-Sweep)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/frequency_sweep` · klassische Registry

**Lenk-Sweep zur Bestimmung des Frequenzgangs (ISO 7401)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `frequency_sweep` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.frequency_sweep`](../../../../vdsim/trajectory/trajectory_generator.py#L354) |
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
| `amplitude_deg` | Lenkradamplitude | ° | 20 | – | – |
| `f_start` | Startfrequenz | Hz | 0.1 | – | – |
| `f_end` | Endfrequenz | Hz | 3 | – | – |
| `duration` | Dauer | s | 30 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Verfahren

[Frequenzgang aus dem Sinus-Sweep](../../reporting/theory.md#frequency_response_estimation)

## Quellen

[ISO 7401:2011 (2011)](../../references.md#iso7401)

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/frequenzgang_80.json](../../../../configs/scenarios/frequenzgang_80.json)
