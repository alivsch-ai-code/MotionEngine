"""Converter verification: interpreter vs generated Python / Rust / C++."""

import subprocess
from pathlib import Path

import numpy as np
import pytest

from vdsim.matlab import generate
from vdsim.matlab import toolchains as tc
from vdsim.matlab.verify import build_native, rust_main, run_interpreter, run_native, run_python, deviation

ROOT = Path(__file__).resolve().parents[2]
A5 = ROOT / "examples" / "matlab" / "kin_tracking_with_orientation_stab.m"
FIX = ROOT / "tests" / "matlab" / "fixtures"
RNG = np.random.default_rng(42)


def a5_case():
    return [*RNG.uniform(-3, 3, 7), float(RNG.choice([-1.0, 1.0])), *RNG.uniform(-3, 3, 5),
            *RNG.uniform(0.8, 2.0, 2), RNG.uniform(800, 2500), RNG.uniform(1000, 4000), RNG.uniform(0, 0.3),
            *RNG.uniform(0.1, 5, 4)]


CASES = {
    A5: [a5_case() for _ in range(500)],
    FIX / "loops.m": [[float(RNG.integers(1, 9)), RNG.uniform(0.5, 9)] for _ in range(50)],
    FIX / "matrices.m": [[RNG.normal(size=(2, 1)), RNG.uniform(-3, 3)] for _ in range(100)],
    FIX / "switch_case.m": [[float(RNG.integers(0, 6)), RNG.normal()] for _ in range(50)],
    FIX / "subfunctions.m": [list(RNG.normal(size=2)) for _ in range(100)],
    FIX / "multi_return.m": [[RNG.normal(size=(5, 1))] for _ in range(100)],
    FIX / "pure_feedback.m": [list(RNG.normal(size=6)) for _ in range(100)],
    FIX / "pid_controller.m": [[*RNG.normal(size=2), 2.0, 1.0, 0.1, 0.01, -1.0, 1.0] for _ in range(200)],
}
NATIVE_OK = [p for p in CASES]


@pytest.mark.parametrize("path", list(CASES), ids=lambda p: p.stem)
def test_python_bitwise_equal_to_interpreter(path):
    code = generate(path, "python")
    assert code.ok, code.report()
    dev = deviation(run_interpreter(path, CASES[path]), run_python(code, CASES[path]))
    assert dev["bitwise"], dev


def test_python_strings_cells():
    code = generate(FIX / "strings_cells.m", "python")
    assert code.ok
    from vdsim.matlab.verify import load_python
    msg, n, s = load_python(code).strings_cells("abc", 1.5)
    assert msg == "abc: 3.00" and n == 10.0 and s.value == 3.0


@pytest.mark.parametrize("target", ["cpp", "rust"])
def test_unsupported_constructs_reported(target):
    code = generate(FIX / "strings_cells.m", target)
    assert not code.ok and all(d.line > 0 for d in code.errors)
    code = generate(FIX / "nested_functions.m", target)
    assert not code.ok and "verschachtelte" in code.errors[0].message


def test_unsupported_slice_has_line():
    from vdsim.matlab import parse
    code = generate(parse("function y = f(x)\n%#type x: vector\ny = sum(x(2:end));\n"), "rust")
    assert not code.ok and code.errors[0].line == 3


def test_comments_and_equations_transferred():
    for target in ("python", "cpp", "rust"):
        text = "\n".join(generate(A5, target).files.values())
        for ref in ("(4.11)", "(4.12)", "(A.10)", "wheel base", "Back-stepping"):
            assert ref in text, (target, ref)


@pytest.mark.skipif(tc.find_rustc() is None, reason="rustc nicht installiert")
@pytest.mark.parametrize("path", NATIVE_OK, ids=lambda p: p.stem)
def test_rust_typechecks(path, tmp_path):
    code = generate(path, "rust")
    assert code.ok, code.report()
    code.write(tmp_path)
    (tmp_path / "main.rs").write_text(rust_main(code.signature), encoding="utf-8")
    res = subprocess.run([tc.find_rustc().executable, "--edition", "2021", "--emit=metadata", "main.rs", "-o",
                          "main.rmeta"], cwd=tmp_path, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr


def _native(target, tmp_path):
    if target == "rust":
        if tc.find_rustc() is None:
            pytest.skip("rustc nicht installiert")
        ok, msg = tc.probe_rust_link()
    else:
        if tc.find_cpp_compiler() is None:
            pytest.skip("kein C++-Compiler (g++/clang++/MSVC) gefunden")
        ok, msg = tc.probe_cpp()
    if not ok:
        pytest.skip(f"{target}-Toolchain kann keine Programme bauen: {msg[:200]}")


@pytest.mark.parametrize("target", ["rust", "cpp"])
def test_native_numerically_equal(target, tmp_path):
    _native(target, tmp_path)
    worst = 0.0
    for path, cases in CASES.items():
        code = generate(path, target)
        assert code.ok, code.report()
        ref = run_interpreter(path, cases)
        out = run_native(code, cases, tmp_path / path.stem, exe=build_native(code, tmp_path / path.stem))
        dev = deviation(ref, out)
        assert dev["max_rel"] < 1e-12 or dev["max_abs"] < 1e-12, (path.stem, dev)
        worst = max(worst, dev["max_abs"])
    print(f"{target}: max. Abweichung zum Interpreter {worst:.3g}")
