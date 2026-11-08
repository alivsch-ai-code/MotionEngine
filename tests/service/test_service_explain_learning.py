"""Trajectory derivation (/plan/explain), neural models (/models/*), parameter schema, stop codes, web hosting."""

import base64
import time

import numpy as np
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from vdsim.learning import MLP, ModelStore, sample_dataset, train_surrogate  # noqa: E402
from vdsim.learning.backends import HTTPBackend  # noqa: E402
from vdsim.planning.polynomials import jerk_integral, polyval  # noqa: E402
from vdsim.service.app import STOP_CODES, create_app  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    return TestClient(create_app(api_key="", model_dir=tmp_path_factory.mktemp("models")))


# ----------------------------------------------------------------------------- explain
@pytest.mark.parametrize("body, lat_mode, lon_mode", [
    ({"target_offset": 3.5, "target_speed": 20.0, "ego": {"vx": 20.0}}, "time", "velocity"),
    ({"stop_at": 40.0, "target_speed": 8.0, "ego": {"vx": 8.0}}, "time", "stopping"),
    ({"target_offset": 1.0, "target_speed": 2.0, "ego": {"vx": 1.0}}, "arc", "velocity"),
])
def test_explain_reproduces_the_planner(client, body, lat_mode, lon_mode):
    r = client.post("/plan/explain", json=body)
    assert r.status_code == 200, r.text
    d = r.json()
    steps = {s["id"]: s for s in d["steps"]}
    assert list(steps) == ["start_state", "lateral", "longitudinal", "selection", "transformation", "constraints",
                           "vehicle_physics"]
    lat, lon, sel = steps["lateral"]["quantities"], steps["longitudinal"]["quantities"], steps["selection"]["quantities"]
    assert lat["mode"] == lat_mode and lon["mode"] == lon_mode
    # coefficients re-derived from the boundary conditions equal the planner's polynomials
    assert lat["verification_max_abs_error"] < 1e-9 and lon["verification_max_abs_error"] < 1e-9
    # the cost recomputed from the formulas equals the planner's cost
    assert sel["cost_total"] == pytest.approx(sel["cost_planner"], rel=1e-9)
    assert sel["cost_total"] == pytest.approx(sel["cost_terms_planner"]["gesamt"], rel=1e-9)
    # jerk integral of the shown coefficients
    c = np.asarray(lon["coefficients"])
    assert lon["jerk_integral"] == pytest.approx(float(jerk_integral(c[None], lon["tau"])[0]), rel=1e-12)
    _, v_end, a_end, _ = (a[0, 0] for a in polyval(c[None], np.array([[lon["tau"]]])))
    if lon_mode == "velocity":
        assert a_end == pytest.approx(0.0, abs=1e-9)
    # every step carries LaTeX formulas, the series is consistent
    assert all(s["formulas"] for s in d["steps"])
    n = len(d["series"]["t"])
    assert all(len(v) == n for v in d["series"].values())
    assert d["candidates"] and sum(c["selected"] for c in d["candidates"]) == 1
    assert all(ch["ok"] for ch in steps["constraints"]["quantities"]["checks"])


def test_explain_vehicle_physics_consistent(client):
    d = client.post("/plan/explain", json={"target_offset": 3.5, "target_speed": 20.0, "ego": {"vx": 20.0}}).json()
    q = next(s for s in d["steps"] if s["id"] == "vehicle_physics")["quantities"]
    # force balance F_yf + F_yr = m a_y and steering = l kappa + EG a_y (linear single track, steady state)
    assert q["F_yf"] + q["F_yr"] == pytest.approx(1600.0 * q["a_y"], rel=1e-9)
    assert q["delta"] == pytest.approx(2.8 * q["kappa"] + q["understeer_gradient"] * q["a_y"], rel=1e-9)
    assert q["a_y"] == pytest.approx(q["v"] ** 2 * q["kappa"], rel=1e-9)


