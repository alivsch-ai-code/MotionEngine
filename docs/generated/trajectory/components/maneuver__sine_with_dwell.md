# Sinus mit Haltezeit (FMVSS 126)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/sine_with_dwell` · klassische Registry

**ESC-Prüfmanöver: 0,7-Hz-Sinus mit 500 ms Haltezeit**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `sine_with_dwell` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.sine_with_dwell`](../../../../vdsim/trajectory/trajectory_generator.py#L338) |
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
| `amplitude_deg` | Lenkradamplitude | ° | 180 | – | – |
| `frequency` | Frequenz | Hz | 0.7 | – | – |
| `dwell` | Haltezeit | s | 0.5 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Quellen

[FMVSS No. 126 (49 CFR 571.126) (2007)](../../references.md#fmvss126)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/sinus_haltezeit_esp.json](../../../../configs/scenarios/sinus_haltezeit_esp.json)
