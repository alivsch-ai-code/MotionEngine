# ad

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.ad` gibt es noch keine handgeschriebene Dokumentation (`vdsim/ad/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init ad`


`vdsim.ad` · Quellcode: [vdsim/ad/](../../../vdsim/ad)

## Übersicht

Paket-Docstring:

```text
Integration of the automated-driving stack: stack definition, graph assembly, runner, results.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 4 |
| Komponenten | 0 |
| Verfahren/Konzepte | 0 |
| @trace-Einträge | 0 |
| Tests | 3 |
| Beispiele | 0 |

## Architektur

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.ad`](../../../vdsim/ad/__init__.py) | 13 | – | Integration of the automated-driving stack: stack definition, graph assembly, runner, results. |
| [`vdsim.ad.results`](../../../vdsim/ad/results.py) | 223 | ADResult | Result of one automated-driving simulation run. |
| [`vdsim.ad.runner`](../../../vdsim/ad/runner.py) | 308 | _Recorder | Scenario runner: scenario spec + stack -> graph -> executor -> ADResult. |
| [`vdsim.ad.stack`](../../../vdsim/ad/stack.py) | 129 | – | The automated-driving stack: which component runs in which layer, and how they are wired. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [research](../research/index.md), [runtime](../runtime/index.md), [world](../world/index.md)
- genutzt von: [api](../api/index.md), [gui](../gui/index.md), [research](../research/index.md)
- externe Bibliotheken: `__future__`, `copy`, `dataclasses`, `json`, `math`, `numpy`, `pathlib`, `time`

## Designentscheidungen

_Noch nicht dokumentiert._

## Implementierung

_Keine Implementierungshinweise in module.yaml._

## Erweiterungspunkte

_Keine angegeben._
