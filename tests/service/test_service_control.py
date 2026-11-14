"""Controller lab and conditions of stack runs."""

import math

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from vdsim.service.app import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    return TestClient(create_app(model_dir=tmp_path_factory.mktemp("models")))


def run(client, **body):
    r = client.post("/control/run", json={"controllers": [{"name": "stanley"}], **body})
    assert r.status_code == 200, r.text
    return r.json()


def test_catalog(client):
    cat = client.get("/control/catalog").json()
    assert [c["name"] for c in cat["controllers"]] == ["pure_pursuit", "stanley", "lqr", "mpc", "werling_bilevel"]
    assert all(c["params"] and c["doc"]["summary"] for c in cat["controllers"])
    assert "lane_change" in cat["paths"] and "double_track" in cat["plants"]


def test_controllers_rank_as_expected_on_a_lane_change(client):
    names = ["pure_pursuit", "stanley", "lqr", "werling_bilevel"]
    out = client.post("/control/run", json={"controllers": [{"name": n} for n in names], "path": "lane_change", "speed": 15}).json()
    err = {r["name"]: r["kpis"]["max_e_n"] for r in out["runs"]}
    assert all(r["stable"] for r in out["runs"])
    assert err["werling_bilevel"] < err["lqr"] < err["stanley"] < err["pure_pursuit"] < 0.5
    assert out["path"]["y"][-1] == pytest.approx(3.5, abs=1e-3)          # the reference ends on the new lane
    # the driven path ends there too
    assert all(r["signals"]["y"][-1] == pytest.approx(3.5, abs=0.1) for r in out["runs"])


def test_terms_reproduce_the_control_law(client):
    r = run(client, path="curve_entry", speed=12)["runs"][0]
    t, s = r["terms"], r["signals"]
    assert set(t) >= {"e_front", "heading", "feedback", "feedforward", "damping"}
    k = len(s["t"]) // 2
    law = math.degrees(t["heading"][k] + t["feedback"][k] + t["feedforward"][k] + t["damping"][k])
    assert s["delta_cmd_deg"][k] == pytest.approx(law, abs=1e-6)          # Stanley: sum of the four terms
    # steady curve of radius 60 m: the feedforward carries the steering angle, about atan(L / R)
    wheelbase = run(client, path="straight")["vehicle"]["wheelbase"]
    assert math.degrees(t["feedforward"][-1]) == pytest.approx(math.degrees(math.atan(wheelbase / 60.0)), rel=0.2)
    pp = client.post("/control/run", json={"controllers": [{"name": "pure_pursuit"}], "speed": 15}).json()["runs"][0]
    assert pp["terms"]["lookahead"][0] == pytest.approx(12.0, abs=1e-6)   # L_d = k v


def test_disturbances_and_conditions(client):
    calm = run(client, path="straight", speed=20)["runs"][0]["kpis"]
    assert calm["max_e_n"] < 1e-3
    gust = run(client, path="straight", speed=20, disturbance={"t": 2.0, "duration": 0.5, "fy": 3000.0})["runs"][0]
    assert 0.02 < gust["kpis"]["max_e_n"] < 1.0 and gust["kpis"]["final_e_n"] < 0.02       # pushed off, comes back
    offset = run(client, path="straight", speed=20, lateral_offset=0.5)["runs"][0]
    assert offset["signals"]["e_n"][0] == pytest.approx(0.5, abs=0.02) and offset["kpis"]["final_e_n"] < 0.05
    # a tighter curve than the friction allows: the double-track vehicle cannot follow on ice
    dry = run(client, path="curve_entry", speed=18, plant="double_track")["runs"][0]["kpis"]
    ice = run(client, path="curve_entry", speed=18, plant="double_track", mu=0.2)["runs"][0]
    assert dry["max_e_n"] < 0.5 and (not ice["stable"] or ice["kpis"]["max_e_n"] > 5 * dry["max_e_n"])


def test_parameters_and_validation(client):
    short = run(client, controllers=[{"name": "pure_pursuit", "params": {"lookahead_gain": 0.4}}], path="s_curve")["runs"][0]
    long = run(client, controllers=[{"name": "pure_pursuit", "params": {"lookahead_gain": 1.5}}], path="s_curve")["runs"][0]
    assert short["kpis"]["max_e_n"] < long["kpis"]["max_e_n"]             # a long look-ahead cuts the corner
    assert client.post("/control/run", json={"controllers": [{"name": "nope"}]}).status_code == 422
    assert client.post("/control/run", json={"controllers": [{"name": "stanley"}], "plant": "x"}).status_code == 422
    assert client.post("/control/run", json={"controllers": []}).status_code == 422


def test_friction_reaches_the_stack(client):
    from vdsim import api

    plant = {"plant": {"component": "vehicle_plant/vehicle_model", "params": {"model": "double_track"}}}
    dry = api.run("kreisverkehr", stack=plant, duration=14.0)
    ice = api.run("kreisverkehr", stack=plant, duration=14.0, environment={"friction": {"base": 0.2}})
    assert dry.kpis["max_e_n"] < 0.3 and ice.kpis["max_e_n"] > 1.0
    r = client.post("/workbench/runs", json={"scenario": "einscherer", "duration": 1.0, "friction": 0.5})
    assert r.status_code == 202 and r.json()["request"]["environment"] == {"friction": {"base": 0.5}}
    assert client.post("/workbench/runs", json={"scenario": "einscherer", "friction": 5.0}).status_code == 422
