"""Pretty printers for AST expressions: MATLAB text and LaTeX (matplotlib mathtext subset).

Identifiers are typeset from their name: Greek names become Greek letters, trailing digits
and ``_parts`` become subscripts, a trailing ``_dot``/``_ddot``/``_hat``/``_bar`` becomes an
accent, e.g. ``kappa_d_dot`` -> ``\\dot{\\kappa}_{d}``, ``y1_d`` -> ``y_{1,d}``,
``e_psi`` -> ``e_{\\psi}``.
"""

from __future__ import annotations

import re

from . import nodes as N

GREEK = {"alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu", "nu",
         "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega", "Gamma", "Delta", "Theta",
         "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega", "varsigma", "varphi", "vartheta",
         "varepsilon", "varrho", "varpi"}
ALIASES = {"gam": "gamma", "lam": "lambda", "ome": "omega", "eps": "epsilon"}
ACCENTS = {"dot": r"\dot", "ddot": r"\ddot", "hat": r"\hat", "bar": r"\bar", "tilde": r"\tilde", "vec": r"\vec"}
FUNCS = {"sin", "cos", "tan", "exp", "log", "sinh", "cosh", "tanh", "arcsin", "arccos", "arctan", "min", "max", "det"}
FUNC_ALIASES = {"asin": "arcsin", "acos": "arccos", "atan": "arctan", "log10": "log_{10}", "log2": "log_{2}"}

# precedence levels (higher binds tighter)
PREC = {"||": 1, "&&": 2, "|": 3, "&": 4, "==": 5, "~=": 5, "<": 5, "<=": 5, ">": 5, ">=": 5, ":": 6,
        "+": 7, "-": 7, "*": 8, "/": 8, "\\": 8, ".*": 8, "./": 8, ".\\": 8, "unary": 9, "^": 10, ".^": 10,
        "postfix": 11, "atom": 12}


def prec_of(e):
    if isinstance(e, N.Binary):
        return PREC[e.op]
    if isinstance(e, N.Range):
        return PREC[":"]
    if isinstance(e, N.Unary):
        return PREC["unary"]
    if isinstance(e, N.Postfix):
        return PREC["postfix"]
    if isinstance(e, N.AnonFunc):
        return 0
    if isinstance(e, N.Number) and (e.value.real < 0 if isinstance(e.value, complex) else e.value < 0):
        return PREC["unary"]
    return PREC["atom"]


# ----------------------------------------------------------------------------- MATLAB text
def to_matlab(e):
    def p(x, level, right=False):
        s = to_matlab(x)
        return f"({s})" if prec_of(x) < level or (right and _neg(x)) else s

    if isinstance(e, N.Number):
        return e.text or _num_text(e.value)
    if isinstance(e, N.String):
        q = '"' if e.double_quoted else "'"
        return q + e.value.replace(q, q + q) + q
    if isinstance(e, N.Ident):
        return e.name
    if isinstance(e, N.Colon):
        return ":"
    if isinstance(e, N.End):
        return "end"
    if isinstance(e, N.Placeholder):
        return "~"
    if isinstance(e, N.Binary):
        lp = PREC[e.op]
        right_level = lp + 1
        sep = "" if e.op in ("^", ".^") else " "
        return f"{p(e.left, lp)}{sep}{e.op}{sep}{p(e.right, right_level, sep == ' ')}"
    if isinstance(e, N.Unary):
        return f"{e.op}{p(e.operand, PREC['unary'])}"
    if isinstance(e, N.Postfix):
        return f"{p(e.operand, PREC['postfix'])}{e.op}"
    if isinstance(e, N.Range):
        parts = [e.start] + ([e.step] if e.step is not None else []) + [e.stop]
        return ":".join(p(x, PREC[":"] + 1) for x in parts)
    if isinstance(e, N.Matrix):
        return "[" + "; ".join(", ".join(to_matlab(x) for x in row) for row in e.rows) + "]"
    if isinstance(e, N.CellArray):
        return "{" + "; ".join(", ".join(to_matlab(x) for x in row) for row in e.rows) + "}"
    if isinstance(e, N.Index):
        return f"{p(e.base, PREC['postfix'])}({', '.join(to_matlab(a) for a in e.args)})"
    if isinstance(e, N.CellIndex):
        return f"{p(e.base, PREC['postfix'])}{{{', '.join(to_matlab(a) for a in e.args)}}}"
    if isinstance(e, N.Field):
        return f"{p(e.base, PREC['postfix'])}.{e.name}"
    if isinstance(e, N.DynField):
        return f"{p(e.base, PREC['postfix'])}.({to_matlab(e.name)})"
    if isinstance(e, N.AnonFunc):
        return f"@({', '.join(e.params)}) {to_matlab(e.body)}"
    if isinstance(e, N.FuncHandle):
        return f"@{e.name}"
    return f"<{type(e).__name__}>"


