# Trajektorienplanung nach Werling – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

### [Kreisapproximation (Ziegler/Stiller)](components/collision_checker__circles.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `collision_checker/circles`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.collision.CircleCollisionChecker` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Max. Krümmung](components/constraint__max_curvature.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/max_curvature`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.MaxCurvature` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Max. Ruck](components/constraint__max_jerk.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/max_jerk`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.MaxJerk` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Max. Querbeschleunigung](components/constraint__max_lateral_acceleration.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/max_lateral_acceleration`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.MaxLateralAcceleration` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Max. Längsbeschleunigung](components/constraint__max_longitudinal_acceleration.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/max_longitudinal_acceleration`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.MaxLongitudinalAcceleration` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Max. Lenkwinkel](components/constraint__max_steering_angle.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/max_steering_angle`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.MaxSteeringAngle` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Max. Lenkwinkelgeschwindigkeit](components/constraint__max_steering_velocity.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/max_steering_velocity`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.MaxSteeringVelocity` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Max. Gierrate](components/constraint__max_yaw_rate.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/max_yaw_rate`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.MaxYawRate` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Geschwindigkeitsbereich](components/constraint__speed_range.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/speed_range`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.SpeedRange` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Kammscher Kreis](components/constraint__tire_force.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/tire_force`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.TireForceConstraint` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Fahrzeugumriss im Korridor](components/constraint__vehicle_envelope.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/vehicle_envelope`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.VehicleEnvelope` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Fahrstabilität (lineares ESM)](components/constraint__vehicle_stability.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `constraint/vehicle_stability`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.constraints.VehicleStability` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Beschleunigung](components/cost_term__acceleration.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/acceleration`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.AccelerationCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Kollisionsrisiko](components/cost_term__collision_risk.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/collision_risk`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.CollisionRiskCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Komfort](components/cost_term__comfort.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/comfort`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.ComfortCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Krümmung](components/cost_term__curvature.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/curvature`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.CurvatureCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Energieeffizienz](components/cost_term__energy.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/energy`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.EnergyCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Ruck (konsistent)](components/cost_term__jerk.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/jerk`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.JerkCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Spurabweichung](components/cost_term__lane_deviation.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/lane_deviation`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.LaneDeviationCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Sicherheitsabstand](components/cost_term__safety_distance.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/safety_distance`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.SafetyDistanceCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Zielerreichung ½kδ² (konsistent)](components/cost_term__terminal_deviation.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/terminal_deviation`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.TerminalDeviationCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Endzeit k_τ τ (konsistent)](components/cost_term__terminal_time.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/terminal_time`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.TerminalTimeCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Fahrzeit](components/cost_term__travel_time.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `cost_term/travel_time`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.cost.TravelTimeCost` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

### [Frenet-Planer (naiv, ohne Konsistenz)](components/trajectory_planner__frenet_naive.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_planner/frenet_naive`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.baselines.FrenetNaivePlanner` |
| Schnittstelle | – |
| Periode | 0.1 s |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `behavior` | `BehaviorCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |
| `prediction` | `Prediction` | – | – | – |
| `status` | `ControllerStatus` | – | Trackingfehler / Reinitialisierung | optional, Rückführung |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `debug` | `PlannerDebug` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

### [Sequentieller Planer (erst längs, dann quer)](components/trajectory_planner__sequential.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_planner/sequential`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.baselines.SequentialPlanner` |
| Schnittstelle | – |
| Periode | 0.1 s |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `behavior` | `BehaviorCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |
| `prediction` | `Prediction` | – | – | – |
| `status` | `ControllerStatus` | – | Trackingfehler / Reinitialisierung | optional, Rückführung |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `debug` | `PlannerDebug` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

