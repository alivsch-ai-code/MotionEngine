# Desktop-Anwendung (PySide6)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.gui` · Quellcode: [vdsim/gui/](../../../vdsim/gui) · Paketdoku: [vdsim/gui/docs/](../../../vdsim/gui/docs)

## Übersicht

**Hauptfenster mit andockbaren Panels für Szenario, Fahrzeugparameter, Live-Ansicht, Analyse, Kennwerte, Laufvergleich, Trajektorien-Editor und Protokoll.**

Die GUI macht die Plattform ohne Programmierung nutzbar: Szenario aus der Bibliothek laden, Fahrzeug
parametrieren, simulieren und live beobachten, Kennwerte bewerten, Läufe vergleichen und Berichte
erzeugen. Unterpakete anderer Teams (vdsim.gui.ad: AD-Workbench) und der Wissensbrowser
(vdsim.gui.knowledge) sind eigenständige Widgets, die in das Hauptfenster eingebettet werden können.

Paket-Docstring:

```text
PySide6 desktop application (GUI layer).
```

| Kennzahl | Anzahl |
|---|---|
| Module | 28 |
| Komponenten | 0 |
| Verfahren/Konzepte | 4 |
| @trace-Einträge | 0 |
| Tests | 6 |
| Beispiele | 2 |

## Architektur

- `app.main()`: QApplication, Theme, Hauptfenster.
- `main_window.MainWindow`: Docks (Szenario, Fahrzeug, Protokoll), zentrale Reiter (Live, Signale, 3D,
  Analyse, Kennwerte, Vergleich, Trajektorien-Editor), Werkzeugleiste und Menüs; die Simulation läuft
  schrittweise im GUI-Takt (30 ms), damit alle Ansichten ohne Threads aktuell bleiben.
- `panels/`: `ScenarioPanel`, `VehiclePanel`, `AnalysisPanel`, `KPIPanel`, `ComparePanel`,
  `TrajectoryEditorPanel`, `LogPanel`.
