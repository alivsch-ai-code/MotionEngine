# Regler, Fahrerassistenz und Fahrwerksregelsysteme – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | Bahnfolge im Doppelspurwechsel, keine stationäre Ablage von Stanley, ACC-Zeitlücke 1,8 s, AEB ohne Kollision, LKA verhindert Spurverlassen, Wirkung von TV, Wankstabilisierung, Hinterachslenkung und ESP, Rückkanal-Schätzung des Aktuatorfehlers |
| [tests/test_vehicle_models.py](../../../tests/test_vehicle_models.py) | ABS hält den Schlupf, ohne ABS blockieren die Räder |

## Tests, die dieses Paket verwenden

### [tests/knowledge/test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py)

Komponenten: `chassis_system/esp`, `lateral_controller/stanley`, `longitudinal_controller/acc`

| Testfunktion | Beschreibung |
|---|---|
| `test_collects_whole_repository` | – |
| `test_legacy_and_framework_components` | – |
| `test_traces_from_code_and_module_yaml` | – |
| `test_handwritten_docs_complete` | – |
| `test_tests_examples_and_configs_linked` | – |
| `test_tolerant_against_broken_files` | – |

### [tests/stabilization/test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py)

Importiert: `vdsim.controllers.esp_controller`

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

### [tests/test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py)

**Zeigt:** Bahnfolge im Doppelspurwechsel, keine stationäre Ablage von Stanley, ACC-Zeitlücke 1,8 s, AEB ohne Kollision, LKA verhindert Spurverlassen, Wirkung von TV, Wankstabilisierung, Hinterachslenkung und ESP, Rückkanal-Schätzung des Aktuatorfehlers

Komponenten: `chassis_system/active_roll`, `chassis_system/esp`, `chassis_system/rear_steering`, `chassis_system/torque_vectoring`, `lateral_controller/curvature_feedforward`, `lateral_controller/lane_keeping`, `longitudinal_controller/acc`, `longitudinal_controller/aeb`, `longitudinal_controller/speed_pi`

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

Komponenten: `lateral_controller/mpc`

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

**Zeigt:** ABS hält den Schlupf, ohne ABS blockieren die Räder

Komponenten: `chassis_system/abs`

| Testfunktion | Beschreibung |
|---|---|
| `test_linear_model_matches_linear_analysis` | – |
| `test_nonlinear_models_close_to_linear_in_linear_range` | – |
| `test_double_track_roll_and_loads_match_quasi_static` | – |
| `test_multibody_wheel_loads_and_static_equilibrium` | – |
| `test_kinematic_model_drives_kinematic_circle` | – |
| `test_wheel_lock_without_abs_and_abs_keeps_slip` | – |
