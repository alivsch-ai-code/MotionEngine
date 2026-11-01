# Trajektorienplanung nach Werling – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `sampling.absolute_grid` | absolutes Endzeitraster (Standard true); false = relatives Raster ohne Konsistenz | – | – |
| `sampling.lat_tau_step / lat_tau_max / lat_d_step / lat_d_range` | Raster der Querkandidaten d(t) (Δτ = 0.5 s bis 5 s, δ = ±3.5 m in 0.5 m) | – | – |
| `sampling.arc_s_step / arc_s_max` | Endpositionsraster d(s) (1 m bis 20 m) | – | – |
| `sampling.lon_tau_step / lon_tau_max / lon_nu_* / lon_sigma_*` | Raster der Längskandidaten (Δτ = 1 s bis 8 s, ν = ±4 m/s fein + grob bis Stillstand, σ = ±3 m) | – | – |
| `cost.terminal_time.k_tau_lat / cost.terminal_deviation.k_delta` | Werling-Gewichte k_τ, k_δ (5, 200); Einrasten nach Bemerkung 2 geprüft | – | – |
| `cost.k_lat / cost.k_lon` | Gewichtung von Quer- und Längskosten (3.2), Werling 1 und k_s | – | – |
| `constraints.<name>.enabled / Grenzwerte` | jede Restriktion einzeln aktivierbar und parametrierbar | – | – |
| `collision.horizon / collision.margin_<typ> / collision.margin_ramp` | Prüfhorizont 3 s, Sicherheitsabstände je Objekttyp, Aufbau über Δt (Abb. 3.10) | – | – |
| `timing.t_comp` | konservative Rechenzeit; Start der neuen Polynome bei t + t_comp | – | – |
| `stabilization.strategy` | bilevel (Standard), low_level, high_level | – | – |
| `configs/planning/{default,comfort,sporty}.json` | fertige Parametrierungen, laden mit vdsim.planning.create_planner(name) | – | – |

## Parameter von [Kreisapproximation (Ziegler/Stiller)](components/collision_checker__circles.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n_circles_ego` | Kreise Ego (< 0: aus Planer-Einstellung) | – | -1 | -1 | 10 |

## Parameter von [Max. Krümmung](components/constraint__max_curvature.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `kappa_max` | Max. Krümmung (≤ 0: aus Lenkanschlag und Radstand) | 1/m | -1 | -1 | 2 |
| `auto_factor` | Faktor auf tan(δ_max)/l (automatisch) | - | 0.95 | 0.1 | 1 |

## Parameter von [Max. Ruck](components/constraint__max_jerk.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `j_max` | Max. Längsruck \|ȧ\| | m/s³ | 25 | 1 | 200 |

## Parameter von [Max. Querbeschleunigung](components/constraint__max_lateral_acceleration.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `a_max` | Max. Querbeschleunigung \|v²κ\| | m/s² | 6 | 0.5 | 15 |

## Parameter von [Max. Längsbeschleunigung](components/constraint__max_longitudinal_acceleration.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `a_accel_max` | Max. Beschleunigung | m/s² | 3 | 0.2 | 10 |
| `a_decel_max` | Max. Verzögerung | m/s² | 8 | 0.5 | 12 |

## Parameter von [Max. Lenkwinkel](components/constraint__max_steering_angle.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `delta_max` | Max. Radlenkwinkel (≤ 0: aus Fahrzeug) | rad | -1 | -1 | 1.2 |

## Parameter von [Max. Lenkwinkelgeschwindigkeit](components/constraint__max_steering_velocity.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `rate_max` | Max. Radlenkwinkelgeschwindigkeit | rad/s | 0.7 | 0.05 | 5 |

## Parameter von [Max. Gierrate](components/constraint__max_yaw_rate.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `r_max` | Max. Gierrate \|vκ\| | rad/s | 1.2 | 0.05 | 5 |

## Parameter von [Geschwindigkeitsbereich](components/constraint__speed_range.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `v_max` | Max. Bahngeschwindigkeit | m/s | 60 | 1 | 100 |
| `allow_reversal` | Richtungsumkehr innerhalb einer Trajektorie zulassen | – | False | – | – |

## Parameter von [Kammscher Kreis](components/constraint__tire_force.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `eta` | Ausnutzungsgrad η des Kammschen Kreises | - | 0.9 | 0.1 | 1 |
| `mu` | Reibwert μ (≤ 0: aus Reifenparametern) | - | -1 | -1 | 2 |

