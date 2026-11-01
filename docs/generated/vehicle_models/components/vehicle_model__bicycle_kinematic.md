# Einspurmodell kinematisch

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [vehicle_models](../index.md) · `vehicle_model/bicycle_kinematic` · klassische Registry

**Kinematisches Einspurmodell ohne Reifenschlupf mit Vorder- und Hinterachslenkung.**

## Zweck

Bahnplanung, Latenzstudien und niedrige Querbeschleunigung.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_model` |
| Name | `bicycle_kinematic` |
| Versionen | legacy |
| Implementierung | [`vdsim.vehicle_models.bicycle_model.KinematicBicycleModel`](../../../../vdsim/vehicle_models/bicycle_model.py#L36) |
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

[Fahrwiderstände](../theory.md#driving_resistances), [Kinematisches Einspurmodell](../theory.md#kinematic_bicycle)

## Annahmen

- Kein Schräglauf
- Ackermann-Geometrie
- Längskraft auf mu m g begrenzt

## Einschränkungen

- Ungültig bei hoher Querbeschleunigung (etwa über 4 m/s²)

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012)

## Verwendung

Tests: [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py), [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/scenarios/spurwechsel_latenzkette.json](../../../../configs/scenarios/spurwechsel_latenzkette.json)
