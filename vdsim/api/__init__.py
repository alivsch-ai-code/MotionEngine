"""Public Python API of the platform (API first: CLI, REST server and GUI use these functions).

    from vdsim import api
    api.list_components("tracking_controller")
    result = api.run("highway_cut_in", stack={"controller": "tracking_controller/werling_bilevel"})
    batch = api.sweep({"scenario": "highway_cut_in"}, {"stack.planner.params.cost.k_jerk": [0.5, 1, 2]})
"""

from __future__ import annotations

from .. import __version__


def info():
    from ..framework.plugins import component_kinds
    return {"name": "vdsim", "version": __version__, "api_version": 1, "component_kinds": component_kinds()}


# ---------------------------------------------------------------------------- components
def list_components(kind=None):
    from ..framework.plugins import available_components
    return available_components(kind)


def describe_component(spec):
    from ..framework.plugins import get_component
    return get_component(spec).describe()


def create_component(spec, params=None):
    from ..framework.plugins import create_component as _create
    return _create(spec, params)


# ---------------------------------------------------------------------------- scenarios and runs
def list_scenarios():
    from ..world import list_ad_scenarios
    return list_ad_scenarios()


def default_stack():
    import copy

    from ..ad.stack import DEFAULT_STACK
    return copy.deepcopy(DEFAULT_STACK)


def build_graph(stack=None):
    from ..ad.stack import build_graph as _build
    return _build(stack)


def run(scenario, stack=None, seed=None, duration=None, scenario_params=None, snapshots=True, progress=None):
    from ..ad import run_scenario
    return run_scenario(scenario, stack=stack, seed=seed, duration=duration, scenario_params=scenario_params,
                        record_snapshots=snapshots, progress=progress)


def run_batch(jobs, workers=0):
    from ..research import run_batch as _batch
    return _batch(jobs, workers)


def sweep(base_job, grid, workers=0):
    from ..research import parameter_sweep
    from ..research import run_batch as _batch
    return _batch(parameter_sweep(base_job, grid), workers)


def monte_carlo(base_job, distributions, n, seed=0, workers=0):
    from ..research import monte_carlo as _mc
    from ..research import run_batch as _batch
    return _batch(_mc(base_job, distributions, n, seed), workers)


def compare(base_job, layer, variants, workers=0):
    from ..research import compare_components
    from ..research import run_batch as _batch
    return _batch(compare_components(base_job, layer, variants), workers)


def benchmark(scenario, stack=None, repeats=3, duration=None):
    from ..research import benchmark as _bench
    return _bench(scenario, stack, repeats, duration)


# ---------------------------------------------------------------------------- graphs
def load_graph(path):
    from ..runtime import Graph
    return Graph.load(path)


def validate_graph(graph_dict):
    from ..runtime import Graph
    graph = Graph.from_dict(graph_dict)
    return [str(issue) for issue in graph.validate()]


# ---------------------------------------------------------------------------- MATLAB
def matlab_analyze(path_or_source):
    from .. import matlab
    return matlab.analyze(path_or_source)


def matlab_convert(path_or_source, target="python"):
    # {"ok", "files": {name: code}, "report"}; `vdsim.matlab.convert` is a module, not a function
    from ..matlab import generate, parse
    src = path_or_source
    mfile = parse(src) if isinstance(src, str) and "\n" in src else src
    code = generate(mfile, target)
    return {"ok": bool(code.ok), "files": dict(code.files), "report": code.report()}


# ---------------------------------------------------------------------------- custom nodes
def create_custom_node(language, name, layer="tracking_controller", dest="custom_nodes"):
    from ..runtime import create_custom_node as _create
    return _create(language, name, layer, dest)


# ---------------------------------------------------------------------------- knowledge
def references():
    # {id: reference dict} of docs/references (the former import of `load_references` did not exist)
    from ..knowledge import ReferenceDB
    return {rid: ref.to_dict() for rid, ref in ReferenceDB().refs.items()}


def knowledge_graph():
    from ..knowledge import build_graph
    return build_graph()


def build_docs(out_dir=None):
    from ..knowledge import generate_docs
    return generate_docs(out_dir=out_dir)
