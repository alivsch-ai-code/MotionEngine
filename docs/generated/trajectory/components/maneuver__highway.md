# Autobahnfahrt

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/highway` · klassische Registry

**Autobahn mit Klothoiden-Kurven und Spurwechsel**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `highway` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.highway`](../../../../vdsim/trajectory/trajectory_generator.py#L367) |
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
| `speed_kmh` | Richtgeschwindigkeit | km/h | 130 | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 2 | – | – |

## Verfahren

[GGV-begrenztes Geschwindigkeitsprofil](../theory.md#ggv_speed_profile), [Pfadkonstruktion aus Krümmungssegmenten](../theory.md#path_construction)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/autobahn_spurhalteassistent.json](../../../../configs/scenarios/autobahn_spurhalteassistent.json)
