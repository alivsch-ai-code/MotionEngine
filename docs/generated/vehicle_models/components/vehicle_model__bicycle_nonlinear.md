# Einspurmodell nichtlinear

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [vehicle_models](../index.md) · `vehicle_model/bicycle_nonlinear` · klassische Registry

**Nichtlineares Einspurmodell mit Reifenmodell je Achse, Längslastverlagerung und Reibellipse.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_model` |
| Name | `bicycle_nonlinear` |
| Versionen | legacy |
| Implementierung | [`vdsim.vehicle_models.bicycle_model.NonlinearBicycleModel`](../../../../vdsim/vehicle_models/bicycle_model.py#L121) |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

## Parameter

_Keine Parameter._

## Verfahren

[Fahrwiderstände](../theory.md#driving_resistances), [Nichtlineares Einspurmodell](../theory.md#nonlinear_bicycle)

## Annahmen

- Keine Wankdynamik
- Seitenkraft je Achse aus einem Reifen mit halber Achslast mal zwei

## Quellen

[Mitschke und Wallentowitz (2014)](../../references.md#mitschke2014), [Pacejka (2012)](../../references.md#pacejka2012)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/scenarios/autobahn_acc.json](../../../../configs/scenarios/autobahn_acc.json)
