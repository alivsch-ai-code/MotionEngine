import copy
import json

from vdsim.knowledge.generator import PAGES, generate, init_package_docs, render_all


def test_artifacts_for_every_package_and_determinism(kb, graph, tmp_path):
    out = tmp_path / "gen"
    first = generate(kb, out, graph)
    files = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob("*") if p.is_file()}
    for name, pkg in kb.packages.items():
        for page in PAGES:
            assert f"{name}/{page}.md" in files, (name, page)
        if pkg.components:
            assert any(f.startswith(f"{name}/components/") for f in files), name
    for name in ("README.md", "traceability_matrix.md", "references.md", "references.bib", "report.md",
                 "knowledge_graph.json", "knowledge_graph.html", "_meta.json"):
        assert name in files
    second = generate(kb, out, graph)
    assert second["written"] == [] and len(second["unchanged"]) == len(first["written"])
    again = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob("*") if p.is_file()}
    assert {k: v for k, v in again.items() if k != "_meta.json"} == {k: v for k, v in files.items() if k != "_meta.json"}
    assert generate(kb, out, graph, check=True)["written"] == []
    root = str(kb.root).encode()
    assert all(root not in v for k, v in files.items() if k != "_meta.json")
    assert "generated_at" in json.loads(files["_meta.json"])


def test_render_twice_identical(kb, graph):
    assert render_all(kb, graph) == render_all(kb, graph)


def test_stub_for_undocumented_package(kb, graph):
    files = render_all(kb, graph)
    for name, pkg in kb.packages.items():
        if not pkg.has_meta:
            assert "Automatischer Stub" in files[f"{name}/index.md"]
    assert "Automatischer Stub" not in files["geometry/index.md"]


def test_traceability_pages(kb, graph):
    files = render_all(kb, graph)
    matrix = files["traceability_matrix.md"]
    assert "ReferenceLine.to_frenet" in matrix and "Werling (2011)" in matrix and "magic_formula" in matrix
    page = files["geometry/traceability.md"]
    assert "Frenet-Transformation" in page and "Warum es diese Implementierungen gibt" in page
    assert "(A.1)-(A.8)" in page
    theory = files["tire_models/theory.md"]
    assert "Pacejka (2012, Kap. 4)" in theory and "Verknüpfung der Verfahren" in theory
    comp = files["controllers/components/lateral_controller__stanley.md"]
    assert "Hoffmann et al. (2007)" in comp and "`gain`" in comp


def test_init_package_docs(kb, tmp_path):
    kb2 = copy.copy(kb)
    kb2.root = tmp_path
    written = init_package_docs(kb2, "core")
    assert len(written) == 2 and all(p.exists() for p in written)
    assert "{#iso8855_conventions}" in written[1].read_text(encoding="utf-8")
