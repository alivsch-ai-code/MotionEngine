from pathlib import Path

import numpy as np
import pytest

from vdsim.matlab import Interpreter, register_builtin
from vdsim.matlab.errors import MatlabRuntimeError

FIX = Path(__file__).resolve().parents[2] / "tests" / "matlab" / "fixtures"


def run(src):
    out = []
    ws = Interpreter.from_source(src, output=out.append).run_script()
    return ws, "".join(out)


def test_indexing_growth_and_end():
    ws, _ = run("v = []; v(3) = 2; A = [1 2; 3 4]; a = A(end, 1); b = A(:)'; c = v(2:end); A(3, 3) = 9;"
                "m = A(logical([1 0 1]), 3); v(2) = [];")
    assert ws["v"].shape == (1, 2) and ws["a"] == 3.0
    np.testing.assert_array_equal(ws["b"], [[1, 3, 2, 4]])
    np.testing.assert_array_equal(ws["c"], [[0, 2]])
    assert ws["A"].shape == (3, 3) and ws["m"].shape == (2, 1)


def test_copy_semantics_and_column_vectors():
    ws, _ = run("a = [1; 2; 3]; b = a; b(1) = 10; n = size(a, 1); s = sum(a); p = a' * a;")
    assert ws["a"][0, 0] == 1 and ws["b"][0, 0] == 10 and (ws["n"], ws["s"], ws["p"]) == (3, 6, 14)


def test_builtins():
    ws, out = run("x = mod(-1, 3); r = rem(-1, 3); q = round(2.5); z = round(-0.5); [m, i] = max([3 7 7]);"
                  "y = interp1([0 1 2], [0 10 20], 1.5); l = linspace(0, 1, 3); c = cumsum([1 2 3]);"
                  "d = diff([1 4 9]); e = isempty([]); fprintf('%d-%s\\n', 5, 'ok'); s = sprintf('%.2f', pi);"
                  "nn = norm([3 4]); a2 = atan2(1, 1); k = numel(zeros(2, 3));")
    assert (ws["x"], ws["r"], ws["q"], ws["z"]) == (2.0, -1.0, 3.0, -1.0)
    assert (ws["m"], ws["i"], ws["y"], ws["e"], ws["nn"], ws["k"]) == (7.0, 2.0, 15.0, True, 5.0, 6.0)
    assert out == "5-ok\n" and ws["s"] == "3.14"
    np.testing.assert_array_equal(ws["d"], [[3, 5]])


def test_fixtures():
    s, p, n_iter, v = Interpreter.from_file(FIX / "loops.m").call(None, 5.0, 2.0)
    assert (s, p) == (55.0, 15.0) and n_iter > 0 and v.shape == (1, 5)
    assert [Interpreter.from_file(FIX / "switch_case.m").call(None, m, 3.0)[0] for m in (1, 2, 3, 4, 9)] == \
        [3.0, -3.0, -3.0, 9.0, 0.0]
    assert Interpreter.from_file(FIX / "subfunctions.m").call(None, 0.2, 0.3) == pytest.approx((0.8, 1.1))
    res = Interpreter.from_file(FIX / "multi_return.m").call(None, np.array([3.0, 1, 4, 1, 5]))
    assert res == (1.0, 5.0, 5.0, 2.8, 1.0)
    assert Interpreter.from_file(FIX / "nested_functions.m").call(None, 3.0) == (9.0,)
    msg, n, s = Interpreter.from_file(FIX / "strings_cells.m").call(None, "abc", 1.5)
    assert msg == "abc: 3.00" and n == 10.0 and s["value"] == 3.0


def test_pid_persistent_and_reset():
    it = Interpreter.from_file(FIX / "pid_controller.m")
    args = (2.0, 1.0, 0.1, 0.01, -1.0, 1.0)
    assert it.call(None, 1.0, 0.2, *args) == (1.0, 0.0)
    u, integ = it.call(None, 1.0, 0.3, *args)
    assert u == pytest.approx(0.4) and integ == pytest.approx(0.007)
    it.reset()
    assert it.call(None, 1.0, 0.2, *args) == (1.0, 0.0)


def test_script_and_registry():
    register_builtin("twice", lambda x: 2 * x)
    assert run("y = twice(21);")[0]["y"] == 42
    assert Interpreter.from_file(FIX / "script_example.m", output=lambda s: None).run_script()["total"] == 20.0


def test_runtime_error_position():
    with pytest.raises(MatlabRuntimeError) as e:
        run("a = [1 2 3];\nb = a(5);")
    assert e.value.line == 2
    with pytest.raises(MatlabRuntimeError, match="Fehler 3"):
        run("error('Fehler %d', 3);")
