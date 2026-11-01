"""Code generators MATLAB -> Python / C++17 / Rust.

    from vdsim.matlab.codegen import generate
    result = generate("controller.m", "rust")      # GeneratedCode(files, diagnostics, signature)
    if result.ok:
        result.write("out/")
"""

from __future__ import annotations

from ...framework.knowledge import trace
from .base import GeneratedCode, Unsupported

TARGETS = ("python", "cpp", "rust")


@trace("aho2006", section="8", concept="matlab_codegen", note="syntax-directed translation with type inference")
def generate(mfile, target, function=None, input_types=None, **options):
    """Translate ``function`` (default: main function) of an MFile/path into ``target``."""
    if target == "python":
        from .python import PythonGenerator as G
    elif target in ("cpp", "c++"):
        from .cpp import CppGenerator as G
    elif target == "rust":
        from .rust import RustGenerator as G
    else:
        raise ValueError(f"unbekanntes Ziel '{target}', erlaubt: {', '.join(TARGETS)}")
    return G(mfile, function, input_types, **options).generate()


__all__ = ["generate", "GeneratedCode", "Unsupported", "TARGETS"]