def _neg(x):
    # unary minus as right operand of * / is parenthesized for readability: a * (-b)
    return isinstance(x, N.Unary) and x.op in "-+" or (isinstance(x, N.Number) and not isinstance(x.value, complex)
                                                     and x.value < 0)


def stmt_to_matlab(s):
    if isinstance(s, N.Assign):
        lhs = to_matlab(s.targets[0]) if not s.multi else "[" + ", ".join(to_matlab(t) for t in s.targets) + "]"
        return f"{lhs} = {to_matlab(s.value)};"
    if isinstance(s, N.ExprStmt):
        return to_matlab(s.expr) + (";" if s.suppress else "")
    return type(s).__name__.lower()


def _num_text(v):
    if isinstance(v, complex):
        return f"{_num_text(v.imag)}i"
    return str(int(v)) if float(v).is_integer() and abs(v) < 1e15 else repr(float(v))


# ----------------------------------------------------------------------------- LaTeX
def latex_name(name):
    """Typeset an identifier (see module docstring)."""
    parts = [p for p in name.split("_") if p]
    if not parts:
        return r"\_"
    accents = []
    while len(parts) > 1 and parts[-1] in ACCENTS:
        accents.append(ACCENTS[parts.pop()])
    base, subs = parts[0], parts[1:]
    m = re.fullmatch(r"([A-Za-z]+?)(\d+)", base)
    if m and m.group(1):
        base, subs = m.group(1), [m.group(2)] + subs
    out = _sym(base)
    for a in accents:
        out = f"{a}{{{out}}}"
    if subs:
        out += "_{" + ",".join(_sym(s) for s in subs) + "}"
    return out


def _sym(s):
    s = ALIASES.get(s, s)
    if s in GREEK:
        return "\\" + s
    if s.isdigit() or len(s) == 1:
        return s
    m = re.fullmatch(r"([A-Za-z]+)(\d+)", s)
    if m and (m.group(1) in GREEK or len(m.group(1)) == 1):
        return _sym(m.group(1)) + m.group(2)
    return r"\mathrm{" + s.replace("_", r"\_") + "}"


def _lnum(v):
    if isinstance(v, complex):
        return f"{_lnum(v.imag)}\\,i"
    if float(v).is_integer() and abs(v) < 1e15:
        return str(int(v))
    text = repr(float(v))
    if "e" in text:
        mant, exp = text.split("e")
        mant = "" if mant in ("1.0", "1") else mant.rstrip("0").rstrip(".") + r" \cdot "
        return f"{mant}10^{{{int(exp)}}}"
    return text


_REL = {"==": "=", "~=": r"\neq", "<": "<", "<=": r"\leq", ">": ">", ">=": r"\geq",
        "&&": r"\wedge", "&": r"\wedge", "||": r"\vee", "|": r"\vee"}


