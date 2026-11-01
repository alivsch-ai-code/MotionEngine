# Trajektorienplanung nach Werling – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/planning/test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py) | Bellman-Konsistenz < 1e-6 (gemessen ~1e-14) für d(t), Folgen und d(s); Unabhängigkeit von der Planungsperiode; naive Variante inkonsistent; Reinitialisierung und Strategien |
| [tests/planning/test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py) | Randbedingungen quintisch/quartisch, Ruckintegral geschlossen = numerisch, Kosten nach Tab. 3.1, absolutes Raster |
| [tests/planning/test_planning_modes.py](../../../tests/planning/test_planning_modes.py) | Spurwechsel gerade und gekrümmt, Folgen auf k0 + kv v, Anhalten exakt an s_stop, Einfädeln, Ablösestrategie, d(s), Rückwärtsfahrt |
| [tests/planning/test_planning_collision.py](../../../tests/planning/test_planning_collision.py) | Kreisüberdeckung, Sicherheitsrampe, dynamische Kollision, Ausweichen, Fallback |
| [tests/planning/test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py) | Restriktions- und Kosten-Plugins, eigene Plugins, Konfigurationen, Debug-Daten, Laufzeit |
| [tests/planning/test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py) | (3.11)–(3.14), Einrast-Warnung, Horizontabschätzung |

## Tests, die dieses Paket verwenden

### [tests/gui_ad/test_gui_ad_workbench.py](../../../tests/gui_ad/test_gui_ad_workbench.py)

Komponenten: `trajectory_planner/werling`

| Testfunktion | Beschreibung |
|---|---|
| `test_workbench_demo_timeline_and_tabs` | – |
| `test_run_overview_event_jump` | – |
| `test_planner_view_tolerates_missing_fields` | – |
| `test_save_and_load_result` | – |
| `test_simulation_thread_progress_failure_cancel` | – |
| `test_demo_scenario_runs_without_runner` | – |
| `test_stack_selection_and_param_dialog` | – |
| `test_tab_registry_placeholder` | – |
| `test_main_entry_point_importable` | – |

### [tests/planning/test_planning_analysis.py](../../../tests/planning/test_planning_analysis.py)

**Zeigt:** (3.11)–(3.14), Einrast-Warnung, Horizontabschätzung

Importiert: `vdsim.planning.analysis`, `vdsim.planning.cost`, `vdsim.planning.polynomials`, `vdsim.planning.sampling`

| Testfunktion | Beschreibung |
|---|---|
| `test_continuous_solution_satisfies_manifold_and_transversality` | – |
| `test_continuous_end_distance_equals_3_14` | remark 2: xi2(0) = xi3(0) = 0, constant reference -> d0 / (1 + k tau^5 / 720) |
| `test_optimal_end_time_fulfills_3_13` | – |
| `test_transversality_sign_change_brackets_optimum` | – |
| `test_lock_in_check_detects_parallel_driving` | – |
| `test_sampling_horizon_estimate` | – |

### [tests/planning/test_planning_collision.py](../../../tests/planning/test_planning_collision.py)

**Zeigt:** Kreisüberdeckung, Sicherheitsrampe, dynamische Kollision, Ausweichen, Fallback

Importiert: `vdsim.planning`, `vdsim.planning.collision`, `vdsim.planning.combination`, `vdsim.planning.kinematics`, `vdsim.planning.planner`, `vdsim.planning.simulation`

| Testfunktion | Beschreibung |
|---|---|
| `test_circle_cover_contains_rectangle` | – |
| `test_collision_time_and_safety_margin_ramp` | – |
| `test_dynamic_collision_with_oncoming_vehicle` | – |
| `test_evasion_around_static_obstacle` | – |
| `test_fallback_when_everything_is_blocked` | – |
| `test_reverse_orientation_used_for_collision` | – |

### [tests/planning/test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py)

**Zeigt:** Bellman-Konsistenz < 1e-6 (gemessen ~1e-14) für d(t), Folgen und d(s); Unabhängigkeit von der Planungsperiode; naive Variante inkonsistent; Reinitialisierung und Strategien

Importiert: `vdsim.planning`, `vdsim.planning.baselines`, `vdsim.planning.planner`, `vdsim.planning.simulation`

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

**Zeigt:** Spurwechsel gerade und gekrümmt, Folgen auf k0 + kv v, Anhalten exakt an s_stop, Einfädeln, Ablösestrategie, d(s), Rückwärtsfahrt

Importiert: `vdsim.planning`, `vdsim.planning.planner`, `vdsim.planning.simulation`

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

**Zeigt:** Restriktions- und Kosten-Plugins, eigene Plugins, Konfigurationen, Debug-Daten, Laufzeit

Importiert: `vdsim.planning`, `vdsim.planning.combination`, `vdsim.planning.config`, `vdsim.planning.constraints`, `vdsim.planning.kinematics`, `vdsim.planning.planner`, `vdsim.planning.simulation`

Komponenten: `collision_checker/circles`, `cost_term/comfort`, `cost_term/jerk`, `trajectory_planner/frenet_naive`, `trajectory_planner/sequential`, `trajectory_planner/werling`

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

**Zeigt:** Randbedingungen quintisch/quartisch, Ruckintegral geschlossen = numerisch, Kosten nach Tab. 3.1, absolutes Raster

Importiert: `vdsim.planning.cost`, `vdsim.planning.lateral`, `vdsim.planning.longitudinal`, `vdsim.planning.polynomials`, `vdsim.planning.sampling`

| Testfunktion | Beschreibung |
|---|---|
| `test_quintic_boundary_conditions_and_matrix_form` | – |
| `test_quartic_boundary_conditions_free_end_position` | – |
| `test_jerk_integral_closed_form_matches_numeric` | – |
| `test_rest_to_rest_jerk_values` | used by the lock-in analysis: quintic 720 d^2 / tau^5, quartic 12 dv^2 / tau^3 |
| `test_continuation_on_target_manifold` | – |
| `test_absolute_time_grid_and_consistency_guard` | – |
| `test_costs_follow_table_3_1` | – |

## Validierung von [trajectory_planner/werling](components/trajectory_planner__werling.md)

- tests/planning/test_planning_consistency.py
- tests/planning/test_planning_modes.py
- tests/planning/test_planning_polynomials.py
