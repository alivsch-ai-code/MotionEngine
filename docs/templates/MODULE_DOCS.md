# Vorlage: Dokumentationsbereich eines Moduls

Jedes Paket `vdsim/<paket>/` hat einen Dokumentationsbereich. Der Generator (`python tools/build_docs.py`) ergänzt ihn automatisch um Schnittstellen, Parameter, Rückverfolgbarkeit und Wissensgraph-Kanten.

```
vdsim/<paket>/            Quellcode (src)
vdsim/<paket>/docs/       module.yaml (Metadaten) + theory.md (Verfahren) + weitere Kapitel
tests/<paket>/            Tests
examples/<paket>/         lauffähige Beispiele
docs/generated/<paket>/   automatisch erzeugt (nicht von Hand bearbeiten)
```

## module.yaml

```yaml
id: planning                         # Paketname
title: Trajektorienplanung nach Werling
summary: Ein Satz, was das Modul tut.
purpose: Warum es das Modul gibt und welches Problem es löst.
architecture: |
  Kurze Beschreibung der inneren Struktur (Klassen, Datenfluss), Markdown erlaubt.
design_decisions:
  - decision: Absolutes Zeitraster der Endzeitpunkte
    reason: sichert zeitliche Konsistenz (Werling Satz 3)
    alternatives: relatives Raster (verletzt Bellman-Prinzip)
implementation:
  - Wichtige Implementierungsdetails (Vektorisierung, Lazy Evaluation, ...)
configuration:
  - name: sampling.d_step
    description: Abstand der lateralen Endabstände
examples:
  - examples/planning/lane_change.py
limitations:
  - Was das Modul nicht kann / bekannte Grenzen
validation:
  - test: tests/planning/test_planning_consistency.py
    shows: Bellman-Konsistenz ohne Störung
references: [werling2011, werling2010icra]
concepts: [frenet_frame, quintic_polynomial, bellman_principle]   # Knoten im Wissensgraph
related_modules: [geometry, stabilization]
extension_points:
  - Neue Kostenterme über @component(kind="cost_term")
```

## theory.md

Für jedes mathematische, physikalische, statistische oder technische Verfahren gibt es einen Abschnitt mit genau diesen Unterüberschriften:

```markdown
## <Verfahren> {#concept-id}

### Ziel und Zweck
### Theorie
### Herleitung              (Expertenmodus: ausführlich)
### Annahmen
### Randbedingungen
### Variablen               (Tabelle Symbol | Bedeutung | Einheit | Code-Name)
### Anwendungsgrenzen
### Vor- und Nachteile
### Numerische Aspekte
### Praktische Auswirkungen
### In einfachen Worten     (allgemeinverständliche Erklärung ohne Formeln)
### Quellen                 ([@werling2011, Abschn. 3.4], ...)
```

Formeln stehen als LaTeX in `$...$` (inline) bzw. `$$...$$` (abgesetzt). Unterstützt wird der matplotlib-mathtext-Umfang, also keine `\begin{aligned}`; mehrzeilige Gleichungen werden als mehrere `$$`-Blöcke geschrieben. Gleichungsnummern der Quelle stehen in Klammern hinter der Formel, z. B. `(3.8)`.

Der Anker `{#concept-id}` verbindet den Abschnitt mit `@trace(concept=...)` im Code und mit dem Wissensgraph.

## Referenzen (docs/references/<thema>.yaml)

```yaml
werling2011:
  type: thesis            # paper | report | standard | book | norm | documentation | software | thesis
  authors: [Moritz Werling]
  title: Ein neues Konzept für die Trajektoriengenerierung und -stabilisierung in zeitkritischen Verkehrsszenarien
  year: 2011
  publisher: KIT Scientific Publishing
  url: https://publikationen.bibliothek.kit.edu/1000021738
  isbn: 978-3-86644-631-1
  notes: Dissertation, Grundlage von vdsim.planning und vdsim.stabilization
```
