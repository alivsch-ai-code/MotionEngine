"""Versioned plugin registry and component factory.

Registration:
    @component                      # uses KIND, NAME, VERSION of the class
    class WerlingPlanner(TrajectoryPlannerBase): ...

Lookup / creation by spec string:
    "trajectory_planner/werling"            latest version
    "trajectory_planner/werling@1.2.0"      exact version
    "trajectory_planner/werling@^1"         newest 1.x
    "python:path/to/file.py:ClassName"      custom Python node (loader registered by vdsim.runtime)
    "rust:path/to/crate", "cpp:path/to/dir", "matlab:path/to/file.m"   (loaders registered by plugins)

Several versions of the same component can be registered side by side; graphs and
results store the exact version for reproducibility.
"""

from __future__ import annotations

import importlib
from collections import defaultdict

from ..core.logging_setup import get_logger

log = get_logger("plugins")

_COMPONENTS = defaultdict(dict)       # (kind, name) -> {version: class}
_LOADERS = {}                         # prefix -> callable(path, params) -> Component instance
_ALIASES = {}                         # "kind/name" -> "kind/name" (renamed components)

# packages whose import registers built-in components (missing packages are skipped)
BUILTIN_MODULES = [
    "vdsim.planning",
    "vdsim.stabilization",
    "vdsim.world",
    "vdsim.perception",
    "vdsim.prediction",
    "vdsim.behavior",
    "vdsim.runtime",
    "vdsim.matlab",
    "vdsim.ad",
]
_loaded = False


def parse_version(text):
    parts = [int(p) for p in str(text).split(".") if p.isdigit()]
    return tuple(parts + [0] * (3 - len(parts)))[:3]


def version_matches(version, constraint):
    if not constraint or constraint in ("*", "latest"):
        return True
    v = parse_version(version)
    if constraint.startswith("^"):
        c = parse_version(constraint[1:])
        return v[0] == c[0] and v >= c
    if constraint.startswith("~"):
        c = parse_version(constraint[1:])
        return v[:2] == c[:2] and v >= c
    if constraint.startswith(">="):
        return v >= parse_version(constraint[2:])
    return v == parse_version(constraint)


def component(cls=None, *, kind=None, name=None, version=None):
    # Class decorator registering a Component subclass
    def decorator(c):
        k, n, v = kind or c.KIND, name or c.NAME, version or c.VERSION
        c.KIND, c.NAME, c.VERSION = k, n, v
        previous = _COMPONENTS[(k, n)].get(v)
        if previous is not None and previous is not c:
            log.debug("component %s/%s@%s re-registered", k, n, v)
        _COMPONENTS[(k, n)][v] = c
        return c
    return decorator(cls) if cls is not None else decorator


def unregister(kind, name, version=None):
    if version is None:
        _COMPONENTS.pop((kind, name), None)
    else:
        _COMPONENTS[(kind, name)].pop(version, None)


def register_loader(prefix, loader):
    # loader(path_spec: str, params: dict | None) -> Component instance
    _LOADERS[prefix] = loader


def load_builtins():
    global _loaded
    if _loaded:
        return
    _loaded = True
    for module in BUILTIN_MODULES:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError as exc:
            if exc.name and exc.name.startswith(module):
                log.debug("optional package %s not available", module)
            else:
                log.warning("could not import %s: %s", module, exc)
        except Exception as exc:  # a broken plugin must not break the platform
            log.warning("could not import %s: %s", module, exc)


def split_spec(spec):
    # "kind/name@constraint" -> (kind, name, constraint)
    base, _, constraint = spec.partition("@")
    base = _ALIASES.get(base, base)
    kind, _, name = base.partition("/")
    if not name:
        raise ValueError(f"component spec '{spec}' must look like 'kind/name[@version]'")
    return kind, name, constraint


def get_component(spec_or_kind, name=None, version=None):
    load_builtins()
    if name is None:
        kind, name, version = split_spec(spec_or_kind)
    else:
        kind = spec_or_kind
    versions = _COMPONENTS.get((kind, name))
    if not versions:
        known = sorted(n for (k, n) in _COMPONENTS if k == kind)
        raise KeyError(f"no component '{kind}/{name}', available: {known}")
    matching = [v for v in versions if version_matches(v, version)]
    if not matching:
        raise KeyError(f"no version of '{kind}/{name}' matches '{version}', available: {sorted(versions)}")
    return versions[max(matching, key=parse_version)]


def create_component(spec, params=None, **overrides):
    # Instantiate a component from a spec string (native or custom node)
    load_builtins()
    prefix, sep, rest = spec.partition(":")
    if sep and prefix in _LOADERS and "/" not in prefix:
        return _LOADERS[prefix](rest, params)
    cls = get_component(spec)
    return cls(params, **overrides)


def available_components(kind=None):
    # list of describe() dicts, newest version first per component
    load_builtins()
    out = []
    for (k, n), versions in sorted(_COMPONENTS.items()):
        if kind and k != kind:
            continue
        for v in sorted(versions, key=parse_version, reverse=True):
            out.append(versions[v].describe())
    return out


def component_kinds():
    load_builtins()
    return sorted({k for k, _ in _COMPONENTS})


def versions_of(kind, name):
    load_builtins()
    return sorted(_COMPONENTS.get((kind, name), {}), key=parse_version)
