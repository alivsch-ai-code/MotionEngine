"""Detection and invocation of native toolchains (rustc/cargo, MSVC cl.exe, g++/clang++).

    tc = find_cpp_compiler()          # Toolchain or None
    compile_cpp(["main.cpp", "ctrl.cpp"], "ctrl.exe", include_dirs=["."], toolchain=tc, cwd=build_dir)
    compile_rust("main.rs", "main.exe", cwd=build_dir)

On Windows without g++/clang++ on PATH, Visual Studio is located with ``vswhere.exe``
(fallback: the default VS 2022 installation paths); the environment of ``vcvars64.bat`` is
captured once and reused for every ``cl`` call. ``VDSIM_CXX`` may point to a compiler.
"""

from __future__ import annotations

import functools
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

VSWHERE = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / \
    "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
VS_DEFAULTS = [Path(r"C:\Program Files\Microsoft Visual Studio\2022") / ed / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
               for ed in ("Community", "Professional", "Enterprise", "BuildTools")]


class ToolchainError(RuntimeError):
    """Compilation failed (message contains the compiler output)."""


@dataclass
class Toolchain:
    kind: str                         # msvc / gcc / clang / rustc / cargo
    executable: str
    env: dict | None = None           # environment for the compiler (MSVC)
    version: str = ""
    extra: dict = field(default_factory=dict)


def _run(cmd, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 300)
    return subprocess.run(cmd, **kw)


