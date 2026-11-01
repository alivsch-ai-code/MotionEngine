# api

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.api` gibt es noch keine handgeschriebene Dokumentation (`vdsim/api/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init api`


`vdsim.api` · Quellcode: [vdsim/api/](../../../vdsim/api)

## Übersicht

Paket-Docstring:

```text
Public Python API of the platform (API first: CLI, REST server and GUI use these functions).

from vdsim import api
api.list_components("tracking_controller")
result = api.run("highway_cut_in", stack={"controller": "tracking_controller/werling_bilevel"})
batch = api.sweep({"scenario": "highway_cut_in"}, {"stack.planner.params.cost.k_jerk": [0.5, 1, 2]})
```

| Kennzahl | Anzahl |
|---|---|
| Module | 2 |
| Komponenten | 0 |
| Verfahren/Konzepte | 0 |
| @trace-Einträge | 0 |
| Tests | 2 |
| Beispiele | 2 |

## Architektur

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.api`](../../../vdsim/api/__init__.py) | 126 | – | Public Python API of the platform (API first: CLI, REST server and GUI use these functions). |
| [`vdsim.api.server`](../../../vdsim/api/server.py) | 243 | JobStore | REST/JSON API (standard library only). |

### Abhängigkeiten

- nutzt: [ad](../ad/index.md), [framework](../framework/index.md), [knowledge](../knowledge/index.md), [matlab](../matlab/index.md), [research](../research/index.md), [runtime](../runtime/index.md), [world](../world/index.md)
- genutzt von: [gui](../gui/index.md)
- externe Bibliotheken: `__future__`, `argparse`, `concurrent`, `copy`, `http`, `json`, `numpy`, `threading`, `traceback`, `urllib`, `uuid`

## Designentscheidungen

_Noch nicht dokumentiert._

## Implementierung

_Keine Implementierungshinweise in module.yaml._

## Erweiterungspunkte

_Keine angegeben._
