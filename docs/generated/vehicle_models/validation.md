# Fahrzeugmodelle – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_vehicle_models.py](../../../tests/test_vehicle_models.py) | lineares Modell gleich analytischer Gierverstärkung, nichtlineare Modelle innerhalb 15 %, Wankgradient und Radlasten des Zweispurmodells gegen quasi-statische Analyse, statisches Gleichgewicht des Mehrkörpermodells, kinematischer Kreis, Radblockieren ohne ABS |

## Tests, die dieses Paket verwenden

### [tests/knowledge/test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py)

Komponenten: `vehicle_model/double_track`

| Testfunktion | Beschreibung |
|---|---|
| `test_collects_whole_repository` | – |
| `test_legacy_and_framework_components` | – |
| `test_traces_from_code_and_module_yaml` | – |
| `test_handwritten_docs_complete` | – |
| `test_tests_examples_and_configs_linked` | – |
| `test_tolerant_against_broken_files` | – |

### [tests/stabilization/test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py)

Importiert: `vdsim.vehicle_models.werling_models`

Komponenten: `vehicle_model/werling_desm`

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

Importiert: `vdsim.vehicle_models.werling_models`

Komponenten: `vehicle_model/werling_kesm`

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

Komponenten: `vehicle_model/bicycle_kinematic`, `vehicle_model/double_track`, `vehicle_model/werling_desm`, `vehicle_model/werling_kesm`

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

Importiert: `vdsim.vehicle_models.werling_models`

Komponenten: `vehicle_model/werling_desm`, `vehicle_model/werling_kesm`

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

### [tests/test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py)

Komponenten: `vehicle_model/bicycle_kinematic`, `vehicle_model/bicycle_nonlinear`, `vehicle_model/double_track`

| Testfunktion | Beschreibung |
|---|---|
| `test_dlc_path_tracking` | – |
| `test_stanley_has_no_steady_state_offset_in_tight_turns` | – |
| `test_acc_keeps_time_gap` | – |
| `test_aeb_avoids_stationary_obstacle` | – |
| `test_lane_keeping_assist_prevents_departure` | – |
| `test_torque_vectoring_reduces_understeer` | – |
| `test_active_roll_reduces_roll_and_rear_steering_acts` | – |
| `test_esp_reduces_side_slip_in_sine_with_dwell` | – |
| `test_latency_chain_scenario_estimates_actuator_error` | – |

### [tests/test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py)

Komponenten: `vehicle_model/bicycle_linear`, `vehicle_model/bicycle_nonlinear`, `vehicle_model/double_track`

| Testfunktion | Beschreibung |
|---|---|
| `test_vehicle_config_json_roundtrip` | – |
| `test_scenario_library_builds` | – |
| `test_scenario_roundtrip` | – |
| `test_solvers_agree` | – |
| `test_results_save_load` | – |
| `test_maneuver_kpis` | – |
| `test_iso2631_weighting` | – |
| `test_report_and_comparison` | – |

### [tests/test_vehicle_models.py](../../../tests/test_vehicle_models.py)

**Zeigt:** lineares Modell gleich analytischer Gierverstärkung, nichtlineare Modelle innerhalb 15 %, Wankgradient und Radlasten des Zweispurmodells gegen quasi-statische Analyse, statisches Gleichgewicht des Mehrkörpermodells, kinematischer Kreis, Radblockieren ohne ABS

Komponenten: `vehicle_model/bicycle_kinematic`, `vehicle_model/bicycle_linear`, `vehicle_model/bicycle_nonlinear`, `vehicle_model/double_track`, `vehicle_model/multibody`

| Testfunktion | Beschreibung |
|---|---|
| `test_linear_model_matches_linear_analysis` | – |
| `test_nonlinear_models_close_to_linear_in_linear_range` | – |
| `test_double_track_roll_and_loads_match_quasi_static` | – |
| `test_multibody_wheel_loads_and_static_equilibrium` | – |
| `test_kinematic_model_drives_kinematic_circle` | – |
| `test_wheel_lock_without_abs_and_abs_keeps_slip` | – |

## Validierung von [vehicle_model/bicycle_linear](components/vehicle_model__bicycle_linear.md)

- Gierverstärkung exakt wie LinearSingleTrackAnalysis (tests/test_vehicle_models.py)

## Validierung von [vehicle_model/double_track](components/vehicle_model__double_track.md)

- Wankgradient und Radlasten innerhalb 2–3 % der quasi-statischen Analyse