# ----------------------------------------------------------------------------- learning library
def test_mlp_learns_a_smooth_function_and_round_trips():
    rng = np.random.default_rng(0)
    x = rng.uniform(-2, 2, (3000, 2))
    y = np.column_stack([np.sin(x[:, 0]) * x[:, 1], x[:, 0] ** 2])
    net = MLP(2, 2, (32, 32))
    hist = net.fit(x, y, epochs=200, lr=3e-3)
    assert hist[-1]["val"] < 0.02 * hist[0]["val"]
    back = MLP.from_bytes(net.to_bytes())
    assert np.allclose(back.predict(x[:10]), net.predict(x[:10]))


def test_gradients_match_finite_differences():
    rng = np.random.default_rng(1)
    net = MLP(3, 2, (5,))
    x, y = rng.normal(size=(7, 3)), rng.normal(size=(7, 2))
    grads = net._gradients(x, y)
    params = net.W + net.b

    def loss():
        return float(np.mean((net._forward(x)[-1] - y) ** 2))
    for p, g in zip(params, grads):
        i = np.unravel_index(0, p.shape)
        old = p[i]
        p[i] = old + 1e-6
        lp = loss()
        p[i] = old - 1e-6
        lm = loss()
        p[i] = old
        assert g[i] == pytest.approx((lp - lm) / 2e-6, rel=1e-4, abs=1e-8)


def test_dataset_is_the_physics_teacher():
    from vdsim.core.parameters import load_vehicle_preset
    from vdsim.core.registry import create
    from vdsim.learning.dataset import control_for
    from vdsim.simulation.environment import Environment
    cfg = load_vehicle_preset("mid_size_sedan")
    x, y = sample_dataset(cfg, n=50, seed=3)
    model = create("vehicle_model", "bicycle_nonlinear", cfg)
    for i in (0, 17, 49):
        ds = model.derivatives(0, np.array([0, 0, 0, *x[i, :3]]), control_for(x[i, 3], x[i, 4], 0.32),
                               Environment())
        assert np.allclose(ds[3:], y[i])
    assert np.all(np.abs(np.arctan2(x[:, 1], x[:, 0])) <= 0.12 + 1e-12)


def test_trained_surrogate_accuracy():
    # reduced budget for the test (the default 20 000 samples / 150 epochs reach R^2 > 0.998)
    net, meta = train_surrogate(n_samples=8000, epochs=120, hidden=(48, 48))
    for name in ("vx_dot", "vy_dot", "r_dot"):
        assert meta["test_metrics"][name]["r2"] > 0.98, meta["test_metrics"]


def test_store_rejects_paths(tmp_path):
    store = ModelStore(tmp_path)
    for bad in ("../x", "abc", "/etc/passwd", "ABCDEF123456"):
        with pytest.raises(KeyError):
            store.get(bad)


def test_http_backend_protocol(monkeypatch):
    import io
    import json

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    seen = {}

    def fake_urlopen(req, timeout):
        seen["body"] = json.loads(req.data)
        return Resp(json.dumps({"outputs": [[1.0, 2.0, 3.0]]}).encode())
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    out = HTTPBackend("http://models.example/predict").predict([[1, 2, 3, 4, 5]])
    assert out.tolist() == [[1.0, 2.0, 3.0]] and seen["body"] == {"inputs": [[1, 2, 3, 4, 5]]}


