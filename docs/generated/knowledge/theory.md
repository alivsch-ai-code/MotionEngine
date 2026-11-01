# Wissens-, Dokumentations- und Rückverfolgbarkeitssystem – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/knowledge/docs/theory.md](../../../vdsim/knowledge/docs/theory.md).

## Graphmodell des Wissens {#knowledge_graph_model}

### Ziel und Zweck
Alle Wissensbausteine (Pakete, Module, Komponenten, Klassen, Funktionen, Verfahren, Quellen, Datentypen, Modelle, Dokumente, Tests, Beispiele, Konfigurationen) und ihre Beziehungen in einer einheitlichen, abfragbaren Struktur.

### Theorie
Gerichteter, typisierter Multigraph $G = (V, E)$ mit Knotentypen $\tau(v) \in T_V$ (13 Typen) und Kanten $(u, v, \rho)$ mit Kantentyp $\rho \in T_E$ (12 Typen: contains, imports, implements, cites, consumes, produces, documented_by, tested_by, example_of, configured_by, related_to, subclass_of). Knoten-IDs sind global eindeutig: Typ plus Schlüssel, z. B. `concept:frenet_transformation`. Abfragen:

- Nachbarschaft $N(v) = \{u : (v, u) \in E \vee (u, v) \in E\}$, optional gefiltert nach Kanten- und Knotentyp.
- Pfad: kürzester ungerichteter Pfad per Breitensuche, Aufwand $O(\vert V\vert + \vert E\vert)$.
- Teilgraph eines Konzepts: Nachbarschaft der Tiefe $k$.
- „Wie funktioniert X“: direkte Nachbarn plus die über Konzepte, Komponenten und Implementierungen erreichbaren Quellen, Tests, Datentypen und Dokumente.

### Herleitung
Rückverfolgbarkeit ist eine Relation zwischen Artefakten. Eine Graphdarstellung macht transitive Fragen (Welche Quelle steckt hinter dieser Funktion? Welche Tests prüfen dieses Verfahren?) zu Pfadsuchen.

### Annahmen
Konzepte werden über stabile IDs (Anker `{#concept-id}`) referenziert; Quellen über Referenz-IDs.

### Randbedingungen
Kanten zu unbekannten Knoten werden verworfen (die Referenzprüfung meldet fehlende IDs separat); private Funktionen erscheinen nur, wenn sie annotiert sind.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $V$ | Knotenmenge | – | `KnowledgeGraph.nodes` |
| $E$ | Kantenmenge | – | `KnowledgeGraph.edges` |
| $T_V, T_E$ | Knoten-, Kantentypen | – | `NODE_TYPES`, `EDGE_TYPES` |

### Anwendungsgrenzen
Semantische Ähnlichkeit (gleiches Verfahren unter anderem Namen) wird nicht erkannt.

### Vor- und Nachteile
- Vorteil: einheitliche Abfragen, Visualisierung, Export (JSON).
- Nachteil: Qualität hängt von der Pflege der IDs ab.

### Numerische Aspekte
Graph mit einigen tausend Knoten; alle Abfragen sind linear.

### Praktische Auswirkungen
Wissensbrowser, `--explain`, `--path` und die generierten Seiten beruhen auf demselben Graphen.

### In einfachen Worten
Eine Landkarte, auf der jedes Stück Code, jede Formel, jede Quelle und jeder Test ein Ort ist und die Straßen zeigen, was wozu gehört.

