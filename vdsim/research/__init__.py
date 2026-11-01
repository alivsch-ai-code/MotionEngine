"""Research mode: KPIs, safety metrics, batch runs, parameter sweeps, Monte Carlo, comparisons, benchmarking."""

from .benchmark import benchmark, format_benchmark
from .experiments import (
                          BatchResult,
                          compare_components,
                          compare_controllers,
                          compare_planners,
                          monte_carlo,
                          parameter_sweep,
                          run_batch,
                          run_job,
)
from .metrics import KPI_INFO, consistency_deviation, cost_analysis, evaluate, kpi_label

__all__ = ["evaluate", "cost_analysis", "consistency_deviation", "KPI_INFO", "kpi_label", "run_batch", "run_job",
           "parameter_sweep", "monte_carlo", "compare_components", "compare_controllers", "compare_planners",
           "BatchResult", "benchmark", "format_benchmark"]
