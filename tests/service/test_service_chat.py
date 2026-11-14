"""Chat assistant (/chat): tool loop, server-sent events and conversation handling with a scripted client.

No request reaches the Anthropic API: a fake client replays prepared responses and records what the
service sent.
"""

import json
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")
anthropic = pytest.importorskip("anthropic")

from fastapi.testclient import TestClient  # noqa: E402

from vdsim.service.app import create_app  # noqa: E402
from vdsim.service.chat import TOOLS  # noqa: E402


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def tool_block(id_, name, input_):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=input_)


def reply(*blocks, stop=None):
    stop = stop or ("tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn")
    return SimpleNamespace(content=list(blocks), stop_reason=stop, model="claude-opus-5-5")


class FakeStream:
    def __init__(self, message):
        self._message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        if isinstance(self._message, Exception):
            raise self._message
        for block in self._message.content:
            if block.type == "text":
                yield SimpleNamespace(type="text", text=block.text)
            elif block.type == "tool_use":
                yield SimpleNamespace(type="content_block_start", content_block=block)

    def get_final_message(self):
        return self._message


class FakeClient:
    def __init__(self, script):
        self.script = list(script)
        self.requests = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kwargs):
        # copy the history as sent: the service keeps appending to the same list afterwards
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return FakeStream(self.script.pop(0))


