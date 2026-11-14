"""REST service (vdsim.service): contract, security, limits and physical consistency of the responses."""

import math

import numpy as np
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from vdsim.analysis import LinearSingleTrackAnalysis  # noqa: E402
from vdsim.core.parameters import load_vehicle_preset  # noqa: E402
from vdsim.service.app import _decimate_index, _Limiter, create_app  # noqa: E402
from vdsim.service.metrics import Metrics  # noqa: E402

KEY = {"X-API-Key": "test-key"}


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(api_key="test-key", max_concurrency=4, max_sim_time=30.0))


@pytest.fixture(scope="module")
def open_client():
    return TestClient(create_app(api_key=""))


# ----------------------------------------------------------------------------- service
def test_health_is_public_and_versioned(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["version"] and body["uptime_s"] >= 0


@pytest.mark.parametrize("path", ["/vehicle", "/metrics", "/trajectory/maneuvers", "/vehicle/mid_size_sedan"])
def test_api_key_required(client, path):
    assert client.get(path).status_code == 401
    assert client.get(path, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get(path, headers=KEY).status_code == 200


def test_no_key_configured_means_open(open_client):
    assert open_client.get("/vehicle").status_code == 200


def test_openapi_lists_all_endpoints(client):
    spec = client.get("/openapi.json").json()
    assert spec["openapi"].startswith("3.")
    for path in ("/simulate", "/plan", "/predict", "/vehicle", "/trajectory", "/health", "/metrics"):
        assert path in spec["paths"], path
    assert client.get("/docs").status_code == 200


def test_metrics_prometheus_format(client):
    client.get("/health")
    text = client.get("/metrics", headers=KEY).text
    assert "# TYPE motionengine_requests_total counter" in text
    assert 'motionengine_requests_total{method="GET",route="/health",status="200"}' in text
    assert 'motionengine_request_duration_seconds_bucket{route="/health",le="+Inf"}' in text


def test_metrics_histogram_is_cumulative():
    m = Metrics()
    for s in (0.001, 0.02, 0.3, 100.0):
        m.observe("GET", "/x", 200, s)
    buckets = m.latency_buckets["/x"]
    assert buckets == sorted(buckets) and buckets[-1] == 3 and m.latency_count["/x"] == 4
    m.reject()
    assert "motionengine_requests_rejected_total 1" in m.render()


def test_limiter_rejects_when_full():
    m = Metrics()
    lim = _Limiter(1, m)
    with lim.slot():
        with pytest.raises(HTTPException) as err:
            with lim.slot():
                pass
        assert err.value.status_code == 503
    with lim.slot():  # released again
        pass
    assert m.rejected == 1


def test_decimation_keeps_endpoints():
    idx = _decimate_index(1000, 7)
    assert idx[0] == 0 and idx[-1] == 999 and len(idx) <= 7
    assert np.array_equal(_decimate_index(5, 10), np.arange(5))


def test_cors_and_env_configuration(monkeypatch):
    monkeypatch.setenv("MOTIONENGINE_API_KEY", "env-key")
    monkeypatch.setenv("MOTIONENGINE_MAX_SIM_TIME", "not-a-number")
    app = create_app(cors_origins=["https://example.org"])
    assert app.state.limits["max_sim_time"] == 120.0
    c = TestClient(app)
    assert c.get("/vehicle").status_code == 401
    assert c.get("/vehicle", headers={"X-API-Key": "env-key"}).status_code == 200
    r = c.options("/vehicle", headers={"Origin": "https://example.org", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "https://example.org"


# ----------------------------------------------------------------------------- vehicle
def test_vehicle_catalog(client):
    body = client.get("/vehicle", headers=KEY).json()
    assert "mid_size_sedan" in body["presets"]
    assert {"bicycle_linear", "double_track", "multibody"} <= set(body["vehicle_models"])
    assert "pacejka" in body["tire_models"] and "stanley" in body["lateral_controllers"]


def test_vehicle_analysis_matches_library(client):
    body = client.get("/vehicle/mid_size_sedan", headers=KEY).json()
    lin = LinearSingleTrackAnalysis(load_vehicle_preset("mid_size_sedan"))
    a = body["analysis"]
    assert a["understeer_gradient"] == pytest.approx(lin.understeer_gradient)
    assert a["characteristic_speed"] == pytest.approx(lin.characteristic_speed)
    assert a["critical_speed"] is None  # understeering vehicle
    assert body["parameters"]["vehicle"]["mass"] > 0
    for row in a["per_speed"]:
        assert row["yaw_gain"] == pytest.approx(lin.steady_state_gains(row["speed"])["yaw_rate"])


@pytest.mark.parametrize("name", ["does_not_exist", "..%2F..%2Fpyproject", "mid_size_sedan.json"])
def test_vehicle_rejects_unknown_and_paths(client, name):
    assert client.get(f"/vehicle/{name}", headers=KEY).status_code in (404, 422)


# ----------------------------------------------------------------------------- trajectory
def test_trajectory_generation(client):
    r = client.post("/trajectory", json={"maneuver": "straight", "params": {"length": 100, "speed_kmh": 36},
                                         "max_points": 11}, headers=KEY)
    assert r.status_code == 200
    body = r.json()
    assert body["n_points"] <= 11 and body["length"] == pytest.approx(100.0, abs=0.5)
    assert np.allclose(body["v"], 10.0) and np.allclose(body["y"], 0.0, atol=1e-6)
    assert np.all(np.diff(body["s"]) > 0)


def test_trajectory_errors(client):
    assert client.post("/trajectory", json={"maneuver": "nope"}, headers=KEY).status_code == 422
    r = client.post("/trajectory", json={"maneuver": "straight", "params": {"bogus": 1}}, headers=KEY)
    assert r.status_code == 422
    assert client.post("/trajectory", json={"maneuver": "straight", "extra": 1}, headers=KEY).status_code == 422
    assert "step_steer" in client.get("/trajectory/maneuvers", headers=KEY).json()


# ----------------------------------------------------------------------------- simulate
def test_simulate_step_steer_matches_linear_theory(client):
    # steady-state yaw-rate gain of the linear single-track model through the full API path
    r = client.post("/simulate", headers=KEY, json={
        "model": "bicycle_linear", "maneuver": "step_steer",
        "maneuver_params": {"speed_kmh": 80, "steering_wheel_deg": 15}, "duration": 6.0,
        "signals": ["t", "r", "delta_f", "fz"], "max_points": 20000})
    assert r.status_code == 200, r.text
    body = r.json()
    t, yaw, delta = (np.array(body["signals"][k], dtype=float) for k in ("t", "r", "delta_f"))
    tail = t > t[-1] - 1.0
    gain = LinearSingleTrackAnalysis(load_vehicle_preset("mid_size_sedan")).steady_state_gains(80 / 3.6)["yaw_rate"]
    assert np.mean(yaw[tail]) / np.mean(delta[tail]) == pytest.approx(gain, rel=1e-3)
    assert len(body["signals"]["fz"][0]) == 4  # per-wheel signals keep their shape
    assert {k["key"] for k in body["kpis"]} >= {"max_ay"}
    assert body["simulated_time"] == pytest.approx(6.0, abs=0.02)


def test_simulate_caps_duration_and_preset(client):
    r = client.post("/simulate", headers=KEY, json={"scenario": "lenkwinkelsprung_80", "model": "bicycle_linear",
                                                    "duration": 1000.0, "max_points": 3, "signals": ["t"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["simulated_time"] <= 30.0 + 0.02 and len(body["signals"]["t"]) <= 3


@pytest.mark.parametrize("payload", [
    {"model": "warp_drive"},
    {"maneuver": "teleport"},
    {"vehicle": "../../etc/passwd"},
    {"lateral_controller": "nope"},
    {"longitudinal_controller": "nope"},
    {"scenario": "unknown_scenario"},
    {"vehicle_overrides": {"mass": 1.0}},
    {"vehicle_overrides": {"vehicle.does_not_exist": 1.0}},
    {"dt_control": 5.0},
    {"solver": "magic"},
])
def test_simulate_rejects_invalid(client, payload):
    assert client.post("/simulate", headers=KEY, json=payload).status_code == 422


def test_simulate_head_wind_increases_drag(client):
    def mean_ax(wind):
        r = client.post("/simulate", headers=KEY, json={
            "model": "bicycle_linear", "maneuver": "straight", "maneuver_params": {"length": 300, "speed_kmh": 100},
            "longitudinal_controller": "speed_pi", "longitudinal_params": {"kp": 0.0, "ki": 0.0, "a_max": 0.0,
                                                                            "a_min": 0.0},
            "environment": {"wind_speed": wind}, "duration": 2.0, "signals": ["ax"]})
        assert r.status_code == 200, r.text
        return float(np.mean(r.json()["signals"]["ax"]))
    assert mean_ax(10.0) < mean_ax(0.0) < mean_ax(-10.0) < 0.0


# ----------------------------------------------------------------------------- predict
def test_predict_constant_velocity_and_ctrv(client):
    objs = [{"id": 1, "x": 0, "y": 0, "psi": 0.0, "v": 10.0, "yaw_rate": 0.2}]
    cv = client.post("/predict", headers=KEY, json={"predictor": "constant_velocity", "horizon": 2.0, "dt": 0.5,
                                                    "objects": objs}).json()["objects"][0]
    assert cv["t"] == pytest.approx([0, 0.5, 1, 1.5, 2]) and cv["x"][-1] == pytest.approx(20.0)
    ct = client.post("/predict", headers=KEY, json={"predictor": "ctrv", "horizon": 2.0, "dt": 0.5,
                                                    "objects": objs}).json()["objects"][0]
    # CTRV: constant speed on a circle of radius v / r
    x, y = np.array(ct["x"]), np.array(ct["y"])
    radius = 10.0 / 0.2
    assert np.allclose(np.hypot(x, y - radius), radius, atol=1e-9)
    assert ct["psi"][-1] == pytest.approx(0.4)


def test_predict_constant_acceleration_stops(client):
    objs = [{"id": 5, "v": 10.0, "a": -5.0}]
    o = client.post("/predict", headers=KEY, json={"predictor": "constant_acceleration", "horizon": 4.0,
                                                   "objects": objs}).json()["objects"][0]
    assert o["x"][-1] == pytest.approx(10.0) and o["v"][-1] == 0.0 and min(o["v"]) >= 0.0


def test_predict_validation(client):
    assert client.post("/predict", headers=KEY, json={"objects": [{"v": -1}]}).status_code == 422
    assert client.post("/predict", headers=KEY, json={"horizon": 100}).status_code == 422
    body = client.post("/predict", headers=KEY, json={}).json()
    assert body["objects"] == []


# ----------------------------------------------------------------------------- plan
def test_plan_lane_change(client):
    r = client.post("/plan", headers=KEY, json={"target_offset": 3.5, "target_speed": 20.0,
                                                "ego": {"vx": 20.0}, "cycles": 1, "max_points": 5000})
    assert r.status_code == 200, r.text
    body = r.json()
    tr = body["trajectory"]
    assert tr["valid"] and not body["fallback"] and body["n_candidates"] > 0
    assert tr["y"][0] == pytest.approx(0.0, abs=1e-6) and tr["y"][-1] == pytest.approx(3.5, abs=0.05)
    # planned lateral acceleration v^2 kappa stays physically plausible
    ay = np.array(tr["v"]) ** 2 * np.array(tr["kappa"])
    assert np.max(np.abs(ay)) < 4.0


def test_plan_stops_before_stop_line_and_avoids_obstacle(client):
    # Werling replacement strategy: the stopping mode takes over once it decelerates more than velocity keeping
    r = client.post("/plan", headers=KEY, json={"stop_at": 60.0, "target_speed": 10.0, "ego": {"vx": 10.0},
                                                "cycles": 200})
    assert r.status_code == 200, r.text
    cycles = r.json()["cycles"]
    assert cycles[-1]["v"] == pytest.approx(0.0, abs=1e-3)
    # speed_range tolerates -0.05 m/s overshoot of the quintic stopping polynomial (no reversal)
    assert max(c["x"] for c in cycles) < 60.0 and all(c["v"] >= -0.05 for c in cycles)

    # slow vehicle ahead in the own lane, free target lane on the left: the plan must not hit it
    obstacle = {"id": 9, "x": 40.0, "y": 0.0, "v": 2.0}
    r = client.post("/plan", headers=KEY, json={"target_speed": 15.0, "ego": {"vx": 15.0}, "obstacles": [obstacle],
                                                "cycles": 30})
    assert r.status_code == 200, r.text
    cycles = r.json()["cycles"]
    assert len(cycles) == 30
    for c in cycles:
        ox = 40.0 + 2.0 * c["t"]
        assert ox - c["x"] > 4.5 or abs(c["y"]) > 1.8


def test_plan_curved_road_and_validation(client):
    road = [{"kind": "straight", "length": 30}, {"kind": "arc", "length": 200, "curvature": 1 / 150}]
    r = client.post("/plan", headers=KEY, json={"road": road, "target_speed": 15.0, "ego": {"vx": 15.0}})
    assert r.status_code == 200
    tr = r.json()["trajectory"]
    assert math.isfinite(tr["cost"]) and tr["theta"][-1] > 0.0  # turns left
    assert client.post("/plan", headers=KEY, json={"config": "../x"}).status_code == 422
    assert client.post("/plan", headers=KEY, json={"road": []}).status_code == 422


def test_require_returns_catalog_string_not_client_input():
    from vdsim.service.app import _require
    allowed = ["mid_size_sedan", "suv"]
    assert _require("suv", allowed, "preset") is allowed[1]
    for bad in ("../suv", "suv.json", "/etc/passwd", "SUV", ""):
        with pytest.raises(HTTPException):
            _require(bad, allowed, "preset")


WAYPOINTS = {"waypoints": [{"x": 0, "y": 0, "v_kmh": 50}, {"x": 80, "y": 0, "v_kmh": 50, "radius": 20},
                           {"x": 120, "y": 40, "v_kmh": 40, "radius": 15}, {"x": 80, "y": 90, "v_kmh": 40}],
             "ay_max": 4.0}


def test_waypoint_trajectory_and_simulation(client):
    r = client.post("/trajectory/waypoints", json=WAYPOINTS, headers=KEY)
    assert r.status_code == 200
    traj = r.json()
    # two legs of 80 m and 56.6 m plus 64 m, shortened by the two fillets
    assert 180.0 < traj["length"] < 80.0 + 56.6 + 64.1
    assert max(abs(k) for k in traj["kappa"]) == pytest.approx(1 / 15, rel=0.2)       # tightest fillet
    v, kappa = np.array(traj["v"]), np.array(traj["kappa"])
    assert np.max(v**2 * np.abs(kappa)) <= 4.0 * 1.15                                  # ay_max limits the speed
    assert client.post("/trajectory/waypoints", json={"waypoints": WAYPOINTS["waypoints"][:1]},
                       headers=KEY).status_code == 422

    sampled = client.post("/trajectory/waypoints/from-maneuver", json={"maneuver": "iso_double_lane_change",
                                                                       "n_points": 12}, headers=KEY).json()
    assert len(sampled["waypoints"]) == 12 and sampled["waypoints"][0]["v_kmh"] == pytest.approx(80.0)
    assert client.post("/trajectory/waypoints/from-maneuver", json={"maneuver": "step_steer"},
                       headers=KEY).status_code == 422

    sim = client.post("/simulate", json={"waypoints": WAYPOINTS}, headers=KEY).json()
    assert sim["name"] == "waypoints" and sim["stop_code"] == "end_of_trajectory" and sim["run_id"]
    assert sim["signals"]["x"][-1] == pytest.approx(80.0, abs=2.0) and sim["signals"]["y"][-1] == pytest.approx(90.0, abs=2.0)
    assert max(abs(e) for e in sim["signals"]["lateral_error"]) < 0.5


def test_simulation_report(client):
    ids = [client.post("/simulate", json={"maneuver": "step_steer", "duration": 2.0, "initial_speed": v},
                       headers=KEY).json()["run_id"] for v in (20.0, 25.0)]
    pdf = client.post("/simulate/report", json={"run_ids": ids, "title": "Test"}, headers=KEY)
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:5] == b"%PDF-" and len(pdf.content) > 50_000
    summary = client.post("/simulate/report", json={"run_ids": ids[:1], "format": "summary"}, headers=KEY)
    assert summary.status_code == 200 and summary.text.startswith("# Engineering Summary")
    assert client.post("/simulate/report", json={"run_ids": ["missing"]}, headers=KEY).status_code == 404
