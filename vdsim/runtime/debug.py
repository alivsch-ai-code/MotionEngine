"""Debugging aids of the executor: breakpoints, probes and the per-node runtime profiler.

Wall-clock time is used only for profiling, never in the simulation logic (determinism).
"""

from __future__ import annotations

import inspect
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from ..framework.types import summarize


# ---------------------------------------------------------------------------- breakpoints
class Breakpoint:
    """Pause before a node is computed (or at the start of a step if node is None).

    condition: None (always), callable(inputs) or callable(inputs, t) -> bool.
    For direct-feedthrough nodes the check happens before step(), for nodes without
    direct feedthrough before update() (phase="update") or before output() (phase="output").
    """

    _ids = 0

    def __init__(self, node=None, condition=None, once=False, phase=None, enabled=True, label=""):
        Breakpoint._ids += 1
        self.id = Breakpoint._ids
        self.node = node
        self.condition = condition
        self.once = once
        self.phase = phase
        self.enabled = enabled
        self.label = label
        self.hits = 0
        self._nargs = _arity(condition) if condition is not None else 0

    def matches(self, inputs, t):
        if not self.enabled:
            return False
        if self.condition is None:
            return True
        if self._nargs >= 2:
            return bool(self.condition(inputs, t))
        return bool(self.condition(inputs))

    def __repr__(self):
        return f"Breakpoint(#{self.id}, node={self.node!r}, hits={self.hits})"


def _arity(fn):
    try:
        params = [p for p in inspect.signature(fn).parameters.values()
                  if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        if any(p.kind == p.VAR_POSITIONAL for p in inspect.signature(fn).parameters.values()):
            return 2
        return len(params)
    except (TypeError, ValueError):
        return 1


@dataclass
class BreakHit:
    breakpoint: Breakpoint
    node: str | None
    phase: str
    t: float
    tick: int
    inputs: dict = field(default_factory=dict)

    def __str__(self):
        where = f"Knoten '{self.node}' ({self.phase})" if self.node else "Schrittbeginn"
        return f"Haltepunkt #{self.breakpoint.id} bei t={self.t:g} s: {where}"


@dataclass
class NodeStep:
    # result of Executor.step_node(): which action was executed
    node: str
    phase: str
    t: float
    tick: int
    outputs: dict | None = None
    step_complete: bool = False


# ---------------------------------------------------------------------------- probes
class Probe:
    """Live value of one port ("node.port"), updated whenever the node writes it."""

    def __init__(self, key, history=0):
        self.key = key
        self.value = None
        self.t = None
        self.updates = 0
        self.history = deque(maxlen=history) if history else None

    def push(self, t, value):
        self.value, self.t = value, t
        self.updates += 1
        if self.history is not None:
            self.history.append((t, value))

    @property
    def text(self):
        return summarize(self.value)

    def __repr__(self):
        return f"Probe({self.key}={self.text} @ t={self.t})"


# ---------------------------------------------------------------------------- profiler
class NodeProfile:
    __slots__ = ("calls", "total_ns", "max_ns", "samples")

    def __init__(self, keep=20000):
        self.calls = 0
        self.total_ns = 0
        self.max_ns = 0
        self.samples = deque(maxlen=keep)

    def add(self, ns):
        self.calls += 1
        self.total_ns += ns
        if ns > self.max_ns:
            self.max_ns = ns
        self.samples.append(ns)

    def stats(self):
        if not self.calls:
            return {"calls": 0, "mean_us": 0.0, "p95_us": 0.0, "max_us": 0.0, "total_ms": 0.0}
        p95 = float(np.percentile(np.fromiter(self.samples, dtype=float), 95)) if self.samples else 0.0
        return {"calls": self.calls, "mean_us": self.total_ns / self.calls / 1e3, "p95_us": p95 / 1e3,
                "max_us": self.max_ns / 1e3, "total_ms": self.total_ns / 1e6}


class Profiler:
    """Per-node computation time (all phases of a node within one step are summed)."""

    def __init__(self, enabled=True, keep=20000):
        self.enabled = enabled
        self.keep = keep
        self.clear()

    def clear(self):
        self.nodes = {}
        self.steps = NodeProfile(self.keep)     # wall time of complete base steps (incl. executor overhead)
        self.node_calls_per_step = []

    def node(self, node_id):
        prof = self.nodes.get(node_id)
        if prof is None:
            prof = self.nodes[node_id] = NodeProfile(self.keep)
        return prof

    def report(self):
        # {node: {"calls", "mean_us", "p95_us", "max_us", "total_ms"}}
        return {nid: p.stats() for nid, p in self.nodes.items()}

    def overhead(self):
        # executor overhead per executed node and step (step wall time minus node compute time)
        node_total = sum(p.total_ns for p in self.nodes.values())
        node_calls = sum(p.calls for p in self.nodes.values())
        if not self.steps.calls or not node_calls:
            return {"steps": self.steps.calls, "per_node_us": 0.0, "per_step_us": 0.0}
        over = max(0, self.steps.total_ns - node_total)
        return {"steps": self.steps.calls, "per_step_us": over / self.steps.calls / 1e3,
                "per_node_us": over / node_calls / 1e3, "step_mean_us": self.steps.total_ns / self.steps.calls / 1e3}

    def table(self):
        rows = sorted(self.report().items(), key=lambda kv: -kv[1]["total_ms"])
        lines = [f"{'Knoten':<24}{'Aufrufe':>9}{'Mittel µs':>12}{'p95 µs':>11}{'Max µs':>11}{'Summe ms':>11}"]
        for nid, s in rows:
            lines.append(f"{nid:<24}{s['calls']:>9}{s['mean_us']:>12.2f}{s['p95_us']:>11.2f}{s['max_us']:>11.1f}"
                         f"{s['total_ms']:>11.2f}")
        ov = self.overhead()
        lines.append(f"Executor-Overhead: {ov['per_node_us']:.2f} µs je Knotenaufruf, "
                     f"{ov['per_step_us']:.2f} µs je Schritt ({ov['steps']} Schritte)")
        return "\n".join(lines)
