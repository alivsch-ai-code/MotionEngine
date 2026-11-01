# MPC (linear zeitvariant)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/mpc` · Version 1.0.0

**Linear zeitvariante modellprädiktive Querregelung entlang des Trajektorienhorizonts mit Lenkwinkel- und Lenkratenbeschränkung.**

## Zweck

Vergleichsregler, der Stellgrößenbeschränkungen explizit berücksichtigt (Werling Tab. 4.1).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `mpc` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_lateral.MPC`](../../../../vdsim/stabilization/classic_lateral.py#L353) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `horizon` | Prädiktionsschritte N | - | 20 | 3 | 100 |
| `dt` | Prädiktionsschrittweite | s | 0.05 | 0.005 | – |
| `q_e` | Gewicht Querfehler | 1/m² | 4 | 0 | – |
| `q_psi` | Gewicht Kursfehler | 1/rad² | 4 | 0 | – |
| `r_delta` | Gewicht Lenkwinkel gegenüber Vorsteuerung | 1/rad² | 1 | 0 | – |
| `r_rate` | Gewicht Lenkrate | s²/rad² | 0.5 | 1e-06 | – |
| `max_rate` | max. Lenkrate | rad/s | 0.6 | 0.01 | – |
| `max_angle` | max. Lenkwinkel (<0: Fahrzeug) | rad | -1 | – | – |
| `update_period` | Neuberechnungsperiode | s | 0.05 | 0 | – |

## Theorie

Zustände $[e_y,e_\psi,\delta]$, Eingang $\dot\delta$; $\dot e_y=v_ke_\psi$, $\dot e_\psi=v_k(\delta/(l+EG\,v_k^2)-\kappa_k)$ mit $v_k,\kappa_k$ der Solltrajektorie zu den Horizontzeitpunkten; kondensiertes QP, gelöst mit ADMM.

## Verfahren

[Mpc lateral](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Kinematik mit Untersteuergradient (quasi-stationäre Gierdynamik)
- Vorwärtsfahrt

## Einschränkungen

- Kein Stabilitätsbeweis ohne Endkosten/Endbeschränkung
- Rechenaufwand höher

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Borrelli et al. (2017)](../../references.md#borrelli2017), [Rajamani (2012)](../../references.md#rajamani2012), [Werling (2011)](../../references.md#werling2011)

## Expertenmodus: Herleitungen und Hinweise

Rekursive Machbarkeit ist durch die Box-Beschränkungen allein nicht garantiert; in der Praxis stabil bei hinreichend langem Horizont (Rawlings/Mayne).
