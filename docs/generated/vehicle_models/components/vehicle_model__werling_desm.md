# Dynamisches Einspurmodell, isotroper Reifen (Werling Modell 4)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [vehicle_models](../index.md) · `vehicle_model/werling_desm` · klassische Registry

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_model` |
| Name | `werling_desm` |
| Versionen | legacy |
| Implementierung | [`vdsim.vehicle_models.werling_models.WerlingDynamicModel`](../../../../vdsim/vehicle_models/werling_models.py#L246) |
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

## Verwendung

Tests: [tests/stabilization/test_stabilization_dynamic.py](../../../../tests/stabilization/test_stabilization_dynamic.py), [tests/stabilization/test_stabilization_kinematic.py](../../../../tests/stabilization/test_stabilization_kinematic.py), [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py), [tests/stabilization/test_stabilization_models.py](../../../../tests/stabilization/test_stabilization_models.py)

Konfigurationen: [configs/stabilization/vehicle_layers_default.json](../../../../configs/stabilization/vehicle_layers_default.json)
