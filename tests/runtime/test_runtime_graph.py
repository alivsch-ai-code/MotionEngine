"""Graph model: validation (German messages), execution order, editing API, JSON, version pinning."""

import json

import pytest

from vdsim.framework.component import Component, Port
from vdsim.framework.plugins import component, unregister
from vdsim.runtime import Graph, GraphError, GraphValidationError


@component
class _FeedbackSum(Component):
    # y = u + previous value of fb (feedback port breaks the loop)
    KIND, NAME, VERSION = "rt_test", "feedback_sum", "1.0.0"
    INPUTS = {"u": Port("float"), "fb": Port("float", optional=True, feedback=True)}
    OUTPUTS = {"y": Port("float")}

    def step(self, t, inputs):
        return {"y": (inputs["u"] or 0.0) + (inputs["fb"] or 0.0)}


@component
class _Versioned(Component):
    KIND, NAME, VERSION = "rt_test", "versioned", "1.0.0"
    OUTPUTS = {"y": Port("float")}

    def step(self, t, inputs):
        return {"y": 1.0}


def _chain():
    g = Graph("chain", base_dt=0.01)
    g.add_node("c", "node/constant", params={"value": 2.0})
    g.add_node("k", "node/gain", params={"k": 3.0})
    g.add_node("s", "node/scope")
    g.connect("c.y", "k.u")
    g.connect("k.y", "s.u1")
    return g


def test_valid_graph_and_order():
    g = _chain()
    rep = g.validate()
    assert rep.ok and not rep.issues
    assert g.execution_order() == ["c", "k", "s"]


def test_type_mismatch_is_rejected_and_reported():
    g = Graph()
    g.add_node("ego", "node/typed_default", params={"type_name": "EgoState"})
    g.add_node("k", "node/gain")
    with pytest.raises(GraphError, match="Typkonflikt: ego.y liefert 'EgoState', k.u erwartet 'float'"):
        g.connect("ego.y", "k.u")
    g.connect("ego.y", "k.u", check=False)
    rep = g.validate()
    assert "type_mismatch" in rep.codes()
    assert not rep.ok


def test_unconnected_input_unknown_port_and_multiple_drivers():
    g = Graph()
    g.add_node("a", "node/constant")
    g.add_node("b", "node/constant")
    g.add_node("k", "node/gain")
    rep = g.validate()
    assert any(i.code == "unconnected_input" and "Pflichteingang k.u" in i.message for i in rep)
    with pytest.raises(GraphError, match="keinen Eingang 'x'"):
        g.connect("a.y", "k.x")
    with pytest.raises(GraphError, match="keinen Ausgang 'u'.*das ist ein Eingang"):
        g.connect("k.u", "a.y")
    g.connect("a.y", "k.u")
    with pytest.raises(GraphError, match="bereits mit a.y verbunden"):
        g.connect("b.y", "k.u")
    g.connections.append(type(g.connections[0])("b.y", "k.u"))     # e.g. hand-edited JSON
    rep = g.validate()
    assert any(i.code == "multiple_drivers" and "mehrfach belegt" in i.message for i in rep)
    g.disconnect(src="b.y")
    assert g.validate().ok


def test_algebraic_loop_detected():
    g = Graph()
    g.add_node("a", "node/gain")
    g.add_node("b", "node/gain")
    g.connect("a.y", "b.u")
    g.connect("b.y", "a.u")
    rep = g.validate()
    loops = [i for i in rep if i.code == "algebraic_loop"]
    assert len(loops) == 1 and "Algebraische Schleife" in loops[0].message and set(loops[0].nodes) == {"a", "b"}
    with pytest.raises(GraphValidationError):
        g.execution_order()


def test_loop_through_unit_delay_or_feedback_port_is_allowed():
    g = Graph()
    g.add_node("a", "node/gain")
    g.add_node("d", "node/unit_delay")
    g.connect("a.y", "d.u")
    g.connect("d.y", "a.u")
    assert g.validate().ok
    assert g.execution_plan() == {"output": ["d"], "step": ["a"], "update": ["d"]}

    g2 = Graph()
    g2.add_node("c", "node/constant")
    g2.add_node("s", "rt_test/feedback_sum")
    g2.add_node("k", "node/gain")
    g2.connect("c.y", "s.u")
    g2.connect("s.y", "k.u")
    g2.connect("k.y", "s.fb")         # loop closed via the feedback port
    assert g2.validate().ok
    assert g2.execution_order() == ["c", "s", "k"]


