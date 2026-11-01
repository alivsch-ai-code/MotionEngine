# Wissens-, Dokumentations- und Rückverfolgbarkeitssystem – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/knowledge/test_knowledge_references.py](../../../tests/knowledge/test_knowledge_references.py) | Laden und Zusammenführen, Validierung, Zitat, BibTeX, Benutzerreferenzen und Verknüpfungen |
| [tests/knowledge/test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py) | Sammeln über das ganze Repository ohne Ausnahme, Toleranz gegenüber defekten Dateien, Referenzbericht |
| [tests/knowledge/test_knowledge_generator.py](../../../tests/knowledge/test_knowledge_generator.py) | Pflichtartefakte je Paket, Determinismus (zwei Läufe identisch), Rückverfolgbarkeitsmatrix |
| [tests/knowledge/test_knowledge_graph.py](../../../tests/knowledge/test_knowledge_graph.py) | Knoten- und Kantentypen, Kette to_frenet → frenet_transformation → werling2011, Abfragen |
| [tests/knowledge/test_knowledge_rendering.py](../../../tests/knowledge/test_knowledge_rendering.py) | Formel-Rendering, Markdown-Konverter, Darstellbarkeit aller theory.md-Formeln |
| [tests/knowledge/test_knowledge_gui.py](../../../tests/knowledge/test_knowledge_gui.py) | Wissensbrowser offscreen (Navigation, Expertenmodus, Graph, Quellen anlegen und verknüpfen) |

## Tests, die dieses Paket verwenden

### [tests/knowledge/conftest.py](../../../tests/knowledge/conftest.py)

Importiert: `vdsim.knowledge.collector`, `vdsim.knowledge.graph`

### [tests/knowledge/test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py)

**Zeigt:** Sammeln über das ganze Repository ohne Ausnahme, Toleranz gegenüber defekten Dateien, Referenzbericht

Importiert: `vdsim.knowledge.collector`

| Testfunktion | Beschreibung |
|---|---|
| `test_collects_whole_repository` | – |
| `test_legacy_and_framework_components` | – |
| `test_traces_from_code_and_module_yaml` | – |
| `test_handwritten_docs_complete` | – |
| `test_tests_examples_and_configs_linked` | – |
| `test_tolerant_against_broken_files` | – |

### [tests/knowledge/test_knowledge_generator.py](../../../tests/knowledge/test_knowledge_generator.py)

**Zeigt:** Pflichtartefakte je Paket, Determinismus (zwei Läufe identisch), Rückverfolgbarkeitsmatrix

Importiert: `vdsim.knowledge.generator`

| Testfunktion | Beschreibung |
|---|---|
| `test_artifacts_for_every_package_and_determinism` | – |
| `test_render_twice_identical` | – |
| `test_stub_for_undocumented_package` | – |
| `test_traceability_pages` | – |
| `test_init_package_docs` | – |

### [tests/knowledge/test_knowledge_graph.py](../../../tests/knowledge/test_knowledge_graph.py)

**Zeigt:** Knoten- und Kantentypen, Kette to_frenet → frenet_transformation → werling2011, Abfragen

Importiert: `vdsim.knowledge.graph`

| Testfunktion | Beschreibung |
|---|---|
| `test_node_and_edge_types` | – |
| `test_frenet_chain` | – |
| `test_queries` | – |
| `test_json_roundtrip_and_html` | – |
| `test_force_layout_deterministic` | – |

### [tests/knowledge/test_knowledge_gui.py](../../../tests/knowledge/test_knowledge_gui.py)

**Zeigt:** Wissensbrowser offscreen (Navigation, Expertenmodus, Graph, Quellen anlegen und verknüpfen)

Importiert: `vdsim.knowledge.references`

| Testfunktion | Beschreibung |
|---|---|
| `test_browser_smoke` | – |

### [tests/knowledge/test_knowledge_references.py](../../../tests/knowledge/test_knowledge_references.py)

**Zeigt:** Laden und Zusammenführen, Validierung, Zitat, BibTeX, Benutzerreferenzen und Verknüpfungen

Importiert: `vdsim.knowledge.generator`, `vdsim.knowledge.references`

| Testfunktion | Beschreibung |
|---|---|
| `test_merge_validation_and_duplicates` | – |
| `test_german_citations` | – |
| `test_bibtex_export` | – |
| `test_search_and_citation_parser` | – |
| `test_user_reference_and_link_roundtrip` | – |
| `test_repository_database_is_valid` | – |
| `test_used_reference_ids_report` | strict for the packages documented here, only a warning for packages still in progress |

### [tests/knowledge/test_knowledge_rendering.py](../../../tests/knowledge/test_knowledge_rendering.py)

**Zeigt:** Formel-Rendering, Markdown-Konverter, Darstellbarkeit aller theory.md-Formeln

Importiert: `vdsim.knowledge.markdown`, `vdsim.knowledge.mathrender`

| Testfunktion | Beschreibung |
|---|---|
| `test_render_png_and_svg` | – |
| `test_markdown_converter` | – |
| `test_markdown_with_rendered_math` | – |
| `test_all_theory_formulas_render` | – |
