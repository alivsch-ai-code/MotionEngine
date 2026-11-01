"""MATLAB semantics helpers on top of numpy (std + numpy only).

These functions are used by the interpreter *and* copied verbatim (``inspect.getsource``)
into generated Python modules that need them, so interpreter and generated code share one
implementation of the subtle parts: column-major 1-based indexing with growth, the colon
operator, round half away from zero, mod/rem, IEEE division of scalars.

Value conventions: scalars are Python float/bool/complex, arrays are 2-D numpy arrays
(column vectors (n, 1), row vectors (1, n)), strings are Python str.
"""

import math

import numpy as np


class _MColon:
    # the magic ':' in an index
    def __repr__(self):
        return ":"


COLON = _MColon()


def m_norm(v):
    # 1x1 arrays -> Python scalars, drop all-zero imaginary parts (MATLAB does the same)
    if isinstance(v, np.ndarray):
        if v.ndim != 2:
            v = v.reshape(1, -1) if v.ndim < 2 else v.reshape(v.shape[0], -1)
        if np.iscomplexobj(v) and v.size and not np.any(v.imag):
            v = v.real.copy()
        if v.size == 1 and v.dtype != object and v.dtype.kind != "U":
            x = v.flat[0]
            if v.dtype == bool:
                return bool(x)
            if np.iscomplexobj(v):
                return complex(x)
            return float(x)
        return v
    if isinstance(v, (np.floating, np.integer)):
        return float(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, (complex, np.complexfloating)):
        return complex(v) if v.imag else float(v.real)
    if isinstance(v, int) and not isinstance(v, bool):
        return float(v)
    return v


def m_arr(v):
    # any numeric value -> 2-D numpy array (strings -> char codes)
    if isinstance(v, np.ndarray):
        return v if v.ndim == 2 else v.reshape(1, -1) if v.ndim < 2 else v.reshape(v.shape[0], -1)
    if isinstance(v, str):
        return np.array([[float(ord(c)) for c in v]]).reshape(1, len(v))
    if isinstance(v, (list, tuple)):
        a = np.asarray(v, dtype=float)
        return a.reshape(-1, 1) if a.ndim == 1 else a
    return np.array([[v]], dtype=bool if isinstance(v, (bool, np.bool_)) else
                    complex if isinstance(v, complex) else float)


def m_div(a, b):
    # scalar right division with IEEE semantics (1/0 = Inf, 0/0 = NaN)
    try:
        return a / b
    except ZeroDivisionError:
        if a == 0 or a != a:
            return math.nan
        return math.copysign(math.inf, a) * math.copysign(1.0, b)


def m_pow(a, b):
    # scalar power, MATLAB semantics (0^-1 = Inf, overflow -> Inf, complex for negative^fraction)
    try:
        return a ** b
    except ZeroDivisionError:
        return math.inf
    except OverflowError:
        with np.errstate(all="ignore"):
            return float(np.power(np.float64(a), np.float64(b)))


def m_round(x):
    # round half away from zero (Python's round() rounds half to even)
    if isinstance(x, np.ndarray):
        a = np.abs(x)
        r = np.floor(a)
        return np.copysign(r + (a - r >= 0.5), x)
    if x != x or x in (math.inf, -math.inf):
        return x
    a = abs(x)
    r = math.floor(a)
    return math.copysign(r + (a - r >= 0.5), x)


def m_mod(a, m):
    # mod(a, m) = a - floor(a/m)*m, mod(a, 0) = a (result has the sign of m)
    if isinstance(a, np.ndarray) or isinstance(m, np.ndarray):
        a, m = np.asarray(a, dtype=float), np.asarray(m, dtype=float)
        with np.errstate(all="ignore"):
            r = np.fmod(a, m)
            r = np.where((r != 0) & ((r < 0) != (m < 0)), r + m, r)
        return np.where(m == 0, a, r)
    if m == 0:
        return a
    r = math.fmod(a, m)
    if r != 0 and (r < 0) != (m < 0):
        r += m
    return r


