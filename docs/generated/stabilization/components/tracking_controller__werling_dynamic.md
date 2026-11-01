# Werling: exakte E/A-Linearisierung (Satz 8)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/werling_dynamic` · Version 1.0.0

**Exakt E/A-linearisierender Trackingregler auf dem dynamischen Einspurmodell mit isotropem Pacejka-Reifen für schnelle Fahrt.**

## Zweck

Stabilisiert einen Referenzpunkt lambda vor dem Schwerpunkt invariant auf der Solltrajektorie; die dynamische Sollgrößentransformation beseitigt den Schleppfehler, die geschwindigkeitsabhängige Vorausschau hält die Dämpfung der Nulldynamik konstant (Werling 4.3).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `werling_dynamic` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.werling_dynamic.WerlingDynamic`](../../../../vdsim/stabilization/werling_dynamic.py#L249) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | Fahrzeugzustand (Schwerpunkt) | – |
| `trajectory` | `PlannedTrajectory` | – | Solltrajektorie des Schwerpunkts | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `zeta` | Dämpfungsgrad der Nulldynamik zeta (4.70) | - | 1 | 0.3 | 3 |
| `lam_fixed` | festes lambda (< -50: geschwindigkeitsabhängig nach (4.70)) | m | -100 | – | – |
| `lam_min` | minimales lambda | m | 0 | -1.5 | 30 |
| `lam_max` | maximales lambda | m | 20 | 0 | 50 |
| `lam_rate` | max. Änderungsrate von lambda | m/s | 4 | 0 | – |
| `pole_n1` | Pol 1 Querfehler | 1/s | -1.18 | – | 0 |
| `pole_n2` | Pol 2 Querfehler | 1/s | -3.82 | – | 0 |
| `pole_t1` | Pol 1 Längsfehler | 1/s | -0.29 | – | 0 |
| `pole_t2` | Pol 2 Längsfehler | 1/s | -1.71 | – | 0 |
| `k_delta` | Lenkwinkel-Rückführung k_delta (4.75) | 1/s | 10 | 0 | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `saturation_exponent` | Exponent n der Sättigungsmodifikation | - | 16 | 2 | 60 |
| `reference_transform` | Sollgrößentransformation: dynamic / static / none | – | dynamic | – | – |
| `v_floor` | Mindestgeschwindigkeit der Nulldynamik-Simulation | m/s | 1 | 0.1 | – |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Theorie

Ausgang (4.46), invariante Fehler (4.48), relativer Grad [2,2], linearisierende Rückführung als Lösung von (4.60) (2D-Newton), lineare Stabilisierung (4.68)/(4.69), Nulldynamik (4.67), lambda(zeta, v_d) (4.70), Online-Simulation der Nulldynamik (4.71)-(4.74), Lenkratenregelung (4.75).

## Verfahren

[Dynamic reference transform](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Exakte E/A-Linearisierung für schnelle Fahrt](../theory.md#exact_io_linearization), [Dynamisches Einspurmodell mit isotropem Reifen](../theory.md#isotropic_tire), [Zero dynamics desm](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Ebene Fahrbahn, keine dynamischen Radlasten (Einspurmodell)
- Reifenparameter A, B, C je Achse bekannt (Certainty Equivalence)
- Antriebs-/Bremskräfte schnell eingeregelt, Kräfteverhältnis gamma bekannt
- v > 0 (Vorwärtsfahrt, singulär bei v = 0)

## Einschränkungen

- Nur lokal (Reifensättigung, Bedingung (4.49))
- Stellgrößenbeschränkungen nicht im Regelgesetz
- Nulldynamik nur für Geradeausfahrt linear analysiert (Satz 9)

## Validierung

- tests/stabilization/test_stabilization_dynamic.py

## Umgesetzte Gleichungen

- `werling2011:(4.39)-(4.45)`
- `werling2011:(4.46)`
- `werling2011:(4.48)`
- `werling2011:(4.50)-(4.60)`
- `werling2011:(4.67)-(4.75)`

## Quellen

[Isidori (1995)](../../references.md#isidori1995), [Khalil (2002)](../../references.md#khalil2002), [Pacejka (2012)](../../references.md#pacejka2012), [Werling (2011)](../../references.md#werling2011)

## Designentscheidungen

- (4.60) über die äquivalente Bedingung der Referenzpunktbeschleunigung in Fahrzeugkoordinaten gelöst
- Sättigungsmodifikation nur an der Vorderachse (Eingang delta), Hinterachse mit Kammschem Kreis
- kappa~_d_dot der transformierten Sollgröße numerisch (Rückwärtsdifferenz)

## Expertenmodus: Herleitungen und Hinweise

Nach Linearisierung gilt $\ddot{\tilde e}_t=\tilde w_2$, $\ddot{\tilde e}_n=\tilde w_1$; mit (4.68)/(4.69) und $k>0$ konvergieren die Fehler exponentiell. Die Nulldynamik (4.67) ist für $\lambda>\max(-l_h,-J/[l_vm])$ stabil (Satz 9), ihre Dämpfung $\zeta$ wird über (4.70) konstant gehalten.

## Verwendung

Tests: [tests/stabilization/test_stabilization_dynamic.py](../../../../tests/stabilization/test_stabilization_dynamic.py), [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py)

Konfigurationen: [configs/stabilization/werling_dynamic_highway.json](../../../../configs/stabilization/werling_dynamic_highway.json)
