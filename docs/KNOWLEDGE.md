# Wissens- und Dokumentationssystem

Mit `vdsim.knowledge` lässt sich jederzeit nachvollziehen, wie ein Teilsystem funktioniert. Das System beantwortet:

- welche Komponenten, Datenflüsse und Modelle beteiligt sind,
- warum eine Implementierung existiert und welches Problem sie löst,
- welche Theorie und welche Annahmen dahinterstehen,
- auf welchen Quellen sie beruht und welche Tests sie prüfen.

Das Wissen wird automatisch aus Code und Paketdoku gesammelt. Daraus entstehen:

- die generierte Dokumentation `docs/generated/`,
- ein Wissensgraph,
- ein Wissensbrowser in der GUI.

## Schnellstart

```powershell
python tools/build_docs.py                    # docs/generated erzeugen (idempotent, deterministisch)
python tools/build_docs.py --check            # Exit-Code 1, wenn docs/generated veraltet ist (CI)
python tools/build_docs.py --report           # fehlende Referenz-IDs, Prüfung der Quellen, Hinweise
python tools/build_docs.py --explain stanley_controller   # „Wie funktioniert X“
python tools/build_docs.py --path geometry.ReferenceLine.to_frenet werling2011
python tools/build_docs.py --search frenet
python tools/build_docs.py --bibtex quellen.bib
python tools/build_docs.py --init <paket>     # Vorlage module.yaml + theory.md anlegen
python -m vdsim.knowledge.gui                 # Wissensbrowser
```

Einstieg in die generierte Doku: `docs/generated/README.md`. Den Wissensgraphen gibt es zusätzlich als eigenständige Seite `docs/generated/knowledge_graph.html`. Sie läuft offline und ohne CDN.

## Ordnerstruktur: Module/{src, tests, examples, docs}

Jedes Modul besitzt automatisch einen eigenen Dokumentationsbereich:

| Rolle | Ort | Inhalt |
|---|---|---|
| src | `vdsim/<paket>/` (bzw. `lane_change/`) | Quellcode mit Docstrings, `DOC = ComponentDoc(...)`, `@trace` |
| docs (handgeschrieben) | `vdsim/<paket>/docs/` | `module.yaml`, `theory.md`, weitere Kapitel `*.md`; Unterpakete dürfen eigene `docs/`-Ordner haben |
| tests | `tests/<paket>/test_<paket>_*.py` (ältere Tests direkt in `tests/`) | werden über Importe und Komponentennamen zugeordnet |
| examples | `examples/<paket>/`, `run_*.py`, in module.yaml genannte Dateien | Beispiele |
| docs (generiert) | `docs/generated/<paket>/` | nicht von Hand bearbeiten |
| Quellen | `docs/references/*.yaml` | Literaturdatenbank, `user.yaml`, `links.yaml` |

Für Pakete ohne handgeschriebene Doku entsteht automatisch ein Stub-Bereich. Er enthält alles, was aus dem Code erkannt wird, und einen Hinweis auf `--init`.

## Generierte Artefakte je Paket

| Datei | Inhalt |
|---|---|
| `index.md` | Übersicht, Architektur (Module, Abhängigkeiten), Designentscheidungen, Implementierung, Komponenten, Verfahren, Erweiterungspunkte |
| `interfaces.md` | Komponenten mit Ports, Typen, Versionen; Datentypen; öffentliche API |
| `configuration.md` | Parameter mit Bezeichnung, Einheit, Default, Min, Max; Parametersätze; Konfigurationsdateien |
| `theory.md` | handgeschriebene Theorie (Zitate aufgelöst) oder „Noch nicht dokumentiert“; Verknüpfung Verfahren → Implementierung → Quelle |
| `examples.md`, `limitations.md`, `validation.md` | Beispiele, Grenzen (Paket, Komponenten, Anwendungsgrenzen der Verfahren), Tests und was sie zeigen |
| `references.md`, `traceability.md` | verwendete Quellen; Kette Implementierung → Gleichung → Konzept → Quelle → Test, mit „Warum“ |
| `components/<kind>__<name>.md` | eine Seite je Komponente |

Global gibt es außerdem diese Dateien:

- `README.md`
- `traceability_matrix.md`
- `references.md` und `references.bib`
- `report.md` mit Referenzprüfung und Hinweisen des Sammlers
- `knowledge_graph.json` und `knowledge_graph.html`
- `_meta.json`, die einzige Datei mit Zeitstempel

## Workflow für Entwickler: neue Komponente

1. **Code und DOC:** Die Komponente bekommt `DOC = ComponentDoc(summary=, purpose=, theory=, assumptions=, limitations=, references=[...], concepts=[...], validation=, extension_points=, expert=)`. Parameter legt man mit `param(default, unit, label, min=, max=)` an. Ports gibt es nur mit Typen aus `vdsim.framework.types`.
2. **@trace:** Jede Funktion, die eine Gleichung umsetzt, erhält
   `@trace("werling2011", section="3.4", equation="(3.8)", concept="quintic_polynomial")`.
   Bestehender Code, der nicht geändert werden soll, wird stattdessen in `module.yaml` unter `traceability:` eingetragen.
