"""Built-in function registry of the interpreter.

    @builtin("hypot")                      # plain function of the evaluated arguments
    def _hypot(a, b): ...

    @builtin("max", multi=True)            # receives nargout=..., may return a tuple
    @builtin("disp", ctx=True)             # receives the interpreter as first argument

Own functions are added with ``register_builtin(name, func, multi=False, ctx=False)``;
type/shape rules for the code generators live in ``typeinfer.BUILTIN_TYPES``.

Scalar arguments are evaluated with ``math`` (the same functions the generated Python code
uses), arrays with numpy; domain errors fall back to the complex result like MATLAB.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass

import numpy as np

from .errors import MatlabRuntimeError
from .pyruntime import (
    COLON,
    m_arr,
    m_cat,
    m_colon,
    m_get,
    m_mod,
    m_norm,
    m_rem,
    m_round,
    m_sign,
    m_sprintf,
    m_wrap_to_pi,
)


@dataclass
class BuiltinSpec:
    name: str
    func: object
    multi: bool = False       # receives nargout, returns tuple for several outputs
    ctx: bool = False         # receives the interpreter


BUILTINS: dict[str, BuiltinSpec] = {}


def register_builtin(name, func, multi=False, ctx=False):
    BUILTINS[name] = BuiltinSpec(name, func, multi, ctx)
    return func


def builtin(*names, multi=False, ctx=False):
    def deco(f):
        for n in names:
            register_builtin(n, f, multi, ctx)
        return f
    return deco


class MStruct(dict):
    """Scalar MATLAB struct (ordered fields, value semantics through copy on assignment)."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def copy(self):
        return MStruct(self)


class MCell:
    """Cell array: 2-D numpy object array."""

    def __init__(self, data):
        self.data = data if isinstance(data, np.ndarray) else np.empty((0, 0), dtype=object)

    @classmethod
    def from_rows(cls, rows):
        rows = [r for r in rows if r]
        if not rows:
            return cls(np.empty((0, 0), dtype=object))
        w = len(rows[0])
        if any(len(r) != w for r in rows):
            raise MatlabRuntimeError("Zellen-Verkettung: Zeilen unterschiedlicher Länge")
        a = np.empty((len(rows), w), dtype=object)
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                a[i, j] = v
        return cls(a)

    @property
    def shape(self):
        return self.data.shape

    def copy(self):
        return MCell(self.data.copy())

    def __repr__(self):
        return f"MCell({self.data.tolist()})"


class MFunction:
    """Function handle: named (@sin, @local) or anonymous (@(x) x.^2 with captured workspace)."""

    def __init__(self, name=None, params=None, body=None, captured=None, interp=None, text=""):
        self.name, self.params, self.body, self.captured, self.interp = name, params, body, captured, interp
        self.text = text

    def __call__(self, *args):
        out = self.interp.call_handle(self, list(args), 1)
        return out[0] if out else None

    def __repr__(self):
        return f"@{self.name}" if self.name else f"@({', '.join(self.params)}) {self.text}"


# ----------------------------------------------------------------------------- helpers
def _is_scalar(v):
    return isinstance(v, (int, float, bool, complex, np.floating, np.integer, np.bool_))


def _num(v):
    # numeric array view (bool/char -> float)
    a = m_arr(v)
    return a.astype(float) if a.dtype == bool or a.dtype.kind == "U" else a


def _dim(a, dim=None):
    if dim is not None:
        d = int(dim) - 1
        if d not in (0, 1):
            raise MatlabRuntimeError("nur Dimensionen 1 und 2 werden unterstützt")
        return d
    return 0 if a.shape[0] != 1 else 1


def elementwise(name, fn, npfn, domain=None):
    # scalar via math (bitwise identical to generated Python), arrays via numpy
    def f(x):
        if isinstance(x, complex):
            return m_norm(getattr(cmath, fn.__name__)(x)) if hasattr(cmath, fn.__name__) else m_norm(npfn(x))
        if _is_scalar(x):
            x = float(x)
            try:
                return fn(x)
            except (ValueError, OverflowError):
                with np.errstate(all="ignore"):
                    return m_norm((domain or npfn)(x))
        a = _num(x)
        with np.errstate(all="ignore"):
            if domain is not None and not np.iscomplexobj(a):
                return m_norm(domain(a))
            return m_norm(npfn(a))
    register_builtin(name, f)
    return f


def _safe_log(x):
    return -math.inf if x == 0 else math.log(x)


def _emath_log(a):
    return np.emath.log(a) if np.any(np.asarray(a) < 0) else np.log(a)


