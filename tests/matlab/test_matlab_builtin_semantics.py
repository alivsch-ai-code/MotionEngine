"""MATLAB semantics of the interpreter builtins against values documented by MathWorks."""

import math

import numpy as np
import pytest

from vdsim.matlab import Interpreter
from vdsim.matlab.errors import MatlabError


def run(src):
    out = []
    ws = Interpreter.from_source(src, output=out.append).run_script()
    return ws, "".join(str(o) for o in out)


def val(src, name="r"):
    ws, _ = run(src)
    v = ws[name]
    return v.item() if isinstance(v, np.ndarray) and v.size == 1 else v


@pytest.mark.parametrize("expr, expected", [
    ("mod(-7, 3)", 2.0), ("rem(-7, 3)", -1.0), ("mod(5, 0)", 5.0), ("round(-2.5)", -3.0), ("round(2.5)", 3.0),
    ("fix(-2.7)", -2.0), ("floor(-2.5)", -3.0), ("ceil(-2.5)", -2.0), ("sign(-0.3)", -1.0),
    ("std([1 2 3 4])", math.sqrt(5 / 3)), ("var([1 2 3 4])", 5 / 3), ("median([3 1 2])", 2.0),
    ("median([1 2 3 4])", 2.5), ("sum(mean([1 2; 3 4]))", 5.0),
    ("prod([1 2 3 4])", 24.0), ("sum(cumsum([1 2 3]))", 10.0), ("sum(cumprod([1 2 3]))", 9.0),
    ("sum(diff([1 4 9]))", 8.0), ("nnz([1 0 2 0])", 2.0), ("numel(find([0 1 1 0]))", 2.0),
    ("hypot(3, 4)", 5.0), ("atan2(1, 1)", math.pi / 4), ("deg2rad(180)", math.pi), ("rad2deg(pi)", 180.0),
    ("wrapToPi(3 * pi / 2)", -math.pi / 2), ("wrapTo2Pi(-pi / 2)", 3 * math.pi / 2),
    ("abs(3 + 4i)", 5.0), ("angle(1i)", math.pi / 2), ("real(2 + 3i)", 2.0), ("imag(conj(2 + 3i))", -3.0),
    ("det([1 2; 3 4])", -2.0), ("trace([1 2; 3 4])", 5.0), ("norm([3 4])", 5.0), ("dot([1 2 3], [4 5 6])", 32.0),
    ("sum(cross([1 0 0], [0 1 0]) .* [0 0 1])", 1.0), ("sum(sum(inv([2 0; 0 4])))", 0.75),
    ("sum(sum(pinv([1 0; 0 2])))", 1.5), ("sum(sum(kron([1 2], [1; 1])))", 6.0), ("sum(diag([1 2; 3 4]))", 5.0),
    ("polyval([1 0 -1], 3)", 8.0), ("interp1([0 1 2], [0 10 20], 1.5)", 15.0), ("trapz([0 1 2], [0 1 4])", 3.0),
    ("numel(linspace(0, 1, 11))", 11.0), ("sum(sum(repmat([1 2], 2, 2)))", 12.0),
    ("max([3 7 2])", 7.0), ("min([3 7 2])", 2.0), ("sum(sort([3 1 2], 'descend') .* [1 0 0])", 3.0),
    ("sum(fliplr([1 2 3]) .* [1 0 0])", 3.0), ("sum(flipud([1; 2]) .* [1; 0])", 2.0),
    ("ndims(ones(2, 3))", 2.0), ("length(zeros(3, 7))", 7.0), ("isempty([])", True), ("isrow([1 2 3])", True),
    ("iscolumn([1; 2])", True), ("isvector([1 2])", True), ("isscalar(5)", True), ("ismatrix(ones(2))", True),
    ("xor(true, false)", True), ("any([0 0 1])", True), ("all([1 1 0])", False), ("isnan(NaN)", True),
    ("isinf(-Inf)", True), ("isfinite(1)", True), ("isreal(2)", True),
    ("isequal([1 2], [1 2])", True), ("islogical(true)", True), ("isnumeric(1)", True), ("ischar('a')", True),
    ("isa(1, 'double')", True), ("eps > 0 && eps < 1e-15", True), ("realmax > 1e300", True), ("pi", math.pi),
    ("str2double('2.5')", 2.5), ("str2num('[1 2 3]') * [1; 1; 1]", 6.0), ("strcmp('ab', 'ab')", True),
    ("strcmpi('AB', 'ab')", True), ("numel(strtrim('  x  '))", 1.0), ("numel(blanks(3))", 3.0),
])
def test_scalar_semantics(expr, expected):
    got = val(f"r = {expr};")
    if isinstance(expected, bool):
        assert bool(got) is expected
    else:
        assert float(np.real(got)) == pytest.approx(expected, rel=1e-12, abs=1e-12)


