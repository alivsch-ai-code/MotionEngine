# Werling: Lyapunov ohne Orientierungsstabilisierung (Satz 6)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/werling_kinematic_center` · Version 1.0.0

**Lyapunov-basierter Trackingregler der geometrischen Fahrzeugmitte ohne Orientierungsstabilisierung für langsame Vorwärtsfahrt.**

## Zweck

Stabilisiert den Punkt lambda ~ l/2 vor der Hinterachse direkt, damit das Fahrzeug ruhiger lenkt und mit kleineren Korrekturamplituden der kollisionsfrei geplanten Konfiguration folgt (Werling 4.2.4).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `werling_kinematic_center` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.werling_kinematic.WerlingKinematicCenter`](../../../../vdsim/stabilization/werling_kinematic.py#L258) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | Fahrzeugzustand (Schwerpunkt) | – |
| `trajectory` | `PlannedTrajectory` | – | Solltrajektorie der Hinterachsmitte | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k1` | k~1 (Positionsfehler) | 1/m² | 0.5 | 0 | – |
| `k3` | k~3 (Geschwindigkeitsfehler) | 1/s | 2 | 0 | – |
| `k4` | k~4 (Kurswinkelfehler) | 1/s | 5 | 0 | – |
| `lam` | Abstand lambda von der Hinterachse (<0: l/2) | m | -1 | – | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `taylor_switch` | Grenze Taylor-Näherung | rad | 0.5 | 0 | 1.5 |
| `sign_variant` | Vorzeichen in (4.31): proof / printed | – | proof | – | – |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Theorie

Flachheitsbasierte Sollgrößentransformation (4.20)-(4.24), invariante Fehler der Fahrzeugmitte (4.25), Fehlerdynamik Modell 3 (4.26)/(4.27), Regelgesetz (4.30)/(4.31) mit Inversen (4.28)/(4.29) und Rücksubstitution (4.7).

## Verfahren

[Flat reference transform](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Lyapunov-Tracking ohne Orientierungsstabilisierung](../theory.md#lyapunov_center), [Zero dynamics kesm](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Kinematisches Einspurmodell, |beta~| < pi/2 (durch die Lenkwinkelgrenze erfüllt)
- Nur Vorwärtsfahrt, |kappa_d| < 1/lambda (Satz 7)

## Einschränkungen

- Rückwärts instabile Nulldynamik (Taschenmessereffekt)
- Orientierung nur über die Nulldynamik stabil (|psi - psi_d| <= pi/2 zu Beginn)

## Validierung

- tests/stabilization/test_stabilization_kinematic.py

## Umgesetzte Gleichungen

- `werling2011:(4.20)-(4.24)`
- `werling2011:(4.25)`
- `werling2011:(4.26)`
- `werling2011:(4.27)`
- `werling2011:(4.28)`
- `werling2011:(4.29)`
- `werling2011:(4.30)`
- `werling2011:(4.31)`
- `werling2011:(4.36)`

## Quellen

[Isidori (1995)](../../references.md#isidori1995), [Khalil (2002)](../../references.md#khalil2002), [Werling (2011)](../../references.md#werling2011)

## Designentscheidungen

- Vorzeichen in (4.31) nach dem Lyapunov-Beweis (+ e~n sin e~theta), der gedruckte Ausdruck (-) verletzt V_dot <= 0

## Expertenmodus: Herleitungen und Hinweise

Mit $\tilde V=\frac{1}{2}[\tilde k_1\tilde e_t^2+\tilde k_1\tilde e_n^2+\tilde e_\theta^2+\tilde e_v^2]$ und $\tilde w_2=\dot{\tilde v}_d-\tilde k_3\tilde e_v-\tilde k_1[\tilde e_t\cos\tilde e_\theta+\tilde e_n\sin\tilde e_\theta]$ folgt $\dot{\tilde V}=-\tilde k_4\tilde e_\theta^2-\tilde k_3\tilde e_v^2\leq0$ (Satz 6). Nulldynamik (4.36) stabil für $v_d>0$, $|\kappa_d|<1/\lambda$ (Satz 7).

## Verwendung

Tests: [tests/stabilization/test_stabilization_kinematic.py](../../../../tests/stabilization/test_stabilization_kinematic.py), [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py)
