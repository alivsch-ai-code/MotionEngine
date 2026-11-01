# Abstandsregeltempomat (ACC)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `longitudinal_controller/acc` · klassische Registry

**Abstandsregeltempomat mit konstanter Zeitlücke.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `longitudinal_controller` |
| Name | `acc` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.speed_controller.AdaptiveCruiseControl`](../../../../vdsim/controllers/speed_controller.py#L55) |
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
| `time_gap` | – | s | 1.8 | – | – |
| `standstill_gap` | – | m | 5 | – | – |
| `k_gap` | – | 1/s² | 0.23 | – | – |
| `k_speed` | – | 1/s | 0.7 | – | – |
| `a_max` | – | m/s² | 2 | – | – |
| `a_min` | – | m/s² | -3.5 | – | – |

## Verfahren

[Abstandsregeltempomat und Notbremsassistent](../theory.md#acc_aeb)

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py), [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)

Konfigurationen: [configs/scenarios/autobahn_acc.json](../../../../configs/scenarios/autobahn_acc.json)
