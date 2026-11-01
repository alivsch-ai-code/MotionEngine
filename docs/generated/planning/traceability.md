# Trajektorienplanung nach Werling – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`continuous_solution`](../../../vdsim/planning/analysis.py#L23) | Abschn. 3.4.1 (3.12) | [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py) | Code (@trace) |
| [`estimate_sampling_horizon`](../../../vdsim/planning/analysis.py#L89) | Abschn. 3.4.2 Bemerkung 1, (3.13) | [Abschätzung des Sampling-Horizonts](theory.md#sampling_horizon) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py) | Code (@trace) |
| [`lock_in_distance`](../../../vdsim/planning/analysis.py#L83) | Abschn. 3.4.2 (3.14) | [Einrasten auf der Referenz](theory.md#lock_in) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py) | Code (@trace) |
| [`transversality_residual`](../../../vdsim/planning/analysis.py#L41) | Abschn. 3.4.1 (3.13) | [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py) | Code (@trace) |
| [`CircleCollisionChecker.check`](../../../vdsim/planning/collision.py#L144) | Abschn. III | [Kollisionsprüfung mit Kreisen](theory.md#collision_circles) | [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py) | Code (@trace) |
| [`CircleCollisionChecker.geometry_info`](../../../vdsim/planning/collision.py#L172) | Abschn. 3.5.4 Abb. 3.10 | [Rampe des Sicherheitsabstands](theory.md#safety_margin_ramp) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py) | Code (@trace) |
| [`CandidateEvaluator.batch`](../../../vdsim/planning/combination.py#L157) | Abschn. 3.5.5 (3.1), (3.2) | [Kombination und Rücktransformation](theory.md#candidate_combination) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`time_to_arc`](../../../vdsim/planning/combination.py#L50) | Abschn. A.1 (A.7), (A.8) | [Frenet-Transformation in geschlossener Form](../geometry/theory.md#frenet_transformation) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`MaxLateralAcceleration.violation`](../../../vdsim/planning/constraints.py#L95) | Abschn. 3.5.4 | [Fahrphysikalische Restriktionen](theory.md#kinematic_constraints) | [Werling (2011)](../references.md#werling2011) | [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`TireForceConstraint.violation`](../../../vdsim/planning/constraints.py#L239) | Abschn. 3.5.4 | [Fahrphysikalische Restriktionen](theory.md#kinematic_constraints) | [Werling (2011)](../references.md#werling2011) | [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`VehicleEnvelope.violation`](../../../vdsim/planning/constraints.py#L260) | Abschn. 5.3 | [Korridor-Restriktion](theory.md#corridor_constraint) | [Werling (2011)](../references.md#werling2011) | [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`CostModel`](../../../vdsim/planning/cost.py#L337) | Abschn. 3.3 (3.2) | [Mehrzielige Kostenfunktion](theory.md#multi_objective_cost) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`TerminalDeviationCost.lateral`](../../../vdsim/planning/cost.py#L141) | Abschn. 3.4.2 Tab. 3.1 | [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`convert_reference`](../../../vdsim/planning/kinematics.py#L62) | Abschn. 3.5.4 | [Referenzpunkt und Geschwindigkeitsregime](theory.md#reference_point) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`taylor_prediction`](../../../vdsim/planning/kinematics.py#L80) | Abschn. 4.5.2 Abb. 4.14 | [Bewegungsprädiktion für die Reinitialisierung](theory.md#motion_prediction) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`build_lateral_set`](../../../vdsim/planning/lateral.py#L63) | Abschn. 3.5.1 Tab. 3.1 | [Querkandidaten d(t) und d(s)](theory.md#lateral_sampling) | [Werling (2011)](../references.md#werling2011) | [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`FollowingTarget.state`](../../../vdsim/planning/longitudinal.py#L98) | Abschn. 3.5.2 s_ref = s_v - [k0 + kv s_dot_v] | [Folgemodus](theory.md#following_mode) | [Werling (2011)](../references.md#werling2011) | [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`MergingTarget.state`](../../../vdsim/planning/longitudinal.py#L116) | Abschn. 3.5.2 (3.15) | [Einfädeln](theory.md#merging_mode) | [Werling (2011)](../references.md#werling2011) | [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`ObjectMotion.state`](../../../vdsim/planning/longitudinal.py#L53) | Abschn. 3.5.2 | [Folgemodus](theory.md#following_mode) | [Werling (2011)](../references.md#werling2011) | [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`build_longitudinal_set`](../../../vdsim/planning/longitudinal.py#L196) | Abschn. 3.5.2 Tab. 3.1 | [Längskandidaten](theory.md#longitudinal_sampling) | [Werling (2011)](../references.md#werling2011) | [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`WerlingPlanner._compose_output`](../../../vdsim/planning/planner.py#L419) | Abschn. 3.5.5 Schritt 1 | [Zeitliche Konsistenz (Bellman-Prinzip)](theory.md#bellman_principle) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`WerlingPlanner._start_state`](../../../vdsim/planning/planner.py#L313) | Abschn. 4.5.2 | [Bi-level-Stabilisierung (Planerseite)](theory.md#bilevel_stabilization) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Code (@trace) |
| [`jerk_integral`](../../../vdsim/planning/polynomials.py#L65) | Abschn. 3.5.5 (3.4) | [Ruckintegral in geschlossener Form](theory.md#jerk_integral) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`quartic_coefficients`](../../../vdsim/planning/polynomials.py#L44) | Abschn. 3.4 (3.8) | [Quartische Optimalpolynome](theory.md#quartic_polynomial) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`quintic_coefficients`](../../../vdsim/planning/polynomials.py#L27) | Abschn. 3.4 (3.6)-(3.8) | [Quintische Optimalpolynome](theory.md#quintic_polynomial) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`end_grid`](../../../vdsim/planning/sampling.py#L35) | Abschn. 3.4.2 Satz 3 | [Absolutes Endzeitraster](theory.md#absolute_time_grid) | [Werling (2011)](../references.md#werling2011) | [test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Code (@trace) |
| [`fallback_candidate`](../../../vdsim/planning/selection.py#L152) | Abschn. 5.3 | [Rückfallebene](theory.md#fallback) | [Werling (2011)](../references.md#werling2011) | – | Code (@trace) |
| [`initial_jerk`](../../../vdsim/planning/selection.py#L175) | Abschn. 3.5.5 Schritt 6 | [Ablösestrategie](theory.md#replacement_strategy) | [Werling (2011)](../references.md#werling2011) | – | Code (@trace) |
| [`select_mode`](../../../vdsim/planning/selection.py#L71) | Abschn. 3.5.5 Schritt 4-5 | [Lazy-Auswahl](theory.md#lazy_selection) | [Werling (2011)](../references.md#werling2011) | – | Code (@trace) |

## Warum es diese Implementierungen gibt

### `continuous_solution`

- **Warum:** Endzeit und Endposition so wählen, dass das Fahrzeug zügig, aber komfortabel auf eine Referenzbewegung $\xi_{ref}(t)$ einschwenkt.
- **Theorie:** [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold)
- **Annahmen:** $k_\tau, k_{\xi_1} > 0$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** c345 = M3(tau)^-1 [xi_ref(tau) - M1(tau) c012], M3 = M2 + 120/k_xi in der c5-Spalte der ersten Zeile

### `estimate_sampling_horizon`

- **Warum:** Bemerkung 1: Prüfen, ob $\tau_{max}$ lang genug ist, damit Satz 3 gilt.
- **Theorie:** [Abschätzung des Sampling-Horizonts](theory.md#sampling_horizon)
- **Annahmen:** Ruhe-zu-Ruhe-Manöver als Worst Case.
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `lock_in_distance`

- **Warum:** Bemerkung 2: Vermeiden, dass das Fahrzeug dauerhaft parallel zur Referenz fährt.
- **Theorie:** [Einrasten auf der Referenz](theory.md#lock_in)
- **Annahmen:** Stillstand auf der Mannigfaltigkeit.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Bemerkung 2: Endabstand d0 / (1 + k_xi tau^5 / 720)

### `transversality_residual`

- **Warum:** Endzeit und Endposition so wählen, dass das Fahrzeug zügig, aber komfortabel auf eine Referenzbewegung $\xi_{ref}(t)$ einschwenkt.
- **Theorie:** [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold)
- **Annahmen:** $k_\tau, k_{\xi_1} > 0$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** -1/2 psi3^2 - psi1 xi_ref_dot - psi2 xi_ref_ddot + k_tau = 0

### `CircleCollisionChecker.check`

- **Warum:** Schnelle statische und dynamische Kollisionsprüfung.
- **Theorie:** [Kollisionsprüfung mit Kreisen](theory.md#collision_circles)
- **Annahmen:** Schwimmwinkel am Referenzpunkt = 0.
- **Quelle:** [Ziegler und Stiller (2010)](../references.md#ziegler2010iv)
- **Hinweis:** Kreisüberdeckung, Überlappung |c_i - c_j| < r_i + r_j + Sicherheitsabstand(t)

### `CircleCollisionChecker.geometry_info`

- **Warum:** Robustheit gegen Messrauschen bei harten Kollisionsrestriktionen.
- **Theorie:** [Rampe des Sicherheitsabstands](theory.md#safety_margin_ramp)
- **Annahmen:** Der Abstand hängt vom Objekttyp ab (Pkw, Lkw, Fußgänger, Radfahrer, statisch, unbekannt).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Sicherheitsabstand linear über Δt aufgebaut

### `CandidateEvaluator.batch`

- **Warum:** Jede Längs- mit jeder Quertrajektorie kombinieren und in Weltkoordinaten bewerten.
- **Theorie:** [Kombination und Rücktransformation](theory.md#candidate_combination)
- **Annahmen:** Die Kosten sind separierbar.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** x(s(t), d(t)) = r(s(t)) + d(t) n_r(s(t)), lazy und vektorisiert in Batches

### `time_to_arc`

- **Warum:** Umrechnung des Bewegungszustands eines Punktes zwischen Weltkoordinaten $[x, y, \theta, \kappa, v, a]$ und Bahnkoordinaten $[s, \dot s, \ddot s, d, d', d'']$ ohne numerisches Differenzieren.
- **Theorie:** [Frenet-Transformation in geschlossener Form](../geometry/theory.md#frenet_transformation)
- **Annahmen:** - Referenzkurve zweimal stetig differenzierbar mit stetigem $\kappa_r'$ (sonst springt $d''$).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** d' = d_dot/s_dot, d'' = (d_ddot - s_ddot d')/s_dot^2 mit Schutz bei s_dot -> 0

### `MaxLateralAcceleration.violation`

- **Warum:** Kandidaten verwerfen, die das Fahrzeug nicht fahren kann.
- **Theorie:** [Fahrphysikalische Restriktionen](theory.md#kinematic_constraints)
- **Annahmen:** Grenzwerte $\leq 0$ werden automatisch aus der VehicleConfig übernommen ($\kappa_{max}$, $\delta_{max}$, $\mu$).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** |v^2 kappa| <= a_y,max

### `TireForceConstraint.violation`

- **Warum:** Kandidaten verwerfen, die das Fahrzeug nicht fahren kann.
- **Theorie:** [Fahrphysikalische Restriktionen](theory.md#kinematic_constraints)
- **Annahmen:** Grenzwerte $\leq 0$ werden automatisch aus der VehicleConfig übernommen ($\kappa_{max}$, $\delta_{max}$, $\mu$).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** sqrt(a^2 + (v^2 kappa)^2) <= eta mu g

### `VehicleEnvelope.violation`

- **Warum:** Der Fahrzeugumriss bleibt im befahrbaren Korridor $[d_{min},d_{max}]$.
- **Theorie:** [Korridor-Restriktion](theory.md#corridor_constraint)
- **Annahmen:** $\Delta\psi = \psi-\theta_r$ mit $\psi = \theta$ (bzw.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Fußnote 8: Box-Restriktion für d(t)

### `CostModel`

- **Warum:** Werling-Kosten um weitere Ziele erweitern (Komfort, Fahrzeit, Energie, Sicherheitsabstand, Kollisionsrisiko …).
- **Theorie:** [Mehrzielige Kostenfunktion](theory.md#multi_objective_cost)
- **Annahmen:** Alle Gewichte stehen in Parametern, nie im Code.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** J = k_lat J_d + k_lon J_s + nicht separierbare Zusatzterme (Re-Ranking)

### `TerminalDeviationCost.lateral`

- **Warum:** Endzeit und Endposition so wählen, dass das Fahrzeug zügig, aber komfortabel auf eine Referenzbewegung $\xi_{ref}(t)$ einschwenkt.
- **Theorie:** [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold)
- **Annahmen:** $k_\tau, k_{\xi_1} > 0$.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** k_tau tau_j + 1/2 k_delta delta_i^2 usw.

### `convert_reference`

- **Warum:** Wahl von Referenzpunkt und Quermodus passend zum Trackingregler.
- **Theorie:** [Referenzpunkt und Geschwindigkeitsregime](theory.md#reference_point)
- **Annahmen:** Beim Regimewechsel wird die Position um $l_h$ entlang der Fahrzeugachse verschoben; $\theta,\kappa,v,a$ werden übernommen.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Schwerpunkt bei schneller Fahrt, Hinterachsmitte bei langsamer Fahrt; kinematische Umrechnung

### `taylor_prediction`

- **Warum:** Den Fahrzustand zum zukünftigen Startzeitpunkt $t_0+t_{comp}$ schätzen.
- **Theorie:** [Bewegungsprädiktion für die Reinitialisierung](theory.md#motion_prediction)
- **Annahmen:** Bei langsamer Fahrt wird $\dot\theta_0$ aus dem Lenkwinkel abgeleitet: $v\tan\delta/l$ (kinematisches Einspurmodell).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Taylor-Reihen der Bewegung mit konstanter Beschleunigung und Kurswinkelrate, singularitätsfrei

### `build_lateral_set`

- **Warum:** Fächer der Querbewegungen zur Referenzkurve, z.
- **Theorie:** [Querkandidaten d(t) und d(s)](theory.md#lateral_sampling)
- **Annahmen:** Spurwechsel: Die Referenzkurve liegt auf der Mitte der Zielspur, der Versatz $d_{ref}$ kommt aus `BehaviorCommand`.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** d(t): delta_i x tau_j, q345(d_ref + delta_i, 0, 0, tau_j); d(s): Strichgrößen, k_s [s(tau)-s(0)]

### `FollowingTarget.state`

- **Warum:** Geschwindigkeitsabhängigen Abstand zum Vorderfahrzeug halten.
- **Theorie:** [Folgemodus](theory.md#following_mode)
- **Annahmen:** $s_v$ stammt aus der Projektion der Prädiktion auf die Referenzkurve oder aus `PredictedObject.s` bei passender `lane_id`.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** geschwindigkeitsabhängiger Sollabstand; s_dot_ref = s_dot_v - kv s_ddot_v, s_ddot_ref = s_ddot_v

### `MergingTarget.state`

- **Warum:** Positionierung in der Mitte einer Lücke auf der Zielspur.
- **Theorie:** [Einfädeln](theory.md#merging_mode)
- **Annahmen:** Beide Fahrzeuge bewegen sich mit konstanter Beschleunigung.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** s_ref = 1/2 [s_a + s_b] (Lückenmitte, Stoßstangen); Ego-Mitte auf der Lückenmitte

### `ObjectMotion.state`

- **Warum:** Geschwindigkeitsabhängigen Abstand zum Vorderfahrzeug halten.
- **Theorie:** [Folgemodus](theory.md#following_mode)
- **Annahmen:** $s_v$ stammt aus der Projektion der Prädiktion auf die Referenzkurve oder aus `PredictedObject.s` bei passender `lane_id`.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** s_v(t) = s_v(0) + s_dot_v(0) t + 1/2 s_ddot_v(0) t^2, nach Stillstand geklemmt

### `build_longitudinal_set`

- **Warum:** Längsbewegungen für die Modi Geschwindigkeithalten, Folgen, Einfädeln und Anhalten.
- **Theorie:** [Längskandidaten](theory.md#longitudinal_sampling)
- **Annahmen:** Nach $\tau$ folgt die Lösung exakt der Referenz $s_{ref}(t)+\sigma$ (bzw.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** s(t): sigma_i x tau_j, q345(s_ref(tau_j)+sigma_i, s_dot_ref(tau_j), s_ddot_ref(tau_j)); s_dot(t): q34

### `WerlingPlanner._compose_output`

- **Warum:** Bei zyklischer Neuplanung soll sich die verbleibende Trajektorie nur verkürzen, nicht verändern.
- **Theorie:** [Zeitliche Konsistenz (Bellman-Prinzip)](theory.md#bellman_principle)
- **Annahmen:** Die Restriktionen sind inaktiv, und nur konsistente Kostenterme sind aktiv.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Ausgabe = alte Trajektorie auf [t, t0 + t_comp], danach die neue

### `WerlingPlanner._start_state`

- **Warum:** Low-level-Stabilisierung gegen dauerhafte Störungen mit High-level-Reaktion auf Impulsstörungen kombinieren.
- **Theorie:** [Bi-level-Stabilisierung (Planerseite)](theory.md#bilevel_stabilization)
- **Annahmen:** Die Schwellwertüberwachung liegt im Regler (`ControllerStatus`).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Reinitialisierung: Position, Richtung, Geschwindigkeit prädiziert; Krümmung, Beschleunigung von der aktuellen Solltrajektorie (stoßfrei)

### `jerk_integral`

- **Warum:** Kosten (3.4) ohne numerische Integration (Algorithmus-Schritt 3).
- **Theorie:** [Ruckintegral in geschlossener Form](theory.md#jerk_integral)
- **Annahmen:** Polynomdarstellung bis höchstens fünften Grades.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Ruckintegral int_0^tau (6c3 + 24c4 t + 60c5 t^2)^2 dt in geschlossener Form

### `quartic_coefficients`

- **Warum:** Optimale Geschwindigkeitswechsel ohne vorgegebene Endposition (Geschwindigkeithalten).
- **Theorie:** [Quartische Optimalpolynome](theory.md#quartic_polynomial)
- **Annahmen:** Die Endkosten sind unabhängig von der Endposition.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Satz 2: c34 = q34(xi2(tau), xi3(tau)) bei freier Endposition, c5 = 0

### `quintic_coefficients`

- **Warum:** Ruckoptimale Bewegung $\xi_1(t)$ (Querablage $d$ oder Längsposition $s$) zwischen festem Anfangs- und Endzustand.
- **Theorie:** [Quintische Optimalpolynome](theory.md#quintic_polynomial)
- **Annahmen:** Der Eingang ist unbeschränkt (freies Problem).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Satz 1: geschlossene Koeffizienten c012 = M1(0)^-1 xi(0), c345 = M2(tau)^-1 [xi(tau) - M1(tau) c012]

### `end_grid`

- **Warum:** Diskretisierung der Zielmannigfaltigkeit, sodass der Rest der alten Optimaltrajektorie im nächsten Zyklus wieder im Satz liegt.
- **Theorie:** [Absolutes Endzeitraster](theory.md#absolute_time_grid)
- **Annahmen:** Der Startzustand liegt exakt auf der alten Trajektorie.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Endzeitpunkte auf absolutem Raster T_k = k*dtau, tau_j = T_k - t0; Rest der alten Optimallösung bleibt verfügbar

### `fallback_candidate`

- **Warum:** Verhalten, wenn keine Trajektorie alle Restriktionen erfüllt.
- **Theorie:** [Rückfallebene](theory.md#fallback)
- **Annahmen:** Es wurden genügend Bremskandidaten geprüft; ist das Budget erschöpft, werden die stärksten Bremskandidaten zusätzlich geprüft.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Fußnote 10: längste kollisionsfreie Trajektorie

### `initial_jerk`

- **Warum:** Auswahl zwischen den aktiven Längsmodi.
- **Theorie:** [Ablösestrategie](theory.md#replacement_strategy)
- **Annahmen:** $\dot a(0)$ wird als Weltgröße aus den exakten Polynomen per zentraler Differenz ($h$ = 1 ms) bestimmt.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Ablösestrategie: kleinster vorzeichenbehafteter Anfangsruck a_dot(0) setzt sich durch

### `select_mode`

- **Warum:** Die beste zulässige Trajektorie finden, ohne alle Kandidaten zu prüfen.
- **Theorie:** [Lazy-Auswahl](theory.md#lazy_selection)
- **Annahmen:** Die Kosten sind vor der Prüfung bekannt (separierbar).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Prüfung in aufsteigender Kostenreihenfolge, erste gültige Trajektorie ist die beste