def test_self_loop_detected():
    g = Graph()
    g.add_node("p", "node/product")
    g.add_node("c", "node/constant")
    g.connect("c.y", "p.u1")
    g.connect("p.y", "p.u2")
    assert "algebraic_loop" in g.validate().codes()


def test_unknown_component_version_and_parameter():
    g = Graph()
    with pytest.raises(GraphError, match="unbekannte Komponente 'foo/bar'"):
        g.add_node("x", "foo/bar")
    with pytest.raises(GraphError, match="keine Version von 'node/gain' passt zu '\\^2'"):
        g.add_node("x", "node/gain@^2")
    with pytest.raises(GraphError, match="ungültiger Parameter"):
        g.add_node("x", "node/gain", params={"kk": 1.0})
    g2 = Graph.from_dict({"nodes": [{"id": "x", "component": "foo/bar"}], "connections": []})
    rep = g2.validate()
    assert rep.errors[0].code == "component_unknown"


def test_period_must_be_multiple_of_base_dt():
    g = _chain()
    g.set_period("k", 0.015)
    rep = g.validate()
    assert any(i.code == "period" and "kein ganzzahliges Vielfaches" in i.message for i in rep)
    g.set_period("k", 0.03)
    assert g.validate().ok and g.period_ticks("k") == 3


def test_editing_api_and_dynamic_ports():
    g = _chain()
    events = []
    g.on_change(lambda ev, info: events.append(ev))
    rev = g.revision
    g.set_param("k", "k", 5)
    assert g.get_param("k", "k") == 5.0 and g.revision == rev           # parameter change is not structural
    g.add_node("sum", "node/sum", params={"signs": "++"})
    assert list(g.ports("sum")[0]) == ["u1", "u2"]
    g.set_param("sum", "signs", "+-+")
    assert list(g.ports("sum")[0]) == ["u1", "u2", "u3"] and g.revision > rev
    g.rename_node("k", "gain")
    assert any(c.src == "gain.y" for c in g.connections)
    g.add_group("grp", ["c", "gain"], "Quelle")
    assert g.group_of("gain") == "grp"
    g.remove_node("c")
    assert all("c" not in (c.src_node, c.dst_node) for c in g.connections)
    assert g.metadata["groups"]["grp"]["nodes"] == ["gain"]
    g.replace_component("gain", "node/saturation")
    assert g.node("gain").component == "node/saturation"
    assert {"add_node", "param", "rename_node", "remove_node", "replace_component"} <= set(events)


def test_json_roundtrip_and_contract_format(tmp_path):
    g = _chain()
    g.set_period("k", 0.02)
    g.move_node("k", (100, 50))
    path = g.save(tmp_path / "chain.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert set(data) == {"format_version", "name", "base_dt", "nodes", "connections", "metadata"}
    assert data["nodes"][1] == {"id": "k", "component": "node/gain", "params": {"k": 3.0}, "period": 0.02,
                                "position": [100.0, 50.0], "version": "1.0.0"}
    assert data["connections"][0] == {"from": "c.y", "to": "k.u"}
    g2 = Graph.load(path)
    assert g2.to_dict() == g.to_dict()
    assert g2.validate().ok


def test_version_pinning_warning():
    data = {"name": "v", "base_dt": 0.01, "nodes": [{"id": "a", "component": "rt_test/versioned@^1",
                                                      "version": "1.0.0"}], "connections": []}
    assert Graph.from_dict(data).validate().ok

    @component
    class _V2(_Versioned):
        VERSION = "1.1.0"
    try:
        g = Graph.from_dict(data)
        assert g.node("a").instance.VERSION == "1.0.0"               # pinned version is used
        rep = g.validate()
        assert rep.ok and any(i.code == "version_mismatch" and "1.1.0" in i.message for i in rep)
        data2 = dict(data, nodes=[dict(data["nodes"][0], version="0.9.0")])
        rep2 = Graph.from_dict(data2).validate()
        assert any(i.code == "version_mismatch" and "0.9.0" in i.message for i in rep2)
        g.pin_versions()
        assert g.node("a").component == "rt_test/versioned@1.0.0"
    finally:
        unregister("rt_test", "versioned", "1.1.0")


def test_validation_report_iterable_for_api():
    g = Graph()
    g.add_node("k", "node/gain")
    texts = [str(i) for i in g.validate()]
    assert texts and texts[0].startswith("Fehler: Pflichteingang")
