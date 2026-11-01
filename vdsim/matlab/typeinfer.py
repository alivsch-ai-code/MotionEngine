"""Type and shape inference for the code generators.

The lattice is deliberately small: ``scalar`` (double), ``bool`` (logical scalar), ``array``
(double matrix with optional known size; vectors are arrays with one dimension 1),
``string``, ``cell``, ``struct``, ``func`` and ``unknown``. Inference is flow-insensitive
per function: the type of a variable is the join over all its assignments, iterated to a
fixed point (loops). Input types come from

  1. explicit hints: ``input_types={"x": "vector"}`` or a pragma comment in the file
     ``%#type x: vector(3)`` / ``%#type A: matrix(2,2)`` / ``%#type s: scalar``,
  2. usage: an input that is indexed, iterated, or passed to size/numel/length/sum/... is
     an array,
  3. otherwise ``scalar``.

Function calls between local functions are inferred interprocedurally (per argument
signature, recursion-safe).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..framework.knowledge import trace
from . import nodes as N

_ELEMENTWISE = {"sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "log10", "log2",
                "sqrt", "abs", "floor", "ceil", "round", "fix", "sign", "deg2rad", "rad2deg", "wrapToPi", "wrapTo2Pi",
                "real", "imag", "conj", "double"}
_BINARY_ELEMENTWISE = {"atan2", "mod", "rem", "hypot", "power"}
_REDUCTIONS = {"sum", "prod", "mean", "median", "max", "min", "std", "var"}
_SCALAR_RESULT = {"numel", "length", "norm", "det", "trace", "dot", "ndims", "nnz", "polyval_scalar", "trapz",
                  "str2double", "toc"}
_BOOL_RESULT = {"isempty", "isscalar", "isvector", "isrow", "iscolumn", "isnumeric", "ischar", "islogical", "iscell",
                "isstruct", "isreal", "isfield", "isequal", "strcmp", "strcmpi", "xor", "not", "isa"}
_CONSTANTS = {"pi", "eps", "Inf", "inf", "NaN", "nan", "realmax", "realmin"}
_STRING_RESULT = {"sprintf", "num2str", "int2str", "mat2str", "upper", "lower", "strtrim", "strrep", "strcat",
                  "func2str", "class", "blanks"}
_NO_RESULT = {"disp", "fprintf", "error", "warning", "assert", "clc", "clear", "close", "format", "hold", "figure",
              "drawnow", "more", "clf", "tic"}
_ARRAY_HINT_FUNCS = {"numel", "length", "size", "sum", "prod", "mean", "median", "norm", "cumsum", "cumprod", "diff",
                     "find", "sort", "any", "all", "isempty", "fliplr", "flipud", "dot", "cross", "det", "inv",
                     "trace", "transpose", "std", "var", "interp1", "reshape", "repmat", "isrow", "iscolumn",
                     "isvector", "trapz"}
PRAGMA = re.compile(r"^\s*#type\s+(\w+)\s*:\s*(\w+)\s*(?:\(\s*([^)]*)\))?\s*$")


@dataclass(frozen=True)
class MType:
    kind: str                 # scalar bool array string cell struct func unknown none
    rows: int | None = None
    cols: int | None = None

    @property
    def is_scalar(self):
        return self.kind in ("scalar", "bool")

    @property
    def is_array(self):
        return self.kind == "array"

    @property
    def is_vector(self):
        return self.kind == "array" and (self.rows == 1 or self.cols == 1)

    def __str__(self):
        if self.kind == "array":
            r = "?" if self.rows is None else self.rows
            c = "?" if self.cols is None else self.cols
            return f"array({r}x{c})"
        return self.kind

    def to_dict(self):
        return {"kind": self.kind, "rows": self.rows, "cols": self.cols, "text": str(self)}


SCALAR, BOOL, UNKNOWN, NONE = MType("scalar"), MType("bool"), MType("unknown"), MType("none")
STRING, CELL, STRUCT, FUNC = MType("string"), MType("cell"), MType("struct"), MType("func")


def array(rows=None, cols=None):
    if rows == 1 and cols == 1:
        return SCALAR
    return MType("array", rows, cols)


def parse_type(text, size=""):
    text = text.lower()
    dims = [int(x) for x in re.findall(r"\d+", size or "")]
    if text in ("scalar", "double", "float"):
        return SCALAR
    if text in ("bool", "logical"):
        return BOOL
    if text in ("vector", "column", "col"):
        return array(dims[0] if dims else None, 1)
    if text == "row":
        return array(1, dims[0] if dims else None)
    if text == "matrix":
        return array(*(dims + [None, None])[:2])
    if text in ("string", "char"):
        return STRING
    if text == "struct":
        return STRUCT
    if text == "cell":
        return CELL
    raise ValueError(f"unbekannter Typ '{text}' (erlaubt: scalar, bool, vector, row, matrix, string, struct, cell)")


def join(a, b):
    if a is None or a.kind in ("unknown", "none"):
        return b if b is not None else a
    if b is None or b.kind in ("unknown", "none"):
        return a
    if a == b:
        return a
    if a.is_scalar and b.is_scalar:
        return SCALAR
    if a.is_array or b.is_array:
        ar = a if a.is_array else None
        br = b if b.is_array else None
        if ar and br:
            return array(ar.rows if ar.rows == br.rows else None, ar.cols if ar.cols == br.cols else None)
        return ar or br
    return UNKNOWN


def broadcast(a, b):
    if a.is_scalar and b.is_scalar:
        return SCALAR
    if a.is_scalar:
        return b if b.is_array else UNKNOWN
    if b.is_scalar:
        return a if a.is_array else UNKNOWN
    if a.is_array and b.is_array:
        def d(x, y):
            if x == 1:
                return y
            if y == 1:
                return x
            return x if x == y else (x if y is None else y if x is None else None)
        return array(d(a.rows, b.rows), d(a.cols, b.cols))
    return UNKNOWN


def const_value(e):
    # constant folding for literal sizes (zeros(3, 1), 1:4, 2*n with literal n)
    if isinstance(e, N.Number) and not isinstance(e.value, complex):
        return float(e.value)
    if isinstance(e, N.Unary) and e.op in "+-":
        v = const_value(e.operand)
        return None if v is None else (v if e.op == "+" else -v)
    if isinstance(e, N.Binary) and e.op in ("+", "-", "*", "/", ".*", "./", "^"):
        a, b = const_value(e.left), const_value(e.right)
        if a is None or b is None:
            return None
        try:
            return {"+": a + b, "-": a - b, "*": a * b, ".*": a * b, "/": a / b, "./": a / b, "^": a ** b}[e.op]
        except (ZeroDivisionError, OverflowError):
            return None
    return None


def _int_or_none(v):
    return int(v) if v is not None and float(v).is_integer() else None


class FunctionTypes:
    """Inferred types of one function for a given input signature."""

    def __init__(self, func, inputs, outputs, env):
        self.func, self.inputs, self.outputs, self.env = func, inputs, outputs, env

    def var(self, name):
        return self.env.get(name, UNKNOWN)


class TypeInference:
    def __init__(self, mfile, input_types=None):
        self.mfile = mfile
        self.local = {f.name: f for f in mfile.all_functions()}
        self.hints = dict(_pragmas(mfile))
        for k, v in (input_types or {}).items():
            self.hints[k] = parse_type(*v) if isinstance(v, tuple) else parse_type(v) if isinstance(v, str) else v
        self.cache = {}
        self._active = set()
        self.unknown_calls = set()

    # ------------------------------------------------------------------ entry
    def infer_entry(self, func):
        sig = tuple(self.hints.get(p, None) or self._usage_type(func, p) for p in func.params)
        return self.infer(func, sig)

    def _usage_type(self, func, name):
        for node in _walk_body(func.body):
            if isinstance(node, N.Index) and isinstance(node.base, N.Ident) and node.base.name == name:
                return array()
            if isinstance(node, N.Index) and isinstance(node.base, N.Ident) and node.base.name in _ARRAY_HINT_FUNCS \
                    and node.base.name not in self.local and node.args and isinstance(node.args[0], N.Ident) \
                    and node.args[0].name == name:
                return array()
            if isinstance(node, N.For) and isinstance(node.iterable, N.Ident) and node.iterable.name == name:
                return array(1, None)
            if isinstance(node, (N.Field, N.DynField)) and isinstance(node.base, N.Ident) and node.base.name == name:
                return STRUCT
            if isinstance(node, N.CellIndex) and isinstance(node.base, N.Ident) and node.base.name == name:
                return CELL
        return SCALAR

    def infer(self, func, sig):
        key = (func.name, sig)
        if key in self.cache:
            return self.cache[key]
        if key in self._active:      # recursion: assume scalars until the fixed point
            return FunctionTypes(func, sig, [SCALAR] * len(func.outputs), {})
        self._active.add(key)
        env = {p: t for p, t in zip(func.params, sig)}
        for _ in range(12):
            before = dict(env)
            self._block(func.body, env, func)
            if env == before:
                break
        outs = [env.get(o, UNKNOWN) for o in func.outputs]
        ft = FunctionTypes(func, sig, outs, env)
        self._active.discard(key)
        self.cache[key] = ft
        return ft

    # ------------------------------------------------------------------ statements
    def _set(self, env, name, t):
        env[name] = join(env.get(name), t)

    def _block(self, body, env, func):
        for s in body:
            self._stmt(s, env, func)

    def _stmt(self, s, env, func):
        if isinstance(s, N.Assign):
            if len(s.targets) > 1 or s.multi:
                types = self.expr_multi(s.value, env, len(s.targets))
                for tg, t in zip(s.targets, types + [UNKNOWN] * len(s.targets)):
                    self._assign(tg, t, env)
            else:
                self._assign(s.targets[0], self.expr(s.value, env), env)
        elif isinstance(s, N.ExprStmt):
            self.expr(s.expr, env)
        elif isinstance(s, N.If):
            for c, b in s.clauses:
                self.expr(c, env)
                self._block(b, env, func)
            if s.else_body:
                self._block(s.else_body, env, func)
        elif isinstance(s, N.For):
            it = self.expr(s.iterable, env)
            self._set(env, s.var, SCALAR if it.is_array and it.rows == 1 or it.is_scalar else
                      array(it.rows, 1) if it.is_array else UNKNOWN)
            self._block(s.body, env, func)
        elif isinstance(s, N.While):
            self.expr(s.cond, env)
            self._block(s.body, env, func)
        elif isinstance(s, N.Switch):
            self.expr(s.subject, env)
            for v, b in s.cases:
                self._block(b, env, func)
            if s.otherwise:
                self._block(s.otherwise, env, func)
        elif isinstance(s, N.TryCatch):
            self._block(s.body, env, func)
            if s.ident:
                self._set(env, s.ident, STRUCT)
            self._block(s.catch_body, env, func)
        elif isinstance(s, (N.Global, N.Persistent)):
            for n in s.names:
                env.setdefault(n, NONE)

    def _assign(self, target, t, env):
        if isinstance(target, N.Ident):
            self._set(env, target.name, t)
        elif isinstance(target, N.Index) and isinstance(target.base, N.Ident):
            name = target.base.name
            cur = env.get(name)
            if cur is not None and cur.kind in ("cell", "struct"):
                return
            self._set(env, name, array() if cur is None or cur.kind in ("none", "unknown") or cur.is_scalar else cur)
        elif isinstance(target, (N.Field, N.DynField)):
            base = target
            while not isinstance(base, N.Ident):
                base = base.base
            self._set(env, base.name, STRUCT)
        elif isinstance(target, N.CellIndex):
            base = target
            while not isinstance(base, N.Ident):
                base = base.base
            self._set(env, base.name, CELL)

    # ------------------------------------------------------------------ expressions
    def expr(self, e, env):
        r = self.expr_multi(e, env, 1)
        return r[0] if r else NONE

    def expr_multi(self, e, env, nargout):
        if isinstance(e, N.Number):
            return [SCALAR]
        if isinstance(e, N.String):
            return [STRING]
        if isinstance(e, N.Ident):
            if e.name in env:
                return [env[e.name]]
            return self.call(e.name, [], [], env, nargout)
        if isinstance(e, N.Binary):
            a, b = self.expr(e.left, env), self.expr(e.right, env)
            if e.op in ("&&", "||"):
                return [BOOL]
            if e.op in ("==", "~=", "<", "<=", ">", ">=", "&", "|"):
                r = broadcast(a, b)
                return [BOOL if r.is_scalar else r]
            if e.op == "*" and a.is_array and b.is_array:
                return [array(a.rows, b.cols)]
            if e.op in ("/", "\\") and a.is_array and b.is_array:
                return [array(a.rows if e.op == "/" else a.cols, b.rows if e.op == "/" else b.cols)]
            if e.op == "^" and a.is_array:
                return [a]
            r = broadcast(a, b)
            return [SCALAR if r.kind == "bool" else r]
        if isinstance(e, N.Unary):
            t = self.expr(e.operand, env)
            if e.op == "~":
                return [BOOL if t.is_scalar else t]
            return [SCALAR if t.kind == "bool" else t]
        if isinstance(e, N.Postfix):
            t = self.expr(e.operand, env)
            return [array(t.cols, t.rows) if t.is_array else t]
        if isinstance(e, N.Range):
            vals = [const_value(x) for x in (e.start, e.step or N.Number(1.0), e.stop)]
            for x in (e.start, e.step, e.stop):
                if x is not None:
                    self.expr(x, env)
            n = None
            if all(v is not None for v in vals) and vals[1] != 0:
                n = max(0, int((vals[2] - vals[0]) // vals[1]) + 1)
            return [array(1, n)]
        if isinstance(e, N.Matrix):
            if not e.rows:
                return [array(0, 0)]
            rows_total, cols = 0, None
            for row in e.rows:
                ts = [self.expr(x, env) for x in row]
                if any(t.kind == "string" for t in ts):
                    return [STRING]
                if any(t.kind == "cell" for t in ts):
                    return [CELL]
                h = ts[0].rows if ts[0].is_array else 1
                w = 0
                for t in ts:
                    c = 1 if t.is_scalar else t.cols if t.is_array else None
                    w = None if w is None or c is None else w + c
                rows_total = None if rows_total is None or h is None else rows_total + h
                cols = w if cols is None else (cols if cols == w else None)
            return [array(rows_total, cols)]
        if isinstance(e, N.CellArray):
            for row in e.rows:
                for x in row:
                    self.expr(x, env)
            return [CELL]
        if isinstance(e, N.Index):
            if isinstance(e.base, N.Ident) and e.base.name not in env:
                ts = [self.expr(a, env) if not isinstance(a, N.Colon) else UNKNOWN for a in e.args]
                return self.call(e.base.name, ts, e.args, env, nargout)
            bt = self.expr(e.base, env)
            if bt.kind == "func":
                for a in e.args:
                    self.expr(a, env)
                return [SCALAR]
            if bt.kind in ("cell", "struct", "string"):
                return [bt]
            ts = [self._index_arg(a, env) for a in e.args]
            if all(t.is_scalar for t in ts):
                return [SCALAR]
            if len(ts) == 1:
                t = ts[0]
                n = None if t.kind != "array" else (t.cols if t.rows == 1 else t.rows if t.cols == 1 else None)
                if t.kind == "colon":
                    return [array(None if bt.rows is None or bt.cols is None else bt.rows * bt.cols, 1)]
                if bt.is_array and bt.cols == 1:
                    return [array(n, 1)]
                return [array(1, n) if bt.is_array and bt.rows == 1 else array()]
            dims = []
            for t, full in zip(ts, (bt.rows if bt.is_array else None, bt.cols if bt.is_array else None)):
                dims.append(1 if t.is_scalar else full if t.kind == "colon" else
                            (t.cols if t.rows == 1 else t.rows) if t.kind == "array" else None)
            return [array(*dims[:2])]
        if isinstance(e, N.CellIndex):
            self.expr(e.base, env)
            return [UNKNOWN]
        if isinstance(e, (N.Field, N.DynField)):
            self.expr(e.base, env)
            return [UNKNOWN]
        if isinstance(e, N.AnonFunc):
            return [FUNC]
        if isinstance(e, N.FuncHandle):
            return [FUNC]
        if isinstance(e, N.End):
            return [SCALAR]
        if isinstance(e, N.Colon):
            return [MType("colon")]
        return [UNKNOWN]

    def _index_arg(self, a, env):
        if isinstance(a, N.Colon):
            return MType("colon")
        t = self.expr(a, env)
        return SCALAR if t.kind == "bool" else t

    def call(self, name, arg_types, arg_nodes, env, nargout):
        if name in self.local:
            f = self.local[name]
            sig = tuple(arg_types) + tuple(self.hints.get(p) or SCALAR for p in f.params[len(arg_types):])
            ft = self.infer(f, sig[:len(f.params)])
            return list(ft.outputs[:max(nargout, 1)])
        return builtin_type(name, arg_types, arg_nodes, nargout, self)


def builtin_type(name, ts, nodes, nargout, inf=None):
    t0 = ts[0] if ts else NONE
    if name in _CONSTANTS or name in ("rand", "randn", "zeros", "ones", "eye", "nan", "NaN", "inf", "Inf"):
        if not ts:
            return [SCALAR]
        if len(ts) == 1 and t0.is_scalar:
            n = _int_or_none(const_value(nodes[0])) if nodes else None
            return [array(n, n)]
        if len(ts) >= 2:
            r = _int_or_none(const_value(nodes[0]))
            c = _int_or_none(const_value(nodes[1]))
            return [array(r, c)]
        if len(ts) == 1 and t0.is_array:       # zeros(size(x))
            return [array()]
        return [array()]
    if name in ("true", "false"):
        return [BOOL] if not ts else [array()]
    if name in ("i", "j"):
        return [SCALAR]
    if name in _ELEMENTWISE:
        return [SCALAR if t0.kind == "bool" else t0]
    if name in _BINARY_ELEMENTWISE:
        return [broadcast(t0, ts[1] if len(ts) > 1 else SCALAR)]
    if name in ("max", "min"):
        if len(ts) >= 2 and not (ts[1].is_array and ts[1].rows == 0):
            return [broadcast(t0, ts[1])]
    if name in _REDUCTIONS:
        if len(ts) >= 2 and name not in ("max", "min", "std", "var"):
            return [array()]
        if t0.is_scalar:
            r = SCALAR
        elif t0.is_array and t0.rows not in (None, 1) and t0.cols not in (None, 1):
            r = array(1, t0.cols)
        else:
            r = SCALAR
        return [r, r] if nargout >= 2 else [r]
    if name in _SCALAR_RESULT:
        return [SCALAR]
    if name in _BOOL_RESULT:
        return [BOOL]
    if name in ("any", "all"):
        return [BOOL if (t0.is_scalar or t0.is_vector or (t0.is_array and None in (t0.rows, t0.cols))) else array()]
    if name in ("isnan", "isinf", "isfinite", "logical"):
        return [BOOL if t0.is_scalar else t0]
    if name == "size":
        if len(ts) >= 2 or nargout >= 2:
            return [SCALAR] * max(nargout, 1)
        return [array(1, 2)]
    if name == "linspace":
        n = _int_or_none(const_value(nodes[2])) if len(nodes) > 2 else 100
        return [array(1, n)]
    if name == "colon":
        return [array(1, None)]
    if name in ("cumsum", "cumprod", "fliplr", "flipud", "sort"):
        return [t0] * max(nargout, 1)
    if name in ("transpose", "ctranspose"):
        return [array(t0.cols, t0.rows) if t0.is_array else t0]
    if name == "diff":
        return [array(None if t0.rows not in (1,) else 1, None if t0.cols not in (1,) else 1)]
    if name in ("find",):
        return [array()] * max(nargout, 1)
    if name == "interp1":
        q = ts[2] if len(ts) > 2 and ts[2].kind != "string" else ts[1] if len(ts) > 1 else SCALAR
        return [q]
    if name in ("inv", "pinv"):
        return [t0]
    if name in ("repmat", "reshape", "diag", "kron", "cross", "horzcat", "vertcat", "polyfit"):
        return [array()]
    if name == "polyval":
        return [ts[1] if len(ts) > 1 else SCALAR]
    if name in _STRING_RESULT:
        return [STRING]
    if name in _NO_RESULT:
        return []
    if name in ("struct",):
        return [STRUCT]
    if name in ("cell", "fieldnames"):
        return [CELL]
    if name in ("feval", "arrayfun", "cellfun", "deal", "str2func"):
        return [UNKNOWN] * max(nargout, 1)
    if inf is not None:
        inf.unknown_calls.add(name)
    return [UNKNOWN] * max(nargout, 1)


def _walk_body(body):
    for s in body:
        yield from s.walk()


def _pragmas(mfile):
    for c in mfile.comments:
        for line in c.text.split("\n"):
            m = PRAGMA.match(line)
            if m:
                yield m.group(1), parse_type(m.group(2), m.group(3) or "")


@trace("aho2006", section="6.5", concept="matlab_type_inference", note="flow-insensitive shape lattice")
def infer_types(mfile, function=None, input_types=None):
    """Infer the types of all variables of ``function`` (default: main) -> FunctionTypes."""
    ti = TypeInference(mfile, input_types)
    return ti.infer_entry(mfile.function(function)), ti