for _n, _f, _np, _dom in [
        ("sin", math.sin, np.sin, None), ("cos", math.cos, np.cos, None), ("tan", math.tan, np.tan, None),
        ("asin", math.asin, np.arcsin, lambda a: np.emath.arcsin(a) if np.any(np.abs(a) > 1) else np.arcsin(a)),
        ("acos", math.acos, np.arccos, lambda a: np.emath.arccos(a) if np.any(np.abs(a) > 1) else np.arccos(a)),
        ("atan", math.atan, np.arctan, None), ("sinh", math.sinh, np.sinh, None), ("cosh", math.cosh, np.cosh, None),
        ("tanh", math.tanh, np.tanh, None), ("exp", math.exp, np.exp, None),
        ("sqrt", math.sqrt, np.sqrt, lambda a: np.emath.sqrt(a) if np.any(np.asarray(a) < 0) else np.sqrt(a)),
        ("log", _safe_log, np.log, _emath_log),
        ("log10", lambda x: -math.inf if x == 0 else math.log10(x), np.log10,
         lambda a: np.emath.log10(a) if np.any(np.asarray(a) < 0) else np.log10(a)),
        ("log2", lambda x: -math.inf if x == 0 else math.log2(x), np.log2,
         lambda a: np.emath.log2(a) if np.any(np.asarray(a) < 0) else np.log2(a)),
        ("floor", math.floor, np.floor, None), ("ceil", math.ceil, np.ceil, None),
        ("fix", math.trunc, np.trunc, None)]:
    elementwise(_n, _f, _np, _dom)


def _wrap_int(f):
    # math.floor & co. return int; keep float
    def g(x):
        r = f(x)
        return float(r) if isinstance(r, int) and not isinstance(r, bool) else r
    return g


for _n in ("floor", "ceil", "fix"):
    BUILTINS[_n].func = _wrap_int(BUILTINS[_n].func)


@builtin("abs")
def _abs(x):
    if _is_scalar(x):
        return abs(complex(x)) if isinstance(x, complex) else abs(float(x))
    return m_norm(np.abs(_num(x)))


@builtin("round")
def _round(x, n=None):
    if n is not None:
        f = 10.0 ** n
        return m_norm(m_round(_num(x) * f) / f) if not _is_scalar(x) else m_round(float(x) * f) / f
    return m_round(float(x)) if _is_scalar(x) else m_norm(m_round(_num(x)))


@builtin("sign")
def _sign(x):
    return m_sign(float(x)) if _is_scalar(x) else m_norm(m_sign(_num(x)))


@builtin("mod")
def _mod(a, m):
    if _is_scalar(a) and _is_scalar(m):
        return m_mod(float(a), float(m))
    return m_norm(m_mod(_num(a), _num(m)))


@builtin("rem")
def _rem(a, b):
    if _is_scalar(a) and _is_scalar(b):
        return m_rem(float(a), float(b))
    return m_norm(m_rem(_num(a), _num(b)))


@builtin("atan2")
def _atan2(y, x):
    if _is_scalar(y) and _is_scalar(x):
        return math.atan2(float(y), float(x))
    return m_norm(np.arctan2(_num(y), _num(x)))


@builtin("hypot")
def _hypot(a, b):
    if _is_scalar(a) and _is_scalar(b):
        return math.hypot(float(a), float(b))
    return m_norm(np.hypot(_num(a), _num(b)))


@builtin("power")
def _power(a, b):
    from .interpreter import binary_op
    return binary_op(".^", a, b)


@builtin("deg2rad")
def _deg2rad(x):
    return float(x) * (math.pi / 180) if _is_scalar(x) else m_norm(_num(x) * (math.pi / 180))


@builtin("rad2deg")
def _rad2deg(x):
    return float(x) * (180 / math.pi) if _is_scalar(x) else m_norm(_num(x) * (180 / math.pi))


@builtin("wrapToPi")
def _wrap_to_pi(x):
    # Mapping Toolbox: wrap to [-pi, pi], positive odd multiples of pi map to pi
    return m_wrap_to_pi(float(x)) if _is_scalar(x) else m_norm(m_wrap_to_pi(_num(x)))


@builtin("wrapTo2Pi")
def _wrap_to_2pi(x):
    if _is_scalar(x):
        x = float(x)
        w = m_mod(x, 2 * math.pi)
        return 2 * math.pi if (w == 0 and x > 0) else w
    a = _num(x)
    w = m_mod(a, 2 * math.pi)
    return m_norm(np.where((w == 0) & (a > 0), 2 * math.pi, w))