@functools.cache
def find_rustc():
    exe = shutil.which("rustc") or _home_cargo_bin("rustc")
    if not exe:
        return None
    try:
        version = _run([exe, "--version"], timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return Toolchain("rustc", exe, version=version)


@functools.cache
def find_cargo():
    exe = shutil.which("cargo") or _home_cargo_bin("cargo")
    if not exe:
        return None
    try:
        version = _run([exe, "--version"], timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return Toolchain("cargo", exe, version=version)


def _home_cargo_bin(name):
    p = Path.home() / ".cargo" / "bin" / (name + (".exe" if os.name == "nt" else ""))
    return str(p) if p.exists() else None


@functools.cache
def find_vcvars():
    """Path of vcvars64.bat of the newest Visual Studio with C++ tools (or None)."""
    if os.name != "nt":
        return None
    if VSWHERE.exists():
        try:
            out = _run([str(VSWHERE), "-latest", "-products", "*", "-requires",
                        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
                       timeout=60).stdout.strip()
            for line in out.splitlines():
                p = Path(line.strip()) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
                if p.exists():
                    return str(p)
        except (OSError, subprocess.SubprocessError):
            pass
    for p in VS_DEFAULTS:
        if p.exists():
            return str(p)
    return None


@functools.cache
def msvc_environment(vcvars):
    """Environment variables after 'call vcvars64.bat' (captured once)."""
    cmd = f'cmd /d /c "call "{vcvars}" >nul 2>&1 && set"'
    res = _run(cmd, timeout=120)
    if res.returncode != 0:
        raise ToolchainError(f"vcvars64.bat fehlgeschlagen:\n{res.stdout}\n{res.stderr}")
    env = {}
    for line in res.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key:
            env[key] = value
    return env


@functools.cache
def find_cpp_compiler():
    """C++17 compiler: $VDSIM_CXX, g++ or clang++ on PATH, else MSVC via vswhere/vcvars64."""
    custom = os.environ.get("VDSIM_CXX")
    candidates = [custom] if custom else []
    candidates += ["g++", "clang++"]
    for c in candidates:
        exe = shutil.which(c) if c else None
        if exe:
            kind = "msvc" if Path(exe).name.lower().startswith("cl") else "clang" if "clang" in exe else "gcc"
            return Toolchain(kind, exe)
    vcvars = find_vcvars()
    if vcvars:
        try:
            env = msvc_environment(vcvars)
        except ToolchainError:
            return None
        cl = shutil.which("cl", path=env.get("Path") or env.get("PATH"))
        if cl:
            return Toolchain("msvc", cl, env=env, extra={"vcvars": vcvars})
    return None


def compile_cpp(sources, output, include_dirs=(), toolchain=None, cwd=None):
    """Compile C++17 sources to an executable; raises ToolchainError with the compiler log."""
    tc = toolchain or find_cpp_compiler()
    if tc is None:
        raise ToolchainError("kein C++-Compiler gefunden (g++/clang++/MSVC)")
    cwd = str(cwd or Path(output).parent)
    if tc.kind == "msvc":
        cmd = [tc.executable, "/nologo", "/EHsc", "/O2", "/std:c++17", "/fp:precise", "/W3", "/utf-8"]
        cmd += [f"/I{d}" for d in include_dirs] + [str(s) for s in sources] + [f"/Fe:{output}"]
        res = _run(cmd, cwd=cwd, env=tc.env)
    else:
        cmd = [tc.executable, "-std=c++17", "-O2", "-ffp-contract=off", "-Wall"]
        cmd += [f"-I{d}" for d in include_dirs] + [str(s) for s in sources] + ["-o", str(output)]
        res = _run(cmd, cwd=cwd)
    if res.returncode != 0:
        raise ToolchainError(f"C++-Kompilierung fehlgeschlagen ({tc.kind}):\n{res.stdout}\n{res.stderr}")
    return res


def compile_rust(source, output, toolchain=None, cwd=None, optimize=True):
    """Compile a Rust crate root file with rustc (std only)."""
    tc = toolchain or find_rustc()
    if tc is None:
        raise ToolchainError("rustc nicht gefunden")
    cmd = [tc.executable, "--edition", "2021", "-C", "debuginfo=0"] + (["-O"] if optimize else []) + \
        [str(source), "-o", str(output)]
    linker, env = msvc_linker(), None
    if linker:                         # MSVC target: explicit link.exe and the vcvars environment (LIB paths)
        cmd[1:1] = ["-C", f"linker={linker}"]
        env = dict(msvc_environment(find_vcvars()))
        for key in ("USERPROFILE", "CARGO_HOME", "RUSTUP_HOME", "HOME"):
            if key in os.environ:
                env.setdefault(key, os.environ[key])
    res = _run(cmd, cwd=str(cwd or Path(output).parent), env=env)
    if res.returncode != 0:
        raise ToolchainError(f"Rust-Kompilierung fehlgeschlagen:\n{res.stdout}\n{res.stderr}")
    return res


@functools.cache
def msvc_linker():
    """MSVC link.exe (Windows); avoids a foreign 'link' on PATH (e.g. Git's coreutils) when calling rustc."""
    if os.name != "nt":
        return None
    vcvars = find_vcvars()
    if not vcvars:
        return None
    try:
        env = msvc_environment(vcvars)
    except ToolchainError:
        return None
    for d in (env.get("Path") or env.get("PATH") or "").split(os.pathsep):
        p = Path(d) / "link.exe"
        if p.exists() and "MSVC" in str(p):
            return str(p)
    return None


def available():
    """Summary of the detected toolchains (CLI 'toolchains')."""
    cpp = find_cpp_compiler()
    rustc, cargo = find_rustc(), find_cargo()
    return {"cpp": {"kind": cpp.kind, "executable": cpp.executable} if cpp else None,
            "rustc": rustc.version if rustc else None, "cargo": cargo.version if cargo else None,
            "vcvars": find_vcvars()}


@functools.cache
def probe_rust_link():
    """(ok, message): can rustc build and link an executable here?"""
    return _probe("rust", 'fn main() { println!("{}", 1.5f64.sin()); }\n')


@functools.cache
def probe_cpp():
    """(ok, message): can the C++ compiler build and link an executable here (e.g. Windows SDK present)?"""
    return _probe("cpp", '#include <cmath>\n#include <cstdio>\nint main() { std::printf("%g", std::sin(1.5)); }\n')


def _probe(kind, source):
    import tempfile
    with tempfile.TemporaryDirectory(prefix="vdsim_probe_") as d:
        src = Path(d) / ("probe.rs" if kind == "rust" else "probe.cpp")
        src.write_text(source, encoding="utf-8")
        exe = Path(d) / "probe.exe"
        try:
            if kind == "rust":
                compile_rust(src, exe, cwd=d, optimize=False)
            else:
                compile_cpp([src.name], exe, cwd=d)
            res = _run([str(exe)], timeout=60)
            return (res.returncode == 0, res.stdout.strip())
        except (ToolchainError, OSError, subprocess.SubprocessError) as exc:
            msg = str(exc)
            if "kernel32.lib" in msg or "crtdbg.h" in msg or "corecrt" in msg:
                msg = "Windows SDK/UCRT fehlt (kernel32.lib bzw. CRT-Header nicht gefunden): " + msg[:300]
            return (False, msg[:800])


def check_rust(source, cwd=None):
    """Type-check a Rust module without linking (rustc --emit=metadata)."""
    tc = find_rustc()
    if tc is None:
        raise ToolchainError("rustc nicht gefunden")
    src = Path(source)
    out = Path(cwd or src.parent) / (src.stem + ".rmeta")
    res = _run([tc.executable, "--edition", "2021", "--crate-type", "lib", "--emit=metadata", str(src), "-o",
                str(out)], cwd=str(cwd or src.parent))
    if res.returncode != 0:
        raise ToolchainError(f"Rust-Typprüfung fehlgeschlagen:\n{res.stdout}\n{res.stderr}")
    return res
