from pathlib import Path

import pytest

from vdsim.matlab import nodes as N
from vdsim.matlab.errors import MatlabSyntaxError
from vdsim.matlab.lexer import tokenize
from vdsim.matlab.parser import parse, parse_file

ROOT = Path(__file__).resolve().parents[2]
A5 = ROOT / "examples" / "matlab" / "kin_tracking_with_orientation_stab.m"
FIX = ROOT / "tests" / "matlab" / "fixtures"


def kinds(src):
    return [(t.kind, t.value) for t in tokenize(src)[0] if t.kind not in ("NEWLINE", "EOF")]


def test_transpose_vs_string_and_matrix_whitespace():
    assert ("OP", "'") in kinds("y = x';")
    assert ("STR", "ab") in kinds("y = 'ab';")
    assert kinds("a = [1 -2 x' 'str'];").count(("COMMA", ",")) == 3
    assert kinds("a = [1 - 2];").count(("COMMA", ",")) == 0
    assert ("NUM", 1e-3) in kinds("x = 1e-3;")
    assert ("OP", "./") in kinds("y = 1./x;")


def test_comments_block_and_continuation():
    src = "%{\nblock\n%}\nx = 1 + ...  continued\n    2; % (4.11)\n% (4.12)\n"
    s = parse(src).script[0]
    assert isinstance(s, N.Assign) and s.end_line == 5
    assert "(4.11)" in s.comment and "(4.12)" in s.comment


def test_precedence_and_ranges():
    e = parse("y = -2^2 + a:b:c;").script[0].value
    assert isinstance(e, N.Range) and e.step is not None
    assert isinstance(e.start, N.Binary) and isinstance(e.start.left, N.Unary)


def test_statements_and_multi_assign():
    src = (
        "function [a, b] = f(x, varargin)\nglobal G\npersistent P\n[a, ~] = max(x);\n"
        "switch x\n  case {1, 2}\n    b = 1;\n  otherwise\n    b = 2;\nend\n"
        "for k = 1:3, a = a + k; end\n"
        "while a > 0 && b < 3\n  a = a - 1; if a < 2, break; elseif a == 5, continue; else, return; end\nend\n"
        "c = {1, 'x'}; s.f = @(t) t.^2; z = x(end, :); w = [1, 2; 3 4];\n")
    f = parse(src).main
    assert f.outputs == ["a", "b"] and f.params == ["x", "varargin"]
    assert [type(s).__name__ for s in f.body][:5] == ["Global", "Persistent", "Assign", "Switch", "For"]
    assert f.body[2].multi and isinstance(f.body[2].targets[1], N.Placeholder)


def test_end_terminated_and_nested_functions():
    m = parse_file(FIX / "nested_functions.m")
    assert m.main.nested and m.main.nested[0].name == "add"
    m2 = parse_file(FIX / "subfunctions.m")
    assert [f.name for f in m2.functions] == ["subfunctions", "add_scaled", "sat", "helper2"]


def test_script_with_local_function():
    m = parse_file(FIX / "script_example.m")
    assert m.kind == "script" and m.functions[0].name == "scale"


def test_a5_structure():
    m = parse_file(A5)
    f = m.main
    assert f.name == "kin_tracking_with_orientation_stab" and len(f.params) == 22
    assert f.outputs == ["delta_dot", "F_l"]
    assert [x.name for x in m.functions] == ["kin_tracking_with_orientation_stab", "normalize_angle"]
    assert "Appendix A.5" in f.doc and "control design parameters" in f.doc


@pytest.mark.parametrize("src,line,col", [("x = (1 + 2;\n", 1, 5), ("y = 3 $ 4;", 1, 7),
                                          ("if x\n y = 1;\n", 1, 1), ("x = 'abc\n", 1, 5)])
def test_errors_with_position(src, line, col):
    with pytest.raises(MatlabSyntaxError) as e:
        parse(src)
    assert (e.value.line, e.value.col) == (line, col)