for _n, _f in [("real", np.real), ("imag", np.imag), ("conj", np.conj), ("angle", np.angle)]:
    register_builtin(_n, lambda x, _f=_f: m_norm(_f(np.asarray(x) if not _is_scalar(x) else complex(x))))


@builtin("complex")
def _complex(a, b=0.0):
    return m_norm(np.asarray(a) + 1j * np.asarray(b)) if not (_is_scalar(a) and _is_scalar(b)) else \
        complex(float(a), float(b))


# ----------------------------------------------------------------------------- constants / constructors
def _shape_args(args):
    if not args:
        return 1, 1
    args = [a for a in args if not isinstance(a, str)]
    if len(args) == 1:
        a = args[0]
        if _is_scalar(a):
            return int(a), int(a)
        v = m_arr(a).ravel()
        return int(v[0]), int(v[1])
    return int(args[0]), int(args[1])


def _filled(value):
    def f(*args):
        r, c = _shape_args(args)
        return m_norm(np.full((max(r, 0), max(c, 0)), value, dtype=float))
    return f


register_builtin("zeros", _filled(0.0))
register_builtin("ones", _filled(1.0))
for _n, _v in [("pi", math.pi), ("Inf", math.inf), ("inf", math.inf), ("NaN", math.nan), ("nan", math.nan)]:
    register_builtin(_n, _filled(_v))
register_builtin("true", lambda *a: m_norm(np.ones(_shape_args(a), dtype=bool)))
register_builtin("false", lambda *a: m_norm(np.zeros(_shape_args(a), dtype=bool)))
register_builtin("i", lambda: 1j)
register_builtin("j", lambda: 1j)
register_builtin("realmax", lambda: 1.7976931348623157e308)
register_builtin("realmin", lambda: 2.2250738585072014e-308)


@builtin("eps")
def _eps(x=None):
    if x is None or isinstance(x, str):
        return 2.220446049250313e-16
    return m_norm(np.spacing(np.abs(_num(x)))) if not _is_scalar(x) else float(np.spacing(abs(float(x))))


@builtin("eye")
def _eye(*args):
    r, c = _shape_args(args)
    return m_norm(np.eye(r, c))


@builtin("rand", "randn", ctx=True)
def _rand(ctx, *args):
    r, c = _shape_args(args)
    gen = ctx.rng.standard_normal if ctx._current_builtin == "randn" else ctx.rng.random
    return m_norm(gen((r, c)))


@builtin("linspace")
def _linspace(a, b, n=100):
    n = int(n)
    if n < 1:
        return np.zeros((1, 0))
    if n == 1:
        return float(b)
    return m_norm(np.linspace(float(a), float(b), n).reshape(1, -1))


@builtin("colon")
def _colon(a, b, c=None):
    return m_norm(m_colon(float(a), 1.0, float(b)) if c is None else m_colon(float(a), float(b), float(c)))


@builtin("repmat")
def _repmat(a, m, n=None):
    if n is None:
        m, n = _shape_args([m])
    return m_norm(np.tile(m_arr(a), (int(m), int(n))))


