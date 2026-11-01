"""Shared translation logic of the statically typed targets (C++17, Rust).

Supported subset: double scalars, logical scalars, real matrices/vectors (small generated
``Mat`` class, column-major, 1-based accessors), if/elseif/else, for over ranges and row
vectors, while, numeric switch, break/continue/return, local functions with several outputs,
persistent variables of the entry function (explicit state struct), anonymous scalar
functions, fprintf/disp/error with literal format strings. Everything else is reported as a
diagnostic error.
"""

from __future__ import annotations

import re

from .. import nodes as N
from ..typeinfer import BOOL, SCALAR
from .base import (
    BaseGenerator,
    Unsupported,
    assigned_count,
    camel,
    first_assignments,
    index_mutated,
    int_literal,
    uses_name,
)

P_OR, P_AND, P_BOR, P_BAND, P_EQ, P_REL, P_ADD, P_MUL, P_UNARY, P_POST, P_ATOM = 1, 2, 3, 5, 6, 7, 9, 10, 11, 14, 15
_UNARY_FUNCS = {"sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "log10", "log2",
                "sqrt", "abs", "floor", "ceil", "round", "fix", "sign"}
_SPEC = re.compile(r"%%|%([-+ #0]*)(\d+)?(?:\.(\d+))?([diouxXfFeEgGcs])")


