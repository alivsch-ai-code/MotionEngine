# Trajektorienstabilisierung nach Werling und Fahrzeugebenen – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/stabilization/test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py) | A.5-Gleichheit, V_dot <= 0 (Satz 4, Satz 6, Vorzeichen 4.31), Nominal- und Konvergenzverhalten, Rückwärtsfahrt, Anhalten ohne Lenksprung, Satz 7 |
| [tests/stabilization/test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | (4.70) gegen zeta, Satz 9, e~_dd = w~, Reifeninversion mit Sättigung, Schleppfehler mit/ohne Sollgrößentransformation bei 30 m/s |
| [tests/stabilization/test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py) | Umschaltung ohne Sprünge, Reinitialisierung bei Böe/Querimpuls, Prädiktionsgenauigkeit, Robustheit double_track |
| [tests/stabilization/test_stabilization_classic.py](../../../tests/stabilization/test_stabilization_classic.py) | Stabilität aller klassischen Regler, MPC-Beschränkungen, ACC |
| [tests/stabilization/test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py) | Split-Range-Integrator gegen Gegenwind/Steigung, Anti-Windup, Aktor, Strecke |
| [tests/stabilization/test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py) | Modell 1 (Lagrange), Modell 4, isotroper Reifen, Lauf im alten Simulator |

## Tests, die dieses Paket verwenden

### [tests/stabilization/test_stabilization_classic.py](../../../tests/stabilization/test_stabilization_classic.py)

**Zeigt:** Stabilität aller klassischen Regler, MPC-Beschränkungen, ACC

Importiert: `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`

| Testfunktion | Beschreibung |
|---|---|
| `test_lateral_controllers_follow_trajectory` | – |
| `test_mpc_horizon_and_constraints` | – |
| `test_longitudinal_controllers_in_composite` | – |
| `test_acc_keeps_time_gap` | – |
| `test_classic_components_have_docs` | – |

### [tests/stabilization/test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py)

**Zeigt:** (4.70) gegen zeta, Satz 9, e~_dd = w~, Reifeninversion mit Sättigung, Schleppfehler mit/ohne Sollgrößentransformation bei 30 m/s

Importiert: `vdsim.stabilization.errors`, `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`, `vdsim.stabilization.werling_dynamic`

| Testfunktion | Beschreibung |
|---|---|
| `test_lambda_formula_gives_constant_damping` | – |
| `test_satz9_minimum_phase_condition` | – |
| `test_satz9_closed_loop_zero_dynamics` | errors held at zero by the controller, the yaw motion follows the zero dynamics (4.67) |
| `test_linearizing_feedback_achieves_w` | e_dd = w~ for the circle reference (equivalent formulation of (4.60)), checked by finite differences |
| `test_tire_inversion_with_saturation` | – |
| `test_point_kinematics_consistency` | – |
| `test_zero_dynamics_reference_steady_state_circle` | reference vehicle on a circle: r0 -> v kappa, delta0 -> l kappa + EG v^2 kappa (linear range) |
| `test_nominal_tracking_on_design_model` | – |
| `test_reference_transformation_removes_lag_error_at_30ms` | – |

### [tests/stabilization/test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py)

**Zeigt:** A.5-Gleichheit, V_dot <= 0 (Satz 4, Satz 6, Vorzeichen 4.31), Nominal- und Konvergenzverhalten, Rückwärtsfahrt, Anhalten ohne Lenksprung, Satz 7

Importiert: `vdsim.stabilization.common`, `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`, `vdsim.stabilization.werling_kinematic`

| Testfunktion | Beschreibung |
|---|---|
| `test_a5_port_is_identical_to_structured_law` | – |
| `test_lyapunov_satz4_numeric` | V_c_dot along the closed loop equals -s_d_dot k2 e_psi^2 - k3 e_v^2 - k4 e_delta^2 <= 0 |
| `test_lyapunov_satz6_sign_of_431` | with the sign of the proof V~_dot = -k4 e_th^2 - k3 e_v^2 <= 0; the printed sign adds 2 k1 e_v e_n sin(e_th), which is indefinite for (k1 e_n)^2 > k3 k4 (here e_n > 6.3 m) |
| `test_nominal_zero_tracking_error_on_design_model` | – |
| `test_convergence_from_initial_errors` | – |
| `test_reverse_driving_satz4_on_plant` | – |
| `test_stop_to_standstill_without_steering_jump` | – |
| `test_zero_dynamics_satz7_and_jack_knife` | – |
| `test_center_controller_orientation_converges` | Satz 7: only the position is stabilized, the orientation converges through the zero dynamics |

### [tests/stabilization/test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py)

**Zeigt:** Split-Range-Integrator gegen Gegenwind/Steigung, Anti-Windup, Aktor, Strecke

Importiert: `vdsim.stabilization`, `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`

Komponenten: `actuator/steering_powertrain`, `tracking_controller/werling_bilevel`, `tracking_controller/werling_dynamic`, `tracking_controller/werling_kinematic_center`, `tracking_controller/werling_kinematic_orientation`, `vehicle_dynamics/split_range`, `vehicle_plant/vehicle_model`

| Testfunktion | Beschreibung |
|---|---|
| `test_split_range_integrator_compensates_disturbance` | vdsim aero_drag uses v_rel = vx - wind_speed: head wind = negative wind_speed |
| `test_split_range_anti_windup` | – |
| `test_actuator_integrates_rate_limits_and_latency` | – |
| `test_plant_wraps_vehicle_models` | – |
| `test_plant_reverse_driving` | – |
| `test_components_registered_with_docs` | – |
| `test_traceability_of_equations` | – |
| `test_parameter_configs_instantiate` | – |

### [tests/stabilization/test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py)

**Zeigt:** Modell 1 (Lagrange), Modell 4, isotroper Reifen, Lauf im alten Simulator

| Testfunktion | Beschreibung |
|---|---|
| `test_models_registered` | – |
| `test_kesm_lagrange_and_singularity_free` | Euler-Lagrange equation of the derivation: s_dd (m + M tan^2 delta) + 2 M v delta_dot tan(delta)/cos^2 = Q, i.e. power balance E_dot = Q v - M v^2 tan(delta) delta_dot / cos^2 (rheonomic steering constraint) |
| `test_kesm_plant_reverses_and_holds_at_standstill` | – |
| `test_desm_matches_model4_and_linear_gain` | vx/vy plant form equals model 4 in (beta, v) coordinates |
| `test_kesm_runs_in_old_simulator` | – |
| `test_desm_standstill_and_low_speed` | – |
| `test_isotropic_tire_inversion` | – |
| `test_isotropic_tire_saturation` | – |

### [tests/stabilization/test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py)

**Zeigt:** Umschaltung ohne Sprünge, Reinitialisierung bei Böe/Querimpuls, Prädiktionsgenauigkeit, Robustheit double_track

Importiert: `vdsim.stabilization.reinit`, `vdsim.stabilization.simulate`, `vdsim.stabilization.switching`, `vdsim.stabilization.trajectories`

| Testfunktion | Beschreibung |
|---|---|
| `test_select_controller_regimes` | – |
| `test_switching_rear_axle_to_cog_without_jumps` | – |
| `test_elliptic_measure_and_monitor` | – |
| `test_prediction_taylor_series_matches_exact_arc` | – |
| `test_reinitialization_on_side_wind_gust` | – |
| `test_reinitialization_on_lateral_impulse` | – |
| `test_prediction_accuracy` | – |
| `test_robustness_double_track_plant` | model error: Werling controller designed on the DESM, plant = vdsim double-track model |

## Validierung von [actuator/steering_powertrain](components/actuator__steering_powertrain.md)

- tests/stabilization/test_stabilization_layers.py

## Validierung von [tracking_controller/acc](components/tracking_controller__acc.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/composite](components/tracking_controller__composite.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/ff_fb](components/tracking_controller__ff_fb.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/lqr](components/tracking_controller__lqr.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/mpc](components/tracking_controller__mpc.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/pi](components/tracking_controller__pi.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/pid](components/tracking_controller__pid.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/pure_pursuit](components/tracking_controller__pure_pursuit.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/speed_pi](components/tracking_controller__speed_pi.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/stanley](components/tracking_controller__stanley.md)

- tests/stabilization/test_stabilization_classic.py

## Validierung von [tracking_controller/werling_bilevel](components/tracking_controller__werling_bilevel.md)

- tests/stabilization/test_stabilization_switching.py

## Validierung von [tracking_controller/werling_dynamic](components/tracking_controller__werling_dynamic.md)

- tests/stabilization/test_stabilization_dynamic.py

## Validierung von [tracking_controller/werling_kinematic_center](components/tracking_controller__werling_kinematic_center.md)

- tests/stabilization/test_stabilization_kinematic.py

## Validierung von [tracking_controller/werling_kinematic_orientation](components/tracking_controller__werling_kinematic_orientation.md)

- tests/stabilization/test_stabilization_kinematic.py

## Validierung von [vehicle_dynamics/split_range](components/vehicle_dynamics__split_range.md)

- tests/stabilization/test_stabilization_layers.py

## Validierung von [vehicle_plant/vehicle_model](components/vehicle_plant__vehicle_model.md)

- tests/stabilization/test_stabilization_layers.py
