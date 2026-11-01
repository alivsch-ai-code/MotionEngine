# Stadtverkehr

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/city` · klassische Registry

**Innerstädtischer Rundkurs mit Abbiegevorgängen**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `city` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.city`](../../../../vdsim/trajectory/trajectory_generator.py#L380) |
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
| `speed_kmh` | Höchstgeschwindigkeit | km/h | 50 | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 2.5 | – | – |

## Verfahren

[GGV-begrenztes Geschwindigkeitsprofil](../theory.md#ggv_speed_profile), [Pfadkonstruktion aus Krümmungssegmenten](../theory.md#path_construction)

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/stadtverkehr.json](../../../../configs/scenarios/stadtverkehr.json)
