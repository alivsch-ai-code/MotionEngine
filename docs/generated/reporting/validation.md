# Auswertung und Berichte – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | Manöver-KPIs, ISO-2631-Wk-Bewertung gegen Normwerte, PDF-Bericht und Laufvergleich |

## Tests, die dieses Paket verwenden

### [tests/test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py)

Importiert: `vdsim.reporting`, `vdsim.reporting.kpi_evaluator`

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

**Zeigt:** Manöver-KPIs, ISO-2631-Wk-Bewertung gegen Normwerte, PDF-Bericht und Laufvergleich

Importiert: `vdsim.reporting`, `vdsim.reporting.kpi_evaluator`, `vdsim.reporting.report_generator`

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
