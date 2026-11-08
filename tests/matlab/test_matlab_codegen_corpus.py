"""Differential test of the MATLAB -> Python converter over a corpus of numeric builtins."""

import ast
from pathlib import Path

import numpy as np
import pytest

from vdsim.matlab import generate
from vdsim.matlab.verify import deviation, load_python, run_interpreter, run_python

FIX = Path(__file__).resolve().parent / "fixtures"


def test_builtin_corpus_matches_interpreter():
    path = FIX / "builtins_corpus.m"
    code = generate(path, "python")
    assert code.ok, code.report()
    rng = np.random.default_rng(11)
    cases = [[float(rng.uniform(-3, 3)), float(rng.uniform(-3, 3))] for _ in range(100)]
    dev = deviation(run_interpreter(path, cases), run_python(code, cases))
    # reductions (std, var, norm) may sum in a different order than the interpreter: not bitwise
    assert dev["max_rel"] < 1e-12, dev


def _chained_comparisons(source):
    return [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Compare) and len(node.ops) > 1]


def test_any_all_logical_are_not_chained_comparisons():
    # MATLAB any(v > c) was emitted as np.any(v > c != 0), i.e. (v > c) and (c != 0) in Python:
    # an exception for longer arrays and a silently wrong result for one-element arrays
    path = FIX / "any_all_compare.m"
    code = generate(path, "python")
    assert code.ok, code.report()
    assert _chained_comparisons(next(iter(code.files.values()))) == []
    fn = load_python(code).any_all_compare
    p, q, r = fn(np.array([[2.0, 3.0, -1.0]]), 0.0)
    assert bool(p) is True and bool(q) is False and float(r) == 2.0
    rng = np.random.default_rng(2)
    cases = [[rng.normal(size=(1, 3)), c] for c in (-0.5, 0.0, 1.0) for _ in range(5)]
    dev = deviation(run_interpreter(path, cases), run_python(code, cases))
    assert dev["bitwise"], dev


@pytest.mark.parametrize("target", ["python"])
def test_corpus_generation_report_is_clean(target):
    code = generate(FIX / "builtins_corpus.m", target)
    assert code.ok and "Fehler" not in code.report()
