"""REST/JSON API (standard library only).

    python run_api.py --port 8765 [--token SECRET]

Binds to 127.0.0.1 by default. Long runs are executed in a background thread; POST returns
a job id, GET /api/v1/jobs/{id} returns the state and the KPIs. The OpenAPI 3.1
description is served at /api/v1/openapi.json.
"""

from __future__ import annotations

import json
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np

from .. import api

PREFIX = "/api/v1"


def _clean(obj):
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _clean(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if np.isfinite(v) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (str, int, bool)) or obj is None:
        return obj
    return str(obj)


class JobStore:
    def __init__(self, workers=2):
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.jobs = {}
        self.results = {}
        self.lock = threading.Lock()

    def submit(self, kind, fn, *args):
        job_id = uuid.uuid4().hex[:12]
        with self.lock:
            self.jobs[job_id] = {"id": job_id, "kind": kind, "state": "queued"}

        def runner():
            with self.lock:
                self.jobs[job_id]["state"] = "running"
            try:
                out = fn(*args)
                with self.lock:
                    self.results[job_id] = out
                    self.jobs[job_id].update(state="done", summary=_summarize(out))
            except Exception as exc:
                with self.lock:
                    self.jobs[job_id].update(state="failed", error=repr(exc), traceback=traceback.format_exc())
        self.pool.submit(runner)
        return job_id


def _summarize(out):
    if hasattr(out, "kpis") and hasattr(out, "signals"):
        return {"kpis": out.kpis, "stop_reason": out.metadata.get("stop_reason", ""), "duration": out.duration,
                "signals": sorted(out.signals)}
    if hasattr(out, "records"):
        return {"records": [{"label": r.get("label"), "ok": r.get("ok"), "kpis": r.get("kpis"),
                             "error": r.get("error")} for r in out.records],
                "statistics": out.statistics()}
    return out


def openapi_spec():
    def op(summary, body=False):
        spec = {"summary": summary, "responses": {"200": {"description": "OK"}}}
        if body:
            spec["requestBody"] = {"content": {"application/json": {"schema": {"type": "object"}}}}
        return spec
    paths = {
        "/info": {"get": op("Plattform- und API-Version")},
        "/components": {"get": op("Komponenten (optional ?kind=)")},
        "/components/{kind}/{name}": {"get": op("Komponentenbeschreibung inkl. Ports, Parameter, Doku")},
        "/scenarios": {"get": op("Szenario-Bibliothek")},
        "/stack/default": {"get": op("Standard-Stack nach Werling")},
        "/graphs/build": {"post": op("Graph aus Stack-Definition erzeugen", True)},
        "/graphs/validate": {"post": op("Graph validieren (Typprüfung, Schleifen)", True)},
        "/runs": {"post": op("Szenario simulieren (asynchron, liefert Job-ID)", True)},
        "/batch": {"post": op("Batch-Simulation", True)},
        "/sweep": {"post": op("Parameter-Sweep", True)},
        "/montecarlo": {"post": op("Monte-Carlo-Simulation", True)},
        "/jobs": {"get": op("Alle Jobs")},
        "/jobs/{id}": {"get": op("Status und Ergebnis eines Jobs")},
        "/jobs/{id}/signals": {"get": op("Zeitreihen eines Laufs (?keys=t,ego_v)")},
        "/matlab/analyze": {"post": op("MATLAB-Quelltext analysieren", True)},
        "/matlab/convert": {"post": op("MATLAB nach python/cpp/rust konvertieren", True)},
        "/knowledge/references": {"get": op("Literatur- und Quellendatenbank")},
    }
    return {"openapi": "3.1.0", "info": {"title": "vdsim API", "version": "1.0.0",
                                         "description": "Entwicklungs- und Simulationsplattform für automatisierte Fahrfunktionen"},
            "servers": [{"url": PREFIX}], "paths": paths,
            "components": {"securitySchemes": {"apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"}}}}


