# Aktive Dämpfung (Skyhook)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `chassis_system/active_damping` · klassische Registry

**skyhook: damper force proportional to the absolute body velocity at each corner**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `chassis_system` |
| Name | `active_damping` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.active_suspension.SkyhookDamping`](../../../../vdsim/controllers/active_suspension.py#L31) |
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
| `systems.active_damping_enabled` | Aktive Dämpfung (Skyhook) aktiv | – | False | – | – |
| `systems.skyhook_gain` | Skyhook-Dämpfung | N s/m | 2500 | 0 | – |

## Verfahren

[Aktives Fahrwerk: Wankstabilisierung und Skyhook](../theory.md#active_suspension)

## Quellen

[Karnopp et al. (1974)](../../references.md#karnopp1974)