def test_column_major_reshape_and_indexing():
    ws, _ = run("A = reshape(1:6, 2, 3); b = A(2, :); c = A(:)'; A(:, 2) = []; e = A(end, end); "
                "v = [5 6 7 8]; v(v > 6) = 0; v(2) = []; [m, i] = max([3 7 2]); [s, k] = sort([3 1 2]);")
    assert np.array_equal(np.ravel(ws["b"]), [2, 4, 6]) and np.array_equal(np.ravel(ws["c"]), [1, 2, 3, 4, 5, 6])
    assert np.shape(ws["A"]) == (2, 2) and float(ws["e"]) == 6.0
    assert np.array_equal(np.ravel(ws["v"]), [5, 0, 0]) and float(ws["m"]) == 7 and float(ws["i"]) == 2
    assert np.array_equal(np.ravel(ws["s"]), [1, 2, 3]) and np.array_equal(np.ravel(ws["k"]), [2, 3, 1])


def test_strings_cells_structs_and_functions():
    ws, out = run("""
s = sprintf('%d-%0.2f', 3, 2.5);
u = upper('ab'); l = lower('CD'); t = strcat('a', 'b', 'c'); r = strrep('hello', 'l', 'L');
n = num2str(42); i2 = int2str(2.7); ms = mat2str([1 2; 3 4]);
c = {1, 'a', [1 2 3]}; nc = numel(c); ic = iscell(c);
lens = cellfun(@numel, {[1 2], 1, []});
sq = arrayfun(@(x) x ^ 2, [1 2 3]);
st.a = 1; st.b = 'x'; f = fieldnames(st); hf = isfield(st, 'a'); st2 = rmfield(st, 'b'); is = isstruct(st);
g = str2func('@(x) x + 1'); gv = g(1); fs = func2str(g); fv = feval(@hypot, 3, 4);
cls = class('abc'); z = complex(1, 2); lg = logical([2 0]); dbl = double('A');
fprintf('%s|', 'out'); disp(7);
""")
    assert ws["s"] == "3-2.50" and ws["u"] == "AB" and ws["l"] == "cd" and ws["t"] == "abc" and ws["r"] == "heLLo"
    assert ws["n"] == "42" and ws["i2"] == "3" and ws["ms"] == "[1 2;3 4]"
    assert float(ws["nc"]) == 3 and bool(ws["ic"])
    assert np.array_equal(np.ravel(ws["lens"]), [2, 1, 0]) and np.array_equal(np.ravel(ws["sq"]), [1, 4, 9])
    assert list(np.ravel(ws["f"].data)) == ["a", "b"] and bool(ws["hf"]) and bool(ws["is"]) and "b" not in ws["st2"]
    assert float(ws["gv"]) == 2 and "x" in ws["fs"] and float(ws["fv"]) == 5
    assert ws["cls"] == "char" and complex(ws["z"]) == complex(1, 2) and float(ws["dbl"]) == 65.0
    assert np.array_equal(np.ravel(ws["lg"]), [True, False])
    assert "out|" in out and "7" in out


def test_control_flow_errors_and_random():
    ws, _ = run("""
acc = 0; for k = 1:5, if mod(k, 2) == 0, continue; end, acc = acc + k; end
w = 0; while true, w = w + 1; if w >= 3, break; end, end
switch 'b', case {'a', 'b'}, sw = 1; otherwise, sw = 2; end
try, error('my:id', 'boom %d', 3); catch err, msg = err.message; end
rng_a = rand(2, 2); rng_b = randn(1, 3);
x = 1:3; x(5) = 9;
""")
    assert float(ws["acc"]) == 9 and float(ws["w"]) == 3 and float(ws["sw"]) == 1
    assert "boom 3" in ws["msg"]
    assert np.shape(ws["rng_a"]) == (2, 2) and np.all((ws["rng_a"] >= 0) & (ws["rng_a"] < 1))
    assert np.array_equal(np.ravel(ws["x"]), [1, 2, 3, 0, 9])
    with pytest.raises(MatlabError):
        run("y = undefined_function_xyz(1);")
    with pytest.raises(MatlabError):
        run("a = [1 2 3]; b = a(5);")


def test_str2num_and_str2func_follow_matlab():
    # str2num accepts matrix literals (MATLAB evaluates the text; vdsim parses literals only, no eval)
    ws, _ = run("a = str2num('[1 2; 3 4]'); b = str2num('7'); c = str2num('disp(1)'); "
                "f = str2func('@(x, y) x * y + 1'); v = f(2, 3); h = str2func('hypot'); w = h(3, 4);")
    assert np.array_equal(ws["a"], [[1, 2], [3, 4]]) and float(ws["b"]) == 7.0 and np.size(ws["c"]) == 0
    assert float(ws["v"]) == 7.0 and float(ws["w"]) == 5.0


