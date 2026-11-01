"""Error and diagnostic types of the MATLAB toolchain (messages for users are German)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


class MatlabError(Exception):
    """Base class; carries an optional source position."""

    def __init__(self, message, line=0, col=0, path=""):
        self.message, self.line, self.col, self.path = message, line, col, path
        super().__init__(self.__str__())

    def __str__(self):
        where = f"{self.path}:" if self.path else ""
        if self.line:
            where += f"{self.line}:{self.col}: "
        elif where:
            where += " "
        return f"{where}{self.message}"


class MatlabSyntaxError(MatlabError):
    """Lexer / parser error (line and column of the offending token)."""


class MatlabRuntimeError(MatlabError):
    """Error raised while interpreting MATLAB code (also MATLAB's error())."""


class UnsupportedConstruct(MatlabError):
    """A construct the code generator cannot translate."""


@dataclass
class Diagnostic:
    severity: str          # "error" | "warning" | "info"
    message: str           # German, for users
    line: int = 0
    col: int = 0
    target: str = ""       # python / cpp / rust / analysis

    def __str__(self):
        loc = f"Zeile {self.line}" + (f", Spalte {self.col}" if self.col else "") if self.line else "global"
        sev = {"error": "Fehler", "warning": "Warnung", "info": "Hinweis"}.get(self.severity, self.severity)
        return f"[{self.target or '-'}] {sev} ({loc}): {self.message}"

    def to_dict(self):
        return asdict(self)
