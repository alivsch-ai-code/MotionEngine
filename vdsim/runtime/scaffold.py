"""Project templates for custom nodes: create_custom_node(language, name, kind, dest).

    create_custom_node("python", "my_controller", "tracking_controller", "custom_nodes")
        -> custom_nodes/my_controller.py               spec "python:custom_nodes/my_controller.py:MyController"
    create_custom_node("rust", "my_controller", "tracking_controller", "custom_nodes")
        -> custom_nodes/my_controller/{Cargo.toml, src/lib.rs, src/vdsim_node.rs}   spec "rust:custom_nodes/my_controller"
    create_custom_node("cpp", "my_controller", "tracking_controller", "custom_nodes")
        -> custom_nodes/my_controller/{my_controller.cpp, vdsim_node.h, CMakeLists.txt}

The generated skeleton has the ports of the chosen layer (vdsim.framework.layers), reads all
inputs typed and writes default values to all outputs, so it builds/loads and runs at once.
kind="node" creates a generic block (u: float -> y: float, y = gain * u).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path

from ..framework import types as T
from ..framework.component import Port
from ..framework.layers import LAYER_BASES
from . import codecs, codegen

TEMPLATES = Path(__file__).resolve().parent / "templates"
LANGUAGES = ("python", "rust", "cpp")


@dataclass
class ScaffoldResult:
    language: str
    path: Path               # python file or project folder
    spec: str                # component spec for the graph
    files: list = field(default_factory=list)
    class_name: str = ""

    def __fspath__(self):
        return str(self.path)


def _camel(name):
    return "".join(p.capitalize() for p in re.split(r"[_\-\s]+", name) if p)


def layer_ports(kind):
    if kind == "node":
        return {"u": Port("float", "Eingang")}, {"y": Port("float", "Ausgang")}, True
    base = LAYER_BASES.get(kind)
    if base is None:
        raise ValueError(f"unbekannte Ebene '{kind}' (verfügbar: node, {', '.join(LAYER_BASES)})")
    return base.input_ports(), base.output_ports(), base.DIRECT_FEEDTHROUGH


def node_info(name, kind, label, ins, outs, ft):
    return {"name": name, "kind": kind, "version": "0.1.0", "label": label,
            "category": getattr(LAYER_BASES.get(kind), "CATEGORY", "Custom Nodes"), "direct_feedthrough": ft,
            "period": None,
            "inputs": [{"name": n, "type": p.type, "optional": p.optional, "feedback": p.feedback}
                       for n, p in ins.items()],
            "outputs": [{"name": n, "type": p.type} for n, p in outs.items()],
            "params": [{"name": "gain", "default": 1.0, "label": "Verstärkung", "unit": ""}]}


def _render(template, **values):
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        raise RuntimeError(f"Template {template}: nicht ersetzt: {left}")
    return text


# ---------------------------------------------------------------------------- python
def _py_default(type_name):
    py = T.TYPES.get(type_name)
    if type_name == "float":
        return "0.0"
    if type_name == "bool":
        return "False"
    if type_name == "Vector":
        return "np.zeros(0)"
    if py is None or py is object or not is_dataclass(py):
        return "None"
    names = {f.name for f in fields(py)}
    if "t" in names:
        return f"{type_name}(t=t)"
    if "t0" in names:
        return f"{type_name}(t0=t)"
    return f"{type_name}()"


def _python(name, kind, label, dest):
    ins, outs, ft = layer_ports(kind)
    cls = _camel(name)
    types = sorted({p.type for p in outs.values() if p.type in T.TYPES and is_dataclass(T.TYPES[p.type])})
    imports = []
    if kind == "node":
        base = "Component"
        imports.append("from vdsim.framework.component import Component, Port")
        attrs = '    KIND = "node"\n    CATEGORY = "Custom Nodes"\n    INPUTS = {"u": Port("float")}\n' \
                '    OUTPUTS = {"y": Port("float")}\n'
    else:
        base = LAYER_BASES[kind].__name__
        imports.append(f"from vdsim.framework.layers import {base}")
        attrs = ""
    if types:
        imports.append(f"from vdsim.framework.types import {', '.join(types)}")
    if any(p.type == "Vector" for p in outs.values()):
        imports.insert(0, "import numpy as np")
    reads = "\n".join(f"        {n} = inputs.get(\"{n}\")      # {p.type}{' (Rückführung, Vorschritt)' if p.feedback else ''}"
                      for n, p in ins.items())
    if kind == "node":
        body = ("    def step(self, t, inputs):\n        u = inputs.get(\"u\")\n        self.steps += 1\n"
                "        return {\"y\": None if u is None else self.params.gain * u}\n")
    elif ft:
        outs_txt = ", ".join(f"\"{n}\": {_py_default(p.type)}" for n, p in outs.items())
        body = (f"    def step(self, t, inputs):\n{reads}\n        self.steps += 1\n"
                f"        # TODO: Algorithmus\n        return {{{outs_txt}}}\n")
    else:
        outs_txt = ", ".join(f"\"{n}\": {_py_default(p.type)}" for n, p in outs.items())
        body = (f"    def output(self, t):\n        # outputs from the internal state only (no direct feedthrough)\n"
                f"        return {{{outs_txt}}}\n\n"
                f"    def update(self, t, inputs, dt):\n{reads}\n        self.steps += 1\n"
                f"        # TODO: Zustand um dt fortschreiben\n")
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{name}.py"
    text = _render("python/node.py.tmpl", LABEL=label, KIND=kind, FILE=path.as_posix(), CLASS=cls, BASE=base,
                   NAME=name, IMPORTS="\n".join(imports), CLASS_ATTRS=attrs, BODY=body.rstrip() + "\n")
    path.write_text(text, encoding="utf-8")
    return ScaffoldResult("python", path, f"python:{path.as_posix()}:{cls}", [path], cls)


# ---------------------------------------------------------------------------- native
_CPP_T = {"float": "double", "bool": "bool", "Vector": "vdsim::Vector"}
_RS_T = {"float": "f64", "bool": "bool", "Vector": "Vec<f64>"}
_HAS_T = {"EgoState", "ControlCommand", "ControllerStatus", "ActuatorCommand"}


def _check_native_types(ins, outs, kind):
    bad = sorted({p.type for p in list(ins.values()) + list(outs.values()) if not codecs.has_codec(p.type)})
    if bad:
        raise ValueError(f"Ebene '{kind}' nutzt Datentypen ohne flachen Codec ({', '.join(bad)}); native Nodes "
                         f"(Rust/C++) sind dafür noch nicht möglich. Unterstützt: {', '.join(codecs.CODEC_TYPES)}")


def _cpp_body(kind, ins, outs, ft):
    lines = []
    reads = [f"    const {_CPP_T.get(p.type, 'vdsim::' + p.type)} {n} = in.get<{_CPP_T.get(p.type, 'vdsim::' + p.type)}>"
             f"(IN_{n.upper()});" for n, p in ins.items()]
    unused = [f"    (void){n};" for n in ins]
    sets = []
    for n, p in outs.items():
        if kind == "node":
            sets.append(f"    out.set(OUT_{n.upper()}, gain_ * u);")
            continue
        ctype = _CPP_T.get(p.type, "vdsim::" + p.type)
        sets.append(f"    {ctype} {n}{'{}' if p.type in _CPP_T else ''};")
        if p.type in _HAS_T:
            sets.append(f"    {n}.t = t;")
        sets.append(f"    out.set(OUT_{n.upper()}, {n});")
    t_used = kind != "node" and any(p.type in _HAS_T for p in outs.values())
    if ft:
        lines.append("  void step(double t, const vdsim::Inputs& in, vdsim::Outputs& out) override {")
        lines += reads + ([] if kind == "node" else unused) + ([] if t_used else ["    (void)t;"])
        lines.append("    ++steps_;")
        lines.append("    // TODO: Algorithmus")
        lines += sets
        lines.append("  }")
    else:
        lines.append("  void output(double t, vdsim::Outputs& out) override {")
        lines.append("    // outputs from the internal state only (no direct feedthrough)")
        if not t_used:
            lines.append("    (void)t;")
        lines += sets
        lines.append("  }")
        lines.append("")
        lines.append("  void update(double t, const vdsim::Inputs& in, double dt) override {")
        lines += reads + unused + ["    (void)t;", "    (void)dt;", "    ++steps_;", "    // TODO: Zustand um dt fortschreiben"]
        lines.append("  }")
    return "\n".join(lines)


def _rust_body(kind, ins, outs, ft):
    lines = []
    reads = [f"        let {'_' if kind != 'node' else ''}{n}: {_RS_T.get(p.type, p.type)} = "
             f"inputs.get(IN_{n.upper()}).unwrap_or_default();" for n, p in ins.items()]
    sets = []
    for n, p in outs.items():
        if kind == "node":
            sets.append(f"        outputs.set(OUT_{n.upper()}, &(self.gain * u));")
            continue
        rtype = _RS_T.get(p.type, p.type)
        if p.type in _HAS_T:
            sets.append(f"        outputs.set(OUT_{n.upper()}, &{rtype} {{ t, ..Default::default() }});")
        else:
            sets.append(f"        outputs.set(OUT_{n.upper()}, &<{rtype}>::default());")
    t_used = kind != "node" and any(p.type in _HAS_T for p in outs.values())
    tname = "t" if t_used else "_t"
    if ft:
        lines.append(f"    fn step(&mut self, {tname}: f64, inputs: &Inputs, outputs: &mut Outputs) -> Result<(), String> {{")
        lines += reads
        lines.append("        self.steps += 1;")
        lines.append("        // TODO: Algorithmus")
        lines += sets
        lines.append("        Ok(())")
        lines.append("    }")
    else:
        lines.append(f"    fn output(&mut self, {tname}: f64, outputs: &mut Outputs) -> Result<(), String> {{")
        lines.append("        // outputs from the internal state only (no direct feedthrough)")
        lines += sets
        lines.append("        Ok(())")
        lines.append("    }")
        lines.append("")
        lines.append("    fn update(&mut self, _t: f64, inputs: &Inputs, _dt: f64) -> Result<(), String> {")
        lines += reads
        lines.append("        self.steps += 1;")
        lines.append("        // TODO: Zustand um dt fortschreiben")
        lines.append("        Ok(())")
        lines.append("    }")
    return "\n".join(lines)


def _port_consts(lang, ins, outs):
    lines = []
    if lang == "cpp":
        lines.append("// port indices (order of \"inputs\" / \"outputs\" in INFO)")
        if ins:
            lines.append("enum Input : size_t { " + ", ".join(f"IN_{n.upper()} = {i}" for i, n in enumerate(ins)) + " };")
        if outs:
            lines.append("enum Output : size_t { " + ", ".join(f"OUT_{n.upper()} = {i}" for i, n in enumerate(outs))
                         + " };")
    else:
        lines.append("// port indices (order of \"inputs\" / \"outputs\" in INFO)")
        lines += [f"const IN_{n.upper()}: usize = {i};" for i, n in enumerate(ins)]
        lines += [f"const OUT_{n.upper()}: usize = {i};" for i, n in enumerate(outs)]
    return "\n".join(lines)


def _native(language, name, kind, label, dest):
    ins, outs, ft = layer_ports(kind)
    _check_native_types(ins, outs, kind)
    cls = _camel(name)
    info = json.dumps(node_info(name, kind, label, ins, outs, ft), ensure_ascii=False)
    proj = dest / name
    proj.mkdir(parents=True, exist_ok=True)
    files = []
    if language == "rust":
        (proj / "src").mkdir(exist_ok=True)
        files.append(proj / "Cargo.toml")
        files[-1].write_text(_render("rust/Cargo.toml.tmpl", NAME=name, LABEL=label, KIND=kind), encoding="utf-8")
        files.append(proj / "src" / "lib.rs")
        files[-1].write_text(_render("rust/lib.rs.tmpl", LABEL=label, KIND=kind, INFO_JSON=info, CLASS=cls,
                                     PORT_CONSTS=_port_consts("rust", ins, outs),
                                     BODY=_rust_body(kind, ins, outs, ft)), encoding="utf-8")
        files += codegen.write_headers(proj / "src", cpp=False, rust=True)
    else:
        files.append(proj / f"{name}.cpp")
        files[-1].write_text(_render("cpp/node.cpp.tmpl", LABEL=label, KIND=kind, INFO_JSON=info, CLASS=cls,
                                     PORT_CONSTS=_port_consts("cpp", ins, outs),
                                     BODY=_cpp_body(kind, ins, outs, ft)), encoding="utf-8")
        files.append(proj / "CMakeLists.txt")
        files[-1].write_text(_render("cpp/CMakeLists.txt.tmpl", NAME=name), encoding="utf-8")
        files += codegen.write_headers(proj, cpp=True, rust=False)
    return ScaffoldResult(language, proj, f"{language}:{proj.as_posix()}", files, cls)


def create_custom_node(language, name, kind="tracking_controller", dest="custom_nodes", label=None, overwrite=False):
    """Create a runnable custom-node skeleton with the ports of layer `kind`. Returns ScaffoldResult."""
    language = {"c++": "cpp", "py": "python", "rs": "rust"}.get(str(language).lower(), str(language).lower())
    if language not in LANGUAGES:
        raise ValueError(f"unbekannte Sprache '{language}' (python, rust, cpp)")
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        raise ValueError(f"Name '{name}' muss snake_case sein (Kleinbuchstaben, Ziffern, '_')")
    dest = Path(dest)
    target = dest / (f"{name}.py" if language == "python" else name)
    if target.exists() and not overwrite:
        raise FileExistsError(f"{target} existiert bereits (overwrite=True zum Überschreiben)")
    label = label or f"{_camel(name)} ({kind})"
    if language == "python":
        return _python(name, kind, label, dest)
    return _native(language, name, kind, label, dest)
