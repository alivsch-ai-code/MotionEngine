import json

from vdsim.knowledge.graph import EDGE_TYPES, NODE_TYPES, KnowledgeGraph, force_layout


def test_node_and_edge_types(graph):
    st = graph.stats()
    for t in NODE_TYPES:
        assert st["node_types"].get(t, 0) > 0, t
    for t in EDGE_TYPES:
        assert st["edge_types"].get(t, 0) > 0, t


def test_frenet_chain(graph):
    fid = graph.resolve("geometry.ReferenceLine.to_frenet")
    assert fid == "function:vdsim.geometry.reference_line.ReferenceLine.to_frenet"
    impl = [e for e in graph.out_edges(fid, "implements") if e.target == "concept:frenet_transformation"]
    assert impl and "A.1" in impl[0].note
    assert any(e.target == "reference:werling2011" for e in graph.out_edges("concept:frenet_transformation", "cites"))
    assert graph.path(fid, "reference:werling2011", directed=True)[-1] == "reference:werling2011"
    assert any(e.target.startswith("document:") for e in graph.out_edges("concept:frenet_transformation", "documented_by"))


def test_queries(graph, kb):
    nb = graph.neighbors("model:tire_model/pacejka")
    assert any(o == "class:vdsim.tire_models.pacejka.PacejkaTire" for _, o, _ in nb)
    sub = graph.concept_subgraph("magic_formula")
    assert "reference:pacejka2012" in sub.nodes and "concept:magic_formula" in sub.nodes
    info = graph.explain("stanley_controller")
    assert info["found"] and "reference:hoffmann2007" in info["reference"]
    md = graph.explain_markdown("stanley_controller", kb.references)
    assert md.startswith("# Wie funktioniert") and "Hoffmann" in md
    assert graph.search("pacejka")
    assert any(e.target == "config:configs/scenarios/iso_doppelspurwechsel_80.json"
               for e in graph.out_edges("component:lateral_controller/stanley", "configured_by"))
    assert any(e.target.startswith("test:") for e in graph.out_edges("module:vdsim.tire_models.pacejka", "tested_by"))


def test_json_roundtrip_and_html(graph):
    again = KnowledgeGraph.from_dict(json.loads(graph.to_json()))
    assert again.stats() == graph.stats()
    page = graph.to_html()
    assert "<script src" not in page and "cdn" not in page.lower() and "graph-data" in page


def test_force_layout_deterministic():
    edges = [(0, 1), (1, 2), (2, 0), (3, 4)]
    a, b = force_layout(5, edges, seed=1), force_layout(5, edges, seed=1)
    assert (a == b).all() and abs(a).max() <= 1.0 + 1e-9
