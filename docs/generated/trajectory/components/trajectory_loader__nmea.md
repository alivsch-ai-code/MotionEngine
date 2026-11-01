# trajectory_loader/nmea

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `trajectory_loader/nmea` · klassische Registry

**$GPRMC / $GNRMC sentences (position + speed over ground)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_loader` |
| Name | `nmea` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_loader.load_nmea`](../../../../vdsim/trajectory/trajectory_loader.py#L142) |
| Schnittstelle | – |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |

## Verfahren

[Import von GPS- und OpenDRIVE-Daten](../theory.md#trajectory_import)

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)
