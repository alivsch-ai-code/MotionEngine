# ISO-Ausweichtest (ISO 3888-2)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/iso_obstacle_avoidance` · klassische Registry

**Ausweichmanöver nach ISO 3888-2 ("Elchtest")**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `iso_obstacle_avoidance` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.iso_obstacle_avoidance`](../../../../vdsim/trajectory/trajectory_generator.py#L204) |
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
| `speed_kmh` | Einfahrgeschwindigkeit | km/h | 60 | – | – |
| `vehicle_width` | Fahrzeugbreite | m | 1.85 | – | – |

## Verfahren

[Pfadkonstruktion aus Krümmungssegmenten](../theory.md#path_construction)

## Quellen

[ISO 3888-2:2011 (2011)](../../references.md#iso3888_2)

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/iso_ausweichtest_60.json](../../../../configs/scenarios/iso_ausweichtest_60.json)
