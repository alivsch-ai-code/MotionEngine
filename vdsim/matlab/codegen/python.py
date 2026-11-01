"""MATLAB -> Python (numpy) code generator.

Scalars become Python floats using ``math`` (the interpreter uses the same functions, so
results are bitwise identical), arrays become 2-D numpy arrays. MATLAB semantics that
plain numpy does not provide (1-based indexing with growth, colon operator, round half
away from zero, mod/rem, sprintf) are taken from ``vdsim.matlab.pyruntime`` and copied
into the generated module, which therefore only depends on numpy.
"""

from __future__ import annotations

import inspect
import keyword
import re

from .. import nodes as N
from .. import pyruntime
from ..typeinfer import SCALAR
from .base import BaseGenerator, GeneratedCode, Unsupported, index_mutated, int_literal, uses_name

_MATH1 = {"sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "log10", "log2", "sqrt"}
_NP1 = {"sin": "np.sin", "cos": "np.cos", "tan": "np.tan", "asin": "np.arcsin", "acos": "np.arccos",
        "atan": "np.arctan", "sinh": "np.sinh", "cosh": "np.cosh", "tanh": "np.tanh", "exp": "np.exp",
        "log": "np.log", "log10": "np.log10", "log2": "np.log2", "sqrt": "np.sqrt", "abs": "np.abs",
        "floor": "np.floor", "ceil": "np.ceil", "fix": "np.trunc", "round": "m_round", "sign": "m_sign",
        "wrapToPi": "m_wrap_to_pi", "isnan": "np.isnan", "isinf": "np.isinf", "isfinite": "np.isfinite",
        "real": "np.real", "imag": "np.imag"}
_SCALAR1 = {"abs": "abs", "floor": "np.floor", "ceil": "np.ceil", "fix": "np.trunc", "round": "m_round",
            "sign": "m_sign", "wrapToPi": "m_wrap_to_pi", "isnan": "math.isnan", "isinf": "math.isinf",
            "isfinite": "math.isfinite", "real": "", "imag": "0.0 *"}
_CONST = {"pi": "math.pi", "Inf": "math.inf", "inf": "math.inf", "NaN": "math.nan", "nan": "math.nan",
          "eps": "2.220446049250313e-16", "true": "True", "false": "False", "realmax": "1.7976931348623157e308",
          "realmin": "2.2250738585072014e-308"}
_HELPER_DEPS = {"m_get": ["m_arr", "m_norm", "_m_index_vec", "COLON"], "m_set": ["m_arr", "m_norm", "_m_index_vec",
                                                                                 "COLON"],
                "m_cat": ["m_arr", "m_norm"], "m_columns": ["m_arr", "m_norm"], "m_wrap_to_pi": ["m_mod"],
                "m_arr": [], "m_norm": [], "_m_index_vec": ["COLON"], "COLON": []}
_HELPER_ORDER = ["COLON", "m_norm", "m_arr", "m_div", "m_pow", "m_round", "m_mod", "m_rem", "m_sign", "m_wrap_to_pi",
                 "m_colon", "m_truth", "m_columns", "_m_index_vec", "m_get", "m_set", "m_cat", "m_sprintf"]
SUPPORTED = (set(_NP1) | set(_CONST) | {"atan2", "hypot", "mod", "rem", "power", "max", "min", "sum", "prod", "mean",
                                        "median", "norm", "numel", "length", "size", "isempty", "zeros", "ones",
                                        "eye", "linspace", "cumsum", "cumprod", "diff", "any", "all", "disp",
                                        "fprintf", "sprintf", "error", "warning", "deg2rad", "rad2deg", "interp1",
                                        "dot", "cross", "det", "inv", "trace", "transpose", "fliplr", "flipud",
                                        "repmat", "reshape", "num2str", "isfield", "struct", "strcmp", "logical",
                                        "double", "isscalar", "xor", "not", "find", "sort", "polyval", "std", "var",
                                        "clc", "clear", "close", "format", "figure", "hold", "drawnow", "assert"})

P_LAMBDA, P_OR, P_AND, P_NOT, P_CMP, P_BOR, P_BAND, P_ADD, P_MUL, P_UNARY, P_POW, P_POST, P_ATOM = \
    0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 14, 15


class PythonGenerator(BaseGenerator):
    target = "python"
    LANGUAGE_NAME = "Python"
    KEYWORDS = set(keyword.kwlist) | {"math", "np", "state", "print", "len", "range", "int", "float", "abs", "max",
                                      "min", "bool", "SimpleNamespace", "str", "list", "type", "object"}
    COMMENT = "#"

    # ------------------------------------------------------------------ entry
    def generate(self):
        funcs = self.collect()
        self.module = self.entry.name
        self.state_objs, self.globals_, body = [], set(), []
        self.uses_namespace = False
        for f, ft in funcs:
            body += self.function(f, ft) + ["", ""]
        head = self.module_doc(funcs)
        imports = ["import math", "", "import numpy as np"]
        if self.uses_namespace or self.state_objs:
            imports.insert(1, "from types import SimpleNamespace")
        helpers = self.helper_source()
        lines = head + imports + [""]
        if helpers:
            lines += ["", "# --- MATLAB semantics helpers (vdsim.matlab.pyruntime) ---", ""] + helpers + [""]
        if self.globals_:
            lines += ["# MATLAB global variables"] + [f"{g} = np.zeros((0, 0))" for g in sorted(self.globals_)] + [""]
        for name, fname, vars_ in self.state_objs:
            init = ", ".join(f"{v}=np.zeros((0, 0))" for v in vars_)
            lines += [f"{name} = SimpleNamespace({init})   # persistent variables of {fname}"]
        if self.state_objs:
            lines += ["", "", "def reset_state():", '    """Clear all persistent variables (like MATLAB \'clear functions\')."""']
            for name, _, vars_ in self.state_objs:
                lines += [f"    {name}.__dict__.update({', '.join(f'{v}=np.zeros((0, 0))' for v in vars_)})"]
            lines += [""]
        lines += ["", ""] + body
        lines += [f"__all__ = [{self.name(self.entry.name)!r}" + (", 'reset_state'" if self.state_objs else "") + "]"]
        text = "\n".join(lines).rstrip() + "\n"
        text = "\n".join(l.rstrip() for l in text.split("\n"))
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        sig = self.signature(funcs[0][1])
        return GeneratedCode("python", {f"{self.module}.py": text}, self.diags, self.name(self.entry.name), sig)

    def signature(self, ft):
        return {"module": self.module, "function": self.name(self.entry.name),
                "inputs": [(p, str(t)) for p, t in zip(self.entry.params, ft.inputs)],
                "outputs": [(o, str(t)) for o, t in zip(self.entry.outputs, ft.outputs)],
                "state": bool(self.state_objs)}

    def module_doc(self, funcs):
        doc = self.entry.doc or self.mfile.doc
        eqs = []
        for f, _ in funcs:
            eqs += self.equations_of(f)
        body = (doc.split("\n") if doc else [f"{self.entry.name} (aus MATLAB übersetzt)"])
        body += ["", f"Generated by vdsim.matlab (target python) from {self.mfile.path or '<source>'}.",
                 "Do not edit by hand; regenerate with: python -m vdsim.matlab convert <file.m> --to python"]
        if eqs:
            body += [f"Equation references: {', '.join(dict.fromkeys(eqs))}"]
        body = [l.replace("\\", "\\\\").replace('"""', "'''") for l in body]
        return ['"""' + body[0]] + body[1:] + ['"""', ""]

    def helper_source(self):
        need, stack = set(), list(self.helpers)
        while stack:
            h = stack.pop()
            if h in need:
                continue
            need.add(h)
            stack += _HELPER_DEPS.get(h, [])
            if h == "m_get" or h == "m_set":
                stack += ["m_arr", "m_norm"]
        out = []
        if "COLON" in need:
            out += [inspect.getsource(pyruntime._MColon).rstrip(), "", "", "COLON = _MColon()", "", ""]
        for h in _HELPER_ORDER:
            if h in need and h != "COLON":
                out += [inspect.getsource(getattr(pyruntime, h)).rstrip(), "", ""]
        return out

    def use(self, helper):
        self.helpers.add(helper)
        return helper

    # ------------------------------------------------------------------ functions
    def function(self, f, ft):
        self.func, self.env = f, dict(ft.env)
        self.ft = ft
        self.int_vars = set()
        self.defined = set(p for p in f.params)
        self.mutated = index_mutated(f)
        self.persistent = {n for s in N.body_statements(f.body) if isinstance(s, N.Persistent) for n in s.names}
        self.global_names = {n for s in N.body_statements(f.body) if isinstance(s, N.Global) for n in s.names}
        self.globals_ |= self.global_names
        self.state_name = "state" if "state" not in self.env else "state_"
        params = [self.name(p) if p != "~" else "_" for p in f.params]
        if params and params[-1] == "varargin":
            self.diag("error", "varargin wird nicht übersetzt", f)
        uses_nargin = uses_name(f, "nargin")
        sig = ", ".join(params if not uses_nargin else [f"{p}=None" for p in params])
        lines = [f"def {self.name(f.name)}({sig}):"]
        doc = f.doc.strip()
        ind = self.INDENT
        if doc:
            doc = doc.replace("\\", "\\\\").replace('"""', "'''")
            dl = doc.split("\n")
            lines.append(f'{ind}"""{dl[0]}' + ('"""' if len(dl) == 1 else ""))
            if len(dl) > 1:
                lines += [f"{ind}{l}".rstrip() for l in dl[1:]] + [f'{ind}"""']
        if self.persistent:
            sname = f"_{f.name}_state"
            self.state_objs.append((sname, f.name, sorted(self.persistent)))
            lines.append(f"{ind}{self.state_name} = {sname}")
        if self.global_names:
            lines.append(f"{ind}global {', '.join(sorted(self.global_names))}")
        if uses_nargin:
            lines.append(f"{ind}nargin = sum(a is not None for a in ({', '.join(params)}{',' if len(params) == 1 else ''}))")
        if uses_name(f, "nargout"):
            self.diag("warning", f"nargout wird in Python als Anzahl der deklarierten Ausgänge ({len(f.outputs)}) "
                                 f"übersetzt", f)
            lines.append(f"{ind}nargout = {len(f.outputs)}")
        for p in f.params:
            if p in self.mutated and self.env.get(p, SCALAR).is_array:
                lines.append(f"{ind}{self.name(p)} = np.array({self.name(p)}, dtype=float)   # MATLAB copy semantics")
        body = self.block(f.body, ind)
        lines += body
        ret = self.return_stmt()
        if not body or not body[-1].strip().startswith("return"):
            if ret != "return" or not body:
                lines.append(f"{ind}{ret}")
        return lines

    def return_stmt(self):
        outs = [self.var(o) for o in self.func.outputs]
        if not outs:
            return "return"
        return "return " + ", ".join(outs)

    def var(self, name):
        if name in self.persistent:
            return f"{self.state_name}.{name}"
        return self.name(name)

    # ------------------------------------------------------------------ statements
    def stmt(self, s, ind):
        if isinstance(s, N.Assign):
            return self.assign(s, ind)
        if isinstance(s, N.ExprStmt):
            return self.expr_stmt(s, ind)
        if isinstance(s, N.If):
            out = []
            for k, (cond, body) in enumerate(s.clauses):
                out.append(f"{ind}{'if' if k == 0 else 'elif'} {self.cond(cond)}:")
                out += self.block(body, ind + self.INDENT) or [ind + self.INDENT + "pass"]
            if s.else_body:
                out.append(f"{ind}else:")
                out += self.block(s.else_body, ind + self.INDENT) or [ind + self.INDENT + "pass"]
            return out
        if isinstance(s, N.For):
            return self.for_stmt(s, ind)
        if isinstance(s, N.While):
            return [f"{ind}while {self.cond(s.cond)}:"] + (self.block(s.body, ind + self.INDENT) or
                                                            [ind + self.INDENT + "pass"])
        if isinstance(s, N.Switch):
            return self.switch(s, ind)
        if isinstance(s, N.Break):
            return [f"{ind}break"]
        if isinstance(s, N.Continue):
            return [f"{ind}continue"]
        if isinstance(s, N.Return):
            return [f"{ind}{self.return_stmt()}"]
        if isinstance(s, N.Persistent):
            return [f"{ind}# persistent {' '.join(s.names)}  -> {self.state_name}.<name> (module-level state)"]
        if isinstance(s, N.Global):
            return [f"{ind}# global {' '.join(s.names)}"]
        if isinstance(s, N.Command):
            self.diag("info", f"MATLAB-Befehl '{s.name}' wird ignoriert", s)
            return [f"{ind}# MATLAB command omitted: {s.name} {' '.join(s.args)}".rstrip()]
        if isinstance(s, N.TryCatch):
            out = [f"{ind}try:"] + (self.block(s.body, ind + self.INDENT) or [ind + self.INDENT + "pass"])
            if s.ident:
                self.uses_namespace = True
                out += [f"{ind}except Exception as exc:",
                        f"{ind}{self.INDENT}{self.name(s.ident)} = SimpleNamespace(message=str(exc), identifier='')"]
                self.env[s.ident] = self.env.get(s.ident, SCALAR)
            else:
                out += [f"{ind}except Exception:"]
            out += self.block(s.catch_body, ind + self.INDENT) or [ind + self.INDENT + "pass"]
            return out
        self.unsupported(f"Anweisung {type(s).__name__} nicht unterstützt", s)

    def cond(self, e):
        code, prec = self.ex(e)
        if self.t(e).is_scalar or self.t(e).kind == "unknown":
            return code
        self.use("m_truth")
        return f"m_truth({code})"

    def for_stmt(self, s, ind):
        it, var = s.iterable, self.var(s.var)
        a = int_literal(it.start) if isinstance(it, N.Range) else None
        step = 1 if isinstance(it, N.Range) and it.step is None else int_literal(it.step) if isinstance(it, N.Range) \
            else None
        if isinstance(it, N.Range) and a is not None and step not in (None, 0):
            b = int_literal(it.stop)
            if b is not None:
                stop = str(b + (1 if step > 0 else -1))
            else:
                stop = f"math.floor({self.code(it.stop)}) + 1" if step > 0 else f"math.ceil({self.code(it.stop)}) - 1"
            rng = f"range({a}, {stop})" if step == 1 else f"range({a}, {stop}, {step})"
            head = f"{ind}for {var} in {rng}:"
            self.int_vars.add(s.var)
        elif isinstance(it, N.Range):
            self.use("m_colon")
            st = "1" if it.step is None else self.code(it.step)
            head = f"{ind}for {var} in m_colon({self.code(it.start)}, {st}, {self.code(it.stop)}).flat:"
        else:
            t = self.t(it)
            if t.is_scalar:
                head = f"{ind}for {var} in [{self.code(it)}]:"
            elif t.is_array and t.rows == 1:
                head = f"{ind}for {var} in {self.p(it, P_POST)}.flat:"
            else:
                self.use("m_columns")
                head = f"{ind}for {var} in m_columns({self.code(it)}):"
        self.defined.add(s.var)
        return [head] + (self.block(s.body, ind + self.INDENT) or [ind + self.INDENT + "pass"])

    def switch(self, s, ind):
        out = []
        if isinstance(s.subject, N.Ident):
            subj = self.code(s.subject)
        else:
            subj = "switch_value"
            out.append(f"{ind}{subj} = {self.code(s.subject)}")
        for k, (value, body) in enumerate(s.cases):
            if isinstance(value, N.CellArray):
                vals = [self.code(x) for row in value.rows for x in row]
                cond = f"{subj} in ({', '.join(vals)}{',' if len(vals) == 1 else ''})"
            else:
                cond = f"{subj} == {self.p(value, P_CMP + 1)}"
            out.append(f"{ind}{'if' if k == 0 else 'elif'} {cond}:")
            out += self.block(body, ind + self.INDENT) or [ind + self.INDENT + "pass"]
        if s.otherwise:
            if not s.cases:
                return out + self.block(s.otherwise, ind)
            out.append(f"{ind}else:")
            out += self.block(s.otherwise, ind + self.INDENT) or [ind + self.INDENT + "pass"]
        return out

    def expr_stmt(self, s, ind):
        e = s.expr
        name = self.callee_name(e)
        if name in ("disp", "fprintf", "error", "warning", "assert", "clc", "clear", "close", "format", "figure",
                    "hold", "drawnow") and name not in self.local:
            return [f"{ind}{l}" for l in self.output_call(name, e.args if isinstance(e, N.Index) else [], e)]
        code = self.code(e)
        if not s.suppress:
            self.diag("info", "Ausgabe ohne Semikolon wird als print() übersetzt", s)
            return [f"{ind}print({code})"]
        return [f"{ind}{code}"]

    def output_call(self, name, args, node):
        if name in ("clc", "clear", "close", "format", "figure", "hold", "drawnow"):
            return [f"pass  # MATLAB {name} omitted"]
        if name == "disp":
            return [f"print({self.code(args[0])})"]
        if name == "assert":
            return [f"assert {self.cond(args[0])}" + (f", {self.code(args[1])}" if len(args) > 1 else "")]
        if args and not isinstance(args[0], N.String) and name == "fprintf" and len(args) > 1:
            args = args[1:]            # file id
        if not args:
            return ["raise RuntimeError('error')"] if name == "error" else ["pass"]
        self.use("m_sprintf")
        fmt = ", ".join(self.code(a) for a in args)
        text = self.code(args[0]) if len(args) == 1 and isinstance(args[0], N.String) and "%" not in \
            args[0].value and "\\" not in args[0].value else f"m_sprintf({fmt})"
        if name == "fprintf":
            return [f"print({text}, end='')"]
        if name == "error":
            return [f"raise RuntimeError({text})"]
        return [f"print('Warnung: ' + {text})"]

    def assign(self, s, ind):
        if s.multi or len(s.targets) > 1:
            return self.multi_assign(s, ind)
        tg, value = s.targets[0], s.value
        out = []
        if isinstance(tg, N.Ident):
            code = self.code(value)
            vt = self.t(value)
            if vt.is_array and isinstance(value, (N.Ident, N.Postfix, N.Field)) and (
                    tg.name in self.mutated or (isinstance(value, N.Ident) and value.name in self.mutated)):
                code = f"{self.p(value, P_POST)}.copy()"
            out.append(f"{ind}{self.var(tg.name)} = {code}")
            self.defined.add(tg.name)
            if tg.name in self.int_vars:
                self.int_vars.discard(tg.name)
        elif isinstance(tg, N.Index):
            out += self.index_assign(tg, value, ind)
        elif isinstance(tg, N.Field):
            base = tg
            while not isinstance(base, N.Ident):
                base = base.base
            if base.name not in self.defined and base is tg.base:
                self.uses_namespace = True
                out.append(f"{ind}{self.var(base.name)} = SimpleNamespace()")
                self.defined.add(base.name)
            out.append(f"{ind}{self.code(tg)} = {self.code(value)}")
        else:
            self.unsupported("Zuweisung an Zellen/dynamische Felder wird nach Python nicht übersetzt", tg)
        if not s.suppress:
            base = tg
            while not isinstance(base, N.Ident):
                base = base.base
            self.diag("info", "Ausgabe ohne Semikolon wird als print() übersetzt", s)
            out.append(f"{ind}print({base.name!r}, '=', {self.var(base.name)})")
        return out

    def multi_assign(self, s, ind):
        names = [self.var(t.name) if isinstance(t, N.Ident) else "_" if isinstance(t, N.Placeholder) else None
                 for t in s.targets]
        if None in names:
            self.unsupported("Mehrfachzuweisung nur an einfache Variablen", s)
        for t in s.targets:
            if isinstance(t, N.Ident):
                self.defined.add(t.name)
        callee = self.callee_name(s.value)
        args = s.value.args if isinstance(s.value, N.Index) else []
        n = len(names)
        if callee in self.local:
            f = self.local[callee]
            call = f"{self.name(callee)}({', '.join(self.code(a) for a in args)})"
            if len(f.outputs) == 1:
                self.unsupported(f"'{callee}' hat nur einen Ausgang", s)
            if n < len(f.outputs):
                call += f"[:{n}]"
            return [f"{ind}{', '.join(names)} = {call}"]
        if callee in ("max", "min") and len(args) == 1 and n == 2:
            x = self.code(args[0])
            return [f"{ind}{names[0]}, {names[1]} = np.nan{callee}({x}), float(np.nanarg{callee}({x}) + 1)"]
        if callee == "size" and len(args) == 1:
            x = self.p(args[0], P_POST)
            parts = [f"float(np.shape({x})[{k}])" if k < 2 else "1.0" for k in range(n)]
            return [f"{ind}{', '.join(names)} = {', '.join(parts)}"]
        self.unsupported(f"Mehrfachzuweisung aus '{callee or 'Ausdruck'}' wird nicht übersetzt", s)

    def index_assign(self, tg, value, ind):
        if not isinstance(tg.base, N.Ident):
            self.unsupported("verschachtelte indizierte Zuweisung wird nicht übersetzt", tg)
        name = tg.base.name
        var = self.var(name)
        t = self.env.get(name, SCALAR)
        delete = isinstance(value, N.Matrix) and not value.rows
        direct = (not delete and t.is_array and t.rows is not None and t.cols is not None and name in self.defined
                  and all(self.t(a).is_scalar and not isinstance(a, N.Colon) for a in tg.args) and len(tg.args) <= 2
                  and self.t(value).is_scalar and (len(tg.args) == 2 or 1 in (t.rows, t.cols)))
        if direct:
            self.base_name = name
            return [f"{ind}{var}[{self.direct_index(tg.args, t)}] = {self.code(value)}"]
        self.use("m_set")
        args = self.index_args(tg.args, name)
        base = var if name in self.defined else "None"
        self.defined.add(name)
        if delete:
            return [f"{ind}{var} = m_set({base}, ({args}{',' if len(tg.args) == 1 else ''}), None, delete=True)"]
        return [f"{ind}{var} = m_set({base}, ({args}{',' if len(tg.args) == 1 else ''}), {self.code(value)})"]

    # ------------------------------------------------------------------ expressions
    def code(self, e):
        return self.ex(e)[0]

    def p(self, e, minprec):
        code, prec = self.ex(e)
        return f"({code})" if prec < minprec else code

    def ex(self, e):
        try:
            return self._ex(e)
        except Unsupported:
            raise
        except RecursionError:  # pragma: no cover
            raise Unsupported("Ausdruck zu tief verschachtelt", e)

    def _ex(self, e):
        if isinstance(e, N.Number):
            v = e.value
            if isinstance(v, complex):
                self.unsupported("komplexe Zahlen werden nicht übersetzt", e)
            text = (e.text or repr(v)).replace("d", "e").replace("D", "e")
            if text.isdigit():
                text = str(int(text))
            if text.startswith("."):
                text = "0" + text
            return text, P_ATOM
        if isinstance(e, N.String):
            return repr(e.value), P_ATOM
        if isinstance(e, N.Ident):
            return self.ident(e)
        if isinstance(e, N.Binary):
            return self.binary(e)
        if isinstance(e, N.Unary):
            if e.op == "-":
                return f"-{self.p(e.operand, P_UNARY)}", P_UNARY
            if e.op == "+":
                return self.ex(e.operand)
            if self.t(e.operand).is_scalar:
                return f"not {self.p(e.operand, P_NOT)}", P_NOT
            return f"np.logical_not({self.code(e.operand)})", P_ATOM
        if isinstance(e, N.Postfix):
            if self.t(e.operand).is_scalar:
                return self.ex(e.operand)
            return f"{self.p(e.operand, P_POST)}.T", P_POST
        if isinstance(e, N.Range):
            self.use("m_colon")
            st = "1" if e.step is None else self.code(e.step)
            return f"m_colon({self.code(e.start)}, {st}, {self.code(e.stop)})", P_ATOM
        if isinstance(e, N.Matrix):
            return self.matrix(e)
        if isinstance(e, N.CellArray):
            if len(e.rows) > 1:
                self.unsupported("mehrzeilige Zellen werden nicht übersetzt", e)
            self.diag("warning", "Zelle wird als Python-Liste übersetzt (nur eindimensional)", e)
            return "[" + ", ".join(self.code(x) for x in (e.rows[0] if e.rows else [])) + "]", P_ATOM
        if isinstance(e, N.Index):
            return self.index(e)
        if isinstance(e, N.CellIndex):
            if len(e.args) != 1:
                self.unsupported("Zellindizierung mit mehreren Indizes wird nicht übersetzt", e)
            return f"{self.p(e.base, P_POST)}[{self.zero_index(e.args[0])}]", P_POST
        if isinstance(e, N.Field):
            return f"{self.p(e.base, P_POST)}.{e.name}", P_POST
        if isinstance(e, N.DynField):
            return f"getattr({self.code(e.base)}, {self.code(e.name)})", P_ATOM
        if isinstance(e, N.AnonFunc):
            saved = dict(self.env)
            for p in e.params:
                self.env[p] = SCALAR
            body = self.code(e.body)
            self.env = saved
            return f"lambda {', '.join(self.name(p) for p in e.params)}: {body}", P_LAMBDA
        if isinstance(e, N.FuncHandle):
            if e.name in self.local:
                return self.name(e.name), P_ATOM
            if e.name in _MATH1:
                return f"math.{e.name}", P_ATOM
            self.unsupported(f"Function Handle auf '{e.name}' wird nicht übersetzt", e)
        if isinstance(e, N.End):
            self.unsupported("'end' nur direkt in Indizes unterstützt", e)
        if isinstance(e, N.Colon):
            self.use("COLON")
            return "COLON", P_ATOM
        self.unsupported(f"Ausdruck {type(e).__name__} nicht unterstützt", e)

    def ident(self, e):
        n = e.name
        if n in self.env or n in self.func.params:
            return self.var(n), P_ATOM
        if n in ("nargin", "nargout"):
            return n, P_ATOM
        if n in _CONST:
            return _CONST[n], P_ATOM
        if n in self.local:
            return f"{self.name(n)}()", P_POST
        if n in ("i", "j"):
            self.unsupported("komplexe Zahlen werden nicht übersetzt", e)
        return self.call(n, [], e)

    def binary(self, e):
        op, l, r = e.op, e.left, e.right
        tl, tr = self.t(l), self.t(r)
        sl, sr = tl.is_scalar, tr.is_scalar
        if op in ("&&", "||", "&", "|"):
            if op in ("&", "|") and not (sl and sr):
                fn = "np.logical_and" if op == "&" else "np.logical_or"
                return f"{fn}({self.code(l)}, {self.code(r)})", P_ATOM
            word, prec = ("and", P_AND) if op in ("&&", "&") else ("or", P_OR)
            lc = self.p(l, prec) if self.is_bool(l) else f"bool({self.code(l)})"
            rc = self.p(r, prec + 1) if self.is_bool(r) else f"bool({self.code(r)})"
            return f"{lc} {word} {rc}", prec
        if op in ("==", "~=", "<", "<=", ">", ">="):
            pyop = "!=" if op == "~=" else op
            return f"{self.p(l, P_BOR)} {pyop} {self.p(r, P_BOR)}", P_CMP
        if op in ("+", "-"):
            return f"{self.p(l, P_ADD)} {op} {self.p(r, P_ADD + 1)}", P_ADD
        if op in ("*", ".*"):
            sym = "@" if op == "*" and not sl and not sr else "*"
            return f"{self.p(l, P_MUL)} {sym} {self.p(r, P_MUL + 1)}", P_MUL
        if op in ("/", "./"):
            if op == "/" and not sr:
                return f"np.linalg.solve({self.p(r, P_POST)}.T, {self.p(l, P_POST)}.T).T", P_POST
            return f"{self.p(l, P_MUL)} / {self.p(r, P_MUL + 1)}", P_MUL
        if op in ("\\", ".\\"):
            if op == "\\" and not sl:
                return f"np.linalg.solve({self.code(l)}, {self.code(r)})", P_ATOM
            return f"{self.p(r, P_MUL)} / {self.p(l, P_MUL + 1)}", P_MUL
        if op in ("^", ".^"):
            if op == "^" and not sl:
                return f"np.linalg.matrix_power({self.code(l)}, int({self.code(r)}))", P_ATOM
            return f"{self.p(l, P_POST)} ** {self.p(r, P_UNARY)}", P_POW
        self.unsupported(f"Operator '{op}' nicht unterstützt", e)

    def matrix(self, e):
        if not e.rows:
            return "np.zeros((0, 0))", P_ATOM
        ts = [[self.t(x) for x in row] for row in e.rows]
        if any(t.kind == "string" for row in ts for t in row):
            if len(e.rows) == 1:
                return " + ".join(self.p(x, P_ADD + 1) for x in e.rows[0]), P_ADD
            self.unsupported("mehrzeilige Zeichenketten-Matrizen werden nicht übersetzt", e)
        if all(t.is_scalar for row in ts for t in row):
            rows = ", ".join("[" + ", ".join(self.code(x) for x in row) + "]" for row in e.rows)
            return f"np.array([{rows}], dtype=float)", P_ATOM
        self.use("m_cat")
        rows = ", ".join("[" + ", ".join(self.code(x) for x in row) + "]" for row in e.rows)
        return f"m_cat([{rows}])", P_ATOM

    # ------------------------------------------------------------------ indexing
    def zero_index(self, a, base=None, dim=None):
        # 0-based integer index code for a scalar MATLAB index
        if isinstance(a, N.End):
            return "-1"
        k = int_literal(a)
        if k is not None:
            return str(k - 1)
        if isinstance(a, N.Binary) and a.op == "-" and isinstance(a.left, N.End) and int_literal(a.right) is not None:
            return str(-1 - int_literal(a.right))
        if isinstance(a, N.Ident) and a.name in self.int_vars:
            return f"{self.var(a.name)} - 1"
        if isinstance(a, N.Binary) and a.op == "+" and int_literal(a.right) is not None and \
                isinstance(a.left, N.Ident) and a.left.name in self.int_vars:
            return f"{self.var(a.left.name)} + {int_literal(a.right) - 1}" if int_literal(a.right) != 1 else \
                self.var(a.left.name)
        return f"int({self.code(a)}) - 1"

    def direct_index(self, args, t):
        if len(args) == 2:
            return f"{self.zero_index(args[0])}, {self.zero_index(args[1])}"
        k = self.zero_index(args[0])
        return f"{k}, 0" if t.cols == 1 else f"0, {k}"

    def index_args(self, args, base_name):
        out = []
        n = len(args)
        for k, a in enumerate(args):
            if isinstance(a, N.Colon):
                self.use("COLON")
                out.append("COLON")
                continue
            saved = getattr(self, "_end_ctx", None)
            self._end_ctx = (self.var(base_name), k, n)
            try:
                out.append(self.code(a) if not self._has_end(a) else self.end_code(a))
            finally:
                self._end_ctx = saved
        return ", ".join(out)

    @staticmethod
    def _has_end(a):
        return any(isinstance(x, N.End) for x in a.walk())

    def end_code(self, a):
        base, k, n = self._end_ctx
        endv = f"np.size({base})" if n == 1 else f"np.shape({base})[{k}]"
        saved = self._ex

        def patched(e):
            if isinstance(e, N.End):
                return endv, P_ATOM
            return saved(e)
        self._ex = patched
        try:
            return self.code(a)
        finally:
            self._ex = saved

    def index(self, e):
        name = self.callee_name(e)
        if name is not None:
            return self.call(name, e.args, e)
        bt = self.t(e.base)
        if bt.kind == "func":
            return f"{self.p(e.base, P_POST)}({', '.join(self.code(a) for a in e.args)})", P_POST
        if bt.kind in ("struct", "cell", "string", "unknown"):
            if bt.kind == "struct" and all(int_literal(a) == 1 for a in e.args):
                return self.ex(e.base)
            if bt.kind == "string":
                self.use("m_get")
                return f"m_get({self.code(e.base)}, {', '.join(self.code(a) for a in e.args)})", P_ATOM
        base_name = e.base.name if isinstance(e.base, N.Ident) else None
        if bt.is_array and base_name and all(self.t(a).is_scalar and not isinstance(a, N.Colon) for a in e.args) \
                and len(e.args) <= 2 and (len(e.args) == 2 or 1 in (bt.rows, bt.cols)):
            return f"{self.p(e.base, P_POST)}[{self.direct_index(e.args, bt)}]", P_POST
        if bt.is_scalar and all(int_literal(a) == 1 for a in e.args):
            return self.ex(e.base)
        if not base_name:
            self.unsupported("Indizierung eines Ausdrucks wird nicht übersetzt", e)
        self.use("m_get")
        return f"m_get({self.var(base_name)}, {self.index_args(e.args, base_name)})", P_ATOM

    # ------------------------------------------------------------------ calls
    def call(self, name, args, node):
        if name in self.local:
            f = self.local[name]
            if len(args) > len(f.params):
                self.unsupported(f"zu viele Argumente für '{name}'", node)
            call = f"{self.name(name)}({', '.join(self.code(a) for a in args)})"
            if len(f.outputs) > 1:
                call += "[0]"
            return call, P_POST
        self.check_builtin(name, node, SUPPORTED)
        c = [self.code(a) for a in args]
        ts = [self.t(a) for a in args]
        scalar = all(t.is_scalar for t in ts)
        if name in _CONST:
            if not args:
                return _CONST[name], P_ATOM
            fill = {"pi": "math.pi", "Inf": "math.inf", "inf": "math.inf", "NaN": "math.nan", "nan": "math.nan",
                    "true": "True", "false": "False"}.get(name)
            if fill is None:
                self.unsupported(f"'{name}' mit Argumenten nicht unterstützt", node)
            return f"np.full({self.shape_code(args)}, {fill})", P_ATOM
        if name in _NP1 or name in _MATH1:
            if len(args) != 1:
                self.unsupported(f"'{name}' mit {len(args)} Argumenten nicht unterstützt", node)
            if scalar:
                if name in _MATH1:
                    return f"math.{name}({c[0]})", P_POST
                fn = _SCALAR1[name]
                if fn.startswith("m_"):
                    self.use(fn)
                if fn == "":
                    return c[0], P_ATOM if self.ex(args[0])[1] >= P_POST else P_LAMBDA
                if fn.endswith("*"):
                    return f"{fn} {self.p(args[0], P_MUL + 1)}", P_MUL
                return f"{fn}({c[0]})", P_POST
            fn = _NP1[name]
            if fn.startswith("m_"):
                self.use(fn)
            return f"{fn}({c[0]})", P_POST
        if name in ("atan2", "hypot"):
            if scalar:
                return f"math.{name}({c[0]}, {c[1]})", P_POST
            return f"np.{'arctan2' if name == 'atan2' else 'hypot'}({c[0]}, {c[1]})", P_POST
        if name in ("mod", "rem"):
            self.use("m_" + name)
            return f"m_{name}({c[0]}, {c[1]})", P_POST
        if name == "power":
            return f"{self.p(args[0], P_POST)} ** {self.p(args[1], P_UNARY)}", P_POW
        if name in ("deg2rad", "rad2deg"):
            factor = "(math.pi / 180)" if name == "deg2rad" else "(180 / math.pi)"
            return f"{self.p(args[0], P_MUL)} * {factor}", P_MUL
        if name in ("max", "min"):
            if len(args) >= 2 and not (isinstance(args[1], N.Matrix) and not args[1].rows):
                return f"np.f{name}({c[0]}, {c[1]})", P_POST
            if len(args) == 1:
                if ts[0].is_scalar:
                    return c[0], self.ex(args[0])[1]
                if ts[0].is_vector or None in (ts[0].rows, ts[0].cols):
                    return f"np.nan{name}({c[0]})", P_POST
            self.unsupported(f"'{name}' über Matrixdimensionen wird nicht übersetzt", node)
        if name in ("sum", "prod", "mean", "median", "std", "var"):
            if len(args) == 1 and (ts[0].is_vector or ts[0].is_scalar or None in (ts[0].rows, ts[0].cols)):
                if name in ("std", "var"):
                    return f"np.{name}({c[0]}, ddof=1)", P_POST
                return f"np.{name}({c[0]})", P_POST
            if len(args) == 2 and int_literal(args[1]) in (1, 2) and name not in ("std", "var"):
                return f"np.{name}({c[0]}, axis={int_literal(args[1]) - 1}, keepdims=True)", P_POST
            if len(args) == 1:
                return f"np.{name}({c[0]}, axis=0, keepdims=True)", P_POST
            self.unsupported(f"'{name}' mit diesen Argumenten wird nicht übersetzt", node)
        if name == "norm":
            if len(args) == 1:
                return (f"abs({c[0]})" if ts[0].is_scalar else f"np.linalg.norm({c[0]})"), P_POST
            return f"np.linalg.norm({c[0]}, {c[1]})", P_POST
        if name == "numel":
            return ("1" if ts[0].is_scalar else f"len({c[0]})" if ts[0].kind == "cell" else
                    f"np.size({c[0]})"), P_POST
        if name == "length":
            if ts[0].is_scalar:
                return "1", P_ATOM
            if ts[0].kind in ("cell", "string"):
                return f"len({c[0]})", P_POST
            return f"(max(np.shape({c[0]})) if np.size({c[0]}) else 0)", P_ATOM
        if name == "size":
            if len(args) == 2:
                d = int_literal(args[1])
                if d in (1, 2):
                    return f"np.shape({c[0]})[{d - 1}]", P_POST
                return f"np.shape({c[0]})[int({c[1]}) - 1]", P_POST
            return f"np.array([np.shape({c[0]})], dtype=float)", P_ATOM
        if name == "isempty":
            return (f"len({c[0]}) == 0" if ts[0].kind in ("cell", "string") else f"np.size({c[0]}) == 0"), P_CMP
        if name == "isscalar":
            return f"np.size({c[0]}) == 1", P_CMP
        if name in ("zeros", "ones"):
            if not args:
                return ("0.0" if name == "zeros" else "1.0"), P_ATOM
            return f"np.{name}({self.shape_code(args)})", P_ATOM
        if name == "eye":
            if len(args) == 1 and self.t(args[0]).is_scalar:
                return f"np.eye({self.int_code(args[0])})", P_ATOM
            if len(args) == 2:
                return f"np.eye({self.int_code(args[0])}, {self.int_code(args[1])})", P_ATOM
            return "1.0" if not args else f"np.eye(*{self.shape_code(args)})", P_ATOM
        if name == "linspace":
            n = c[2] if len(args) > 2 else "100"
            return f"np.linspace({c[0]}, {c[1]}, int({n})).reshape(1, -1)", P_POST
        if name in ("cumsum", "cumprod", "diff"):
            t0 = ts[0]
            axis = 1 if t0.rows == 1 else 0
            if t0.rows is None and t0.cols is None:
                self.diag("warning", f"'{name}': Orientierung unbekannt, Spaltenrichtung angenommen", node)
            return f"np.{name}({c[0]}, axis={axis})", P_POST
        if name in ("any", "all"):
            return (f"bool({c[0]})" if ts[0].is_scalar else f"bool(np.{name}({c[0]} != 0))"), P_POST
        if name == "sprintf":
            self.use("m_sprintf")
            return f"m_sprintf({', '.join(c)})", P_POST
        if name == "num2str":
            if len(args) == 1 and ts[0].is_scalar:
                return f"format({c[0]}, 'g')", P_POST
            self.unsupported("num2str mit Format/Arrays wird nicht übersetzt", node)
        if name == "interp1":
            if len(args) != 3 or not ts[2].is_scalar and not ts[2].is_array:
                self.unsupported("interp1 wird nur als interp1(x, v, xq) (linear) übersetzt", node)
            return (f"np.interp({c[2]}, np.ravel({c[0]}), np.ravel({c[1]}), left=math.nan, right=math.nan)",
                    P_POST)
        if name == "dot":
            return f"float(np.sum(np.ravel({c[0]}) * np.ravel({c[1]})))", P_POST
        if name == "cross":
            return f"np.cross(np.ravel({c[0]}), np.ravel({c[1]})).reshape(np.shape({c[0]}))", P_POST
        if name in ("det", "inv", "trace"):
            fn = {"det": "np.linalg.det", "inv": "np.linalg.inv", "trace": "np.trace"}[name]
            return f"{fn}({c[0]})", P_POST
        if name == "transpose":
            return f"{self.p(args[0], P_POST)}.T", P_POST
        if name in ("fliplr", "flipud"):
            return f"np.{name}({c[0]})", P_POST
        if name == "repmat":
            return f"np.tile({c[0]}, ({c[1]}, {c[2] if len(c) > 2 else c[1]}))", P_POST
        if name == "reshape":
            return f"np.reshape({c[0]}, ({', '.join(f'int({x})' for x in c[1:])}), order='F')", P_POST
        if name == "isfield":
            return f"hasattr({c[0]}, {c[1]})", P_POST
        if name == "struct":
            self.uses_namespace = True
            kv = ", ".join(f"{args[k].value}={c[k + 1]}" for k in range(0, len(args) - 1, 2)
                           if isinstance(args[k], N.String))
            return f"SimpleNamespace({kv})", P_POST
        if name == "strcmp":
            return f"{self.p(args[0], P_BOR)} == {self.p(args[1], P_BOR)}", P_CMP
        if name in ("logical",):
            return (f"bool({c[0]})" if scalar else f"({c[0]} != 0)"), P_ATOM
        if name == "double":
            return (f"float({c[0]})" if scalar else f"np.asarray({c[0]}, dtype=float)"), P_POST
        if name == "xor":
            return f"bool({c[0]}) != bool({c[1]})", P_CMP
        if name == "not":
            return f"not {self.p(args[0], P_NOT)}", P_NOT
        if name == "polyval":
            return f"np.polyval(np.ravel({c[0]}), {c[1]})", P_POST
        if name == "find":
            self.unsupported("find wird nicht übersetzt", node)
        if name == "sort":
            return f"np.sort({c[0]}, axis={1 if ts[0].rows == 1 else 0})", P_POST
        if name in ("disp", "fprintf", "error", "warning", "assert"):
            self.unsupported(f"'{name}' kann nicht als Ausdruck verwendet werden", node)
        self.unsupported(f"Built-in '{name}' wird für Python nicht unterstützt", node)

    def int_code(self, a):
        return self.code(a) if int_literal(a) is not None else f"int({self.code(a)})"

    def shape_code(self, args):
        c = [self.code(a) for a in args]
        conv = [x if int_literal(a) is not None else f"int({x})" for a, x in zip(args, c)]
        if len(args) == 1:
            if self.t(args[0]).is_array:
                return f"tuple(int(v) for v in np.ravel({c[0]})[:2])"
            return f"({conv[0]}, {conv[0]})"
        return f"({conv[0]}, {conv[1]})"
