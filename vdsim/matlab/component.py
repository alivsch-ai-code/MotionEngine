"""MATLAB functions as platform components (``matlab:datei.m`` spec strings).

    comp = load_matlab_component("examples/matlab/kin_tracking_with_orientation_stab.m",
                                 params={"l_v": 1.2, "l_h": 1.5, "k1": 1.0})
    out = comp.step(0.0, {"y1_d": 0.0, ...})            # -> {"delta_dot": ..., "F_l": ...}

Every input of the MATLAB function becomes an input port unless it is fixed through
``params`` (then it is a component parameter). Ports are ``float`` for scalars and
``Vector`` for arrays (column vectors), outputs likewise. ``backend="interpreter"`` executes
the original MATLAB logic, ``backend="python"`` the generated Python code (identical results,
faster); persistent variables are reset in ``reset()`` and carried over by hot reload.
"""

from __future__ import annotations

import re
from dataclasses import make_dataclass
from pathlib import Path

import numpy as np

from ..core.parameters import param
from ..framework.component import Component, Port
from ..framework.knowledge import ComponentDoc
from .analysis import analyze
from .codegen import generate
from .interpreter import Interpreter, to_value
from .parser import parse_file
from .typeinfer import TypeInference

BACKENDS = ("interpreter", "python")


class MatlabComponent(Component):
    """Base class of the dynamically created MATLAB components."""

    KIND, LANGUAGE, CATEGORY = "matlab", "matlab", "MATLAB"
    MFILE = None              # parsed MFile
    FUNCTION = ""             # MATLAB function name
    BACKEND = "interpreter"
    ARG_ORDER = ()            # MATLAB parameter order
    INPUT_TYPES = {}

    def __init__(self, params=None, **overrides):
        super().__init__(params, **overrides)
        self._make_backend()

    def _make_backend(self):
        self._log = []
        if self.BACKEND == "interpreter":
            self._interp = Interpreter(self.MFILE, output=self._log.append)
            n = len(self.MFILE.function(self.FUNCTION).outputs)
            self._fn = lambda *a: self._interp.call(self.FUNCTION, *a, nargout=n)
        else:
            from .verify import load_python
            code = generate(self.MFILE, "python", function=self.FUNCTION, input_types=self.INPUT_TYPES)
            if not code.ok:
                raise ValueError("MATLAB-Funktion nicht nach Python übersetzbar:\n" + code.report())
            self._module = load_python(code)
            fn = getattr(self._module, code.entry)
            self._fn = lambda *a: (lambda r: r if isinstance(r, tuple) else (r,))(fn(*a))

    def reset(self, context):
        super().reset(context)
        if self.BACKEND == "interpreter":
            self._interp.reset()
        elif hasattr(self._module, "reset_state"):
            self._module.reset_state()

    def step(self, t, inputs):
        args = []
        for name in self.ARG_ORDER:
            if name in self.INPUTS:
                v = inputs.get(name)
                if v is None:
                    raise ValueError(f"{self.NAME}: Eingang '{name}' ist nicht verbunden bzw. hat noch keinen Wert")
            else:
                v = getattr(self.params, name)
            if isinstance(v, (list, tuple)) or (isinstance(v, np.ndarray) and v.ndim == 1):
                v = np.asarray(v, dtype=float).reshape(-1, 1)
            args.append(to_value(v) if self.BACKEND == "interpreter" else v)
        result = self._fn(*args)
        out = {}
        for (name, port), value in zip(self.output_ports().items(), result):
            if port.type == "Vector":
                out[name] = np.asarray(value, dtype=float).ravel()
            elif port.type == "bool":
                out[name] = bool(value)
            else:
                out[name] = float(value)
                self.signals[name] = out[name]
        return out

    def get_state(self):
        if self.BACKEND == "interpreter":
            return {"persistent": {k: dict(v) for k, v in self._interp.persistent.items()},
                    "globals": dict(self._interp.globals)}
        st = {k: dict(v.__dict__) for k, v in vars(self._module).items() if k.endswith("_state")
              and hasattr(v, "__dict__") and not callable(v)}
        return {"python_state": st}

    def set_state(self, state):
        if self.BACKEND == "interpreter" and "persistent" in state:
            self._interp.persistent.update({k: dict(v) for k, v in state["persistent"].items()})
            self._interp.globals.update(state.get("globals", {}))
        elif "python_state" in state:
            for k, v in state["python_state"].items():
                if hasattr(self._module, k):
                    getattr(self._module, k).__dict__.update(v)