# ----------------------------------------------------------------------------- learning API
def _wait(client, job_id, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/models/jobs/{job_id}").json()
        if job["state"] in ("done", "failed", "cancelled"):
            return job
        time.sleep(0.2)
    raise TimeoutError


def test_train_evaluate_simulate_delete(client):
    r = client.post("/models/train", json={"n_samples": 4000, "epochs": 60, "hidden": [32, 32], "name": "test"})
    assert r.status_code == 202
    job = _wait(client, r.json()["id"])
    assert job["state"] == "done" and job["history"] and job["progress"] == 1.0
    mid = job["model_id"]
    meta = client.get(f"/models/{mid}").json()
    assert meta["name"] == "test" and meta["test_metrics"]["vy_dot"]["r2"] > 0.9 and meta["history"]
    assert any(m["id"] == mid and "history" not in m for m in client.get("/models").json())
    sim = client.post("/simulate", json={"model": f"neural_{mid}", "maneuver": "step_steer", "duration": 2.0,
                                        "signals": ["t", "r"]})
    assert sim.status_code == 200 and sim.json()["model"] == f"neural_{mid}"
    ev = client.post(f"/models/{mid}/evaluate", json={"maneuver": "step_steer", "duration": 3.0}).json()
    assert ev["max_position_error"] >= 0 and len(ev["series"]["t"]) == len(ev["series"]["neural_y"])
    assert client.delete(f"/models/{mid}").status_code == 204
    assert client.get(f"/models/{mid}").status_code == 404
    assert client.post("/simulate", json={"model": f"neural_{mid}"}).status_code == 422


def test_train_validation_and_cancel(client):
    assert client.post("/models/train", json={"hidden": [1000]}).status_code == 422
    assert client.post("/models/train", json={"vehicle": "../x"}).status_code == 422
    r = client.post("/models/train", json={"n_samples": 50000, "epochs": 1000})
    jid = r.json()["id"]
    assert client.post("/models/train", json={}).status_code == 409
    client.post(f"/models/jobs/{jid}/cancel")
    assert _wait(client, jid)["state"] in ("cancelled", "done")
    assert client.get("/models/jobs/nope").status_code == 404


def test_connect_rules(client, monkeypatch):
    # HTTP models: only operator-approved hosts (the server would make the request: SSRF)
    r = client.post("/models/connect", json={"name": "x", "backend": "http", "url": "http://169.254.169.254/x"})
    assert r.status_code == 403
    assert client.post("/models/connect", json={"name": "x", "backend": "http", "url": "file:///etc/passwd"}).status_code == 422
    assert client.post("/models/connect", json={"name": "x", "backend": "onnx"}).status_code == 422
    assert client.post("/models/connect", json={"name": "x", "backend": "onnx",
                                                "onnx_base64": "%%%"}).status_code == 422


def test_connect_onnx_model(client):
    pytest.importorskip("onnx")
    pytest.importorskip("onnxruntime")
    from onnx import TensorProto, helper, numpy_helper
    w = np.zeros((5, 3), dtype=np.float32)
    w[4, 0] = 1.0 / 1600.0
    graph = helper.make_graph([helper.make_node("MatMul", ["x", "W"], ["y"])], "g",
                              [helper.make_tensor_value_info("x", TensorProto.FLOAT, [None, 5])],
                              [helper.make_tensor_value_info("y", TensorProto.FLOAT, [None, 3])],
                              [numpy_helper.from_array(w, "W")])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 9
    r = client.post("/models/connect", json={"name": "onnx", "backend": "onnx",
                                            "onnx_base64": base64.b64encode(model.SerializeToString()).decode()})
    assert r.status_code == 201, r.text
    assert r.json()["backend"] == "onnx"


# ----------------------------------------------------------------------------- i18n support, web hosting
def test_vehicle_schema_and_stop_codes(client):
    body = client.get("/vehicle/mid_size_sedan").json()
    keys = {p["key"]: p for p in body["schema"]}
    assert keys["vehicle.mass"]["unit"] == "kg" and keys["vehicle.mass"]["value"] == 1600.0
    assert keys["tires.mu"]["min"] == 0.05
    r = client.post("/simulate", json={"model": "bicycle_linear", "maneuver": "step_steer", "duration": 1.0})
    assert r.json()["stop_code"] == "duration_reached"
    assert len(set(STOP_CODES.values())) == len(STOP_CODES)


def test_web_app_is_served(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "assets" / "a.js").write_text("x")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    c = TestClient(create_app(api_key="k", web_dir=tmp_path, model_dir=tmp_path / "m"))
    assert c.get("/").text == "<html>app</html>"
    assert c.get("/app/simulate").text == "<html>app</html>"
    assert c.get("/assets/a.js").text == "x" and c.get("/favicon.svg").status_code == 200
    assert c.get("/nope/x").status_code == 404
    # the API stays protected and is not shadowed by the single-page app
    assert c.get("/vehicle").status_code == 401 and c.get("/health").json()["status"] == "ok"