def make_handler(store, token=None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "vdsim-api/1.0"

        def log_message(self, fmt, *args):  # quiet by default
            pass

        def _send(self, code, payload):
            body = json.dumps(_clean(payload), ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _auth(self):
            if token and self.headers.get("X-API-Key") != token:
                self._send(401, {"error": "ungültiger oder fehlender API-Schlüssel"})
                return False
            return True

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}") if n else {}

        def do_GET(self):
            if not self._auth():
                return
            url = urlparse(self.path)
            path, query = url.path, parse_qs(url.query)
            if not path.startswith(PREFIX):
                return self._send(404, {"error": "unbekannter Pfad"})
            parts = [p for p in path[len(PREFIX):].split("/") if p]
            try:
                if parts == ["info"]:
                    return self._send(200, api.info())
                if parts == ["openapi.json"]:
                    return self._send(200, openapi_spec())
                if parts == ["components"]:
                    return self._send(200, api.list_components(query.get("kind", [None])[0]))
                if len(parts) == 3 and parts[0] == "components":
                    return self._send(200, api.describe_component(f"{parts[1]}/{parts[2]}"))
                if parts == ["scenarios"]:
                    return self._send(200, api.list_scenarios())
                if parts == ["stack", "default"]:
                    return self._send(200, api.default_stack())
                if parts == ["jobs"]:
                    return self._send(200, list(store.jobs.values()))
                if len(parts) == 2 and parts[0] == "jobs":
                    job = store.jobs.get(parts[1])
                    return self._send(200, job) if job else self._send(404, {"error": "Job unbekannt"})
                if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "signals":
                    res = store.results.get(parts[1])
                    if res is None or not hasattr(res, "signals"):
                        return self._send(404, {"error": "kein Simulationsergebnis"})
                    keys = query.get("keys", [""])[0].split(",") if query.get("keys") else list(res.signals)
                    return self._send(200, {k: res.signals[k] for k in keys if k in res.signals})
                if parts == ["knowledge", "references"]:
                    return self._send(200, api.references())
            except KeyError as exc:
                return self._send(404, {"error": str(exc)})
            except Exception as exc:
                return self._send(500, {"error": repr(exc)})
            return self._send(404, {"error": "unbekannter Pfad"})

        def do_POST(self):
            if not self._auth():
                return
            path = urlparse(self.path).path
            parts = [p for p in path[len(PREFIX):].split("/") if p] if path.startswith(PREFIX) else []
            try:
                body = self._body()
                if parts == ["graphs", "build"]:
                    return self._send(200, api.build_graph(body.get("stack")))
                if parts == ["graphs", "validate"]:
                    return self._send(200, {"issues": api.validate_graph(body.get("graph", body))})
                if parts == ["runs"]:
                    job_id = store.submit("run", api.run, body["scenario"], body.get("stack"), body.get("seed"),
                                          body.get("duration"), body.get("scenario_params"), body.get("snapshots", False))
                    return self._send(202, {"id": job_id, "state": "queued"})
                if parts == ["batch"]:
                    job_id = store.submit("batch", api.run_batch, body["jobs"], int(body.get("workers", 0)))
                    return self._send(202, {"id": job_id, "state": "queued"})
                if parts == ["sweep"]:
                    job_id = store.submit("sweep", api.sweep, body["base_job"], body["grid"], int(body.get("workers", 0)))
                    return self._send(202, {"id": job_id, "state": "queued"})
                if parts == ["montecarlo"]:
                    job_id = store.submit("montecarlo", api.monte_carlo, body["base_job"], body["distributions"],
                                          int(body["n"]), int(body.get("seed", 0)), int(body.get("workers", 0)))
                    return self._send(202, {"id": job_id, "state": "queued"})
                if parts == ["matlab", "analyze"]:
                    return self._send(200, api.matlab_analyze(body["source"]))
                if parts == ["matlab", "convert"]:
                    return self._send(200, {"code": api.matlab_convert(body["source"], body.get("target", "python"))})
            except KeyError as exc:
                return self._send(400, {"error": f"fehlendes Feld {exc}"})
            except Exception as exc:
                return self._send(500, {"error": repr(exc)})
            return self._send(404, {"error": "unbekannter Pfad"})

    return Handler


def serve(host="127.0.0.1", port=8765, token=None, workers=2):
    store = JobStore(workers)
    httpd = ThreadingHTTPServer((host, port), make_handler(store, token))
    return httpd, store


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="vdsim REST-API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", default=None, help="API-Schlüssel (Header X-API-Key)")
    args = parser.parse_args(argv)
    httpd, _ = serve(args.host, args.port, args.token)
    print(f"vdsim API auf http://{args.host}:{args.port}{PREFIX}  (OpenAPI: {PREFIX}/openapi.json)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
