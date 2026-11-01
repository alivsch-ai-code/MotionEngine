# MPC

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `lateral_controller/mpc` · klassische Registry

**Lineare modellprädiktive Bahnregelung auf der Fehlerdynamik des Einspurmodells mit Krümmungsvorschau und Lenkwinkelgrenzen.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `lateral_controller` |
| Name | `mpc` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.mpc_controller.MPCController`](../../../../vdsim/controllers/mpc_controller.py#L20) |
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

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Horizontlänge N in Schritten | - | 25 | – | – |
| `dt` | Diskretisierung des Vorhersagemodells | s | 0.05 | – | – |
| `q_lateral` | Gewicht der Querablage | 1/m² | 10 | – | – |
| `q_heading` | Gewicht des Kurswinkelfehlers | 1/rad² | 5 | – | – |
| `r_steer` | Gewicht des Lenkwinkels | 1/rad² | 1 | – | – |
| `r_rate` | Gewicht der Lenkwinkeländerung je Schritt | 1/rad² | 20 | – | – |
| `update_period` | Neuberechnungsperiode | s | 0.01 | – | – |

## Verfahren

[Lineares Einspurmodell](../../vehicle_models/theory.md#linear_bicycle), [Modellprädiktive Bahnregelung (lineare MPC)](../theory.md#path_mpc)

## Einschränkungen

- Lineare Reifen im Vorhersagemodell
- konstante Geschwindigkeit über den Horizont

## Quellen

[Borrelli et al. (2017)](../../references.md#borrelli2017), [Rajamani (2012)](../../references.md#rajamani2012), [Stark und Parker (1995)](../../references.md#stark1995)

## Verwendung

Tests: [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py)

Konfigurationen: [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../../configs/scenarios/iso_doppelspurwechsel_mpc.json), [configs/scenarios/stadtverkehr.json](../../../../configs/scenarios/stadtverkehr.json)