def to_latex(e, functions=()):
    """LaTeX of an expression; ``functions`` = names that are calls (not array indexing)."""
    L = lambda x: to_latex(x, functions)  # noqa: E731

    def par(x, level, right=False):
        s = L(x)
        return rf"\left({s}\right)" if prec_of(x) < level or (right and _neg(x)) else s

    if isinstance(e, N.Number):
        return _lnum(e.value)
    if isinstance(e, N.String):
        return r"\mathrm{``" + e.value.replace("_", r"\_").replace(" ", r"\ ") + "''}"
    if isinstance(e, N.Ident):
        if e.name == "pi":
            return r"\pi"
        if e.name in ("Inf", "inf"):
            return r"\infty"
        return latex_name(e.name)
    if isinstance(e, N.Colon):
        return ":"
    if isinstance(e, N.End):
        return r"\mathrm{end}"
    if isinstance(e, N.Placeholder):
        return r"\sim"
    if isinstance(e, N.Binary):
        lp = PREC[e.op]
        if e.op in ("/", "./"):
            if isinstance(e.left, N.Unary) and e.left.op == "-":
                return rf"-\frac{{{L(e.left.operand)}}}{{{L(e.right)}}}"
            return rf"\frac{{{L(e.left)}}}{{{L(e.right)}}}"
        if e.op in ("^", ".^"):
            base = L(e.left)
            if prec_of(e.left) < PREC["postfix"]:
                base = rf"\left({base}\right)"
            return f"{{{base}}}^{{{L(e.right)}}}"
        if e.op in ("*", ".*"):
            left, right = par(e.left, lp), par(e.right, lp + 1, True)
            sep = r" \cdot " if (right[:1].isdigit() or right.startswith(r"\frac") or left.endswith("}") and
                                 right[:1].isdigit()) or isinstance(e.right, N.Number) else r" \, "
            if e.op == ".*":
                sep = r" \circ "
            return f"{left}{sep}{right}"
        if e.op in ("\\", ".\\"):
            return f"{par(e.left, lp)}^{{-1}} {par(e.right, lp + 1)}"
        if e.op in _REL:
            return f"{par(e.left, lp)} {_REL[e.op]} {par(e.right, lp + 1)}"
        return f"{par(e.left, lp)} {e.op} {par(e.right, lp + 1, True)}"
    if isinstance(e, N.Unary):
        if e.op == "~":
            return rf"\neg {par(e.operand, PREC['unary'])}"
        return f"{e.op}{par(e.operand, PREC['unary'] + 1 if e.op == '-' else PREC['unary'])}"
    if isinstance(e, N.Postfix):
        return f"{{{par(e.operand, PREC['postfix'])}}}^{{T}}"
    if isinstance(e, N.Range):
        parts = [e.start] + ([e.step] if e.step is not None else []) + [e.stop]
        return ":".join(par(x, PREC[":"] + 1) for x in parts)
    if isinstance(e, N.Matrix):
        return r"\left[" + r" ;\ ".join(", ".join(L(x) for x in row) for row in e.rows) + r"\right]"
    if isinstance(e, N.CellArray):
        return r"\left\{" + r" ;\ ".join(", ".join(L(x) for x in row) for row in e.rows) + r"\right\}"
    if isinstance(e, N.Index):
        args = ", ".join(L(a) for a in e.args)
        if isinstance(e.base, N.Ident):
            name = e.base.name
            if name in functions or name not in _VARS_HINT:
                return _func_latex(name, e.args, L)
        return f"{par(e.base, PREC['postfix'])}_{{{args}}}"
    if isinstance(e, N.CellIndex):
        return f"{par(e.base, PREC['postfix'])}_{{\\{{{', '.join(L(a) for a in e.args)}\\}}}}"
    if isinstance(e, N.Field):
        return f"{par(e.base, PREC['postfix'])}.{latex_name(e.name)}"
    if isinstance(e, N.DynField):
        return f"{par(e.base, PREC['postfix'])}.\\left({L(e.name)}\\right)"
    if isinstance(e, N.AnonFunc):
        return rf"\left({', '.join(latex_name(p) for p in e.params)}\right) \mapsto {L(e.body)}"
    if isinstance(e, N.FuncHandle):
        return rf"@\mathrm{{{e.name}}}"
    return r"\mathrm{?}"


class _VarsHint(set):
    pass


_VARS_HINT = _VarsHint()       # filled per call by latex_of_assignment (array variables)


def _has_accent(name):
    parts = name.split("_")
    return len(parts) > 1 and parts[-1] in ACCENTS


def _func_latex(name, args, L):
    a = [L(x) for x in args]
    if name == "sqrt" and len(a) == 1:
        return rf"\sqrt{{{a[0]}}}"
    if name == "abs" and len(a) == 1:
        return rf"\left|{a[0]}\right|"
    if name == "norm" and len(a) >= 1:
        return rf"\left\|{a[0]}\right\|"
    if name == "floor" and len(a) == 1:
        return rf"\lfloor {a[0]} \rfloor"
    if name == "ceil" and len(a) == 1:
        return rf"\lceil {a[0]} \rceil"
    if name == "exp" and len(a) == 1 and len(a[0]) < 25:
        return rf"e^{{{a[0]}}}"
    fname = FUNC_ALIASES.get(name, name)
    if fname in FUNCS or fname.startswith("log_"):
        head = "\\" + fname if fname in FUNCS else r"\log_{" + fname[5:-1] + "}"
    else:
        head = r"\mathrm{" + name.replace("_", r"\_") + "}"
    return rf"{head}\left({', '.join(a)}\right)"


def assignment_latex(stmt, functions=(), arrays=()):
    """LaTeX of an assignment statement (``arrays``: names indexed as arrays, not calls)."""
    _VARS_HINT.clear()
    _VARS_HINT.update(arrays)
    try:
        if stmt.multi or len(stmt.targets) > 1:
            lhs = r"\left[" + ", ".join(to_latex(t, functions) for t in stmt.targets) + r"\right]"
        else:
            lhs = to_latex(stmt.targets[0], functions)
        return f"{lhs} = {to_latex(stmt.value, functions)}"
    finally:
        _VARS_HINT.clear()


def expr_latex(e, functions=(), arrays=()):
    _VARS_HINT.clear()
    _VARS_HINT.update(arrays)
    try:
        return to_latex(e, functions)
    finally:
        _VARS_HINT.clear()