### Quellen
[[Gotel und Finkelstein (1994)](../references.md#gotel1994)]

## Kräftebasiertes Graphlayout {#force_directed_layout}

### Ziel und Zweck
Übersichtliche Anordnung des Wissensgraphen: verbundene Knoten nah beieinander, unverbundene auf Abstand.

### Theorie
Fruchterman-Reingold mit idealer Kantenlänge $k = C\sqrt{A/n}$:

$$f_{ab}(d) = \frac{k^2}{d}, \qquad f_{an}(d) = \frac{d^2}{k}$$

Je Iteration: Verschiebung aus Abstoßung aller Paare und Anziehung entlang der Kanten, begrenzt durch die Temperatur $T$, die linear abkühlt; zusätzlich schwache Gravitation zum Ursprung.

### Herleitung
Physikalische Analogie: Knoten sind geladene Teilchen, Kanten Federn. Das Gleichgewicht der Kräfte entspricht einem lokalen Minimum einer Energiefunktion; die Abkühlung verhindert Oszillationen.

### Annahmen
Ungewichtete Kanten; Startpositionen aus festem Zufallsstartwert (deterministisch).

### Randbedingungen
Python-Layout (GUI) $O(n^2)$ je Iteration, für Teilgraphen bis einige hundert Knoten; das HTML nutzt ein Gitter für die Abstoßung (näherungsweise $O(n)$).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k$ | ideale Kantenlänge | – | `k` |
| $T$ | Temperatur (maximale Verschiebung) | – | `temp` |
| $n$ | Knotenzahl | – | `n` |

### Anwendungsgrenzen
Große, dichte Graphen werden unübersichtlich; deshalb Filter und Nachbarschaftsansicht.

### Vor- und Nachteile
- Vorteil: einfach, gute Ergebnisse für dünn besetzte Graphen.
- Nachteil: lokale Minima, quadratischer Aufwand.

### Numerische Aspekte
Abstände nach unten begrenzt; Positionen werden auf $[-1, 1]$ normiert.

### Praktische Auswirkungen
Reiter „Wissensgraph“ im Browser und knowledge_graph.html.

### In einfachen Worten
Die Knoten stoßen sich ab, die Verbindungen ziehen sie zusammen – bis sich ein ruhiges Bild ergibt.

### Quellen
[[Fruchterman und Reingold (1991)](../references.md#fruchterman1991)]

## Rückverfolgbarkeitsmodell {#traceability_model}

### Ziel und Zweck
Für jede wesentliche Implementierung erkennbar machen, warum sie existiert, welches Problem sie löst, welche Theorie und Annahmen dahinterstehen, auf welchen Quellen sie beruht und welche Tests sie prüfen.

### Theorie
Ein Rückverfolgbarkeitseintrag ist das Tupel

$$t = (\mathrm{Implementierung}, \mathrm{Abschnitt}, \mathrm{Gleichung}, \mathrm{Konzept}, \mathrm{Quelle}, \mathrm{Tests}, \mathrm{Herkunft})$$

Quellen der Einträge: `@trace(quelle, section=, equation=, concept=)` im Code (Herkunft „Code“) und `traceability:` in module.yaml (Herkunft „module.yaml“). Über das Konzept sind Ziel, Theorie, Annahmen und Grenzen aus theory.md erreichbar; Tests kommen aus dem Eintrag oder aus Testdateien, die das Modul importieren.

### Herleitung
Vorwärts-Rückverfolgbarkeit (Quelle → Konzept → Implementierung → Test) und Rückwärts-Rückverfolgbarkeit (Test → Implementierung → Quelle) sind dieselbe Kette in beiden Richtungen; die Graphkanten implements, cites und tested_by bilden sie ab.

### Annahmen
Konzept- und Referenz-IDs sind stabil; Annotationen werden bei Änderungen gepflegt.

### Randbedingungen
Fehlende Referenz-IDs werden als Hinweis gemeldet (report.md), nicht als Fehler.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $t$ | Trace-Eintrag | – | `kb.traces` |
| Herkunft | Code oder module.yaml | – | `origin` |

### Anwendungsgrenzen
Keine Anforderungsebene (Lastenheft); Tests werden über Importe zugeordnet, nicht über Abdeckung.

### Vor- und Nachteile
- Vorteil: maschinell prüfbar, ohne zusätzliches Werkzeug.
- Nachteil: hängt von Disziplin bei Annotationen ab.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
traceability.md je Paket und traceability_matrix.md; Reiter „Rückverfolgbarkeit“ im Browser. Grundlage für Sicherheitsnachweise im Sinne von ISO 26262.

### In einfachen Worten
Zu jeder wichtigen Funktion steht dabei: nach welcher Formel aus welchem Buch sie rechnet und welcher Test das prüft.

### Quellen
[[Gotel und Finkelstein (1994)](../references.md#gotel1994)], [[ISO 26262:2018 (2018)](../references.md#iso26262)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Kräftebasiertes Graphlayout](theory.md#force_directed_layout) | [`graph.force_layout`](../../../vdsim/knowledge/graph.py#L551) | – | [Fruchterman und Reingold (1991)](../references.md#fruchterman1991) |
| [Graphmodell des Wissens](theory.md#knowledge_graph_model) | [`collector.Collector.run`](../../../vdsim/knowledge/collector.py#L599), [`graph.KnowledgeGraph.path`](../../../vdsim/knowledge/graph.py#L177), [`graph.build_graph`](../../../vdsim/knowledge/graph.py#L352) | – | [Gotel und Finkelstein (1994)](../references.md#gotel1994) |
| [Rückverfolgbarkeitsmodell](theory.md#traceability_model) | [`knowledge.trace`](../../../vdsim/framework/knowledge.py#L41), [`collector.Collector._doc_traces`](../../../vdsim/knowledge/collector.py#L953), [`generator.trace_rows`](../../../vdsim/knowledge/generator.py#L536) | – | [Gotel und Finkelstein (1994)](../references.md#gotel1994), [ISO 26262:2018 (2018)](../references.md#iso26262) |