def events(response):
    out = []
    for chunk in response.text.split("\n\n"):
        if not chunk.strip():
            continue
        lines = dict(line.split(": ", 1) for line in chunk.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


def make(script, tmp_path):
    client = FakeClient(script)
    app = create_app(api_key="k", model_dir=tmp_path / "models", chat_client=client)
    return TestClient(app, headers={"X-API-Key": "k"}), client


def test_simulation_tool_round_trip(tmp_path):
    http, fake = make([
        reply(text_block("Running it."), tool_block("tu_1", "run_simulation",
                                                    {"maneuver": "iso_double_lane_change", "model": "bicycle_linear",
                                                     "duration": 2.0})),
        reply(text_block("The maximum lateral acceleration is moderate.")),
    ], tmp_path)
    r = http.post("/chat", json={"message": "Simulate a double lane change"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    ev = events(r)
    kinds = [e for e, _ in ev]
    assert kinds[0] == "start" and kinds[-1] == "done"
    assert "tool_use" in kinds and "tool_result" in kinds and kinds.count("text") == 2
    result = next(d for e, d in ev if e == "tool_result")
    assert result["ok"] and result["view"]["kind"] == "simulation" and result["view"]["model"] == "bicycle_linear"
    assert {"t", "x", "y", "ay"} <= set(result["view"]["signals"])

    # second request: the assistant turn as returned, then the tool result as JSON for the model
    sent = fake.requests[1]
    assert sent["model"] == "claude-opus-5-5" and sent["fallbacks"] == "default"
    assert sent["output_config"] == {"effort": "medium"} and sent["tools"] is TOOLS
    assert all(t["eager_input_streaming"] for t in sent["tools"])
    assert sent["messages"][1]["role"] == "assistant"
    tool_result = sent["messages"][2]["content"][0]
    assert tool_result["type"] == "tool_result" and tool_result["tool_use_id"] == "tu_1"
    payload = json.loads(tool_result["content"])
    assert payload["model"] == "bicycle_linear" and any(k["key"] == "max_ay" for k in payload["kpis"])

    # the conversation continues with the full history
    conv_id = ev[0][1]["conversation_id"]
    fake.script.append(reply(text_block("Sure.")))
    http.post("/chat", json={"message": "And at 120 km/h?", "conversation_id": conv_id})
    assert len(fake.requests[2]["messages"]) == 5 and fake.requests[2]["messages"][-1]["content"] == "And at 120 km/h?"


def test_invalid_tool_input_goes_back_as_error(tmp_path):
    http, fake = make([
        reply(tool_block("tu_1", "run_simulation", {"maneuver": "iso_double_lane_change", "speed": 30}),
              tool_block("tu_2", "run_simulation", {"maneuver": "does_not_exist"}),
              tool_block("tu_3", "unknown_tool", {})),
        reply(text_block("Those inputs were wrong.")),
    ], tmp_path)
    ev = events(http.post("/chat", json={"message": "x"}))
    results = [d for e, d in ev if e == "tool_result"]
    assert [r["ok"] for r in results] == [False, False, False]
    assert "speed" in results[0]["error"] and "unknown maneuver" in results[1]["error"]
    sent = fake.requests[1]["messages"][2]["content"]
    assert len(sent) == 3 and all(b["is_error"] for b in sent)  # all results in one message


def test_plan_and_prediction_tools(tmp_path):
    http, _ = make([
        reply(tool_block("tu_1", "plan_trajectory", {"ego": {"vx": 20.0}, "target_speed": 20.0, "target_offset": 3.5,
                                                     "obstacles": [{"id": 1, "x": 60.0, "y": 0.0, "v": 10.0}],
                                                     "cycles": 5}),
              tool_block("tu_2", "predict_objects", {"horizon": 3.0, "objects": [{"id": 7, "x": 0, "y": 0, "v": 10}]}),
              tool_block("tu_3", "get_catalog", {})),
        reply(text_block("Done.")),
    ], tmp_path)
    results = {d["name"]: d for e, d in events(http.post("/chat", json={"message": "x"})) if e == "tool_result"}
    plan = results["plan_trajectory"]
    assert plan["ok"] and plan["view"]["kind"] == "plan" and plan["view"]["valid"]
    assert len(plan["view"]["driven"]["x"]) == 5 and plan["view"]["road"]["x"]
    pred = results["predict_objects"]["view"]["objects"][0]
    assert pred["id"] == 7 and abs(pred["x"][-1] - 30.0) < 1e-6
    assert results["get_catalog"]["ok"]


def test_failed_turn_is_rolled_back(tmp_path):
    request = __import__("httpx2").Request("POST", "https://api.anthropic.com/v1/messages")
    http, fake = make([
        reply(tool_block("tu_1", "get_catalog", {})),
        anthropic.APIConnectionError(request=request),
    ], tmp_path)
    ev = events(http.post("/chat", json={"message": "first"}))
    assert ev[-1][0] == "error" and ev[-1][1]["code"] == "network"
    conv_id = ev[0][1]["conversation_id"]
    # the next message starts from a clean history: no dangling tool call
    fake.script.append(reply(text_block("ok")))
    events(http.post("/chat", json={"message": "second", "conversation_id": conv_id}))
    assert [m["role"] for m in fake.requests[-1]["messages"]] == ["user"]
    assert fake.requests[-1]["messages"][0]["content"] == "second"


def test_refusal_and_truncation_end_the_turn(tmp_path):
    http, _ = make([reply(text_block("..."), stop="refusal")], tmp_path)
    assert events(http.post("/chat", json={"message": "x"}))[-1] == (
        "error", {"code": "refusal", "message": "the model declined this request"})
    http, _ = make([reply(tool_block("tu_1", "get_catalog", {}), stop="max_tokens")], tmp_path)
    assert events(http.post("/chat", json={"message": "x"}))[-1][1]["code"] == "truncated"


def test_tool_limit_turns_tools_off(tmp_path, monkeypatch):
    import vdsim.service.chat as chat

    monkeypatch.setattr(chat, "MAX_TOOL_ROUNDS", 2)
    http, fake = make([reply(tool_block(f"tu_{i}", "get_catalog", {})) for i in range(2)]
                      + [reply(text_block("final"))], tmp_path)
    assert events(http.post("/chat", json={"message": "x"}))[-1][0] == "done"
    assert fake.requests[1]["tool_choice"] == {"type": "auto"} and fake.requests[2]["tool_choice"] == {"type": "none"}
    last = fake.requests[2]["messages"][-1]["content"]
    assert last[-1]["type"] == "text" and "limit" in last[-1]["text"]


def test_chat_requires_key_and_validates(tmp_path):
    http, _ = make([], tmp_path)
    assert TestClient(http.app).post("/chat", json={"message": "x"}).status_code == 401
    assert http.post("/chat", json={"message": ""}).status_code == 422
    assert http.post("/chat", json={"message": "x", "extra": 1}).status_code == 422
    status = http.get("/chat/status").json()
    assert status["available"] and status["model"] == "claude-opus-5-5"
    assert http.delete("/chat/unknown").status_code == 204


def test_chat_rate_limit_per_client(tmp_path, monkeypatch):
    monkeypatch.setenv("MOTIONENGINE_CHAT_RATE", "2")
    http, _ = make([reply(text_block("a")), reply(text_block("b")), reply(text_block("c"))], tmp_path)
    codes = [http.post("/chat", json={"message": "hello"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]                       # the third message is stopped before it reaches the model
    limited = http.post("/chat", json={"message": "hello"})
    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) >= 1
    assert http.post("/chat", json={"message": ""}).status_code == 422      # invalid messages do not count
