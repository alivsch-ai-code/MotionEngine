# Aktive Wankstabilisierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `chassis_system/active_roll` · klassische Registry

**counteracts the roll moment of the lateral acceleration (gain 1 = full compensation)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `chassis_system` |
| Name | `active_roll` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.active_suspension.ActiveRollStabilization`](../../../../vdsim/controllers/active_suspension.py#L10) |
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
| `systems.active_roll_enabled` | Aktive Wankstabilisierung aktiv | – | False | – | – |
| `systems.active_roll_gain` | Wankkompensationsgrad | - | 0.8 | 0 | 1.2 |

## Verfahren

[Aktives Fahrwerk: Wankstabilisierung und Skyhook](../theory.md#active_suspension)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)