## Parameter von [Fahrzeugumriss im Korridor](components/constraint__vehicle_envelope.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `margin` | Zusätzlicher Abstand zum Korridorrand | m | 0 | 0 | 2 |

## Parameter von [Fahrstabilität (lineares ESM)](components/constraint__vehicle_stability.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `beta_max` | Max. stationärer Schwimmwinkel (dynamischer Anteil) | rad | 0.12 | 0.01 | 0.5 |
| `ay_linear_max` | Querbeschleunigung im linearen Bereich, Anteil von μ g | - | 0.8 | 0.1 | 1 |
| `v_min` | Prüfung erst ab Geschwindigkeit | m/s | 5 | 0 | 30 |

## Parameter von [Beschleunigung](components/cost_term__acceleration.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight_lat` | Gewicht ∫ d̈² dt (bzw. ∫ d''² ds) | s³/m² | 0 | 0 | – |
| `weight_lon` | Gewicht ∫ s̈² dt | s³/m² | 0 | 0 | – |

## Parameter von [Kollisionsrisiko](components/cost_term__collision_risk.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ exp(−Abstand²/(2σ²)) dt | 1/s | 0 | 0 | – |
| `sigma` | Unsicherheit σ der Objektposition | m | 1 | 0.05 | 10 |

## Parameter von [Komfort](components/cost_term__comfort.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ (a_quer² + a_längs²) dt (Weltkoordinaten) | s³/m² | 0 | 0 | – |

## Parameter von [Krümmung](components/cost_term__curvature.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ κ² dℓ | m | 0 | 0 | – |

## Parameter von [Energieeffizienz](components/cost_term__energy.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht Traktionsenergie je Masse | s²/m² | 0 | 0 | – |
| `regen_efficiency` | Rückgewinnungsgrad beim Verzögern | - | 0 | 0 | 1 |

## Parameter von [Ruck (konsistent)](components/cost_term__jerk.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_lat` | Gewicht Querruck d(t)  ∫½ d⃛² dt | - | 1 | 0 | – |
| `k_arc` | Gewicht Querruck d(s)  ∫½ d‴² ds | - | 1000 | 0 | – |
| `k_lon` | Gewicht Längsruck ∫½ s⃛² dt | - | 1 | 0 | – |

## Parameter von [Spurabweichung](components/cost_term__lane_deviation.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ (d − d_ref)² dt | 1/(m² s) | 0 | 0 | – |
| `relative_to_d_ref` | Abweichung zu d_ref (sonst zur Spurmitte d = 0) | – | True | – | – |

## Parameter von [Sicherheitsabstand](components/cost_term__safety_distance.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ max(0, d_soll − Abstand)² dt | 1/(m² s) | 0 | 0 | – |
| `distance` | Weicher Wunschabstand zu Objekten | m | 2 | 0 | 20 |

## Parameter von [Zielerreichung ½kδ² (konsistent)](components/cost_term__terminal_deviation.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_delta` | k_δ Endversatz quer (d(t)) | 1/m² | 200 | 0 | – |
| `k_delta_arc` | k_δ Endversatz quer (d(s)) | 1/m² | 600 | 0 | – |
| `k_sigma` | k_σ Positionsversatz (Folgen, Einfädeln, Anhalten) | 1/m² | 30 | 0 | – |
| `k_nu` | k_ν Geschwindigkeitsversatz | s²/m² | 20 | 0 | – |

## Parameter von [Endzeit k_τ τ (konsistent)](components/cost_term__terminal_time.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_tau_lat` | k_τ quer (d(t)) | 1/s | 5 | 0 | – |
| `k_s_arc` | k_s quer (d(s)): k_s [s(τ) − s(0)] | 1/m | 8 | 0 | – |
| `k_tau_lon` | k_τ längs | 1/s | 2 | 0 | – |

## Parameter von [Fahrzeit](components/cost_term__travel_time.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht Zeitverlust gegenüber Wunschgeschwindigkeit | 1/s | 0 | 0 | – |

## Parameter von [Frenet-Planer (naiv, ohne Konsistenz)](components/trajectory_planner__frenet_naive.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `sampling` | Sampling (relatives Raster) | – | {…} | – | – |
| `longitudinal` | Längsmodi | – | {…} | – | – |
| `cost` | Kostenfunktion | – | {…} | – | – |
| `constraints` | Restriktionen | – | {…} | – | – |
| `collision` | Kollisionsprüfung | – | {…} | – | – |
| `timing` | Zeitverhalten | – | {…} | – | – |
| `stabilization` | Stabilisierung (immer vom Messzustand) | – | {…} | – | – |
| `search` | Suche | – | {…} | – | – |

