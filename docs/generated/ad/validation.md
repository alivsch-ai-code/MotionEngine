# ad – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

_Keine Validierungsangaben in module.yaml._

## Tests, die dieses Paket verwenden

### [tests/gui_ad/test_gui_ad_run.py](../../../tests/gui_ad/test_gui_ad_run.py)

Importiert: `vdsim.ad`, `vdsim.ad.runner`

| Testfunktion | Beschreibung |
|---|---|
| `test_real_run_in_workbench` | – |

### [tests/gui_ad/test_gui_ad_workbench.py](../../../tests/gui_ad/test_gui_ad_workbench.py)

Importiert: `vdsim.ad.results`

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

### [tests/research/test_research_metrics.py](../../../tests/research/test_research_metrics.py)

Importiert: `vdsim.ad.results`

| Testfunktion | Beschreibung |
|---|---|
| `test_rectangle_distance_and_overlap` | – |
| `test_ttc_thw_and_min_distance` | – |
| `test_consistency_deviation_detects_replanning_jumps` | – |
| `test_evaluate_and_save_load_roundtrip` | – |
| `test_sweep_and_monte_carlo_jobs_are_deterministic` | – |
| `test_batch_statistics_and_sensitivity` | – |