@builtin("reshape")
def _reshape(a, *dims):
    r, c = _shape_args(dims) if len(dims) != 2 or not any(isinstance(d, np.ndarray) and d.size == 0 for d in dims) \
        else (None, None)
    A = m_arr(a)
    if r is None:
        r, c = (A.size // int(dims[1]), int(dims[1])) if isinstance(dims[0], np.ndarray) else (int(dims[0]),
                                                                                              A.size // int(dims[0]))
    if r * c != A.size:
        raise MatlabRuntimeError(f"reshape: {A.size} Elemente passen nicht in {r}x{c}")
    return m_norm(A.reshape((r, c), order="F"))


@builtin("diag")
def _diag(a):
    A = m_arr(a)
    return m_norm(np.diag(A.ravel()) if 1 in A.shape else np.diag(A).reshape(-1, 1))


@builtin("cell")
def _cell(*args):
    r, c = _shape_args(args)
    data = np.empty((r, c), dtype=object)
    for idx in np.ndindex(r, c):
        data[idx] = np.zeros((0, 0))
    return MCell(data)


@builtin("struct")
def _struct(*args):
    s = MStruct()
    for k in range(0, len(args) - 1, 2):
        v = args[k + 1]
        if isinstance(v, MCell):
            if v.data.size != 1:
                raise MatlabRuntimeError("Struct-Arrays werden nicht unterstützt")
            v = v.data.flat[0]
        s[args[k]] = v
    return s


@builtin("fieldnames")
def _fieldnames(s):
    return MCell.from_rows([[k] for k in s.keys()])


@builtin("isfield")
def _isfield(s, name):
    return isinstance(s, MStruct) and name in s


@builtin("rmfield")
def _rmfield(s, name):
    out = s.copy()
    out.pop(name, None)
    return out


# ----------------------------------------------------------------------------- size / type queries
def _shape(x):
    if isinstance(x, str):
        return (1, len(x))
    if isinstance(x, MCell):
        return x.shape
    if isinstance(x, (MStruct, MFunction)) or _is_scalar(x):
        return (1, 1)
    return m_arr(x).shape


@builtin("size", multi=True)
def _size(x, dim=None, nargout=1):
    s = _shape(x)
    if dim is not None:
        return float(s[int(dim) - 1]) if int(dim) <= 2 else 1.0
    if nargout <= 1:
        return np.array([[float(s[0]), float(s[1])]])
    return tuple([float(s[0]), float(s[1])] + [1.0] * (nargout - 2))


register_builtin("numel", lambda x: float(np.prod(_shape(x))))
register_builtin("length", lambda x: 0.0 if 0 in _shape(x) else float(max(_shape(x))))
register_builtin("ndims", lambda x: 2.0)
register_builtin("isempty", lambda x: 0 in _shape(x))
register_builtin("isscalar", lambda x: _shape(x) == (1, 1))
register_builtin("isvector", lambda x: 1 in _shape(x) and _shape(x) != (0, 1) and max(_shape(x)) >= 1
                 and min(_shape(x)) == 1)
register_builtin("isrow", lambda x: _shape(x)[0] == 1)
register_builtin("iscolumn", lambda x: _shape(x)[1] == 1)
register_builtin("ismatrix", lambda x: True)
register_builtin("isnumeric", lambda x: not isinstance(x, (str, MCell, MStruct, MFunction, bool, np.bool_))
                 and not (isinstance(x, np.ndarray) and x.dtype in (bool, object) or
                          isinstance(x, np.ndarray) and x.dtype.kind == "U"))
register_builtin("ischar", lambda x: isinstance(x, str) or (isinstance(x, np.ndarray) and x.dtype.kind == "U"))
register_builtin("islogical", lambda x: isinstance(x, (bool, np.bool_)) or
                 (isinstance(x, np.ndarray) and x.dtype == bool))
register_builtin("iscell", lambda x: isinstance(x, MCell))
register_builtin("isstruct", lambda x: isinstance(x, MStruct))
register_builtin("isreal", lambda x: not np.iscomplexobj(np.asarray(x)) if not isinstance(x, (MCell, MStruct, str))
                 else True)
register_builtin("isa", lambda x, cls: {"double": not isinstance(x, (str, bool, MCell, MStruct)),
                                        "numeric": not isinstance(x, (str, bool, MCell, MStruct)),
                                        "float": not isinstance(x, (str, bool, MCell, MStruct)),
                                        "char": isinstance(x, str), "logical": isinstance(x, bool),
                                        "cell": isinstance(x, MCell), "struct": isinstance(x, MStruct),
                                        "function_handle": isinstance(x, MFunction)}.get(cls, False))
register_builtin("class", lambda x: "char" if isinstance(x, str) else "logical" if isinstance(x, (bool, np.bool_))
                 or (isinstance(x, np.ndarray) and x.dtype == bool) else "cell" if isinstance(x, MCell)
                 else "struct" if isinstance(x, MStruct) else "function_handle" if isinstance(x, MFunction)
                 else "double")
register_builtin("double", lambda x: m_norm(_num(x)) if not _is_scalar(x) else
                 (complex(x) if isinstance(x, complex) else float(x)))
register_builtin("logical", lambda x: m_norm(_num(x) != 0) if not _is_scalar(x) else bool(x))
for _n, _f in [("isnan", np.isnan), ("isinf", np.isinf), ("isfinite", np.isfinite)]:
    register_builtin(_n, lambda x, _f=_f: bool(_f(x)) if _is_scalar(x) else m_norm(_f(_num(x))))


@builtin("isequal")
def _isequal(a, *others):
    for b in others:
        if isinstance(a, str) or isinstance(b, str):
            if a != b:
                return False
        elif _shape(a) != _shape(b) or not np.array_equal(m_arr(a), m_arr(b)):
            return False
    return True


# ----------------------------------------------------------------------------- reductions
def _reduce(npfn, empty):
    def f(x, dim=None):
        a = _num(x)
        if a.size == 0 and dim is None:
            return empty
        if dim is None and 1 in a.shape:
            return m_norm(npfn(a))          # vectors: same call as the generated Python code
        return m_norm(npfn(a, axis=_dim(a, dim), keepdims=True))
    return f


register_builtin("sum", _reduce(np.sum, 0.0))
register_builtin("prod", _reduce(np.prod, 1.0))
register_builtin("mean", _reduce(np.mean, math.nan))
register_builtin("median", _reduce(np.median, math.nan))
register_builtin("any", lambda x, dim=None: bool(np.any(_num(x) != 0)) if (dim is None and 1 in _shape(x)) or
                 _is_scalar(x) else m_norm(np.any(_num(x) != 0, axis=_dim(_num(x), dim), keepdims=True)))
register_builtin("all", lambda x, dim=None: bool(np.all(_num(x) != 0)) if (dim is None and 1 in _shape(x)) or
                 _is_scalar(x) else m_norm(np.all(_num(x) != 0, axis=_dim(_num(x), dim), keepdims=True)))
register_builtin("cumsum", lambda x, dim=None: m_norm(np.cumsum(_num(x), axis=_dim(_num(x), dim))))
register_builtin("cumprod", lambda x, dim=None: m_norm(np.cumprod(_num(x), axis=_dim(_num(x), dim))))
register_builtin("nnz", lambda x: float(np.count_nonzero(_num(x))))


@builtin("std")
def _std(x, w=0, dim=None):
    a = _num(x)
    n = a.shape[_dim(a, dim)]
    return m_norm(np.std(a, axis=_dim(a, dim), keepdims=True, ddof=0 if w == 1 or n == 1 else 1))


@builtin("var")
def _var(x, w=0, dim=None):
    a = _num(x)
    n = a.shape[_dim(a, dim)]
    return m_norm(np.var(a, axis=_dim(a, dim), keepdims=True, ddof=0 if w == 1 or n == 1 else 1))


@builtin("diff")
def _diff(x, n=1, dim=None):
    a = _num(x)
    return m_norm(np.diff(a, n=int(n), axis=_dim(a, dim)))


def _minmax(name, npfn, argfn, pair):
    def f(a, b=None, dim=None, nargout=1):
        if b is not None and not (isinstance(b, np.ndarray) and b.size == 0):
            if _is_scalar(a) and _is_scalar(b):
                return float(pair(float(a), float(b)))
            return m_norm(pair(_num(a), _num(b)))
        A = _num(a)
        if A.size == 0:
            return (np.zeros((0, 0)),) * max(nargout, 1) if nargout > 1 else np.zeros((0, 0))
        if dim is None and 1 in A.shape:     # vectors: NaN-ignoring like MATLAB, same as generated code
            with np.errstate(all="ignore"):
                if np.all(np.isnan(A)):
                    return (math.nan, 1.0) if nargout >= 2 else math.nan
                val = float(np.nanmax(A) if name == "max" else np.nanmin(A))
                if nargout >= 2:
                    return val, float((np.nanargmax(A) if name == "max" else np.nanargmin(A)) + 1)
                return val
        ax = _dim(A, dim)
        with np.errstate(all="ignore"):
            nanall = np.all(np.isnan(A), axis=ax, keepdims=True)
            filled = np.where(np.isnan(A), np.inf if name == "min" else -np.inf, A)
            val = np.where(nanall, np.nan, npfn(filled, axis=ax, keepdims=True))
            idx = np.where(nanall, 0, argfn(filled, axis=ax).reshape(val.shape)) + 1.0
        if nargout >= 2:
            return m_norm(val), m_norm(idx.astype(float))
        return m_norm(val)
    register_builtin(name, f, multi=True)


_minmax("max", np.max, np.argmax, np.fmax)
_minmax("min", np.min, np.argmin, np.fmin)


@builtin("norm")
def _norm(x, p=2):
    A = _num(x)
    if A.size == 0:
        return 0.0
    if 1 in A.shape:
        v = A.ravel()
        if isinstance(p, str):
            p = {"fro": 2, "inf": np.inf, "Inf": np.inf}[p]
        return float(np.linalg.norm(v, p))
    return float(np.linalg.norm(A, {"fro": "fro", "inf": np.inf}.get(p, p) if isinstance(p, str) else p))


@builtin("dot")
def _dot(a, b):
    return float(np.sum(np.conj(_num(a).ravel()) * _num(b).ravel()))


@builtin("cross")
def _cross(a, b):
    A, B = _num(a), _num(b)
    return m_norm(np.cross(A.ravel(), B.ravel()).reshape(A.shape))


register_builtin("det", lambda a: float(np.linalg.det(_num(a))))
register_builtin("inv", lambda a: m_norm(np.linalg.inv(_num(a))))
register_builtin("pinv", lambda a: m_norm(np.linalg.pinv(_num(a))))
register_builtin("trace", lambda a: float(np.trace(_num(a))))
register_builtin("transpose", lambda a: m_norm(m_arr(a).T))
register_builtin("ctranspose", lambda a: m_norm(np.conj(m_arr(a).T)))
register_builtin("fliplr", lambda a: m_norm(m_arr(a)[:, ::-1]))
register_builtin("flipud", lambda a: m_norm(m_arr(a)[::-1, :]))
register_builtin("horzcat", lambda *a: m_cat([list(a)]))
register_builtin("vertcat", lambda *a: m_cat([[x] for x in a]))
register_builtin("kron", lambda a, b: m_norm(np.kron(_num(a), _num(b))))
register_builtin("trapz", lambda x, y=None: float(np.trapz(_num(y if y is not None else x).ravel(),
                                                          _num(x).ravel() if y is not None else None))
                 if hasattr(np, "trapz") else float(np.trapezoid(_num(y if y is not None else x).ravel(),
                                                                 _num(x).ravel() if y is not None else None)))


@builtin("polyval")
def _polyval(p, x):
    return m_norm(np.polyval(_num(p).ravel(), _num(x))) if not _is_scalar(x) else \
        float(np.polyval(_num(p).ravel(), float(x)))


@builtin("polyfit")
def _polyfit(x, y, n):
    return m_norm(np.polyfit(_num(x).ravel(), _num(y).ravel(), int(n)).reshape(1, -1))


@builtin("find", multi=True)
def _find(x, n=None, nargout=1):
    A = _num(x)
    k = np.flatnonzero(A.ravel(order="F") != 0)
    if n is not None:
        k = k[:int(n)]
    if nargout >= 2:
        r, c = np.unravel_index(k, A.shape, order="F")
        shape = (1, -1) if A.shape[0] == 1 else (-1, 1)
        return m_norm((r + 1.0).reshape(shape)), m_norm((c + 1.0).reshape(shape))
    out = (k + 1.0).reshape((1, -1) if A.shape[0] == 1 else (-1, 1))
    return m_norm(out) if out.size else np.zeros((1, 0) if A.shape[0] == 1 else (0, 1))


@builtin("sort", multi=True)
def _sort(x, *opts, nargout=1):
    A = _num(x)
    descend = any(isinstance(o, str) and o.lower() == "descend" for o in opts)
    dims = [o for o in opts if not isinstance(o, str)]
    ax = _dim(A, dims[0] if dims else None)
    idx = np.argsort(-A if descend else A, axis=ax, kind="stable")
    val = np.take_along_axis(A, idx, axis=ax)
    return (m_norm(val), m_norm(idx + 1.0)) if nargout >= 2 else m_norm(val)


@builtin("interp1")
def _interp1(x, v, xq=None, method="linear", extrap=None):
    if xq is None:
        x, v, xq = None, x, v
    if isinstance(xq, str):
        raise MatlabRuntimeError("interp1: Abfragepunkte fehlen")
    V = _num(v).ravel()
    X = np.arange(1.0, V.size + 1) if x is None else _num(x).ravel()
    Q = _num(xq)
    method = method.lower() if isinstance(method, str) else "linear"
    if isinstance(extrap, str) and method == "extrap":
        method = "linear"
    if X.size and X[0] > X[-1]:
        X, V = X[::-1], V[::-1]
    q = Q.ravel(order="F")
    if method == "linear":
        out = np.interp(q, X, V)
        if isinstance(extrap, str) and extrap == "extrap":
            lo, hi = q < X[0], q > X[-1]
            out[lo] = V[0] + (q[lo] - X[0]) * (V[1] - V[0]) / (X[1] - X[0])
            out[hi] = V[-1] + (q[hi] - X[-1]) * (V[-1] - V[-2]) / (X[-1] - X[-2])
    elif method in ("nearest", "previous", "next"):
        k = np.searchsorted(X, q, side="right") - 1
        k = np.clip(k, 0, X.size - 1)
        if method == "nearest":
            k2 = np.clip(k + 1, 0, X.size - 1)
            k = np.where(np.abs(X[k2] - q) < np.abs(q - X[k]), k2, k)
        elif method == "next":
            k = np.where(X[k] < q, np.clip(k + 1, 0, X.size - 1), k)
        out = V[k].astype(float)
    elif method in ("spline", "pchip", "cubic"):
        from scipy.interpolate import CubicSpline, PchipInterpolator
        f = CubicSpline(X, V) if method == "spline" else PchipInterpolator(X, V)
        out = f(q)
    else:
        raise MatlabRuntimeError(f"interp1: Methode '{method}' nicht unterstützt")
    if extrap is None or isinstance(extrap, str) and extrap != "extrap":
        if method != "spline":
            out = np.where((q < X[0]) | (q > X[-1]), np.nan, out)
    elif not isinstance(extrap, str):
        out = np.where((q < X[0]) | (q > X[-1]), float(extrap), out)
    return m_norm(out.reshape(Q.shape, order="F"))


# ----------------------------------------------------------------------------- logic
register_builtin("xor", lambda a, b: bool(a) != bool(b) if _is_scalar(a) and _is_scalar(b) else
                 m_norm(np.logical_xor(_num(a) != 0, _num(b) != 0)))
register_builtin("not", lambda a: (not a) if _is_scalar(a) else m_norm(_num(a) == 0))


# ----------------------------------------------------------------------------- strings / output
def _fmt_num(v):
    if isinstance(v, (bool, np.bool_)):
        return str(int(v))
    if isinstance(v, complex):
        return f"{v.real:.4f} {'+' if v.imag >= 0 else '-'} {abs(v.imag):.4f}i"
    if v == int(v) if math.isfinite(v) else False:
        return str(int(v))
    if not math.isfinite(v):
        return "NaN" if v != v else ("Inf" if v > 0 else "-Inf")
    return f"{v:.4f}" if 1e-3 <= abs(v) < 1e5 else f"{v:.4e}"


def format_value(v):
    # short display like MATLAB's 'format short'
    if isinstance(v, str):
        return v
    if isinstance(v, MStruct):
        return "\n".join(f"    {k}: {format_value(x)}" for k, x in v.items())
    if isinstance(v, MCell):
        return "{" + "; ".join(", ".join(repr(x) for x in row) for row in v.data.tolist()) + "}"
    if isinstance(v, MFunction):
        return repr(v)
    if _is_scalar(v):
        return _fmt_num(v if isinstance(v, complex) else float(v))
    a = m_arr(v)
    if a.size == 0:
        return "[]"
    return "\n".join("   " + "   ".join(_fmt_num(x if np.iscomplexobj(a) else float(x)) for x in row)
                     for row in a.tolist())


@builtin("num2str")
def _num2str(x, fmt=None):
    if isinstance(x, str):
        return x
    if fmt is not None:
        return m_sprintf(fmt if isinstance(fmt, str) else f"%.{int(fmt)}g", x)
    if _is_scalar(x):
        v = float(x) if not isinstance(x, complex) else x
        return str(int(v)) if isinstance(v, float) and math.isfinite(v) and v == int(v) else f"{v:.5g}"
    return "  ".join(_num2str(float(e)) for e in m_arr(x).ravel())


register_builtin("int2str", lambda x: _num2str(m_round(float(x))) if _is_scalar(x) else
                 _num2str(m_norm(m_round(_num(x)))))
register_builtin("mat2str", lambda x: _num2str(x) if _is_scalar(x) else
                 "[" + ";".join(" ".join(_num2str(float(e)) for e in row) for row in m_arr(x).tolist()) + "]")
register_builtin("sprintf", lambda fmt, *args: m_sprintf(fmt, *args))
register_builtin("str2double", lambda s: float(s) if _isfloat(s) else math.nan)
def _str2num(s):
    # numeric literals and matrices of literals ('3', '[1 2; 3 4]', '1, 2'); MATLAB evaluates the text with
    # eval - deliberately not done here, anything else returns [] like a failed conversion in MATLAB
    text = s.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    rows = [r for r in text.replace("\n", ";").split(";") if r.strip()]
    values = [r.replace(",", " ").split() for r in rows]
    if not values or any(len(v) != len(values[0]) for v in values) or not all(_isfloat(x) for v in values for x in v):
        return np.zeros((0, 0))
    out = np.array([[float(x) for x in v] for v in values])
    return float(out[0, 0]) if out.size == 1 else out


register_builtin("str2num", _str2num)
register_builtin("strcmp", lambda a, b: isinstance(a, str) and isinstance(b, str) and a == b)
register_builtin("strcmpi", lambda a, b: isinstance(a, str) and isinstance(b, str) and a.lower() == b.lower())
register_builtin("upper", lambda s: s.upper())
register_builtin("lower", lambda s: s.lower())
register_builtin("strtrim", lambda s: s.strip())
register_builtin("strrep", lambda s, a, b: s.replace(a, b))
register_builtin("strcat", lambda *s: "".join(x.rstrip() if isinstance(x, str) else str(x) for x in s))
register_builtin("blanks", lambda n: " " * int(n))


def _isfloat(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


@builtin("disp", ctx=True)
def _disp(ctx, x):
    ctx.write(format_value(x) + "\n")


@builtin("fprintf", ctx=True)
def _fprintf(ctx, *args):
    if args and not isinstance(args[0], str) and _is_scalar(args[0]) and len(args) > 1:
        args = args[1:]            # file id 1 (stdout) / 2 (stderr)
    ctx.write(m_sprintf(args[0], *args[1:]))


@builtin("error", ctx=True)
def _error(ctx, *args):
    if args and isinstance(args[0], str) and len(args) > 1 and ":" in args[0] and " " not in args[0] \
            and isinstance(args[1], str):
        args = args[1:]            # error(identifier, message, ...)
    msg = m_sprintf(args[0], *args[1:]) if args else "Fehler"
    raise MatlabRuntimeError(msg)


@builtin("warning", ctx=True)
def _warning(ctx, *args):
    if args and isinstance(args[0], str) and args[0] in ("on", "off", "query"):
        return None
    if args and isinstance(args[0], str) and len(args) > 1 and ":" in args[0] and " " not in args[0]:
        args = args[1:]
    ctx.write("Warnung: " + (m_sprintf(args[0], *args[1:]) if args else "") + "\n")


@builtin("assert", ctx=True)
def _assert(ctx, cond, *msg):
    from .pyruntime import m_truth
    if not m_truth(cond):
        raise MatlabRuntimeError(m_sprintf(msg[0], *msg[1:]) if msg else "Assertion fehlgeschlagen")


for _n in ("clc", "clear", "close", "format", "hold", "more", "clf", "figure", "drawnow", "pkg", "tic"):
    register_builtin(_n, lambda *a: None)
register_builtin("toc", lambda *a: 0.0)


# ----------------------------------------------------------------------------- handles / higher order
@builtin("feval", ctx=True, multi=True)
def _feval(ctx, f, *args, nargout=1):
    out = ctx.call_handle(f if isinstance(f, MFunction) else MFunction(name=f, interp=ctx), list(args), nargout)
    return tuple(out) if nargout > 1 else (out[0] if out else None)


@builtin("arrayfun", ctx=True)
def _arrayfun(ctx, f, *args):
    uniform = True
    if len(args) >= 2 and isinstance(args[-2], str) and args[-2] == "UniformOutput":
        uniform, args = bool(args[-1]), args[:-2]
    arrs = [m_arr(a) for a in args]
    shape = arrs[0].shape
    res = [ctx.call_handle(f, [m_norm(a.ravel(order="F")[k]) for a in arrs], 1)[0]
           for k in range(arrs[0].size)]
    if uniform:
        return m_norm(np.array(res, dtype=float).reshape(shape, order="F"))
    data = np.empty(shape, dtype=object)
    for k, r in enumerate(res):
        data[np.unravel_index(k, shape, order="F")] = r
    return MCell(data)


@builtin("cellfun", ctx=True)
def _cellfun(ctx, f, *args):
    uniform = True
    if len(args) >= 2 and isinstance(args[-2], str) and args[-2] == "UniformOutput":
        uniform, args = bool(args[-1]), args[:-2]
    if isinstance(f, str):
        f = MFunction(name={"isempty": "isempty", "length": "length"}.get(f, f), interp=ctx)
    cells = [a.data for a in args]
    shape = cells[0].shape
    res = [ctx.call_handle(f, [c.ravel(order="F")[k] for c in cells], 1)[0] for k in range(cells[0].size)]
    if uniform:
        return m_norm(np.array(res, dtype=float).reshape(shape, order="F"))
    data = np.empty(shape, dtype=object)
    for k, r in enumerate(res):
        data[np.unravel_index(k, shape, order="F")] = r
    return MCell(data)


@builtin("deal", multi=True)
def _deal(*args, nargout=1):
    if len(args) == 1:
        return tuple([args[0]] * max(nargout, 1)) if nargout > 1 else args[0]
    return tuple(args[:max(nargout, 1)]) if nargout > 1 else args[0]


@builtin("func2str")
def _func2str(f):
    return repr(f)


@builtin("str2func", ctx=True)
def _str2func(ctx, s):
    # 'name' -> handle to a function, '@(x) expr' -> anonymous function (as in MATLAB)
    if s.strip().startswith("@"):
        from .interpreter import Frame
        from .parser import parse
        stmt = parse(f"f__ = {s.strip()};").script[0]
        return ctx.eval(stmt.value, Frame())
    return MFunction(name=s, interp=ctx)


__all__ = ["BUILTINS", "BuiltinSpec", "MCell", "MFunction", "MStruct", "builtin", "register_builtin", "format_value",
           "COLON", "m_get"]
