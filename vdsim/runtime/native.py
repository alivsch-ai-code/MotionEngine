"""Native custom nodes (C ABI) for Rust and C++, loaded with ctypes.

Specs: "rust:path/to/crate", "cpp:path/to/dir" (built on demand, see build.py) or a path to
an already built library (.dll/.so/.dylib). The library is copied to a shadow path with a
version counter before loading (Windows locks loaded DLLs, so the original can be rebuilt
while the node runs). The node appears as a regular Component; its class (ports,
parameters, KIND/NAME/VERSION) is created from vdsim_node_info().

C ABI (version 1), all functions extern "C":
    uint32_t    vdsim_abi_version(void)
    const char* vdsim_node_info(void)                       JSON, see below
    void*       vdsim_create(const double* params, size_t n) parameters in declared order
    void        vdsim_destroy(void* h)
    int32_t     vdsim_reset(void* h, double dt, uint64_t seed)
    int32_t     vdsim_step(void* h, double t, size_t n_in, const double* const* in, const size_t* in_len,
                           size_t n_out, double* const* out, const size_t* out_cap, size_t* out_len)
    int32_t     vdsim_fetch_outputs(void* h, size_t n_out, double* const* out, const size_t* out_cap,
                                    size_t* out_len)          after rc 1: copy the pending outputs again
    int32_t     vdsim_output(void* h, double t, size_t n_out, double* const* out, ...)   no feedthrough
    int32_t     vdsim_update(void* h, double t, double dt, size_t n_in, const double* const* in,
                             const size_t* in_len)           no feedthrough
    size_t      vdsim_get_state(void* h, double* buf, size_t cap)   returns the required length
    int32_t     vdsim_set_state(void* h, const double* buf, size_t n)
    const char* vdsim_last_error(void* h)
Return codes: 0 ok, 1 an output buffer was too small (out_len holds the required sizes),
< 0 error (message via vdsim_last_error). out_len = 0 means "output not set" (value held).
Inputs that are not connected / not yet available have length 0.

node_info JSON:
    {"name": "...", "kind": "tracking_controller", "version": "1.0.0", "label": "...",
     "category": "...", "direct_feedthrough": true, "period": null,
     "inputs":  [{"name": "ego", "type": "EgoState", "optional": false, "feedback": false}, ...],
     "outputs": [{"name": "command", "type": "ControlCommand", "capacity": 6}, ...],
     "params":  [{"name": "lookahead", "default": 4.0, "label": "Vorausschau", "unit": "m"}, ...]}
"""

from __future__ import annotations

import ctypes
import itertools
import json
import os
import shutil
import sys
import weakref
from dataclasses import asdict, make_dataclass
from pathlib import Path

import numpy as np

from ..core.parameters import param
from ..framework.component import Component, Port
from ..framework.context import stable_seed
from ..framework.knowledge import ComponentDoc
from ..framework.types import TYPES
from . import build as B
from . import codecs
from .python_nodes import resolve_path

ABI_VERSION = 1
_DP = ctypes.POINTER(ctypes.c_double)
_DPP = ctypes.POINTER(_DP)
_SP = ctypes.POINTER(ctypes.c_size_t)
_shadow_counter = itertools.count(1)
_LIBS = {}       # (artifact path, mtime_ns) -> NativeLibrary
_CACHED_TYPES = ("PlannedTrajectory", "Prediction", "ReferenceLine", "ObjectList", "WorldState")


class NativeNodeError(RuntimeError):
    pass


def _free_library(handle):
    if sys.platform.startswith("win"):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.FreeLibrary.argtypes = [ctypes.c_void_p]
        kernel32.FreeLibrary.restype = ctypes.c_int
        return bool(kernel32.FreeLibrary(ctypes.c_void_p(handle)))
    try:
        import _ctypes
        _ctypes.dlclose(handle)
        return True
    except (ImportError, OSError, AttributeError):
        return False


_cleaned = set()


def _cleanup_shadows(shadow_dir):
    # remove shadow copies of earlier processes (still locked ones are skipped)
    if str(shadow_dir) in _cleaned:
        return
    _cleaned.add(str(shadow_dir))
    tag = f"_{os.getpid()}_"
    for f in shadow_dir.glob("*"):
        if tag not in f.name:
            try:
                f.unlink()
            except OSError:
                pass


