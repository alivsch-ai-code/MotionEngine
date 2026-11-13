"""Development environment endpoints: workbench runs, experiments, MATLAB, knowledge."""

import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from vdsim.service.app import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    return TestClient(create_app(model_dir=tmp_path_factory.mktemp("models")))


def _wait(client, url, timeout=120.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        job = client.get(url).json()
        if job["state"] not in ("queued", "running"):
            return job
        time.sleep(0.2)
    raise AssertionError("job did not finish")


def test_catalog_and_graph(client):
    cat = client.get("/workbench/catalog").json()
    assert len(cat["scenarios"]) >= 14 and {layer["layer"] for layer in cat["layers"]} >= {"planner", "controller"}
    planner = next(layer for layer in cat["layers"] if layer["layer"] == "planner")
    assert planner["default"] == "trajectory_planner/werling_parking" and len(planner["components"]) >= 3
    g = client.post("/workbench/graph", json={"stack": {"planner": {"component": "trajectory_planner/werling"}}}).json()
    assert len(g["nodes"]) == 9 and not g["issues"] and "trajectory" in g["ports"]["planner"]["outputs"]
    assert next(n for n in g["nodes"] if n["id"] == "planner")["component"] == "trajectory_planner/werling"


def test_run_result_snapshot_and_download(client):
    r = client.post("/workbench/runs", json={"scenario": "autobahn_ueberholen", "duration": 3.0})
    assert r.status_code == 202
    job = _wait(client, f"/workbench/runs/{r.json()['id']}")
    assert job["state"] == "done" and job["summary"]["n_snapshots"] > 10
    res = client.get(f"/workbench/runs/{job['id']}/result?max_points=200").json()
    assert len(res["signals"]["t"]) <= 200 and {"ego_x", "ego_y", "ego_psi", "ego_v"} <= set(res["signals"])
    assert res["road"]["lanes"] and res["objects"] and res["kpis"] and res["profile"]["planner"]["calls"] > 0
    snap = client.get(f"/workbench/runs/{job['id']}/snapshots/5?max_candidates=40").json()
    assert 0 <= snap["best_index"] < len(snap["candidates_x"]) <= 41 and snap["cost_terms"] and snap["trajectory"]["x"]
    assert client.get(f"/workbench/runs/{job['id']}/snapshots/9999").status_code == 404
    assert client.get(f"/workbench/runs/{job['id']}/download").json()
    assert any(j["id"] == job["id"] for j in client.get("/workbench/runs").json())


def test_run_validation_and_cancel(client):
    assert client.post("/workbench/runs", json={"scenario": "../x"}).status_code == 422
    bad = {"scenario": "autobahn_ueberholen", "stack": {"planner": {"component": "tracking_controller/stanley"}}}
    assert client.post("/workbench/runs", json=bad).status_code == 422
    assert client.get("/workbench/runs/nope").status_code == 404
    r = client.post("/workbench/runs", json={"scenario": "autobahn_ueberholen", "duration": 60.0}).json()
    client.post(f"/workbench/runs/{r['id']}/cancel")
    assert _wait(client, f"/workbench/runs/{r['id']}")["state"] == "cancelled"
    assert client.get(f"/workbench/runs/{r['id']}/result").status_code == 409


def test_experiment_compare(client):
    body = {"kind": "compare", "base": {"scenario": "autobahn_ueberholen", "duration": 2.0}, "layer": "planner",
            "variants": {"werling": {"component": "trajectory_planner/werling"},
                         "naive": {"component": "trajectory_planner/frenet_naive"}}}
    r = client.post("/workbench/experiments", json=body)
    assert r.status_code == 202
    job = _wait(client, f"/workbench/experiments/{r.json()['id']}")
    assert job["state"] == "done" and len(job["records"]) == 2 and all(rec["ok"] for rec in job["records"])
    assert "max_ay" in job["records"][0]["kpis"]
    assert client.post("/workbench/experiments", json={**body, "variants": {}}).status_code == 422
    too_many = {"kind": "sweep", "base": body["base"], "grid": {"seed": list(range(100))}}
    assert client.post("/workbench/experiments", json=too_many).status_code == 422


def test_matlab_and_knowledge(client):
    src = "function y = f(x)\n  y = 2*x + 1;\nend\n"
    conv = client.post("/matlab/convert", json={"source": src}).json()
    assert conv["ok"] and "def f" in conv["files"]["f.py"]
    ana = client.post("/matlab/analyze", json={"source": src}).json()
    assert ana["functions"][0]["name"] == "f" and "x" in ana["functions"][0]["variables"]
    assert client.post("/matlab/convert", json={"source": "function ("}).status_code in (200, 422)
    assert len(client.get("/knowledge/references").json()) > 20
    nodes = client.get("/knowledge/nodes?q=werling&limit=5").json()
    assert nodes and client.get("/knowledge/explain", params={"id": nodes[0]["id"]}).json()["markdown"]
    assert client.get("/knowledge/explain", params={"id": "does-not-exist-xyz"}).status_code == 404
    doc = client.get("/knowledge/components/trajectory_planner/werling").json()
    assert doc["doc"]["summary"] and client.get("/knowledge/components/x/y").status_code == 404


def test_rewired_graph(client):
    g = client.post("/workbench/graph", json={"stack": {}}).json()
    assert g["default_connections"] == g["connections"]
    assert g["ports"]["planner"]["input_types"]["prediction"] == {"type": "Prediction", "optional": False}
    optional_removed = [c for c in g["connections"] if c["to"] != "planner.status"]
    assert not client.post("/workbench/graph", json={"stack": {}, "connections": optional_removed}).json()["issues"]
    required_removed = [c for c in g["connections"] if c["to"] != "planner.prediction"]
    issues = client.post("/workbench/graph", json={"stack": {}, "connections": required_removed}).json()["issues"]
    assert len(issues) == 1 and "planner.prediction" in issues[0]
    r = client.post("/workbench/runs", json={"scenario": "einscherer", "connections": required_removed})
    assert r.status_code == 422 and "planner.prediction" in r.json()["detail"]
    assert client.post("/workbench/graph", json={"connections": [{"from": "a b", "to": "x.y"}]}).status_code == 422


def test_live_session_matches_batch_run_and_import(client):
    body = {"scenario": "einscherer", "duration": 2.0}
    live = client.post("/workbench/live", json=body)
    assert live.status_code == 201
    sid, dt = live.json()["id"], live.json()["base_dt"]
    assert live.json()["frame"]["t"] == 0.0 and live.json()["road"]["lanes"]

    one = client.post(f"/workbench/live/{sid}/advance", json={"steps": 1}).json()        # single step
    assert one["n_steps"] == 1 and one["snapshot"] is not None and not one["stopped"]
    half = client.post(f"/workbench/live/{sid}/advance", json={"seconds": 0.5, "known_snapshots": 99}).json()
    assert half["t"] == pytest.approx(0.5, abs=1.5 * dt) and half["snapshot"] is None and "ego_x" in half["row"]
    end = client.post(f"/workbench/live/{sid}/advance", json={"seconds": 2.0}).json()
    assert end["stopped"] and end["t"] == pytest.approx(2.0, abs=dt)

    job = client.post(f"/workbench/live/{sid}/finish").json()
    assert job["state"] == "done" and job["kind"] == "live" and job["summary"]["duration"] == pytest.approx(2.0)
    assert client.post(f"/workbench/live/{sid}/advance", json={"steps": 1}).status_code == 404
    live_result = client.get(f"/workbench/runs/{job['id']}/result").json()

    batch = client.post("/workbench/runs", json=body).json()
    assert _wait(client, f"/workbench/runs/{batch['id']}")["state"] == "done"
    batch_result = client.get(f"/workbench/runs/{batch['id']}/result").json()
    assert live_result["signals"]["ego_x"][-1] == pytest.approx(batch_result["signals"]["ego_x"][-1], abs=1e-9)
    assert live_result["kpis"]["min_distance"] == batch_result["kpis"]["min_distance"]

    # the download is one file and loads again
    saved = client.get(f"/workbench/runs/{job['id']}/download").json()
    assert saved["format"] == "motionengine-ad-result"
    loaded = client.post("/workbench/runs/import", json={"meta": saved["meta"], "npz": saved["npz"], "name": "loaded"})
    assert loaded.status_code == 201 and loaded.json()["kind"] == "import" and loaded.json()["name"] == "loaded"
    again = client.get(f"/workbench/runs/{loaded.json()['id']}/result").json()
    assert again["signals"]["ego_x"] == live_result["signals"]["ego_x"] and again["kpis"] == live_result["kpis"]
    assert client.get(f"/workbench/runs/{loaded.json()['id']}/snapshots/3").json()["trajectory"]["x"]
    assert client.post("/workbench/runs/import", json={"meta": {}, "npz": "AAAA"}).status_code == 422
    assert client.post("/workbench/runs/import", json={"meta": {}, "npz": saved["npz"]}).status_code == 422


def test_live_session_limits(client):
    assert client.post("/workbench/live", json={"scenario": "nope"}).status_code == 422
    assert client.post("/workbench/live/unknown/advance", json={"steps": 1}).status_code == 404
    sid = client.post("/workbench/live", json={"scenario": "einscherer"}).json()["id"]
    assert client.post(f"/workbench/live/{sid}/advance", json={"seconds": 5.0}).status_code == 422
    assert client.delete(f"/workbench/live/{sid}").status_code == 204
    assert client.post(f"/workbench/live/{sid}/advance", json={"steps": 1}).status_code == 404