def m_rem(a, b):
    # rem(a, b) = a - fix(a/b)*b (sign of a), rem(a, 0) = NaN
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        with np.errstate(all="ignore"):
            return np.fmod(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    if b == 0 or a != a or b != b or a in (math.inf, -math.inf):
        return math.nan
    return math.fmod(a, b)


def m_sign(x):
    if isinstance(x, np.ndarray):
        return np.sign(x)
    if x != x:
        return x
    return 1.0 if x > 0 else -1.0 if x < 0 else 0.0


def m_wrap_to_pi(x):
    # wrapToPi: [-pi, pi], positive odd multiples of pi map to +pi
    w = m_mod(x + math.pi, 2 * math.pi) - math.pi
    if isinstance(w, np.ndarray):
        return np.where((w == -math.pi) & (np.asarray(x) > 0), math.pi, w)
    return math.pi if (w == -math.pi and x > 0) else w


def m_columns(x):
    # iteration of a MATLAB for loop: the columns of x (scalars for row vectors)
    a = m_arr(x)
    return [m_norm(a[:, [k]]) for k in range(a.shape[1])] if a.size else []


def m_colon(a, s, b):
    # a:s:b as row vector; elements a + k*s (k = 0..n), last element clipped to b
    if s == 0 or a != a or s != s or b != b or (s > 0 and a > b) or (s < 0 and a < b):
        return np.zeros((1, 0))
    q = (b - a) / s
    n = math.floor(q + 4 * 2.220446049250313e-16 * max(1.0, abs(q)))
    v = a + np.arange(n + 1) * s
    if n >= 0 and ((s > 0 and v[-1] > b) or (s < 0 and v[-1] < b)):
        v[-1] = b
    return v.reshape(1, -1)


def m_truth(v):
    # condition of if/while: all elements nonzero and not empty
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, float, np.floating, np.integer)):
        if v != v:
            raise ValueError("NaN kann nicht in einen Wahrheitswert umgewandelt werden")
        return v != 0
    if isinstance(v, str):
        return len(v) > 0 and all(c != "\0" for c in v)
    a = np.asarray(v)
    return a.size > 0 and bool(np.all(a != 0))


def _m_index_vec(idx, extent):
    # one MATLAB index (1-based, logical mask or ':') -> 0-based integer array
    if idx is COLON:
        return np.arange(extent)
    a = np.asarray(idx)
    if a.dtype == bool:
        flat = a.ravel(order="F")
        if flat.size > extent and np.any(flat[extent:]):
            raise IndexError(f"Index überschreitet die Arraygrenzen (Länge {extent})")
        return np.flatnonzero(flat)
    if isinstance(idx, str):
        raise IndexError("Strings sind als Index nicht erlaubt")
    f = a.astype(float).ravel(order="F")
    if f.size and (np.any(f != np.floor(f)) or np.any(f < 1)):
        bad = f[(f != np.floor(f)) | (f < 1)][0]
        raise IndexError(f"Index muss eine positive ganze Zahl oder logisch sein (Wert {bad:g})")
    return f.astype(np.int64) - 1


def m_get(x, *idx):
    # x(i), x(i, j): 1-based, column-major, result shape following MATLAB's rules
    is_str = isinstance(x, str)
    A = np.array(list(x), dtype="<U1").reshape(1, len(x)) if is_str else m_arr(x)
    if len(idx) > 2 and all(not (i is COLON) and np.all(np.asarray(i) == 1) for i in idx[2:]):
        idx = idx[:2]
    if len(idx) == 1:
        i = idx[0]
        flat = A.ravel(order="F")
        if i is COLON:
            out = flat.reshape(-1, 1)
        else:
            k = _m_index_vec(i, flat.size)
            if k.size and k.max() >= flat.size:
                raise IndexError(f"Index {k.max() + 1} überschreitet die Anzahl der Elemente ({flat.size})")
            out = flat[k]
            ia = np.asarray(i)
            if ia.dtype == bool:
                out = out.reshape(1, -1) if A.shape[0] == 1 else out.reshape(-1, 1)
            else:
                ishape = ia.shape if ia.ndim == 2 else (1, ia.size)
                if A.size != 1 and 1 in A.shape and 1 in ishape:
                    out = out.reshape(1, -1) if A.shape[0] == 1 else out.reshape(-1, 1)
                else:
                    out = out.reshape(ishape, order="F")
    elif len(idx) == 2:
        r = _m_index_vec(idx[0], A.shape[0])
        c = _m_index_vec(idx[1], A.shape[1])
        if (r.size and r.max() >= A.shape[0]) or (c.size and c.max() >= A.shape[1]):
            raise IndexError(f"Index ({(r.max() + 1) if r.size else 0}, {(c.max() + 1) if c.size else 0}) "
                             f"überschreitet die Matrixgröße {A.shape[0]}x{A.shape[1]}")
        out = A[np.ix_(r, c)]
    else:
        raise IndexError("mehr als zwei Indizes werden nicht unterstützt")
    if is_str:
        return "".join(out.ravel(order="F")) if out.shape[0] <= 1 else out
    return m_norm(out)