class NativeGenerator(BaseGenerator):
    """Subclasses define the syntax hooks (see CppGenerator / RustGenerator)."""

    STATE_ARG = "state"

    # ------------------------------------------------------------------ setup per function
    def setup_function(self, f, ft):
        self.func, self.env, self.ft = f, dict(ft.env), ft
        self.persistent = {n for s in N.body_statements(f.body) if isinstance(s, N.Persistent) for n in s.names}
        if self.persistent and f is not self.entry:
            self.diag("error", f"persistente Variablen in der lokalen Funktion '{f.name}' werden nicht übersetzt "
                               f"(nur in der Hauptfunktion)", f)
        for s in N.body_statements(f.body):
            if isinstance(s, N.Global):
                self.diag("error", "globale Variablen werden nicht übersetzt", s)
        for name in ("nargin", "nargout", "varargin", "varargout"):
            if uses_name(f, name) or name in f.params or name in f.outputs:
                self.diag("error", f"'{name}' wird nicht übersetzt", f)
        self.counts = assigned_count(f)
        self.mutated = index_mutated(f)
        has_return = any(isinstance(s, N.Return) for s in N.body_statements(f.body))
        self.inline = {k: v for k, v in first_assignments(f).items()
                       if not (has_return and k in f.outputs) and k not in self.persistent and k not in f.params}
        loop_vars = {s.var for s in N.body_statements(f.body) if isinstance(s, N.For)}
        self.loop_vars = loop_vars
        locals_ = [n for n in self.env if n not in f.params and n not in self.persistent]
        for o in f.outputs:
            if o not in locals_ and o not in f.params:
                locals_.append(o)
        self.hoisted = [n for n in locals_ if n not in self.inline and not self._only_loop_var(f, n)]
        self.declared = set(f.params) | set(self.hoisted)
        self.params_reassigned = {p for p in f.params if self.counts.get(p, 0) > 0}

    @staticmethod
    def _only_loop_var(f, name):
        stmts = list(N.body_statements(f.body))
        if not any(isinstance(s, N.For) and s.var == name for s in stmts):
            return False
        inside = set()
        for s in stmts:
            if isinstance(s, N.For) and s.var == name:
                for x in N.body_statements(s.body):
                    inside.add(id(x))
        for s in stmts:
            if id(s) in inside or (isinstance(s, N.For) and s.var == name):
                continue
            if isinstance(s, (N.If, N.For, N.While, N.Switch, N.TryCatch)):
                exprs = [c for c, _ in s.clauses] if isinstance(s, N.If) else \
                    [s.iterable] if isinstance(s, N.For) else [s.cond] if isinstance(s, N.While) else \
                    [s.subject] if isinstance(s, N.Switch) else []
                if any(isinstance(n, N.Ident) and n.name == name for e in exprs for n in e.walk()):
                    return False
                continue
            if any(isinstance(n, N.Ident) and n.name == name for n in s.walk()):
                return False
        return True

    def vtype(self, name, node=None):
        t = self.env.get(name, SCALAR)
        if t.kind in ("scalar", "bool", "array", "func"):
            return t
        if t.kind in ("none", "unknown"):
            return SCALAR
        self.unsupported(f"Variable '{name}' hat den Typ '{t}', der nach {self.LANGUAGE_NAME} nicht übersetzt wird",
                         node)

    def kind(self, e):
        t = self.t(e)
        if t.is_array:
            return "mat"
        if t.kind == "bool":
            return "bool"
        if t.kind in ("scalar", "unknown", "none"):
            return "scalar"
        if t.kind == "func":
            return "func"
        if t.kind == "string":
            self.unsupported("Zeichenketten werden nur als Literal in fprintf/disp/error übersetzt", e)
        self.unsupported(f"Werte vom Typ '{t}' werden nach {self.LANGUAGE_NAME} nicht übersetzt", e)

    # ------------------------------------------------------------------ expression helpers
    def code(self, e):
        return self.ex(e)[0]

    def p(self, e, minprec):
        c, prec = self.ex(e)
        return f"({c})" if prec < minprec else c

    def num(self, e, minprec=P_ATOM):
        k = self.kind(e)
        if k == "bool":
            return self.bool_to_num(self.code(e))
        if k == "mat":
            self.unsupported("Matrix an einer Stelle, an der ein Skalar erwartet wird", e)
        return self.p(e, minprec)

    def boolean(self, e, minprec=P_ATOM):
        k = self.kind(e)
        if k == "bool":
            return self.p(e, minprec)
        if k == "mat":
            self.helpers.add("mat")
            return self.mat_truth(self.mat_arg(e))
        c = self.p(e, P_EQ + 1)
        out = f"{c} != {self.flit(0)}"
        return f"({out})" if minprec > P_EQ else out

    def flit(self, v):
        v = float(v)
        if v.is_integer() and abs(v) < 1e16:
            return f"{int(v)}.0"
        r = repr(v)
        return r if ("." in r or "e" in r or "inf" in r or "nan" in r) else r + ".0"

    def number(self, e):
        if isinstance(e.value, complex):
            self.unsupported("komplexe Zahlen werden nicht übersetzt", e)
        text = (e.text or "").lower().replace("d", "e")
        if not text or text.endswith("i"):
            return self.flit(e.value)
        if text.startswith("."):
            text = "0" + text
        if "." not in text and "e" not in text:
            text = str(int(text)) + ".0"
        elif "e" in text and "." not in text.split("e")[0] and self.target == "rust":
            mant, exp = text.split("e")
            text = f"{mant}.0e{exp}"
        elif text.endswith("."):
            text += "0"
        return text

    def ex(self, e):
        if isinstance(e, N.Number):
            return self.number(e), P_ATOM
        if isinstance(e, N.String):
            self.unsupported("Zeichenketten werden nur als Literal in fprintf/disp/error übersetzt", e)
        if isinstance(e, N.Ident):
            return self.ident(e)
        if isinstance(e, N.Binary):
            return self.binary(e)
        if isinstance(e, N.Unary):
            k = self.kind(e.operand)
            if e.op == "+":
                return self.ex(e.operand)
            if e.op == "-":
                if k == "mat":
                    self.helpers.add("mat")
                    return f"mlab::neg({self.mat_arg(e.operand)})", P_POST
                return f"-{self.num(e.operand, P_UNARY)}", P_UNARY
            if k == "mat":
                self.unsupported("logische Operationen auf Matrizen werden nicht übersetzt", e)
            return f"!{self.boolean(e.operand, P_UNARY)}", P_UNARY
        if isinstance(e, N.Postfix):
            if self.kind(e.operand) != "mat":
                return self.ex(e.operand)
            self.helpers.add("mat")
            return f"mlab::transpose({self.mat_arg(e.operand)})", P_POST
        if isinstance(e, N.Matrix):
            return self.matrix(e)
        if isinstance(e, N.Index):
            return self.index(e)
        if isinstance(e, N.AnonFunc):
            return self.lambda_expr(e), P_ATOM
        if isinstance(e, N.Range):
            self.unsupported("Bereiche a:b werden nur als for-Schleifenbereich übersetzt", e)
        if isinstance(e, (N.CellArray, N.CellIndex)):
            self.unsupported("Zellen werden nicht übersetzt", e)
        if isinstance(e, (N.Field, N.DynField)):
            self.unsupported("Structs werden nicht übersetzt", e)
        if isinstance(e, N.End):
            return self.end_value(e), P_POST
        if isinstance(e, N.FuncHandle):
            self.unsupported("Function Handles (@name) werden nicht übersetzt", e)
        self.unsupported(f"Ausdruck {type(e).__name__} wird nicht übersetzt", e)

    def end_value(self, e):
        ctx = getattr(self, "_end_ctx", None)
        if ctx is None:
            self.unsupported("'end' außerhalb eines Index", e)
        base, k, n = ctx
        return self.mat_end(base, k, n)

    def ident(self, e):
        n = e.name
        if n in self.persistent:
            return self.persistent_read(n), P_POST
        if n in self.env or n in self.func.params:
            return self.var_ref(n), P_ATOM
        consts = self.constants()
        if n in consts:
            return consts[n], P_ATOM
        if n in self.local:
            return self.call_local(n, [], e)
        return self.builtin(n, [], e)

    def binary(self, e):
        op, l, r = e.op, e.left, e.right
        kl, kr = self.kind(l), self.kind(r)
        if op in ("&&", "||", "&", "|"):
            if "mat" in (kl, kr):
                self.unsupported("logische Operationen auf Matrizen werden nicht übersetzt", e)
            sym, prec = ("&&", P_AND) if op in ("&&", "&") else ("||", P_OR)
            return f"{self.boolean(l, prec)} {sym} {self.boolean(r, prec + 1)}", prec
        if op in ("==", "~=", "<", "<=", ">", ">="):
            if "mat" in (kl, kr):
                self.unsupported("Vergleiche von Matrizen werden nicht übersetzt", e)
            sym = "!=" if op == "~=" else op
            prec = P_EQ if sym in ("==", "!=") else P_REL
            if kl == "bool" and kr == "bool" and sym in ("==", "!="):
                return f"{self.p(l, P_REL + 1)} {sym} {self.p(r, P_REL + 1)}", prec
            return f"{self.num(l, P_ADD)} {sym} {self.num(r, P_ADD)}", prec
        if "mat" in (kl, kr):
            return self.mat_binary(e, kl, kr)
        if op in ("+", "-"):
            return f"{self.num(l, P_ADD)} {op} {self.num(r, P_ADD + 1)}", P_ADD
        if op in ("*", ".*"):
            return f"{self.num(l, P_MUL)} * {self.num(r, P_MUL + 1)}", P_MUL
        if op in ("/", "./"):
            return f"{self.num(l, P_MUL)} / {self.num(r, P_MUL + 1)}", P_MUL
        if op in ("\\", ".\\"):
            return f"{self.num(r, P_MUL)} / {self.num(l, P_MUL + 1)}", P_MUL
        if op in ("^", ".^"):
            return self.pow_code(l, r), P_POST
        self.unsupported(f"Operator '{op}' wird nicht übersetzt", e)

    def mat_binary(self, e, kl, kr):
        self.helpers.add("mat")
        op = e.op
        a, b = self.mat_arg(e.left), self.mat_arg(e.right)
        both = kl == "mat" and kr == "mat"
        if op == "+":
            fn = "add"
        elif op == "-":
            fn = "sub"
        elif op == ".*" or (op == "*" and not both):
            fn = "emul"
        elif op == "*":
            fn = "matmul"
        elif op == "./" or (op == "/" and kr != "mat"):
            fn = "ediv"
        elif op == ".^" or (op == "^" and kl != "mat"):
            fn = "epow"
        elif op == ".\\" or (op == "\\" and kl != "mat"):
            return f"mlab::ediv({b}, {a})", P_POST
        else:
            self.unsupported(f"Matrixoperator '{op}' (Division/Potenz von Matrizen) wird nicht übersetzt", e)
        return f"mlab::{fn}({a}, {b})", P_POST

    def matrix(self, e):
        if not e.rows:
            self.helpers.add("mat")
            return self.mat_empty(), P_POST
        self.helpers.add("mat")
        kinds = [[self.kind(x) for x in row] for row in e.rows]
        if all(k != "mat" for row in kinds for k in row):
            widths = {len(r) for r in e.rows}
            if len(widths) != 1:
                self.unsupported("Matrixliteral mit unterschiedlich langen Zeilen", e)
            vals = ", ".join(self.num(x, P_OR) for row in e.rows for x in row)
            return self.mat_from_rows(len(e.rows), len(e.rows[0]), vals), P_POST
        rows = []
        for row in e.rows:
            rows.append(self.mat_hcat([self.mat_arg(x) for x in row]))
        return self.mat_vcat(rows), P_POST

    def index(self, e):
        name = self.callee_name(e)
        if name is not None:
            if name in self.local:
                return self.call_local(name, e.args, e)
            return self.builtin(name, e.args, e)
        bt = self.t(e.base)
        if bt.kind == "func":
            return self.call_lambda(e), P_POST
        if not isinstance(e.base, N.Ident):
            self.unsupported("Indizierung eines Ausdrucks wird nicht übersetzt", e)
        if bt.is_scalar:
            if all(int_literal(a) == 1 for a in e.args):
                return self.ex(e.base)
        if not bt.is_array:
            self.unsupported(f"Indizierung von '{e.base.name}' wird nicht übersetzt", e)
        if len(e.args) not in (1, 2) or any(isinstance(a, N.Colon) or not self.t(a).is_scalar for a in e.args):
            self.unsupported("nur skalare Indizes werden übersetzt (keine Bereiche, ':' oder logischen Indizes)", e)
        self.helpers.add("mat")
        return self.mat_get(e.base.name, self.index_codes(e.base.name, e.args)), P_POST

    def index_codes(self, base, args):
        out = []
        for k, a in enumerate(args):
            saved = getattr(self, "_end_ctx", None)
            self._end_ctx = (base, k, len(args))
            try:
                out.append(self.num(a, P_OR))
            finally:
                self._end_ctx = saved
        return out

    # ------------------------------------------------------------------ builtins
    def builtin(self, name, args, node):
        kinds = [self.kind(a) for a in args]
        scalar = all(k != "mat" for k in kinds)
        consts = self.constants()
        if name in consts and not args:
            return consts[name], P_ATOM
        if name in _UNARY_FUNCS and len(args) == 1:
            if scalar:
                return self.scalar_func(name, args[0]), P_POST
            self.helpers.add("mat")
            return f"mlab::{self.mat_func_name(name)}({self.mat_arg(args[0])})", P_POST
        if name in ("atan2", "hypot", "mod", "rem", "max", "min", "power") and len(args) == 2:
            if not scalar:
                self.unsupported(f"'{name}' mit Matrixargumenten wird nicht übersetzt", node)
            return self.scalar_func2(name, args[0], args[1]), P_POST
        if name in ("max", "min") and len(args) == 3 and isinstance(args[1], N.Matrix) and not args[1].rows:
            self.unsupported(f"'{name}' über Dimensionen wird nicht übersetzt", node)
        if name in ("sum", "prod", "mean", "max", "min", "norm", "numel", "length", "isempty") and len(args) == 1:
            if kinds[0] != "mat":
                if name in ("numel", "length"):
                    return self.flit(1), P_ATOM
                if name == "isempty":
                    if args[0].__class__ is N.Ident and args[0].name in self.persistent:
                        return self.persistent_isempty(args[0].name), P_UNARY
                    return "false", P_ATOM
                if name == "norm":
                    return self.scalar_func("abs", args[0]), P_POST
                return self.ex(args[0])
            t = self.t(args[0])
            if name in ("sum", "prod", "mean", "max", "min") and not (t.is_vector or None in (t.rows, t.cols)):
                self.unsupported(f"'{name}' einer Matrix (spaltenweise) wird nicht übersetzt", node)
            self.helpers.add("mat")
            if name == "isempty":
                return f"{self.mat_method(args[0], 'numel')} == {self.flit(0)}", P_EQ
            if name in ("numel", "length"):
                return self.mat_method(args[0], name), P_POST
            return f"mlab::{name}({self.mat_arg(args[0])})", P_POST
        if name == "size" and len(args) == 2:
            d = int_literal(args[1])
            if kinds[0] != "mat":
                return self.flit(1), P_ATOM
            if d not in (1, 2):
                self.unsupported("size(x, d) nur mit d = 1 oder 2", node)
            self.helpers.add("mat")
            return self.mat_method(args[0], "nrows" if d == 1 else "ncols"), P_POST
        if name in ("zeros", "ones", "eye") and len(args) in (1, 2):
            if not scalar:
                self.unsupported(f"{name}(size(...)) wird nicht übersetzt", node)
            self.helpers.add("mat")
            r = self.num(args[0], P_OR)
            c = self.num(args[1], P_OR) if len(args) == 2 else r
            return self.mat_ctor(name, r, c), P_POST
        if name in ("zeros", "ones") and not args:
            return self.flit(0 if name == "zeros" else 1), P_ATOM
        if name in ("deg2rad", "rad2deg") and len(args) == 1 and scalar:
            f = f"({consts['pi']} / 180.0)" if name == "deg2rad" else f"(180.0 / {consts['pi']})"
            return f"{self.num(args[0], P_MUL)} * {f}", P_MUL
        if name in ("isnan", "isinf", "isfinite") and len(args) == 1 and scalar:
            return self.scalar_pred(name, args[0]), P_POST
        if name == "wrapToPi" and len(args) == 1 and scalar:
            self.helpers.add("wrap")
            return f"mlab::wrap_to_pi({self.num(args[0], P_OR)})", P_POST
        if name in ("disp", "fprintf", "error", "warning", "sprintf"):
            self.unsupported(f"'{name}' kann nicht als Ausdruck verwendet werden", node)
        if name in self.local:
            return self.call_local(name, args, node)
        from ..builtins import BUILTINS
        if name in BUILTINS:
            self.unsupported(f"Built-in '{name}' (mit {len(args)} Argument(en)) wird nach {self.LANGUAGE_NAME} "
                             f"nicht übersetzt", node)
        self.unsupported(f"unbekannte Funktion oder Variable '{name}'", node)

    # ------------------------------------------------------------------ statements
    def stmt(self, s, ind):
        if isinstance(s, N.Assign):
            return self.assign(s, ind)
        if isinstance(s, N.ExprStmt):
            return self.expr_stmt(s, ind)
        if isinstance(s, N.If):
            out = []
            for k, (cond, body) in enumerate(s.clauses):
                out.append(self.if_head(self.boolean(cond, P_OR), ind, first=k == 0))
                out += self.block(body, ind + self.INDENT)
            if s.else_body:
                out.append(self.else_head(ind))
                out += self.block(s.else_body, ind + self.INDENT)
            out.append(f"{ind}}}")
            return out
        if isinstance(s, N.For):
            return self.for_stmt(s, ind)
        if isinstance(s, N.While):
            return [self.while_head(self.boolean(s.cond, P_OR), ind)] + self.block(s.body, ind + self.INDENT) + \
                [f"{ind}}}"]
        if isinstance(s, N.Switch):
            return self.switch(s, ind)
        if isinstance(s, N.Break):
            return [f"{ind}break;"]
        if isinstance(s, N.Continue):
            return [f"{ind}continue;"]
        if isinstance(s, N.Return):
            return [f"{ind}{self.return_stmt()}"]
        if isinstance(s, N.Persistent):
            return [f"{ind}{self.COMMENT} persistent {' '.join(s.names)} -> {self.STATE_ARG}.<name>"]
        if isinstance(s, N.Global):
            self.unsupported("globale Variablen werden nicht übersetzt", s)
        if isinstance(s, N.Command):
            self.diag("info", f"MATLAB-Befehl '{s.name}' wird ignoriert", s)
            return [f"{ind}{self.COMMENT} MATLAB command omitted: {s.name} {' '.join(s.args)}".rstrip()]
        if isinstance(s, N.TryCatch):
            self.unsupported("try/catch wird nicht übersetzt", s)
        self.unsupported(f"Anweisung {type(s).__name__} wird nicht übersetzt", s)

    def for_stmt(self, s, ind):
        it = s.iterable
        var = self.name(s.var)
        if isinstance(it, N.Range):
            self.helpers.add("colon")
            st = self.flit(1) if it.step is None else self.num(it.step, P_OR)
            head = self.for_range_head(var, self.num(it.start, P_OR), st, self.num(it.stop, P_OR), ind, s.var)
        else:
            t = self.t(it)
            if t.is_array and t.rows == 1 and isinstance(it, N.Ident):
                self.helpers.add("mat")
                head = self.for_vec_head(var, self.var_ref(it.name), ind, s.var)
            else:
                self.unsupported("for-Schleifen nur über Bereiche a:s:b oder Zeilenvektor-Variablen", s)
        return [head] + self.block(s.body, ind + self.INDENT) + [f"{ind}}}"]

    def switch(self, s, ind):
        if self.kind(s.subject) == "mat":
            self.unsupported("switch über Matrizen wird nicht übersetzt", s)
        subj = self.num(s.subject, P_ADD)
        out = []
        for k, (value, body) in enumerate(s.cases):
            vals = [x for row in value.rows for x in row] if isinstance(value, N.CellArray) else [value]
            cond = " || ".join(f"{subj} == {self.num(v, P_ADD)}" for v in vals)
            out.append(self.if_head(cond, ind, first=k == 0))
            out += self.block(body, ind + self.INDENT)
        if s.otherwise:
            if s.cases:
                out.append(self.else_head(ind))
                out += self.block(s.otherwise, ind + self.INDENT)
            else:
                return self.block(s.otherwise, ind)
        if s.cases:
            out.append(f"{ind}}}")
        return out

    def expr_stmt(self, s, ind):
        e = s.expr
        name = self.callee_name(e)
        args = e.args if isinstance(e, N.Index) else []
        if name in ("disp", "fprintf", "error", "warning"):
            return [ind + l for l in self.output_stmt(name, args, e)]
        if name in ("clc", "clear", "close", "format", "figure", "hold", "drawnow", "tic"):
            return [f"{ind}{self.COMMENT} MATLAB {name} omitted"]
        if name in self.local:
            return [f"{ind}{self.call_local(name, args, e)[0]};"]
        if not s.suppress:
            self.unsupported("Ausgabe ohne Semikolon wird nicht übersetzt (bitte disp/fprintf verwenden)", s)
        return [f"{ind}{self.code(e)};"]

    def output_stmt(self, name, args, node):
        if name == "disp":
            if len(args) != 1:
                self.unsupported("disp mit einem Argument erwartet", node)
            a = args[0]
            if isinstance(a, N.String):
                return [self.print_literal(a.value + "\n")]
            if self.kind(a) == "mat":
                self.helpers.add("mat")
                return [self.disp_mat(self.mat_arg(a))]
            return [self.print_format("%g\n", [self.num(a, P_OR)])]
        if name == "fprintf" and args and not isinstance(args[0], N.String) and len(args) > 1:
            args = args[1:]
        if not args or not isinstance(args[0], N.String):
            self.unsupported(f"{name}: das Format muss ein String-Literal sein", node)
        fmt, rest = args[0].value, args[1:]
        vals = []
        for a in rest:
            if isinstance(a, N.String):
                vals.append(("str", a.value))
            elif self.kind(a) == "mat":
                self.unsupported(f"{name}: Matrixargumente werden nicht übersetzt", a)
            else:
                vals.append(("num", self.num(a, P_OR)))
        specs = [m for m in _SPEC.finditer(fmt) if m.group(0) != "%%"]
        if len(specs) != len(vals):
            self.unsupported(f"{name}: Anzahl der Formatangaben ({len(specs)}) und Argumente ({len(vals)}) "
                             f"muss übereinstimmen (Format-Recycling wird nicht übersetzt)", node)
        for m, (kind, _) in zip(specs, vals):
            if (m.group(4) == "s") != (kind == "str"):
                self.unsupported(f"{name}: %s nur für String-Literale", node)
        text = fmt.replace("\\n", "\n").replace("\\t", "\t")
        if name == "fprintf":
            return [self.print_format(text, vals)]
        if name == "warning":
            return [self.print_format("Warnung: " + text + "\n", vals)]
        return [self.raise_error(text, vals)]

    def assign(self, s, ind):
        if s.multi or len(s.targets) > 1:
            return self.multi_assign(s, ind)
        tg, value = s.targets[0], s.value
        if isinstance(tg, N.Ident):
            name = tg.name
            if name in self.persistent:
                return [f"{ind}{self.persistent_write(name, self.value_code(value, self.vtype(name, s)))}"]
            t = self.vtype(name, s)
            code = self.value_code(value, t)
            if name in self.inline and self.inline[name] is s and name not in self.declared:
                self.declared.add(name)
                mutable = self.counts.get(name, 0) > 1 or name in self.mutated or name in self.loop_vars
                return [f"{ind}{self.declare(name, t, code, mutable, value)}"]
            return [f"{ind}{self.var_ref(name, lhs=True)} = {code};"]
        if isinstance(tg, N.Index):
            if not isinstance(tg.base, N.Ident):
                self.unsupported("verschachtelte indizierte Zuweisung wird nicht übersetzt", tg)
            name = tg.base.name
            t = self.vtype(name, tg)
            if not t.is_array:
                self.unsupported(f"indizierte Zuweisung an '{name}': Variable muss eine Matrix sein "
                                 f"(z. B. mit zeros(m, n) anlegen)", tg)
            if isinstance(value, N.Matrix) and not value.rows:
                self.unsupported("Löschen von Elementen (x(i) = []) wird nicht übersetzt", tg)
            if len(tg.args) not in (1, 2) or any(isinstance(a, N.Colon) or not self.t(a).is_scalar
                                                 for a in tg.args):
                self.unsupported("nur skalare Indizes werden übersetzt", tg)
            if self.kind(value) == "mat":
                self.unsupported("Zuweisung einer Matrix an ein Element", tg)
            if name not in self.declared and name not in self.func.params:
                self.unsupported(f"'{name}' muss vor der indizierten Zuweisung angelegt werden (z. B. zeros)", tg)
            self.helpers.add("mat")
            return [f"{ind}{self.mat_set(name, self.index_codes(name, tg.args), self.num(value, P_OR))}"]
        self.unsupported("Zuweisung an Zellen/Structs wird nicht übersetzt", tg)

    def value_code(self, value, t):
        k = self.kind(value)
        if t.is_array:
            if k != "mat":
                self.unsupported("Skalar an eine Matrixvariable zugewiesen (Typ wechselt)", value)
            return self.mat_value(value)
        if t.kind == "func":
            return self.code(value)
        if k == "mat":
            self.unsupported("Matrix an eine skalare Variable zugewiesen", value)
        if t == BOOL:
            return self.boolean(value, P_OR)
        return self.num(value, P_OR)

    def multi_assign(self, s, ind):
        targets = []
        for t in s.targets:
            if isinstance(t, N.Placeholder):
                targets.append(None)
            elif isinstance(t, N.Ident) and t.name not in self.persistent:
                targets.append(t.name)
            else:
                self.unsupported("Mehrfachzuweisung nur an einfache lokale Variablen", s)
        callee = self.callee_name(s.value)
        args = s.value.args if isinstance(s.value, N.Index) else []
        out = []
        for n in targets:
            if n and n not in self.declared:
                self.declared.add(n)
                out.append(f"{ind}{self.declare(n, self.vtype(n, s), self.default_value(self.vtype(n, s)), True)}")
        if callee in self.local:
            f = self.local[callee]
            if len(targets) > len(f.outputs):
                self.unsupported(f"'{callee}' hat nur {len(f.outputs)} Ausgänge", s)
            call = self.call_local(callee, args, s.value, full=True)[0]
            return out + self.unpack(targets, [f.outputs[k] for k in range(len(targets))], call, ind,
                                     len(f.outputs))
        if callee in ("max", "min") and len(args) == 1 and len(targets) == 2 and self.kind(args[0]) == "mat":
            self.helpers.add("mat")
            call = f"mlab::{callee}_index({self.mat_arg(args[0])})"
            return out + self.unpack(targets, ["first", "second"], call, ind, 2, pair=True)
        if callee == "size" and len(args) == 1 and len(targets) == 2 and self.kind(args[0]) == "mat":
            self.helpers.add("mat")
            lines = []
            for n, m in zip(targets, ("nrows", "ncols")):
                if n:
                    lines.append(f"{ind}{self.var_ref(n, lhs=True)} = {self.mat_method(args[0], m)};")
            return out + lines
        self.unsupported(f"Mehrfachzuweisung aus '{callee or 'Ausdruck'}' wird nicht übersetzt", s)

    # ------------------------------------------------------------------ printf conversion
    @staticmethod
    def c_format(fmt):
        # MATLAB format -> C printf format for double arguments
        def conv(m):
            if m.group(0) == "%%":
                return "%%"
            flags, width, prec, c = m.group(1) or "", m.group(2) or "", m.group(3), m.group(4)
            p = f".{prec}" if prec is not None else ""
            if c in "diu":
                return f"%{flags}{width}.0f"
            if c in "xXoc":
                raise Unsupported(f"Formatangabe %{c} wird nicht übersetzt")
            return f"%{flags}{width}{p}{c}"
        return _SPEC.sub(conv, fmt)

    @staticmethod
    def rust_format(fmt):
        out, last = [], 0
        for m in _SPEC.finditer(fmt):
            out.append(fmt[last:m.start()].replace("{", "{{").replace("}", "}}"))
            last = m.end()
            if m.group(0) == "%%":
                out.append("%")
                continue
            flags, width, prec, c = m.group(1) or "", m.group(2) or "", m.group(3), m.group(4)
            align = "<" if "-" in flags else ""
            sign = "+" if "+" in flags else ""
            zero = "0" if "0" in flags and not align else ""
            if c in "diu":
                spec = f"{align}{sign}{zero}{width}.0"
            elif c in "fF":
                spec = f"{align}{sign}{zero}{width}.{prec if prec is not None else 6}"
            elif c in "eE":
                spec = f"{align}{sign}{zero}{width}" + (f".{prec}" if prec is not None else ".6") + c.lower()
            elif c in "gG":
                spec = f"{align}{sign}{zero}{width}"
            elif c == "s":
                spec = f"{align}{width}"
            else:
                raise Unsupported(f"Formatangabe %{c} wird nicht übersetzt")
            out.append("{" + (":" + spec if spec else "") + "}")
        out.append(fmt[last:].replace("{", "{{").replace("}", "}}"))
        return "".join(out)

    @staticmethod
    def string_literal(text):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'

    # ------------------------------------------------------------------ misc
    def result_struct_name(self, f):
        return camel(f.name) + "Result"

    def state_struct_name(self):
        return camel(self.entry.name) + "State"
