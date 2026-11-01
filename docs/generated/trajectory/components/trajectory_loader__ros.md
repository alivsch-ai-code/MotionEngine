# trajectory_loader/ros

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `trajectory_loader/ros` · klassische Registry

**nav_msgs/Path as YAML (rostopic echo / ros2 topic echo) or JSON**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `trajectory_loader` |
| Name | `ros` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_loader.load_ros`](../../../../vdsim/trajectory/trajectory_loader.py#L110) |
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
