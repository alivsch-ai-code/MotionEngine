# Antriebsschlupfregelung (ASR/TCS)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `chassis_system/tcs` · klassische Registry

**Antriebsschlupfregelung über Modulationsfaktor des Antriebsmoments.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `chassis_system` |
| Name | `tcs` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.slip_control.TractionControl`](../../../../vdsim/controllers/slip_control.py#L45) |
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
| `systems.tcs_enabled` | ASR/TCS aktiv | – | True | – | – |
| `systems.tcs_target_slip` | TCS Zielschlupf | - | 0.1 | 0.02 | 0.4 |

## Verfahren

[Schlupfregelung ABS und ASR](../theory.md#wheel_slip_control)

## Quellen

[Reif (2010)](../../references.md#reif2010)

## Verwendung

Konfigurationen: [configs/vehicles/ev_sedan.json](../../../../configs/vehicles/ev_sedan.json), [configs/vehicles/mid_size_sedan.json](../../../../configs/vehicles/mid_size_sedan.json), [configs/vehicles/sports_car.json](../../../../configs/vehicles/sports_car.json), [configs/vehicles/suv.json](../../../../configs/vehicles/suv.json)