## Parameter von [Sequentieller Planer (erst längs, dann quer)](components/trajectory_planner__sequential.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `sampling` | Sampling (Zielmannigfaltigkeiten) | – | {…} | – | – |
| `longitudinal` | Längsmodi | – | {…} | – | – |
| `cost` | Kostenfunktion | – | {…} | – | – |
| `constraints` | Restriktionen | – | {…} | – | – |
| `collision` | Kollisionsprüfung | – | {…} | – | – |
| `timing` | Zeitverhalten | – | {…} | – | – |
| `stabilization` | Bi-level-Stabilisierung | – | {…} | – | – |
| `search` | Suche | – | {…} | – | – |

## Parameter von [Trajektorienplaner (Werling)](components/trajectory_planner__werling.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `sampling` | Sampling (Zielmannigfaltigkeiten) | – | {…} | – | – |
| `longitudinal` | Längsmodi | – | {…} | – | – |
| `cost` | Kostenfunktion | – | {…} | – | – |
| `constraints` | Restriktionen | – | {…} | – | – |
| `collision` | Kollisionsprüfung | – | {…} | – | – |
| `timing` | Zeitverhalten | – | {…} | – | – |
| `stabilization` | Bi-level-Stabilisierung | – | {…} | – | – |
| `search` | Suche | – | {…} | – | – |

## Parametersatz `FrenetNaiveParams` (`vdsim.planning.baselines`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `sampling` | Sampling (relatives Raster) | – | {…} | – | – |
| `longitudinal` | Längsmodi | – | {…} | – | – |
| `cost` | Kostenfunktion | – | {…} | – | – |
| `constraints` | Restriktionen | – | {…} | – | – |
| `collision` | Kollisionsprüfung | – | {…} | – | – |
| `timing` | Zeitverhalten | – | {…} | – | – |
| `stabilization` | Stabilisierung (immer vom Messzustand) | – | {…} | – | – |
| `search` | Suche | – | {…} | – | – |

## Parametersatz `CollisionSettings` (`vdsim.planning.collision`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `checker` | Kollisionsprüfer (Spec) | – | collision_checker/circles | – | – |
| `horizon` | Einheitlicher Prüfhorizont | s | 3 | 0.5 | 10 |
| `dt` | Zeitraster der Prüfung | s | 0.1 | 0.01 | 0.5 |
| `margin_ramp` | Aufbauzeit Δt des Sicherheitsabstands (Abb. 3.10) | s | 1 | 0 | 5 |
| `margin_car` | Sicherheitsabstand Pkw | m | 0.5 | 0 | 5 |
| `margin_truck` | Sicherheitsabstand Lkw | m | 0.7 | 0 | 5 |
| `margin_pedestrian` | Sicherheitsabstand Fußgänger | m | 1.5 | 0 | 5 |
| `margin_cyclist` | Sicherheitsabstand Radfahrer | m | 1 | 0 | 5 |
| `margin_static` | Sicherheitsabstand statische Hindernisse | m | 0.3 | 0 | 5 |
| `margin_unknown` | Sicherheitsabstand unbekannt | m | 0.5 | 0 | 5 |
| `min_probability` | Prädiktionen mit kleinerer Wahrscheinlichkeit ignorieren | - | 0.05 | 0 | 1 |
| `front_overhang` | Überhang vorne (< 0: aus Länge und Radstand) | m | -1 | -1 | 3 |
| `rear_overhang` | Überhang hinten (< 0: aus Länge und Radstand) | m | -1 | -1 | 3 |
| `n_circles_ego` | Kreise Ego-Fahrzeug | – | 3 | 1 | 10 |
| `max_circles_object` | Max. Kreise je Objekt | – | 5 | 1 | 20 |
| `checker_params` | Parameter eines eigenen Prüfers | – | {…} | – | – |

## Parametersatz `CircleCheckerParams` (`vdsim.planning.collision`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n_circles_ego` | Kreise Ego (< 0: aus Planer-Einstellung) | – | -1 | -1 | 10 |

## Parametersatz `LateralAccelerationParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `a_max` | Max. Querbeschleunigung \|v²κ\| | m/s² | 6 | 0.5 | 15 |

## Parametersatz `LongitudinalAccelerationParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `a_accel_max` | Max. Beschleunigung | m/s² | 3 | 0.2 | 10 |
| `a_decel_max` | Max. Verzögerung | m/s² | 8 | 0.5 | 12 |

