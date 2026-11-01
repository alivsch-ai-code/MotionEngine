# Wissens-, Dokumentations- und Rückverfolgbarkeitssystem

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.knowledge` · Quellcode: [vdsim/knowledge/](../../../vdsim/knowledge) · Paketdoku: [vdsim/knowledge/docs/](../../../vdsim/knowledge/docs)

## Übersicht

**Sammelt Wissen aus Code und Doku, erzeugt die Paketdokumentation, verknüpft Implementierung, Theorie, Quellen und Tests und stellt alles als Wissensgraph und Wissensbrowser bereit.**

Ein Entwickler soll jederzeit verstehen, wie ein Teilsystem funktioniert, welche Komponenten, Datenflüsse
und Modelle beteiligt sind, warum eine Implementierung existiert, welche Theorie und Annahmen dahinterstehen
und auf welchen Quellen sie beruht. Das Paket macht dieses Wissen automatisch auffindbar: aus Docstrings,
Komponenten-Metadaten (`ComponentDoc`, Ports, Parameter), `@trace`-Annotationen, den handgeschriebenen
`module.yaml`/`theory.md` je Paket, Tests, Beispielen, Konfigurationen und der Referenzdatenbank.

Paket-Docstring:

```text
Knowledge, documentation and traceability system of vdsim.

    references   reference database (docs/references/*.yaml), citations, BibTeX, user references and links
    collector    collects packages, modules, components, @trace entries, module.yaml, theory.md, tests,
                 examples and configurations into a KnowledgeBase
    graph        knowledge graph (nodes / edges, queries, JSON and standalone HTML export, force layout)
    generator    generates docs/generated/<package>/ (deterministic, idempotent)
    markdown     small Markdown -> HTML converter for the GUI (formulas via mathrender)
    mathrender   LaTeX formulas -> PNG / SVG with matplotlib mathtext (cached per user)

Command line: python tools/build_docs.py   (or python -m vdsim.knowledge)
GUI:          python -m vdsim.knowledge.gui
See docs/KNOWLEDGE.md.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 11 |
| Komponenten | 0 |
| Verfahren/Konzepte | 3 |
| @trace-Einträge | 6 |
| Tests | 7 |
| Beispiele | 1 |

## Architektur

- `references.py`: `ReferenceDB` (alle docs/references/*.yaml), Validierung, Suche, deutsche Zitate, BibTeX,
  Benutzerreferenzen (`user.yaml`) und Verknüpfungen (`links.yaml`).
- `collector.py`: `collect()` → `KnowledgeBase` (Pakete, Module per ast, Komponenten beider Registries,
  Traces, Konzepte, Datentypen, Parametersätze, Tests, Beispiele, Konfigurationen, Hinweise).
- `graph.py`: `build_graph()` → `KnowledgeGraph` (13 Knoten-, 12 Kantentypen), Abfragen, JSON/HTML-Export, `force_layout()`.
- `generator.py`: `generate()` schreibt docs/generated/ deterministisch; Seitenbausteine werden auch vom Browser genutzt.
- `markdown.py`, `mathrender.py`: Markdown → HTML mit gerenderten Formeln für die GUI.
- `cli.py` / `tools/build_docs.py`: Kommandozeile; `gui.py`: Starter des Wissensbrowsers.
- `vdsim/gui/knowledge/`: `KnowledgeBrowser(QWidget)` mit Navigation, Dokument, Wissensgraph, Rückverfolgbarkeit, Quellen, Suche und Expertenmodus.

### Datenfluss

Code (ast, Import) + docs/*.yaml/md + Tests/Beispiele/Configs → Collector → KnowledgeBase → Graph →
Generator (docs/generated) und Browser (GUI).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.knowledge`](../../../vdsim/knowledge/__init__.py) | 30 | – | Knowledge, documentation and traceability system of vdsim. |
| [`vdsim.knowledge.__main__`](../../../vdsim/knowledge/__main__.py) | 8 | – | python -m vdsim.knowledge: generate the documentation (see vdsim.knowledge.cli). |
| [`vdsim.knowledge.cli`](../../../vdsim/knowledge/cli.py) | 91 | – | Command line of the knowledge system (used by tools/build_docs.py and python -m vdsim.knowledge). |
| [`vdsim.knowledge.collector`](../../../vdsim/knowledge/collector.py) | 1329 | FunctionInfo, ClassInfo, ModuleInfo, ConceptSection, DocFile, ComponentInfo | Collects knowledge from code and documentation into a KnowledgeBase. |
| [`vdsim.knowledge.generator`](../../../vdsim/knowledge/generator.py) | 952 | Linker | Documentation generator: docs/generated/<package>/ for every package (deterministic, idempotent). |
| [`vdsim.knowledge.graph`](../../../vdsim/knowledge/graph.py) | 725 | Node, Edge, KnowledgeGraph | Knowledge graph: components, algorithms, models, data structures and documents with their relations. |
| [`vdsim.knowledge.gui`](../../../vdsim/knowledge/gui.py) | 27 | – | Standalone knowledge browser: python -m vdsim.knowledge.gui |
| [`vdsim.knowledge.markdown`](../../../vdsim/knowledge/markdown.py) | 304 | MarkdownRenderer | Small Markdown -> HTML converter for the knowledge browser (no external dependency). |
| [`vdsim.knowledge.mathrender`](../../../vdsim/knowledge/mathrender.py) | 136 | RenderResult | LaTeX formulas -> PNG / SVG images with matplotlib mathtext (no LaTeX installation needed). |
| [`vdsim.knowledge.paths`](../../../vdsim/knowledge/paths.py) | 60 | – | Repository layout used by the knowledge system (all paths relative to the repository root). |
| [`vdsim.knowledge.references`](../../../vdsim/knowledge/references.py) | 535 | Issue, Reference, ReferenceDB | Reference database: merges all docs/references/*.yaml files. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [gui](../gui/index.md), [trajectory](../trajectory/index.md), [vehicle_models](../vehicle_models/index.md)
- genutzt von: [api](../api/index.md), [gui](../gui/index.md)
- externe Bibliotheken: `PySide6`, `__future__`, `argparse`, `ast`, `collections`, `contextlib`, `dataclasses`, `datetime`, `hashlib`, `html`, `importlib`, `inspect`, `io`, `json`, `logging`, `matplotlib`, `numpy`, `os`, `pathlib`, `posixpath`, `re`, `struct`, `sys`, `tempfile`, `threading`, `time`, `yaml`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Dokumentation neben dem Code (vdsim/<paket>/docs), Generat getrennt (docs/generated) | Muster Module/{src, tests, examples, docs}; Handgeschriebenes und Erzeugtes werden nie vermischt | – |
| Tolerantes Sammeln (Hinweise statt Abbruch) | Mehrere Teams arbeiten parallel; halbfertige Pakete dürfen die Doku der anderen nicht blockieren | – |
| Rückverfolgbarkeit aus zwei Quellen – @trace im Code und traceability in module.yaml | neuer Code wird direkt annotiert; bestehender Code wird nachträglich dokumentiert, ohne ihn zu ändern | – |
| Deterministische Ausgabe ohne Zeitstempel (außer _meta.json), Schreiben nur bei Änderung | generierte Doku ist diff- und reviewbar; --check eignet sich für CI | – |
| Eigener Markdown-Konverter und matplotlib-mathtext statt externer Bibliotheken | keine neuen Abhängigkeiten; Formeln auch offline und ohne LaTeX-Installation | – |
| Wissensgraph-HTML mit eigenem JavaScript ohne CDN | funktioniert offline und in abgeschotteten Netzen | – |

## Implementierung

- GUI-Module (Import von PySide6/pyqtgraph/OpenGL auf oberster Ebene oder matplotlib.use) werden nur statisch analysiert, alle anderen zusätzlich importiert.
- Komponenten der klassischen Registry erhalten Ports aus ihrer Schnittstelle (LEGACY_INTERFACES) und Parameter aus der Konstruktorsignatur; Einheiten aus TireParameters bzw. module.yaml.
- Tests, Beispiele und Konfigurationen werden über Importe und Zeichenketten (Spec-Strings, model=, lateral_controller=, systems.X_enabled) mit Komponenten verknüpft.
- Formelbilder werden mit SHA-256-Schlüssel im Benutzer-Cache abgelegt (VDSIM_CACHE_DIR überschreibt).

### Verfahren und Konzepte

- [Kräftebasiertes Graphlayout](theory.md#force_directed_layout)
- [Graphmodell des Wissens](theory.md#knowledge_graph_model)
- [Rückverfolgbarkeitsmodell](theory.md#traceability_model)

## Erweiterungspunkte

- Neue Knoten- oder Kantentypen in graph.NODE_TYPES/EDGE_TYPES und build_graph()
- Neue Seiten je Paket über PAGE_BUILDERS im Generator
- Weitere Quellen des Collectors als zusätzlicher Schritt in Collector.run()

## Verwandte Module

[framework](../framework/index.md), [gui](../gui/index.md)

## Hauptquellen

[Fruchterman und Reingold (1991)](../references.md#fruchterman1991), [Gotel und Finkelstein (1994)](../references.md#gotel1994), [ISO 26262:2018 (2018)](../references.md#iso26262), [Matplotlib Development Team](../references.md#matplotlib_mathtext)
