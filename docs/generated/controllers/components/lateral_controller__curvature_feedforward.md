# Krümmungsvorsteuerung (ohne Rückführung)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `lateral_controller/curvature_feedforward` · klassische Registry

**Steers the kinematic angle of the path curvature at the current position, no feedback**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `lateral_controller` |
| Name | `curvature_feedforward` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.open_loop.CurvatureFeedforward`](../../../../vdsim/controllers/open_loop.py#L26) |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

## Parameter

_Keine Parameter._

## Verfahren

[Kinematisches Einspurmodell](../../vehicle_models/theory.md#kinematic_bicycle)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)

Konfigurationen: [configs/scenarios/spurwechsel_latenzkette.json](../../../../configs/scenarios/spurwechsel_latenzkette.json)
