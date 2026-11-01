"""Custom nodes in Python: spec "python:path/to/file.py:ClassName" (class name optional if unique).

The file contains a Component subclass (typically derived from a layer base class of
vdsim.framework.layers so that it has the same ports as the native components). Each load
executes the source under a unique module name (no bytecode cache), which is what makes
hot reloading reliable: a new class object, a new instance, state via get_state/set_state.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import os
import re
import sys
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path

from ..framework.component import Component, params_from_dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_counter = itertools.count(1)
_modules_by_path = {}          # path -> module name currently loaded


def parse_python_spec(rest):
    # "dir/file.py:Class" / "C:/dir/file.py:Class" / "dir/file.py" -> (path, class name or None)
    m = re.match(r"^(.*?\.py)(?::([A-Za-z_]\w*))?$", rest.strip())
    if not m:
        raise ValueError(f"ungültige Python-Node-Angabe '{rest}' (erwartet 'pfad/datei.py:Klasse')")
    return m.group(1), m.group(2)


def resolve_path(path, roots=()):
    p = Path(path)
    if p.is_absolute():
        if not p.exists():
            raise FileNotFoundError(f"Datei '{p}' nicht gefunden")
        return p.resolve()
    for root in [*roots, Path.cwd(), PROJECT_ROOT]:
        cand = Path(root) / p
        if cand.exists():
            return cand.resolve()
    raise FileNotFoundError(f"Datei '{path}' nicht gefunden (gesucht relativ zu {Path.cwd()} und {PROJECT_ROOT})")


def file_stamp(path):
    st = os.stat(path)
    return st.st_mtime_ns, st.st_size


def load_class(path, class_name=None):
    """Execute the file under a fresh module name and return (class, module)."""
    path = Path(path).resolve()
    source = path.read_text(encoding="utf-8")
    digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    mod_name = f"vdsim_custom_{re.sub(r'[^A-Za-z0-9_]', '_', path.stem)}_{digest}_{next(_counter)}"
    spec = importlib.util.spec_from_loader(mod_name, loader=None, origin=str(path))
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    sys.modules[mod_name] = module           # dataclasses need the module in sys.modules
    added = str(path.parent) not in sys.path
    if added:
        sys.path.insert(0, str(path.parent))
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(mod_name, None)
        raise
    finally:
        if added:
            try:
                sys.path.remove(str(path.parent))
            except ValueError:
                pass
    if class_name:
        cls = getattr(module, class_name, None)
        if cls is None:
            sys.modules.pop(mod_name, None)
            raise AttributeError(f"Klasse '{class_name}' nicht in {path.name} gefunden")
    else:
        candidates = [obj for obj in vars(module).values()
                      if isinstance(obj, type) and issubclass(obj, Component) and obj.__module__ == mod_name]
        if len(candidates) != 1:
            sys.modules.pop(mod_name, None)
            names = ", ".join(c.__name__ for c in candidates) or "keine"
            raise AttributeError(f"{path.name}: Klassenname angeben ('python:{path.name}:Klasse'); "
                                 f"gefundene Komponenten: {names}")
        cls = candidates[0]
    if not (isinstance(cls, type) and issubclass(cls, Component)):
        sys.modules.pop(mod_name, None)
        raise TypeError(f"'{class_name}' in {path.name} ist keine Component-Unterklasse")
    old = _modules_by_path.get((str(path), cls.__name__))
    if old and old != mod_name:
        sys.modules.pop(old, None)
    _modules_by_path[(str(path), cls.__name__)] = mod_name
    return cls, module


def transfer_params(old_params, new_cls):
    # carry parameter values over to a (possibly changed) parameter dataclass
    p_cls = new_cls.PARAMS
    if old_params is None or not is_dataclass(old_params) or p_cls is None:
        return None
    data = asdict(old_params)
    names = {f.name for f in fields(p_cls)}
    return params_from_dict(p_cls, {k: v for k, v in data.items() if k in names})


class PythonSource:
    """Reload information attached to an instance as `_vdsim_source`."""

    kind = "python"

    def __init__(self, path, class_name, stamp=None):
        self.path = Path(path)
        self.class_name = class_name
        self.stamp = stamp or file_stamp(self.path)
        self._failed = None

    def describe(self):
        return f"python:{self.path.as_posix()}:{self.class_name}"

    def changed(self):
        try:
            cur = file_stamp(self.path)
        except OSError:
            return False
        return cur != self.stamp and cur != self._failed

    def mark_failed(self):
        try:
            self._failed = file_stamp(self.path)
        except OSError:
            pass

    def prepare(self):
        return None       # nothing to build

    def instantiate(self, old):
        stamp = file_stamp(self.path)
        cls, _ = load_class(self.path, self.class_name)
        inst = cls(transfer_params(getattr(old, "params", None), cls))
        inst._vdsim_source = PythonSource(self.path, cls.__name__, stamp)
        return inst


def load_python_node(rest, params=None, roots=()):
    """Loader for "python:" specs (registered by vdsim.runtime)."""
    path, class_name = parse_python_spec(rest)
    path = resolve_path(path, roots)
    stamp = file_stamp(path)
    cls, _ = load_class(path, class_name)
    inst = cls(params)
    inst._vdsim_source = PythonSource(path, cls.__name__, stamp)
    return inst
