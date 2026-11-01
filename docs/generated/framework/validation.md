# Komponenten-Framework der AD-Plattform – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

_Keine Validierungsangaben in module.yaml._

## Tests, die dieses Paket verwenden

### [tests/behavior/test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py)

Importiert: `vdsim.framework`, `vdsim.framework.context`, `vdsim.framework.plugins`, `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_following_after_cut_in` | – |
| `test_merge_selects_gap_and_moves_reference` | – |
| `test_stop_at_red_light` | – |
| `test_box_restriction_markings` | – |
| `test_parking_direction_change_only_at_standstill` | – |
| `test_hazard_indicator_postpones_lane_change` | – |

### [tests/matlab/test_matlab_component.py](../../../tests/matlab/test_matlab_component.py)

Importiert: `vdsim.framework.component`, `vdsim.framework.plugins`

| Testfunktion | Beschreibung |
|---|---|
| `test_a5_component` | – |
| `test_loader_spec_vector_ports_and_state` | – |
| `test_unconnected_input_and_bad_params` | – |
| `test_convert_file_and_cli` | – |
| `test_reference_implementation` | – |

### [tests/perception/test_perception_sensor.py](../../../tests/perception/test_perception_sensor.py)

Importiert: `vdsim.framework`, `vdsim.framework.context`, `vdsim.framework.plugins`, `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_reproducible_with_seed` | – |
| `test_range_and_field_of_view` | – |
| `test_occlusion_and_latency` | – |
| `test_ground_truth_passthrough` | – |

### [tests/planning/test_planning_collision.py](../../../tests/planning/test_planning_collision.py)

Importiert: `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_circle_cover_contains_rectangle` | – |
| `test_collision_time_and_safety_margin_ramp` | – |
| `test_dynamic_collision_with_oncoming_vehicle` | – |
| `test_evasion_around_static_obstacle` | – |
| `test_fallback_when_everything_is_blocked` | – |
| `test_reverse_orientation_used_for_collision` | – |

### [tests/planning/test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py)

Importiert: `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_bellman_consistency_lane_change_d_of_t` | – |
| `test_bellman_consistency_following` | – |
| `test_bellman_consistency_slow_arc_mode` | – |
| `test_active_restriction_breaks_consistency_only_while_active` | narrow corridor: the envelope restriction pushes the solution away from the free optimum (3.2); when it becomes inactive the plan jumps once, otherwise the cycles stay exactly consistent |
| `test_cycle_time_independence` | consistent planner: the executed trajectory does not depend on the replanning period (Abb. 3.2) |
| `test_naive_baseline_is_not_consistent` | – |
| `test_output_composition_old_trajectory_until_start` | – |
| `test_reinitialization_from_controller_request_and_prediction` | – |
| `test_stabilization_strategies` | – |
| `test_regime_hysteresis_and_reference_point_switch` | – |

### [tests/planning/test_planning_modes.py](../../../tests/planning/test_planning_modes.py)

Importiert: `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_velocity_keeping_reaches_v_ref` | – |
| `test_lane_change_straight_road` | – |
| `test_lane_change_curved_road` | – |
| `test_following_converges_to_desired_gap` | – |
| `test_following_braking_leader_clamped_at_standstill` | – |
| `test_stopping_exactly_at_stop_line` | – |
| `test_merging_into_gap_center` | – |
| `test_replacement_strategy_selects_conservative_mode` | – |
| `test_slow_driving_uses_arc_mode_and_rear_axle` | – |
| `test_reverse_driving` | – |
| `test_output_fields_and_dkappa_robust` | – |

### [tests/planning/test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py)

Importiert: `vdsim.framework.plugins`, `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_components_registered_and_described` | – |
| `test_constraint_plugins_detect_violations` | – |
| `test_jerk_steering_rate_and_envelope_constraints` | – |
| `test_custom_constraint_and_disable_builtin` | – |
| `test_cost_weights_change_the_selection` | – |
| `test_example_cost_term_and_collision_checker` | – |
| `test_planner_configs` | – |
| `test_debug_snapshot_and_runtime` | – |
| `test_sequential_baseline_runs` | – |

### [tests/prediction/test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py)

Importiert: `vdsim.framework`, `vdsim.framework.context`, `vdsim.framework.plugins`, `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_ca_exact_and_clamped` | – |
| `test_ca_frenet_along_lane` | – |
| `test_cv_and_lane_following` | – |

### [tests/research/test_research_metrics.py](../../../tests/research/test_research_metrics.py)

Importiert: `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_rectangle_distance_and_overlap` | – |
| `test_ttc_thw_and_min_distance` | – |
| `test_consistency_deviation_detects_replanning_jumps` | – |
| `test_evaluate_and_save_load_roundtrip` | – |
| `test_sweep_and_monte_carlo_jobs_are_deterministic` | – |
| `test_batch_statistics_and_sensitivity` | – |

### [tests/runtime/test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py)

