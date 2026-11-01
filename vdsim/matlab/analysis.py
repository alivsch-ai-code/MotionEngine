"""Static analysis of MATLAB control code ("Regellogik darstellen und analysieren").

``analyze(mfile_or_path)`` returns a :class:`FileAnalysis` with, per function,

* signature (inputs/outputs), variables with definition and use lines, inferred types,
* data-flow dependencies (direct and which outputs depend on which inputs), call graph,
  used built-ins and unknown functions,
* equation references from comments (``% (4.11)``), assignments as MATLAB text and LaTeX,
* unused variables/inputs and complexity measures (cyclomatic complexity, nesting, ...),
* recognized control structure: gains (k1..kn, Kp, ...), reference and measured signals,
  error signals, feedback terms (gain x error), feedforward terms (reference terms without
  gain/error), integrators/differentiators on persistent states,

plus JSON (``to_json``) and Graphviz DOT (``to_dot``) export for GUI and documentation.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..framework.knowledge import trace
from . import nodes as N
from .builtins import BUILTINS
from .errors import Diagnostic
from .latex import assignment_latex, expr_latex, latex_name, stmt_to_matlab, to_matlab
from .parser import parse_file
from .typeinfer import TypeInference

EQUATION = re.compile(r"\(\s*((?:[A-Z]\.?)?\d+(?:\.\d+)*[a-z]?)\s*\)")
GAIN = re.compile(r"^(?:[kK](?:_?[a-zA-Z]{1,3})?_?\d*|[kK]|gain\w*|Gain\w*)$")
REFERENCE = re.compile(r"(?:^|_)(?:d|ref|des|soll|set|sp|target|cmd)(?:_|$)|^(?:r|w|ref\w*|setpoint)$")
ERROR_NAME = re.compile(r"^(?:e|err|error)(?:_\w+|\d+\w*)?$")


@dataclass
class VariableInfo:
    name: str
    role: str                       # input / output / inout / local / persistent / global / loop
    type: str = "unknown"
    defs: list = field(default_factory=list)
    uses: list = field(default_factory=list)
    signal: str = ""                # reference / gain / measurement / error / parameter (control analysis)
    latex: str = ""


@dataclass
class FunctionAnalysis:
    name: str
    inputs: list
    outputs: list
    line: int
    end_line: int
    doc: str = ""
    nested_in: str | None = None
    variables: dict = field(default_factory=dict)
    dependencies: dict = field(default_factory=dict)        # var -> direct dependencies
    output_dependencies: dict = field(default_factory=dict)  # output -> inputs it depends on
    calls: list = field(default_factory=list)                # local functions
    builtins: list = field(default_factory=list)
    unknown_calls: list = field(default_factory=list)
    assignments: list = field(default_factory=list)          # {line, target, matlab, latex, equations, comment}
    equations: list = field(default_factory=list)
    unused_variables: list = field(default_factory=list)
    unused_inputs: list = field(default_factory=list)
    complexity: dict = field(default_factory=dict)
    control: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["variables"] = {k: asdict(v) for k, v in self.variables.items()}
        return d


@dataclass
class FileAnalysis:
    path: str
    kind: str
    doc: str
    functions: list
    call_graph: dict
    builtins: list
    equations: list
    diagnostics: list

    @property
    def main(self):
        return self.functions[0] if self.functions else None

    def function(self, name=None):
        if name is None:
            return self.main
        for f in self.functions:
            if f.name == name:
                return f
        raise KeyError(name)

    def to_dict(self):
        return {"path": self.path, "kind": self.kind, "doc": self.doc,
                "functions": [f.to_dict() for f in self.functions], "call_graph": self.call_graph,
                "builtins": self.builtins, "equations": self.equations,
                "diagnostics": [d.to_dict() for d in self.diagnostics]}

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_dot(self, kind="dataflow", function=None):
        return dataflow_dot(self.function(function)) if kind == "dataflow" else callgraph_dot(self)

    def summary(self):
        # human readable German summary (CLI)
        lines = [f"Datei: {self.path} ({'Funktionsdatei' if self.kind == 'function' else 'Skript'})"]
        for f in self.functions:
            lines.append(f"\nFunktion {f.name}({', '.join(f.inputs)}) -> [{', '.join(f.outputs)}]  "
                         f"Zeilen {f.line}-{f.end_line}")
            c = f.complexity
            lines.append(f"  Komplexität: zyklomatisch {c['cyclomatic']}, Anweisungen {c['statements']}, "
                         f"Schachtelung {c['max_nesting']}, Operationen {c['operations']}")
            if f.calls:
                lines.append(f"  ruft auf: {', '.join(f.calls)}")
            if f.builtins:
                lines.append(f"  Built-ins: {', '.join(f.builtins)}")
            if f.unknown_calls:
                lines.append(f"  unbekannte Funktionen: {', '.join(f.unknown_calls)}")
            for out, deps in f.output_dependencies.items():
                lines.append(f"  {out} hängt ab von: {', '.join(deps) or '-'}")
            if f.equations:
                lines.append("  Gleichungen: " + ", ".join(sorted({e['equation'] for e in f.equations},
                                                                  key=_eq_key)))
            ctl = f.control
            if ctl.get("gains"):
                lines.append(f"  Regelungsstruktur: {ctl['structure']}")
                lines.append(f"    Verstärkungen: {', '.join(ctl['gains'])}")
                lines.append(f"    Sollgrößen: {', '.join(ctl['references']) or '-'}; "
                             f"Messgrößen: {', '.join(ctl['measurements']) or '-'}")
                lines.append(f"    Regelfehler: {', '.join(ctl['errors']) or '-'}")
                for t in ctl["feedback_terms"]:
                    lines.append(f"    Rückführung  (Z. {t['line']}) {t['target']}: {t['term']}")
                for t in ctl["feedforward_terms"]:
                    lines.append(f"    Vorsteuerung (Z. {t['line']}) {t['target']}: {t['term']}")
            if f.unused_variables:
                lines.append(f"  nicht verwendete Variablen: {', '.join(f.unused_variables)}")
            if f.unused_inputs:
                lines.append(f"  nicht verwendete Eingänge: {', '.join(f.unused_inputs)}")
        for d in self.diagnostics:
            lines.append(str(d))
        return "\n".join(lines)


def _eq_key(s):
    return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in re.split(r"[.]", re.sub(r"([a-z])$", r".\1", s))]


# ----------------------------------------------------------------------------- helpers
def _idents(e):
    return [n.name for n in e.walk() if isinstance(n, N.Ident)]


def _target_name(t):
    while not isinstance(t, (N.Ident, N.Placeholder)):
        t = t.base
    return t.name if isinstance(t, N.Ident) else None


def _calls_in(e, variables, local):
    # names used as functions (not variables)
    out = []
    for n in e.walk():
        if isinstance(n, N.Index) and isinstance(n.base, N.Ident) and n.base.name not in variables:
            out.append(n.base.name)
        elif isinstance(n, N.Ident) and n.name not in variables:
            out.append(n.name)
        elif isinstance(n, N.FuncHandle):
            out.append(n.name)
    return out


def _stmt_exprs(s):
    # (expressions read by the statement header, assigned targets)
    if isinstance(s, N.Assign):
        reads = [s.value]
        for t in s.targets:
            node = t
            while isinstance(node, (N.Index, N.CellIndex, N.Field, N.DynField)):
                if isinstance(node, (N.Index, N.CellIndex)):
                    reads.extend(node.args)
                elif isinstance(node, N.DynField):
                    reads.append(node.name)
                node = node.base
        return reads, [t for t in s.targets if not isinstance(t, N.Placeholder)]
    if isinstance(s, N.ExprStmt):
        return [s.expr], []
    if isinstance(s, N.If):
        return [c for c, _ in s.clauses], []
    if isinstance(s, N.For):
        return [s.iterable], []
    if isinstance(s, N.While):
        return [s.cond], []
    if isinstance(s, N.Switch):
        return [s.subject] + [v for v, _ in s.cases], []
    return [], []


def _additive_terms(e, sign=1):
    # flatten a +/- chain into signed terms
    if isinstance(e, N.Binary) and e.op in ("+", "-"):
        return _additive_terms(e.left, sign) + _additive_terms(e.right, sign if e.op == "+" else -sign)
    if isinstance(e, N.Unary) and e.op == "-" and isinstance(e.operand, N.Binary) and e.operand.op in ("+", "-"):
        return _additive_terms(e.operand, -sign)
    return [(sign, e)]


def _equations_of(stmt):
    return EQUATION.findall(stmt.comment)


# ----------------------------------------------------------------------------- analysis
class _Analyzer:
    def __init__(self, mfile, input_types=None):
        self.mfile = mfile
        self.local = {f.name: f for f in mfile.all_functions()}
        self.ti = TypeInference(mfile, input_types)
        self.results = {}
        self.diagnostics = []
        self._active = set()

    def function(self, f):
        if f.name in self.results:
            return self.results[f.name]
        if f.name in self._active:
            return None
        self._active.add(f.name)
        fa = self._analyze(f)
        self._active.discard(f.name)
        self.results[f.name] = fa
        return fa

    def _analyze(self, f):
        fa = FunctionAnalysis(f.name, list(f.params), list(f.outputs), f.line, f.end_line, f.doc, f.parent)
        try:
            types = self.ti.infer_entry(f).env
        except Exception as exc:  # inference must not break the analysis
            types = {}
            self.diagnostics.append(Diagnostic("warning", f"Typinferenz fehlgeschlagen: {exc}", f.line,
                                               target="analysis"))
        vars_ = {}

        def var(name, role="local"):
            if name not in vars_:
                vars_[name] = VariableInfo(name, role, str(types.get(name, "unknown")), latex=latex_name(name))
            return vars_[name]

        for p in f.params:
            if p != "~":
                var(p, "input")
        for o in f.outputs:
            v = var(o, "output")
            if o in f.params:
                v.role = "inout"
        stmts = list(N.body_statements(f.body))
        for s in stmts:
            if isinstance(s, (N.Persistent, N.Global)):
                for n in s.names:
                    var(n, "persistent" if isinstance(s, N.Persistent) else "global").defs.append(s.line)
            if isinstance(s, N.For):
                var(s.var, "loop").defs.append(s.line)
            if isinstance(s, N.Assign):
                for t in s.targets:
                    name = _target_name(t)
                    if name:
                        var(name).defs.append(s.line)
            if isinstance(s, N.TryCatch) and s.ident:
                var(s.ident).defs.append(s.line)
        names = set(vars_)
        # uses
        calls, builtins_used, unknown = [], [], []
        for s in stmts:
            reads, targets = _stmt_exprs(s)
            for e in reads:
                for n in _idents(e):
                    if n in names:
                        vars_[n].uses.append(s.line)
                for c in _calls_in(e, names, self.local):
                    if c in self.local:
                        calls.append(c)
                    elif c in BUILTINS:
                        builtins_used.append(c)
                    elif c not in ("nargin", "nargout", "end", "varargin", "ans"):
                        unknown.append(c)
            for t in targets:
                if not isinstance(t, N.Ident):     # x(i) = ... reads x
                    n = _target_name(t)
                    if n in names:
                        vars_[n].uses.append(s.line)
            if isinstance(s, N.Command):
                builtins_used.append(s.name)
        if self.mfile.path:
            d = Path(self.mfile.path).parent
            external = [c for c in unknown if (d / f"{c}.m").exists()]
            calls += external
            unknown = [c for c in unknown if c not in external]
        fa.calls = sorted(set(calls))
        fa.builtins = sorted(set(builtins_used))
        fa.unknown_calls = sorted(set(unknown))
        for c in fa.unknown_calls:
            self.diagnostics.append(Diagnostic("warning", f"Funktion oder Variable '{c}' ist unbekannt "
                                                          f"(in {f.name})", f.line, target="analysis"))
        for v in vars_.values():
            v.defs, v.uses = sorted(set(v.defs)), sorted(set(v.uses))
        fa.variables = vars_
        fa.dependencies = self._dependencies(f, names)
        fa.output_dependencies = self._output_deps(fa)
        fa.unused_variables = sorted(v.name for v in vars_.values() if v.role in ("local", "loop", "persistent")
                                     and not v.uses and v.name not in ("ans",))
        fa.unused_inputs = [p for p in f.params if p != "~" and p in vars_ and not vars_[p].uses
                            and p not in f.outputs and p != "varargin"]
        fa.complexity = self._complexity(f, stmts)
        arrays = {n for n, t in types.items() if getattr(t, "is_array", False)}
        functions = set(self.local) | set(BUILTINS) | set(fa.unknown_calls)
        for s in stmts:
            eqs = _equations_of(s)
            if isinstance(s, N.Assign):
                entry = {"line": s.line, "end_line": s.end_line,
                         "target": ", ".join(filter(None, (_target_name(t) for t in s.targets))),
                         "matlab": stmt_to_matlab(s), "latex": assignment_latex(s, functions - names, arrays),
                         "equations": eqs, "comment": s.comment, "leading": list(s.leading)}
                fa.assignments.append(entry)
            for eq in eqs:
                fa.equations.append({"equation": eq, "line": s.line,
                                     "target": ", ".join(filter(None, (_target_name(t) for t in s.targets)))
                                     if isinstance(s, N.Assign) else "",
                                     "latex": assignment_latex(s, functions - names, arrays)
                                     if isinstance(s, N.Assign) else ""})
        fa.control = self._control(f, fa, stmts, functions - names, arrays)
        for name, v in vars_.items():
            v.signal = fa.control["signals"].get(name, "")
        return fa

    # ------------------------------------------------------------------ data flow
    def _dependencies(self, f, names):
        deps = {n: set() for n in names}

        def visit(body, control):
            for s in body:
                if isinstance(s, N.Assign):
                    reads = set()
                    if len(s.targets) > 1 and isinstance(s.value, N.Index) and isinstance(s.value.base, N.Ident) \
                            and s.value.base.name in self.local:
                        callee = self.function(self.local[s.value.base.name])
                        arg_ids = [set(_idents(a)) & names for a in s.value.args]
                        for k, t in enumerate(s.targets):
                            n = _target_name(t)
                            if not n:
                                continue
                            d = set(control)
                            if callee is not None and k < len(callee.outputs):
                                for i, p in enumerate(callee.inputs):
                                    if p in callee.output_dependencies.get(callee.outputs[k], []) and i < len(arg_ids):
                                        d |= arg_ids[i]
                            else:
                                d |= set().union(*arg_ids) if arg_ids else set()
                            deps[n] |= d
                        continue
                    for e in _stmt_exprs(s)[0]:
                        reads |= set(_idents(e)) & names
                    for t in s.targets:
                        n = _target_name(t)
                        if n:
                            deps[n] |= reads | set(control) | ({n} if not isinstance(t, N.Ident) else set())
                elif isinstance(s, N.If):
                    c = set(control)
                    for cond, b in s.clauses:
                        c |= set(_idents(cond)) & names
                        visit(b, c)
                    if s.else_body:
                        visit(s.else_body, c)
                elif isinstance(s, N.For):
                    it = set(_idents(s.iterable)) & names
                    deps[s.var] |= it | set(control)
                    visit(s.body, set(control) | it | {s.var})
                elif isinstance(s, N.While):
                    visit(s.body, set(control) | (set(_idents(s.cond)) & names))
                elif isinstance(s, N.Switch):
                    c = set(control) | (set(_idents(s.subject)) & names)
                    for v, b in s.cases:
                        visit(b, c | (set(_idents(v)) & names))
                    if s.otherwise:
                        visit(s.otherwise, c)
                elif isinstance(s, N.TryCatch):
                    visit(s.body, control)
                    visit(s.catch_body, control)
        visit(f.body, set())
        return {k: sorted(v - {k}) for k, v in deps.items()}

    def _output_deps(self, fa):
        inputs = [p for p in fa.inputs if p != "~"]
        out = {}
        for o in fa.outputs:
            seen, stack = set(), [o]
            while stack:
                v = stack.pop()
                for d in fa.dependencies.get(v, []):
                    if d not in seen:
                        seen.add(d)
                        stack.append(d)
            out[o] = [p for p in inputs if p in seen or (p == o)]
        return out

    def _transitive(self, fa, start):
        seen, stack = set(), list(start)
        while stack:
            v = stack.pop()
            for d in fa.dependencies.get(v, []):
                if d not in seen:
                    seen.add(d)
                    stack.append(d)
        return seen

    # ------------------------------------------------------------------ complexity
    @staticmethod
    def _complexity(f, stmts):
        cyclo, ops = 1, 0
        for s in stmts:
            if isinstance(s, N.If):
                cyclo += len(s.clauses)
            elif isinstance(s, (N.For, N.While)):
                cyclo += 1
            elif isinstance(s, N.Switch):
                cyclo += len(s.cases)
            elif isinstance(s, N.TryCatch):
                cyclo += 1
            for e in _stmt_exprs(s)[0]:
                for n in e.walk():
                    if isinstance(n, N.Binary):
                        if n.op in ("&&", "||"):
                            cyclo += 1
                        ops += 1
                    elif isinstance(n, N.Unary) and n.op == "-":
                        ops += 1
                    elif isinstance(n, N.Index) and isinstance(n.base, N.Ident) and n.base.name in BUILTINS:
                        ops += 1

        def depth(body, d=0):
            m = d
            for s in body:
                subs = []
                if isinstance(s, N.If):
                    subs = [b for _, b in s.clauses] + ([s.else_body] if s.else_body else [])
                elif isinstance(s, (N.For, N.While)):
                    subs = [s.body]
                elif isinstance(s, N.Switch):
                    subs = [b for _, b in s.cases] + ([s.otherwise] if s.otherwise else [])
                elif isinstance(s, N.TryCatch):
                    subs = [s.body, s.catch_body]
                for b in subs:
                    m = max(m, depth(b, d + 1))
            return m
        return {"cyclomatic": cyclo, "statements": len(stmts), "max_nesting": depth(f.body),
                "operations": ops, "lines": max(0, f.end_line - f.line + 1)}

    # ------------------------------------------------------------------ control structure
    @trace("werling2011", section="4.2", concept="matlab_control_structure",
           note="heuristic: gain x error = feedback, reference terms without gain = feedforward")
    def _control(self, f, fa, stmts, functions, arrays):
        inputs = [p for p in f.params if p != "~"]
        gains = [p for p in inputs if GAIN.match(p)]
        refs = [p for p in inputs if REFERENCE.search(p) and p not in gains]
        persistent = {n for s in stmts if isinstance(s, N.Persistent) for n in s.names}
        assigns = [s for s in stmts if isinstance(s, N.Assign)]
        errors, measured = [], set()
        ref_dep = lambda name: bool(({name} | self._transitive(fa, [name])) & set(refs))  # noqa: E731
        for s in assigns:
            if len(s.targets) != 1 or not isinstance(s.targets[0], N.Ident):
                continue
            name = s.targets[0].name
            diffs = [n for n in s.value.walk() if isinstance(n, N.Binary) and n.op == "-"]
            is_err = bool(ERROR_NAME.match(name))
            for d in diffs:
                li, ri = set(_idents(d.left)), set(_idents(d.right))
                if not (li | ri) <= set(inputs) or (li | ri) & set(gains):
                    continue                # only plain differences of input signals: y - y_d
                lref, rref = bool(li & set(refs)), bool(ri & set(refs))
                lmeas = (li & set(inputs)) - set(refs) - set(gains)
                rmeas = (ri & set(inputs)) - set(refs) - set(gains)
                if (lref and rmeas) or (rref and lmeas):
                    is_err = True
                    measured |= (lmeas | rmeas)
            if is_err and name not in fa.outputs and name not in persistent:
                errors.append(name)
        errors = list(dict.fromkeys(errors))
        err_dep = {n for n in fa.variables if n in errors or (self._transitive(fa, [n]) & set(errors))}
        # integrators / differentiators on persistent states
        integrators, differentiators = [], []
        for s in assigns:
            if len(s.targets) != 1 or not isinstance(s.targets[0], N.Ident):
                continue
            name = s.targets[0].name
            if name in persistent and isinstance(s.value, N.Binary) and s.value.op in ("+", "-") and \
                    name in _idents(s.value) and (set(_idents(s.value)) & err_dep - {name}):
                integrators.append({"state": name, "line": s.line, "update": to_matlab(s.value)})
        for s in assigns:
            for n in s.value.walk():
                if isinstance(n, N.Binary) and n.op == "-":
                    li, ri = set(_idents(n.left)), set(_idents(n.right))
                    prev = (li | ri) & persistent
                    cur = (li | ri) & set(errors)
                    if prev and cur and not any(i["state"] in prev for i in integrators):
                        differentiators.append({"state": sorted(prev)[0], "signal": sorted(cur)[0], "line": s.line,
                                                "expression": to_matlab(n)})
        integ_states = {i["state"] for i in integrators}
        feedback, feedforward, other = [], [], []
        for s in assigns:
            name = ", ".join(filter(None, (_target_name(t) for t in s.targets)))
            if name in errors:
                continue                    # definitions of error signals are neither feedback nor feedforward
            for sign, term in _additive_terms(s.value):
                ids = set(_idents(term))
                g = sorted(ids & set(gains))
                e = sorted(i for i in ids if i in err_dep) or                     sorted(ids & (set(inputs) - set(refs) - set(gains))) if g else sorted(i for i in ids if i in err_dep)
                r = sorted(i for i in ids if (i in refs or (i in fa.variables and ref_dep(i))) and i not in err_dep
                           and i not in gains)
                text = ("-" if sign < 0 else "") + to_matlab(term)
                entry = {"target": name, "line": s.line, "term": text, "gains": g, "signals": e or r,
                         "latex": ("-" if sign < 0 else "") + expr_latex(term, functions, arrays)}
                if g and e:
                    kind = "feedback"
                    if ids & integ_states:
                        kind = "integral"
                    elif any(d["line"] == s.line for d in differentiators) and not (set(e) & set(errors)) or \
                            any(d["line"] == s.line for d in differentiators) and len(ids) <= 2 and \
                            not (ids & set(errors)):
                        kind = "derivative"
                    entry["kind"] = kind
                    feedback.append(entry)
                elif r and not g and not e and len(_additive_terms(s.value)) > 1:
                    feedforward.append(entry)
                elif g and r and not e:
                    entry["kind"] = "gain_feedforward"
                    feedforward.append(entry)
        # derivative terms: gain x variable computed from a differentiator expression
        diff_vars = set()
        for s in assigns:
            if any(d["line"] == s.line for d in differentiators) and isinstance(s.targets[0], N.Ident):
                diff_vars.add(s.targets[0].name)
        for t in feedback:
            ids = set(re.findall(r"[A-Za-z_]\w*", t["term"]))
            if ids & diff_vars:
                t["kind"] = "derivative"
            elif ids & integ_states:
                t["kind"] = "integral"
        has_p = any(t.get("kind") == "feedback" for t in feedback)
        has_i = bool(integrators) and any(t.get("kind") == "integral" for t in feedback)
        has_d = any(t.get("kind") == "derivative" for t in feedback)
        if has_i or has_d:
            structure = ("P" if has_p else "") + ("I" if has_i else "") + ("D" if has_d else "") + "-Regler"
        elif feedback:
            structure = "Zustands-/Fehlerrückführung"
        else:
            structure = "keine Rückführung erkannt"
        if feedforward:
            structure += " mit Vorsteuerung"
        elif feedback:
            structure += " (reine Rückführung, ohne Vorsteuerung)"
        signals = {}
        for p in inputs:
            signals[p] = "gain" if p in gains else "reference" if p in refs else \
                "measurement" if p in measured else "parameter"
        for e in errors:
            signals[e] = "error"
        for s in integ_states:
            signals[s] = "integrator"
        return {"gains": gains, "references": refs, "measurements": sorted(measured, key=inputs.index),
                "parameters": [p for p in inputs if signals[p] == "parameter"], "errors": errors,
                "feedback_terms": feedback, "feedforward_terms": feedforward, "integrators": integrators,
                "differentiators": differentiators, "has_feedforward": bool(feedforward),
                "has_feedback": bool(feedback), "structure": structure, "signals": signals}


@trace("aho2006", section="9.2", concept="matlab_analysis", note="reaching definitions / data dependence")
def analyze(source, input_types=None):
    """Analyze an MFile, a path or MATLAB source text -> FileAnalysis."""
    if isinstance(source, N.MFile):
        mfile = source
    elif isinstance(source, Path) or (isinstance(source, str) and source.endswith(".m") and "\n" not in source):
        mfile = parse_file(source)
    else:
        from .parser import parse
        mfile = parse(source)
    an = _Analyzer(mfile, input_types)
    funcs = [an.function(f) for f in mfile.all_functions()]
    funcs = [f for f in funcs if f is not None]
    call_graph = {f.name: f.calls for f in funcs}
    if mfile.kind == "script":
        call_graph["<script>"] = sorted({n.base.name for s in mfile.script for n in s.walk()
                                         if isinstance(n, N.Index) and isinstance(n.base, N.Ident)
                                         and n.base.name in an.local})
    builtins_used = sorted({b for f in funcs for b in f.builtins})
    equations = [dict(e, function=f.name) for f in funcs for e in f.equations]
    for f in funcs:
        for v in f.unused_variables:
            an.diagnostics.append(Diagnostic("info", f"Variable '{v}' wird zugewiesen, aber nicht verwendet "
                                                     f"(in {f.name})", f.variables[v].defs[0] if
                                             f.variables[v].defs else f.line, target="analysis"))
        for v in f.unused_inputs:
            an.diagnostics.append(Diagnostic("info", f"Eingang '{v}' von {f.name} wird nicht verwendet", f.line,
                                             target="analysis"))
    return FileAnalysis(mfile.path, mfile.kind, mfile.main.doc if mfile.main else mfile.doc, funcs, call_graph,
                        builtins_used, equations, an.diagnostics)


# ----------------------------------------------------------------------------- DOT export
_SIGNAL_COLORS = {"reference": "#3fb950", "gain": "#e3a33b", "measurement": "#3987e5", "parameter": "#9a9ca3",
                  "error": "#f85149", "integrator": "#a371f7"}


def _q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dataflow_dot(fa):
    """Graphviz DOT of the data-flow graph of one function (inputs -> intermediates -> outputs)."""
    lines = [f"digraph {_q(fa.name)} {{", "  rankdir=LR;", '  node [fontname="Helvetica", fontsize=10];',
             f"  label={_q(f'Datenfluss {fa.name}')}; labelloc=t;"]
    eq_of = {}
    for a in fa.assignments:
        for t in a["target"].split(", "):
            if a["equations"]:
                eq_of.setdefault(t, []).extend(a["equations"])
    for name, v in fa.variables.items():
        signal = fa.control.get("signals", {}).get(name, "")
        color = _SIGNAL_COLORS.get(signal, "#c8c8c8")
        shape = "box" if v.role == "input" else "doubleoctagon" if v.role in ("output", "inout") else \
            "box3d" if v.role == "persistent" else "ellipse"
        label = name + (f"\\n{', '.join(dict.fromkeys(eq_of[name]))}" if name in eq_of else "")
        lines.append(f"  {_q(name)} [shape={shape}, style=filled, fillcolor={_q(color)}, label={_q(label)}];")
    if fa.inputs:
        lines.append("  { rank=source; " + " ".join(_q(p) for p in fa.inputs if p in fa.variables) + " }")
    if fa.outputs:
        lines.append("  { rank=sink; " + " ".join(_q(o) for o in fa.outputs if o in fa.variables) + " }")
    for target, deps in fa.dependencies.items():
        for d in deps:
            lines.append(f"  {_q(d)} -> {_q(target)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def callgraph_dot(file_analysis):
    lines = ["digraph calls {", "  rankdir=LR;", '  node [fontname="Helvetica", fontsize=10];']
    for f in file_analysis.functions:
        lines.append(f"  {_q(f.name)} [shape=box, style=filled, fillcolor=\"#3987e5\", fontcolor=white];")
        for c in f.calls:
            lines.append(f"  {_q(f.name)} -> {_q(c)};")
        for b in f.builtins:
            lines.append(f"  {_q('builtin:' + b)} [label={_q(b)}, shape=ellipse, style=dashed];")
            lines.append(f"  {_q(f.name)} -> {_q('builtin:' + b)} [style=dashed];")
    lines.append("}")
    return "\n".join(lines) + "\n"
