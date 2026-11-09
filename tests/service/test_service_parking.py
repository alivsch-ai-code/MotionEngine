"""REST endpoint POST /park and the assistant's parking tool."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from vdsim.service.app import create_app  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    return TestClient(create_app(model_dir=tmp_path_factory.mktemp("models")))


def test_park_perpendicular_counter_phase(client):
    r = client.post("/park", json={"kind": "perpendicular", "entry": "reverse", "steering": "counter", "layout": "rwd"})
    assert r.status_code == 200
    j = r.json()
    assert j["success"] and j["path"]["segments"][-1]["direction"] == -1
    assert j["geometry"]["mode"] == "counter" and j["geometry"]["min_radius"] < 4.0
    d = j["driven"]
    assert d["success"] and d["kpis"]["final_position_error"] < 0.15
    assert len(d["t"]) == len(d["x"]) == len(d["psi"]) and max(abs(a) for a in d["delta_r"]) > 0
    # path and drive are returned for the vehicle center; the goal is the spot center
    assert abs(j["path"]["x"][-1] - j["scenario"]["goal"][0]) < 1e-6
    assert any(o["kind"] == "car" for o in j["scenario"]["obstacles"])


def test_park_reports_impossible_spots_and_validates(client):
    j = client.post("/park", json={"kind": "parallel", "gap_length": 4.0}).json()
    assert not j["success"] and "collides" in j["message"] and "path" not in j
    assert client.post("/park", json={"steering": "diagonal"}).status_code == 422
    assert client.post("/park", json={"vehicle": "../x"}).status_code == 422
    assert client.post("/park", json={"time_limit": 100}).status_code == 422


def test_park_traction_depends_on_drive_layout(client):
    body = {"kind": "perpendicular", "entry": "reverse", "mu": 0.2, "slope": 0.1}
    fwd = client.post("/park", json={**body, "layout": "fwd"}).json()
    awd = client.post("/park", json={**body, "layout": "awd"}).json()
    assert not fwd["driven"]["success"] and "traction" in fwd["driven"]["message"]
    assert awd["driven"]["success"]


def test_assistant_parking_tool():
    from test_service_chat import events, make, reply, text_block, tool_block  # same directory (pytest prepend mode)

    http, fake = make([
        reply(tool_block("tu_1", "plan_parking", {"kind": "angled", "entry": "forward", "steering": "rear"})),
        reply(text_block("Parked.")),
    ], __import__("pathlib").Path(__import__("tempfile").mkdtemp()))
    res = {d["name"]: d for e, d in events(http.post("/chat", json={"message": "park"})) if e == "tool_result"}
    view = res["plan_parking"]["view"]
    assert res["plan_parking"]["ok"] and view["kind"] == "parking" and view["success"]
    import json
    sent = json.loads(fake.requests[1]["messages"][2]["content"][0]["content"])
    assert sent["path_found"] and sent["closed_loop"]["parked"] and sent["moves"] >= 1
