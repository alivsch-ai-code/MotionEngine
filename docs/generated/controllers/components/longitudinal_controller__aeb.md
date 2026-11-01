# Notbremsassistent (AEB)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `longitudinal_controller/aeb` · klassische Registry

**Time-to-collision based staged braking on top of a base longitudinal controller**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `longitudinal_controller` |
| Name | `aeb` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.speed_controller.EmergencyBrakeAssist`](../../../../vdsim/controllers/speed_controller.py#L86) |
| Schnittstelle | `vdsim.core.interfaces.LongitudinalController` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `acceleration` | `float` | – | Beschleunigungsanforderung in m/s² | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `base` | – | – | acc | – | – |
| `ttc_warning` | – | s | 2.6 | – | – |
| `ttc_partial` | – | s | 2 | – | – |
| `ttc_full` | – | s | 1.3 | – | – |
| `partial_decel` | – | m/s² | 5 | – | – |
| `full_decel` | – | m/s² | 9.5 | – | – |

## Verfahren

[Abstandsregeltempomat und Notbremsassistent](../theory.md#acc_aeb)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)

Konfigurationen: [configs/scenarios/notbremsassistent_70.json](../../../../configs/scenarios/notbremsassistent_70.json)