### [Trajektorienplaner (Werling)](components/trajectory_planner__werling.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_planner/werling`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.planning.planner.WerlingPlanner` |
| Schnittstelle | – |
| Periode | 0.1 s |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `behavior` | `BehaviorCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |
| `prediction` | `Prediction` | – | – | – |
| `status` | `ControllerStatus` | – | Trackingfehler / Reinitialisierung | optional, Rückführung |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `debug` | `PlannerDebug` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

## Öffentliche API

### `vdsim.planning.analysis`

| Name | Art | Beschreibung |
|---|---|---|
| [`continuous_solution(xi0, tau, k_xi, ref_state, k_jerk)`](../../../vdsim/planning/analysis.py#L23) | Funktion | xi0 = (xi1, xi2, xi3)(0); ref_state = (xi_ref, xi_ref_dot, xi_ref_ddot)(tau) cost: k_jerk int 1/2 u^2 + 1/2 k_xi (xi1(tau) - xi_ref(tau))^2 (the k_tau tau part is added by the caller) |
| [`transversality_residual(coeffs, tau, ref_state, k_tau, k_jerk)`](../../../vdsim/planning/analysis.py#L41) | Funktion | Hamiltonian condition for a free end time; psi from (3.6) (scaled with the jerk weight) |
| [`optimal_end_time(xi0, k_tau, k_xi, ref_fn, tau_max, n, k_jerk)`](../../../vdsim/planning/analysis.py#L51) | Funktion | continuous optimum over tau of k_jerk int 1/2 u^2 + k_tau tau + 1/2 k_xi e^2 (remark 1) |
| [`lock_in_distance(d0, k_xi, tau, k_jerk)`](../../../vdsim/planning/analysis.py#L83) | Funktion | remaining distance to the reference of the continuous optimum (xi2(0) = xi3(0) = 0, constant reference) |
| [`estimate_sampling_horizon(sampling, cost, lane_width, speed_change, position_change, factor)`](../../../vdsim/planning/analysis.py#L89) | Funktion | optimal end times of representative maneuvers -> recommended tau_max (remark 1) |
| [`lock_in_check(sampling, cost)`](../../../vdsim/planning/analysis.py#L128) | Funktion | remark 2 as a configuration check of the discrete sets (d(t), d(s), s(t) and s_dot(t)) |

### `vdsim.planning.baselines`

| Name | Art | Beschreibung |
|---|---|---|
| [`FrenetNaiveParams`](../../../vdsim/planning/baselines.py#L47) | Klasse | – |
| [`FrenetNaivePlanner`](../../../vdsim/planning/baselines.py#L56) | Klasse | – |
| [`SequentialPlanner`](../../../vdsim/planning/baselines.py#L70) | Klasse | – |

### `vdsim.planning.collision`

| Name | Art | Beschreibung |
|---|---|---|
| [`CollisionSettings`](../../../vdsim/planning/collision.py#L35) | Klasse | – |
| [`CollisionResult`](../../../vdsim/planning/collision.py#L59) | Klasse | – |
| [`CollisionChecker`](../../../vdsim/planning/collision.py#L73) | Klasse | – |
| [`CircleCheckerParams`](../../../vdsim/planning/collision.py#L92) | Klasse | – |
| [`CircleCollisionChecker`](../../../vdsim/planning/collision.py#L97) | Klasse | – |
| [`circle_cover(length, width, n)`](../../../vdsim/planning/collision.py#L66) | Funktion | Ziegler/Stiller: n circles covering a rectangle -> (offsets along the axis from the center, radius) |

### `vdsim.planning.combination`

| Name | Art | Beschreibung |
|---|---|---|
| [`PlanningContext`](../../../vdsim/planning/combination.py#L26) | Klasse | everything cost terms, constraints and collision checkers may need about the current cycle |
| [`TrajectoryBatch`](../../../vdsim/planning/combination.py#L62) | Klasse | B candidate trajectories sampled on the common check horizon (arrays of shape (B, K)). |
| [`CandidateEvaluator`](../../../vdsim/planning/combination.py#L134) | Klasse | Lazy evaluation of combined candidates (lateral index i, longitudinal index j). |
| [`time_to_arc(s_d, s_dd, d_d, d_dd, eps)`](../../../vdsim/planning/combination.py#L50) | Funktion | – |
| [`frenet_to_world(reference_line, s, s_d, s_dd, d, d_p, d_pp)`](../../../vdsim/planning/combination.py#L54) | Funktion | vectorized A.1 on arrays of any shape |

### `vdsim.planning.config`

| Name | Art | Beschreibung |
|---|---|---|
| [`config_path(name_or_path)`](../../../vdsim/planning/config.py#L17) | Funktion | – |
| [`load_planner_config(name_or_path)`](../../../vdsim/planning/config.py#L24) | Funktion | dict with "component" and "params" |
| [`create_planner(name_or_path, **overrides)`](../../../vdsim/planning/config.py#L32) | Funktion | planner instance from a configuration file (overrides: dotted parameter names, e.g. |
| [`available_configs()`](../../../vdsim/planning/config.py#L38) | Funktion | – |

### `vdsim.planning.constraints`

| Name | Art | Beschreibung |
|---|---|---|
| [`ConstraintResult`](../../../vdsim/planning/constraints.py#L38) | Klasse | – |
| [`Constraint`](../../../vdsim/planning/constraints.py#L45) | Klasse | – |
| [`LateralAccelerationParams`](../../../vdsim/planning/constraints.py#L82) | Klasse | – |
| [`MaxLateralAcceleration`](../../../vdsim/planning/constraints.py#L88) | Klasse | – |
| [`LongitudinalAccelerationParams`](../../../vdsim/planning/constraints.py#L100) | Klasse | – |
| [`MaxLongitudinalAcceleration`](../../../vdsim/planning/constraints.py#L107) | Klasse | – |
| [`JerkParams`](../../../vdsim/planning/constraints.py#L118) | Klasse | – |
| [`MaxJerk`](../../../vdsim/planning/constraints.py#L124) | Klasse | – |
| [`CurvatureParams`](../../../vdsim/planning/constraints.py#L135) | Klasse | – |
| [`MaxCurvature`](../../../vdsim/planning/constraints.py#L142) | Klasse | – |
| [`SteeringAngleParams`](../../../vdsim/planning/constraints.py#L161) | Klasse | – |
| [`MaxSteeringAngle`](../../../vdsim/planning/constraints.py#L167) | Klasse | – |
| [`SteeringRateParams`](../../../vdsim/planning/constraints.py#L185) | Klasse | – |
| [`MaxSteeringVelocity`](../../../vdsim/planning/constraints.py#L191) | Klasse | – |
| [`YawRateParams`](../../../vdsim/planning/constraints.py#L203) | Klasse | – |
| [`MaxYawRate`](../../../vdsim/planning/constraints.py#L209) | Klasse | – |
| [`TireForceParams`](../../../vdsim/planning/constraints.py#L219) | Klasse | – |
| [`TireForceConstraint`](../../../vdsim/planning/constraints.py#L226) | Klasse | – |
| [`EnvelopeParams`](../../../vdsim/planning/constraints.py#L244) | Klasse | – |
| [`VehicleEnvelope`](../../../vdsim/planning/constraints.py#L250) | Klasse | – |
| [`StabilityParams`](../../../vdsim/planning/constraints.py#L278) | Klasse | – |
| [`VehicleStability`](../../../vdsim/planning/constraints.py#L286) | Klasse | – |
| [`SpeedParams`](../../../vdsim/planning/constraints.py#L309) | Klasse | – |
| [`SpeedRange`](../../../vdsim/planning/constraints.py#L316) | Klasse | – |
| [`ConstraintSettings`](../../../vdsim/planning/constraints.py#L335) | Klasse | – |
| [`ConstraintSet`](../../../vdsim/planning/constraints.py#L351) | Klasse | Instantiated, enabled constraints of one planner. |
| [`group(label)`](../../../vdsim/planning/constraints.py#L32) | Funktion | nested parameter group (dataclass field with a GUI label) |
| [`limits_for_prefilter(settings, factor)`](../../../vdsim/planning/constraints.py#L393) | Funktion | longitudinal (a_min, a_max, v_max) and lateral \|d_ddot\| bounds for the Frenet pre-filter (step 3) |

### `vdsim.planning.cost`

| Name | Art | Beschreibung |
|---|---|---|
| [`CostTerm`](../../../vdsim/planning/cost.py#L45) | Klasse | – |
| [`JerkCostParams`](../../../vdsim/planning/cost.py#L79) | Klasse | – |
| [`JerkCost`](../../../vdsim/planning/cost.py#L86) | Klasse | – |
| [`TerminalTimeParams`](../../../vdsim/planning/cost.py#L102) | Klasse | – |
| [`TerminalTimeCost`](../../../vdsim/planning/cost.py#L109) | Klasse | – |
| [`TerminalDeviationParams`](../../../vdsim/planning/cost.py#L124) | Klasse | – |
| [`TerminalDeviationCost`](../../../vdsim/planning/cost.py#L132) | Klasse | – |
| [`AccelerationCostParams`](../../../vdsim/planning/cost.py#L152) | Klasse | – |
| [`AccelerationCost`](../../../vdsim/planning/cost.py#L159) | Klasse | – |
| [`LaneDeviationParams`](../../../vdsim/planning/cost.py#L174) | Klasse | – |
| [`LaneDeviationCost`](../../../vdsim/planning/cost.py#L181) | Klasse | – |
| [`TravelTimeParams`](../../../vdsim/planning/cost.py#L193) | Klasse | – |
| [`TravelTimeCost`](../../../vdsim/planning/cost.py#L199) | Klasse | – |
| [`EnergyParams`](../../../vdsim/planning/cost.py#L212) | Klasse | – |
| [`EnergyCost`](../../../vdsim/planning/cost.py#L219) | Klasse | – |
| [`ComfortParams`](../../../vdsim/planning/cost.py#L237) | Klasse | – |
| [`ComfortCost`](../../../vdsim/planning/cost.py#L243) | Klasse | – |
| [`CurvatureCostParams`](../../../vdsim/planning/cost.py#L254) | Klasse | – |
| [`CurvatureCost`](../../../vdsim/planning/cost.py#L260) | Klasse | – |
| [`SafetyDistanceParams`](../../../vdsim/planning/cost.py#L271) | Klasse | – |
| [`SafetyDistanceCost`](../../../vdsim/planning/cost.py#L278) | Klasse | – |
| [`CollisionRiskParams`](../../../vdsim/planning/cost.py#L292) | Klasse | – |
| [`CollisionRiskCost`](../../../vdsim/planning/cost.py#L299) | Klasse | – |
| [`CostSettings`](../../../vdsim/planning/cost.py#L314) | Klasse | – |
| [`CostModel`](../../../vdsim/planning/cost.py#L337) | Klasse | Instantiated cost terms; computes set costs, combined costs and the breakdown. |

### `vdsim.planning.kinematics`

| Name | Art | Beschreibung |
|---|---|---|
| [`EgoGeometry`](../../../vdsim/planning/kinematics.py#L21) | Klasse | – |
| [`convert_reference(state, from_point, to_point, geometry, direction)`](../../../vdsim/planning/kinematics.py#L62) | Funktion | state dict x, y, theta (direction of motion), kappa, v, a -> same dict for the other reference point. |
| [`taylor_prediction(x, y, theta, v, v_dot, theta_dot, dt)`](../../../vdsim/planning/kinematics.py#L80) | Funktion | predicted (x, y, theta, v) of the reference point after dt (dt may be an array) |
| [`ego_reference_state(ego, reference_point, geometry, slow_speed)`](../../../vdsim/planning/kinematics.py#L90) | Funktion | Reference point state (x, y, theta, v, v_dot, theta_dot, kappa, a) from a measured EgoState (CoG) |

### `vdsim.planning.lateral`

| Name | Art | Beschreibung |
|---|---|---|
| [`LateralSet`](../../../vdsim/planning/lateral.py#L26) | Klasse | – |
| [`lateral_targets(d_ref, d_step, d_range, d_min, d_max, half_width)`](../../../vdsim/planning/lateral.py#L49) | Funktion | delta_i relative to d_ref, pruned to end positions whose footprint fits into the corridor |
| [`build_lateral_set(start, mode, t_start, d_ref, d_min, d_max, half_width, sampling, grid, keep_k, prefilter_limit)`](../../../vdsim/planning/lateral.py#L63) | Funktion | start: FrenetState-like (d, d_d, d_dd, d_p, d_pp, s); grid: evaluation grid (t_rel or s_rel) |

### `vdsim.planning.longitudinal`

| Name | Art | Beschreibung |
|---|---|---|
| [`LongitudinalParams`](../../../vdsim/planning/longitudinal.py#L30) | Klasse | – |
| [`ObjectMotion`](../../../vdsim/planning/longitudinal.py#L38) | Klasse | 1d motion along the reference curve with constant acceleration, clamped at standstill |
| [`VelocityTarget`](../../../vdsim/planning/longitudinal.py#L62) | Klasse | – |
| [`StoppingTarget`](../../../vdsim/planning/longitudinal.py#L72) | Klasse | – |
| [`FollowingTarget`](../../../vdsim/planning/longitudinal.py#L88) | Klasse | – |
| [`MergingTarget`](../../../vdsim/planning/longitudinal.py#L107) | Klasse | – |
| [`LongitudinalSet`](../../../vdsim/planning/longitudinal.py#L165) | Klasse | – |
| [`object_motion(obj, reference_line, t_start, lane_id, window)`](../../../vdsim/planning/longitudinal.py#L127) | Funktion | Frenet motion (s, s_dot, s_ddot at t_start) of a predicted object along the reference curve. |
| [`build_longitudinal_set(start, target, t_start, sampling, grid, keep_k, limits, label)`](../../../vdsim/planning/longitudinal.py#L196) | Funktion | – |
| [`make_target(mode, behavior, prediction, reference_line, t_start, geometry, reference_point, direction, lon_params)`](../../../vdsim/planning/longitudinal.py#L235) | Funktion | LongitudinalMode -> target object (or (None, reason) if the mode cannot be realized) |

### `vdsim.planning.plan`

| Name | Art | Beschreibung |
|---|---|---|
| [`TrajectoryPlan`](../../../vdsim/planning/plan.py#L21) | Klasse | – |

### `vdsim.planning.planner`

| Name | Art | Beschreibung |
|---|---|---|
| [`TimingParams`](../../../vdsim/planning/planner.py#L52) | Klasse | – |
| [`StabilizationParams`](../../../vdsim/planning/planner.py#L59) | Klasse | – |
| [`SearchParams`](../../../vdsim/planning/planner.py#L70) | Klasse | – |
| [`WerlingPlannerParams`](../../../vdsim/planning/planner.py#L80) | Klasse | – |
| [`StartState`](../../../vdsim/planning/planner.py#L92) | Klasse | – |
| [`WerlingPlanner`](../../../vdsim/planning/planner.py#L156) | Klasse | – |
| [`same_line(a, b)`](../../../vdsim/planning/planner.py#L113) | Funktion | identical reference curve (object identity or identical samples) |

### `vdsim.planning.polynomials`

| Name | Art | Beschreibung |
|---|---|---|
| [`ConstantReference`](../../../vdsim/planning/polynomials.py#L91) | Klasse | reference trajectory xi_ref(t) = value (lateral d_ref, stopping position) |
| [`PolynomialSet`](../../../vdsim/planning/polynomials.py#L106) | Klasse | N optimal polynomials xi1 on [0, tau_i] plus their continuation on the target manifold. |
| [`quintic_coefficients(x0, v0, a0, x1, v1, a1, tau)`](../../../vdsim/planning/polynomials.py#L27) | Funktion | vectorized q012 / q345: start (x0, v0, a0), end (x1, v1, a1) at tau -> coefficients (..., 6), ascending |
| [`quartic_coefficients(x0, v0, a0, v1, a1, tau)`](../../../vdsim/planning/polynomials.py#L44) | Funktion | vectorized q012 / q34: free end position -> coefficients (..., 6) with c5 = 0 |
| [`coefficient_matrices(tau)`](../../../vdsim/planning/polynomials.py#L54) | Funktion | M1(tau), M2(tau) of (3.7) (used by the analysis functions and the tests) |
| [`jerk_integral(coeffs, tau)`](../../../vdsim/planning/polynomials.py#L65) | Funktion | int_0^tau xi1'''(t)^2 dt (without the factor 1/2 of (3.4)) |
| [`polyval(coeffs, t)`](../../../vdsim/planning/polynomials.py#L77) | Funktion | value and the first three derivatives; coeffs (n, 6), t (n, k) or (k,) -> 4 arrays (n, k) |

### `vdsim.planning.sampling`

| Name | Art | Beschreibung |
|---|---|---|
| [`EndGrid`](../../../vdsim/planning/sampling.py#L26) | Klasse | discretized end "times" (or arc positions) of one candidate set |
| [`SamplingParams`](../../../vdsim/planning/sampling.py#L74) | Klasse | – |
| [`end_grid(start, step, tau_min, tau_max, absolute, keep_k)`](../../../vdsim/planning/sampling.py#L35) | Funktion | End times tau_j for a start time/position `start`. |
| [`offsets(step, lower, upper, include)`](../../../vdsim/planning/sampling.py#L60) | Funktion | symmetric grid i*step (i integer) within [lower, upper]; 0 is always part of the grid |

### `vdsim.planning.selection`

| Name | Art | Beschreibung |
|---|---|---|
| [`SelectionSettings`](../../../vdsim/planning/selection.py#L26) | Klasse | – |
| [`ModeResult`](../../../vdsim/planning/selection.py#L35) | Klasse | – |
| [`select_mode(label, lat, lon, evaluator, cost_model, constraints, checker, ctx, settings, k_lat, k_lon)`](../../../vdsim/planning/selection.py#L71) | Funktion | – |
| [`fallback_candidate(res)`](../../../vdsim/planning/selection.py#L152) | Funktion | longest admissible trajectory: among candidates within the vehicle restrictions the one with the latest first collision; if every candidate violates a restriction, the latest first violation |
| [`initial_jerk(res, c, h)`](../../../vdsim/planning/selection.py#L175) | Funktion | signed initial jerk a_dot(0) of the world trajectory (exact polynomials, central difference) |
| [`choose_mode(results)`](../../../vdsim/planning/selection.py#L190) | Funktion | step 6 over all modes with a valid trajectory; None if every mode failed |
| [`choose_fallback(results)`](../../../vdsim/planning/selection.py#L200) | Funktion | – |

### `vdsim.planning.simulation`

| Name | Art | Beschreibung |
|---|---|---|
| [`ClosedLoopLog`](../../../vdsim/planning/simulation.py#L45) | Klasse | – |
| [`ego_from_point(point, geometry, reference_point, t)`](../../../vdsim/planning/simulation.py#L17) | Funktion | TrajectoryPoint of the reference point -> EgoState at the CoG (zero side slip at the reference point) |
| [`constant_velocity_object(obj_id, x0, y0, psi, v, t0, horizon, dt, length, width, obj_type, a)`](../../../vdsim/planning/simulation.py#L29) | Funktion | predicted object with constant acceleration along a straight line (speed clamped at 0) |
| [`run_closed_loop(planner, behavior_fn, ego0, t_end, prediction_fn, disturbance, period, keep_trajectories)`](../../../vdsim/planning/simulation.py#L55) | Funktion | behavior_fn(t, ego) -> BehaviorCommand; prediction_fn(t) -> Prediction; disturbance(t, ego) -> EgoState |
