"""Tree-walking interpreter for the MATLAB AST (numpy semantics, 1-based indexing).

    interp = Interpreter.from_file("examples/matlab/kin_tracking_with_orientation_stab.m")
    delta_dot, F_l = interp.call("kin_tracking_with_orientation_stab", *args, nargout=2)

Values: Python float/bool/complex for scalars, 2-D numpy arrays (column vectors (n, 1)),
str for char row vectors, MStruct / MCell / MFunction. Assignments copy (MATLAB value
semantics). Functions are resolved in the order variable -> local/nested function ->
built-in -> ``<name>.m`` on the search path (directory of the loaded file first).
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from ..framework.knowledge import trace
from . import nodes as N
from .builtins import BUILTINS, MCell, MFunction, MStruct, format_value
from .errors import MatlabError, MatlabRuntimeError
from .parser import parse, parse_file
from .pyruntime import COLON, m_arr, m_cat, m_colon, m_div, m_get, m_norm, m_pow, m_set, m_truth

EMPTY = np.zeros((0, 0))


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


class _Return(Exception):
    pass


def to_value(a):
    # Python/numpy argument -> interpreter value (1-D sequences become column vectors)
    if isinstance(a, (list, tuple)):
        a = np.asarray(a, dtype=float)
    if isinstance(a, np.ndarray) and a.ndim == 1:
        a = a.reshape(-1, 1)
    return m_norm(a)


def _is_scalar(v):
    return isinstance(v, (int, float, bool, complex, np.floating, np.integer, np.bool_))


def _sc(v):
    # scalar to float/complex (bool -> 1.0)
    return v if isinstance(v, complex) else float(v)


# ----------------------------------------------------------------------------- operators
def binary_op(op, a, b):
    if _is_scalar(a) and _is_scalar(b):
        x, y = _sc(a), _sc(b)
        if op == "+":
            return x + y
        if op == "-":
            return x - y
        if op in ("*", ".*"):
            return x * y
        if op in ("/", "./"):
            return m_div(x, y)
        if op in ("\\", ".\\"):
            return m_div(y, x)
        if op in ("^", ".^"):
            return m_norm(m_pow(x, y))
        if op == "==":
            return x == y
        if op == "~=":
            return x != y
        if op in ("<", "<=", ">", ">="):
            if isinstance(x, complex) or isinstance(y, complex):
                x, y = x.real, y.real
            return {"<": x < y, "<=": x <= y, ">": x > y, ">=": x >= y}[op]
        if op == "&":
            return bool(x) and bool(y)
        if op == "|":
            return bool(x) or bool(y)
        raise MatlabRuntimeError(f"unbekannter Operator '{op}'")
    if isinstance(a, str) and isinstance(b, str) and op in ("==", "~=") and len(a) != len(b):
        raise MatlabRuntimeError("Matrixdimensionen stimmen nicht überein (Strings unterschiedlicher Länge)")
    if isinstance(a, (MCell, MStruct, MFunction)) or isinstance(b, (MCell, MStruct, MFunction)):
        raise MatlabRuntimeError(f"Operator '{op}' ist für Zellen, Structs und Function Handles nicht definiert")
    A, B = m_arr(a), m_arr(b)
    if A.dtype.kind == "U" or A.dtype == bool:
        A = A.astype(float) if A.dtype == bool else np.vectorize(ord)(A).astype(float)
    if B.dtype.kind == "U" or B.dtype == bool:
        B = B.astype(float) if B.dtype == bool else np.vectorize(ord)(B).astype(float)
    sa, sb = A.size == 1, B.size == 1
    with np.errstate(all="ignore"):
        if op == "*" and not (sa or sb):
            if A.shape[1] != B.shape[0]:
                raise MatlabRuntimeError(f"Matrixmultiplikation: innere Dimensionen {A.shape[0]}x{A.shape[1]} "
                                         f"und {B.shape[0]}x{B.shape[1]} passen nicht")
            return m_norm(A @ B)
        if op == "/" and not sb:
            return m_norm(_solve(B.T, A.T).T)
        if op == "\\" and not sa:
            return m_norm(_solve(A, B))
        if op == "^" and not (sa and sb):
            if sb and A.shape[0] == A.shape[1] and float(B.flat[0]).is_integer():
                return m_norm(np.linalg.matrix_power(A, int(B.flat[0])))
            raise MatlabRuntimeError("'^' erfordert eine quadratische Matrix und einen ganzzahligen Exponenten "
                                     "(elementweise: '.^')")
        if not _broadcastable(A.shape, B.shape):
            raise MatlabRuntimeError(f"Matrixdimensionen stimmen nicht überein: {A.shape[0]}x{A.shape[1]} "
                                     f"{op} {B.shape[0]}x{B.shape[1]}")
        if op == "+":
            r = A + B
        elif op == "-":
            r = A - B
        elif op in ("*", ".*"):
            r = A * B
        elif op in ("/", "./"):
            r = A / B
        elif op in ("\\", ".\\"):
            r = B / A
        elif op in ("^", ".^"):
            r = np.power(A.astype(complex), B) if (np.any(A < 0) and np.any(B != np.round(B))) else np.power(A, B)
        elif op == "==":
            r = A == B
        elif op == "~=":
            r = A != B
        elif op == "<":
            r = A < B
        elif op == "<=":
            r = A <= B
        elif op == ">":
            r = A > B
        elif op == ">=":
            r = A >= B
        elif op == "&":
            r = (A != 0) & (B != 0)
        elif op == "|":
            r = (A != 0) | (B != 0)
        else:
            raise MatlabRuntimeError(f"unbekannter Operator '{op}'")
    return m_norm(r)


def _broadcastable(s1, s2):
    return all(x == y or x == 1 or y == 1 for x, y in zip(s1, s2))


def _solve(A, B):
    if A.shape[0] == A.shape[1]:
        try:
            return np.linalg.solve(A, B)
        except np.linalg.LinAlgError:
            pass
    return np.linalg.lstsq(A, B, rcond=None)[0]


def unary_op(op, v):
    if op == "+":
        return v
    if op == "-":
        if _is_scalar(v):
            return -_sc(v)
        return m_norm(-m_arr(v).astype(float) if m_arr(v).dtype == bool else -m_arr(v))
    if op == "~":
        if _is_scalar(v):
            return not v
        return m_norm(m_arr(v) == 0)
    raise MatlabRuntimeError(f"unbekannter Operator '{op}'")


# ----------------------------------------------------------------------------- frames
class Frame:
    def __init__(self, func=None, parent=None, key=""):
        self.vars = {}
        self.func, self.parent, self.key = func, parent, key
        self.global_names, self.persistent_names = set(), set()
        self.nargin = self.nargout = 0


class Interpreter:
    """Executes MATLAB functions and scripts; see module docstring."""

    def __init__(self, mfile=None, search_path=None, output=None, seed=0, max_iterations=10_000_000):
        self.files = {}                    # path -> MFile
        self.functions = {}                # name -> (Function, MFile) of the main file
        self.search_path = [Path(p) for p in (search_path or [])]
        self.globals, self.persistent = {}, {}
        self.output = output               # callable(str) or None (stdout)
        self.rng = np.random.default_rng(seed)
        self.max_iterations = max_iterations
        self.stack = []
        self._current_builtin = ""
        self._end_stack = []
        self.mfile = None
        if mfile is not None:
            self.load(mfile)

    @classmethod
    def from_file(cls, path, **kw):
        return cls(parse_file(path), **kw)

    @classmethod
    def from_source(cls, source, **kw):
        return cls(parse(source), **kw)

    def load(self, mfile):
        if isinstance(mfile, (str, Path)) and str(mfile).endswith(".m"):
            mfile = parse_file(mfile)
        self.mfile = mfile
        self.files[mfile.path] = mfile
        for f in mfile.functions:
            self.functions.setdefault(f.name, (f, mfile))
        if mfile.path:
            d = Path(mfile.path).resolve().parent
            if d not in self.search_path:
                self.search_path.insert(0, d)
        return mfile

    def reset(self):
        # clear persistent and global variables (new simulation run)
        self.persistent.clear()
        self.globals.clear()

    def write(self, text):
        if self.output is None:
            print(text, end="")
        else:
            self.output(text)

    # ------------------------------------------------------------------ public calls
    @trace("mathworks_matlab", section="Language Fundamentals", concept="matlab_interpreter")
    def call(self, name=None, *args, nargout=None):
        """Call a function of the loaded file; returns a tuple of ``nargout`` outputs."""
        func, mfile = self._lookup_function(name or self.mfile.main.name, None)
        if func is None:
            raise MatlabRuntimeError(f"Funktion '{name}' nicht gefunden")
        n = len(func.outputs) if nargout is None else nargout
        out = self.call_function(func, mfile, [to_value(a) for a in args], n)
        return tuple(out)

    def run_script(self, mfile=None, workspace=None):
        """Execute a script; returns its workspace (dict)."""
        mfile = mfile or self.mfile
        if isinstance(mfile, (str, Path)):
            mfile = self.load(mfile)
        frame = Frame(key=f"{mfile.path}:<script>")
        frame.vars.update(workspace or {})
        self.stack.append((frame, mfile))
        try:
            self.exec_block(mfile.script, frame)
        except _Return:
            pass
        finally:
            self.stack.pop()
        return frame.vars

    # ------------------------------------------------------------------ functions
    def _lookup_function(self, name, mfile):
        # local / nested function of the calling file, functions of the main file, files on the path
        files = [mfile] if mfile is not None else []
        files += [self.mfile] if self.mfile is not None else []
        for mf in files:
            if mf is None:
                continue
            for f in mf.all_functions():
                if f.name == name and (f.parent is None or self._nested_visible(f)):
                    return f, mf
        if name in self.functions:
            return self.functions[name]
        for d in self.search_path:
            p = d / f"{name}.m"
            if p.exists():
                mf = self.files.get(str(p)) or parse_file(p)
                self.files[str(p)] = mf
                if mf.functions:
                    self.functions[name] = (mf.functions[0], mf)
                    return mf.functions[0], mf
        return None, None

    def _nested_visible(self, f):
        return True

    def call_function(self, func, mfile, args, nargout):
        params = func.params
        varargin = bool(params) and params[-1] == "varargin"
        fixed = params[:-1] if varargin else params
        if len(args) > len(fixed) and not varargin:
            raise MatlabRuntimeError(f"zu viele Eingabeargumente für '{func.name}' ({len(args)} statt höchstens "
                                     f"{len(fixed)})", func.line, func.col, mfile.path)
        outs = func.outputs
        varargout = bool(outs) and outs[-1] == "varargout"
        if nargout > len(outs) and not varargout:
            raise MatlabRuntimeError(f"zu viele Ausgabeargumente für '{func.name}' ({nargout} statt höchstens "
                                     f"{len(outs)})", func.line, func.col, mfile.path)
        parent = None
        if func.parent is not None:
            for fr, _ in reversed(self.stack):
                if fr.func is not None and fr.func.name == func.parent:
                    parent = fr
                    break
        frame = Frame(func, parent, key=f"{mfile.path}:{func.name}")
        for p, a in zip(fixed, args):
            if p != "~":
                frame.vars[p] = a
        if varargin:
            frame.vars["varargin"] = MCell.from_rows([list(args[len(fixed):])]) if len(args) > len(fixed) \
                else MCell(np.empty((1, 0), dtype=object))
        frame.nargin, frame.nargout = len(args), nargout
        if len(self.stack) > 256:
            raise MatlabRuntimeError("maximale Rekursionstiefe (256) überschritten")
        self.stack.append((frame, mfile))
        try:
            self.exec_block(func.body, frame)
        except _Return:
            pass
        finally:
            self.stack.pop()
        result = []
        names = outs[:-1] if varargout else outs
        for k in range(max(nargout, 1) if outs else 0):
            if k < len(names):
                name = names[k]
                if not self._has(frame, name):
                    if k == 0 and nargout == 0:
                        break
                    raise MatlabRuntimeError(f"Ausgabe '{name}' von '{func.name}' wurde nicht zugewiesen",
                                             func.line, func.col, mfile.path)
                result.append(self._get(frame, name))
            else:
                vo = self._get(frame, "varargout") if self._has(frame, "varargout") else MCell(np.empty((1, 0),
                                                                                                       dtype=object))
                j = k - len(names)
                if j >= vo.data.size:
                    raise MatlabRuntimeError(f"varargout von '{func.name}' enthält zu wenige Elemente")
                result.append(vo.data.ravel(order="F")[j])
        return result

    def call_handle(self, f, args, nargout):
        if not isinstance(f, MFunction):
            if isinstance(f, str):
                f = MFunction(name=f, interp=self)
            else:
                raise MatlabRuntimeError("Function Handle erwartet")
        if f.name is not None:
            frame, mfile = self.stack[-1] if self.stack else (Frame(), self.mfile)
            return self._call_named(f.name, args, nargout, frame, mfile, None)
        frame = Frame(key="<anonymous>")
        frame.vars.update(f.captured)
        for p, a in zip(f.params, args):
            frame.vars[p] = a
        mfile = self.stack[-1][1] if self.stack else self.mfile
        self.stack.append((frame, mfile))
        try:
            v = self.eval_multi(f.body, frame, nargout)
        finally:
            self.stack.pop()
        return v

    def _call_named(self, name, args, nargout, frame, mfile, node):
        func, mf = self._lookup_function(name, mfile)
        if func is not None:
            return self.call_function(func, mf, args, nargout)
        spec = BUILTINS.get(name)
        if spec is not None:
            return self._call_builtin(spec, args, nargout, node, mfile)
        raise self._err(f"nicht definierte Funktion oder Variable '{name}'", node, mfile)

    def _call_builtin(self, spec, args, nargout, node, mfile):
        if any(a is COLON for a in args):
            raise self._err(f"':' ist kein gültiges Argument für '{spec.name}'", node, mfile)
        kwargs = {"nargout": nargout} if spec.multi else {}
        prev, self._current_builtin = self._current_builtin, spec.name
        try:
            r = spec.func(self, *args, **kwargs) if spec.ctx else spec.func(*args, **kwargs)
        except MatlabError as e:
            if not e.line and node is not None:
                e.line, e.col, e.path = node.line, node.col, mfile.path if mfile else ""
            raise
        except (TypeError, ValueError, IndexError, KeyError, AttributeError, np.linalg.LinAlgError) as e:
            raise self._err(f"Fehler in '{spec.name}': {e}", node, mfile) from e
        finally:
            self._current_builtin = prev
        if r is None:
            return []
        if spec.multi and isinstance(r, tuple):
            return [m_norm(x) for x in r]
        return [m_norm(r) if not isinstance(r, (str, MCell, MStruct, MFunction)) else r]

    # ------------------------------------------------------------------ variables
    def _scope(self, frame, name):
        # frame that owns `name` (nested functions share variables with their parent)
        f = frame
        while f is not None:
            if name in f.vars or name in f.global_names or name in f.persistent_names:
                return f
            f = f.parent
        return None

    def _has(self, frame, name):
        f = self._scope(frame, name)
        if f is None:
            return False
        if name in f.global_names:
            return name in self.globals
        if name in f.persistent_names:
            return True
        return True

    def _get(self, frame, name):
        f = self._scope(frame, name)
        if name in f.global_names:
            return self.globals[name]
        if name in f.persistent_names:
            return self.persistent[f.key][name]
        return f.vars[name]

    def _set(self, frame, name, value):
        f = self._scope(frame, name) or frame
        if name in f.global_names:
            self.globals[name] = value
        elif name in f.persistent_names:
            self.persistent[f.key][name] = value
        else:
            f.vars[name] = value

    def _special(self, frame, name):
        if name == "nargin":
            return float(frame.nargin)
        if name == "nargout":
            return float(frame.nargout)
        return None

    # ------------------------------------------------------------------ statements
    def _err(self, msg, node, mfile=None):
        if mfile is None and self.stack:
            mfile = self.stack[-1][1]
        return MatlabRuntimeError(msg, getattr(node, "line", 0), getattr(node, "col", 0),
                                  mfile.path if mfile is not None else "")

    def exec_block(self, body, frame):
        for s in body:
            self.exec_stmt(s, frame)

    def exec_stmt(self, s, frame):
        try:
            self._exec(s, frame)
        except (_Break, _Continue, _Return, MatlabError):
            raise
        except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError, OverflowError,
                np.linalg.LinAlgError) as e:
            raise self._err(str(e), s) from e

    def _exec(self, s, frame):
        if isinstance(s, N.Assign):
            if s.multi or len(s.targets) > 1:
                n = len(s.targets)
                values = self.eval_multi(s.value, frame, n)
                if len(values) < n:
                    raise self._err(f"zu wenige Ausgaben ({len(values)} statt {n})", s)
                for tg, v in zip(s.targets, values):
                    if not isinstance(tg, N.Placeholder):
                        self.assign(tg, v, frame)
                        self._show(tg, s, frame)
            else:
                tg = s.targets[0]
                if isinstance(s.value, N.Matrix) and not s.value.rows and isinstance(tg, N.Index):
                    self.assign(tg, None, frame, delete=True)
                else:
                    v = self.eval(s.value, frame)
                    if v is None:
                        raise self._err("Ausdruck liefert keinen Wert", s.value)
                    self.assign(tg, v, frame)
                self._show(tg, s, frame)
        elif isinstance(s, N.ExprStmt):
            e = s.expr
            if isinstance(e, N.Ident) and not self._has(frame, e.name) and self._special(frame, e.name) is None:
                out = self._call_named(e.name, [], 0, frame, self.stack[-1][1] if self.stack else None, e)
                v = out[0] if out else None
            elif isinstance(e, N.Index) and isinstance(e.base, N.Ident) and not self._has(frame, e.base.name):
                args = self._eval_args(e.args, frame, None)
                out = self._call_named(e.base.name, args, 0, frame, self.stack[-1][1] if self.stack else None, e)
                v = out[0] if out else None
            else:
                v = self.eval(e, frame)
            if v is not None:
                if not (isinstance(e, N.Ident) and self._has(frame, e.name)):
                    self._set(frame, "ans", v)
                if not s.suppress:
                    name = e.name if isinstance(e, N.Ident) and self._has(frame, e.name) else "ans"
                    self.write(f"{name} =\n{format_value(v)}\n")
        elif isinstance(s, N.If):
            for cond, body in s.clauses:
                if self._truth(self.eval(cond, frame), cond):
                    self.exec_block(body, frame)
                    return
            if s.else_body:
                self.exec_block(s.else_body, frame)
        elif isinstance(s, N.For):
            it = self.eval(s.iterable, frame)
            if isinstance(it, MCell):
                cols = [MCell(it.data[:, [k]]) for k in range(it.shape[1])]
            elif _is_scalar(it):
                cols = [it]
            elif isinstance(it, str):
                cols = list(it)
            else:
                A = m_arr(it)
                cols = [m_norm(A[:, [k]]) for k in range(A.shape[1])] if A.size else []
            for v in cols:
                self._set(frame, s.var, v)
                try:
                    self.exec_block(s.body, frame)
                except _Break:
                    break
                except _Continue:
                    continue
        elif isinstance(s, N.While):
            count = 0
            while self._truth(self.eval(s.cond, frame), s.cond):
                count += 1
                if count > self.max_iterations:
                    raise self._err(f"while-Schleife: mehr als {self.max_iterations} Iterationen", s)
                try:
                    self.exec_block(s.body, frame)
                except _Break:
                    break
                except _Continue:
                    continue
        elif isinstance(s, N.Switch):
            subject = self.eval(s.subject, frame)
            for value_expr, body in s.cases:
                value = self.eval(value_expr, frame)
                if self._case_match(subject, value):
                    self.exec_block(body, frame)
                    return
            if s.otherwise:
                self.exec_block(s.otherwise, frame)
        elif isinstance(s, N.Break):
            raise _Break()
        elif isinstance(s, N.Continue):
            raise _Continue()
        elif isinstance(s, N.Return):
            raise _Return()
        elif isinstance(s, N.Global):
            for n in s.names:
                frame.global_names.add(n)
                frame.vars.pop(n, None)
                self.globals.setdefault(n, EMPTY)
        elif isinstance(s, N.Persistent):
            store = self.persistent.setdefault(frame.key, {})
            for n in s.names:
                frame.persistent_names.add(n)
                store.setdefault(n, EMPTY)
        elif isinstance(s, N.TryCatch):
            try:
                self.exec_block(s.body, frame)
            except MatlabError as e:
                if s.ident:
                    self._set(frame, s.ident, MStruct(message=e.message, identifier=""))
                self.exec_block(s.catch_body, frame)
        elif isinstance(s, N.Command):
            if s.name == "clear" and (not s.args or s.args == ["all"]):
                frame.vars.clear()
        else:
            raise self._err(f"Anweisung {type(s).__name__} nicht unterstützt", s)

    def _truth(self, v, node):
        try:
            return m_truth(v)
        except ValueError as e:
            raise self._err(str(e), node) from e

    @staticmethod
    def _case_match(subject, value):
        if isinstance(value, MCell):
            return any(Interpreter._case_match(subject, v) for v in value.data.ravel())
        if isinstance(subject, str) or isinstance(value, str):
            return isinstance(subject, str) and isinstance(value, str) and subject == value
        if _is_scalar(subject) and _is_scalar(value):
            return _sc(subject) == _sc(value)
        return False

    def _show(self, target, stmt, frame):
        if stmt.suppress:
            return
        base = target
        while not isinstance(base, N.Ident):
            base = base.base
        self.write(f"{base.name} =\n{format_value(self._get(frame, base.name))}\n")

    # ------------------------------------------------------------------ assignment
    def assign(self, target, value, frame, delete=False):
        chain = []
        node = target
        while not isinstance(node, N.Ident):
            chain.append(node)
            node = node.base
        chain.reverse()
        name = node.name
        current = self._get(frame, name) if self._has(frame, name) else None
        self._set(frame, name, self._assign_chain(current, chain, value, frame, delete))

    def _assign_chain(self, cur, chain, value, frame, delete):
        if not chain:
            return value
        node, rest = chain[0], chain[1:]
        if isinstance(node, (N.Field, N.DynField)):
            fname = node.name if isinstance(node, N.Field) else self.eval(node.name, frame)
            if cur is None or (isinstance(cur, np.ndarray) and cur.size == 0):
                s = MStruct()
            elif isinstance(cur, MStruct):
                s = cur.copy()
            else:
                raise self._err("Feldzuweisung auf einen Wert, der kein Struct ist", node)
            s[fname] = self._assign_chain(s.get(fname), rest, value, frame, delete)
            return s
        if isinstance(node, N.Index):
            if isinstance(cur, MCell):
                args = self._eval_args(node.args, frame, cur)
                if rest:
                    raise self._err("verschachtelte Zuweisung in Zellen über '()' nicht unterstützt", node)
                if delete:
                    return MCell(np.asarray(m_set(_cell_index_array(cur), args, None, delete=True)))
                return _cell_set(cur, args, value if isinstance(value, MCell) else None, value)
            if rest:
                if isinstance(cur, MStruct) and all(self._is_one(a, frame) for a in node.args):
                    return self._assign_chain(cur, rest, value, frame, delete)
                raise self._err("Struct-Arrays (x(i).feld = ...) werden nicht unterstützt", node)
            args = self._eval_args(node.args, frame, cur if cur is not None else EMPTY)
            if delete:
                if cur is None:
                    raise self._err("Löschen aus einer nicht definierten Variable", node)
                return m_set(cur, args, None, delete=True)
            if isinstance(value, (MStruct, MCell, MFunction)):
                if all(self._is_one(a, frame) for a in node.args) and (cur is None or isinstance(cur, MStruct)):
                    return value
                raise self._err("Struct-/Zell-Arrays werden nicht unterstützt", node)
            if isinstance(cur, str) or isinstance(value, str):
                arr = list(cur) if isinstance(cur, str) else []
                s = m_set(np.array([[float(ord(c)) for c in arr]]).reshape(1, -1) if arr else None, args,
                          m_arr(value) if not isinstance(value, str) else
                          np.array([[float(ord(c)) for c in value]]))
                return "".join(chr(int(c)) for c in m_arr(s).ravel())
            return m_set(cur, args, value)
        if isinstance(node, N.CellIndex):
            c = MCell(np.empty((0, 0), dtype=object)) if cur is None or (isinstance(cur, np.ndarray) and
                                                                           cur.size == 0) else cur
            if not isinstance(c, MCell):
                raise self._err("'{}'-Zuweisung auf einen Wert, der keine Zelle ist", node)
            args = self._eval_args(node.args, frame, c)
            if rest:
                inner = _cell_get(c, args)
                inner = inner[0] if len(inner) == 1 else None
                value = self._assign_chain(inner, rest, value, frame, delete)
            return _cell_set(c, args, None, value)
        raise self._err("ungültiges Zuweisungsziel", node)

    def _is_one(self, a, frame):
        v = self.eval(a, frame)
        return _is_scalar(v) and _sc(v) == 1

    # ------------------------------------------------------------------ expressions
    def eval(self, e, frame):
        out = self.eval_multi(e, frame, 1)
        return out[0] if out else None

    def eval_multi(self, e, frame, nargout):
        # returns a list of values (several only for function calls with nargout > 1)
        if isinstance(e, N.Number):
            return [e.value]
        if isinstance(e, N.String):
            return [e.value]
        if isinstance(e, N.Ident):
            if self._has(frame, e.name):
                v = self._get(frame, e.name)
                if isinstance(v, MFunction) and nargout != 1 and False:
                    return self.call_handle(v, [], nargout)
                return [v]
            sp = self._special(frame, e.name)
            if sp is not None:
                return [sp]
            out = self._call_named(e.name, [], max(nargout, 1), frame, self._cur_file(), e)
            if not out:
                raise self._err(f"'{e.name}' liefert keinen Wert", e)
            return out
        if isinstance(e, N.Binary):
            if e.op in ("&&", "||"):
                a = self._logical_scalar(self.eval(e.left, frame), e)
                if e.op == "&&" and not a:
                    return [False]
                if e.op == "||" and a:
                    return [True]
                return [self._logical_scalar(self.eval(e.right, frame), e)]
            try:
                return [binary_op(e.op, self.eval(e.left, frame), self.eval(e.right, frame))]
            except MatlabRuntimeError as err:
                if not err.line:
                    raise self._err(err.message, e) from err
                raise
        if isinstance(e, N.Unary):
            return [unary_op(e.op, self.eval(e.operand, frame))]
        if isinstance(e, N.Postfix):
            v = self.eval(e.operand, frame)
            if _is_scalar(v):
                return [v.conjugate() if (e.op == "'" and isinstance(v, complex)) else v]
            if isinstance(v, MCell):
                return [MCell(v.data.T.copy())]
            if isinstance(v, str):
                return [np.array(list(v), dtype="<U1").reshape(-1, 1) if len(v) != 1 else v]
            A = m_arr(v)
            return [m_norm(np.conj(A.T) if e.op == "'" else A.T.copy())]
        if isinstance(e, N.Range):
            a = self.eval(e.start, frame)
            s = 1.0 if e.step is None else self.eval(e.step, frame)
            b = self.eval(e.stop, frame)
            vals = [_sc(m_arr(x).flat[0]) if not _is_scalar(x) and m_arr(x).size else x for x in (a, s, b)]
            if any(not _is_scalar(x) for x in vals):
                return [np.zeros((1, 0))]
            return [m_norm(m_colon(*[float(np.real(x)) for x in vals]))]
        if isinstance(e, N.Matrix):
            rows = []
            for row in e.rows:
                vals = []
                for x in row:
                    vals.extend(self.eval_multi(x, frame, 1) if not self._is_cs_list(x) else self._cs_list(x, frame))
                rows.append(vals)
            if any(isinstance(v, MCell) for r in rows for v in r):
                return [_cell_cat(rows)]
            try:
                return [m_cat(rows)]
            except ValueError as err:
                raise self._err(str(err), e) from err
        if isinstance(e, N.CellArray):
            rows = []
            for row in e.rows:
                vals = []
                for x in row:
                    vals.extend(self._cs_list(x, frame) if self._is_cs_list(x) else [self.eval(x, frame)])
                rows.append(vals)
            return [MCell.from_rows(rows)]
        if isinstance(e, N.Index):
            return self._eval_index(e, frame, nargout)
        if isinstance(e, N.CellIndex):
            base = self.eval(e.base, frame)
            if not isinstance(base, MCell):
                raise self._err("'{}'-Indizierung auf einen Wert, der keine Zelle ist", e)
            vals = _cell_get(base, self._eval_args(e.args, frame, base))
            return vals
        if isinstance(e, (N.Field, N.DynField)):
            base = self.eval(e.base, frame)
            name = e.name if isinstance(e, N.Field) else self.eval(e.name, frame)
            if not isinstance(base, MStruct):
                raise self._err(f"Feldzugriff '.{name}' auf einen Wert, der kein Struct ist", e)
            if name not in base:
                raise self._err(f"Struct hat kein Feld '{name}'", e)
            return [base[name]]
        if isinstance(e, N.AnonFunc):
            captured = {}
            for node in e.body.walk():
                if isinstance(node, N.Ident) and node.name not in e.params and self._has(frame, node.name):
                    captured[node.name] = self._get(frame, node.name)
            return [MFunction(params=e.params, body=e.body, captured=captured, interp=self,
                              text=_expr_text(e.body))]
        if isinstance(e, N.FuncHandle):
            return [MFunction(name=e.name, interp=self)]
        if isinstance(e, N.End):
            return [self._end_value(e)]
        if isinstance(e, N.Colon):
            return [COLON]
        raise self._err(f"Ausdruck {type(e).__name__} nicht unterstützt", e)

    def _cur_file(self):
        return self.stack[-1][1] if self.stack else self.mfile

    def _logical_scalar(self, v, node):
        if _is_scalar(v):
            return bool(v)
        a = m_arr(v)
        if a.size != 1:
            raise self._err("Operanden von '&&'/'||' müssen skalar sein", node)
        return bool(a.flat[0])

    @staticmethod
    def _is_cs_list(x):
        return isinstance(x, N.CellIndex)

    def _cs_list(self, x, frame):
        base = self.eval(x.base, frame)
        return _cell_get(base, self._eval_args(x.args, frame, base))

    def _eval_index(self, e, frame, nargout):
        base = e.base
        if isinstance(base, N.Ident) and not self._has(frame, base.name) and self._special(frame, base.name) is None:
            args = self._eval_args(e.args, frame, None)
            out = self._call_named(base.name, args, nargout, frame, self._cur_file(), e)
            if not out and nargout >= 1:
                raise self._err(f"'{base.name}' liefert keinen Wert", e)
            return out
        value = self.eval(base, frame)
        if isinstance(value, MFunction):
            return self.call_handle(value, self._eval_args(e.args, frame, None), nargout)
        args = self._eval_args(e.args, frame, value)
        if isinstance(value, MCell):
            return [MCell(np.asarray(_cell_subset(value, args)))]
        if isinstance(value, MStruct):
            if all(_is_scalar(a) and _sc(a) == 1 for a in args):
                return [value]
            raise self._err("Struct-Arrays werden nicht unterstützt", e)
        try:
            return [m_get(value, *args)]
        except (IndexError, ValueError) as err:
            raise self._err(str(err), e) from err

    def _eval_args(self, args, frame, container):
        out = []
        n = len(args)
        for k, a in enumerate(args):
            if isinstance(a, N.Colon):
                out.append(COLON)
                continue
            self._end_stack.append((container, k, n))
            try:
                if self._is_cs_list(a):
                    out.extend(self._cs_list(a, frame))
                else:
                    out.append(self.eval(a, frame))
            finally:
                self._end_stack.pop()
        return out

    def _end_value(self, node):
        if not self._end_stack or self._end_stack[-1][0] is None:
            raise self._err("'end' außerhalb eines Index", node)
        container, k, n = self._end_stack[-1]
        shape = container.shape if isinstance(container, MCell) else (1, len(container)) \
            if isinstance(container, str) else m_arr(container).shape if not isinstance(container, MStruct) else (1, 1)
        if n == 1:
            return float(shape[0] * shape[1])
        if k == 0:
            return float(shape[0])
        if k == 1:
            return float(shape[1]) if n == 2 else float(shape[1])
        return 1.0


# ----------------------------------------------------------------------------- cells
def _cell_index_array(c):
    return c.data


def _cell_get(c, args):
    data = c.data
    if len(args) == 1:
        flat = data.ravel(order="F")
        k = np.arange(flat.size) if args[0] is COLON else (np.asarray(m_arr(args[0]).ravel(order="F"), dtype=float)
                                                         .astype(int) - 1)
        if k.size and k.max() >= flat.size:
            raise MatlabRuntimeError(f"Zellindex {k.max() + 1} überschreitet die Größe ({flat.size})")
        return [flat[i] for i in k]
    r = np.arange(data.shape[0]) if args[0] is COLON else m_arr(args[0]).ravel().astype(int) - 1
    cc = np.arange(data.shape[1]) if args[1] is COLON else m_arr(args[1]).ravel().astype(int) - 1
    return [data[i, j] for j in cc for i in r]


def _cell_subset(c, args):
    data = c.data
    if len(args) == 1:
        flat = data.ravel(order="F")
        k = np.arange(flat.size) if args[0] is COLON else m_arr(args[0]).ravel(order="F").astype(int) - 1
        sub = flat[k]
        return sub.reshape(1, -1) if data.shape[0] == 1 else sub.reshape(-1, 1)
    r = np.arange(data.shape[0]) if args[0] is COLON else m_arr(args[0]).ravel().astype(int) - 1
    cc = np.arange(data.shape[1]) if args[1] is COLON else m_arr(args[1]).ravel().astype(int) - 1
    return data[np.ix_(r, cc)]


def _cell_set(c, args, cellvalue, value):
    data = c.data
    if len(args) == 1:
        k = int(_sc(args[0])) - 1 if _is_scalar(args[0]) else None
        if k is None:
            raise MatlabRuntimeError("Zellzuweisung nur mit skalarem Index unterstützt")
        n = data.size
        if k >= n:
            shape = (1, k + 1) if data.shape[0] <= 1 else (k + 1, 1) if data.shape[1] == 1 else None
            if shape is None:
                raise MatlabRuntimeError("Zelle kann mit linearem Index nicht vergrößert werden")
            new = np.empty(shape, dtype=object)
            for i in range(shape[0] * shape[1]):
                new.flat[i] = np.zeros((0, 0))
            flat = data.ravel(order="F")
            for i in range(n):
                new.ravel(order="F")[i] = flat[i]
            nf = new.ravel(order="F")
            nf[:n] = flat
            data = nf.reshape(shape, order="F")
        else:
            data = data.copy()
        flat = data.ravel(order="F").copy()
        flat[k] = cellvalue.data.flat[0] if cellvalue is not None else value
        return MCell(flat.reshape(data.shape, order="F"))
    i, j = int(_sc(args[0])) - 1, int(_sc(args[1])) - 1
    rows, cols = max(data.shape[0], i + 1), max(data.shape[1], j + 1)
    new = np.empty((rows, cols), dtype=object)
    for idx in np.ndindex(rows, cols):
        new[idx] = np.zeros((0, 0))
    new[:data.shape[0], :data.shape[1]] = data
    new[i, j] = cellvalue.data.flat[0] if cellvalue is not None else value
    return MCell(new)


def _cell_cat(rows):
    out = []
    for row in rows:
        items = []
        for v in row:
            if isinstance(v, MCell):
                items.append(v.data)
            elif isinstance(v, np.ndarray) and v.size == 0:
                continue
            else:
                a = np.empty((1, 1), dtype=object)
                a[0, 0] = v
                items.append(a)
        if items:
            out.append(np.hstack(items))
    return MCell(np.vstack(out) if out else np.empty((0, 0), dtype=object))


def _expr_text(e):
    try:
        from .latex import to_matlab
        return to_matlab(e)
    except Exception:  # pragma: no cover - display only
        return "..."


def run_function(path, *args, function=None, nargout=None, **kw):
    """Convenience: parse ``path`` and call ``function`` (default: main function)."""
    interp = Interpreter.from_file(path, **kw)
    return interp.call(function, *args, nargout=nargout)


__all__ = ["Interpreter", "binary_op", "unary_op", "run_function", "EMPTY", "math"]
