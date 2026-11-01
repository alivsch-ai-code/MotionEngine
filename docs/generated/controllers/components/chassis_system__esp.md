# ESP

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `chassis_system/esp` · klassische Registry

**yaw-rate control by single-wheel braking (oversteer: outer front, understeer: inner rear)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `chassis_system` |
| Name | `esp` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.esp_controller.ElectronicStabilityProgram`](../../../../vdsim/controllers/esp_controller.py#L33) |
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
| `systems.esp_enabled` | ESP aktiv | – | False | – | – |
| `systems.esp_gain` | ESP Verstärkung Giermoment | N m s/rad | 20000 | 0 | – |
| `systems.esp_deadband` | ESP Totband Gierrate | rad/s | 0.03 | 0 | – |

## Verfahren

[ESP – Gierratenregelung durch Einzelradbremsung](../theory.md#esp_yaw_control), [Eigenlenkgradient und charakteristische Geschwindigkeit](../../analysis/theory.md#understeer_gradient)

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012), [Reif (2010)](../../references.md#reif2010), [van Zanten et al. (1995)](../../references.md#vanzanten1995)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py), [tests/stabilization/test_stabilization_dynamic.py](../../../../tests/stabilization/test_stabilization_dynamic.py), [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)

Konfigurationen: [configs/scenarios/bremsen_split_mu.json](../../../../configs/scenarios/bremsen_split_mu.json), [configs/scenarios/sinus_haltezeit_esp.json](../../../../configs/scenarios/sinus_haltezeit_esp.json)
