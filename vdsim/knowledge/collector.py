"""Collects knowledge from code and documentation into a KnowledgeBase.

Sources (all optional, missing or half-finished files only produce warnings):
    - packages and modules (ast): docstrings, classes, functions, imports, decorators,
      leading comments as documentation fallback
    - components: vdsim.framework.plugins.available_components() (versioned components) and
      the classic registry vdsim.core.registry (vehicle_model, tire_model, lateral_controller, ...)
    - ComponentDoc, ports and types, parameter schema (unit, limits, default)
    - @trace entries (vdsim.framework.knowledge.TRACES after importing all packages) plus
      statically parsed @trace decorators of modules that cannot be imported
    - vdsim/<package>/docs/module.yaml and theory.md (sections, concept anchors {#concept-id})
    - tests, examples and configuration files that reference modules or components
    - docs/references/*.yaml (ReferenceDB)

Modules that import Qt / pyqtgraph / OpenGL at top level or switch the matplotlib backend
are analysed statically only (no import side effects in headless runs).
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import inspect
import io
import json
import logging
import re
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .paths import EXTRA_PACKAGES, rel, root_dir
from .references import ReferenceDB, parse_citations

log = logging.getLogger("vdsim.knowledge")

GUI_MODULES = ("PySide6", "PyQt5", "PyQt6", "pyqtgraph", "OpenGL", "tkinter")
SKIP_DIRS = {"__pycache__", "docs", ".pytest_cache", ".git", ".venv", "node_modules", "build", "target"}
MODEL_KINDS = {"vehicle_model", "tire_model", "vehicle_plant"}
COMPONENT_DOC_FIELDS = ("summary", "purpose", "theory", "assumptions", "limitations", "design_decisions",
                        "references", "equations", "validation", "extension_points", "concepts", "expert")
MODULE_YAML_KEYS = ("id", "title", "summary", "purpose", "architecture", "design_decisions", "implementation",
                    "configuration", "examples", "limitations", "validation", "references", "concepts",
                    "related_modules", "extension_points", "components", "traceability", "expert", "stability",
                    "data_flow", "models", "status", "maintainers", "glossary")
# keyword / JSON keys whose string value names a component of the classic registry
KEYWORD_KINDS = {"model": "vehicle_model", "vehicle_model": "vehicle_model", "lateral_controller": "lateral_controller",
                 "longitudinal_controller": "longitudinal_controller", "maneuver": "maneuver",
                 "tire_model": "tire_model", "tires.model": "tire_model", "base": "longitudinal_controller"}
# ports of the classic registry kinds (they are plain Python interfaces, not framework components)
LEGACY_INTERFACES = {
    "vehicle_model": ({"u": "ControlInput", "env": "Environment"}, {"state": "VehicleState"},
                      "vdsim.core.interfaces.VehicleModel"),
    "tire_model": ({"alpha": "float", "kappa": "float", "fz": "float", "mu": "float", "camber": "float"},
                   {"fx": "float", "fy": "float", "mz": "float"}, "vdsim.core.interfaces.TireModel"),
    "lateral_controller": ({"state": "VehicleState", "reference": "Trajectory"}, {"steer": "float"},
                           "vdsim.core.interfaces.LateralController"),
    "longitudinal_controller": ({"state": "VehicleState", "reference": "Trajectory", "env": "Environment"},
                                {"acceleration": "float"}, "vdsim.core.interfaces.LongitudinalController"),
    "chassis_system": ({"state": "VehicleState", "u": "ControlInput"}, {"u": "ControlInput"},
                       "vdsim.core.interfaces.ChassisSystem"),
    "maneuver": ({}, {"trajectory": "Trajectory"}, ""),
    "trajectory_loader": ({"path": "Any"}, {"trajectory": "Trajectory"}, ""),
}
PORT_DESCRIPTIONS = {"steer": "Radlenkwinkel-Anforderung vorne in rad", "acceleration": "Beschleunigungsanforderung in m/s²",
                     "fx": "Längskraft in N", "fy": "Seitenkraft in N", "mz": "Rückstellmoment in N m",
                     "alpha": "Schräglaufwinkel in rad", "kappa": "Längsschlupf (-)", "fz": "Radlast in N",
                     "mu": "Reibwert (-)", "camber": "Sturzwinkel in rad"}
# data types of the classic simulation core (in addition to vdsim.framework.types.TYPES)
LEGACY_TYPES = {
    "VehicleState": ("vdsim.simulation.vehicle_state", "VehicleState", "modellunabhängiger Fahrzeugzustand (klassischer Simulator)"),
    "Trajectory": ("vdsim.trajectory.trajectory", "Trajectory", "Referenzpfad mit Geschwindigkeitsprofil"),
    "Projection": ("vdsim.trajectory.trajectory", "Projection", "Ergebnis der Pfadprojektion"),
    "Environment": ("vdsim.simulation.environment", "Environment", "Reibwertkarte, Fahrbahn, Wind, Verkehr"),
    "SimulationResult": ("vdsim.simulation.results", "SimulationResult", "Zeitreihen und Metadaten eines Laufs"),
    "VehicleConfig": ("vdsim.core.parameters", "VehicleConfig", "vollständiger Fahrzeugparametersatz"),
    "FrenetState": ("vdsim.geometry.reference_line", "FrenetState", "Bahnkoordinaten eines Punktes"),
    "KPI": ("vdsim.reporting.kpi_evaluator", "KPI", "Kennwert mit Einheit und Bewertung"),
}


# ---------------------------------------------------------------------------- data structures
@dataclass
class FunctionInfo:
    name: str
    qualname: str
    module: str
    lineno: int = 0
    doc: str = ""
    args: list = field(default_factory=list)
    decorators: list = field(default_factory=list)
    is_method: bool = False

    @property
    def id(self):
        return f"{self.module}.{self.qualname}"


@dataclass
class ClassInfo:
    name: str
    qualname: str
    module: str
    lineno: int = 0
    doc: str = ""
    bases: list = field(default_factory=list)          # resolved dotted names where possible
    methods: list = field(default_factory=list)
    decorators: list = field(default_factory=list)
    fields: list = field(default_factory=list)          # annotated class attributes (dataclasses)

    @property
    def id(self):
        return f"{self.module}.{self.qualname}"


@dataclass
class ModuleInfo:
    name: str
    package: str
    path: str
    doc: str = ""
    classes: list = field(default_factory=list)
    functions: list = field(default_factory=list)
    imports: list = field(default_factory=list)         # internal modules (dotted)
    external_imports: list = field(default_factory=list)
    lines: int = 0
    registrations: list = field(default_factory=list)   # [(kind, name, qualname)]
    static_traces: list = field(default_factory=list)
    gui: bool = False
    imported: bool = False
    error: str = ""
    _raw_imports: list = field(default_factory=list, repr=False)

    @property
    def summary(self):
        return first_sentence(self.doc)


@dataclass
class ConceptSection:
    id: str
    title: str
    package: str
    file: str
    level: int = 2
    text: str = ""
    subsections: list = field(default_factory=list)     # [(title, markdown)]
    citations: list = field(default_factory=list)       # [(ref_id, locator)]
    equations: list = field(default_factory=list)

    def subsection(self, title):
        for t, body in self.subsections:
            if t.lower().startswith(title.lower()):
                return body
        return ""


@dataclass
class DocFile:
    package: str
    path: str
    title: str = ""
    text: str = ""
    sections: list = field(default_factory=list)        # ConceptSection with anchors
    headings: list = field(default_factory=list)        # [(level, title, anchor)]


@dataclass
class ComponentInfo:
    id: str                        # "kind/name"
    kind: str
    name: str
    package: str = ""
    module: str = ""
    qualname: str = ""
    version: str = ""
    versions: list = field(default_factory=list)
    label: str = ""
    category: str = ""
    language: str = "python"
    legacy: bool = False
    period: object = None
    direct_feedthrough: bool = True
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    params: list = field(default_factory=list)
    config_fields: list = field(default_factory=list)
    doc: dict = field(default_factory=dict)
    interface: str = ""
    source: str = ""

    @property
    def is_model(self):
        return self.kind in MODEL_KINDS

    @property
    def class_id(self):
        return f"{self.module}.{self.qualname}" if self.module and self.qualname else ""


@dataclass
class UsageInfo:
    # a test file, example or configuration file and what it refers to
    path: str
    kind: str                      # "test" | "example" | "config"
    title: str = ""
    doc: str = ""
    modules: list = field(default_factory=list)
    components: list = field(default_factory=list)
    functions: list = field(default_factory=list)       # tests: [(name, doc)]
    related: list = field(default_factory=list)         # other config files
    shows: dict = field(default_factory=dict)           # package -> "what it shows" (module.yaml validation)


@dataclass
class DataTypeInfo:
    name: str
    description: str = ""
    module: str = ""
    qualname: str = ""
    fields: list = field(default_factory=list)          # [(name, type, default)]
    legacy: bool = False
    color: str = ""


@dataclass
class ParamSet:
    # parameter dataclass defined in a package (fields with unit / label / limits)
    module: str
    qualname: str
    doc: str = ""
    fields: list = field(default_factory=list)


@dataclass
class ConceptInfo:
    id: str
    title: str = ""
    package: str = ""               # package whose theory.md documents it
    section: ConceptSection = None
    packages: list = field(default_factory=list)
    components: list = field(default_factory=list)
    implementations: list = field(default_factory=list)
    references: list = field(default_factory=list)

    @property
    def documented(self):
        return self.section is not None


@dataclass
class PackageInfo:
    name: str
    dotted: str
    path: str
    doc: str = ""
    modules: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    has_meta: bool = False
    theory: DocFile = None
    documents: list = field(default_factory=list)       # further DocFile chapters
    docs_dir: str = ""
    components: list = field(default_factory=list)
    tests: list = field(default_factory=list)
    examples: list = field(default_factory=list)
    configs: list = field(default_factory=list)
    traces: list = field(default_factory=list)
    concepts: list = field(default_factory=list)
    param_sets: list = field(default_factory=list)
    is_namespace: bool = False
    sub_meta: dict = field(default_factory=dict)        # nested docs folders: {"vdsim/gui/ad/docs": meta}

    def meta_list(self, key):
        # list-valued module.yaml key of the package and of all nested docs folders
        out = list(as_list(self.meta.get(key)))
        for sub in self.sub_meta.values():
            out += as_list(sub.get(key))
        return out

    def meta_dict(self, key):
        out = {}
        for meta in [self.meta] + list(self.sub_meta.values()):
            value = meta.get(key)
            if isinstance(value, dict):
                out.update(value)
        return out

    @property
    def title(self):
        return str(self.meta.get("title") or self.name)

    @property
    def summary(self):
        return str(self.meta.get("summary") or first_sentence(self.doc))


@dataclass
class KnowledgeBase:
    root: Path
    packages: dict = field(default_factory=dict)
    modules: dict = field(default_factory=dict)
    components: dict = field(default_factory=dict)
    traces: list = field(default_factory=list)
    concepts: dict = field(default_factory=dict)
    references: ReferenceDB = None
    tests: dict = field(default_factory=dict)
    examples: dict = field(default_factory=dict)
    configs: dict = field(default_factory=dict)
    datatypes: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    def warn(self, message):
        self.warnings.append(message)

    def package_of(self, module):
        return package_name(module)

    def function(self, dotted):
        # FunctionInfo / ClassInfo by "module.Class.method" (longest module prefix)
        parts = dotted.split(".")
        for i in range(len(parts) - 1, 0, -1):
            mod = self.modules.get(".".join(parts[:i]))
            if mod is None:
                continue
            qual = ".".join(parts[i:])
            for cls in mod.classes:
                if cls.qualname == qual:
                    return cls
                for m in cls.methods:
                    if m.qualname == qual:
                        return m
            for fn in mod.functions:
                if fn.qualname == qual:
                    return fn
        return None

    def split_implementation(self, dotted):
        # "vdsim.geometry.reference_line.ReferenceLine.to_frenet" -> (module, qualname)
        parts = dotted.split(".")
        for i in range(len(parts) - 1, 0, -1):
            if ".".join(parts[:i]) in self.modules:
                return ".".join(parts[:i]), ".".join(parts[i:])
        return dotted.rsplit(".", 1)[0], dotted.rsplit(".", 1)[-1]

    def used_reference_ids(self):
        # {ref_id: [places]} of every reference id used in code or documentation
        used = {}

        def add(ref_id, where):
            if ref_id:
                used.setdefault(str(ref_id), set()).add(where)
        for comp in self.components.values():
            for ref_id in comp.doc.get("references", []) or []:
                add(ref_id, f"component:{comp.id}")
        for tr in self.traces:
            add(tr.get("source"), f"{tr.get('origin', '@trace')}:{tr['module']}.{tr['qualname']}")
        for pkg in self.packages.values():
            for ref_id in pkg.meta_list("references"):
                add(ref_id, f"module.yaml:{pkg.name}")
            for doc in ([pkg.theory] if pkg.theory else []) + pkg.documents:
                for ref_id, _ in parse_citations(doc.text):
                    add(ref_id, doc.path)
        for link in self.references.links if self.references else []:
            add(link["reference"], "links.yaml")
        return {k: sorted(v) for k, v in sorted(used.items())}

    def reference_report(self):
        # missing reference ids (used but not defined) and validation issues of the database
        used = self.used_reference_ids()
        missing = {rid: where for rid, where in used.items() if rid not in self.references}
        return {"missing": missing, "issues": [str(i) for i in self.references.issues],
                "defined": len(self.references), "used": len(used)}


# ---------------------------------------------------------------------------- helpers
def first_sentence(text):
    text = " ".join((text or "").strip().split())
    if not text:
        return ""
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return (m.group(1) if m else text)[:300]


def as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def package_name(module):
    parts = str(module).split(".")
    if parts[0] == "vdsim" and len(parts) > 1:
        return parts[1]
    return parts[0]


def humanize(concept_id):
    return str(concept_id).replace("_", " ").replace("-", " ").strip().capitalize()


def _const(node):
    return node.value if isinstance(node, ast.Constant) else None


def _call_name(node):
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _leading_comment(lines, node):
    # comment lines between the def/class line and the first statement of the body
    if not getattr(node, "body", None):
        return ""
    start = node.lineno
    end = node.body[0].lineno - 1
    out = []
    for i in range(start, min(end, len(lines))):
        s = lines[i].strip()
        if s.startswith("#"):
            out.append(s.lstrip("#").strip())
        elif out and s:
            break
    if not out:
        # comment as first lines of the body (after a multi-line signature)
        i = node.body[0].lineno - 2
        block = []
        while i >= start and lines[i].strip().startswith("#"):
            block.insert(0, lines[i].strip().lstrip("#").strip())
            i -= 1
        out = block
    return " ".join(out)


def _node_doc(node, lines):
    doc = ast.get_docstring(node) or ""
    return doc.strip() if doc else _leading_comment(lines, node)


# ---------------------------------------------------------------------------- module parsing
def parse_module(path, name, package, root):
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ModuleInfo(name, package, rel(path, root), error=f"nicht lesbar: {exc}")
    info = ModuleInfo(name, package, rel(path, root), lines=source.count("\n") + 1)
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        info.error = f"Syntaxfehler Zeile {exc.lineno}: {exc.msg}"
        return info
    lines = source.splitlines()
    info.doc = (ast.get_docstring(tree) or "").strip()
    is_pkg = path.name == "__init__.py"
    base_parts = name.split(".") if is_pkg else name.split(".")[:-1]
    raw_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                raw_imports.append((alias.name, None, node in tree.body))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = base_parts[: len(base_parts) - (node.level - 1)] if node.level > 1 else list(base_parts)
                mod = ".".join(parts + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            for alias in node.names:
                raw_imports.append((mod, alias.name, node in tree.body))
    info._raw_imports = raw_imports
    top_level_ext = {imp[0].split(".")[0] for imp in raw_imports if imp[2]}
    info.gui = bool(top_level_ext & set(GUI_MODULES))
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and func.attr == "use" and isinstance(func.value, ast.Name) \
                    and func.value.id == "matplotlib":
                info.gui = True
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn = _function_info(node, name, node.name, lines, False)
            info.functions.append(fn)
            _decorator_facts(node, info, node.name)
        elif isinstance(node, ast.ClassDef):
            cls = ClassInfo(node.name, node.name, name, node.lineno, _node_doc(node, lines),
                            [ast.unparse(b) for b in node.bases], decorators=[ast.unparse(d) for d in node.decorator_list])
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cls.methods.append(_function_info(item, name, f"{node.name}.{item.name}", lines, True))
                    _decorator_facts(item, info, f"{node.name}.{item.name}")
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    default = ast.unparse(item.value) if item.value is not None else ""
                    cls.fields.append((item.target.id, ast.unparse(item.annotation), default[:80]))
            info.classes.append(cls)
            _decorator_facts(node, info, node.name)
    return info


def _function_info(node, module, qualname, lines, is_method):
    args = [a.arg for a in node.args.args + node.args.kwonlyargs]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return FunctionInfo(node.name, qualname, module, node.lineno, _node_doc(node, lines), args,
                        [ast.unparse(d) for d in node.decorator_list], is_method)


def _decorator_facts(node, info, qualname):
    for dec in node.decorator_list:
        name = _call_name(dec)
        if not isinstance(dec, ast.Call):
            continue
        args = [_const(a) for a in dec.args]
        kwargs = {k.arg: _const(k.value) for k in dec.keywords if k.arg}
        if name == "register" and len(args) >= 2 and all(isinstance(a, str) for a in args[:2]):
            info.registrations.append((args[0], args[1], qualname))
        elif name == "maneuver" and args and isinstance(args[0], str):
            info.registrations.append(("maneuver", args[0], qualname))
        elif name == "trace":
            source = args[0] if args else kwargs.get("source")
            if isinstance(source, str):
                entry = {"module": info.name, "qualname": qualname, "source": source, "section": "", "equation": "",
                         "concept": "", "note": ""}
                for i, key in enumerate(("section", "equation", "concept", "note"), start=1):
                    if len(args) > i and isinstance(args[i], str):
                        entry[key] = args[i]
                for key in ("section", "equation", "concept", "note"):
                    if isinstance(kwargs.get(key), str):
                        entry[key] = kwargs[key]
                info.static_traces.append(entry)


# ---------------------------------------------------------------------------- markdown documents
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*(?:\{#([A-Za-z0-9_.:\-]+)\})?\s*$")
EQUATION = re.compile(r"\$\$(.+?)\$\$", re.S)


def parse_markdown_doc(path, package, root):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    doc = DocFile(package, rel(path, root), text=text)
    lines = text.splitlines()
    headings = []         # (line index, level, title, anchor)
    fenced = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = HEADING.match(line)
        if m:
            headings.append((i, len(m.group(1)), m.group(2).strip(), m.group(3) or ""))
    doc.headings = [(lvl, title, anchor) for _, lvl, title, anchor in headings]
    for _, lvl, title, _ in headings:
        if lvl == 1:
            doc.title = title
            break
    for k, (i, lvl, title, anchor) in enumerate(headings):
        if not anchor or lvl < 2:
            continue
        end = len(lines)
        for j, lvl2, _, _ in headings[k + 1:]:
            if lvl2 <= lvl:
                end = j
                break
        body = "\n".join(lines[i + 1:end]).strip("\n")
        section = ConceptSection(anchor, title, package, doc.path, lvl, body)
        subs = [(j, l2, t2) for j, l2, t2, _ in headings[k + 1:] if j < end and l2 == lvl + 1]
        for n, (j, _, t2) in enumerate(subs):
            stop = subs[n + 1][0] if n + 1 < len(subs) else end
            section.subsections.append((t2, "\n".join(lines[j + 1:stop]).strip()))
        section.citations = parse_citations(body)
        section.equations = [e.strip() for e in EQUATION.findall(body)]
        doc.sections.append(section)
    return doc


# ---------------------------------------------------------------------------- collector
class Collector:
    def __init__(self, root=None, import_modules=True, packages=None):
        self.root = root_dir(root)
        self.import_modules = import_modules
        self.only = set(packages) if packages else None
        self.kb = KnowledgeBase(self.root)

    # ------------------------------------------------------------------ main
    def run(self):
        kb = self.kb
        steps = [self._references, self._packages, self._imports, self._components, self._traces,
                 self._datatypes, self._param_sets, self._usages, self._doc_traces, self._concepts, self._aggregate]
        for step in steps:
            try:
                step()
            except Exception as exc:   # one broken step must never stop the whole collection
                kb.warn(f"Sammelschritt {step.__name__} abgebrochen: {type(exc).__name__}: {exc}")
                log.debug("collector step failed", exc_info=True)
        kb.warnings = sorted(set(kb.warnings))
        return kb

    def _references(self):
        self.kb.references = ReferenceDB(self.root / "docs" / "references")

    # ------------------------------------------------------------------ packages and modules
    def _package_dirs(self):
        out = []
        vdsim_dir = self.root / "vdsim"
        if vdsim_dir.is_dir():
            for d in sorted(vdsim_dir.iterdir()):
                if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith((".", "_")):
                    if (d / "__init__.py").exists() or any(d.glob("*.py")) or (d / "docs").is_dir():
                        out.append((d.name, f"vdsim.{d.name}", d))
        for name in EXTRA_PACKAGES:
            d = self.root / name
            if d.is_dir():
                out.append((name, name, d))
        if self.only:
            out = [p for p in out if p[0] in self.only]
        return out

    def _packages(self):
        kb = self.kb
        for name, dotted, path in self._package_dirs():
            pkg = PackageInfo(name, dotted, rel(path, self.root), docs_dir=rel(path / "docs", self.root),
                              is_namespace=not (path / "__init__.py").exists())
            if pkg.is_namespace and any(path.glob("*.py")):
                kb.warn(f"Paket {dotted}: __init__.py fehlt (Namespace-Paket)")
            for py in sorted(path.rglob("*.py")):
                if any(part in SKIP_DIRS for part in py.relative_to(path).parts[:-1]):
                    continue
                parts = list(py.relative_to(path).with_suffix("").parts)
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                mod_name = ".".join([dotted] + parts)
                info = parse_module(py, mod_name, name, self.root)
                if info.error:
                    kb.warn(f"{info.path}: {info.error}")
                kb.modules[mod_name] = info
                pkg.modules.append(mod_name)
                if mod_name == dotted:
                    pkg.doc = info.doc
            pkg.modules.sort()
            self._package_docs(pkg, path)
            kb.packages[name] = pkg

    def _package_docs(self, pkg, path):
        docs = path / "docs"
        meta_path = docs / "module.yaml"
        if meta_path.exists():
            try:
                meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
                if not isinstance(meta, dict):
                    raise ValueError("keine Zuordnung")
                pkg.meta, pkg.has_meta = meta, True
                unknown = sorted(set(meta) - set(MODULE_YAML_KEYS))
                if unknown:
                    self.kb.warn(f"{rel(meta_path, self.root)}: unbekannte Schlüssel {unknown}")
                if meta.get("id") and str(meta["id"]) != pkg.name:
                    self.kb.warn(f"{rel(meta_path, self.root)}: id '{meta['id']}' passt nicht zum Paket '{pkg.name}'")
            except Exception as exc:
                self.kb.warn(f"{rel(meta_path, self.root)} nicht lesbar: {str(exc).splitlines()[0]}")
        for sub_docs in sorted(path.rglob("docs")):
            if sub_docs == docs or not sub_docs.is_dir() or "__pycache__" in sub_docs.parts:
                continue
            if any(part in SKIP_DIRS - {"docs"} for part in sub_docs.relative_to(path).parts):
                continue
            sub_yaml = sub_docs / "module.yaml"
            if sub_yaml.exists():
                try:
                    sub = yaml.safe_load(sub_yaml.read_text(encoding="utf-8")) or {}
                    if isinstance(sub, dict):
                        pkg.sub_meta[rel(sub_docs, self.root)] = sub
                except Exception as exc:
                    self.kb.warn(f"{rel(sub_yaml, self.root)} nicht lesbar: {str(exc).splitlines()[0]}")
            for md in sorted(sub_docs.glob("*.md")):
                doc = parse_markdown_doc(md, pkg.name, self.root)
                if doc is not None:
                    pkg.documents.append(doc)
        if docs.is_dir():
            for md in sorted(docs.glob("*.md")):
                doc = parse_markdown_doc(md, pkg.name, self.root)
                if doc is None:
                    self.kb.warn(f"{rel(md, self.root)} nicht lesbar")
                    continue
                if md.name == "theory.md":
                    pkg.theory = doc
                else:
                    pkg.documents.append(doc)

    def _imports(self):
        kb = self.kb
        known = set(kb.modules)
        roots = {"vdsim"} | set(EXTRA_PACKAGES)
        for info in kb.modules.values():
            internal, external = set(), set()
            for mod, name, _ in info._raw_imports:
                top = mod.split(".")[0] if mod else ""
                if top in roots:
                    candidate = f"{mod}.{name}" if name and f"{mod}.{name}" in known else mod
                    while candidate and candidate not in known and "." in candidate:
                        candidate = candidate.rsplit(".", 1)[0]
                    if candidate in known and candidate != info.name:
                        internal.add(candidate)
                elif top:
                    external.add(top)
            info.imports = sorted(internal)
            info.external_imports = sorted(external)
        if not self.import_modules:
            return
        for name in sorted(kb.modules):
            info = kb.modules[name]
            if info.gui or info.error or name.endswith("__main__") or self._depends_on_gui(name, set()):
                continue
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    importlib.import_module(name)
                info.imported = True
            except BaseException as exc:  # noqa: BLE001 - SystemExit of half-finished modules included
                if isinstance(exc, KeyboardInterrupt):
                    raise
                kb.warn(f"Import von {name} fehlgeschlagen: {type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}")

    def _depends_on_gui(self, name, seen):
        # module imports (transitively, top level) a GUI module of the repository
        if name in seen:
            return False
        seen.add(name)
        info = self.kb.modules.get(name)
        if info is None:
            return False
        if info.gui:
            return True
        return any(self._depends_on_gui(dep, seen) for dep in info.imports
                   if dep in self.kb.modules and any(raw[0] and dep.startswith(raw[0]) and raw[2]
                                                     for raw in info._raw_imports))

    # ------------------------------------------------------------------ components
    def _components(self):
        kb = self.kb
        if self.import_modules:
            try:
                from ..framework.plugins import available_components
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    described = available_components()
            except Exception as exc:
                described = []
                kb.warn(f"available_components() fehlgeschlagen: {exc}")
            grouped = {}
            for d in described:
                grouped.setdefault(f"{d['kind']}/{d['name']}", []).append(d)
            for cid, items in sorted(grouped.items()):
                d = items[0]          # newest first
                comp = ComponentInfo(cid, d["kind"], d["name"], package_name(d.get("module", "")), d.get("module", ""),
                                     d.get("class", ""), str(d.get("version", "")), [str(i["version"]) for i in items],
                                     d.get("label", ""), d.get("category", ""), d.get("language", "python"), False,
                                     d.get("period"), bool(d.get("direct_feedthrough", True)),
                                     dict(sorted((d.get("inputs") or {}).items())),
                                     dict(sorted((d.get("outputs") or {}).items())),
                                     list(d.get("params") or []), doc=dict(d.get("doc") or {}), source="plugins")
                kb.components[cid] = comp
            self._legacy_components()
        # statically registered components of modules that could not be imported
        for info in kb.modules.values():
            for kind, name, qualname in info.registrations:
                cid = f"{kind}/{name}"
                if cid not in kb.components:
                    comp = ComponentInfo(cid, kind, name, info.package, info.name, qualname, "legacy", ["legacy"],
                                         legacy=True, source="static")
                    self._legacy_ports(comp)
                    kb.components[cid] = comp
        self._component_yaml()

    def _legacy_components(self):
        kb = self.kb
        try:
            from ..core import registry
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                registry._load_builtin_plugins()
            entries = {k: dict(v) for k, v in registry._REGISTRY.items()}
        except Exception as exc:
            kb.warn(f"klassische Registry nicht lesbar: {exc}")
            return
        labels = {}
        try:
            from ..vehicle_models import MODEL_LABELS
            labels.update({("vehicle_model", k): v for k, v in MODEL_LABELS.items()})
        except Exception:
            pass
        maneuver_info = {}
        try:
            from ..trajectory.trajectory_generator import MANEUVER_INFO
            maneuver_info = MANEUVER_INFO
        except Exception:
            pass
        units = self._known_param_units()
        for kind in sorted(entries):
            for name in sorted(entries[kind]):
                obj = entries[kind][name]
                cid = f"{kind}/{name}"
                module = getattr(obj, "__module__", "")
                label = getattr(obj, "label", "") if isinstance(getattr(obj, "label", ""), str) else ""
                label = label or labels.get((kind, name), "") or maneuver_info.get(name, {}).get("label", "")
                comp = ComponentInfo(cid, kind, name, package_name(module), module, getattr(obj, "__qualname__", ""),
                                     "legacy", ["legacy"], label, maneuver_info.get(name, {}).get("category", kind),
                                     legacy=True, source="registry")
                self._legacy_ports(comp)
                comp.params = self._signature_params(obj, maneuver_info.get(name, {}).get("params", {}), units)
                doc = {}
                try:
                    from ..framework.knowledge import ComponentDoc, doc_of
                    d = getattr(obj, "DOC", None)
                    if isinstance(d, ComponentDoc):
                        doc = d.to_dict()
                    else:
                        doc = {"summary": first_sentence(doc_of(obj).summary)} if obj.__doc__ else {}
                except Exception:
                    pass
                if not doc.get("summary"):
                    info = kb.modules.get(module)
                    fn = kb.function(f"{module}.{comp.qualname}") if info else None
                    summary = (fn.doc if fn else "") or (maneuver_info.get(name, {}).get("description", ""))
                    if summary:
                        doc["summary"] = first_sentence(summary)
                comp.doc = doc
                kb.components[cid] = comp

    def _legacy_ports(self, comp):
        ins, outs, iface = LEGACY_INTERFACES.get(comp.kind, ({}, {}, ""))
        comp.inputs = {k: {"type": v, "description": PORT_DESCRIPTIONS.get(k, ""), "unit": "", "optional": False,
                           "feedback": False} for k, v in ins.items()}
        comp.outputs = {k: {"type": v, "description": PORT_DESCRIPTIONS.get(k, ""), "unit": "", "optional": False,
                            "feedback": False} for k, v in outs.items()}
        comp.interface = iface

    def _known_param_units(self):
        # field name -> metadata of all parameter dataclasses of the vehicle configuration
        out = {}
        try:
            from ..core.parameters import VehicleConfig
            for group in dataclasses.fields(VehicleConfig):
                for f in dataclasses.fields(group.default_factory()):
                    out.setdefault(f.name, dict(f.metadata))
        except Exception:
            pass
        return out

    @staticmethod
    def _signature_params(obj, labels, units):
        try:
            target = obj.__init__ if inspect.isclass(obj) else obj
            sig = inspect.signature(target)
        except (TypeError, ValueError):
            return []
        out = []
        for p in sig.parameters.values():
            if p.name in ("self", "config", "cls") or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                continue
            default = None if p.default is inspect.Parameter.empty else p.default
            entry = {"name": p.name, "default": default, "type": type(default).__name__ if default is not None else "",
                     "label": p.name, "unit": ""}
            if p.name in labels:
                lab = labels[p.name]
                entry["label"], entry["unit"] = (lab[0], lab[1]) if isinstance(lab, (tuple, list)) else (str(lab), "")
            elif p.name in units:
                entry["label"] = units[p.name].get("label", p.name)
                entry["unit"] = units[p.name].get("unit", "")
                for key in ("min", "max"):
                    if key in units[p.name]:
                        entry[key] = units[p.name][key]
            if p.default is inspect.Parameter.empty:
                entry["required"] = True
            out.append(entry)
        return out

    def _component_yaml(self):
        # module.yaml "components:" supplements ComponentDoc and parameter descriptions
        kb = self.kb
        cfg_meta = self._config_field_meta()
        for pkg in kb.packages.values():
            entries = pkg.meta_dict("components")
            if not isinstance(entries, dict):
                kb.warn(f"{pkg.docs_dir}/module.yaml: 'components' muss eine Zuordnung sein")
                continue
            for cid, extra in sorted(entries.items()):
                comp = kb.components.get(str(cid))
                if comp is None:
                    kb.warn(f"{pkg.docs_dir}/module.yaml: Komponente '{cid}' ist nicht registriert")
                    continue
                if not isinstance(extra, dict):
                    continue
                for key in COMPONENT_DOC_FIELDS:
                    if extra.get(key) and not comp.doc.get(key):
                        comp.doc[key] = extra[key]
                for pname, pmeta in (extra.get("parameters") or {}).items():
                    for entry in comp.params:
                        if entry["name"] == pname and isinstance(pmeta, dict):
                            for k in ("unit", "label", "min", "max", "description"):
                                if k in pmeta and (not entry.get(k) or entry.get(k) == entry["name"]):
                                    entry[k] = pmeta[k]
                for spec in as_list(extra.get("config_fields")):
                    for path, meta in cfg_meta:
                        if path == spec or (spec.endswith("*") and path.startswith(spec[:-1])):
                            comp.config_fields.append({"name": path, **meta})
                if extra.get("label") and not comp.label:
                    comp.label = extra["label"]

    def _config_field_meta(self):
        out = []
        try:
            from ..core.parameters import VehicleConfig
            from ..framework.component import params_schema
            for group in dataclasses.fields(VehicleConfig):
                for entry in params_schema(group.default_factory):
                    meta = {k: v for k, v in entry.items() if k != "name"}
                    out.append((f"{group.name}.{entry['name']}", meta))
        except Exception as exc:
            self.kb.warn(f"Fahrzeugparameter nicht lesbar: {exc}")
        return out

    # ------------------------------------------------------------------ traces
    def _traces(self):
        kb = self.kb
        dynamic = []
        if self.import_modules:
            try:
                from ..framework.knowledge import TRACES
                dynamic = [dict(t) for t in TRACES]
            except Exception as exc:
                kb.warn(f"TRACES nicht lesbar: {exc}")
        seen = set()
        for t in dynamic + [dict(t) for info in kb.modules.values() for t in info.static_traces]:
            key = (t.get("module"), t.get("qualname"), t.get("source"), t.get("equation"), t.get("concept"),
                   t.get("section"))
            if key in seen:
                continue
            seen.add(key)
            t.setdefault("origin", "@trace")
            t["package"] = package_name(t.get("module", ""))
            t["implementation"] = f"{t.get('module')}.{t.get('qualname')}"
            kb.traces.append(t)

    def _doc_traces(self):
        # module.yaml "traceability:" for code without @trace (documented after the fact)
        kb = self.kb
        for pkg in kb.packages.values():
            for item in pkg.meta_list("traceability"):
                if not isinstance(item, dict) or not item.get("implementation"):
                    kb.warn(f"{pkg.docs_dir}/module.yaml: ungültiger traceability-Eintrag {item!r}")
                    continue
                impl = str(item["implementation"])
                module, qualname = kb.split_implementation(impl)
                if module not in kb.modules:
                    kb.warn(f"{pkg.docs_dir}/module.yaml: Implementierung '{impl}' nicht gefunden")
                elif kb.function(impl) is None and qualname:
                    kb.warn(f"{pkg.docs_dir}/module.yaml: '{qualname}' nicht in {module} gefunden")
                sources = as_list(item.get("source") or item.get("sources") or [""])
                for source in sources:
                    key = (module, qualname, source, str(item.get("equation", "")), str(item.get("concept", "")))
                    if any((t["module"], t["qualname"], t["source"], t["equation"], t["concept"]) == key
                           for t in kb.traces):
                        continue
                    kb.traces.append({"module": module, "qualname": qualname, "source": str(source or ""),
                                      "section": str(item.get("section", "")), "equation": str(item.get("equation", "")),
                                      "concept": str(item.get("concept", "")), "note": str(item.get("note", "")),
                                      "origin": "module.yaml", "package": package_name(module),
                                      "implementation": f"{module}.{qualname}", "tests": as_list(item.get("tests"))})
        kb.traces.sort(key=lambda t: (t["package"], t["module"], t["qualname"], t["concept"], t["source"],
                                      t["equation"], t["origin"]))

    # ------------------------------------------------------------------ data types and parameter sets
    def _datatypes(self):
        kb = self.kb
        types, desc, colors = {}, {}, {}
        if self.import_modules:
            try:
                from ..framework import types as ftypes
                types, desc, colors = dict(ftypes.TYPES), dict(ftypes.TYPE_DESCRIPTIONS), dict(ftypes.TYPE_COLORS)
            except Exception as exc:
                kb.warn(f"vdsim.framework.types nicht lesbar: {exc}")
        for name in sorted(types):
            py = types[name]
            module = getattr(py, "__module__", "") if py not in (object, float, bool) else ""
            if module == "builtins" or module.startswith("numpy"):
                module = ""
            info = DataTypeInfo(name, desc.get(name, ""), module, getattr(py, "__qualname__", "") if module else "",
                                color=colors.get(name, ""))
            if module and dataclasses.is_dataclass(py):
                info.fields = [(f.name, str(f.type), _default_text(f)) for f in dataclasses.fields(py)]
            kb.datatypes[name] = info
        for name, (module, qual, text) in LEGACY_TYPES.items():
            if name in kb.datatypes:
                continue
            info = DataTypeInfo(name, text, module, qual, legacy=True)
            cls = None
            mod = kb.modules.get(module)
            if mod:
                cls = next((c for c in mod.classes if c.qualname == qual), None)
            if cls is None:
                continue
            info.fields = [(f[0], f[1], f[2]) for f in cls.fields]
            kb.datatypes[name] = info
        # port types that are not registered
        for comp in kb.components.values():
            for port in list(comp.inputs.values()) + list(comp.outputs.values()):
                t = port.get("type", "Any")
                if t not in kb.datatypes:
                    kb.datatypes[t] = DataTypeInfo(t, "nicht registrierter Port-Typ")

    def _param_sets(self):
        kb = self.kb
        if not self.import_modules:
            return
        try:
            from ..framework.component import params_schema
        except Exception:
            return
        import sys
        for name, info in sorted(kb.modules.items()):
            mod = sys.modules.get(name)
            if mod is None or not info.imported:
                continue
            for cls in info.classes:
                obj = getattr(mod, cls.name, None)
                if obj is None or not dataclasses.is_dataclass(obj) or getattr(obj, "__module__", "") != name:
                    continue
                flds = dataclasses.fields(obj)
                if not flds or not (cls.name.endswith(("Parameters", "Params", "Config")) or
                                    any("unit" in f.metadata for f in flds)):
                    continue
                try:
                    schema = params_schema(obj)
                except Exception:
                    continue
                kb.packages[info.package].param_sets.append(ParamSet(name, cls.name, cls.doc, schema)) \
                    if info.package in kb.packages else None

    # ------------------------------------------------------------------ tests, examples, configs
    def _usages(self):
        kb = self.kb
        files = []
        tests_dir = self.root / "tests"
        if tests_dir.is_dir():
            files += [(p, "test") for p in sorted(tests_dir.rglob("*.py"))
                      if p.name.startswith("test") or p.name == "conftest.py"]
        examples_dir = self.root / "examples"
        if examples_dir.is_dir():
            files += [(p, "example") for p in sorted(examples_dir.rglob("*.py"))]
        files += [(p, "example") for p in sorted(self.root.glob("run_*.py"))]
        for path, kind in files:
            if any(part in SKIP_DIRS for part in path.relative_to(self.root).parts[:-1]):
                continue
            usage = self._python_usage(path, kind)
            if usage is not None:
                (kb.tests if kind == "test" else kb.examples)[usage.path] = usage
        cfg_dir = self.root / "configs"
        if cfg_dir.is_dir():
            for path in sorted(cfg_dir.rglob("*")):
                if path.suffix.lower() in (".json", ".yaml", ".yml") and path.is_file():
                    usage = self._config_usage(path)
                    if usage is not None:
                        kb.configs[usage.path] = usage
        for pkg in kb.packages.values():
            for item in pkg.meta_list("validation"):
                if isinstance(item, dict) and item.get("test"):
                    test = str(item["test"]).split("::")[0]
                    if test in kb.tests:
                        kb.tests[test].shows[pkg.name] = str(item.get("shows", ""))
                    else:
                        kb.warn(f"{pkg.docs_dir}/module.yaml: Test '{test}' nicht gefunden")

    def _python_usage(self, path, kind):
        kb = self.kb
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            kb.warn(f"{rel(path, self.root)} nicht analysierbar: {exc}")
            return None
        lines = source.splitlines()
        usage = UsageInfo(rel(path, self.root), kind, path.stem, (ast.get_docstring(tree) or "").strip())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                for alias in node.names:
                    full = f"{node.module}.{alias.name}"
                    mods.add(full if full in kb.modules else node.module)
                    pkg_mod = kb.modules.get(node.module)
                    if full not in kb.modules and pkg_mod is not None:
                        # name re-exported by a package: link the submodule that defines it
                        for dep in pkg_mod.imports:
                            sub = kb.modules.get(dep)
                            if sub and any(x.name == alias.name for x in sub.classes + sub.functions):
                                mods.add(dep)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name)
        resolved = set()
        for m in mods:
            while m and m not in kb.modules and "." in m:
                m = m.rsplit(".", 1)[0]
            if m in kb.modules:
                resolved.add(m)
        usage.modules = sorted(resolved)
        usage.components = sorted(self._component_refs_ast(tree))
        if kind == "test":
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                    usage.functions.append((node.name, _node_doc(node, lines)))
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith("test"):
                            usage.functions.append((f"{node.name}.{item.name}", _node_doc(item, lines)))
        return usage

    def _component_refs_ast(self, tree):
        comps = self.kb.components
        found = set()

        def add(kind, name):
            if isinstance(name, str) and f"{kind}/{name}" in comps:
                found.add(f"{kind}/{name}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                found |= self._spec_refs(node.value)
            elif isinstance(node, ast.Call):
                fname = _call_name(node)
                for kw in node.keywords:
                    if kw.arg in KEYWORD_KINDS:
                        add(KEYWORD_KINDS[kw.arg], _const(kw.value))
                    if kw.arg == "vehicle_overrides" and isinstance(kw.value, ast.Dict):
                        for k in kw.value.keys:
                            found |= self._override_refs(_const(k))
                args = [_const(a) for a in node.args]
                if fname in ("create", "get") and len(args) >= 2 and isinstance(args[0], str):
                    add(args[0], args[1])
                elif fname == "generate" and args and isinstance(args[0], str):
                    add("maneuver", args[0])
                elif fname == "parametrize" and len(node.args) >= 2 and isinstance(args[0], str):
                    names = [n.strip() for n in args[0].split(",")]
                    values = node.args[1]
                    if isinstance(values, (ast.List, ast.Tuple)):
                        for elt in values.elts:
                            row = elt.elts if isinstance(elt, (ast.Tuple, ast.List)) else [elt]
                            for n, v in zip(names, row):
                                if n in KEYWORD_KINDS:
                                    add(KEYWORD_KINDS[n], _const(v))
            elif isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    key = _const(k)
                    if key in KEYWORD_KINDS:
                        add(KEYWORD_KINDS[key], _const(v))
                    found |= self._override_refs(key)
        return found

    def _spec_refs(self, text):
        out = set()
        if "/" in text and len(text) < 120:
            base = text.split("@")[0].strip()
            if base in self.kb.components:
                out.add(base)
        return out

    def _override_refs(self, key):
        out = set()
        if isinstance(key, str) and key.startswith("systems.") and key.endswith("_enabled"):
            name = key[len("systems."):-len("_enabled")]
            if f"chassis_system/{name}" in self.kb.components:
                out.add(f"chassis_system/{name}")
        if key == "tires.model":
            pass
        return out

    def _config_usage(self, path):
        kb = self.kb
        try:
            if path.stat().st_size > 2_000_000:
                return None
            text = path.read_text(encoding="utf-8")
            data = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
        except Exception as exc:
            kb.warn(f"{rel(path, self.root)} nicht lesbar: {str(exc).splitlines()[0] if str(exc) else exc}")
            return None
        usage = UsageInfo(rel(path, self.root), "config", path.stem)
        if isinstance(data, dict):
            usage.title = str(data.get("name") or data.get("title") or path.stem)
            usage.doc = str(data.get("description") or "")
        comps, related = set(), set()

        def walk(obj, depth=0):
            if depth > 12:
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        if k in KEYWORD_KINDS and f"{KEYWORD_KINDS[k]}/{v}" in kb.components:
                            comps.add(f"{KEYWORD_KINDS[k]}/{v}")
                        comps.update(self._spec_refs(v))
                        if k == "vehicle" and (self.root / "configs" / "vehicles" / f"{v}.json").exists():
                            related.add(f"configs/vehicles/{v}.json")
                        if k == "model" and f"tire_model/{v}" in kb.components and "vehicles" in path.parts:
                            comps.add(f"tire_model/{v}")
                    elif v is True:
                        comps.update(self._override_refs(k))
                        if isinstance(k, str) and k.endswith("_enabled") and "vehicles" in path.parts:
                            name = k[:-len("_enabled")]
                            if f"chassis_system/{name}" in kb.components:
                                comps.add(f"chassis_system/{name}")
                    walk(v, depth + 1)
            elif isinstance(obj, list):
                for v in obj[:5000]:
                    if isinstance(v, str):
                        comps.update(self._spec_refs(v))
                    else:
                        walk(v, depth + 1)
        walk(data)
        usage.components = sorted(comps)
        usage.related = sorted(related)
        return usage

    # ------------------------------------------------------------------ concepts and aggregation
    def _concepts(self):
        kb = self.kb

        def concept(cid):
            cid = str(cid)
            if cid not in kb.concepts:
                kb.concepts[cid] = ConceptInfo(cid, humanize(cid))
            return kb.concepts[cid]
        for pkg in sorted(kb.packages.values(), key=lambda p: p.name):
            for doc in ([pkg.theory] if pkg.theory else []) + pkg.documents:
                for sec in doc.sections:
                    c = concept(sec.id)
                    if c.section is not None:
                        kb.warn(f"Konzept '{sec.id}' mehrfach dokumentiert ({c.section.file}, {sec.file})")
                        continue
                    c.section, c.title, c.package = sec, sec.title, pkg.name
                    c.references.extend(r for r, _ in sec.citations)
            for cid in pkg.meta_list("concepts"):
                c = concept(cid)
                c.packages.append(pkg.name)
        for comp in kb.components.values():
            for cid in as_list(comp.doc.get("concepts")):
                c = concept(cid)
                c.components.append(comp.id)
                c.references.extend(as_list(comp.doc.get("references")))
        for tr in kb.traces:
            if tr.get("concept"):
                c = concept(tr["concept"])
                c.implementations.append(tr["implementation"])
                if tr.get("source"):
                    c.references.append(tr["source"])
        for c in kb.concepts.values():
            c.packages = sorted(set(c.packages) | ({c.package} if c.package else set()))
            c.components = sorted(set(c.components))
            c.implementations = sorted(set(c.implementations))
            c.references = sorted(set(str(r) for r in c.references if r))
            if c.section is None:
                kb.warn(f"Konzept '{c.id}' ohne theory.md-Abschnitt")

    def _aggregate(self):
        kb = self.kb
        for comp in kb.components.values():
            if comp.package in kb.packages:
                kb.packages[comp.package].components.append(comp.id)
        for tr in kb.traces:
            if tr["package"] in kb.packages:
                kb.packages[tr["package"]].traces.append(tr)
        for pkg in kb.packages.values():
            pkg.components.sort()
            mods = set(pkg.modules)
            comps = set(pkg.components)
            concepts = set(pkg.meta_list("concepts"))
            if pkg.theory:
                concepts |= {s.id for s in pkg.theory.sections}
            for doc in pkg.documents:
                concepts |= {s.id for s in doc.sections}
            concepts |= {t["concept"] for t in pkg.traces if t.get("concept")}
            for cid in comps:
                concepts |= set(as_list(kb.components[cid].doc.get("concepts")))
            pkg.concepts = sorted(str(c) for c in concepts)
            for path, usage in kb.tests.items():
                if mods & set(usage.modules) or comps & set(usage.components) or pkg.name in usage.shows \
                        or path.startswith(f"tests/{pkg.name}/"):
                    pkg.tests.append(path)
            declared = {str(e) for e in pkg.meta_list("examples")}
            for path, usage in kb.examples.items():
                if mods & set(usage.modules) or comps & set(usage.components) or path in declared \
                        or path.startswith(f"examples/{pkg.name}/"):
                    pkg.examples.append(path)
            for path, usage in kb.configs.items():
                if comps & set(usage.components):
                    pkg.configs.append(path)
            for missing in sorted(declared - set(kb.examples)):
                if (self.root / missing).is_file():
                    kb.examples[missing] = UsageInfo(missing, "example", Path(missing).name)
                    pkg.examples.append(missing)
                elif " " not in missing:
                    kb.warn(f"{pkg.docs_dir}/module.yaml: Beispiel '{missing}' nicht gefunden")
            if not pkg.has_meta:
                kb.warn(f"Paket '{pkg.name}' ohne {pkg.docs_dir}/module.yaml (automatischer Stub)")


def _default_text(f):
    if f.default is not dataclasses.MISSING:
        return repr(f.default)[:60]
    if f.default_factory is not dataclasses.MISSING:
        try:
            return repr(f.default_factory())[:60]
        except Exception:
            return ""
    return ""


def collect(root=None, import_modules=True, packages=None):
    # Build the KnowledgeBase of the repository (never raises for broken or missing files)
    return Collector(root, import_modules, packages).run()
