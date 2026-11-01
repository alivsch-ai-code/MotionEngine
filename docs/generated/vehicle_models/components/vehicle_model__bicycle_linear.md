# Einspurmodell linear

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [vehicle_models](../index.md) · `vehicle_model/bicycle_linear` · klassische Registry

**Lineares Einspurmodell (6 Zustände) mit Zustandsraumdarstellung für Analyse und Reglerentwurf.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_model` |
| Name | `bicycle_linear` |
| Versionen | legacy |
| Implementierung | [`vdsim.vehicle_models.bicycle_model.LinearBicycleModel`](../../../../vdsim/vehicle_models/bicycle_model.py#L65) |
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

[Fahrwiderstände](../theory.md#driving_resistances), [Lineares Einspurmodell](../theory.md#linear_bicycle)

## Annahmen

- Kleine Winkel
- lineare Achs-Seitenkräfte
- statische Achslasten

## Einschränkungen

- Keine Sättigung der Seitenkräfte

## Validierung

- Gierverstärkung exakt wie LinearSingleTrackAnalysis (tests/test_vehicle_models.py)

## Quellen

[Mitschke und Wallentowitz (2014)](../../references.md#mitschke2014), [Rajamani (2012)](../../references.md#rajamani2012)

## Verwendung

Tests: [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)