def m_set(x, idx, value, delete=False):
    # x(idx...) = value with MATLAB growth rules; returns the new array (copy semantics)
    if x is None or (isinstance(x, np.ndarray) and x.size == 0 and not delete):
        A = np.zeros((0, 0)) if x is None else x
    else:
        A = m_arr(x)
    V = m_arr(value) if not isinstance(value, np.ndarray) else value
    if V.dtype == bool and A.dtype != bool and A.size:
        V = V.astype(float)
    dtype = np.result_type(A.dtype, V.dtype) if A.size else V.dtype
    if dtype == bool and A.size and A.dtype != bool:
        dtype = float
    A = A.astype(dtype, copy=True)
    if delete:
        if len(idx) == 1:
            flat = A.ravel(order="F")
            k = _m_index_vec(idx[0], flat.size)
            keep = np.delete(flat, k)
            return m_norm(keep.reshape(-1, 1) if A.shape[1] == 1 and A.shape[0] != 1 else keep.reshape(1, -1))
        r = _m_index_vec(idx[0], A.shape[0])
        c = _m_index_vec(idx[1], A.shape[1])
        if idx[0] is COLON or len(r) == A.shape[0]:
            return m_norm(np.delete(A, c, axis=1))
        if idx[1] is COLON or len(c) == A.shape[1]:
            return m_norm(np.delete(A, r, axis=0))
        raise IndexError("Löschen erfordert ':' in einer Dimension")
    if len(idx) > 2 and all(not (i is COLON) and np.all(np.asarray(i) == 1) for i in idx[2:]):
        idx = idx[:2]
    if len(idx) == 1:
        i = idx[0]
        n = A.size
        k = np.arange(n) if i is COLON else _m_index_vec(i, n if np.asarray(i).dtype != bool else np.asarray(i).size)
        need = int(k.max()) + 1 if k.size else 0
        shape = A.shape
        if need > n:
            if n == 0:
                shape = (1, need) if A.shape[1] != 0 or A.shape[0] == 0 else (need, 1)
                if A.shape == (0, 0) or A.shape[0] <= 1:
                    shape = (1, need)
            elif A.shape[0] == 1:
                shape = (1, need)
            elif A.shape[1] == 1:
                shape = (need, 1)
            else:
                raise IndexError("Matrix kann mit linearem Index nicht vergrößert werden")
        flat = np.zeros(shape[0] * shape[1], dtype=dtype)
        old = A.ravel(order="F")
        if n and shape != A.shape:
            flat[:n] = old
        elif n:
            flat = old.copy()
        if V.size == 1:
            flat[k] = V.flat[0]
        elif V.size == k.size:
            flat[k] = V.ravel(order="F")
        else:
            raise ValueError(f"Zuweisung: {k.size} Elemente links, {V.size} rechts")
        return m_norm(flat.reshape(shape, order="F"))
    if len(idx) == 2:
        r = np.arange(max(A.shape[0], V.shape[0] if A.size == 0 else 0)) if idx[0] is COLON else \
            _m_index_vec(idx[0], A.shape[0])
        c = np.arange(max(A.shape[1], V.shape[1] if A.size == 0 else 0)) if idx[1] is COLON else \
            _m_index_vec(idx[1], A.shape[1])
        rows = max(A.shape[0], int(r.max()) + 1 if r.size else 0)
        cols = max(A.shape[1], int(c.max()) + 1 if c.size else 0)
        if (rows, cols) != A.shape:
            B = np.zeros((rows, cols), dtype=dtype)
            B[:A.shape[0], :A.shape[1]] = A
            A = B
        if V.size == 1:
            A[np.ix_(r, c)] = V.flat[0]
        elif V.size == r.size * c.size:
            A[np.ix_(r, c)] = V.reshape(r.size, c.size) if V.shape == (r.size, c.size) else \
                V.ravel(order="F").reshape((r.size, c.size), order="F")
        else:
            raise ValueError(f"Zuweisung: {r.size}x{c.size} links, {V.shape[0]}x{V.shape[1]} rechts")
        return m_norm(A)
    raise IndexError("mehr als zwei Indizes werden nicht unterstützt")