- `param_tree.py`: Parameterbäume (pyqtgraph) automatisch aus den Parameter-Datenklassen (Bezeichnung, Einheit, Grenzen).
- `theme.py`: dunkles Theme (Farben, QSS, pyqtgraph-Optionen); auch vom Wissensbrowser verwendet.
- `knowledge/`: Wissensbrowser `KnowledgeBrowser` (siehe Paket knowledge).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.gui`](../../../vdsim/gui/__init__.py) | 2 | – | PySide6 desktop application (GUI layer). |
| [`vdsim.gui.ad`](../../../vdsim/gui/ad/__init__.py) | 25 | – | AD workbench GUI: planner/controller visualization with interactive timeline, research dashboard. |
| [`vdsim.gui.ad.__main__`](../../../vdsim/gui/ad/__main__.py) | 6 | – | – |
| [`vdsim.gui.ad.data`](../../../vdsim/gui/ad/data.py) | 203 | Polyline, ResultData | Tolerant access to an ADResult for the views: time lookup, snapshots, objects, names, geometry. |
| [`vdsim.gui.ad.demo`](../../../vdsim/gui/ad/demo.py) | 329 | – | Synthetic ADResult / BatchResult data so the workbench can be developed and tested without the runner. |
| [`vdsim.gui.ad.planner_view`](../../../vdsim/gui/ad/planner_view.py) | 193 | InfoBar, PlannerView | PlannerView: central visualization of planner and controller with an interactive timeline. |
| [`vdsim.gui.ad.research_panel`](../../../vdsim/gui/ad/research_panel.py) | 1018 | BatchWorker, ExperimentForm, SmallMultiples, ResearchPanel | ResearchPanel: research mode of the workbench. |
| [`vdsim.gui.ad.run_overview`](../../../vdsim/gui/ad/run_overview.py) | 130 | RunOverview | RunOverview: KPIs, events, runtime profile and provenance of a single ADResult. |
| [`vdsim.gui.ad.style`](../../../vdsim/gui/ad/style.py) | 175 | Placeholder | Plot conventions of the AD workbench (data-viz rules) and small pyqtgraph helpers. |
| [`vdsim.gui.ad.timeline`](../../../vdsim/gui/ad/timeline.py) | 213 | EventSlider, Timeline | Interactive timeline: slider over the simulation time with event marks, play/pause, speed, single step, jump to the previous/next event. |
| [`vdsim.gui.ad.topview`](../../../vdsim/gui/ad/topview.py) | 466 | CandidateLayer, TopView | Bird's-eye view of a planning cycle: lanes, reference path, cost-colored candidates, selected trajectory, collision circles, objects with faded predicted outlines, vehicle envelope, ego pose, desired position, MPC horizon, stop lines, traffic lights, parking spaces. |
| [`vdsim.gui.ad.views`](../../../vdsim/gui/ad/views.py) | 447 | TimeScope, ScopeGroup, FrenetView, CostView, ConstraintView, ControllerView | Analysis views of the planner view: Frenet view, cost evaluation, restriction violations, controller states and command scopes. |
| [`vdsim.gui.ad.workbench`](../../../vdsim/gui/ad/workbench.py) | 674 | ParamDialog, _Cancelled, SimWorker, ADWorkbench | ADWorkbench: main window of the automated-driving development and simulation platform. |
| [`vdsim.gui.app`](../../../vdsim/gui/app.py) | 20 | – | Entry point of the desktop application. |
| [`vdsim.gui.knowledge`](../../../vdsim/gui/knowledge/__init__.py) | 10 | – | Knowledge browser (GUI of vdsim.knowledge): embeddable widget KnowledgeBrowser(QWidget). |
| [`vdsim.gui.knowledge.browser`](../../../vdsim/gui/knowledge/browser.py) | 481 | KnowledgeBrowser | Knowledge browser widget: navigation tree, documents with rendered formulas, expert mode, knowledge graph, traceability table, sources (search, create, link) and full-text search. |
| [`vdsim.gui.knowledge.graph_view`](../../../vdsim/gui/knowledge/graph_view.py) | 105 | EdgeItem, NodeItem, GraphView | Interactive knowledge-graph view (QGraphicsView): force layout, movable nodes, zoom, click signals. |
| [`vdsim.gui.main_window`](../../../vdsim/gui/main_window.py) | 429 | MainWindow | Main window: dockable setup panels, live/analysis tabs, toolbar and menus; runs the simulation step by step in the GUI loop so all views update in real time. |
| [`vdsim.gui.panels`](../../../vdsim/gui/panels/__init__.py) | 2 | – | GUI panels (dockable / tabbed widgets). |
| [`vdsim.gui.panels.analysis_panel`](../../../vdsim/gui/panels/analysis_panel.py) | 106 | AnalysisPanel | Analysis tab: matplotlib engineering plots (overview, tires, Pacejka curves, GGV, Bode, quasi-static, heatmaps, energy) for the last run and the current vehicle configuration. |
| [`vdsim.gui.panels.compare_panel`](../../../vdsim/gui/panels/compare_panel.py) | 91 | ComparePanel | Run comparison: keeps the finished runs, KPI comparison table and comparison plot. |
| [`vdsim.gui.panels.kpi_panel`](../../../vdsim/gui/panels/kpi_panel.py) | 96 | KPIPanel | KPI dashboard: headline tiles, full KPI table with ratings, vehicle characteristics from the analyses. |
| [`vdsim.gui.panels.log_panel`](../../../vdsim/gui/panels/log_panel.py) | 34 | _Emitter, QtLogHandler, LogPanel | Log panel: shows the vdsim log messages inside the GUI. |
| [`vdsim.gui.panels.scenario_panel`](../../../vdsim/gui/panels/scenario_panel.py) | 328 | ScenarioPanel | Scenario dashboard: maneuver, model, controllers, actuator latency, environment, simulation settings. |
| [`vdsim.gui.panels.trajectory_editor`](../../../vdsim/gui/panels/trajectory_editor.py) | 224 | TrajectoryEditorPanel | Interactive track editor: draggable waypoints (double-click a segment to insert one), waypoint table with speed and corner radius, generated path preview with speed profile, friction map (mu patches). |
| [`vdsim.gui.panels.vehicle_panel`](../../../vdsim/gui/panels/vehicle_panel.py) | 85 | VehiclePanel | Vehicle parameter editor: preset selection, parameter tree (vehicle, tires, chassis, powertrain, brakes, control systems), JSON import/export. |
| [`vdsim.gui.param_tree`](../../../vdsim/gui/param_tree.py) | 61 | – | Builds pyqtgraph parameter trees from the parameter dataclasses (labels, units, limits) and back. |
| [`vdsim.gui.theme`](../../../vdsim/gui/theme.py) | 56 | – | Dark engineering theme for the Qt application and pyqtgraph. |

### Abhängigkeiten

- nutzt: [ad](../ad/index.md), [analysis](../analysis/index.md), [api](../api/index.md), [core](../core/index.md), [framework](../framework/index.md), [knowledge](../knowledge/index.md), [reporting](../reporting/index.md), [research](../research/index.md), [simulation](../simulation/index.md), [trajectory](../trajectory/index.md), [vehicle_models](../vehicle_models/index.md), [visualization](../visualization/index.md), [world](../world/index.md)
- genutzt von: [knowledge](../knowledge/index.md)
- externe Bibliotheken: `PySide6`, `__future__`, `copy`, `html`, `importlib`, `inspect`, `json`, `logging`, `math`, `matplotlib`, `numpy`, `pathlib`, `pyqtgraph`, `re`, `sys`, `tempfile`, `time`, `traceback`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Simulation schrittweise im GUI-Takt statt in einem Thread | keine Synchronisation zwischen Simulator und Ansichten nötig; „Maximal“ rechnet trotzdem so schnell wie möglich | – |
| Parametermasken aus Metadaten der Datenklassen | neue Parameter erscheinen ohne GUI-Änderung | – |
| Dunkles Theme zentral in theme.py | einheitliches Erscheinungsbild aller Unterpakete | – |

## Implementierung

- Docklayout wird gespeichert und lässt sich zurücksetzen.
- matplotlib wird im Analyse-Panel auf das QtAgg-Backend umgestellt (deshalb analysiert das Wissenssystem GUI-Module nur statisch).

### Verfahren und Konzepte

- [Zeitliche Konsistenz (Bellman-Prinzip)](../planning/theory.md#bellman_principle)
- [Frenet frame](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Vollfaktorieller Versuchsplan](../research/theory.md#full_factorial_design)
- [Monte-Carlo-Simulation und Sensitivität](../research/theory.md#monte_carlo)

## Erweiterungspunkte

- Neue Panels als QWidget in panels/ und Registrierung im MainWindow (Dock oder Reiter)
- Eingebettete Widgets anderer Pakete (vdsim.gui.ad, vdsim.gui.knowledge.KnowledgeBrowser)

## Unterpakete mit eigener Doku

| Ordner | Titel | Kurzfassung |
|---|---|---|
| [vdsim/gui/ad/docs](../../../vdsim/gui/ad/docs) | AD-Workbench (GUI für automatisierte Fahrfunktionen) | Desktop-Werkbank zur Entwicklung und Analyse automatisierter Fahrfunktionen nach Werling: Planer- und Reglervisualisierung mit interaktiver Zeitleiste, Lauf-Kennwerte und Forschungs-Dashboard. |

## Verwandte Module

[visualization](../visualization/index.md), [reporting](../reporting/index.md), [simulation](../simulation/index.md), [knowledge](../knowledge/index.md)
