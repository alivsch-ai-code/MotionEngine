"""Runtime of the component platform: graph model, executor, debugging, versioning, custom nodes.

    graph        Graph / Node / Connection, validation (German messages), execution order, JSON
    executor     deterministic multi-rate executor (two-phase, feedback ports, ZOH), real-time mode
    debug        breakpoints, probes, profiler
    recorder     time series of ports / component signals, events
    blocks       Simulink-like basic blocks (KIND "node")
    versioning   snapshot store (.history), diff, restore, optional git commit
    python_nodes "python:file.py:Class" loader with hot reload
    native       C ABI nodes ("rust:crate", "cpp:dir") via ctypes, shadow-copy hot reload
    build        cargo / MSVC / g++ build orchestration
    codegen      vdsim_node.h / vdsim_node.rs generated from framework.types
    scaffold     create_custom_node(): project templates for python / rust / cpp
    hot_reload   HotReloader (mtime polling, state transfer via get_state/set_state)

Importing this package registers the blocks and the loaders "python", "rust" and "cpp".
"""

from ..framework.plugins import register_loader
from . import blocks  # noqa: F401  (registers the basic blocks)
from .debug import Breakpoint, BreakHit, NodeStep, Probe, Profiler
from .executor import ExecutionError, Executor, RunResult, RuntimeTypeError
from .graph import (Connection, Graph, GraphError, GraphValidationError, Node, ValidationIssue,
                    ValidationReport)
from .hot_reload import HotReloader, ReloadEvent
from .python_nodes import load_python_node
from .recorder import Event, Recorder
from .versioning import GraphDiff, Version, VersionStore, diff_graphs


def _rust_loader(path, params=None):
    from .native import load_native_node
    return load_native_node("rust", path, params)


def _cpp_loader(path, params=None):
    from .native import load_native_node
    return load_native_node("cpp", path, params)


register_loader("python", load_python_node)
register_loader("rust", _rust_loader)
register_loader("cpp", _cpp_loader)


def create_custom_node(language, name, kind="tracking_controller", dest="custom_nodes", **kw):
    from .scaffold import create_custom_node as _create
    return _create(language, name, kind, dest, **kw)


__all__ = ["Graph", "Node", "Connection", "GraphError", "GraphValidationError", "ValidationIssue",
           "ValidationReport", "Executor", "RunResult", "ExecutionError", "RuntimeTypeError", "Recorder", "Event",
           "Breakpoint", "BreakHit", "NodeStep", "Probe", "Profiler", "HotReloader", "ReloadEvent",
           "VersionStore", "Version", "GraphDiff", "diff_graphs", "load_python_node", "create_custom_node"]
