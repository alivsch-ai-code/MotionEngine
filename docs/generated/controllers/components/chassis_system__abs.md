# ABS

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `chassis_system/abs` · klassische Registry

**Antiblockiersystem über radindividuellen Modulationsfaktor des Bremsmoments.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `chassis_system` |
| Name | `abs` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.slip_control.AntiLockBraking`](../../../../vdsim/controllers/slip_control.py#L29) |
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
| `systems.abs_enabled` | ABS aktiv | – | True | – | – |
| `systems.abs_target_slip` | ABS Zielschlupf | - | 0.12 | 0.02 | 0.4 |

## Verfahren

[Schlupfregelung ABS und ASR](../theory.md#wheel_slip_control)

## Quellen

[Reif (2010)](../../references.md#reif2010)

## Verwendung

Tests: [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/vehicles/ev_sedan.json](../../../../configs/vehicles/ev_sedan.json), [configs/vehicles/mid_size_sedan.json](../../../../configs/vehicles/mid_size_sedan.json), [configs/vehicles/sports_car.json](../../../../configs/vehicles/sports_car.json), [configs/vehicles/suv.json](../../../../configs/vehicles/suv.json)
