import copy
import shutil

import pytest

from vdsim.knowledge.references import ReferenceDB


@pytest.fixture(scope="module")
def qapp():
    from PySide6 import QtWidgets
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_browser_smoke(qapp, kb, graph, tmp_path):
    from vdsim.gui.knowledge import KnowledgeBrowser
    refs = tmp_path / "refs"
    shutil.copytree(kb.root / "docs" / "references", refs)
    kb2 = copy.copy(kb)
    kb2.references = ReferenceDB(refs)
    browser = KnowledgeBrowser(knowledge=kb2, graph=graph)
    assert browser.tree.topLevelItemCount() > 10

    browser.navigate("concept:frenet_transformation")
    text = browser.doc.toPlainText()
    assert "Frenet" in text and "Herleitung" not in text            # expert content hidden
    browser.expert.setChecked(True)
    assert "Herleitung" in browser.doc.toPlainText()
    assert browser.graph_view.items_by_id                             # graph tab follows the selection

    browser.navigate("page:geometry/traceability")
    assert "to_frenet" in browser.doc.toPlainText()
    browser.navigate("geometry.ReferenceLine.to_frenet")
    assert browser.current == ("node", "function:vdsim.geometry.reference_line.ReferenceLine.to_frenet")
    browser.back()
    assert browser.current[0] == "page"

    browser.search.setText("pacejka")
    assert browser.results.count() > 0
    assert browser.trace_table.rowCount() == len(kb.traces)
    browser.graph_mode.setCurrentIndex(2)
    assert browser.graph_view.items_by_id

    ref = browser.add_reference("testref2026", {"type": "book", "authors": ["Erika Muster"], "title": "Testbuch",
                                                "year": 2026, "publisher": "Verlag"},
                                target="component:lateral_controller/stanley")
    assert ref.short() == "Muster (2026)"
    assert (refs / "user.yaml").exists() and "testref2026" in (refs / "links.yaml").read_text(encoding="utf-8")
    assert any(e.target == "reference:testref2026"
               for e in browser.graph.out_edges("component:lateral_controller/stanley", "cites"))
    assert "testref2026" in kb2.references and "testref2026" not in kb.references
