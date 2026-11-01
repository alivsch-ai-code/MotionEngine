"""Traceability and documentation metadata.

Every component can carry a ComponentDoc (why it exists, which problem it solves, theory,
assumptions, limitations, sources). Functions that implement a specific equation or
concept are marked with @trace so that the knowledge graph and the traceability matrix
can link implementation <-> theory <-> literature:

    @trace("werling2011", section="3.4", equation="(3.8)", concept="quintic_polynomial")
    def quintic_coefficients(...): ...

Reference ids refer to the entries in docs/references/*.yaml.
"""

from __future__ import annotations

import functools
from dataclasses import asdict, dataclass, field

TRACES = []          # list of dicts, filled at import time by @trace


@dataclass
class ComponentDoc:
    summary: str = ""                     # one sentence: what the component does
    purpose: str = ""                     # why it exists / which problem it solves
    theory: str = ""                      # short description of the underlying theory (Markdown, $...$ math)
    assumptions: list = field(default_factory=list)
    limitations: list = field(default_factory=list)
    design_decisions: list = field(default_factory=list)
    references: list = field(default_factory=list)       # reference ids (docs/references/*.yaml)
    equations: list = field(default_factory=list)        # e.g. ["werling2011:(4.11)", "werling2011:(4.12)"]
    validation: list = field(default_factory=list)       # how it is verified (tests, comparisons)
    extension_points: list = field(default_factory=list)
    concepts: list = field(default_factory=list)         # concept ids for the knowledge graph
    expert: str = ""                                     # derivations / stability notes (Markdown), expert mode

    def to_dict(self):
        return asdict(self)


def trace(source, section="", equation="", concept="", note=""):
    # Decorator linking a function/class to its conceptual origin
    def decorator(obj):
        entry = {"module": obj.__module__, "qualname": obj.__qualname__, "source": source, "section": section,
                 "equation": equation, "concept": concept, "note": note}
        TRACES.append(entry)
        existing = getattr(obj, "__trace__", [])
        try:
            obj.__trace__ = [*existing, entry]
        except (AttributeError, TypeError):
            pass
        return obj
    return decorator


def traces_for(module_prefix=""):
    return [t for t in TRACES if t["module"].startswith(module_prefix)]


def doc_of(obj):
    # ComponentDoc of a class/instance (empty doc if none is declared)
    doc = getattr(obj, "DOC", None)
    return doc if isinstance(doc, ComponentDoc) else ComponentDoc(summary=(obj.__doc__ or "").strip().split("\n")[0])


def wraps_trace(func):
    # helper for decorators that wrap traced functions
    @functools.wraps(func)
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    inner.__trace__ = getattr(func, "__trace__", [])
    return inner
