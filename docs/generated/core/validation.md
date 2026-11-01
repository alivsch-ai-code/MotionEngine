# Kern – Konventionen, Parameter, Schnittstellen, Registry – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | JSON-Roundtrip der Fahrzeugkonfiguration und aller Szenarien |

## Tests, die dieses Paket verwenden

### [tests/conftest.py](../../../tests/conftest.py)

Importiert: `vdsim.core.parameters`

### [tests/planning/test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py)

Importiert: `vdsim.core.parameters`

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

### [tests/stabilization/test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py)

Importiert: `vdsim.core.registry`

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

### [tests/test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py)

**Zeigt:** JSON-Roundtrip der Fahrzeugkonfiguration und aller Szenarien

Importiert: `vdsim.core.parameters`

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

Importiert: `vdsim.core.registry`

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

Importiert: `vdsim.core.conventions`, `vdsim.core.registry`

| Testfunktion | Beschreibung |
|---|---|
| `test_linear_model_matches_linear_analysis` | – |
| `test_nonlinear_models_close_to_linear_in_linear_range` | – |
| `test_double_track_roll_and_loads_match_quasi_static` | – |
| `test_multibody_wheel_loads_and_static_equilibrium` | – |
| `test_kinematic_model_drives_kinematic_circle` | – |
| `test_wheel_lock_without_abs_and_abs_keeps_slip` | – |
