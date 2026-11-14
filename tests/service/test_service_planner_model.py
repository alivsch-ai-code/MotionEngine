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
    assert r.status_code == 202 and r.json()["name"] == "Werling imitation (default, regression)"
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


def test_approaches_and_situation_settings(client):
    import numpy as np

    from vdsim.learning.trajectory import ChoiceBackend, sample_situation, train_planner

    for approach in ("classification", "dagger"):
        net, meta = train_planner(n_samples=400, epochs=30, hidden=(32, 32), approach=approach, eval_situations=10,
                                  situations={"max_objects": 1, "curve_share": 0.0})
        m = meta["planner_metrics"]
        assert meta["approach"] == approach and meta["situations"]["max_objects"] == 1
        assert m["invalid_cycles"] == m["invalid_cycles_teacher"] and m["collisions"] == m["collisions_teacher"]
        assert m["network_share"] > 0.3
    assert meta["dagger_rounds"] and sum(meta["dagger_rounds"]) > 0          # the learner's own states were labeled
    net, meta = train_planner(n_samples=300, epochs=10, hidden=(16,), approach="classification", eval_situations=5)
    out = ChoiceBackend(net).predict(np.zeros((3, 31)))
    assert out.shape == (3, 4) and all(v in meta["head"]["delta_classes"] for v in out[:, 0])
    # settings change the situations
    rng = np.random.default_rng(0)
    plain = [sample_situation(rng, {"max_objects": 0, "curve_share": 0.0, "speed_min": 10.0, "speed_max": 12.0}) for _ in range(30)]
    assert all(not s["obstacles"] and len(s["road"]) == 1 and 10.0 <= s["ego"]["vx"] <= 12.0 for s in plain)
    assert client.post("/models/train", json={"kind": "trajectory_planner", "approach": "nope"}).status_code == 422
    assert client.post("/models/train", json={"kind": "trajectory_planner", "situations": {"max_objects": 9}}).status_code == 422


def test_connect_an_external_planner_model(client, monkeypatch):
    from vdsim.learning import backends

    class Fixed:                       # stands in for an ONNX graph: always proposes "stay on the lane, keep the speed"
        def __init__(self, data):
            self.data = data

        def predict(self, x):
            import numpy as np

            return np.tile([0.0, 2.0, 0.0, 3.0], (len(x), 1))

    monkeypatch.setattr(backends, "ONNXBackend", Fixed)
    r = client.post("/models/connect", json={"name": "my planner", "backend": "onnx", "onnx_base64": "AAAA",
                                             "kind": "trajectory_planner"})
    assert r.status_code == 201, r.text
    meta = r.json()
    assert meta["kind"] == "trajectory_planner" and meta["approach"] == "external" and len(meta["features"]) == 31
    m = meta["planner_metrics"]
    assert m["invalid_cycles"] == m["invalid_cycles_teacher"] and 0.0 < m["network_share"] <= 1.0
    drive = client.post(f"/models/{meta['id']}/drive", json={"situation": SITUATION, "cycles": 20})
    assert drive.status_code == 200 and not drive.json()["summary"]["collision_learned"]

    class Wrong(Fixed):
        def predict(self, x):
            import numpy as np

            return np.zeros((len(x), 3))

    monkeypatch.setattr(backends, "ONNXBackend", Wrong)
    bad = client.post("/models/connect", json={"name": "x", "backend": "onnx", "onnx_base64": "AAAA", "kind": "trajectory_planner"})
    assert bad.status_code == 422 and "31 inputs to 4 outputs" in bad.json()["detail"]
