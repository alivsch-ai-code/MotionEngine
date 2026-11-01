# Torque Vectoring

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `chassis_system/torque_vectoring` · klassische Registry

**yaw moment from left/right drive-torque difference on the driven axles**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `chassis_system` |
| Name | `torque_vectoring` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.torque_vectoring.TorqueVectoring`](../../../../vdsim/controllers/torque_vectoring.py#L11) |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

## Parameter

_Keine Parameter._

Zugehörige Fahrzeugparameter:

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.torque_vectoring_enabled` | Torque Vectoring aktiv | – | False | – | – |
| `systems.torque_vectoring_gain` | Torque Vectoring Verstärkung | N m s/rad | 30000 | 0 | – |
| `systems.torque_vectoring_target` | TV Ziel-Eigenlenkverhalten (0 = neutral, 1 = passiv) | - | 0 | -0.5 | 1 |
| `powertrain.torque_vectoring_max_torque` | Torque Vectoring max. Differenzmoment (Rad) | N m | 800 | 0 | – |

## Verfahren

[Torque Vectoring](../theory.md#torque_vectoring)

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)
