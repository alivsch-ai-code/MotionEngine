# Fahrzeuganalyse – linear und quasi-statisch – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_vehicle_models.py](../../../tests/test_vehicle_models.py) | Gierverstärkung des linearen Modells gleich der analytischen Lösung; Wankgradient und Radlasten des Zweispurmodells gegen die quasi-statische Analyse |

## Tests, die dieses Paket verwenden

### [tests/stabilization/test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py)

Importiert: `vdsim.analysis`, `vdsim.analysis.linear_analysis`

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

Importiert: `vdsim.analysis`, `vdsim.analysis.linear_analysis`

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

**Zeigt:** Gierverstärkung des linearen Modells gleich der analytischen Lösung; Wankgradient und Radlasten des Zweispurmodells gegen die quasi-statische Analyse

Importiert: `vdsim.analysis`, `vdsim.analysis.linear_analysis`, `vdsim.analysis.quasi_static`

| Testfunktion | Beschreibung |
|---|---|
| `test_linear_model_matches_linear_analysis` | – |
| `test_nonlinear_models_close_to_linear_in_linear_range` | – |
| `test_double_track_roll_and_loads_match_quasi_static` | – |
| `test_multibody_wheel_loads_and_static_equilibrium` | – |
| `test_kinematic_model_drives_kinematic_circle` | – |
| `test_wheel_lock_without_abs_and_abs_keeps_slip` | – |
