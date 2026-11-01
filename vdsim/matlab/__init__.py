"""MATLAB integration: import, interpret, analyze and convert MATLAB code.

    parse / parse_file           lexer + recursive-descent parser -> AST (vdsim.matlab.nodes)
    Interpreter                  executes the AST (numpy semantics, 1-based, built-in registry)
    analyze                      signatures, data flow, call graph, equations, control structure, JSON/DOT
    generate / convert_file      code generators Python (numpy), C++17, Rust with diagnostics
    load_matlab_component        MATLAB function -> Component ("matlab:datei.m[:funktion]" loader)
    toolchains / verify          compiler detection and back-to-back verification

CLI: ``python -m vdsim.matlab convert|analyze|run|toolchains``.
"""

from __future__ import annotations

from ..framework.plugins import register_loader
from .analysis import FileAnalysis, analyze
from .builtins import register_builtin
from .codegen import GeneratedCode, generate
from .component import MatlabComponent, load_matlab_component, matlab_loader
from .convert import convert_file
from .errors import Diagnostic, MatlabError, MatlabRuntimeError, MatlabSyntaxError
from .interpreter import Interpreter, run_function
from .latex import latex_name, to_latex, to_matlab
from .parser import parse, parse_file

register_loader("matlab", matlab_loader)

__all__ = ["parse", "parse_file", "Interpreter", "run_function", "register_builtin", "analyze", "FileAnalysis",
           "generate", "GeneratedCode", "convert_file", "load_matlab_component", "MatlabComponent", "Diagnostic",
           "MatlabError", "MatlabSyntaxError", "MatlabRuntimeError", "to_latex", "to_matlab", "latex_name"]
