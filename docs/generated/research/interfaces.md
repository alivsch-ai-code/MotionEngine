# Forschungsmodus – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.research.benchmark`

| Name | Art | Beschreibung |
|---|---|---|
| [`benchmark(scenario, stack, repeats, duration, seed)`](../../../vdsim/research/benchmark.py#L10) | Funktion | Runs the scenario `repeats` times and aggregates the executor profile of every node |
| [`format_benchmark(report)`](../../../vdsim/research/benchmark.py#L45) | Funktion | – |

### `vdsim.research.experiments`

| Name | Art | Beschreibung |
|---|---|---|
| [`BatchResult`](../../../vdsim/research/experiments.py#L170) | Klasse | – |
| [`set_path(job, dotted, value)`](../../../vdsim/research/experiments.py#L33) | Funktion | – |
| [`get_path(job, dotted, default)`](../../../vdsim/research/experiments.py#L44) | Funktion | – |
| [`run_job(job)`](../../../vdsim/research/experiments.py#L53) | Funktion | Executes one job; returns a light, picklable record (KPIs, metadata, optional saved path) |
| [`run_batch(jobs, workers, progress)`](../../../vdsim/research/experiments.py#L76) | Funktion | workers = 0 -> sequential in this process; > 0 -> process pool (order of the result list = job order) |
| [`parameter_sweep(base_job, grid, label_fmt)`](../../../vdsim/research/experiments.py#L98) | Funktion | full factorial grid: {"stack.planner.params.cost.k_jerk": [0.1, 1, 10], ...} -> list of jobs |
| [`monte_carlo(base_job, distributions, n, seed, vary_scenario_seed)`](../../../vdsim/research/experiments.py#L133) | Funktion | n jobs with parameters drawn from `distributions` ({path: {"dist": ..., ...}}); reproducible via seed |
| [`compare_components(base_job, layer, variants)`](../../../vdsim/research/experiments.py#L150) | Funktion | one job per component variant of a layer, e.g. |
| [`compare_controllers(base_job, variants)`](../../../vdsim/research/experiments.py#L162) | Funktion | – |
| [`compare_planners(base_job, variants)`](../../../vdsim/research/experiments.py#L166) | Funktion | – |

### `vdsim.research.metrics`

| Name | Art | Beschreibung |
|---|---|---|
| [`rectangle_distance(ca, cb)`](../../../vdsim/research/metrics.py#L94) | Funktion | minimum distance between rectangles (0 if they overlap), arrays (n, 4, 2) |
| [`safety_metrics(result)`](../../../vdsim/research/metrics.py#L127) | Funktion | – |
| [`post_encroachment_time(result, dt)`](../../../vdsim/research/metrics.py#L172) | Funktion | smallest time difference between ego and an object occupying the same location (crossing paths) |
| [`comfort_metrics(result)`](../../../vdsim/research/metrics.py#L208) | Funktion | – |
| [`tracking_metrics(result)`](../../../vdsim/research/metrics.py#L224) | Funktion | – |
| [`planner_metrics(result)`](../../../vdsim/research/metrics.py#L240) | Funktion | – |
| [`consistency_deviation(result, horizon)`](../../../vdsim/research/metrics.py#L264) | Funktion | Bellman check: max position difference between plan k and the remainder of plan k-1 on the overlapping time interval (cycles with re-initialization are excluded) |
| [`cost_analysis(result)`](../../../vdsim/research/metrics.py#L288) | Funktion | average contribution of every cost term of the selected trajectories + time series |
| [`mission_metrics(result)`](../../../vdsim/research/metrics.py#L311) | Funktion | – |
| [`evaluate(result)`](../../../vdsim/research/metrics.py#L326) | Funktion | all KPI groups -> flat dict (stored in result.kpis) |
| [`kpi_label(key)`](../../../vdsim/research/metrics.py#L341) | Funktion | – |
