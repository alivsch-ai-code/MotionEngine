"""Versioning: snapshots in .history, structured/text diff, restore, optional git commit."""

import json
import shutil
import subprocess

import pytest

from vdsim.runtime import Graph, VersionStore, diff_graphs


def _graph():
    g = Graph("v", base_dt=0.01)
    g.add_node("c", "node/constant", params={"value": 1.0})
    g.add_node("k", "node/gain", params={"k": 2.0})
    g.connect("c.y", "k.u")
    return g


def test_snapshot_diff_restore(tmp_path):
    path = tmp_path / "graph.json"
    store = VersionStore(path, git=False)
    g = _graph()
    v1 = store.snapshot(g, "Ausgangsstand")
    assert v1.id == "v0001" and v1.parent is None and path.exists()
    assert (tmp_path / ".history" / "graph" / "index.json").exists()
    assert store.snapshot(g, "unverändert").id == "v0001"           # same content -> no new version

    g.set_param("k", "k", 5.0)
    g.add_node("s", "node/scope")
    g.connect("k.y", "s.u1")
    g.set_period("c", 0.1)
    v2 = store.snapshot(g, "Verstärkung erhöht, Scope")
    assert v2.id == "v0002" and v2.parent == "v0001" and v2.hash != v1.hash
    assert [v.id for v in store.list()] == ["v0001", "v0002"] and store.head.id == "v0002"

    d = store.diff("v0001", "v0002")
    assert [n["id"] for n in d.added_nodes] == ["s"]
    assert d.changed_nodes["k"]["params.k"] == (2.0, 5.0)
    assert d.changed_nodes["c"]["period"] == (None, 0.1)
    assert d.added_connections == [("k.y", "s.u1")] and not d.removed_connections
    text = d.text()
    assert "+ Knoten s (node/scope)" in text and "~ Knoten k: params.k: 2.0 → 5.0" in text
    assert "+ Verbindung k.y → s.u1" in text

    doc, v3 = store.restore("v0001")
    assert v3.id == "v0003" and v3.parent == "v0002" and v3.hash == v1.hash
    restored = Graph.load(path)
    assert restored.get_param("k", "k") == 2.0 and "s" not in restored.nodes
    assert store.diff("v0001").empty and "Keine Unterschiede" in store.diff("v0001", "v0003").text()
    assert "Wiederhergestellt aus v0001" in store.log()


def test_component_configuration_diff(tmp_path):
    store = VersionStore(tmp_path / "planner_params.json", git=False)
    store.snapshot({"k_jerk": 1.0, "sampling": {"d_step": 0.5}}, "a")
    store.snapshot({"k_jerk": 2.0, "sampling": {"d_step": 0.5, "t_max": 8}}, "b")
    d = store.diff("v0001", "v0002")
    assert d.changes["k_jerk"] == (1.0, 2.0) and "sampling.t_max" in d.changes
    assert "~ k_jerk: 1.0 → 2.0" in d.text()


def test_diff_graphs_direct():
    a = _graph()
    b = _graph()
    b.remove_node("k")
    d = diff_graphs(a, b)
    assert [n["id"] for n in d.removed_nodes] == ["k"] and d.removed_connections == [("c.y", "k.u")]


@pytest.mark.skipif(shutil.which("git") is None, reason="git nicht installiert")
def test_git_commit_in_temporary_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, check=True)  # noqa: E731
    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "vdsim test")
    store = VersionStore(repo / "graphs" / "stack.json")          # git="auto"
    v = store.snapshot(_graph(), "erster Stand")
    assert v.git_commit and len(v.git_commit) == 40
    log = run("log", "--oneline").stdout
    assert "stack.json v0001: erster Stand" in log
    files = run("show", "--name-only", "--format=", "HEAD").stdout
    assert "graphs/stack.json" in files and "graphs/.history/stack/index.json" in files
    json.loads((repo / "graphs" / "stack.json").read_text(encoding="utf-8"))
