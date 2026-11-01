"""Recursive-descent parser: MATLAB tokens -> AST (``nodes``).

Operator precedence (lowest to highest), as in the MATLAB language reference:

    ||   &&   |   &   < <= > >= == ~=   :   + -   * / \\ .* ./ .\\   unary + - ~   ^ .^ ' .'

Function files may terminate functions with ``end`` (then nested functions are possible)
or not; which style a file uses is decided by counting block openers and ``end``
keywords outside of indices, like MATLAB does.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..framework.knowledge import trace
from . import nodes as N
from .errors import MatlabSyntaxError
from .lexer import BLOCK_OPENERS, tokenize

EQUATION_ONLY = re.compile(r"^\s*\(\s*(?:[A-Z]\.?)?\d+(\.\d+)*[a-z]?\s*\)\s*$")
_CMP = {"==", "~=", "<", "<=", ">", ">="}
_MUL = {"*", "/", "\\", ".*", "./", ".\\"}


class Parser:
    def __init__(self, tokens, comments, path="", source=""):
        self.toks, self.comments, self.path, self.source = tokens, comments, path, source
        self.i = 0
        self._doc_lines = set()
        self.functions_end = self._detect_end_style()

    # ------------------------------------------------------------------ token helpers
    @property
    def tok(self):
        return self.toks[self.i]

    def look(self, k=1):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def advance(self):
        t = self.toks[self.i]
        if t.kind != "EOF":
            self.i += 1
        self.last = t
        return t

    def is_op(self, *ops, tok=None):
        t = tok or self.tok
        return t.kind == "OP" and t.value in ops

    def is_kw(self, *kws, tok=None):
        t = tok or self.tok
        return t.kind == "KW" and t.value in kws and not t.index_end

    def error(self, msg, tok=None):
        t = tok or self.tok
        raise MatlabSyntaxError(msg, t.line, t.col, self.path)

    def expect_op(self, op):
        if not self.is_op(op):
            self.error(f"'{op}' erwartet, gefunden {self._describe(self.tok)}")
        return self.advance()

    def expect_kw(self, kw, opened=None):
        if not self.is_kw(kw):
            where = f" (zu '{opened.value}' in Zeile {opened.line})" if opened else ""
            self.error(f"'{kw}' erwartet{where}, gefunden {self._describe(self.tok)}")
        return self.advance()

    def expect_ident(self):
        if self.tok.kind != "IDENT":
            self.error(f"Bezeichner erwartet, gefunden {self._describe(self.tok)}")
        return self.advance()

    @staticmethod
    def _describe(t):
        if t.kind == "EOF":
            return "Dateiende"
        if t.kind == "NEWLINE":
            return "Zeilenende"
        return f"'{t.value}'"

    def skip_separators(self):
        while self.tok.kind in ("NEWLINE", "SEMI", "COMMA"):
            self.advance()

    def _detect_end_style(self):
        openers = ends = funcs = 0
        for t in self.toks:
            if t.kind == "KW" and not t.index_end:
                if t.value in BLOCK_OPENERS:
                    openers += 1
                    funcs += t.value == "function"
                elif t.value == "end":
                    ends += 1
        if funcs == 0:
            return False
        if ends > openers:
            extra = [t for t in self.toks if t.kind == "KW" and t.value == "end" and not t.index_end][-1]
            raise MatlabSyntaxError("überzähliges 'end'", extra.line, extra.col, self.path)
        return ends == openers

    # ------------------------------------------------------------------ program
    def parse(self):
        self.skip_separators()
        functions, script = [], []
        kind = "function" if self.is_kw("function") else "script"
        if kind == "script":
            script = self.parse_block({"function"}, top=True)
        while self.is_kw("function"):
            functions.append(self.parse_function())
            self.skip_separators()
        if self.tok.kind != "EOF":
            self.error(f"unerwartetes {self._describe(self.tok)} außerhalb einer Funktion")
        mfile = N.MFile(kind, functions, script, self.comments, path=self.path, source=self.source, line=1, col=1)
        self._attach_comments(mfile)
        return mfile

    def parse_function(self, parent=None):
        start = self.expect_kw("function")
        outputs = []
        # output list: [a, b] = name  |  a = name  |  name
        if self.is_op("["):
            self.advance()
            while not self.is_op("]"):
                if self.tok.kind == "COMMA":
                    self.advance()
                    continue
                outputs.append(self.expect_ident().value)
            self.advance()
            self.expect_op("=")
            name = self._func_name()
        else:
            first = self._func_name()
            if self.is_op("="):
                self.advance()
                outputs, name = [first], self._func_name()
            else:
                name = first
        params = []
        if self.is_op("("):
            self.advance()
            while not self.is_op(")"):
                if self.tok.kind == "COMMA":
                    self.advance()
                elif self.is_op("~"):
                    self.advance()
                    params.append("~")
                else:
                    params.append(self.expect_ident().value)
            self.advance()
        header_end = self.last.line
        if self.tok.kind not in ("NEWLINE", "SEMI", "COMMA", "EOF"):
            self.error(f"Zeilenende nach dem Funktionskopf erwartet, gefunden {self._describe(self.tok)}")
        func = N.Function(name, params, outputs, [], line=start.line, col=start.col, parent=parent)
        func._header_end = header_end
        terminators = {"end"} if self.functions_end else {"function"}
        func.body = self.parse_block(terminators, func=func)
        if self.functions_end:
            self.expect_kw("end", start)
        func.end_line = self.last.line
        func.doc = self._function_doc(func, first=parent is None)
        return func

    def _func_name(self):
        name = self.expect_ident().value
        while self.is_op("."):          # set.Prop / get.Prop (class methods)
            self.advance()
            name += "." + self.expect_ident().value
        return name

    # ------------------------------------------------------------------ statements
    def parse_block(self, terminators, func=None, top=False):
        body = []
        while True:
            self.skip_separators()
            t = self.tok
            if t.kind == "EOF":
                return body
            if t.kind == "KW" and not t.index_end and t.value in terminators:
                return body
            if self.is_kw("function"):
                if func is not None and self.functions_end:
                    func.nested.append(self.parse_function(parent=func.name))
                    continue
                if top:
                    return body
                self.error("'function' an dieser Stelle nicht erlaubt (fehlt ein 'end'?)")
            if t.kind == "KW" and not t.index_end and t.value in ("end", "else", "elseif", "case", "otherwise",
                                                                    "catch"):
                self.error(f"unerwartetes '{t.value}'")
            body.append(self.parse_statement())

    def _finish(self, stmt, start):
        stmt.line, stmt.col = start.line, start.col
        stmt.end_line = self.last.line
        return stmt

    def _terminator(self):
        # statement end: ';' suppresses the output
        t = self.tok
        if t.kind == "SEMI":
            self.advance()
            return True
        if t.kind in ("COMMA", "NEWLINE"):
            self.advance()
            return False
        if t.kind == "EOF" or (t.kind == "KW" and not t.index_end):
            return False
        self.error(f"Anweisungsende erwartet, gefunden {self._describe(t)}")

    def parse_statement(self):
        t = self.tok
        if t.kind == "CMD":
            self.advance()
            stmt = self._finish(N.Command(t.value[0], list(t.value[1])), t)
            self._terminator()
            return stmt
        if t.kind == "KW":
            handler = {"if": self.parse_if, "for": self.parse_for, "parfor": self.parse_for,
                       "while": self.parse_while, "switch": self.parse_switch, "try": self.parse_try}.get(t.value)
            if handler:
                return handler()
            if t.value in ("break", "continue", "return"):
                self.advance()
                stmt = self._finish({"break": N.Break, "continue": N.Continue, "return": N.Return}[t.value](), t)
                self._terminator()
                return stmt
            if t.value in ("global", "persistent"):
                self.advance()
                names = []
                while self.tok.kind == "IDENT" and self.tok.line == t.line:
                    names.append(self.advance().value)
                if not names:
                    self.error(f"Variablenname nach '{t.value}' erwartet")
                stmt = self._finish((N.Global if t.value == "global" else N.Persistent)(names), t)
                self._terminator()
                return stmt
        expr = self.parse_expr()
        if self.is_op("="):
            eq = self.advance()
            if isinstance(expr, N.Matrix):
                if len(expr.rows) != 1:
                    self.error("ungültige Mehrfachzuweisung", eq)
                targets, multi = expr.rows[0], True
            else:
                targets, multi = [expr], False
            for tg in targets:
                self._check_lvalue(tg, eq)
            value = self.parse_expr()
            stmt = N.Assign(targets, value, multi=multi)
        else:
            stmt = N.ExprStmt(expr)
        self._finish(stmt, t)
        stmt.suppress = self._terminator()
        return stmt

    def _check_lvalue(self, e, tok):
        base = e
        while isinstance(base, (N.Index, N.CellIndex, N.Field, N.DynField)):
            base = base.base
        if not isinstance(base, (N.Ident, N.Placeholder)):
            raise MatlabSyntaxError("ungültiges Zuweisungsziel", e.line or tok.line, e.col or tok.col, self.path)

    def _block_until(self, kws, opened):
        body = self.parse_block(set(kws))
        if self.tok.kind == "EOF":
            self.error(f"'end' zu '{opened.value}' fehlt (Dateiende erreicht)", opened)
        return body

    def parse_if(self):
        start = self.advance()
        clauses, else_body = [], None
        cond = self.parse_expr()
        clauses.append((cond, self._block_until(("elseif", "else", "end"), start)))
        while self.is_kw("elseif"):
            self.advance()
            cond = self.parse_expr()
            clauses.append((cond, self._block_until(("elseif", "else", "end"), start)))
        if self.is_kw("else"):
            self.advance()
            else_body = self._block_until(("end",), start)
        self.expect_kw("end", start)
        stmt = self._finish(N.If(clauses, else_body), start)
        self._terminator()
        return stmt

    def parse_for(self):
        start = self.advance()
        paren = self.is_op("(")
        if paren:
            self.advance()
        var = self.expect_ident().value
        self.expect_op("=")
        iterable = self.parse_expr()
        if paren:
            self.expect_op(")")
        body = self._block_until(("end",), start)
        self.expect_kw("end", start)
        stmt = self._finish(N.For(var, iterable, body), start)
        self._terminator()
        return stmt

    def parse_while(self):
        start = self.advance()
        cond = self.parse_expr()
        body = self._block_until(("end",), start)
        self.expect_kw("end", start)
        stmt = self._finish(N.While(cond, body), start)
        self._terminator()
        return stmt

    def parse_switch(self):
        start = self.advance()
        subject = self.parse_expr()
        self.skip_separators()
        cases, otherwise = [], None
        while self.is_kw("case"):
            self.advance()
            value = self.parse_expr()
            cases.append((value, self._block_until(("case", "otherwise", "end"), start)))
        if self.is_kw("otherwise"):
            self.advance()
            otherwise = self._block_until(("end",), start)
        self.expect_kw("end", start)
        stmt = self._finish(N.Switch(subject, cases, otherwise), start)
        self._terminator()
        return stmt

    def parse_try(self):
        start = self.advance()
        body = self._block_until(("catch", "end"), start)
        ident, catch_body = None, []
        if self.is_kw("catch"):
            c = self.advance()
            if self.tok.kind == "IDENT" and self.tok.line == c.line:
                ident = self.advance().value
            catch_body = self._block_until(("end",), start)
        self.expect_kw("end", start)
        stmt = self._finish(N.TryCatch(body, ident, catch_body), start)
        self._terminator()
        return stmt

    # ------------------------------------------------------------------ expressions
    def _bin(self, sub, ops):
        left = sub()
        while self.tok.kind == "OP" and self.tok.value in ops:
            op = self.advance()
            right = sub()
            left = N.Binary(op.value, left, right, line=op.line, col=op.col)
        return left

    def parse_expr(self):
        return self._bin(self._andand, {"||"})

    def _andand(self):
        return self._bin(self._or, {"&&"})

    def _or(self):
        return self._bin(self._and, {"|"})

    def _and(self):
        return self._bin(self._cmp, {"&"})

    def _cmp(self):
        return self._bin(self._range, _CMP)

    def _range(self):
        start_tok = self.tok
        first = self._add()
        if not self.is_op(":"):
            return first
        self.advance()
        second = self._add()
        if self.is_op(":"):
            self.advance()
            third = self._add()
            return N.Range(first, second, third, line=start_tok.line, col=start_tok.col)
        return N.Range(first, None, second, line=start_tok.line, col=start_tok.col)

    def _add(self):
        return self._bin(self._mul, {"+", "-"})

    def _mul(self):
        return self._bin(self._unary, _MUL)

    def _unary(self):
        t = self.tok
        if self.is_op("-", "+", "~"):
            if t.value == "~" and self.look().kind == "COMMA" or (t.value == "~" and self.is_op("]", tok=self.look())):
                self.advance()
                return N.Placeholder(line=t.line, col=t.col)
            self.advance()
            return N.Unary(t.value, self._unary(), line=t.line, col=t.col)
        return self._power()

    def _power(self):
        left = self._postfix()
        while self.is_op("^", ".^"):
            op = self.advance()
            right = self._power_operand()
            left = N.Binary(op.value, left, right, line=op.line, col=op.col)
        return left

    def _power_operand(self):
        t = self.tok
        if self.is_op("-", "+", "~"):
            self.advance()
            return N.Unary(t.value, self._power_operand(), line=t.line, col=t.col)
        return self._postfix()

    def _postfix(self):
        e = self._primary()
        while True:
            t = self.tok
            if self.is_op("("):
                self.advance()
                e = N.Index(e, self._args(")"), line=e.line, col=e.col)
            elif self.is_op("{") and not t.ws_before:
                self.advance()
                e = N.CellIndex(e, self._args("}"), line=e.line, col=e.col)
            elif self.is_op(".") and self.look().kind in ("IDENT", "KW"):
                self.advance()
                e = N.Field(e, self.advance().value, line=e.line, col=e.col)
            elif self.is_op(".") and self.is_op("(", tok=self.look()):
                self.advance()
                self.advance()
                name = self.parse_expr()
                self.expect_op(")")
                e = N.DynField(e, name, line=e.line, col=e.col)
            elif self.is_op("'", ".'"):
                self.advance()
                e = N.Postfix(t.value, e, line=e.line, col=e.col)
            else:
                return e

    def _args(self, close):
        args = []
        while True:
            if self.is_op(close):
                self.advance()
                return args
            t = self.tok
            if self.is_op(":") and (self.look().kind == "COMMA" or self.is_op(close, tok=self.look())):
                self.advance()
                args.append(N.Colon(line=t.line, col=t.col))
            else:
                args.append(self.parse_expr())
            if self.tok.kind == "COMMA":
                self.advance()
            elif not self.is_op(close):
                self.error(f"',' oder '{close}' erwartet, gefunden {self._describe(self.tok)}")

    def _primary(self):
        t = self.tok
        if t.kind == "NUM":
            self.advance()
            return N.Number(t.value, t.text, line=t.line, col=t.col)
        if t.kind == "STR":
            self.advance()
            return N.String(t.value, t.text == '"', line=t.line, col=t.col)
        if t.kind == "IDENT":
            self.advance()
            return N.Ident(t.value, line=t.line, col=t.col)
        if t.kind == "KW" and t.value == "end" and t.index_end:
            self.advance()
            return N.End(line=t.line, col=t.col)
        if self.is_op("("):
            self.advance()
            e = self.parse_expr()
            self.expect_op(")")
            e._paren = True
            return e
        if self.is_op("[", "{"):
            self.advance()
            rows = self._rows("]" if t.value == "[" else "}")
            cls = N.Matrix if t.value == "[" else N.CellArray
            return cls(rows, line=t.line, col=t.col)
        if self.is_op("@"):
            self.advance()
            if self.is_op("("):
                self.advance()
                params = []
                while not self.is_op(")"):
                    if self.tok.kind == "COMMA":
                        self.advance()
                    elif self.is_op("~"):
                        self.advance()
                        params.append("~")
                    else:
                        params.append(self.expect_ident().value)
                self.advance()
                return N.AnonFunc(params, self.parse_expr(), line=t.line, col=t.col)
            name = self.expect_ident().value
            while self.is_op(".") and self.look().kind == "IDENT":
                self.advance()
                name += "." + self.advance().value
            return N.FuncHandle(name, line=t.line, col=t.col)
        if t.kind == "KW":
            self.error(f"Schlüsselwort '{t.value}' an dieser Stelle nicht erlaubt")
        self.error(f"Ausdruck erwartet, gefunden {self._describe(t)}")

    def _rows(self, close):
        rows, row = [], []
        while True:
            t = self.tok
            if self.is_op(close):
                self.advance()
                if row:
                    rows.append(row)
                return rows
            if t.kind == "SEMI":
                self.advance()
                if row:
                    rows.append(row)
                row = []
                continue
            if t.kind == "COMMA":
                self.advance()
                continue
            if t.kind in ("EOF", "NEWLINE"):
                self.error(f"'{close}' erwartet, gefunden {self._describe(t)}")
            row.append(self.parse_expr())
            if not (self.tok.kind in ("COMMA", "SEMI") or self.is_op(close)):
                self.error(f"',' oder '{close}' erwartet, gefunden {self._describe(self.tok)}")

    # ------------------------------------------------------------------ comments
    def _function_doc(self, func, first):
        after = self._comment_block_after(func._header_end)
        before = self._comment_block_before(func.line) if first else []
        lines = before + ([""] if before and after else []) + after
        return "\n".join(l for l in lines if not l.lstrip().startswith("#")).strip("\n")   # without %#type pragmas

    def _comment_block_after(self, line):
        by_line = {c.line: c for c in self.comments if not c.trailing}
        out, ln = [], line + 1
        while ln in by_line:
            c = by_line[ln]
            self._doc_lines.add(c.line)
            out.extend(_clean(c.text).split("\n"))
            ln = (c.end_line or c.line) + 1
        return out

    def _comment_block_before(self, line):
        by_end = {(c.end_line or c.line): c for c in self.comments if not c.trailing}
        out, ln = [], line - 1
        while ln in by_end:
            c = by_end[ln]
            self._doc_lines.add(c.line)
            out = _clean(c.text).split("\n") + out
            ln = c.line - 1
        return out

    def _attach_comments(self, mfile):
        stmts = list(N.body_statements(mfile.script))
        for f in mfile.all_functions():
            stmts.extend(N.body_statements(f.body))
        stmts.sort(key=lambda s: (s.line, s.col))
        code_lines = sorted({t.line for t in self.toks if t.kind not in ("NEWLINE", "EOF", "SEMI", "COMMA")})
        simple = {}
        for s in stmts:
            compound = isinstance(s, (N.If, N.For, N.While, N.Switch, N.TryCatch))
            last = s.line if compound else s.end_line
            s.comment = " ".join(c.text.strip() for c in self.comments
                                 if c.trailing and s.line <= c.line <= last and _owner(stmts, c, s))
            if not compound:
                simple.setdefault(s.end_line, s)
        # standalone comments: leading comments of the next statement; a line holding only an
        # equation number belongs to the statement above (A.5: '% (4.12)' below w2 = ...)
        import bisect
        stmt_by_line = {}
        for s in stmts:
            stmt_by_line.setdefault(s.line, s)
        for c in self.comments:
            if c.trailing or c.line in self._doc_lines:
                continue
            k = bisect.bisect_right(code_lines, c.line)
            prev_line = code_lines[k - 1] if k else 0
            next_line = code_lines[k] if k < len(code_lines) else None
            if EQUATION_ONLY.match(c.text) and prev_line in simple:
                s = simple[prev_line]
                s.comment = (s.comment + " " + c.text.strip()).strip()
            elif next_line in stmt_by_line:
                stmt_by_line[next_line].leading.append(_clean(c.text))


def _owner(stmts, comment, stmt):
    # the trailing comment belongs to the innermost statement covering its line
    for s in stmts:
        if s is stmt:
            continue
        compound = isinstance(s, (N.If, N.For, N.While, N.Switch, N.TryCatch))
        last = s.line if compound else s.end_line
        if s.line <= comment.line <= last and (s.line > stmt.line or (s.line == stmt.line and s.col > stmt.col)):
            return False
    return True


def _clean(text):
    # strip one leading blank of each comment line
    return "\n".join(line[1:] if line.startswith(" ") else line for line in text.split("\n"))


@trace("aho2006", section="4.4", concept="matlab_parser", note="recursive descent, operator precedence levels")
def parse(source, path=""):
    """Parse MATLAB source text into an ``MFile`` AST (raises MatlabSyntaxError)."""
    tokens, comments = tokenize(source, path)
    return Parser(tokens, comments, path, source).parse()


def parse_file(path):
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    return parse(text, str(path))
