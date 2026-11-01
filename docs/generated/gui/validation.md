# Desktop-Anwendung (PySide6) – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | GUI-Durchlauf ohne Bildschirm (offscreen) |
| [tests/gui_ad/test_gui_ad_workbench.py](../../../tests/gui_ad/test_gui_ad_workbench.py) | Workbench mit synthetischem Ergebnis, Zeitleiste, Ereignissprünge, alle Tabs, Thread, Speichern/Laden, Parameterdialog, fehlende Felder |
| [tests/gui_ad/test_gui_ad_research.py](../../../tests/gui_ad/test_gui_ad_research.py) | Forschungs-Dashboard für alle Experimenttypen mit synthetischem BatchResult, Jobs, Export, Laden in die Planer-Ansicht |
| [tests/gui_ad/test_gui_ad_run.py](../../../tests/gui_ad/test_gui_ad_run.py) | echter Lauf über vdsim.ad.run_scenario (übersprungen, solange der Runner fehlt) |

## Tests, die dieses Paket verwenden

### [tests/gui_ad/conftest.py](../../../tests/gui_ad/conftest.py)

Importiert: `vdsim.gui.ad.demo`, `vdsim.gui.theme`

### [tests/gui_ad/test_gui_ad_research.py](../../../tests/gui_ad/test_gui_ad_research.py)

**Zeigt:** Forschungs-Dashboard für alle Experimenttypen mit synthetischem BatchResult, Jobs, Export, Laden in die Planer-Ansicht

Importiert: `vdsim.gui.ad.demo`, `vdsim.gui.ad.research_panel`, `vdsim.gui.ad.workbench`

| Testfunktion | Beschreibung |
|---|---|
| `test_research_panel_synthetic_batch` | – |
| `test_research_panel_benchmark_report` | – |
| `test_build_jobs_for_all_experiments` | – |
| `test_research_result_opens_in_planner_view` | – |
| `test_research_runs_batch_in_thread` | run_batch replaced by a synthetic batch: checks the thread wiring and the progress bar |

### [tests/gui_ad/test_gui_ad_run.py](../../../tests/gui_ad/test_gui_ad_run.py)

**Zeigt:** echter Lauf über vdsim.ad.run_scenario (übersprungen, solange der Runner fehlt)

Importiert: `vdsim.gui.ad.workbench`

| Testfunktion | Beschreibung |
|---|---|
| `test_real_run_in_workbench` | – |

### [tests/gui_ad/test_gui_ad_workbench.py](../../../tests/gui_ad/test_gui_ad_workbench.py)

**Zeigt:** Workbench mit synthetischem Ergebnis, Zeitleiste, Ereignissprünge, alle Tabs, Thread, Speichern/Laden, Parameterdialog, fehlende Felder

Importiert: `vdsim.gui.ad`, `vdsim.gui.ad.planner_view`, `vdsim.gui.ad.workbench`

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

### [tests/knowledge/test_knowledge_gui.py](../../../tests/knowledge/test_knowledge_gui.py)

Importiert: `vdsim.gui.knowledge`, `vdsim.gui.knowledge.browser`

| Testfunktion | Beschreibung |
|---|---|
| `test_browser_smoke` | – |

### [tests/test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py)

**Zeigt:** GUI-Durchlauf ohne Bildschirm (offscreen)

Importiert: `vdsim.gui.main_window`, `vdsim.gui.theme`

| Testfunktion | Beschreibung |
|---|---|
| `test_lane_change_study_regression` | results of the original latency study (run_lane_change.py) must not change |
| `test_gui_smoke` | – |