Importiert: `vdsim.framework.context`, `vdsim.framework.layers`, `vdsim.framework.plugins`, `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_python_loader_and_hot_reload_with_state_transfer` | – |
| `test_hot_reload_error_keeps_old_instance` | – |
| `test_hot_reload_port_change_revalidates` | – |
| `test_python_example_nodes_have_layer_ports` | – |
| `test_example_chain_closed_loop_and_deterministic` | – |
| `test_sensor_fusion_reduces_noise_and_is_reproducible` | – |
| `test_create_custom_node_python_runs` | – |

### [tests/runtime/test_runtime_executor.py](../../../tests/runtime/test_runtime_executor.py)

Importiert: `vdsim.framework.component`, `vdsim.framework.plugins`

| Testfunktion | Beschreibung |
|---|---|
| `test_two_phase_integrator_loop_exact` | – |
| `test_multirate_timing_exact_and_zoh` | – |
| `test_long_run_has_no_drift` | – |
| `test_feedback_port_reads_previous_step` | – |
| `test_determinism_bit_identical` | – |
| `test_breakpoint_single_step_pause_resume` | – |
| `test_step_and_pause_in_realtime_mode` | – |
| `test_stop_condition_request_stop_and_events` | – |
| `test_listeners_probes_and_profiler` | – |
| `test_runtime_type_check_and_node_errors` | – |
| `test_runtime_graph_changes_and_parameters` | – |
| `test_scope_and_vector_blocks` | – |

### [tests/runtime/test_runtime_graph.py](../../../tests/runtime/test_runtime_graph.py)

Importiert: `vdsim.framework.component`, `vdsim.framework.plugins`

| Testfunktion | Beschreibung |
|---|---|
| `test_valid_graph_and_order` | – |
| `test_type_mismatch_is_rejected_and_reported` | – |
| `test_unconnected_input_unknown_port_and_multiple_drivers` | – |
| `test_algebraic_loop_detected` | – |
| `test_loop_through_unit_delay_or_feedback_port_is_allowed` | – |
| `test_self_loop_detected` | – |
| `test_unknown_component_version_and_parameter` | – |
| `test_period_must_be_multiple_of_base_dt` | – |
| `test_editing_api_and_dynamic_ports` | – |
| `test_json_roundtrip_and_contract_format` | – |
| `test_version_pinning_warning` | – |
| `test_validation_report_iterable_for_api` | – |

### [tests/runtime/test_runtime_native.py](../../../tests/runtime/test_runtime_native.py)

Importiert: `vdsim.framework.context`, `vdsim.framework.plugins`, `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_codegen_layouts_match_python_codecs` | – |
| `test_example_headers_are_current` | – |
| `test_scaffold_rejects_layers_without_codec` | – |
| `test_rust_example_build_load_run_matches_python` | codec round trip through the native interface: EgoState + PlannedTrajectory in, ControlCommand out |
| `test_rust_codec_roundtrip_all_types` | – |
| `test_rust_hot_reload_in_graph` | – |
| `test_rust_scaffold_compiles_and_runs` | – |
| `test_cpp_example_build_load_run_matches_python` | – |
| `test_cpp_codec_roundtrip_all_types` | – |
| `test_cpp_scaffold_compiles_and_runs` | – |

### [tests/stabilization/test_stabilization_classic.py](../../../tests/stabilization/test_stabilization_classic.py)

Importiert: `vdsim.framework.plugins`

| Testfunktion | Beschreibung |
|---|---|
| `test_lateral_controllers_follow_trajectory` | – |
| `test_mpc_horizon_and_constraints` | – |
| `test_longitudinal_controllers_in_composite` | – |
| `test_acc_keeps_time_gap` | – |
| `test_classic_components_have_docs` | – |

### [tests/stabilization/test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py)

Importiert: `vdsim.framework.types`

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

### [tests/stabilization/test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py)

Importiert: `vdsim.framework.context`, `vdsim.framework.knowledge`, `vdsim.framework.plugins`, `vdsim.framework.types`

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

### [tests/stabilization/test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py)

Importiert: `vdsim.framework.types`

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

### [tests/world/test_world_actors.py](../../../tests/world/test_world_actors.py)

Importiert: `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_sat` | – |
| `test_traffic_light_cycle` | – |
| `test_density_no_collisions_60s` | – |
| `test_cut_in_trigger_deterministic` | – |
| `test_pedestrian_trigger` | – |
| `test_vehicles_stop_at_red_light` | – |

### [tests/world/test_world_scenarios.py](../../../tests/world/test_world_scenarios.py)

Importiert: `vdsim.framework`, `vdsim.framework.context`, `vdsim.framework.plugins`, `vdsim.framework.types`

| Testfunktion | Beschreibung |
|---|---|
| `test_library_complete` | – |
| `test_scenario_builds_and_renders` | – |
| `test_spec_roundtrip_and_seed` | – |
| `test_engine_collision_offroad_events` | – |
| `test_lateral_impulse_event` | – |
