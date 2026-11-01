# Trajektorienplanung nach Werling

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.planning` · Quellcode: [vdsim/planning/](../../../vdsim/planning) · Paketdoku: [vdsim/planning/docs/](../../../vdsim/planning/docs)

## Übersicht

**Zeitlich konsistente, sampling-basierte Trajektorienplanung in Frenet-Koordinaten mit kombinierter Quer- und Längsoptimierung, Kollisionsprüfung und Bi-level-Stabilisierung (Werling 2011, Kap. 2–3, Anh. A).**

Das Paket erzeugt im 10-Hz-Takt Solltrajektorien für die Trajektorienregelung. Es setzt die
Optimierungsheuristik von Werling um: Gewählt wird die beste Lösung aus der Funktionenklasse der
unrestringierten Optimallösung (quintische bzw. quartische Polynome), die alle Restriktionen einhält.
Dank absolutem Endzeitraster und exakter Fortsetzung der alten Trajektorie ist die Planung bei
inaktiven Restriktionen zeitlich konsistent (Bellman-Prinzip, Satz 3). Das macht sie unabhängig von
der Planungsfrequenz, und eine Low-level-Stabilisierung kann darauf aufsetzen.

Paket-Docstring:

```text
Trajectory planning after Werling (2011), chapters 2-3 and appendix A.

    polynomials   optimal quintic/quartic polynomials (3.3)-(3.8), closed-form jerk integral
    sampling      discretized target manifolds on an absolute time / arc-length grid (Satz 3)
    lateral       d(t) and d(s) candidate sets (3.5.1)
    longitudinal  velocity / following / merging / stopping modes (3.5.2, Tab. 3.1)
    combination   combination (3.2) and lazy world transformation (3.1, A.1)
    cost          multi-objective cost terms (kind="cost_term"), consistent Werling terms
    constraints   restrictions (kind="constraint")
    collision     circle based collision checking (kind="collision_checker", 3.5.4)
    selection     lazy selection, replacement strategy, fallback (3.5.5)
    plan          exact polynomial representation of the selected trajectory
    kinematics    ego geometry, reference points, motion prediction (4.5.2)
    analysis      continuous solution (3.12), (3.13), lock-in (3.14), sampling horizon
    planner       trajectory_planner/werling
    baselines     trajectory_planner/frenet_naive, trajectory_planner/sequential
    config        configs/planning/*.json

Importing the package registers all components.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 17 |
| Komponenten | 26 |
| Verfahren/Konzepte | 25 |
| @trace-Einträge | 29 |
| Tests | 7 |
| Beispiele | 8 |

## Architektur

`WerlingPlanner.plan_cycle()` folgt Abschn. 3.5.5:
1. **Startzustand** (`planner._start_state`): exakte Auswertung des alten `TrajectoryPlan` zu t0 + t_comp
   oder Reinitialisierung aus der Prädiktion (`kinematics.taylor_prediction`, 4.5.2).
2. **Regime/Quermodus**: d(t) mit Schwerpunkt oder d(s) mit Hinterachse (Hysterese um v_s), Projektion (A.2).
3. **Kandidatensätze**: `lateral.build_lateral_set`, `longitudinal.build_longitudinal_set` mit
   `polynomials` (3.8) und geschlossenem Ruckintegral, Kosten über `cost.CostModel`, Frenet-Vorfilter.
4. **Kombination** (`combination.CandidateEvaluator`): (3.2), Rücktransformation A.1 lazy in Batches.
5. **Prüfung** (`selection.select_mode`): Restriktions-Plugins (`constraints`) und Kollisionsprüfer
   (`collision`), erste gültige = beste; Re-Ranking nicht separierbarer Kostenterme.
6. **Ablösestrategie/Fallback** (`selection.choose_mode`, `choose_fallback`).
Ausgabe: `PlannedTrajectory` (alte Trajektorie bis t0 + t_comp, dann neue; `plan` = exakte Polynome)
und `PlannerDebug`. Analysen (3.12)–(3.14) in `analysis`; Vergleichsplaner in `baselines`.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.planning`](../../../vdsim/planning/__init__.py) | 43 | – | Trajectory planning after Werling (2011), chapters 2-3 and appendix A. |
| [`vdsim.planning.analysis`](../../../vdsim/planning/analysis.py) | 170 | – | Analysis of the optimal control problem (Werling 2011, 3.4.1, remarks 1 and 2). |
| [`vdsim.planning.baselines`](../../../vdsim/planning/baselines.py) | 93 | FrenetNaiveParams, FrenetNaivePlanner, SequentialPlanner | Comparison planners for planner benchmarks (Werling 2011, 3.1, 3.2, Abb. |
| [`vdsim.planning.collision`](../../../vdsim/planning/collision.py) | 179 | CollisionSettings, CollisionResult, CollisionChecker, CircleCheckerParams, CircleCollisionChecker | Static and dynamic collision checking (Werling 2011, 3.5.4; Ziegler/Stiller 2010). |
| [`vdsim.planning.combination`](../../../vdsim/planning/combination.py) | 173 | PlanningContext, TrajectoryBatch, CandidateEvaluator | Combination of lateral and longitudinal candidates and the transformation into world coordinates. |
| [`vdsim.planning.config`](../../../vdsim/planning/config.py) | 41 | – | Planner configurations (configs/planning/*.json). |
| [`vdsim.planning.constraints`](../../../vdsim/planning/constraints.py) | 404 | ConstraintResult, Constraint, LateralAccelerationParams, MaxLateralAcceleration, LongitudinalAccelerationParams, MaxLongitudinalAcceleration | Restrictions of the trajectory planner as plugins (kind="constraint", Werling 2011, 3.5.4). |
| [`vdsim.planning.cost`](../../../vdsim/planning/cost.py) | 408 | CostTerm, JerkCostParams, JerkCost, TerminalTimeParams, TerminalTimeCost, TerminalDeviationParams | Configurable multi-objective cost of the trajectory planner (kind="cost_term"). |
| [`vdsim.planning.kinematics`](../../../vdsim/planning/kinematics.py) | 119 | EgoGeometry | Ego geometry, reference points and the motion prediction of the high-level stabilization. |
| [`vdsim.planning.lateral`](../../../vdsim/planning/lateral.py) | 88 | LateralSet | Lateral candidate sets (Werling 2011, 3.5.1, Tab. |
| [`vdsim.planning.longitudinal`](../../../vdsim/planning/longitudinal.py) | 264 | LongitudinalParams, ObjectMotion, VelocityTarget, StoppingTarget, FollowingTarget, MergingTarget | Longitudinal operating modes and candidate sets (Werling 2011, 3.5.2, Tab. |
| [`vdsim.planning.plan`](../../../vdsim/planning/plan.py) | 105 | TrajectoryPlan | Exact representation of a planned trajectory (PlannedTrajectory.plan). |
| [`vdsim.planning.planner`](../../../vdsim/planning/planner.py) | 521 | TimingParams, StabilizationParams, SearchParams, WerlingPlannerParams, StartState, WerlingPlanner | Werling trajectory planner (Werling 2011, chapters 2-3, appendix A). |
| [`vdsim.planning.polynomials`](../../../vdsim/planning/polynomials.py) | 165 | ConstantReference, PolynomialSet | Optimal polynomials of the integrator chain (Werling 2011, section 3.4). |
| [`vdsim.planning.sampling`](../../../vdsim/planning/sampling.py) | 101 | EndGrid, SamplingParams | Discretization of the target manifolds (Werling 2011, 3.4.2, Satz 3, Tab. |
| [`vdsim.planning.selection`](../../../vdsim/planning/selection.py) | 207 | SelectionSettings, ModeResult | Lazy selection of the best admissible trajectory per longitudinal mode (Werling 2011, 3.5.5). |
| [`vdsim.planning.simulation`](../../../vdsim/planning/simulation.py) | 77 | ClosedLoopLog | Minimal closed loop for planner tests and examples (ideal trajectory tracking). |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [geometry](../geometry/index.md)
- genutzt von: –
- externe Bibliotheken: `__future__`, `dataclasses`, `json`, `numpy`, `pathlib`, `time`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Absolutes Endzeitraster T_k = k·Δτ (bzw. Endpositionsraster S_k = k·Δs im d(s)-Modus) | Der Rest der alten Optimaltrajektorie ist im neuen Satz enthalten (Satz 3) | relatives Raster (trajectory_planner/frenet_naive, nicht konsistent) |
| Schutz des alten Endzeitpunkts unterhalb von τ_min | Beim Absinken des kleinsten τ bliebe die alte Lösung sonst kurz vor Erreichen der Mannigfaltigkeit nicht verfügbar | sehr kleines τ_min allein (numerisch extreme Polynome) |
| Plan als Polynomkoeffizienten statt Abtastwerte | exakte Startzustände, Konsistenzfehler im Bereich der Maschinengenauigkeit | Interpolation der Ausgabe (Konsistenzfehler ~ Interpolationsfehler) |
| Kollisionsprüfung nur für restriktionskonforme Kandidaten, Referenzkurve je Längssatz einmal ausgewertet | Rechenzeit; der Fallback nutzt bei Restriktionsverletzung den Verletzungszeitpunkt | vollständige Prüfung aller Kandidaten |
| Fallback mit Gleichstandsauflösung über die Geschwindigkeit im Kollisionszeitpunkt | Kollisionszeiten sind auf das Prüfraster quantisiert; Werling folgt der Trajektorie mit maximal zulässiger Verzögerung | billigste unter den längsten (bremst nicht) |
| Grobes Endgeschwindigkeitsraster bis zum Stillstand im Geschwindigkeitsmodus | Ohne langsamere Endgeschwindigkeiten bleiben hinter langsamerem Verkehr nur Anhaltekandidaten gültig; die Ablösestrategie würde dann anhalten | nur ν ∈ [−ν_max, ν_max] und Anhaltekandidaten |

## Implementierung

- Koeffizienten (3.8) in geschlossener Form, vektorisiert für alle (δ_i, τ_j); Ruckintegral analytisch
- Lazy-Auswertung mit wachsenden Batches (32 … 1024) in aufsteigender Kostenreihenfolge, Budget max_checks
- Weltkoordinaten ausschließlich über ReferenceLine.to_cartesian (A.1); d(t) über (A.7), (A.8) mit Schutz bei ṡ → 0
- dκ/dℓ aus exakter Zeitableitung von κ bzw. im d(s)-Modus geometrisch (robust bei v ≈ 0)
- Plugins über @component (kind constraint, cost_term, collision_checker), Gewichte nur in Parametern
- **Konfigurationsprüfung beim reset():** Einrast-Analyse (Bemerkung 2) und Samplinghorizont (Bemerkung 1)

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`collision_checker/circles`](components/collision_checker__circles.md) | Kreisapproximation (Ziegler/Stiller) | 1.0.0 | Kollisionsprüfung mit Kreisüberdeckung der Fahrzeugumrisse, statisch und dynamisch über die Prädiktion. |
| [`constraint/max_curvature`](components/constraint__max_curvature.md) | Max. Krümmung | 1.0.0 | Minimaler Kurvenradius (kinematische Restriktion). |
| [`constraint/max_jerk`](components/constraint__max_jerk.md) | Max. Ruck | 1.0.0 | Begrenzt den Bahnruck ȧ (Differenzenquotient auf dem Prüfraster). |
| [`constraint/max_lateral_acceleration`](components/constraint__max_lateral_acceleration.md) | Max. Querbeschleunigung | 1.0.0 | Begrenzt die Querbeschleunigung v²κ entlang der Trajektorie. |
| [`constraint/max_longitudinal_acceleration`](components/constraint__max_longitudinal_acceleration.md) | Max. Längsbeschleunigung | 1.0.0 | Getrennte Grenzen für Beschleunigen und Verzögern. |
| [`constraint/max_steering_angle`](components/constraint__max_steering_angle.md) | Max. Lenkwinkel | 1.0.0 | Kinematischer Lenkwinkel δ = atan(lκ) innerhalb des Lenkanschlags. |
| [`constraint/max_steering_velocity`](components/constraint__max_steering_velocity.md) | Max. Lenkwinkelgeschwindigkeit | 1.0.0 | δ̇ = l κ̇ / (1 + (lκ)²) begrenzt (Lenkaktor-Dynamik). |
| [`constraint/max_yaw_rate`](components/constraint__max_yaw_rate.md) | Max. Gierrate | 1.0.0 | Gierrate ψ̇ = vκ des Referenzpunkts begrenzt. |
| [`constraint/speed_range`](components/constraint__speed_range.md) | Geschwindigkeitsbereich | 1.0.0 | 0 ≤ v ≤ v_max: keine Richtungsumkehr innerhalb einer Trajektorie. |
| [`constraint/tire_force`](components/constraint__tire_force.md) | Kammscher Kreis | 1.0.0 | Kammscher Kreis √(a² + (v²κ)²) ≤ η μ g. |
| [`constraint/vehicle_envelope`](components/constraint__vehicle_envelope.md) | Fahrzeugumriss im Korridor | 1.0.0 | Alle vier Fahrzeugecken liegen im Korridor d_min ≤ d ≤ d_max. |
| [`constraint/vehicle_stability`](components/constraint__vehicle_stability.md) | Fahrstabilität (lineares ESM) | 1.0.0 | Stationärer Schwimmwinkel und Querbeschleunigung im linearen Bereich des Einspurmodells. |
| [`cost_term/acceleration`](components/cost_term__acceleration.md) | Beschleunigung | 1.0.0 | Quadratintegral der straßenrelativen Beschleunigungen über den Prüfhorizont. |
| [`cost_term/collision_risk`](components/cost_term__collision_risk.md) | Kollisionsrisiko | 1.0.0 | Gaußförmiges Risikomaß über den kleinsten Abstand zu den prädizierten Objekten. |
| [`cost_term/comfort`](components/cost_term__comfort.md) | Komfort | 1.0.0 | Beschleunigungsbelastung der Insassen in Weltkoordinaten (inkl. |
| [`cost_term/curvature`](components/cost_term__curvature.md) | Krümmung | 1.0.0 | Geometrische Krümmungsenergie ∫ κ² dℓ = ∫ κ² v dt. |
| [`cost_term/energy`](components/cost_term__energy.md) | Energieeffizienz | 1.0.0 | Traktionsenergie je Masse ∫ ṡ (s̈ + c_r g + ρ c_w A ṡ²/(2m)) dt mit Rekuperation. |
| [`cost_term/jerk`](components/cost_term__jerk.md) | Ruck (konsistent) | 1.0.0 | Ruckintegral ∫½u² dt des Optimalsteuerproblems (3.4), geschlossen ausgewertet. |
| [`cost_term/lane_deviation`](components/cost_term__lane_deviation.md) | Spurabweichung | 1.0.0 | Integrierte Querabweichung zur Referenz über den Prüfhorizont (bzw. |
| [`cost_term/safety_distance`](components/cost_term__safety_distance.md) | Sicherheitsabstand | 1.0.0 | Weiche Abstandskosten zusätzlich zur harten Kollisionsrestriktion. |
| [`cost_term/terminal_deviation`](components/cost_term__terminal_deviation.md) | Zielerreichung ½kδ² (konsistent) | 1.0.0 | Endabweichung ½kδ δ², ½kσ σ², ½kν ν² von der Referenz (Zielerreichung). |
| [`cost_term/terminal_time`](components/cost_term__terminal_time.md) | Endzeit k_τ τ (konsistent) | 1.0.0 | Endkosten k_τ τ (bzw. |
| [`cost_term/travel_time`](components/cost_term__travel_time.md) | Fahrzeit | 1.0.0 | Zeitverlust max(0, v_soll T − Δs)/v_soll auf dem Prüfhorizont. |
| [`trajectory_planner/frenet_naive`](components/trajectory_planner__frenet_naive.md) | Frenet-Planer (naiv, ohne Konsistenz) | 1.0.0 | Vergleichsplaner: Frenet-Sampling mit relativem Endzeitraster und Neuplanung vom Messzustand. |
| [`trajectory_planner/sequential`](components/trajectory_planner__sequential.md) | Sequentieller Planer (erst längs, dann quer) | 1.0.0 | Vergleichsplaner: Längsbewegung ohne Kenntnis der Querbewegung, danach Querbewegung (Werling 3.1). |
| [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | Trajektorienplaner (Werling) | 1.0.0 | Trajektorienplanung nach Werling: optimale Polynome in Frenet-Koordinaten, diskretisierte Zielmannigfaltigkeiten auf absolutem Zeitraster, zeitliche Konsistenz und Bi-level-Stabilisierung. |

### Verfahren und Konzepte

- [Absolutes Endzeitraster](theory.md#absolute_time_grid)
- [Zeitliche Konsistenz (Bellman-Prinzip)](theory.md#bellman_principle)
- [Bi-level-Stabilisierung (Planerseite)](theory.md#bilevel_stabilization)
- [Kombination und Rücktransformation](theory.md#candidate_combination)
- [Kollisionsprüfung mit Kreisen](theory.md#collision_circles)
- [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold)
- [Korridor-Restriktion](theory.md#corridor_constraint)
- [Rückfallebene](theory.md#fallback)
- [Folgemodus](theory.md#following_mode)
- [Frenet-Transformation in geschlossener Form](../geometry/theory.md#frenet_transformation)
- [Ruckintegral in geschlossener Form](theory.md#jerk_integral)
- [Fahrphysikalische Restriktionen](theory.md#kinematic_constraints)
- [Querkandidaten d(t) und d(s)](theory.md#lateral_sampling)
- [Lazy-Auswahl](theory.md#lazy_selection)
- [Einrasten auf der Referenz](theory.md#lock_in)
- [Längskandidaten](theory.md#longitudinal_sampling)
- [Einfädeln](theory.md#merging_mode)
- [Bewegungsprädiktion für die Reinitialisierung](theory.md#motion_prediction)
- [Mehrzielige Kostenfunktion](theory.md#multi_objective_cost)
- [Quartische Optimalpolynome](theory.md#quartic_polynomial)
- [Quintische Optimalpolynome](theory.md#quintic_polynomial)
- [Referenzpunkt und Geschwindigkeitsregime](theory.md#reference_point)
- [Ablösestrategie](theory.md#replacement_strategy)
- [Rampe des Sicherheitsabstands](theory.md#safety_margin_ramp)
- [Abschätzung des Sampling-Horizonts](theory.md#sampling_horizon)

## Erweiterungspunkte

- Neue Kostenterme über @component(kind="cost_term") oder cost.custom = [{spec, params}]
- Neue Restriktionen über @component(kind="constraint") oder constraints.custom
- Eigene Kollisionsprüfer über @component(kind="collision_checker") oder collision.checker = "python:…"
- Eigene Planervarianten als Unterklasse von WerlingPlanner (siehe baselines.py)

## Verwandte Module

[geometry](../geometry/index.md), [stabilization](../stabilization/index.md), [behavior](../behavior/index.md), [prediction](../prediction/index.md), [ad](../ad/index.md)

## Hauptquellen

[Bellman (1957)](../references.md#bellman1957), [Bryson und Ho (1975)](../references.md#bryson1975), [Kamm (1936)](../references.md#kamm1936), [Mitschke und Wallentowitz (2004)](../references.md#mitschke2004), [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv)
