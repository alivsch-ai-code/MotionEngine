# Rennstrecke (Ideallinie)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/race_track` · klassische Registry

**Rundkurs mit berechneter Ideallinie (minimale Krümmung) und GGV-Geschwindigkeitsprofil**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `race_track` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.race_track`](../../../../vdsim/trajectory/trajectory_generator.py#L436) |
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
| `track_width` | Streckenbreite | m | 12 | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 7 | – | – |
| `ax_max` | Max. Längsbeschleunigung | m/s² | 3.5 | – | – |
| `ax_min` | Max. Verzögerung | m/s² | -6.5 | – | – |
| `v_max_kmh` | Höchstgeschwindigkeit | km/h | 230 | – | – |
| `laps` | Runden | - | 1 | – | – |

## Verfahren

[GGV-begrenztes Geschwindigkeitsprofil](../theory.md#ggv_speed_profile), [Ideallinie mit minimaler Krümmung](../theory.md#racing_line)

## Quellen

[Braghin et al. (2008)](../../references.md#braghin2008), [Kapania et al. (2016)](../../references.md#kapania2016)

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/rennstrecke_sportwagen.json](../../../../configs/scenarios/rennstrecke_sportwagen.json)
