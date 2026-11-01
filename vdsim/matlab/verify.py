"""Back-to-back verification of the converters against the interpreter.

    report = verify_file("controller.m", cases, targets=("python", "rust", "cpp"), workdir=tmp)
    report["rust"]["max_abs"]  -> largest deviation from the interpreter

For the native targets a small ``main`` is generated that reads the test inputs from a
text file (``n`` cases; scalars as values, arrays as ``rows cols`` followed by the values in
column-major order), calls the generated function (one state object across all cases, so
persistent variables behave as in a simulation loop) and prints all outputs with full
precision. Missing toolchains raise ``ToolchainError``.
"""

from __future__ import annotations

import subprocess
import types
from pathlib import Path

import numpy as np

from ..framework.knowledge import trace
from .codegen import generate
from .interpreter import Interpreter, to_value
from .parser import parse_file
from .toolchains import ToolchainError, compile_cpp, compile_rust, find_cpp_compiler, find_rustc


def _is_array(type_text):
    return type_text.startswith("array")


def flatten(value):
    """Output value -> list of floats (column-major)."""
    if isinstance(value, (bool, np.bool_)):
        return [float(value)]
    return [float(x) for x in np.asarray(value, dtype=float).ravel(order="F")]


def write_inputs(path, cases, signature):
    lines = [str(len(cases))]
    for args in cases:
        parts = []
        for (name, ttext), a in zip(signature["inputs"], args):
            if _is_array(ttext):
                arr = np.asarray(to_value(a), dtype=float)
                arr = arr.reshape(1, 1) if arr.ndim == 0 else arr
                parts += [str(arr.shape[0]), str(arr.shape[1])] + [repr(float(x)) for x in arr.ravel(order="F")]
            else:
                parts.append(repr(float(a)))
        lines.append(" ".join(parts))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_outputs(text):
    return [[float(x) for x in line.split()] for line in text.strip().splitlines() if line.strip()]


# ----------------------------------------------------------------------------- harness sources
def rust_main(sig):
    m, fn = sig["module"], sig["function"]
    lines = [f"mod {m};", "", "fn main() {",
             "    let path = std::env::args().nth(1).expect(\"input file\");",
             "    let text = std::fs::read_to_string(path).expect(\"read input\");",
             "    let mut it = text.split_whitespace().map(|s| s.parse::<f64>().expect(\"number\"));",
             "    let n = it.next().unwrap() as usize;"]
    if sig.get("state"):
        lines.append(f"    let mut state = {m}::{sig['state']}::default();")
    lines.append("    for _ in 0..n {")
    args = ["&mut state"] if sig.get("state") else []
    for k, (name, t) in enumerate(sig["inputs"]):
        if _is_array(t):
            lines += [f"        let r{k} = it.next().unwrap() as usize;", f"        let c{k} = it.next().unwrap() as usize;",
                      f"        let a{k} = {m}::mlab::Mat {{ rows: r{k}, cols: c{k}, "
                      f"data: (0..r{k} * c{k}).map(|_| it.next().unwrap()).collect() }};"]
            args.append(f"&a{k}")
        else:
            lines.append(f"        let a{k} = it.next().unwrap();")
            args.append(f"a{k}")
    lines.append(f"        let out = {m}::{fn}({', '.join(args)});")
    outs = sig["outputs"]
    for k, (name, t) in enumerate(outs):
        ref = "out" if len(outs) == 1 else f"out.{k}"
        if _is_array(t):
            lines.append(f"        for x in {ref}.data.iter() {{ print!(\"{{:e}} \", x); }}")
        elif t == "bool":
            lines.append(f"        print!(\"{{}} \", if {ref} {{ 1 }} else {{ 0 }});")
        else:
            lines.append(f"        print!(\"{{:e}} \", {ref});")
    lines += ["        println!();", "    }", "}", ""]
    return "\n".join(lines)