def _port_type(t):
    if t.is_array:
        return "Vector"
    if t.kind == "bool":
        return "bool"
    return "float"


def _class_name(name):
    return "Matlab_" + re.sub(r"\W", "_", name)


def load_matlab_component(path, function=None, backend="interpreter", params=None, input_types=None, name=None,
                          version="1.0.0"):
    """Load a MATLAB function file as Component instance (see module docstring)."""
    if backend not in BACKENDS:
        raise ValueError(f"unbekanntes Backend '{backend}', erlaubt: {', '.join(BACKENDS)}")
    mfile = parse_file(path)
    if mfile.kind == "script" and not mfile.functions:
        raise ValueError(f"{path}: Skripte ohne Funktion können nicht als Komponente geladen werden "
                         f"(bitte eine Funktion mit Ein- und Ausgängen definieren)")
    func = mfile.function(function)
    params = dict(params or {})
    unknown = [k for k in params if k not in func.params]
    if unknown:
        raise ValueError(f"Parameter {unknown} sind keine Eingänge von {func.name}({', '.join(func.params)})")
    ft = TypeInference(mfile, input_types).infer_entry(func)
    inputs = {p: Port(_port_type(t), f"MATLAB-Eingang {p}") for p, t in zip(func.params, ft.inputs)
              if p not in params and p != "~"}
    outputs = {o: Port(_port_type(t if t.kind not in ("unknown", "none") else ft.outputs[0]), f"MATLAB-Ausgang {o}")
               for o, t in zip(func.outputs, ft.outputs)}
    fields = []
    for k, v in params.items():
        default = float(v) if np.isscalar(v) else list(np.asarray(v, dtype=float).ravel())
        fields.append((k, type(default), param(default, "", k)))
    p_cls = make_dataclass(f"{_class_name(func.name)}Params", fields)
    analysis = analyze(mfile, input_types)
    fa = analysis.function(func.name)
    lines = [l for l in func.doc.split("\n")] if func.doc else []
    summary = lines[0].strip() if lines else f"MATLAB-Funktion {func.name}"
    doc = ComponentDoc(
        summary=summary,
        purpose=f"Import der MATLAB-Funktion {func.name} aus {Path(path).name}; die originale Regellogik wird "
                f"{'interpretiert' if backend == 'interpreter' else 'als generierter Python-Code ausgeführt'}.",
        theory="\n".join(lines[1:]).strip(),
        equations=sorted({e["equation"] for e in fa.equations}),
        assumptions=["MATLAB-Semantik (1-basiert, Spaltenvektoren, Kopiersemantik) nach vdsim.matlab"],
        limitations=["unterstützter MATLAB-Umfang siehe vdsim/matlab/docs/theory.md"],
        validation=["tests/matlab/test_matlab_component.py"],
        concepts=["matlab_import", "matlab_interpreter"],
        expert=f"Regelungsstruktur: {fa.control.get('structure', '-')}")
    cls = type(_class_name(func.name), (MatlabComponent,), {
        "NAME": name or func.name, "VERSION": version, "LABEL": func.name, "INPUTS": inputs, "OUTPUTS": outputs,
        "PARAMS": p_cls, "MFILE": mfile, "FUNCTION": func.name, "BACKEND": backend,
        "ARG_ORDER": tuple(func.params), "INPUT_TYPES": dict(input_types or {}), "DOC": doc,
        "SOURCE_PATH": str(path), "ANALYSIS": analysis, "__module__": __name__})
    return cls(params)


def matlab_loader(spec, params=None):
    """Loader for 'matlab:pfad/datei.m[:funktion]' (registered in vdsim.matlab)."""
    m = re.match(r"^(.*?\.m)(?::(\w+))?$", spec.strip())
    if not m:
        raise ValueError(f"ungültige MATLAB-Spezifikation '{spec}' (erwartet: datei.m[:funktion])")
    params = dict(params or {})
    backend = params.pop("backend", "interpreter")
    function = params.pop("function", None) or m.group(2)
    input_types = params.pop("input_types", None)
    return load_matlab_component(m.group(1), function=function, backend=backend, params=params,
                                 input_types=input_types)
