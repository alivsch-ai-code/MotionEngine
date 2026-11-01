# trajectory_loader/opendrive

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `trajectory_loader/opendrive` · klassische Registry

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_loader` |
| Name | `opendrive` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_loader.load_xodr`](../../../../vdsim/trajectory/trajectory_loader.py#L185) |
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
| `road_id` | – | – | – | – | – |
| `lane_id` | – | – | -1 | – | – |

## Verfahren

[Import von GPS- und OpenDRIVE-Daten](../theory.md#trajectory_import)

## Quellen

[ASAM OpenDRIVE](../../references.md#asam_opendrive)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py), [tests/test_trajectory.py](../../../../tests/test_trajectory.py)
