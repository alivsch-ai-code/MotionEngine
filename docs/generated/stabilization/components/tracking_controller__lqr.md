# LQR (geschwindigkeitsgeplant)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/lqr` · Version 1.0.0

**Zustandsregler auf das Querfehlermodell des Einspurmodells mit diskreter Riccati-Lösung, Gain-Scheduling über die Geschwindigkeit und stationärer Vorsteuerung.**

## Zweck

Optimaler linearer Vergleichsregler (Rajamani 3.2).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `lqr` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_lateral.LQR`](../../../../vdsim/stabilization/classic_lateral.py#L261) |
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
| `q_e` | Gewicht Querfehler | 1/m² | 1 | 0 | – |
| `q_e_dot` | Gewicht Querfehlerrate | s²/m² | 0 | 0 | – |
| `q_psi` | Gewicht Kursfehler | 1/rad² | 1 | 0 | – |
| `q_psi_dot` | Gewicht Kursfehlerrate | s²/rad² | 0 | 0 | – |
| `r_delta` | Gewicht Lenkwinkel | 1/rad² | 10 | 1e-06 | – |
| `dt` | Diskretisierung | s | 0.01 | 0.001 | – |
| `v_min` | untere Stützstelle Gain-Scheduling | m/s | 2 | 0.5 | – |
| `v_max` | obere Stützstelle Gain-Scheduling | m/s | 50 | 5 | – |

## Theorie

$x=[e_1,\dot e_1,e_2,\dot e_2]$, $u=-Kx+\delta_{ff}$, $K$ aus der DARE des mit ZOH diskretisierten Modells, $\delta_{ff}=l\kappa+K_V v^2\kappa-k_3e_{2,ss}$.

## Verfahren

[Lqr lateral](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Lineare Reifen, kleine Winkel, Vorwärtsfahrt

## Einschränkungen

- Linearisierung, Modell singulär bei v -> 0 (v_min)

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012)

## Expertenmodus: Herleitungen und Hinweise

Für jedes feste $v$ ist der geschlossene diskrete Kreis $A_d-B_dK$ asymptotisch stabil (stabilisierbares Paar, $Q\geq0$ beobachtbar); langsames Gain-Scheduling erhält die Stabilität.
