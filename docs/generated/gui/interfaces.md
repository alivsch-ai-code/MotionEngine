# Desktop-Anwendung (PySide6) – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.gui.ad`

| Name | Art | Beschreibung |
|---|---|---|
| [`main(argv)`](../../../vdsim/gui/ad/__init__.py#L7) | Funktion | – |

### `vdsim.gui.ad.data`

| Name | Art | Beschreibung |
|---|---|---|
| [`Polyline`](../../../vdsim/gui/ad/data.py#L56) | Klasse | arc-length parametrized polyline with a vectorized Frenet projection |
| [`ResultData`](../../../vdsim/gui/ad/data.py#L79) | Klasse | – |
| [`arr(value, dtype)`](../../../vdsim/gui/ad/data.py#L13) | Funktion | – |
| [`rect(x, y, psi, length, width)`](../../../vdsim/gui/ad/data.py#L23) | Funktion | closed outline (5 points) of an oriented rectangle centered at (x, y) |
| [`circle(x, y, r, n)`](../../../vdsim/gui/ad/data.py#L32) | Funktion | – |
| [`join(polylines)`](../../../vdsim/gui/ad/data.py#L37) | Funktion | list of (xs, ys) -> NaN separated arrays for one PlotDataItem (connect="finite") |
| [`object_circles(length, width, n)`](../../../vdsim/gui/ad/data.py#L48) | Funktion | covering circles of a rectangle along its length (offsets from the center, radius) |

### `vdsim.gui.ad.demo`

| Name | Art | Beschreibung |
|---|---|---|
| [`make_demo_result(duration, dt, plan_dt, seed)`](../../../vdsim/gui/ad/demo.py#L56) | Funktion | – |
| [`make_demo_batch(kind, n, seed, save_dir)`](../../../vdsim/gui/ad/demo.py#L259) | Funktion | kind: compare \| sweep \| monte_carlo \| batch. |

### `vdsim.gui.ad.planner_view`

| Name | Art | Beschreibung |
|---|---|---|
| [`InfoBar`](../../../vdsim/gui/ad/planner_view.py#L22) | Klasse | – |
| [`PlannerView`](../../../vdsim/gui/ad/planner_view.py#L70) | Klasse | – |

### `vdsim.gui.ad.research_panel`

| Name | Art | Beschreibung |
|---|---|---|
| [`BatchWorker`](../../../vdsim/gui/ad/research_panel.py#L80) | Klasse | – |
| [`ExperimentForm`](../../../vdsim/gui/ad/research_panel.py#L115) | Klasse | – |
| [`SmallMultiples`](../../../vdsim/gui/ad/research_panel.py#L373) | Klasse | one bar chart (or histogram for many runs) per KPI of a group |
| [`ResearchPanel`](../../../vdsim/gui/ad/research_panel.py#L415) | Klasse | – |
| [`safe_label(text)`](../../../vdsim/gui/ad/research_panel.py#L35) | Funktion | labels double as file names of saved runs (ADResult.save uses with_suffix -> no '.') |
| [`unique_labels(jobs)`](../../../vdsim/gui/ad/research_panel.py#L41) | Funktion | – |
| [`parse_values(text)`](../../../vdsim/gui/ad/research_panel.py#L51) | Funktion | "0.5, 1, 2" \| "0.1:2:5" (linspace start:stop:n) \| words (strings) |
| [`infer_kind(batch)`](../../../vdsim/gui/ad/research_panel.py#L69) | Funktion | – |

### `vdsim.gui.ad.run_overview`

| Name | Art | Beschreibung |
|---|---|---|
| [`RunOverview`](../../../vdsim/gui/ad/run_overview.py#L52) | Klasse | – |
| [`kpi_meta(key)`](../../../vdsim/gui/ad/run_overview.py#L14) | Funktion | (label, unit, group, better) with fallbacks when vdsim.research is not importable |
| [`table(headers, stretch)`](../../../vdsim/gui/ad/run_overview.py#L26) | Funktion | – |
| [`fill(t, rows)`](../../../vdsim/gui/ad/run_overview.py#L37) | Funktion | – |

### `vdsim.gui.ad.style`

| Name | Art | Beschreibung |
|---|---|---|
| [`Placeholder`](../../../vdsim/gui/ad/style.py#L166) | Klasse | stands in for a tab whose module is not (yet) available |
| [`pen(color, width, style, alpha)`](../../../vdsim/gui/ad/style.py#L45) | Funktion | – |
| [`brush(color, alpha)`](../../../vdsim/gui/ad/style.py#L54) | Funktion | – |
| [`cat_color(i)`](../../../vdsim/gui/ad/style.py#L61) | Funktion | fixed categorical order; beyond eight entities fall back to a neutral gray (no generated hues) |
| [`cost_colors(n_bins)`](../../../vdsim/gui/ad/style.py#L66) | Funktion | – |
| [`make_plot(title, ylabel, unit, xlabel, xunit, legend, parent)`](../../../vdsim/gui/ad/style.py#L70) | Funktion | – |
| [`cursor(plot, color)`](../../../vdsim/gui/ad/style.py#L98) | Funktion | – |
| [`sig(result, key)`](../../../vdsim/gui/ad/style.py#L105) | Funktion | signal array or None (missing / not numeric / all NaN) |
| [`fmt(value, digits)`](../../../vdsim/gui/ad/style.py#L119) | Funktion | – |
| [`set_bars(plot, labels, values, colors, horizontal, highlight, width)`](../../../vdsim/gui/ad/style.py#L131) | Funktion | replace the bars of a categorical bar chart; one color per bar (entity) or a single series color |

### `vdsim.gui.ad.timeline`

| Name | Art | Beschreibung |
|---|---|---|
| [`EventSlider`](../../../vdsim/gui/ad/timeline.py#L20) | Klasse | horizontal slider that paints colored event marks below the groove |
| [`Timeline`](../../../vdsim/gui/ad/timeline.py#L49) | Klasse | – |

### `vdsim.gui.ad.topview`

| Name | Art | Beschreibung |
|---|---|---|
| [`CandidateLayer`](../../../vdsim/gui/ad/topview.py#L60) | Klasse | one PlotDataItem per cost bin + invalid groups + selected trajectory, shared by top and Frenet view |
| [`TopView`](../../../vdsim/gui/ad/topview.py#L119) | Klasse | – |
| [`classify_candidates(snap, n_bins)`](../../../vdsim/gui/ad/topview.py#L23) | Funktion | candidate indices per cost bin (valid), invalid groups and the selected index |
| [`candidate_lines(xs, ys, idx)`](../../../vdsim/gui/ad/topview.py#L48) | Funktion | – |

### `vdsim.gui.ad.views`

| Name | Art | Beschreibung |
|---|---|---|
| [`TimeScope`](../../../vdsim/gui/ad/views.py#L36) | Klasse | One plot with one y-axis (one unit), several series, time cursor and optional event marks. |
| [`ScopeGroup`](../../../vdsim/gui/ad/views.py#L73) | Klasse | – |
| [`FrenetView`](../../../vdsim/gui/ad/views.py#L93) | Klasse | – |
| [`CostView`](../../../vdsim/gui/ad/views.py#L176) | Klasse | – |
| [`ConstraintView`](../../../vdsim/gui/ad/views.py#L239) | Klasse | – |
| [`ControllerView`](../../../vdsim/gui/ad/views.py#L316) | Klasse | – |
| [`CommandView`](../../../vdsim/gui/ad/views.py#L432) | Klasse | – |
| [`title_legend(entries)`](../../../vdsim/gui/ad/views.py#L29) | Funktion | compact legend in the title row: colored mark + label in secondary text color (never covers the data) |

### `vdsim.gui.ad.workbench`

| Name | Art | Beschreibung |
|---|---|---|
| [`ParamDialog`](../../../vdsim/gui/ad/workbench.py#L117) | Klasse | pyqtgraph ParameterTree built from describe()["params"]; values() returns the changed values (nested). |
| [`SimWorker`](../../../vdsim/gui/ad/workbench.py#L214) | Klasse | – |
| [`ADWorkbench`](../../../vdsim/gui/ad/workbench.py#L257) | Klasse | – |
| [`load_tab(spec)`](../../../vdsim/gui/ad/workbench.py#L51) | Funktion | "module:Class" -> (widget, title, error message or "") |
| [`default_stack()`](../../../vdsim/gui/ad/workbench.py#L64) | Funktion | – |
| [`components(kind)`](../../../vdsim/gui/ad/workbench.py#L72) | Funktion | – |
| [`list_scenarios()`](../../../vdsim/gui/ad/workbench.py#L80) | Funktion | library scenarios (api.list_scenarios) followed by the scenario types (also valid scenario names) |
| [`scenario_spec(name)`](../../../vdsim/gui/ad/workbench.py#L98) | Funktion | library scenarios by name; scenario types as spec dict (the runner only loads library files by name) |
| [`component_schema(spec)`](../../../vdsim/gui/ad/workbench.py#L108) | Funktion | – |
| [`main(argv)`](../../../vdsim/gui/ad/workbench.py#L655) | Funktion | – |

### `vdsim.gui.app`

| Name | Art | Beschreibung |
|---|---|---|
| [`main()`](../../../vdsim/gui/app.py#L12) | Funktion | – |

### `vdsim.gui.knowledge.browser`

| Name | Art | Beschreibung |
|---|---|---|
| [`KnowledgeBrowser`](../../../vdsim/gui/knowledge/browser.py#L36) | Klasse | – |

### `vdsim.gui.knowledge.graph_view`

| Name | Art | Beschreibung |
|---|---|---|
| [`EdgeItem`](../../../vdsim/gui/knowledge/graph_view.py#L12) | Klasse | – |
| [`NodeItem`](../../../vdsim/gui/knowledge/graph_view.py#L29) | Klasse | – |
| [`GraphView`](../../../vdsim/gui/knowledge/graph_view.py#L61) | Klasse | – |

### `vdsim.gui.main_window`

| Name | Art | Beschreibung |
|---|---|---|
| [`MainWindow`](../../../vdsim/gui/main_window.py#L27) | Klasse | – |

### `vdsim.gui.panels.analysis_panel`

| Name | Art | Beschreibung |
|---|---|---|
| [`AnalysisPanel`](../../../vdsim/gui/panels/analysis_panel.py#L20) | Klasse | – |

### `vdsim.gui.panels.compare_panel`

| Name | Art | Beschreibung |
|---|---|---|
| [`ComparePanel`](../../../vdsim/gui/panels/compare_panel.py#L11) | Klasse | – |

### `vdsim.gui.panels.kpi_panel`

| Name | Art | Beschreibung |
|---|---|---|
| [`KPIPanel`](../../../vdsim/gui/panels/kpi_panel.py#L17) | Klasse | – |

### `vdsim.gui.panels.log_panel`

| Name | Art | Beschreibung |
|---|---|---|
| [`QtLogHandler`](../../../vdsim/gui/panels/log_panel.py#L12) | Klasse | – |
| [`LogPanel`](../../../vdsim/gui/panels/log_panel.py#L22) | Klasse | – |

### `vdsim.gui.panels.scenario_panel`

| Name | Art | Beschreibung |
|---|---|---|
| [`ScenarioPanel`](../../../vdsim/gui/panels/scenario_panel.py#L39) | Klasse | – |

### `vdsim.gui.panels.trajectory_editor`

| Name | Art | Beschreibung |
|---|---|---|
| [`TrajectoryEditorPanel`](../../../vdsim/gui/panels/trajectory_editor.py#L13) | Klasse | – |

### `vdsim.gui.panels.vehicle_panel`

| Name | Art | Beschreibung |
|---|---|---|
| [`VehiclePanel`](../../../vdsim/gui/panels/vehicle_panel.py#L13) | Klasse | – |

### `vdsim.gui.param_tree`

| Name | Art | Beschreibung |
|---|---|---|
| [`config_to_parameter(config)`](../../../vdsim/gui/param_tree.py#L36) | Funktion | – |
| [`parameter_to_config(root, config)`](../../../vdsim/gui/param_tree.py#L45) | Funktion | write the values of the tree back into a (copied) VehicleConfig |

### `vdsim.gui.theme`

| Name | Art | Beschreibung |
|---|---|---|
| [`apply_theme(app)`](../../../vdsim/gui/theme.py#L43) | Funktion | – |
