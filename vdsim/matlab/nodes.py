"""AST node classes of the MATLAB subset.

Every node carries ``line``/``col`` (1-based) of its first token. Statements additionally
carry ``end_line``, the trailing comment of their last line and leading comment lines,
which the analysis (equation references) and the code generators (comment transfer) use.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields


@dataclass
class Node:
    line: int = field(default=0, kw_only=True)
    col: int = field(default=0, kw_only=True)

    def children(self):
        for f in fields(self):
            if f.name in ("line", "col", "end_line", "comment", "leading"):
                continue
            v = getattr(self, f.name)
            yield from _iter_nodes(v)

    def walk(self):
        # pre-order traversal of this node and all descendants
        yield self
        for c in self.children():
            yield from c.walk()


def _iter_nodes(v):
    if isinstance(v, Node):
        yield v
    elif isinstance(v, (list, tuple)):
        for x in v:
            yield from _iter_nodes(x)


# ----------------------------------------------------------------------------- expressions
class Expr(Node):
    pass


@dataclass
class Number(Expr):
    value: float | complex
    text: str = ""


@dataclass
class String(Expr):
    value: str
    double_quoted: bool = False


@dataclass
class Ident(Expr):
    name: str


@dataclass
class Colon(Expr):
    """Magic colon ':' in an index (all elements)."""


@dataclass
class End(Expr):
    """'end' inside an index: last index of the indexed dimension."""


@dataclass
class Placeholder(Expr):
    """'~' output placeholder in [~, i] = max(x)."""


@dataclass
class Binary(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Unary(Expr):
    op: str          # '-', '+', '~'
    operand: Expr


@dataclass
class Postfix(Expr):
    op: str          # "'" (ctranspose) or ".'" (transpose)
    operand: Expr


@dataclass
class Range(Expr):
    start: Expr
    step: Expr | None
    stop: Expr


@dataclass
class Matrix(Expr):
    rows: list       # list[list[Expr]]


@dataclass
class CellArray(Expr):
    rows: list


@dataclass
class Index(Expr):
    """x(args): array indexing or function call (resolved at run time / by analysis)."""
    base: Expr
    args: list


@dataclass
class CellIndex(Expr):
    base: Expr
    args: list


@dataclass
class Field(Expr):
    base: Expr
    name: str


@dataclass
class DynField(Expr):
    base: Expr
    name: Expr


@dataclass
class AnonFunc(Expr):
    params: list     # list[str]
    body: Expr


@dataclass
class FuncHandle(Expr):
    name: str


# ----------------------------------------------------------------------------- statements
@dataclass
class Stmt(Node):
    end_line: int = field(default=0, kw_only=True)
    comment: str = field(default="", kw_only=True)            # trailing comment of the statement
    leading: list = field(default_factory=list, kw_only=True)  # comment lines directly above


@dataclass
class ExprStmt(Stmt):
    expr: Expr
    suppress: bool = True        # terminated by ';'


@dataclass
class Assign(Stmt):
    targets: list                # list[Expr] (Ident, Index, CellIndex, Field, Placeholder)
    value: Expr
    suppress: bool = True
    multi: bool = False          # [a, b] = ...


@dataclass
class If(Stmt):
    clauses: list                # list[(cond, body)]
    else_body: list | None = None


@dataclass
class For(Stmt):
    var: str
    iterable: Expr
    body: list


@dataclass
class While(Stmt):
    cond: Expr
    body: list


@dataclass
class Switch(Stmt):
    subject: Expr
    cases: list                  # list[(value_expr, body)]
    otherwise: list | None = None


@dataclass
class TryCatch(Stmt):
    body: list
    ident: str | None
    catch_body: list


@dataclass
class Break(Stmt):
    pass


@dataclass
class Continue(Stmt):
    pass


@dataclass
class Return(Stmt):
    pass


@dataclass
class Global(Stmt):
    names: list


@dataclass
class Persistent(Stmt):
    names: list


@dataclass
class Command(Stmt):
    name: str
    args: list


# ----------------------------------------------------------------------------- program units
@dataclass
class Function(Node):
    name: str
    params: list                 # input names ('varargin' allowed, '~' for ignored)
    outputs: list                # output names
    body: list
    nested: list = field(default_factory=list)      # nested functions (end-terminated files)
    doc: str = ""                                   # help text (header comments)
    end_line: int = 0
    parent: str | None = None                       # enclosing function of a nested function


@dataclass
class MFile(Node):
    kind: str                    # "function" | "script"
    functions: list              # top-level functions (main first) and local functions
    script: list                 # script statements (kind == "script")
    comments: list               # lexer comments
    path: str = ""
    source: str = ""
    doc: str = ""

    @property
    def main(self):
        return self.functions[0] if self.functions else None

    def all_functions(self):
        out = []

        def visit(f):
            out.append(f)
            for n in f.nested:
                visit(n)
        for f in self.functions:
            visit(f)
        return out

    def function(self, name=None):
        if name is None:
            return self.main
        for f in self.all_functions():
            if f.name == name:
                return f
        raise KeyError(f"Funktion '{name}' nicht in {self.path or 'Datei'} gefunden, "
                       f"vorhanden: {[f.name for f in self.all_functions()]}")


def body_statements(body):
    # all statements in a body, recursively (including nested blocks)
    for s in body:
        yield s
        if isinstance(s, If):
            for _, b in s.clauses:
                yield from body_statements(b)
            if s.else_body:
                yield from body_statements(s.else_body)
        elif isinstance(s, (For, While)):
            yield from body_statements(s.body)
        elif isinstance(s, Switch):
            for _, b in s.cases:
                yield from body_statements(b)
            if s.otherwise:
                yield from body_statements(s.otherwise)
        elif isinstance(s, TryCatch):
            yield from body_statements(s.body)
            yield from body_statements(s.catch_body)
