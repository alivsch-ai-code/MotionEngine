# Wissens-, Dokumentations- und Rückverfolgbarkeitssystem – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`Collector._doc_traces`](../../../vdsim/knowledge/collector.py#L953) | – | [Rückverfolgbarkeitsmodell](theory.md#traceability_model) | [ISO 26262:2018 (2018)](../references.md#iso26262) | [conftest.py](../../../tests/knowledge/conftest.py), [test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py) | module.yaml |
| [`Collector.run`](../../../vdsim/knowledge/collector.py#L599) | – | [Graphmodell des Wissens](theory.md#knowledge_graph_model) | – | [conftest.py](../../../tests/knowledge/conftest.py), [test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py) | module.yaml |
| [`trace_rows`](../../../vdsim/knowledge/generator.py#L536) | – | [Rückverfolgbarkeitsmodell](theory.md#traceability_model) | [Gotel und Finkelstein (1994)](../references.md#gotel1994) | [test_knowledge_generator.py](../../../tests/knowledge/test_knowledge_generator.py), [test_knowledge_references.py](../../../tests/knowledge/test_knowledge_references.py) | Code (@trace) |
| [`KnowledgeGraph.path`](../../../vdsim/knowledge/graph.py#L177) | – | [Graphmodell des Wissens](theory.md#knowledge_graph_model) | [Gotel und Finkelstein (1994)](../references.md#gotel1994) | [conftest.py](../../../tests/knowledge/conftest.py), [test_knowledge_graph.py](../../../tests/knowledge/test_knowledge_graph.py) | Code (@trace) |
| [`build_graph`](../../../vdsim/knowledge/graph.py#L352) | – | [Graphmodell des Wissens](theory.md#knowledge_graph_model) | [Gotel und Finkelstein (1994)](../references.md#gotel1994) | [conftest.py](../../../tests/knowledge/conftest.py), [test_knowledge_graph.py](../../../tests/knowledge/test_knowledge_graph.py) | Code (@trace) |
| [`force_layout`](../../../vdsim/knowledge/graph.py#L551) | – | [Kräftebasiertes Graphlayout](theory.md#force_directed_layout) | [Fruchterman und Reingold (1991)](../references.md#fruchterman1991) | [conftest.py](../../../tests/knowledge/conftest.py), [test_knowledge_graph.py](../../../tests/knowledge/test_knowledge_graph.py) | Code (@trace) |

## Warum es diese Implementierungen gibt

### `Collector._doc_traces`

- **Warum:** Für jede wesentliche Implementierung erkennbar machen, warum sie existiert, welches Problem sie löst, welche Theorie und Annahmen dahinterstehen, auf welchen Quellen sie beruht und welche Tests sie prüfen.
- **Theorie:** [Rückverfolgbarkeitsmodell](theory.md#traceability_model)
- **Annahmen:** Konzept- und Referenz-IDs sind stabil; Annotationen werden bei Änderungen gepflegt.
- **Quelle:** [ISO 26262:2018 (2018)](../references.md#iso26262)

### `Collector.run`

- **Warum:** Alle Wissensbausteine (Pakete, Module, Komponenten, Klassen, Funktionen, Verfahren, Quellen, Datentypen, Modelle, Dokumente, Tests, Beispiele, Konfigurationen) und ihre Beziehungen in einer einheitlichen, abfragbaren Struktur.
- **Theorie:** [Graphmodell des Wissens](theory.md#knowledge_graph_model)
- **Annahmen:** Konzepte werden über stabile IDs (Anker `{#concept-id}`) referenziert; Quellen über Referenz-IDs.
- **Quelle:** –

### `trace_rows`

- **Warum:** Für jede wesentliche Implementierung erkennbar machen, warum sie existiert, welches Problem sie löst, welche Theorie und Annahmen dahinterstehen, auf welchen Quellen sie beruht und welche Tests sie prüfen.
- **Theorie:** [Rückverfolgbarkeitsmodell](theory.md#traceability_model)
- **Annahmen:** Konzept- und Referenz-IDs sind stabil; Annotationen werden bei Änderungen gepflegt.
- **Quelle:** [Gotel und Finkelstein (1994)](../references.md#gotel1994)
- **Hinweis:** Kette Implementierung → Gleichung → Konzept → Quelle → Test

### `KnowledgeGraph.path`

- **Warum:** Alle Wissensbausteine (Pakete, Module, Komponenten, Klassen, Funktionen, Verfahren, Quellen, Datentypen, Modelle, Dokumente, Tests, Beispiele, Konfigurationen) und ihre Beziehungen in einer einheitlichen, abfragbaren Struktur.
- **Theorie:** [Graphmodell des Wissens](theory.md#knowledge_graph_model)
- **Annahmen:** Konzepte werden über stabile IDs (Anker `{#concept-id}`) referenziert; Quellen über Referenz-IDs.
- **Quelle:** [Gotel und Finkelstein (1994)](../references.md#gotel1994)
- **Hinweis:** Breitensuche: kürzester Pfad

### `build_graph`

- **Warum:** Alle Wissensbausteine (Pakete, Module, Komponenten, Klassen, Funktionen, Verfahren, Quellen, Datentypen, Modelle, Dokumente, Tests, Beispiele, Konfigurationen) und ihre Beziehungen in einer einheitlichen, abfragbaren Struktur.
- **Theorie:** [Graphmodell des Wissens](theory.md#knowledge_graph_model)
- **Annahmen:** Konzepte werden über stabile IDs (Anker `{#concept-id}`) referenziert; Quellen über Referenz-IDs.
- **Quelle:** [Gotel und Finkelstein (1994)](../references.md#gotel1994)
- **Hinweis:** Knoten und Kanten aus Code, Doku und Quellen

### `force_layout`

- **Warum:** Übersichtliche Anordnung des Wissensgraphen: verbundene Knoten nah beieinander, unverbundene auf Abstand.
- **Theorie:** [Kräftebasiertes Graphlayout](theory.md#force_directed_layout)
- **Annahmen:** Ungewichtete Kanten; Startpositionen aus festem Zufallsstartwert (deterministisch).
- **Quelle:** [Fruchterman und Reingold (1991)](../references.md#fruchterman1991)
- **Hinweis:** Abstoßung k²/d, Anziehung d²/k, Abkühlung
