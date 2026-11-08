"""Command line entry points: scenario runner, MATLAB tool, knowledge tool, legacy REST endpoints."""

import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from vdsim.cli.scenario import main as scenario_main
from vdsim.simulation.scenario import Scenario


@pytest.fixture
def short_scenario(tmp_path):
    path = tmp_path / "kurz.json"
    Scenario(name="Kurz", model="bicycle_linear", maneuver="step_steer",
             maneuver_params={"speed_kmh": 60, "duration": 2}, duration=1.5).save(path)
    return path


def test_scenario_cli_list(capsys):
    scenario_main(["--list"])
    out = capsys.readouterr().out
    assert "iso_doppelspurwechsel_80" in out and "kreisfahrt_r40" in out


def test_scenario_cli_help_without_arguments(capsys):
    scenario_main([])
    assert "usage" in capsys.readouterr().out.lower()


def test_scenario_cli_run_and_exports(short_scenario, tmp_path, capsys, monkeypatch):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    monkeypatch.setattr(plt, "show", lambda: None)
    csv, pdf, md = tmp_path / "r.csv", tmp_path / "r.pdf", tmp_path / "r.md"
    scenario_main([str(short_scenario), str(short_scenario), "--csv", str(csv), "--report", str(pdf),
                   "--summary", str(md), "--plot"])
    out = capsys.readouterr().out
    assert "=== Kurz" in out and "Max. Querbeschleunigung" in out
    assert csv.read_text().startswith("t,") and pdf.read_bytes()[:4] == b"%PDF" and md.exists()
    plt.close("all")


# ----------------------------------------------------------------------------- MATLAB tool
def test_matlab_cli(tmp_path, capsys):
    from tests_path import FIXTURES

    from vdsim.matlab.__main__ import main as matlab_main
    src = FIXTURES / "pid_controller.m"
    assert matlab_main(["analyze", str(src)]) in (0, None)
    assert "pid_controller" in capsys.readouterr().out
    assert matlab_main(["analyze", str(src), "--json"]) in (0, None)
    json.loads(capsys.readouterr().out)
    for extra in (["--dot", "dataflow"], ["--dot", "calls"], ["--latex"]):
        assert matlab_main(["analyze", str(src), *extra]) in (0, None)
        assert capsys.readouterr().out
    assert matlab_main(["convert", str(src), "--to", "python", "--out", str(tmp_path)]) in (0, None)
    assert list(tmp_path.glob("*.py"))
    assert matlab_main(["run", str(FIXTURES / "subfunctions.m"), "1.0", "2.0"]) in (0, None)
    assert capsys.readouterr().out
    assert matlab_main(["toolchains"]) in (0, None)


# ----------------------------------------------------------------------------- knowledge tool
def test_knowledge_cli(tmp_path, capsys):
    from vdsim.knowledge.cli import main as kb_main
    assert kb_main(["--report", "--quiet"]) in (0, 1, None)
    assert kb_main(["--search", "Werling", "--quiet"]) in (0, None)
    assert "werling" in capsys.readouterr().out.lower()
    assert kb_main(["--explain", "planning", "--quiet"]) in (0, None)
    bib = tmp_path / "refs.bib"
    assert kb_main(["--bibtex", str(bib), "--quiet"]) in (0, None)
    assert "@" in bib.read_text(encoding="utf-8")


# ----------------------------------------------------------------------------- legacy REST server
@pytest.fixture
def legacy():
    from vdsim.api.server import serve
    httpd, store = serve(port=0, token=None)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}/api/v1", store
    httpd.shutdown()
    httpd.server_close()


def _call(url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"},
                                 method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def _wait(base, job_id, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, job = _call(f"{base}/jobs/{job_id}")
        if job["state"] in ("done", "failed"):
            return job
        time.sleep(0.05)
    raise TimeoutError(job_id)


def test_legacy_rest_jobs(legacy):
    base, _ = legacy
    status, info = _call(f"{base}/info")
    assert status == 200 and info["api_version"] == 1
    assert _call(f"{base}/scenarios")[0] == 200 and _call(f"{base}/stack/default")[0] == 200
    status, comps = _call(f"{base}/components?kind=predictor")
    assert status == 200 and comps
    spec = comps[0] if isinstance(comps[0], str) else f"{comps[0]['kind']}/{comps[0]['name']}"
    assert _call(f"{base}/components/{spec}")[0] == 200
    assert _call(f"{base}/components/nope/nope")[0] in (404, 500)
    status, job = _call(f"{base}/runs", {"scenario": "einscherer", "duration": 0.5, "seed": 1})
    assert status == 202
    done = _wait(base, job["id"])
    assert done["state"] == "done" and "kpis" in done["summary"]
    status, sig = _call(f"{base}/jobs/{job['id']}/signals?keys=t")
    assert status == 200 and list(sig) == ["t"]
    assert _call(f"{base}/jobs")[0] == 200
    assert _call(f"{base}/jobs/unknown")[0] == 404 and _call(f"{base}/jobs/unknown/signals")[0] == 404
    base_job = {"scenario": "einscherer", "duration": 0.3}
    for path, body in (("batch", {"jobs": [base_job]}),
                       ("sweep", {"base_job": base_job, "grid": {"seed": [1, 2]}}),
                       ("montecarlo", {"base_job": base_job, "n": 2,
                                       "distributions": {"seed": {"dist": "integer", "low": 0, "high": 5}}})):
        status, job = _call(f"{base}/{path}", body)
        assert status == 202, path
        done = _wait(base, job["id"])
        assert done["state"] == "done" and done["summary"]["records"], path
    assert _call(f"{base}/runs", {})[0] == 400
    assert _call(f"{base}/unknown", {})[0] == 404 and _call(f"{base}/unknown")[0] == 404
    assert _call(base.replace("/api/v1", "/other"))[0] == 404


def test_legacy_rest_graph_and_matlab(legacy):
    base, _ = legacy
    _, graph = _call(f"{base}/graphs/build", {"stack": {}})
    status, res = _call(f"{base}/graphs/validate", {"graph": graph})
    assert status == 200 and res["issues"] == []
    src = "function y = f(x)\ny = 2 * x + 1;\nend\n"
    status, res = _call(f"{base}/matlab/analyze", {"source": src})
    assert status == 200 and res["functions"][0]["name"] == "f"
    status, res = _call(f"{base}/matlab/convert", {"source": src, "target": "python"})
    assert status == 200 and res["code"]["ok"] and "def f(" in next(iter(res["code"]["files"].values()))
    # a path is parsed as MATLAB source text, never opened on the server
    status, res = _call(f"{base}/matlab/analyze", {"source": "/etc/passwd.m"})
    assert status == 500 or not any("root" in str(v) for v in res.values())
    status, refs = _call(f"{base}/knowledge/references")
    assert status == 200 and refs


def test_public_python_api_knowledge_functions(tmp_path):
    from vdsim import api
    refs = api.references()
    assert "werling2011" in refs and refs["werling2011"]["title"]
    assert type(api.knowledge_graph()).__name__ == "KnowledgeGraph"
    conv = api.matlab_convert("function y = g(x)\ny = x * 3;\nend\n", "python")
    assert conv["ok"] and conv["files"]