def m_cat(rows):
    # [a, b; c, d] (rows: list of lists of values); strings concatenate to strings
    out_rows = []
    for row in rows:
        items = [v for v in row if not (isinstance(v, np.ndarray) and v.size == 0)]
        if items and all(isinstance(v, str) for v in items):
            out_rows.append("".join(items))
            continue
        if not items:
            continue
        arrs = [m_arr(v) for v in items]
        h = arrs[0].shape[0]
        if any(a.shape[0] != h for a in arrs):
            raise ValueError("horizontale Verkettung: Zeilenzahlen stimmen nicht überein")
        out_rows.append(np.hstack(arrs))
    if not out_rows:
        return np.zeros((0, 0))
    if all(isinstance(r, str) for r in out_rows):
        if len(out_rows) == 1:
            return out_rows[0]
        if len({len(r) for r in out_rows}) != 1:
            raise ValueError("vertikale Verkettung: Zeichenketten unterschiedlicher Länge")
        return np.array([list(r) for r in out_rows], dtype="<U1")
    arrs = [m_arr(r) for r in out_rows]
    w = arrs[0].shape[1]
    if any(a.shape[1] != w for a in arrs):
        raise ValueError("vertikale Verkettung: Spaltenzahlen stimmen nicht überein")
    return m_norm(np.vstack(arrs))


def m_sprintf(fmt, *args):
    # MATLAB sprintf: C format specifiers, escapes, format recycling over all arguments
    import re
    fmt = (fmt.replace("\\\\", "\0").replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
           .replace("\0", "\\"))
    spec = re.compile(r"%%|%([-+ #0]*)(\d+|\*)?(?:\.(\d+))?([diouxXfFeEgGcs])")
    items = []
    for a in args:
        if isinstance(a, str):
            items.append(a)
        elif isinstance(a, np.ndarray):
            items.extend(a.ravel(order="F").tolist())
        else:
            items.append(a)
    parts = list(spec.finditer(fmt))
    n_specs = sum(1 for p in parts if p.group(0) != "%%")

    def one(m, v):
        flags, width, prec, conv = m.group(1) or "", m.group(2) or "", m.group(3), m.group(4)
        p = f".{prec}" if prec is not None else ""
        if conv in "diouxX":
            if isinstance(v, str):
                return v
            fv = float(v)
            if not math.isfinite(fv) or fv != math.floor(fv):
                return f"%{flags}{width}{p}e" % fv     # MATLAB switches to %e for non-integers
            return f"%{flags}{width}{'d' if conv in 'iu' else conv}" % int(float(v))
        if conv == "c":
            return v if isinstance(v, str) else chr(int(v))
        if conv == "s":
            return f"%{flags}{width}{p}s" % (v if isinstance(v, str) else f"{float(v):g}")
        return f"%{flags}{width}{p}{conv}" % (float(v) if not isinstance(v, str) else float("nan"))

    out, pos = [], 0
    while True:
        last = 0
        for m in parts:
            out.append(fmt[last:m.start()])
            last = m.end()
            if m.group(0) == "%%":
                out.append("%")
                continue
            if items and pos >= len(items):
                return "".join(out)          # stop in front of the first conversion without data
            out.append(one(m, items[pos]) if items else "")
            pos += bool(items)
        out.append(fmt[last:])
        if not items or pos >= len(items) or n_specs == 0:
            return "".join(out)
