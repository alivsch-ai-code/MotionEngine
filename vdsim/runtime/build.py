"""Build orchestration for native custom nodes (Rust via cargo, C++ via MSVC / g++ / clang++).

    res = build("rust", "examples/custom_nodes/rust/my_controller_node")    # BuildResult
    res.ok, res.artifact, res.log, res.duration
    job = build_async("cpp", "path/to/dir", callback=print)                 # background thread

Build artifacts go to a build directory outside the source tree (default:
<tempdir>/vdsim_native, override with set_build_root() or VDSIM_BUILD_DIR), so example
crates never get a target/ folder.

Windows toolchain discovery: cargo / cl are taken from PATH; otherwise Visual Studio is
located with vswhere.exe and the environment of vcvars64.bat is captured once and cached
(running vcvars takes several seconds). If the Windows SDK is missing (no kernel32.lib),
Rust builds still work: import libraries for the system DLLs are generated with
dumpbin/lib.exe from the MSVC tools (fallback, logged). C++ additionally needs the UCRT
headers of the Windows SDK; without them the C++ build is reported as unavailable.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..core.logging_setup import get_logger

log = get_logger("runtime.build")
IS_WINDOWS = sys.platform.startswith("win")
LIB_SUFFIX = ".dll" if IS_WINDOWS else (".dylib" if sys.platform == "darwin" else ".so")
VSWHERE = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio" / \
    "Installer" / "vswhere.exe"
_build_root = None
_lock = threading.Lock()
_SYSTEM_IMPORT_LIBS = {"kernel32": "kernel32", "ntdll": "ntdll", "userenv": "userenv", "ws2_32": "ws2_32",
                       "dbghelp": "dbghelp", "advapi32": "advapi32", "bcrypt": "bcrypt",
                       "bcryptprimitives": "bcryptprimitives", "ucrt": "ucrtbase", "user32": "user32",
                       "shell32": "shell32", "ole32": "ole32", "oleaut32": "oleaut32"}


class NativeBuildError(RuntimeError):
    def __init__(self, result):
        tail = "\n".join(result.log.strip().splitlines()[-25:])
        super().__init__(f"Build von '{result.project}' ({result.language}) fehlgeschlagen:\n{tail}")
        self.result = result
        self.log = result.log


@dataclass
class BuildResult:
    ok: bool
    language: str
    project: str
    artifact: Path | None = None
    log: str = ""
    duration: float = 0.0
    command: list = field(default_factory=list)
    build_dir: Path | None = None
    skipped: bool = False          # artifact was up to date

    def raise_for_error(self):
        if not self.ok:
            raise NativeBuildError(self)
        return self


# ---------------------------------------------------------------------------- build directories
def get_build_root():
    if _build_root is not None:
        return Path(_build_root)
    env = os.environ.get("VDSIM_BUILD_DIR")
    return Path(env) if env else Path(tempfile.gettempdir()) / "vdsim_native"


def set_build_root(path):
    global _build_root
    _build_root = None if path is None else Path(path)


def build_dir_for(language, project_dir):
    project_dir = Path(project_dir).resolve()
    digest = hashlib.sha1(str(project_dir).lower().encode()).hexdigest()[:10]
    return get_build_root() / f"{language}_{project_dir.name}_{digest}"


def toolchain_cache_dir():
    return Path(tempfile.gettempdir()) / "vdsim_toolchain"


# ---------------------------------------------------------------------------- sources
def source_files(language, project_dir):
    project_dir = Path(project_dir)
    if language == "rust":
        files = [project_dir / "Cargo.toml"] + sorted((project_dir / "src").rglob("*.rs"))
        build_rs = project_dir / "build.rs"
        if build_rs.exists():
            files.append(build_rs)
        return [f for f in files if f.exists()]
    exts = {".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hh"}
    skip = {"build", "target", ".history", "__pycache__"}
    return sorted(f for f in project_dir.rglob("*")
                  if f.suffix.lower() in exts and not skip & set(f.relative_to(project_dir).parts[:-1]))


def source_stamp(language, project_dir):
    files = source_files(language, project_dir)
    return max((f.stat().st_mtime_ns for f in files), default=0), len(files)


def rust_lib_name(crate_dir):
    text = (Path(crate_dir) / "Cargo.toml").read_text(encoding="utf-8")
    lib = re.search(r"^\[lib\][^\[]*?^name\s*=\s*\"([^\"]+)\"", text, re.M | re.S)
    if lib:
        return lib.group(1)
    pkg = re.search(r"^\[package\][^\[]*?^name\s*=\s*\"([^\"]+)\"", text, re.M | re.S)
    if not pkg:
        raise ValueError(f"{crate_dir}/Cargo.toml: kein Paketname gefunden")
    return pkg.group(1).replace("-", "_")


def artifact_path(language, project_dir, build_dir=None):
    build_dir = Path(build_dir or build_dir_for(language, project_dir))
    if language == "rust":
        name = rust_lib_name(project_dir)
        prefix = "" if IS_WINDOWS else "lib"
        return build_dir / "release" / f"{prefix}{name}{LIB_SUFFIX}"
    return build_dir / f"{Path(project_dir).resolve().name}{LIB_SUFFIX}"


def needs_rebuild(language, project_dir, build_dir=None):
    art = artifact_path(language, project_dir, build_dir)
    if not art.exists():
        return True
    return source_stamp(language, project_dir)[0] > art.stat().st_mtime_ns


# ---------------------------------------------------------------------------- MSVC environment
def find_vs_installation():
    if not IS_WINDOWS or not VSWHERE.exists():
        return None
    try:
        out = subprocess.run([str(VSWHERE), "-latest", "-products", "*", "-requires",
                              "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    path = out.stdout.strip().splitlines()
    return Path(path[0]) if path and Path(path[0]).exists() else None


def _env_key(env, name):
    for k in env:
        if k.upper() == name.upper():
            return k
    return name


_msvc_env_cache = {}


def msvc_environment():
    """Environment of vcvars64.bat (cached in memory and on disk), or None."""
    if "env" in _msvc_env_cache:
        return _msvc_env_cache["env"]
    env = None
    vs = find_vs_installation()
    if vs is not None:
        bat = vs / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
        if bat.exists():
            cache = toolchain_cache_dir() / "msvc_env.json"
            key = f"{bat}|{bat.stat().st_mtime_ns}"
            try:
                data = json.loads(cache.read_text(encoding="utf-8"))
                if data.get("key") == key:
                    env = data["vars"]
            except (OSError, ValueError, KeyError):
                pass
            if env is None:
                out = subprocess.run(f'cmd /s /c ""{bat}" >nul && set"', capture_output=True, text=True, timeout=120)
                if out.returncode == 0:
                    captured = dict(line.split("=", 1) for line in out.stdout.splitlines() if "=" in line)
                    keep = ("PATH", "INCLUDE", "LIB", "LIBPATH", "VCINSTALLDIR", "VCTOOLSINSTALLDIR",
                            "VSINSTALLDIR", "WINDOWSSDKDIR", "UCRTVERSION", "UNIVERSALCRTSDKDIR",
                            "WINDOWSSDKVERSION", "VCTOOLSVERSION")
                    env = {k: v for k, v in captured.items() if k.upper() in keep}
                    try:
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        cache.write_text(json.dumps({"key": key, "vars": env}), encoding="utf-8")
                    except OSError:
                        pass
    _msvc_env_cache["env"] = env
    return env


def _merged_env(extra):
    env = dict(os.environ)
    if extra:
        for k, v in extra.items():
            env[_env_key(env, k)] = v
    return env


def _dirs(env, name):
    return [Path(p) for p in env.get(_env_key(env, name), "").split(os.pathsep) if p]


def _find_in(dirs, filename):
    for d in dirs:
        if (d / filename).exists():
            return d / filename
    return None


def windows_sdk_libs_available(env):
    return _find_in(_dirs(env, "LIB"), "kernel32.lib") is not None


def ucrt_headers_available(env):
    return _find_in(_dirs(env, "INCLUDE"), "math.h") is not None


def ensure_import_libs(env):
    """Generate import libraries for system DLLs (fallback without Windows SDK). Returns the dir or None."""
    out_dir = toolchain_cache_dir() / "implibs"
    with _lock:
        if (out_dir / "done.txt").exists():
            return out_dir
        tools = _dirs(env, "PATH")
        dumpbin, libexe = _find_in(tools, "dumpbin.exe"), _find_in(tools, "lib.exe")
        if dumpbin is None or libexe is None:
            return None
        out_dir.mkdir(parents=True, exist_ok=True)
        sysdir = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
        for lib, dll in _SYSTEM_IMPORT_LIBS.items():
            dll_path = sysdir / f"{dll}.dll"
            if not dll_path.exists():
                dll_path = sysdir / "downlevel" / f"{dll}.dll"
                if not dll_path.exists():
                    continue
            res = subprocess.run([str(dumpbin), "/nologo", "/exports", str(dll_path)], capture_output=True, text=True,
                                 env=_merged_env(env), timeout=120)
            names, started = [], False
            for line in res.stdout.splitlines():
                if "ordinal hint" in line:
                    started = True
                    continue
                m = re.match(r"\s+\d+\s+[0-9A-F]+\s+(?:[0-9A-F]{8}\s+)?([A-Za-z_?@$][\w?@$]*)", line)
                if started and m:
                    names.append(m.group(1))
            if not names:
                continue
            deffile = out_dir / f"{lib}.def"
            deffile.write_text(f"LIBRARY {dll}.dll\nEXPORTS\n" + "\n".join(names) + "\n", encoding="ascii",
                               errors="ignore")
            subprocess.run([str(libexe), "/nologo", f"/def:{deffile}", f"/out:{out_dir / (lib + '.lib')}",
                            "/machine:x64"], capture_output=True, text=True, env=_merged_env(env), timeout=120)
        (out_dir / "done.txt").write_text("ok", encoding="ascii")
        log.warning("Windows SDK nicht gefunden: Import-Bibliotheken aus System-DLLs erzeugt (%s)", out_dir)
        return out_dir


def rust_environment():
    """(env overrides or None, note) for cargo on this machine."""
    if not IS_WINDOWS:
        return None, ""
    env = msvc_environment()
    if env is None:
        return None, ""
    env = dict(env)
    note = ""
    if not windows_sdk_libs_available(env):
        implibs = ensure_import_libs(env)
        if implibs is not None:
            env[_env_key(env, "LIB")] = env.get(_env_key(env, "LIB"), "") + os.pathsep + str(implibs)
            note = (f"Hinweis: Windows SDK fehlt, verwende erzeugte Import-Bibliotheken aus {implibs} "
                    f"(Abhilfe: 'Windows 11 SDK' im Visual Studio Installer installieren)\n")
    return env, note


# ---------------------------------------------------------------------------- toolchains
def find_cargo():
    cargo = shutil.which("cargo")
    if cargo:
        return cargo
    cand = Path.home() / ".cargo" / "bin" / ("cargo.exe" if IS_WINDOWS else "cargo")
    return str(cand) if cand.exists() else None


@dataclass
class CppCompiler:
    kind: str                  # "msvc" | "gcc" | "clang"
    path: str
    env: dict | None = None
    usable: bool = True
    problem: str = ""


def find_cpp_compiler():
    """Best available C++ compiler (CppCompiler with usable/problem) or None."""
    if IS_WINDOWS:
        cl = shutil.which("cl")
        if cl:
            return CppCompiler("msvc", cl, None)
        env = msvc_environment()
        if env is not None:
            cl = shutil.which("cl", path=env.get(_env_key(env, "PATH"), ""))
            if cl:
                comp = CppCompiler("msvc", cl, dict(env))
                if not ucrt_headers_available(env):
                    comp.usable = False
                    comp.problem = ("Windows SDK (UCRT-Header, z. B. math.h) nicht installiert: C++-Build mit MSVC "
                                    "nicht möglich. Abhilfe: im Visual Studio Installer die Komponente "
                                    "'Windows 11 SDK' installieren.")
                elif not windows_sdk_libs_available(env):
                    implibs = ensure_import_libs(env)
                    if implibs is not None:
                        comp.env[_env_key(comp.env, "LIB")] += os.pathsep + str(implibs)
                gpp = shutil.which("g++") or shutil.which("clang++")
                if comp.usable or not gpp:
                    return comp
    for name, kind in (("g++", "gcc"), ("clang++", "clang")):
        exe = shutil.which(name)
        if exe:
            return CppCompiler(kind, exe, None)
    return None


_probe_cache = {}


def toolchain_status(language):
    """(available: bool, message) - checks that a trivial library can be built (cached per process)."""
    if language in _probe_cache:
        return _probe_cache[language]
    tmp = Path(tempfile.mkdtemp(prefix=f"vdsim_probe_{language}_"))
    try:
        if language == "rust":
            if find_cargo() is None:
                res = (False, "cargo nicht gefunden")
            else:
                (tmp / "src").mkdir()
                (tmp / "Cargo.toml").write_text('[package]\nname = "vdsim_probe"\nversion = "0.1.0"\nedition = "2021"\n'
                                                '[lib]\ncrate-type = ["cdylib"]\n', encoding="utf-8")
                (tmp / "src" / "lib.rs").write_text('#[no_mangle]\npub extern "C" fn vdsim_probe() -> i32 { 42 }\n',
                                                    encoding="utf-8")
                r = build_rust(tmp, tmp / "target")
                res = (r.ok, "ok" if r.ok else r.log[-2000:])
        else:
            comp = find_cpp_compiler()
            if comp is None:
                res = (False, "kein C++-Compiler gefunden (cl, g++, clang++)")
            elif not comp.usable:
                res = (False, comp.problem)
            else:
                (tmp / "probe.cpp").write_text('#include <vector>\n#include <cmath>\nextern "C"\n#ifdef _WIN32\n'
                                               '__declspec(dllexport)\n#endif\nint vdsim_probe() { std::vector<double> '
                                               'v(2, 1.0); return (int)std::sqrt(v[0] + v[1] + 2.0); }\n',
                                               encoding="utf-8")
                r = build_cpp(tmp, tmp / "build", compiler=comp)
                res = (r.ok, "ok" if r.ok else r.log[-2000:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    _probe_cache[language] = res
    return res


# ---------------------------------------------------------------------------- builds
def _run(cmd, cwd, env, timeout):
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace")
        return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), time.perf_counter() - t0
    except subprocess.TimeoutExpired as exc:
        return -1, f"Zeitüberschreitung nach {timeout} s\n{exc.output or ''}", time.perf_counter() - t0
    except OSError as exc:
        return -1, f"Start fehlgeschlagen: {exc}", time.perf_counter() - t0


def build_rust(crate_dir, build_dir=None, release=True, timeout=600):
    crate_dir = Path(crate_dir).resolve()
    build_dir = Path(build_dir or build_dir_for("rust", crate_dir))
    cargo = find_cargo()
    if cargo is None:
        return BuildResult(False, "rust", str(crate_dir), log="cargo nicht gefunden (Rust installieren: rustup.rs)")
    extra, note = rust_environment()
    env = _merged_env(extra)
    env["CARGO_TERM_COLOR"] = "never"
    cmd = [cargo, "build", "--manifest-path", str(crate_dir / "Cargo.toml"), "--target-dir", str(build_dir)]
    if release:
        cmd.append("--release")
    build_dir.mkdir(parents=True, exist_ok=True)
    lock = crate_dir / "Cargo.lock"
    had_lock = lock.exists()
    rc, out, dur = _run(cmd, crate_dir, env, timeout)
    if not had_lock:
        try:
            lock.unlink()           # keep the source tree clean (std-only crates need no lock file)
        except OSError:
            pass
    art = artifact_path("rust", crate_dir, build_dir)
    if not release:
        art = build_dir / "debug" / art.name
    ok = rc == 0 and art.exists()
    return BuildResult(ok, "rust", str(crate_dir), art if ok else None, note + " ".join(cmd) + "\n" + out, dur, cmd,
                       build_dir)


def build_cpp(src_dir, build_dir=None, compiler=None, timeout=600, extra_flags=()):
    src_dir = Path(src_dir).resolve()
    build_dir = Path(build_dir or build_dir_for("cpp", src_dir))
    comp = compiler or find_cpp_compiler()
    if comp is None:
        return BuildResult(False, "cpp", str(src_dir), log="kein C++-Compiler gefunden (MSVC cl, g++ oder clang++)")
    if not comp.usable:
        return BuildResult(False, "cpp", str(src_dir), log=comp.problem)
    sources = [f for f in source_files("cpp", src_dir) if f.suffix.lower() in (".cpp", ".cc", ".cxx", ".c")]
    if not sources:
        return BuildResult(False, "cpp", str(src_dir), log=f"keine C++-Quellen in {src_dir}")
    build_dir.mkdir(parents=True, exist_ok=True)
    art = artifact_path("cpp", src_dir, build_dir)
    if comp.kind == "msvc":
        obj = build_dir / "obj"
        obj.mkdir(exist_ok=True)
        cmd = [comp.path, "/nologo", "/LD", "/O2", "/EHsc", "/std:c++17", "/utf-8", "/W3", f"/I{src_dir}",
               *extra_flags, *[str(s) for s in sources], f"/Fe{art}", f"/Fo{obj}{os.sep}", "/link", "/INCREMENTAL:NO"]
    else:
        cmd = [comp.path, "-shared", "-O2", "-std=c++17", "-fPIC", f"-I{src_dir}", *extra_flags,
               *[str(s) for s in sources], "-o", str(art)]
        if IS_WINDOWS:
            cmd += ["-static-libgcc", "-static-libstdc++"]
    rc, out, dur = _run(cmd, build_dir, _merged_env(comp.env), timeout)
    ok = rc == 0 and art.exists()
    return BuildResult(ok, "cpp", str(src_dir), art if ok else None, " ".join(cmd) + "\n" + out, dur, cmd, build_dir)


def build(language, project_dir, build_dir=None, force=False, **kw):
    """Build if sources are newer than the artifact (force=True: always)."""
    if language not in ("rust", "cpp"):
        raise ValueError(f"unbekannte Sprache '{language}' (rust, cpp)")
    project_dir = Path(project_dir).resolve()
    if not force and not needs_rebuild(language, project_dir, build_dir):
        bdir = Path(build_dir or build_dir_for(language, project_dir))
        return BuildResult(True, language, str(project_dir), artifact_path(language, project_dir, bdir),
                           "Artefakt aktuell, kein Build nötig", 0.0, [], bdir, skipped=True)
    fn = build_rust if language == "rust" else build_cpp
    res = fn(project_dir, build_dir, **kw)
    log.info("build %s %s: %s (%.1f s)", language, project_dir.name, "ok" if res.ok else "FEHLER", res.duration)
    return res


class BuildJob:
    """Background build (thread); result available via .result / wait()."""

    def __init__(self, language, project_dir, callback=None, **kw):
        self.language, self.project_dir = language, project_dir
        self.result = None
        self._callback = callback
        self._thread = threading.Thread(target=self._run, args=(kw,), daemon=True)
        self._thread.start()

    def _run(self, kw):
        try:
            self.result = build(self.language, self.project_dir, **kw)
        except Exception as exc:  # noqa: BLE001
            self.result = BuildResult(False, self.language, str(self.project_dir), log=f"{type(exc).__name__}: {exc}")
        if self._callback is not None:
            self._callback(self.result)

    def done(self):
        return not self._thread.is_alive()

    def wait(self, timeout=None):
        self._thread.join(timeout)
        return self.result


def build_async(language, project_dir, callback=None, **kw):
    return BuildJob(language, project_dir, callback, **kw)