3. **module.yaml:** Metadaten nach `docs/templates/MODULE_DOCS.md`. Zusätzlich erkennt der Sammler:
   - `components:` mit Ergänzungen je Komponente: `summary`, `concepts`, `references`, `parameters` (Einheiten und Beschreibungen für Konstruktorargumente), `config_fields` (z. B. `systems.esp_*`)
   - `traceability:` mit `implementation`, `concept`, `source`, `section`, `equation`, `tests`, `note`
   - `data_flow`, `models`, `expert`, `stability`
4. **theory.md:** Je Verfahren ein Abschnitt `## Name {#concept-id}` mit den zwölf Unterabschnitten der Vorlage. Dazu gehören „In einfachen Worten“ und eine Variablentabelle mit Spalte `Code-Name`. Formeln stehen in `$…$` bzw. `$$…$$` im matplotlib-mathtext-Umfang. Verboten sind `aligned`, Matrizen und `\underbrace`. In Tabellenzellen nutzt man `\vert` statt `|`. Zitate schreibt man als `[@id, Abschn. 3.4]`, Querverweise als `[Text](#andere-concept-id)`.
5. **Referenz:** Eintrag in `docs/references/<thema>.yaml` anlegen. Typen: paper, report, standard, book, norm, documentation, software, thesis. Alternativ geht es im Browser über den Reiter „Quellen“ (→ `user.yaml`), dort lässt sich die Referenz auch mit einer Komponente verknüpfen (→ `links.yaml`). Nur echte Quellen eintragen; unsichere Details wie Seiten oder ISBN weglassen.
6. **build_docs:** `python tools/build_docs.py` ausführen, danach `--report` auf fehlende IDs prüfen. `python -m pytest tests/knowledge` prüft unter anderem Vollständigkeit und Darstellbarkeit der Formeln.

## Rückverfolgbarkeit

Ein Eintrag besteht aus: Implementierung, Abschnitt, Gleichung, Konzept, Quelle, Tests und Herkunft (Code oder module.yaml). Darüber ist für jede wesentliche Implementierung erkennbar:

- **warum** sie existiert: „Ziel und Zweck“ des Konzepts,
- **welche Theorie** dahintersteht: der Abschnitt in theory.md,
- **welche Annahmen** gelten: „Annahmen“ des Konzepts,
- **auf welchen Quellen** sie beruht,
- **welche Tests** sie prüfen.

Fehlende Referenz-IDs sind nur Hinweise, keine Fehler, weil Pakete parallel entstehen.

## Wissensgraph

**Knotentypen:**

- package, module, component, class, function
- concept, reference, datatype, model
- document, test, example, config

**Kantentypen:**

- contains, imports, implements, cites
- consumes, produces
- documented_by, tested_by, example_of, configured_by
- related_to, subclass_of

Beispielkette: `function:…ReferenceLine.to_frenet` –implements→ `concept:frenet_transformation` –cites→ `reference:werling2011`.

**API:**

```python
from vdsim.knowledge import collect, build_graph
kb = collect(); g = build_graph(kb)
g.neighbors("model:tire_model/pacejka"); g.path("geometry.ReferenceLine.to_frenet", "werling2011")
g.concept_subgraph("magic_formula"); print(g.explain_markdown("stanley_controller", kb.references))
```

## Wissensbrowser (GUI)

`vdsim.gui.knowledge.KnowledgeBrowser(QWidget)` lässt sich in das Hauptfenster einbetten; eigenständig startet er mit `python -m vdsim.knowledge.gui`. Aufbau:

- **Navigationsbaum:** Paket → Seiten, Komponenten, Verfahren, Module → Klassen und Funktionen; dazu die Quellen.
- **Dokumentansicht:** mit gerenderten Formeln (Bild-Cache im Benutzerordner; `VDSIM_CACHE_DIR` überschreibt den Ort).
- **Expertenmodus:** blendet Herleitungen, Stabilitätsbetrachtungen, Designentscheidungen, Optimierungsprobleme, Forschungsbezüge, Erweiterungspunkte und `ComponentDoc.expert` ein. Blöcke zwischen `<!-- expert -->` und `<!-- /expert -->` gelten ebenfalls als Expertenstoff.
- **Reiter:**
  - „Wissensgraph“: Nachbarschaft oder Übersicht mit Knotentyp-Filter. Klick wählt einen Knoten aus, Doppelklick öffnet das Dokument.
  - „Rückverfolgbarkeit“: filterbare Tabelle.
  - „Quellen“: Suche, Details mit BibTeX, Referenz anlegen und verknüpfen.
- **Suche:** über Knoten, Quellen und den Volltext der Theorie.