def cpp_main(sig):
    m, fn, ns = sig["module"], sig["function"], sig["namespace"]
    lines = [f'#include "{m}.hpp"', "", "#include <cstdio>", "#include <fstream>", "", "int main(int argc, char** argv) {",
             "    if (argc < 2) return 2;", "    std::ifstream in(argv[1]);", "    double nn = 0.0;", "    in >> nn;"]
    if sig.get("state"):
        lines.append(f"    {ns}::{sig['state']} state;")
    lines.append("    for (long k = 0; k < static_cast<long>(nn); ++k) {")
    args = ["state"] if sig.get("state") else []
    for k, (name, t) in enumerate(sig["inputs"]):
        if _is_array(t):
            lines += [f"        double r{k} = 0.0, c{k} = 0.0;", f"        in >> r{k} >> c{k};",
                      f"        mlab::Mat a{k}(static_cast<std::size_t>(r{k}), static_cast<std::size_t>(c{k}), 0.0);",
                      f"        for (double& x : a{k}.data) in >> x;"]
        else:
            lines += [f"        double a{k} = 0.0;", f"        in >> a{k};"]
        args.append(f"a{k}")
    lines.append(f"        const auto out = {ns}::{fn}({', '.join(args)});")
    outs = sig["outputs"]
    for k, (name, t) in enumerate(outs):
        ref = "out" if len(outs) == 1 else f"out.{sig['output_fields'][k]}"
        if _is_array(t):
            lines.append(f"        for (double x : {ref}.data) std::printf(\"%.17g \", x);")
        else:
            lines.append(f"        std::printf(\"%.17g \", static_cast<double>({ref}));")
    lines += ["        std::printf(\"\\n\");", "    }", "    return 0;", "}", ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- runners
def load_python(code):
    """Exec generated Python code into a fresh module object."""
    mod = types.ModuleType(code.signature.get("module", "generated"))
    exec(compile(next(iter(code.files.values())), f"<generated {mod.__name__}>", "exec"), mod.__dict__)
    return mod


def run_interpreter(path, cases, function=None):
    it = Interpreter.from_file(path, output=lambda s: None)
    nout = len(parse_file(path).function(function).outputs)
    return [sum((flatten(v) for v in it.call(function, *a, nargout=nout)), []) for a in cases]


def run_python(code, cases):
    mod = load_python(code)
    fn = getattr(mod, code.entry)
    out = []
    for a in cases:
        r = fn(*[to_value(x) for x in a])
        r = r if isinstance(r, tuple) else (r,)
        out.append(sum((flatten(v) for v in r), []))
    return out


def build_native(code, workdir):
    """Write the generated sources plus a test main into workdir and compile -> executable path."""
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    code.write(work)
    sig = code.signature
    if code.target == "rust":
        (work / "main.rs").write_text(rust_main(sig), encoding="utf-8")
        exe = work / ("main_rs.exe")
        compile_rust(work / "main.rs", exe, cwd=work)
    else:
        (work / "main.cpp").write_text(cpp_main(sig), encoding="utf-8")
        exe = work / "main_cpp.exe"
        compile_cpp(["main.cpp", f"{sig['module']}.cpp"], exe, include_dirs=["."], cwd=work)
    return exe


def run_native(code, cases, workdir, exe=None):
    work = Path(workdir)
    exe = exe or build_native(code, work)
    inp = work / "inputs.txt"
    write_inputs(inp, cases, code.signature)
    res = subprocess.run([str(exe), str(inp)], capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        raise RuntimeError(f"Programm {exe.name} fehlgeschlagen:\n{res.stdout}\n{res.stderr}")
    return read_outputs(res.stdout)


def deviation(ref, other):
    max_abs = max_rel = 0.0
    bitwise = True
    for a, b in zip(ref, other):
        if len(a) != len(b):
            return {"max_abs": float("inf"), "max_rel": float("inf"), "bitwise": False, "cases": len(ref)}
        for x, y in zip(a, b):
            if x == y or (x != x and y != y):
                continue
            bitwise = False
            d = abs(x - y)
            max_abs = max(max_abs, d)
            max_rel = max(max_rel, d / max(abs(x), 1e-300))
    if len(ref) != len(other):
        bitwise = False
        max_abs = float("inf")
    return {"max_abs": max_abs, "max_rel": max_rel, "bitwise": bitwise, "cases": len(ref)}


@trace("mathworks_matlab", concept="matlab_codegen_verification", note="back-to-back test interpreter vs. targets")
def verify_file(path, cases, targets=("python", "rust", "cpp"), workdir=None, function=None, input_types=None):
    """Compare the generated code of all ``targets`` with the interpreter on ``cases``."""
    ref = run_interpreter(path, cases, function)
    report = {"interpreter": {"cases": len(cases)}}
    for t in targets:
        code = generate(path, t, function=function, input_types=input_types)
        if not code.ok:
            report[t] = {"error": code.report()}
            continue
        if t == "python":
            out = run_python(code, cases)
        else:
            if workdir is None:
                raise ValueError("workdir für native Ziele erforderlich")
            if (t == "rust" and find_rustc() is None) or (t == "cpp" and find_cpp_compiler() is None):
                raise ToolchainError(f"keine Toolchain für {t}")
            out = run_native(code, cases, Path(workdir) / t)
        report[t] = deviation(ref, out)
    return report