## Parametersatz `JerkParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `j_max` | Max. Längsruck \|ȧ\| | m/s³ | 25 | 1 | 200 |

## Parametersatz `CurvatureParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `kappa_max` | Max. Krümmung (≤ 0: aus Lenkanschlag und Radstand) | 1/m | -1 | -1 | 2 |
| `auto_factor` | Faktor auf tan(δ_max)/l (automatisch) | - | 0.95 | 0.1 | 1 |

## Parametersatz `SteeringAngleParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `delta_max` | Max. Radlenkwinkel (≤ 0: aus Fahrzeug) | rad | -1 | -1 | 1.2 |

## Parametersatz `SteeringRateParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `rate_max` | Max. Radlenkwinkelgeschwindigkeit | rad/s | 0.7 | 0.05 | 5 |

## Parametersatz `YawRateParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `r_max` | Max. Gierrate \|vκ\| | rad/s | 1.2 | 0.05 | 5 |

## Parametersatz `TireForceParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `eta` | Ausnutzungsgrad η des Kammschen Kreises | - | 0.9 | 0.1 | 1 |
| `mu` | Reibwert μ (≤ 0: aus Reifenparametern) | - | -1 | -1 | 2 |

## Parametersatz `EnvelopeParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `margin` | Zusätzlicher Abstand zum Korridorrand | m | 0 | 0 | 2 |

## Parametersatz `StabilityParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `beta_max` | Max. stationärer Schwimmwinkel (dynamischer Anteil) | rad | 0.12 | 0.01 | 0.5 |
| `ay_linear_max` | Querbeschleunigung im linearen Bereich, Anteil von μ g | - | 0.8 | 0.1 | 1 |
| `v_min` | Prüfung erst ab Geschwindigkeit | m/s | 5 | 0 | 30 |

## Parametersatz `SpeedParams` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `v_max` | Max. Bahngeschwindigkeit | m/s | 60 | 1 | 100 |
| `allow_reversal` | Richtungsumkehr innerhalb einer Trajektorie zulassen | – | False | – | – |

## Parametersatz `ConstraintSettings` (`vdsim.planning.constraints`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_range` | Geschwindigkeitsbereich | – | {…} | – | – |
| `max_lateral_acceleration` | Max. Querbeschleunigung | – | {…} | – | – |
| `max_longitudinal_acceleration` | Max. Längsbeschleunigung | – | {…} | – | – |
| `max_jerk` | Max. Ruck | – | {…} | – | – |
| `max_curvature` | Max. Krümmung | – | {…} | – | – |
| `max_steering_angle` | Max. Lenkwinkel | – | {…} | – | – |
| `max_steering_velocity` | Max. Lenkwinkelgeschwindigkeit | – | {…} | – | – |
| `max_yaw_rate` | Max. Gierrate | – | {…} | – | – |
| `tire_force` | Kammscher Kreis | – | {…} | – | – |
| `vehicle_envelope` | Fahrzeugumriss im Korridor | – | {…} | – | – |
| `vehicle_stability` | Fahrstabilität | – | {…} | – | – |
| `custom` | Weitere Restriktionen [{spec, params}] | – | [] | – | – |

## Parametersatz `JerkCostParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_lat` | Gewicht Querruck d(t)  ∫½ d⃛² dt | - | 1 | 0 | – |
| `k_arc` | Gewicht Querruck d(s)  ∫½ d‴² ds | - | 1000 | 0 | – |
| `k_lon` | Gewicht Längsruck ∫½ s⃛² dt | - | 1 | 0 | – |

## Parametersatz `TerminalTimeParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_tau_lat` | k_τ quer (d(t)) | 1/s | 5 | 0 | – |
| `k_s_arc` | k_s quer (d(s)): k_s [s(τ) − s(0)] | 1/m | 8 | 0 | – |
| `k_tau_lon` | k_τ längs | 1/s | 2 | 0 | – |

## Parametersatz `TerminalDeviationParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_delta` | k_δ Endversatz quer (d(t)) | 1/m² | 200 | 0 | – |
| `k_delta_arc` | k_δ Endversatz quer (d(s)) | 1/m² | 600 | 0 | – |
| `k_sigma` | k_σ Positionsversatz (Folgen, Einfädeln, Anhalten) | 1/m² | 30 | 0 | – |
| `k_nu` | k_ν Geschwindigkeitsversatz | s²/m² | 20 | 0 | – |

