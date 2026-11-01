# Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_trajectory.py](../../../tests/test_trajectory.py) | Geometrie aller Manöver, Pylonengassen, Geschwindigkeitsprofil-Grenzen, Projektion auf geschlossenen Strecken, alle Importformate, Fillet-Radius im Editor |

## Tests, die dieses Paket verwenden

### [tests/knowledge/test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py)

Komponenten: `maneuver/iso_double_lane_change`, `trajectory_loader/opendrive`

| Testfunktion | Beschreibung |
|---|---|
| `test_collects_whole_repository` | – |
| `test_legacy_and_framework_components` | – |
| `test_traces_from_code_and_module_yaml` | – |
| `test_handwritten_docs_complete` | – |
| `test_tests_examples_and_configs_linked` | – |
| `test_tolerant_against_broken_files` | – |

### [tests/stabilization/test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py)

Komponenten: `maneuver/iso_double_lane_change`, `maneuver/step_steer`

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

Komponenten: `maneuver/circle`, `maneuver/figure_eight`, `maneuver/highway`, `maneuver/iso_double_lane_change`, `maneuver/lane_change`, `maneuver/sine_with_dwell`, `maneuver/straight`

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

Komponenten: `maneuver/braking`, `maneuver/circle`, `maneuver/iso_double_lane_change`, `maneuver/slalom`, `maneuver/step_steer`, `maneuver/straight`

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

### [tests/test_trajectory.py](../../../tests/test_trajectory.py)

**Zeigt:** Geometrie aller Manöver, Pylonengassen, Geschwindigkeitsprofil-Grenzen, Projektion auf geschlossenen Strecken, alle Importformate, Fillet-Radius im Editor

Importiert: `vdsim.trajectory`, `vdsim.trajectory.speed_profile`, `vdsim.trajectory.trajectory`, `vdsim.trajectory.trajectory_generator`, `vdsim.trajectory.trajectory_loader`, `vdsim.trajectory.waypoint_editor`

Komponenten: `maneuver/city`, `maneuver/iso_double_lane_change`, `maneuver/lane_change`, `maneuver/slalom`

| Testfunktion | Beschreibung |
|---|---|
| `test_all_maneuvers_generate` | – |
| `test_lane_change_geometry` | – |
| `test_iso_dlc_reference_stays_inside_gates` | – |
| `test_path_builder_circle_and_closed_track` | – |
| `test_speed_profile_respects_limits` | – |
| `test_projection_sign_and_closed_track_start` | – |
| `test_importers` | – |
| `test_opendrive_lanes` | – |
| `test_csv_json_roundtrip` | – |
| `test_waypoint_editor_fillet_radius` | – |

### [tests/test_vehicle_models.py](../../../tests/test_vehicle_models.py)

Komponenten: `maneuver/braking`, `maneuver/step_steer`, `maneuver/straight`

| Testfunktion | Beschreibung |
|---|---|
| `test_linear_model_matches_linear_analysis` | – |
| `test_nonlinear_models_close_to_linear_in_linear_range` | – |
| `test_double_track_roll_and_loads_match_quasi_static` | – |
| `test_multibody_wheel_loads_and_static_equilibrium` | – |
| `test_kinematic_model_drives_kinematic_circle` | – |
| `test_wheel_lock_without_abs_and_abs_keeps_slip` | – |
