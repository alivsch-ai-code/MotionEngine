# trajectory_loader/matlab

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `trajectory_loader/matlab` · klassische Registry

**.mat (v5/v7) with variables x, y[, v] or a struct with these fields, or an N x 2/3 matrix**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_loader` |
| Name | `matlab` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_loader.load_matlab`](../../../../vdsim/trajectory/trajectory_loader.py#L160) |
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

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)