class NativeLibrary:
    """One loaded (shadow-copied) node library, shared by all instances of that build."""

    def __init__(self, path, language="native", shadow_dir=None):
        self.path = Path(path).resolve()
        self.language = language
        self.mtime = self.path.stat().st_mtime_ns
        shadow_dir = Path(shadow_dir or B.get_build_root() / "shadow")
        shadow_dir.mkdir(parents=True, exist_ok=True)
        _cleanup_shadows(shadow_dir)
        n = next(_shadow_counter)
        self.shadow = shadow_dir / f"{self.path.stem}_{os.getpid()}_{n}{self.path.suffix}"
        shutil.copy2(self.path, self.shadow)
        self.lib = ctypes.CDLL(str(self.shadow))
        self.refs = 0
        self.closed = False
        self._bind()
        try:
            self.info = json.loads(self.lib.vdsim_node_info().decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            self.close()
            raise NativeNodeError(f"{self.path.name}: vdsim_node_info() liefert kein gültiges JSON: {exc}") from None
        self._check_info()

    def _fn(self, name, restype, argtypes, required=True):
        try:
            f = getattr(self.lib, name)
        except AttributeError:
            if required:
                raise NativeNodeError(f"{self.path.name}: ABI-Funktion '{name}' fehlt") from None
            return None
        f.restype, f.argtypes = restype, argtypes
        return f

    def _bind(self):
        vp, d, sz, i32 = ctypes.c_void_p, ctypes.c_double, ctypes.c_size_t, ctypes.c_int32
        ver = self._fn("vdsim_abi_version", ctypes.c_uint32, [])
        if ver() != ABI_VERSION:
            v = ver()
            self.close()
            raise NativeNodeError(f"{self.path.name}: ABI-Version {v}, erwartet {ABI_VERSION} "
                                  f"(Header mit vdsim.runtime.codegen neu erzeugen)")
        self.f_info = self._fn("vdsim_node_info", ctypes.c_char_p, [])
        self.f_create = self._fn("vdsim_create", vp, [_DP, sz])
        self.f_destroy = self._fn("vdsim_destroy", None, [vp])
        self.f_reset = self._fn("vdsim_reset", i32, [vp, d, ctypes.c_uint64])
        self.f_step = self._fn("vdsim_step", i32, [vp, d, sz, _DPP, _SP, sz, _DPP, _SP, _SP], required=False)
        self.f_fetch = self._fn("vdsim_fetch_outputs", i32, [vp, sz, _DPP, _SP, _SP], required=False)
        self.f_output = self._fn("vdsim_output", i32, [vp, d, sz, _DPP, _SP, _SP], required=False)
        self.f_update = self._fn("vdsim_update", i32, [vp, d, d, sz, _DPP, _SP], required=False)
        self.f_get_state = self._fn("vdsim_get_state", sz, [vp, _DP, sz])
        self.f_set_state = self._fn("vdsim_set_state", i32, [vp, _DP, sz])
        self.f_error = self._fn("vdsim_last_error", ctypes.c_char_p, [vp], required=False)

    def _check_info(self):
        info = self.info
        for key in ("name", "inputs", "outputs"):
            if key not in info:
                raise NativeNodeError(f"{self.path.name}: node_info ohne '{key}'")
        for p in info["inputs"] + info["outputs"]:
            t = p.get("type", "Any")
            if t not in TYPES:
                raise NativeNodeError(f"{self.path.name}: Port '{p.get('name')}' hat unbekannten Typ '{t}'")
            if not codecs.has_codec(t):
                raise NativeNodeError(f"{self.path.name}: Port '{p.get('name')}': für Typ '{t}' gibt es keinen "
                                      f"flachen Codec (unterstützt: {', '.join(codecs.CODEC_TYPES)})")
        ft = info.get("direct_feedthrough", True)
        if ft and self.f_step is None:
            raise NativeNodeError(f"{self.path.name}: vdsim_step fehlt")
        if not ft and (self.f_output is None or self.f_update is None):
            raise NativeNodeError(f"{self.path.name}: Node ohne Durchgriff braucht vdsim_output und vdsim_update")

    def acquire(self):
        self.refs += 1

    def release(self):
        self.refs -= 1
        if self.refs <= 0:
            self.close()

    def close(self):
        if self.closed:
            return
        self.closed = True
        for k, v in list(_LIBS.items()):
            if v is self:
                del _LIBS[k]
        handle = getattr(self.lib, "_handle", None)
        self.lib = None
        if handle:
            _free_library(handle)
        try:
            self.shadow.unlink()
        except OSError:
            pass


def library(path, language="native"):
    path = Path(path).resolve()
    key = (str(path), path.stat().st_mtime_ns)
    lib = _LIBS.get(key)
    if lib is None or lib.closed:
        lib = _LIBS[key] = NativeLibrary(path, language)
        lib.cls = make_native_class(lib, language)
    return lib


# ---------------------------------------------------------------------------- component
class NativeComponent(Component):
    """Base class of the generated component classes (one per loaded library)."""

    LANGUAGE = "native"
    # reuse the encoding of large inputs if the very same object arrives again (values are treated as immutable)
    cache_inputs = True
    _LIBRARY = None
    _IN = ()        # ((name, type), ...) in ABI order
    _OUT = ()

    def __init__(self, params=None, **overrides):
        super().__init__(params, **overrides)
        self._lib = type(self)._LIBRARY
        self._lib.acquire()
        self._h = None
        self._closed = False
        n_out = len(self._OUT)
        self._out_bufs = [np.zeros(max(1, int(cap)), dtype=float) for cap in self._CAPS]
        self._out_ptrs = (_DP * max(1, n_out))()
        self._out_caps = (ctypes.c_size_t * max(1, n_out))()
        self._out_lens = (ctypes.c_size_t * max(1, n_out))()
        for i, buf in enumerate(self._out_bufs):
            self._set_out(i, buf)
        n_in = len(self._IN)
        self._in_cache = [None] * n_in
        self._in_ptrs = (_DP * max(1, n_in))()
        self._in_lens = (ctypes.c_size_t * max(1, n_in))()
        self._state_buf = np.zeros(64)
        self._hbox = [None]
        self._create()
        weakref.finalize(self, NativeComponent._finalize, self._lib, self._hbox)

    # ------------------------------------------------------------------ handle management
    def _param_vector(self):
        vals = []
        for name in self._PARAM_NAMES:
            v = getattr(self.params, name)
            vals.append(float(v))
        return np.asarray(vals, dtype=float)

    def _create(self):
        pv = self._param_vector()
        self._pv = pv
        ptr = pv.ctypes.data_as(_DP) if pv.size else None
        self._h = self._lib.f_create(ptr, pv.size)
        self._hbox[0] = self._h
        if not self._h:
            raise NativeNodeError(f"Native Node '{self.NAME}': vdsim_create() fehlgeschlagen (Parameter: {pv.tolist()})")

    @staticmethod
    def _finalize(lib, handle_box):
        # last resort if close() was not called
        if lib is not None and not lib.closed and handle_box and handle_box[0]:
            try:
                lib.f_destroy(handle_box[0])
            except Exception:  # noqa: BLE001
                pass

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._h and self._lib is not None and not self._lib.closed:
            self._lib.f_destroy(self._h)
        self._h = None
        self._hbox[0] = None
        if self._lib is not None:
            self._lib.release()

    def _error(self, rc, what):
        msg = ""
        if self._lib.f_error is not None and self._h:
            raw = self._lib.f_error(self._h)
            msg = raw.decode("utf-8", "replace") if raw else ""
        raise NativeNodeError(f"Native Node '{self.instance_name}' ({self.LANGUAGE}): {what} fehlgeschlagen "
                              f"(Code {rc}){': ' + msg if msg else ''}")

    def _set_out(self, i, buf):
        self._out_ptrs[i] = buf.ctypes.data_as(_DP)
        self._out_caps[i] = buf.size

    # ------------------------------------------------------------------ buffers
    def _encode_inputs(self, inputs):
        arrays = []
        cache = self._in_cache
        for i, (name, tp) in enumerate(self._IN):
            v = inputs.get(name) if inputs else None
            hit = cache[i] if self.cache_inputs and tp in _CACHED_TYPES else None
            if hit is not None and hit[0] is v:
                arr = hit[1]          # same (unchanged) object as in the previous call, e.g. 10 Hz trajectory
            else:
                arr = codecs.encode(tp, v) if v is not None else np.zeros(0)
                arr = np.ascontiguousarray(arr, dtype=float)
                if tp in _CACHED_TYPES:
                    cache[i] = (v, arr)
            arrays.append(arr)
            self._in_ptrs[i] = arr.ctypes.data_as(_DP) if arr.size else None
            self._in_lens[i] = arr.size
        return arrays          # keep alive during the call

    def _collect(self, rc, what):
        if rc == 1:
            for i, buf in enumerate(self._out_bufs):
                need = self._out_lens[i]
                if need > buf.size:
                    nb = np.zeros(int(need * 1.5) + 1)
                    self._out_bufs[i] = nb
                    self._set_out(i, nb)
            if self._lib.f_fetch is None:
                raise NativeNodeError(f"Native Node '{self.instance_name}': Ausgangspuffer zu klein und "
                                      f"vdsim_fetch_outputs fehlt")
            rc = self._lib.f_fetch(self._h, len(self._OUT), self._out_ptrs, self._out_caps, self._out_lens)
        if rc != 0:
            self._error(rc, what)
        out = {}
        for i, (name, tp) in enumerate(self._OUT):
            n = self._out_lens[i]
            if n:
                out[name] = codecs.decode(tp, self._out_bufs[i][:n].copy())
        return out

    # ------------------------------------------------------------------ lifecycle
    def reset(self, context):
        super().reset(context)
        dt = getattr(self, "sample_time", None) or getattr(context, "dt", 0.01)
        seed = stable_seed(getattr(context, "seed", 0), self.instance_name)
        rc = self._lib.f_reset(self._h, float(dt), seed)
        if rc != 0:
            self._error(rc, "reset()")

    def step(self, t, inputs):
        keep = self._encode_inputs(inputs)
        rc = self._lib.f_step(self._h, float(t), len(self._IN), self._in_ptrs, self._in_lens, len(self._OUT),
                              self._out_ptrs, self._out_caps, self._out_lens)
        del keep
        return self._collect(rc, "step()")

    def output(self, t):
        rc = self._lib.f_output(self._h, float(t), len(self._OUT), self._out_ptrs, self._out_caps, self._out_lens)
        return self._collect(rc, "output()")

    def update(self, t, inputs, dt):
        keep = self._encode_inputs(inputs)
        rc = self._lib.f_update(self._h, float(t), float(dt), len(self._IN), self._in_ptrs, self._in_lens)
        del keep
        if rc != 0:
            self._error(rc, "update()")

    # ------------------------------------------------------------------ state (hot reload)
    def native_state(self):
        n = self._lib.f_get_state(self._h, self._state_buf.ctypes.data_as(_DP), self._state_buf.size)
        if n > self._state_buf.size:
            self._state_buf = np.zeros(int(n * 1.5) + 1)
            n = self._lib.f_get_state(self._h, self._state_buf.ctypes.data_as(_DP), self._state_buf.size)
        return self._state_buf[:n].copy()

    def set_native_state(self, arr):
        arr = np.ascontiguousarray(arr, dtype=float)
        rc = self._lib.f_set_state(self._h, arr.ctypes.data_as(_DP) if arr.size else None, arr.size)
        if rc != 0:
            self._error(rc, "set_state()")

    def get_state(self):
        return {"__native_state__": self.native_state(), "signals": dict(self.signals)}

    def set_state(self, state):
        if "__native_state__" in state:
            self.set_native_state(state["__native_state__"])
        if "signals" in state:
            self.signals = dict(state["signals"])

    def params_changed(self, name=None):
        # parameters are passed to create(): recreate the native object and keep its state
        state = self.native_state()
        old = self._h
        self._create()
        self._lib.f_destroy(old)
        if self.context is not None:
            self.reset(self.context)
        self.set_native_state(state)

    def __repr__(self):
        return f"<NativeComponent {self.spec()} ({self.LANGUAGE}) from {self._LIBRARY.path.name}>"


def make_native_class(lib, language):
    info = lib.info
    pfields = []
    names = []
    for p in info.get("params", []):
        limits = {k: p[k] for k in ("min", "max", "step") if k in p}
        if p.get("description"):
            limits["description"] = p["description"]
        pfields.append((p["name"], float, param(float(p.get("default", 0.0)), p.get("unit", ""),
                                                p.get("label", p["name"]), **limits)))
        names.append(p["name"])
    params_cls = make_dataclass(f"{_camel(info['name'])}Params", pfields)
    inputs = {p["name"]: Port(p.get("type", "Any"), p.get("description", ""), p.get("unit", ""),
                              bool(p.get("optional", False)), bool(p.get("feedback", False))) for p in info["inputs"]}
    outputs = {p["name"]: Port(p.get("type", "Any"), p.get("description", ""), p.get("unit", ""))
               for p in info["outputs"]}
    caps = [int(p.get("capacity") or codecs.DEFAULT_CAPACITY.get(p.get("type"), 64)) for p in info["outputs"]]
    attrs = {
        "KIND": info.get("kind", "node"), "NAME": info["name"], "VERSION": info.get("version", "1.0.0"),
        "LABEL": info.get("label", info["name"]), "CATEGORY": info.get("category", ""),
        "INPUTS": inputs, "OUTPUTS": outputs, "PARAMS": params_cls, "PERIOD": info.get("period"),
        "DIRECT_FEEDTHROUGH": bool(info.get("direct_feedthrough", True)), "LANGUAGE": language,
        "DOC": ComponentDoc(summary=info.get("summary", f"Native Node ({language}) aus {lib.path.name}")),
        "_LIBRARY": lib, "_IN": tuple((p["name"], p.get("type", "Any")) for p in info["inputs"]),
        "_OUT": tuple((p["name"], p.get("type", "Any")) for p in info["outputs"]), "_CAPS": tuple(caps),
        "_PARAM_NAMES": tuple(names),
    }
    cls = type(f"Native{_camel(info['name'])}", (NativeComponent,), attrs)
    cls.__module__ = __name__
    return cls


def _camel(name):
    return "".join(part.capitalize() for part in str(name).replace("-", "_").split("_") if part) or "Node"


# ---------------------------------------------------------------------------- loading / hot reload
class NativeSource:
    """Reload information for a native node (rebuild on source change, shadow-copy reload)."""

    def __init__(self, language, project_dir, build_dir, artifact, stamp):
        self.kind = language
        self.project_dir = Path(project_dir) if project_dir else None
        self.build_dir = build_dir
        self.artifact = Path(artifact)
        self.stamp = stamp
        self._failed = None
        self.last_build = None

    def describe(self):
        return f"{self.kind}:{(self.project_dir or self.artifact).as_posix()}"

    def _current(self):
        if self.project_dir is None:
            st = self.artifact.stat()
            return (st.st_mtime_ns, 1)
        return B.source_stamp(self.kind, self.project_dir)

    def changed(self):
        try:
            cur = self._current()
        except OSError:
            return False
        return cur != self.stamp and cur != self._failed

    def mark_failed(self):
        try:
            self._failed = self._current()
        except OSError:
            pass

    def prepare(self):
        if self.project_dir is None:
            return None
        res = B.build(self.kind, self.project_dir, self.build_dir)
        self.last_build = res
        if not res.ok:
            raise B.NativeBuildError(res)
        return res

    def instantiate(self, old):
        if self.last_build is None and self.project_dir is not None:
            self.prepare()
        stamp = self._current()
        lib = library(self.artifact, self.kind)
        cls = lib.cls
        p_old = asdict(old.params) if getattr(old, "params", None) is not None else {}
        names = set(cls._PARAM_NAMES)
        inst = cls({k: v for k, v in p_old.items() if k in names})
        inst._vdsim_source = NativeSource(self.kind, self.project_dir, self.build_dir, self.artifact, stamp)
        if self.last_build is not None:
            inst.build_log = self.last_build.log
        self.last_build = None
        return inst


def load_native_node(language, path, params=None, build_dir=None):
    """Loader for "rust:" / "cpp:" specs: build if needed, load, instantiate."""
    p = resolve_path(path)
    if p.is_file() and p.suffix.lower() in (".dll", ".so", ".dylib"):
        lib = library(p, language)
        inst = lib.cls(params)
        st = p.stat()
        inst._vdsim_source = NativeSource(language, None, None, p, (st.st_mtime_ns, 1))
        return inst
    if not p.is_dir():
        raise NativeNodeError(f"'{path}' ist weder ein Projektordner noch eine Bibliothek")
    stamp = B.source_stamp(language, p)
    res = B.build(language, p, build_dir)
    if not res.ok:
        raise B.NativeBuildError(res)
    lib = library(res.artifact, language)
    inst = lib.cls(params)
    inst.build_log = res.log
    inst._vdsim_source = NativeSource(language, p, build_dir, res.artifact, stamp)
    return inst
