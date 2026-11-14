"""Trajectory planner model through the REST service: train, inspect, drive against the teacher, plan."""

import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from vdsim.service.app import create_app  # noqa: E402

SITUATION = {"road": [{"kind": "straight", "length": 400}], "ego": {"x": 0, "y": 0, "psi": 0, "vx": 20},
             "target_speed": 20, "d_min": -1.75, "d_max": 5.25, "obstacles": [{"id": 1, "x": 60, "y": 0, "v": 5}]}


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    return TestClient(create_app(model_dir=tmp_path_factory.mktemp("models")))


@pytest.fixture(scope="module")
def model(client):
    r = client.post("/models/train", json={"kind": "trajectory_planner", "n_samples": 500, "epochs": 40, "hidden": [48, 48]})
    assert r.status_code == 202 and r.json()["name"] == "Werling imitation (default)"
    t0 = time.time()
    while time.time() - t0 < 240:
        job = client.get(f"/models/jobs/{r.json()['id']}").json()
        if job["state"] not in ("queued", "running"):
            break
        time.sleep(0.5)
    assert job["state"] == "done", job["error"]
    return client.get(f"/models/{job['model_id']}").json()


def test_training_reports_planner_metrics(model):
    assert model["kind"] == "trajectory_planner" and model["backend"] == "mlp" and len(model["features"]) == 31
    assert set(model["test_metrics"]) == {"lat_delta", "lat_tau", "lon_nu", "lon_tau"}
    m = model["planner_metrics"]
    # safety does not depend on the quality of the network: the same cycles are valid as with the teacher
    assert m["invalid_cycles"] == m["invalid_cycles_teacher"] and m["collisions"] == m["collisions_teacher"]
    assert m["acceptance"] > 0.6 and m["cost_ratio_median"] == pytest.approx(1.0, abs=0.05)
    assert m["network_share"] + m["fallback_share"] + m["out_of_scope_share"] + m["infeasible_share"] == pytest.approx(1.0)


def test_drive_against_the_teacher(client, model):
    r = client.post(f"/models/{model['id']}/drive", json={"situation": SITUATION, "cycles": 40})
    assert r.status_code == 200
    out = r.json()
    s = out["summary"]
    assert s["cycles"] == 40 and not s["collision_learned"] and 0.0 <= s["network_share"] <= 1.0
    assert len(out["learned"]["x"]) == len(out["teacher"]["x"]) == 40 and out["road"]["left_x"] and out["objects"]
    assert s["max_path_difference"] < 2.0                     # same maneuver as the teacher
    random = client.post(f"/models/{model['id']}/drive", json={"seed": 5, "cycles": 10}).json()
    assert random["situation"]["road"] and len(random["learned"]["source"]) == 10
    assert client.post(f"/models/{model['id']}/drive", json={"situation": {**SITUATION, "stop_at": 100.0}}).status_code == 422


def test_plan_with_the_model(client, model):
    plain = client.post("/plan", json=SITUATION).json()
    assert plain["source"] == "teacher" and plain["network_share"] is None
    guided = client.post("/plan", json={**SITUATION, "model": model["id"], "cycles": 10}).json()
    assert guided["trajectory"]["valid"] and guided["source"] in ("network", "teacher") and guided["network_share"] is not None
    assert client.post("/plan", json={**SITUATION, "model": "0123456789ab"}).status_code == 404


def test_model_kinds_are_not_mixed_up(client, model):
    assert client.post(f"/models/{model['id']}/evaluate", json={}).status_code == 422
    assert client.post("/simulate", json={"model": f"neural_{model['id']}"}).status_code == 422
    assert client.post("/models/train", json={"kind": "trajectory_planner", "n_samples": 50000}).status_code == 422


def test_learned_planner_in_the_stack(client, model, monkeypatch):
    # the stack component loads the model from the model store by id
    monkeypatch.setenv("MOTIONENGINE_MODEL_DIR", str(client.app.state.model_dir))
    from vdsim import api

    stack = {"planner": {"component": "trajectory_planner/learned", "params": {"model": model["id"]}}}
    learned, teacher = api.run("einscherer", stack=stack, duration=4.0), api.run("einscherer", duration=4.0)
    sources = [s["info"].get("source") for s in learned.snapshots]
    assert sources.count("network") > 0.5 * len(sources)
    assert learned.kpis["collision"] == teacher.kpis["collision"] == 0
    assert learned.kpis["min_distance"] == pytest.approx(teacher.kpis["min_distance"], abs=1.0)
