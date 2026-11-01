# Mehrkörpermodell (24 Zustände)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [vehicle_models](../index.md) · `vehicle_model/multibody` · klassische Registry

**Mehrkörpermodell mit 24 Zuständen – Aufbau mit Hub, Wanken, Nicken, vier ungefederte Massen, Raddrehung, Fahrbahnanregung.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_model` |
| Name | `multibody` |
| Versionen | legacy |
| Implementierung | [`vdsim.vehicle_models.multibody_model.MultibodyModel`](../../../../vdsim/vehicle_models/multibody_model.py#L25) |
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

[Fahrwiderstände](../theory.md#driving_resistances), [Mehrkörpermodell mit Vertikaldynamik](../theory.md#multibody)

## Annahmen

- Kleine Aufbauwinkel
- lineare Feder- und Reifensteifigkeiten
- Dämpferkennlinien als Tabellen

## Einschränkungen

- Fahrbahnprofil links und rechts gleich
- Reifen als Punktkontakt

## Quellen

[Mitschke und Wallentowitz (2014)](../../references.md#mitschke2014), [Schramm et al. (2018)](../../references.md#schramm2018)

## Verwendung

Tests: [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/scenarios/komfort_strasse_klasse_c.json](../../../../configs/scenarios/komfort_strasse_klasse_c.json)