## Parametersatz `AccelerationCostParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight_lat` | Gewicht ∫ d̈² dt (bzw. ∫ d''² ds) | s³/m² | 0 | 0 | – |
| `weight_lon` | Gewicht ∫ s̈² dt | s³/m² | 0 | 0 | – |

## Parametersatz `LaneDeviationParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ (d − d_ref)² dt | 1/(m² s) | 0 | 0 | – |
| `relative_to_d_ref` | Abweichung zu d_ref (sonst zur Spurmitte d = 0) | – | True | – | – |

## Parametersatz `TravelTimeParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht Zeitverlust gegenüber Wunschgeschwindigkeit | 1/s | 0 | 0 | – |

## Parametersatz `EnergyParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht Traktionsenergie je Masse | s²/m² | 0 | 0 | – |
| `regen_efficiency` | Rückgewinnungsgrad beim Verzögern | - | 0 | 0 | 1 |

## Parametersatz `ComfortParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ (a_quer² + a_längs²) dt (Weltkoordinaten) | s³/m² | 0 | 0 | – |

## Parametersatz `CurvatureCostParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ κ² dℓ | m | 0 | 0 | – |

## Parametersatz `SafetyDistanceParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ max(0, d_soll − Abstand)² dt | 1/(m² s) | 0 | 0 | – |
| `distance` | Weicher Wunschabstand zu Objekten | m | 2 | 0 | 20 |

## Parametersatz `CollisionRiskParams` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ exp(−Abstand²/(2σ²)) dt | 1/s | 0 | 0 | – |
| `sigma` | Unsicherheit σ der Objektposition | m | 1 | 0.05 | 10 |

## Parametersatz `CostSettings` (`vdsim.planning.cost`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_lat` | Gewicht Querkosten k_lat (3.2) | - | 1 | 0 | – |
| `k_lon` | Gewicht Längskosten k_lon = k_s (3.2) | - | 1 | 0 | – |
| `rerank_window` | Re-Ranking-Fenster für nicht separierbare Terme | – | 10 | 1 | 500 |
| `jerk` | Ruck (konsistent) | – | {…} | – | – |
| `terminal_time` | Endzeit (konsistent) | – | {…} | – | – |
| `terminal_deviation` | Zielerreichung (konsistent) | – | {…} | – | – |
| `acceleration` | Beschleunigung | – | {…} | – | – |
| `lane_deviation` | Spurabweichung | – | {…} | – | – |
| `travel_time` | Fahrzeit | – | {…} | – | – |
| `energy` | Energieeffizienz | – | {…} | – | – |
| `comfort` | Komfort | – | {…} | – | – |
| `curvature` | Krümmung | – | {…} | – | – |
| `safety_distance` | Sicherheitsabstand | – | {…} | – | – |
| `collision_risk` | Kollisionsrisiko | – | {…} | – | – |
| `custom` | Weitere Kostenterme [{spec, params}] | – | [] | – | – |

## Parametersatz `LongitudinalParams` (`vdsim.planning.longitudinal`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k0` | Folgen: Mindestabstand k0 (Stoßstange zu Stoßstange) | m | 5 | 0 | 50 |
| `kv` | Folgen: Zeitlücke kv | s | 1.5 | 0 | 5 |
| `prediction_window` | Schätzfenster s, ṡ, s̈ der Objekte | s | 1 | 0.1 | 5 |
| `v_max` | Max. Geschwindigkeit (Vorfilter) | m/s | 60 | 1 | 100 |

## Parametersatz `TimingParams` (`vdsim.planning.planner`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `t_comp` | Konservative Rechenzeit t_comp (Startzeit t0 + t_comp) | s | 0.05 | 0 | 1 |
| `dt_out` | Abtastung der Ausgabetrajektorie | s | 0.05 | 0.005 | 0.5 |
| `output_horizon` | Ausgabehorizont (auf der Mannigfaltigkeit verlängert) | s | 6 | 0.5 | 30 |

## Parametersatz `StabilizationParams` (`vdsim.planning.planner`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `strategy` | Stabilisierungsstrategie | – | bilevel | – | – |
| `v_switch` | Umschaltgeschwindigkeit v_s langsam/schnell | m/s | 3 | 0 | 20 |
| `hysteresis` | Hysterese der Umschaltung | m/s | 0.5 | 0 | 5 |
| `use_controller_prediction` | Prädiktion des Reglers (ControllerStatus.prediction) nutzen | – | True | – | – |
| `reinit_distance` | Zusätzliche Reinitialisierung ab Positionsfehler (0 = aus) | m | 0 | 0 | 50 |

