from pathlib import Path

import pytest
import yaml

from vdsim.knowledge.references import ReferenceDB, parse_citations

OWN_PACKAGES = ["core", "tire_models", "vehicle_models", "powertrain", "actuators", "controllers", "trajectory",
                "simulation", "analysis", "reporting", "visualization", "gui", "framework", "geometry", "lane_change",
                "knowledge"]


def _write(path, data):
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def refdir(tmp_path):
    _write(tmp_path / "a.yaml", {
        "werling2011": {"type": "thesis", "authors": ["Moritz Werling"], "title": "Ein neues Konzept", "year": 2011,
                        "publisher": "KIT Scientific Publishing"},
        "mw2014": {"type": "book", "authors": ["Manfred Mitschke", "Henning Wallentowitz"], "title": "Dynamik",
                   "year": 2014, "publisher": "Springer Vieweg"},
        "s2018": {"type": "book", "authors": ["Dieter Schramm", "Manfred Hiller", "Roberto Bardini"],
                  "title": "Modellbildung & Simulation", "year": 2018, "publisher": "Springer"}})
    _write(tmp_path / "b.yaml", {
        "werling2011": {"type": "paper", "title": "dup", "authors": ["X"], "year": 2000, "venue": "Y"},
        "broken": {"type": "paper", "title": "ohne Autoren"},
        "badtype": {"type": "blog", "title": "x"},
        "iso8855": {"type": "norm", "number": "ISO 8855:2011", "title": "Vocabulary", "year": 2011},
        "conf": {"type": "paper", "authors": ["A B"], "title": "T", "year": 2010, "venue": "IEEE Conference X"}})
    (tmp_path / "c.yaml").write_text("x: [unclosed", encoding="utf-8")
    return tmp_path


def test_merge_validation_and_duplicates(refdir):
    db = ReferenceDB(refdir)
    assert {"werling2011", "mw2014", "s2018", "iso8855", "conf"} <= set(db.refs)
    assert db["werling2011"].type == "thesis"                     # first definition wins
    messages = " ".join(str(i) for i in db.issues)
    assert "doppelte ID" in messages and "Pflichtfeld fehlt" in messages and "unbekannter Typ" in messages
    assert "YAML nicht lesbar" in messages                       # broken file -> issue, no exception


def test_german_citations(refdir):
    db = ReferenceDB(refdir)
    assert db.cite("werling2011") == "Werling (2011)"
    assert db.cite("werling2011", "Abschn. 3.4") == "Werling (2011, Abschn. 3.4)"
    assert db.cite("mw2014") == "Mitschke und Wallentowitz (2014)"
    assert db.cite("s2018") == "Schramm et al. (2018)"
    assert db.cite("iso8855") == "ISO 8855:2011 (2011)"
    assert "Werling, M. (2011)" in db.cite("werling2011", style="full")
    assert db.cite("missing") == "[missing?]"


def test_bibtex_export(refdir):
    db = ReferenceDB(refdir)
    bib = db.bibtex()
    assert "@phdthesis{werling2011," in bib and "@book{mw2014," in bib and "@inproceedings{conf," in bib
    assert "author = {Manfred Mitschke and Henning Wallentowitz}" in bib
    assert r"Modellbildung \& Simulation" in bib


def test_search_and_citation_parser(refdir):
    db = ReferenceDB(refdir)
    assert db.search("werling")[0].id == "werling2011"
    assert [r.id for r in db.search("2014")] == ["mw2014"]
    assert parse_citations("siehe [@werling2011, Abschn. A.1; @mw2014]") == [("werling2011", "Abschn. A.1"),
                                                                              ("mw2014", "")]


def test_user_reference_and_link_roundtrip(refdir):
    db = ReferenceDB(refdir)
    ref = db.add_user_reference("doe2020", {"type": "paper", "authors": ["Jane Doe"], "title": "Test",
                                            "year": 2020, "venue": "Journal"})
    assert ref.user and (refdir / "user.yaml").exists()
    with pytest.raises(ValueError):
        db.add_user_reference("werling2011", {"type": "paper", "title": "x"})   # owned by another file
    with pytest.raises(ValueError):
        db.add_user_reference("bad", {"type": "paper", "title": "x"})            # required fields missing
    db.link("doe2020", "component:lateral_controller/stanley", "Testlink")
    again = ReferenceDB(refdir)
    assert "doe2020" in again
    assert again.links_for(reference="doe2020")[0]["target"] == "component:lateral_controller/stanley"
    assert again.unlink("doe2020", "component:lateral_controller/stanley")
    assert again.remove_user_reference("doe2020") and "doe2020" not in again


def test_repository_database_is_valid():
    db = ReferenceDB()
    assert {"werling2011", "pacejka2012", "iso2631_1", "snider2009", "fruchterman1991"} <= set(db.refs)
    own = [i for i in db.issues if i.file in ("vehicle_dynamics.yaml", "user.yaml", "links.yaml")]
    assert own == [], own
    assert db.cite("pacejka2012") == "Pacejka (2012)"


def test_used_reference_ids_report(kb):
    # strict for the packages documented here, only a warning for packages still in progress
    from vdsim.knowledge.generator import package_reference_ids
    missing_own = {}
    for name in OWN_PACKAGES:
        for rid, where in package_reference_ids(kb, kb.packages[name]).items():
            if rid not in kb.references:
                missing_own[rid] = where
    assert missing_own == {}
    report = kb.reference_report()
    if report["missing"]:
        import warnings
        warnings.warn(f"fehlende Referenz-IDs anderer Pakete: {sorted(report['missing'])}")