@pytest.mark.parametrize("expr, expected", [
    ("2 + 3", 5.0), ("2 - 3", -1.0), ("2 * 3", 6.0), ("6 / 4", 1.5), ("4 \\ 6", 1.5), ("2 ^ 10", 1024.0),
    ("2 .^ 3", 8.0), ("3 == 3", True), ("3 ~= 3", False), ("2 < 3", True), ("2 <= 2", True), ("2 > 3", False),
    ("3 >= 3", True), ("1 & 0", False), ("1 | 0", True), ("-(2)", -2.0), ("~0", True), ("+4", 4.0),
    ("1 / 0", math.inf), ("(1 + 2i) > 0.5", True),
    ("sum(sum([1 2; 3 4] * [1; 1]))", 10.0), ("sum([2 4] / [1 2])", 2.0), ("sum([1 2; 3 4] \\ [5; 6])", 0.5),
    ("sum(sum([1 1; 0 1] ^ 3))", 5.0), ("sum([1 2 3] .* 2)", 12.0),
    ("sum([1 2 3] - 1)", 3.0), ("sum([4 6] ./ [2 3])", 4.0), ("sum([2 3] .\\ [4 9])", 5.0),
    ("sum([1 2 3] == [1 0 3])", 2.0), ("sum([1 2 3] ~= 2)", 2.0), ("sum([1 2 3] < 2)", 1.0),
    ("sum([1 2 3] <= 2)", 2.0), ("sum([1 2 3] > 2)", 1.0), ("sum([1 2 3] >= 2)", 2.0),
    ("sum([1 0 1] & [1 1 0])", 1.0), ("sum([1 0 0] | [0 0 1])", 2.0), ("sum(-[1 2])", -3.0),
    ("sum(~[1 0 2])", 1.0), ("sum(-[true false])", -1.0), ("sum('ab' == 'ab')", 2.0), ("sum('a' + 1)", 98.0),
    ("real(sum([-8 8] .^ (1/3)))", 3.0),
    ("sum(sum([1 2; 3 4] / [1 0; 0 2]))", 7.0),
])
def test_operator_semantics(expr, expected):
    got = val(f"r = {expr};")
    if isinstance(expected, bool):
        assert bool(got) is expected
    else:
        assert float(np.real(got)) == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("src", [
    "r = [1 2 3] * [4 5 6];", "r = [1 2; 3 4] ^ 0.5;", "r = [1 2 3] + [1 2];", "r = 'ab' == 'abc';",
    "c = {1}; r = c + 1;", "s.a = 1; r = s * 2;", "c = {1, 2}; r = c{5};", "x = 3; r = x.a;",
])
def test_operator_errors(src):
    with pytest.raises(MatlabError):
        run(src)


def test_cells_and_functions_semantics():
    ws, _ = run("""
c = {1, 'two'; [3 4], {5}};
a = c{1, 2}; b = c(2, :); n = numel(c); s = size(c);
d = {}; d{3} = 'x'; e = {1; 2}; e{4} = 7; f = [c(1, :), {9}];
g = c(:)'; h = c([1 2]);
[p, q] = deal(1, 2);
""")
    assert ws["a"] == "two" and float(ws["n"]) == 4 and np.array_equal(np.ravel(ws["s"]), [2, 2])
    assert ws["b"].data.shape == (1, 2) and ws["d"].data.shape == (1, 3) and ws["e"].data.shape == (4, 1)
    assert ws["f"].data.shape == (1, 3) and ws["g"].data.shape == (1, 4) and ws["h"].data.shape == (2, 1)
    assert float(ws["p"]) == 1 and float(ws["q"]) == 2


def test_functions_nargin_nested_and_persistent():
    src = """
function [s, n] = main_fn(a, b)
if nargin < 2
    b = 10;
end
s = helper(a) + b;
n = counter() + counter();
end

function y = helper(x)
y = 2 * x;
end

function k = counter()
persistent cnt
if isempty(cnt)
    cnt = 0;
end
cnt = cnt + 1;
k = cnt;
end
"""
    interp = Interpreter.from_source(src)
    s, n = interp.call(None, 3.0, nargout=2)
    assert float(s) == 16.0 and float(n) == 3.0
    s2 = interp.call(None, 1.0, 1.0, nargout=1)
    assert float(np.ravel(s2)[0] if isinstance(s2, (list, tuple, np.ndarray)) else s2) == 3.0
