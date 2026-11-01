"""File conversion MATLAB -> Python / C++ / Rust (used by the CLI)."""

from __future__ import annotations

from pathlib import Path

from .codegen import TARGETS, generate
from .parser import parse_file


def convert_file(path, target="all", out_dir=".", function=None, input_types=None, force=False):
    """Convert ``path`` and write the sources to ``out_dir`` (one sub folder per target for 'all').

    Returns {target: GeneratedCode}. Files are only written when there are no errors in the
    diagnostics (``force=True`` writes anyway, unsupported places are marked in the code).
    """
    mfile = parse_file(path)
    targets = TARGETS if target == "all" else (target,)
    out = {}
    for t in targets:
        code = generate(mfile, t, function=function, input_types=input_types)
        if code.ok or force:
            code.write(Path(out_dir) / t if target == "all" else Path(out_dir))
        out[t] = code
    return out
