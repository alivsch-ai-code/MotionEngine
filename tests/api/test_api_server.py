import json
import threading
import urllib.request

import pytest

from vdsim.api.server import openapi_spec, serve


@pytest.fixture
def server():
    httpd, store = serve(port=0, token="secret")
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}/api/v1"
    httpd.shutdown()
    httpd.server_close()


def _get(url, token="secret"):
    req = urllib.request.Request(url, headers={"X-API-Key": token} if token else {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, json.loads(resp.read())


def test_auth_info_and_openapi(server):
    with pytest.raises(urllib.error.HTTPError) as err:
        _get(f"{server}/info", token=None)
    assert err.value.code == 401
    status, info = _get(f"{server}/info")
    assert status == 200 and info["name"] == "vdsim"
    status, spec = _get(f"{server}/openapi.json")
    assert spec["openapi"] == "3.1.0" and "/runs" in spec["paths"]
    assert set(openapi_spec()["paths"]) == set(spec["paths"])


def test_components_and_graph_build(server):
    status, comps = _get(f"{server}/components")
    assert status == 200 and isinstance(comps, list)
    req = urllib.request.Request(f"{server}/graphs/build", data=json.dumps({"stack": {}}).encode(),
                                 headers={"X-API-Key": "secret", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        graph = json.loads(resp.read())
    assert [n["id"] for n in graph["nodes"]][:3] == ["world", "perception", "prediction"]
    assert {"from": "controller.status", "to": "planner.status"} in graph["connections"]
