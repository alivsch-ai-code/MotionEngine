# Trajektorienstabilisierung nach Werling und Fahrzeugebenen – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`LQR.control`](../../../vdsim/stabilization/classic_lateral.py#L300) | Abschn. 3.2 | [Lqr lateral](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Rajamani (2012)](../references.md#rajamani2012) | – | Code (@trace) |
| [`MPC.solve`](../../../vdsim/stabilization/classic_lateral.py#L381) | – | [Mpc lateral](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Borrelli et al. (2017)](../references.md#borrelli2017) | – | Code (@trace) |
| [`PurePursuit.control`](../../../vdsim/stabilization/classic_lateral.py#L180) | Abschn. 2.2 | [Pure Pursuit](../controllers/theory.md#pure_pursuit) | [Snider (2009)](../references.md#snider2009) | – | Code (@trace) |
| [`Stanley.control`](../../../vdsim/stabilization/classic_lateral.py#L217) | – | [Stanley](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Hoffmann et al. (2007)](../references.md#hoffmann2007) | – | Code (@trace) |
| [`lateral_error_model`](../../../vdsim/stabilization/classic_lateral.py#L250) | Abschn. 3.2 | [Lqr lateral](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Rajamani (2012)](../references.md#rajamani2012) | – | Code (@trace) |
| [`ACC.accel`](../../../vdsim/stabilization/classic_longitudinal.py#L181) | Abschn. 5 | [Acc](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Rajamani (2012)](../references.md#rajamani2012) | – | Code (@trace) |
| [`PID.accel`](../../../vdsim/stabilization/classic_longitudinal.py#L73) | – | [Pid](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Åström und Hägglund (2006)](../references.md#astrom2006) | – | Code (@trace) |
| [`VehicleSpeedController.accel`](../../../vdsim/stabilization/classic_longitudinal.py#L213) | – | [Anti windup](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Åström und Hägglund (2006)](../references.md#astrom2006) | – | Code (@trace) |
| [`center_errors`](../../../vdsim/stabilization/errors.py#L67) | Abschn. 4.2.4.2 (4.25) | [Lyapunov-Tracking ohne Orientierungsstabilisierung](theory.md#lyapunov_center) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`flat_reference_transform`](../../../vdsim/stabilization/errors.py#L53) | Abschn. 4.2.4.1 (4.20)-(4.24) | [Flat reference transform](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`frenet_errors`](../../../vdsim/stabilization/errors.py#L78) | Abschn. 4.3.3.1 (4.48), (4.58), (4.59) | [Invariant tracking error](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`rear_axle_error_rates`](../../../vdsim/stabilization/errors.py#L28) | Abschn. 4.2.3.1 (4.10a)-(4.10c) | [Invariant tracking error](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`rear_axle_errors`](../../../vdsim/stabilization/errors.py#L21) | Abschn. 4.2.3.1 (4.9) | [Invariant tracking error](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`taylor_terms`](../../../vdsim/stabilization/errors.py#L35) | Abschn. A.3 (A.10)-(A.13) | [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`elliptic_measure`](../../../vdsim/stabilization/reinit.py#L19) | Abschn. 4.5.1 | [Reinitialisierung und Bewegungsprädiktion](theory.md#reinitialization_trigger) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py) | Code (@trace) |
| [`predict_motion`](../../../vdsim/stabilization/reinit.py#L65) | Abschn. 4.5.2 | [Bewegungsprädiktion für die Reinitialisierung](../planning/theory.md#motion_prediction) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py) | Code (@trace) |
| [`select_controller`](../../../vdsim/stabilization/switching.py#L51) | Abschn. 4.4 | [Stoßfreie Reglerumschaltung](theory.md#controller_switching) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py) | Code (@trace) |
| [`SplitRangeDynamics.step`](../../../vdsim/stabilization/vehicle_layers.py#L83) | Abschn. 5.1.2.2 | [Split-Range-Längskraftumsetzung](theory.md#split_range) | [Werling (2011)](../references.md#werling2011) | – | Code (@trace) |
| [`ZeroDynamicsReference.derivatives`](../../../vdsim/stabilization/werling_dynamic.py#L183) | Abschn. 4.3.3.4 (4.72), (4.73) | [Dynamic reference transform](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`ZeroDynamicsReference.reference`](../../../vdsim/stabilization/werling_dynamic.py#L210) | Abschn. 4.3.3.4 (4.71), (4.74) | [Dynamic reference transform](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`lookahead_for_damping`](../../../vdsim/stabilization/werling_dynamic.py#L56) | Abschn. 4.3.3.3 (4.70) | [Zero dynamics desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`point_kinematics`](../../../vdsim/stabilization/werling_dynamic.py#L66) | Abschn. 4.3.3.1 (4.50)-(4.57) | [Exakte E/A-Linearisierung für schnelle Fahrt](theory.md#exact_io_linearization) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`solve_linearizing_input`](../../../vdsim/stabilization/werling_dynamic.py#L88) | Abschn. 4.3.3.1 (4.60), (4.43) | [Exakte E/A-Linearisierung für schnelle Fahrt](theory.md#exact_io_linearization) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`zero_dynamics_coefficients`](../../../vdsim/stabilization/werling_dynamic.py#L46) | Abschn. 4.3.3.2 (4.67) | [Zero dynamics desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | Code (@trace) |
| [`center_law`](../../../vdsim/stabilization/werling_kinematic.py#L124) | Abschn. 4.2.4.3 (4.28)-(4.31) | [Lyapunov-Tracking ohne Orientierungsstabilisierung](theory.md#lyapunov_center) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py) | Code (@trace) |
| [`force_from_acceleration`](../../../vdsim/stabilization/werling_kinematic.py#L85) | Abschn. 4.2.2 (4.6), (4.7) | [Erweitertes kinematisches Einspurmodell](theory.md#kesm) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py) | Code (@trace) |
| [`kin_tracking_with_orientation_stab`](../../../vdsim/stabilization/werling_kinematic.py#L41) | Abschn. A.5 (4.7), (4.9)-(4.18), (A.10)-(A.13) | [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py) | Code (@trace) |
| [`orientation_law`](../../../vdsim/stabilization/werling_kinematic.py#L95) | Abschn. 4.2.3.2 (4.11), (4.12), (4.15)-(4.18) | [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py) | Code (@trace) |

## Warum es diese Implementierungen gibt

### `PurePursuit.control`

- **Warum:** Geometrischer Bahnregler: Ein Kreisbogen durch die Hinterachse trifft einen Zielpunkt im Abstand $l_d$ auf der Bahn.
- **Theorie:** [Pure Pursuit](../controllers/theory.md#pure_pursuit)
- **Annahmen:** Kinematisches Fahrzeug, Zielpunkt auf der Bahn bei $s_{proj} + l_d$.
- **Quelle:** [Snider (2009)](../references.md#snider2009)

### `center_errors`

- **Warum:** Direkte Stabilisierung der geometrischen Fahrzeugmitte ($\lambda\approx l/2$ vor der Hinterachse) bei langsamer Vorwärtsfahrt (Satz 6).
- **Theorie:** [Lyapunov-Tracking ohne Orientierungsstabilisierung](theory.md#lyapunov_center)
- **Annahmen:** Vorwärtsfahrt, $|\tilde\beta|<\pi/2$ (durch den Lenkanschlag erfüllt), Planung für den flachen Ausgang $\lambda=0$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `taylor_terms`

- **Warum:** Stabilisierung der Hinterachsmitte samt Orientierung für langsame Vorwärts- und Rückwärtsfahrt (Satz 4).
- **Theorie:** [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation)
- **Annahmen:** KESM gültig, Zustände gemessen, Werling-Vorzeichen: $\psi_d=\theta+\pi$ rückwärts, $v_d=\varsigma v$, $\kappa_d=\varsigma\kappa$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `elliptic_measure`

- **Warum:** High-level-Anteil der Bi-level-Stabilisierung: Impulsstörungen früh erkennen und die Planung vom prädizierten Fahrzustand neu starten lassen.
- **Theorie:** [Reinitialisierung und Bewegungsprädiktion](theory.md#reinitialization_trigger)
- **Annahmen:** Planer beantwortet die Anforderung mit `reinitialized=True`; Krümmung und Beschleunigung setzt er aus der aktuellen Trajektorie fort.
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `predict_motion`

- **Warum:** Den Fahrzustand zum zukünftigen Startzeitpunkt $t_0+t_{comp}$ schätzen.
- **Theorie:** [Bewegungsprädiktion für die Reinitialisierung](../planning/theory.md#motion_prediction)
- **Annahmen:** Bei langsamer Fahrt wird $\dot\theta_0$ aus dem Lenkwinkel abgeleitet: $v\tan\delta/l$ (kinematisches Einspurmodell).
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `select_controller`

- **Warum:** Wechsel zwischen den drei Reglern nach Fahrsituation (Abb.
- **Theorie:** [Stoßfreie Reglerumschaltung](theory.md#controller_switching)
- **Annahmen:** Konsistente Trajektorien beider Referenzpunkte zum Umschaltzeitpunkt.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Abb. 4.13

### `SplitRangeDynamics.step`

- **Warum:** Umsetzung der Solllängskraft in Antriebs- und Bremsmomente mit Kompensation der in den Entwurfsmodellen vernachlässigten Fahrwiderstände.
- **Theorie:** [Split-Range-Längskraftumsetzung](theory.md#split_range)
- **Annahmen:** Momente wirken unverzögert; $a_{exp}$ vom Regler (Werling: $w_2$), gemessen $a=a_x+rv_y$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Abb. 5.3

### `point_kinematics`

- **Warum:** Invariantes Trajektorientracking auf dem DESM mit isotropem Reifen bei schneller Fahrt (Satz 8) ohne Schleppfehler.
- **Theorie:** [Exakte E/A-Linearisierung für schnelle Fahrt](theory.md#exact_io_linearization)
- **Annahmen:** $v>0$, Reifenparameter bekannt, $\gamma$ bekannt (Antrieb nach Layout, Bremsen 0.75), Bedingung (4.49) lokal erfüllt.
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `solve_linearizing_input`

- **Warum:** Invariantes Trajektorientracking auf dem DESM mit isotropem Reifen bei schneller Fahrt (Satz 8) ohne Schleppfehler.
- **Theorie:** [Exakte E/A-Linearisierung für schnelle Fahrt](theory.md#exact_io_linearization)
- **Annahmen:** $v>0$, Reifenparameter bekannt, $\gamma$ bekannt (Antrieb nach Layout, Bremsen 0.75), Bedingung (4.49) lokal erfüllt.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** 2D-Newton; Reifen mit Sättigungsmodifikation (Fußnote 17), Sättigung -> Lenkwinkel zum Querkraftoptimum

### `center_law`

- **Warum:** Direkte Stabilisierung der geometrischen Fahrzeugmitte ($\lambda\approx l/2$ vor der Hinterachse) bei langsamer Vorwärtsfahrt (Satz 6).
- **Theorie:** [Lyapunov-Tracking ohne Orientierungsstabilisierung](theory.md#lyapunov_center)
- **Annahmen:** Vorwärtsfahrt, $|\tilde\beta|<\pi/2$ (durch den Lenkanschlag erfüllt), Planung für den flachen Ausgang $\lambda=0$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Vorzeichen in (4.31) nach dem Lyapunov-Beweis: + e~n sin e~theta

### `force_from_acceleration`

- **Warum:** Entwurfsmodell für langsame Fahrt (vorwärts, rückwärts, Stand), das neben der Lenkwinkelrate die Reifenlängskräfte als Eingang enthält, damit keine unterlagerte Geschwindigkeitsregelung nötig ist.
- **Theorie:** [Erweitertes kinematisches Einspurmodell](theory.md#kesm)
- **Annahmen:** Keine Schräglaufwinkel (geringe Querbeschleunigung), ebene Fahrbahn, schnelle unterlagerte Antriebs-/Bremsregelung.
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `kin_tracking_with_orientation_stab`

- **Warum:** Stabilisierung der Hinterachsmitte samt Orientierung für langsame Vorwärts- und Rückwärtsfahrt (Satz 4).
- **Theorie:** [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation)
- **Annahmen:** KESM gültig, Zustände gemessen, Werling-Vorzeichen: $\psi_d=\theta+\pi$ rückwärts, $v_d=\varsigma v$, $\kappa_d=\varsigma\kappa$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** zeilengleiche Umsetzung des MATLAB-Beispielprogramms

### `orientation_law`

- **Warum:** Stabilisierung der Hinterachsmitte samt Orientierung für langsame Vorwärts- und Rückwärtsfahrt (Satz 4).
- **Theorie:** [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation)
- **Annahmen:** KESM gültig, Zustände gemessen, Werling-Vorzeichen: $\psi_d=\theta+\pi$ rückwärts, $v_d=\varsigma v$, $\kappa_d=\varsigma\kappa$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
