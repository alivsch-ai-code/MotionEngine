# Hinterachslenkung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `chassis_system/rear_steering` · klassische Registry

**speed-dependent ratio: counter-phase at low speed (agility), in-phase at high speed (stability)**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `chassis_system` |
| Name | `rear_steering` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.rear_axle_steering.RearAxleSteering`](../../../../vdsim/controllers/rear_axle_steering.py#L10) |
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
| `systems.rear_steering_enabled` | Hinterachslenkung aktiv | – | False | – | – |
| `systems.rear_steering_ratio_low` | HAL Verhältnis niedrige Geschw. (gegensinnig < 0) | - | -0.2 | -1 | 1 |
| `systems.rear_steering_ratio_high` | HAL Verhältnis hohe Geschw. (gleichsinnig > 0) | - | 0.1 | -1 | 1 |
| `systems.rear_steering_speed_low` | HAL Übergang Beginn | m/s | 8 | 0 | – |
| `systems.rear_steering_speed_high` | HAL Übergang Ende | m/s | 22 | 0 | – |

## Verfahren

[Hinterachslenkung](../theory.md#rear_axle_steering)

## Quellen

[Mitschke und Wallentowitz (2014)](../../references.md#mitschke2014)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)
