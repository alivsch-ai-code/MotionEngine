# trajectory_loader/gpx

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `trajectory_loader/gpx` · klassische Registry

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_loader` |
| Name | `gpx` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_loader.load_gpx`](../../../../vdsim/trajectory/trajectory_loader.py#L121) |
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
