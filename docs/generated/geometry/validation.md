# Geometrie – Referenzkurven und Frenet-Koordinaten – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

_Keine Validierungsangaben in module.yaml._

## Tests, die dieses Paket verwenden

### [tests/planning/test_planning_collision.py](../../../tests/planning/test_planning_collision.py)

Importiert: `vdsim.geometry`, `vdsim.geometry.reference_line`

| Testfunktion | Beschreibung |
|---|---|
| `test_circle_cover_contains_rectangle` | – |
| `test_collision_time_and_safety_margin_ramp` | – |
| `test_dynamic_collision_with_oncoming_vehicle` | – |
| `test_evasion_around_static_obstacle` | – |
| `test_fallback_when_everything_is_blocked` | – |
| `test_reverse_orientation_used_for_collision` | – |

### [tests/planning/test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py)

Importiert: `vdsim.geometry`, `vdsim.geometry.reference_line`

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

Importiert: `vdsim.geometry`, `vdsim.geometry.reference_line`

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

Importiert: `vdsim.geometry`, `vdsim.geometry.reference_line`

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

### [tests/planning/test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py)

Importiert: `vdsim.geometry.reference_line`

| Testfunktion | Beschreibung |
|---|---|
| `test_quintic_boundary_conditions_and_matrix_form` | – |
| `test_quartic_boundary_conditions_free_end_position` | – |
| `test_jerk_integral_closed_form_matches_numeric` | – |
| `test_rest_to_rest_jerk_values` | used by the lock-in analysis: quintic 720 d^2 / tau^5, quartic 12 dv^2 / tau^3 |
| `test_continuation_on_target_manifold` | – |
| `test_absolute_time_grid_and_consistency_guard` | – |
| `test_costs_follow_table_3_1` | – |

### [tests/runtime/test_runtime_native.py](../../../tests/runtime/test_runtime_native.py)

Importiert: `vdsim.geometry`, `vdsim.geometry.reference_line`

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
