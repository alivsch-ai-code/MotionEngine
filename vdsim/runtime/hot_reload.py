"""Hot reloading of custom nodes (Python and native).

Every instance created by a custom-node loader carries `_vdsim_source` with
    changed()            mtime polling of the source files
    prepare()            expensive part (native: rebuild), may run in a background thread
    instantiate(old)     new instance with the parameters of the old one
    mark_failed()        remember the broken source state (no endless retries)

Reload sequence (HotReloader._swap):
    1. new = source.instantiate(old)                 error -> old instance stays active
    2. new.reset(old.context); new.set_state(old.get_state())
    3. ports changed? -> graph re-validated; invalid -> old instance stays active
    4. graph.replace_instance(); executor recompiles at the next step; old.close() (FreeLibrary)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .graph import _port_signature


@dataclass
class ReloadEvent:
    node: str
    ok: bool
    message: str
    kind: str = "python"
    ports_changed: bool = False
    pending: bool = False
    duration: float = 0.0
    log: str = ""


class HotReloader:
    def __init__(self, graph, executor=None, poll_interval=0.0, async_build=False):
        self.graph = graph
        self.executor = executor
        self.poll_interval = poll_interval
        self.async_build = async_build
        self._last_poll = -1e18
        self._jobs = {}          # node id -> (thread, holder)

    def watched(self):
        return {nid: n.instance._vdsim_source for nid, n in self.graph.nodes.items()
                if getattr(n.instance, "_vdsim_source", None) is not None}

    def check(self, force=False):
        now = time.monotonic()
        if not force and now - self._last_poll < self.poll_interval:
            return []
        self._last_poll = now
        events = []
        for nid, holder in list(self._jobs.items()):
            thread, box = holder
            if thread.is_alive():
                continue
            del self._jobs[nid]
            if nid in self.graph.nodes:
                events.append(self._finish(nid, box))
        for nid, src in self.watched().items():
            if nid in self._jobs or not (force or src.changed()):
                continue
            if self.async_build and getattr(src, "kind", "python") != "python":
                box = {"src": src, "t0": time.perf_counter()}
                thread = threading.Thread(target=self._prepare, args=(src, box), daemon=True)
                self._jobs[nid] = (thread, box)
                thread.start()
                events.append(ReloadEvent(nid, True, f"Knoten '{nid}': Quelländerung erkannt, Build läuft ...",
                                          src.kind, pending=True))
                continue
            box = {"src": src, "t0": time.perf_counter()}
            self._prepare(src, box)
            events.append(self._finish(nid, box))
        return events

    def wait(self, timeout=None):
        # block until background builds are finished, then apply them
        for thread, _ in list(self._jobs.values()):
            thread.join(timeout)
        return self.check(force=False) if not self._jobs else []

    @staticmethod
    def _prepare(src, box):
        try:
            box["prepared"] = src.prepare()
        except Exception as exc:  # noqa: BLE001
            box["error"] = exc

    def _finish(self, nid, box):
        src = box["src"]
        kind = getattr(src, "kind", "python")
        if "error" in box:
            src.mark_failed()
            exc = box["error"]
            return ReloadEvent(nid, False, f"Neuladen von '{nid}' fehlgeschlagen ({type(exc).__name__}: {exc}); "
                                           f"die bisherige Version bleibt aktiv.", kind,
                               duration=time.perf_counter() - box["t0"], log=getattr(exc, "log", ""))
        return self._swap(nid, src, box)

    def _swap(self, nid, src, box):
        node = self.graph.nodes[nid]
        old = node.instance
        kind = getattr(src, "kind", "python")
        t0 = box["t0"]
        try:
            new = src.instantiate(old)
        except Exception as exc:  # noqa: BLE001
            src.mark_failed()
            return ReloadEvent(nid, False, f"Neuladen von '{nid}' fehlgeschlagen ({type(exc).__name__}: {exc}); "
                                           f"die bisherige Version bleibt aktiv.", kind,
                               duration=time.perf_counter() - t0)
        new.instance_name = nid
        new_src = new._vdsim_source
        try:
            if getattr(old, "context", None) is not None:
                if getattr(old, "sample_time", None) is not None:
                    new.sample_time = old.sample_time
                new.reset(old.context)
            new.set_state(old.get_state())
        except Exception as exc:  # noqa: BLE001
            _close(new)
            src.mark_failed()
            return ReloadEvent(nid, False, f"Zustandsübertragung für '{nid}' fehlgeschlagen ({type(exc).__name__}: "
                                           f"{exc}); die bisherige Version bleibt aktiv.", kind,
                               duration=time.perf_counter() - t0)
        new._vdsim_source = new_src          # set_state may have copied the old source object
        ports_changed = _port_signature(old.ports()) != _port_signature(new.ports())
        node.instance = new
        if ports_changed:
            rep = self.graph.validate()
            if rep.errors:
                node.instance = old
                _close(new)
                src.mark_failed()
                return ReloadEvent(nid, False, f"Neu geladene Version von '{nid}' hat geänderte Ports und macht den "
                                               f"Graphen ungültig; die bisherige Version bleibt aktiv:\n{rep.text()}",
                                   kind, ports_changed=True, duration=time.perf_counter() - t0)
        node.instance = old
        self.graph.replace_instance(nid, new, structural=True)
        if self.executor is not None:
            self.executor.mark_initialized(new)
        _close(old)
        msg = f"Knoten '{nid}' neu geladen ({kind}, Version {new.VERSION})"
        if ports_changed:
            msg += ", Ports geändert, Graph neu validiert"
        return ReloadEvent(nid, True, msg, kind, ports_changed, duration=time.perf_counter() - t0,
                           log=getattr(new, "build_log", ""))


def _close(inst):
    fn = getattr(inst, "close", None)
    if callable(fn):
        try:
            fn()
        except Exception:  # noqa: BLE001
            pass
