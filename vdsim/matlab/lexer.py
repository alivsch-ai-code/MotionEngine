"""Lexer for the MATLAB subset used in controller and simulation code.

Handles the context-sensitive parts of the MATLAB grammar:
  * ``'`` is the transpose operator after a value (identifier, number, ``)``, ``]``, ``}``,
    ``'``) and a string delimiter otherwise; inside ``[]``/``{}`` a preceding blank makes
    it a string (``[a 'x']``),
  * inside ``[]``/``{}`` blanks separate elements: a comma token is inserted between two
    values (``[1 -2]`` = two elements, ``[1 - 2]`` = one), newlines separate rows,
  * ``end`` inside ``()``/``{}`` is the index keyword (``x(end)``),
  * comments ``%``, block comments ``%{ ... %}`` (own lines, nestable), continuation ``...``,
  * command syntax for a few display commands (``clc``, ``clear all``, ``format long``).

Comments are not tokens; they are collected in ``Lexer.comments`` with their position so
that the parser can attach them to statements (documentation, equation references).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import MatlabSyntaxError

KEYWORDS = {"break", "case", "catch", "continue", "else", "elseif", "end", "for", "function", "global", "if",
            "otherwise", "parfor", "persistent", "return", "switch", "try", "while"}
BLOCK_OPENERS = {"if", "for", "parfor", "while", "switch", "try", "function"}
COMMAND_WORDS = {"clc", "clear", "close", "format", "hold", "more", "clf", "figure", "drawnow", "warning", "pkg"}
OPERATORS = [".*", "./", ".\\", ".^", ".'", "==", "~=", "!=", "<=", ">=", "&&", "||",
             "+", "-", "*", "/", "\\", "^", "<", ">", "&", "|", "~", "!", "=", "(", ")", "[", "]", "{", "}",
             ":", ".", "@", "'"]
_NUMBER = re.compile(r"(\d+(\.(?![*/\\^'])\d*)?|\.\d+)([eEdD][+-]?\d+)?")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_VALUE_END_OPS = {")", "]", "}", "'", ".'"}


@dataclass
class Token:
    kind: str           # NUM IDENT STR KW OP NEWLINE SEMI COMMA CMD EOF
    value: object
    line: int
    col: int
    ws_before: bool = False
    index_end: bool = False   # 'end' keyword inside () or {} (index context)
    text: str = ""            # source text (numbers)

    def ends_value(self):
        if self.kind in ("NUM", "IDENT", "STR"):
            return True
        if self.kind == "KW" and self.value == "end" and self.index_end:
            return True
        return self.kind == "OP" and self.value in _VALUE_END_OPS

    def __repr__(self):
        return f"{self.kind}({self.value!r})@{self.line}:{self.col}"


@dataclass
class Comment:
    line: int
    col: int
    text: str            # without the leading '%' (block comments: joined lines)
    trailing: bool       # code precedes the comment on the same line
    block: bool = False
    end_line: int = 0


class Lexer:
    def __init__(self, source, path=""):
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.path = path
        self.tokens: list[Token] = []
        self.comments: list[Comment] = []
        self.pos, self.line, self.line_start = 0, 1, 0
        self.stack = []                 # open brackets: ( [ {
        self.stack_pos = []
        self.ws = False
        self.code_on_line = False

    # ------------------------------------------------------------------ helpers
    def error(self, msg, line=None, col=None):
        raise MatlabSyntaxError(msg, line or self.line, col or self.col(), self.path)

    def col(self, pos=None):
        return (self.pos if pos is None else pos) - self.line_start + 1

    def peek(self, k=0):
        i = self.pos + k
        return self.src[i] if i < len(self.src) else ""

    def in_matrix(self):
        return bool(self.stack) and self.stack[-1] in "[{"

    def prev(self):
        return self.tokens[-1] if self.tokens else None

    def emit(self, kind, value, line, col, text=""):
        tok = Token(kind, value, line, col, self.ws, text=text)
        if kind == "KW" and value == "end" and any(b in "({" for b in self.stack):
            tok.kind, tok.index_end = "KW", True
        # implicit element separator inside [] / {}
        if self.in_matrix() and self.ws and self.prev() is not None and self.prev().ends_value() \
                and self._starts_value(tok):
            self.tokens.append(Token("COMMA", ",", line, col, True))
        self.tokens.append(tok)
        self.ws = False
        self.code_on_line = True
        return tok

    def _starts_value(self, tok):
        if tok.kind in ("NUM", "IDENT", "STR"):
            return True
        if tok.kind == "KW" and tok.value == "end" and tok.index_end:
            return True
        if tok.kind != "OP":
            return False
        if tok.value in ("(", "[", "{", "@"):
            return True
        if tok.value in ("~", "!"):
            return self.peek() != "="
        if tok.value in ("+", "-"):
            return self.peek() not in (" ", "\t")      # unary sign: '[a -b]'
        return False

    def newline(self):
        self.line += 1
        self.line_start = self.pos
        self.code_on_line = False

    def at_statement_start(self):
        p = self.prev()
        return not self.stack and (p is None or p.kind in ("NEWLINE", "SEMI", "COMMA"))

    # ------------------------------------------------------------------ main loop
    def tokenize(self):
        src = self.src
        while self.pos < len(src):
            c = src[self.pos]
            if c in " \t":
                self.pos += 1
                self.ws = True
                continue
            if c == "\n":
                self._newline_token()
                continue
            if c == "%" or (c == "#" and False):
                self._comment()
                continue
            if src.startswith("...", self.pos):
                start, line = self.pos, self.line
                end = src.find("\n", self.pos)
                end = len(src) if end < 0 else end
                text = src[self.pos + 3:end].strip()
                if text:
                    self.comments.append(Comment(line, self.col(start) + 3, text.lstrip("%").strip(), True))
                self.pos = end + 1 if end < len(src) else end
                if end < len(src):
                    self.newline()
                    self.code_on_line = True
                self.ws = True
                continue
            line, col = self.line, self.col()
            if c.isdigit() or (c == "." and self.peek(1).isdigit()):
                self._number(line, col)
                continue
            if c.isalpha() or c == "_":
                m = _IDENT.match(src, self.pos)
                word = m.group(0)
                if word in COMMAND_WORDS and self.at_statement_start() and self._command(word, m.end(), line, col):
                    continue
                self.pos = m.end()
                self.emit("KW" if word in KEYWORDS else "IDENT", word, line, col)
                continue
            if c == '"':
                self._string('"', line, col)
                continue
            if c == "'":
                p = self.prev()
                transpose = p is not None and p.ends_value() and not (self.in_matrix() and self.ws)
                if not transpose:
                    self._string("'", line, col)
                    continue
            if c == ";" or c == ",":
                self.pos += 1
                if self.in_matrix() or (self.stack and c == ","):
                    self.emit("SEMI" if c == ";" else "COMMA", c, line, col)
                else:
                    self.emit("SEMI" if c == ";" else "COMMA", c, line, col)
                continue
            for op in OPERATORS:
                if src.startswith(op, self.pos):
                    if op == ".'" and not (self.prev() and self.prev().ends_value()):
                        continue
                    self.pos += len(op)
                    op = {"!=": "~=", "!": "~"}.get(op, op)
                    if op in "([{":
                        self.emit("OP", op, line, col)
                        self.stack.append(op)
                        self.stack_pos.append((line, col))
                    elif op in ")]}":
                        if not self.stack or {")": "(", "]": "[", "}": "{"}[op] != self.stack[-1]:
                            self.error(f"unerwartetes '{op}'", line, col)
                        self.stack.pop()
                        self.stack_pos.pop()
                        self.ws = False
                        self.emit("OP", op, line, col)
                    else:
                        self.emit("OP", op, line, col)
                    break
            else:
                self.error(f"unerwartetes Zeichen '{c}'", line, col)
        if self.stack:
            self.error(f"nicht geschlossene Klammer '{self.stack[-1]}'", *self.stack_pos[-1])
        self.emit("NEWLINE", "\n", self.line, self.col())
        self.ws = False
        self.tokens.append(Token("EOF", None, self.line, self.col()))
        return self.tokens

    # ------------------------------------------------------------------ pieces
    def _newline_token(self):
        line, col = self.line, self.col()
        self.pos += 1
        if self.in_matrix():
            p = self.prev()
            if p is not None and p.kind not in ("SEMI",) and not (p.kind == "OP" and p.value in "[{"):
                self.tokens.append(Token("SEMI", ";", line, col))     # newline = row separator
        elif not self.stack:
            p = self.prev()
            if p is not None and p.kind != "NEWLINE":
                self.tokens.append(Token("NEWLINE", "\n", line, col))
        self.ws = False
        self.newline()

    def _comment(self):
        src, start, line = self.src, self.pos, self.line
        end = src.find("\n", self.pos)
        end = len(src) if end < 0 else end
        text = src[self.pos + 1:end]
        before = src[self.line_start:start]
        if text.strip() == "{" and not before.strip():
            self._block_comment(end)
            return
        self.comments.append(Comment(line, self.col(start), text, bool(before.strip()), end_line=line))
        self.pos = end

    def _block_comment(self, end):
        src, line = self.src, self.line
        depth, lines = 1, []
        pos = end + 1 if end < len(src) else end
        self.pos = pos
        if end < len(src):
            self.newline()
        while self.pos < len(src):
            e = src.find("\n", self.pos)
            e = len(src) if e < 0 else e
            text = src[self.pos:e]
            stripped = text.strip()
            self.pos = e + 1 if e < len(src) else e
            if stripped == "%{":
                depth += 1
            elif stripped == "%}":
                depth -= 1
                if depth == 0:
                    self.comments.append(Comment(line, 1, "\n".join(lines), False, True, self.line))
                    if e < len(src):
                        self.newline()
                    return
            lines.append(text)
            if e < len(src):
                self.newline()
        self.error("Blockkommentar '%{' ohne schließendes '%}'", line, 1)

    def _number(self, line, col):
        m = _NUMBER.match(self.src, self.pos)
        text = m.group(0)
        self.pos = m.end()
        value = float(text.replace("d", "e").replace("D", "e"))
        if self.peek() in ("i", "j") and not (self.peek(1).isalnum() or self.peek(1) == "_"):
            self.pos += 1
            text += "i"
            value = complex(0.0, value)
        elif self.peek().isalpha() or self.peek() == "_":
            self.error(f"ungültige Zahl '{text}{self.peek()}'", line, col)
        self.emit("NUM", value, line, col, text=text)

    def _string(self, quote, line, col):
        src, i, out = self.src, self.pos + 1, []
        while True:
            if i >= len(src) or src[i] == "\n":
                self.error("String nicht abgeschlossen", line, col)
            if src[i] == quote:
                if i + 1 < len(src) and src[i + 1] == quote:
                    out.append(quote)
                    i += 2
                    continue
                break
            out.append(src[i])
            i += 1
        self.pos = i + 1
        tok = self.emit("STR", "".join(out), line, col)
        tok.text = quote

    def _command(self, word, end, line, col):
        # command syntax: 'clear all', 'format long', 'hold on'
        src = self.src
        rest_end = end
        while rest_end < len(src) and src[rest_end] not in "\n;,%":
            rest_end += 1
        rest = src[end:rest_end]
        if not rest.strip():
            return False
        if rest[0] not in " \t" or rest.lstrip()[0] in "=(":
            return False
        args = rest.split()
        if any(not re.fullmatch(r"[-\w.]+", a) for a in args):
            return False
        self.pos = rest_end
        self.emit("CMD", (word, args), line, col)
        return True


def tokenize(source, path=""):
    lx = Lexer(source, path)
    return lx.tokenize(), lx.comments
