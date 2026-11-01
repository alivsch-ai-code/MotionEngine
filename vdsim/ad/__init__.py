"""Integration of the automated-driving stack: stack definition, graph assembly, runner, results."""

from .results import ADResult
from .stack import DEFAULT_STACK, LAYERS, build_graph, merge_stack


def run_scenario(*args, **kwargs):
    from .runner import run_scenario as _run
    return _run(*args, **kwargs)


__all__ = ["ADResult", "DEFAULT_STACK", "LAYERS", "build_graph", "merge_stack", "run_scenario"]
