"""Common machinery of the code generators (Python, C++17, Rust).

A generator translates the entry function of an MFile and all local functions it calls.
Types come from ``typeinfer``; every construct a target cannot express faithfully is
reported as a :class:`Diagnostic` (severity ``error``) with line/column instead of being
translated silently wrong. The generated text keeps the MATLAB comments, the help text and
the equation references.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .. import nodes as N
from ..builtins import BUILTINS
from ..errors import Diagnostic
from ..parser import parse_file
from ..typeinfer import BOOL, SCALAR, UNKNOWN, TypeInference

EQUATION = re.compile(r"\(\s*((?:[A-Z]\.?)?\d+(?:\.\d+)*[a-z]?)\s*\)")


@dataclass
class GeneratedCode:
    target: str
    files: dict                      # file name -> source text
    diagnostics: list
    entry: str = ""
    signature: dict = field(default_factory=dict)

    @property
    def ok(self):
        return not any(d.severity == "error" for d in self.diagnostics)

    @property
    def errors(self):
        return [d for d in self.diagnostics if d.severity == "error"]

    def write(self, out_dir):
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for name, text in self.files.items():
            p = out / name
            p.write_text(text, encoding="utf-8", newline="\n")
            paths.append(p)
        return paths

    def report(self):
        return "\n".join(str(d) for d in self.diagnostics)


class Unsupported(Exception):
    def __init__(self, message, node=None):
        super().__init__(message)
        self.message, self.node = message, node


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def camel(name):
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\W]+", name) if p)


class BaseGenerator:
    target = ""
    KEYWORDS: set = set()
    COMMENT = "#"
    INDENT = "    "

    def __init__(self, mfile, function=None, input_types=None, **options):
        if isinstance(mfile, (str, Path)):
            mfile = parse_file(mfile)
        self.mfile = mfile
        self.entry = mfile.function(function)
        self.options = options
        self.ti = TypeInference(mfile, input_types)
        self.local = {f.name: f for f in mfile.all_functions()}
        self.diags: list[Diagnostic] = []
        self.helpers: set = set()
        self.env = {}
        self.func = None
        self._emitted_comments = set()

    # ------------------------------------------------------------------ diagnostics
    def diag(self, severity, message, node=None):
        d = Diagnostic(severity, message, getattr(node, "line", 0) or 0, getattr(node, "col", 0) or 0, self.target)
        if not any(x.message == d.message and x.line == d.line for x in self.diags):
            self.diags.append(d)

    def unsupported(self, message, node=None):
        raise Unsupported(message, node)

    # ------------------------------------------------------------------ functions to translate
    def collect(self):
        """[(Function, FunctionTypes)] for the entry and all called local functions."""
        out, seen = [], {}
        queue = [(self.entry, self.ti.infer_entry(self.entry))]
        while queue:
            f, ft = queue.pop(0)
            if f.name in seen:
                if seen[f.name].inputs != ft.inputs:
                    self.diag("error", f"Funktion '{f.name}' wird mit unterschiedlichen Argumenttypen aufgerufen "
                                       f"({', '.join(map(str, seen[f.name].inputs))} / "
                                       f"{', '.join(map(str, ft.inputs))})", f)
                continue
            seen[f.name] = ft
            out.append((f, ft))
            if f.nested:
                for nf in f.nested:
                    self.diag("error", f"verschachtelte Funktion '{nf.name}' (gemeinsamer Workspace) wird nicht "
                                       f"übersetzt", nf)
            for node in _walk(f.body):
                if isinstance(node, (N.Index, N.Ident)):
                    name = node.base.name if isinstance(node, N.Index) and isinstance(node.base, N.Ident) else \
                        node.name if isinstance(node, N.Ident) else None
                    if name in self.local and name not in ft.env and self.local[name].parent is None:
                        args = node.args if isinstance(node, N.Index) else []
                        ts = tuple(self.ti.expr(a, ft.env) for a in args)
                        callee = self.local[name]
                        ts = (ts + tuple(SCALAR for _ in callee.params))[:len(callee.params)]
                        ts = tuple(SCALAR if t.kind == "bool" else t for t in ts)
                        queue.append((callee, self.ti.infer(callee, ts)))
        return out

    # ------------------------------------------------------------------ helpers for subclasses
    def name(self, n):
        return n + "_" if n in self.KEYWORDS else n

    def t(self, e):
        try:
            return self.ti.expr(e, self.env)
        except Exception:  # pragma: no cover - defensive
            return UNKNOWN

    def is_scalar(self, e):
        return self.t(e).is_scalar

    def is_bool(self, e):
        return self.t(e) == BOOL

    def callee_name(self, e):
        if isinstance(e, N.Index) and isinstance(e.base, N.Ident) and e.base.name not in self.env:
            return e.base.name
        if isinstance(e, N.Ident) and e.name not in self.env:
            return e.name
        return None

    def comment_lines(self, text, indent):
        out = []
        for line in text.split("\n"):
            line = line.rstrip()
            out.append(f"{indent}{self.COMMENT} {line}".rstrip() if line else f"{indent}{self.COMMENT}")
        return out

    def leading(self, s, indent):
        out = []
        for c in s.leading:
            out += self.comment_lines(c, indent)
        return out

    def trailing(self, s):
        return f"  {self.COMMENT} {s.comment}" if s.comment else ""

    def equations_of(self, f):
        eqs = []
        for s in N.body_statements(f.body):
            eqs += EQUATION.findall(s.comment)
        return list(dict.fromkeys(eqs))

    # statement dispatch with error capture
    def block(self, body, indent):
        lines = []
        for s in body:
            lines += self.leading(s, indent)
            try:
                stmt_lines = self.stmt(s, indent)
            except Unsupported as u:
                self.diag("error", u.message, u.node or s)
                stmt_lines = [f"{indent}{self.COMMENT} NICHT ÜBERSETZT: {u.message}"]
            if stmt_lines and s.comment and not isinstance(s, (N.If, N.For, N.While, N.Switch, N.TryCatch)):
                stmt_lines[-1] += self.trailing(s)
            elif stmt_lines and s.comment:
                stmt_lines[0] += self.trailing(s)
            lines += stmt_lines
        return lines

    def stmt(self, s, indent):  # pragma: no cover - abstract
        raise NotImplementedError

    # common checks
    def check_builtin(self, name, node, supported):
        if name in self.local:
            return
        if name not in supported:
            if name in BUILTINS:
                self.unsupported(f"Built-in '{name}' wird für {self.LANGUAGE_NAME} nicht unterstützt", node)
            self.unsupported(f"unbekannte Funktion '{name}' (nicht lokal definiert und kein Built-in)", node)

    LANGUAGE_NAME = ""


def _walk(body):
    for s in body:
        yield from s.walk()


def first_assignments(f):
    """Variables whose first occurrence is an unconditional top-level 'x = expr' (inline declaration)."""
    seen, inline = set(), {}
    for idx, s in enumerate(f.body):
        names_used = {n.name for n in s.walk() if isinstance(n, N.Ident)}
        if isinstance(s, N.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], N.Ident):
            name = s.targets[0].name
            rhs = {n.name for n in s.value.walk() if isinstance(n, N.Ident)}
            if name not in seen and name not in rhs:
                inline[name] = s
            seen |= rhs | {name}
        elif isinstance(s, N.Assign) and s.multi and all(isinstance(t, (N.Ident, N.Placeholder)) for t in s.targets):
            rhs = {n.name for n in s.value.walk() if isinstance(n, N.Ident)}
            for t in s.targets:
                if isinstance(t, N.Ident) and t.name not in seen and t.name not in rhs:
                    inline.setdefault(t.name, s)
            seen |= rhs | {t.name for t in s.targets if isinstance(t, N.Ident)}
        else:
            seen |= names_used
            for st in N.body_statements([s]):
                if isinstance(st, N.For):
                    seen.add(st.var)
    return inline


def assigned_count(f):
    counts = {}
    for s in N.body_statements(f.body):
        if isinstance(s, N.Assign):
            for t in s.targets:
                b = t
                while isinstance(b, (N.Index, N.Field, N.CellIndex, N.DynField)):
                    b = b.base
                if isinstance(b, N.Ident):
                    counts[b.name] = counts.get(b.name, 0) + (1 if b is t else 2)
        elif isinstance(s, N.For):
            counts[s.var] = counts.get(s.var, 0) + 2
    return counts


def index_mutated(f):
    out = set()
    for s in N.body_statements(f.body):
        if isinstance(s, N.Assign):
            for t in s.targets:
                if isinstance(t, (N.Index, N.CellIndex, N.Field)):
                    b = t
                    while not isinstance(b, (N.Ident, N.Placeholder)):
                        b = b.base
                    if isinstance(b, N.Ident):
                        out.add(b.name)
    return out


def uses_name(f, name):
    return any(isinstance(n, N.Ident) and n.name == name for n in _walk(f.body))


def int_literal(e):
    if isinstance(e, N.Number) and not isinstance(e.value, complex) and float(e.value).is_integer():
        return int(e.value)
    if isinstance(e, N.Unary) and e.op == "-" and int_literal(e.operand) is not None:
        return -int_literal(e.operand)
    return None