## Parametersatz `SearchParams` (`vdsim.planning.planner`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `batch_min` | Erste Batchgröße der Lazy-Prüfung | – | 32 | 1 | 4096 |
| `batch_max` | Max. Batchgröße | – | 1024 | 1 | 8192 |
| `max_checks` | Max. geprüfte Kandidaten je Modus | – | 15000 | 1 | 200000 |
| `brake_candidates` | Zusätzlich geprüfte Bremskandidaten (Fallback) | – | 8 | 0 | 100 |
| `debug_candidates` | Kandidaten in PlannerDebug | – | 150 | 0 | 2000 |
| `arc_grid_step` | Prüfraster d(s) für den Vorfilter | m | 0.5 | 0.05 | 5 |

## Parametersatz `WerlingPlannerParams` (`vdsim.planning.planner`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `sampling` | Sampling (Zielmannigfaltigkeiten) | – | {…} | – | – |
| `longitudinal` | Längsmodi | – | {…} | – | – |
| `cost` | Kostenfunktion | – | {…} | – | – |
| `constraints` | Restriktionen | – | {…} | – | – |
| `collision` | Kollisionsprüfung | – | {…} | – | – |
| `timing` | Zeitverhalten | – | {…} | – | – |
| `stabilization` | Bi-level-Stabilisierung | – | {…} | – | – |
| `search` | Suche | – | {…} | – | – |

## Parametersatz `SamplingParams` (`vdsim.planning.sampling`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `absolute_grid` | Absolutes Endzeitraster (zeitliche Konsistenz, Satz 3) | – | True | – | – |
| `lat_tau_step` | Raster Endzeit quer Δτ | s | 0.5 | 0.05 | 2 |
| `lat_tau_min` | Kleinste Endzeit quer τ_min | s | 0.05 | 0 | 2 |
| `lat_tau_max` | Größte Endzeit quer τ_max | s | 5 | 0.5 | 15 |
| `lat_d_step` | Raster Querversatz δ | m | 0.5 | 0.05 | 2 |
| `lat_d_range` | Max. Querversatz \|δ\| relativ zu d_ref | m | 3.5 | 0 | 10 |
| `arc_s_step` | Raster Endposition d(s) Δs | m | 1 | 0.1 | 10 |
| `arc_s_min` | Kleinste Bogenlänge d(s) | m | 0.05 | 0 | 10 |
| `arc_s_max` | Größte Bogenlänge d(s) | m | 20 | 1 | 100 |
| `lon_tau_step` | Raster Endzeit längs Δτ | s | 1 | 0.05 | 2 |
| `lon_tau_min` | Kleinste Endzeit längs τ_min | s | 0.05 | 0 | 2 |
| `lon_tau_max` | Größte Endzeit längs τ_max | s | 8 | 0.5 | 20 |
| `lon_sigma_step` | Raster Positionsversatz σ | m | 1 | 0.05 | 10 |
| `lon_sigma_range` | Max. Positionsversatz \|σ\| | m | 3 | 0 | 30 |
| `stop_allow_overshoot` | Anhalten: σ > 0 (hinter der Haltelinie) zulassen | – | False | – | – |
| `lon_nu_step` | Raster Geschwindigkeitsversatz ν | m/s | 1 | 0.05 | 10 |
| `lon_nu_range` | Max. Geschwindigkeitsversatz \|ν\| | m/s | 4 | 0 | 30 |
| `include_stop_candidates` | Geschwindigkeitsmodus: Anhaltekandidaten (Endgeschw. 0) ergänzen | – | True | – | – |
| `lon_nu_coarse_step` | Grobes ν-Raster unterhalb von −\|ν\|max bis Stillstand (0 = aus) | m/s | 2 | 0 | 10 |
| `prefilter` | Vorfilter straßenrelativer Beschleunigungen (Schritt 3) | – | True | – | – |
| `prefilter_factor` | Vorfilter: Faktor auf die Restriktionsgrenzen | - | 1.25 | 1 | 5 |

## Konfigurationsdateien, die Komponenten dieses Pakets verwenden

| Datei | Titel | Komponenten |
|---|---|---|
| [configs/planning/comfort.json](../../../configs/planning/comfort.json) | comfort | `trajectory_planner/werling` |
| [configs/planning/default.json](../../../configs/planning/default.json) | default | `trajectory_planner/werling` |
| [configs/planning/sporty.json](../../../configs/planning/sporty.json) | sporty | `trajectory_planner/werling` |
