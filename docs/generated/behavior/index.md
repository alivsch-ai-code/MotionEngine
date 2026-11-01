# behavior

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.behavior` gibt es noch keine handgeschriebene Dokumentation (`vdsim/behavior/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init behavior`


`vdsim.behavior` · Quellcode: [vdsim/behavior/](../../../vdsim/behavior)

## Übersicht

Paket-Docstring:

```text
Behavior planning layer: rule-based state machine (lane keeping/change, merging, overtaking, junctions, parking).
```

| Kennzahl | Anzahl |
|---|---|
| Module | 4 |
| Komponenten | 1 |
| Verfahren/Konzepte | 5 |
| @trace-Einträge | 2 |
| Tests | 1 |
| Beispiele | 0 |

## Architektur

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.behavior`](../../../vdsim/behavior/__init__.py) | 10 | – | Behavior planning layer: rule-based state machine (lane keeping/change, merging, overtaking, junctions, parking). |
| [`vdsim.behavior.closed_loop`](../../../vdsim/behavior/closed_loop.py) | 50 | – | Closed loop world -> perception -> prediction -> behavior with the kinematic ego stand-in. |
| [`vdsim.behavior.params`](../../../vdsim/behavior/params.py) | 77 | RuleBasedParams | Parameters of the rule-based behavior planner (flat dataclass, German labels for the GUI). |
| [`vdsim.behavior.rule_based`](../../../vdsim/behavior/rule_based.py) | 923 | _Geo, RuleBasedBehavior | Rule-based behavior planner "behavior_planner/rule_based" (Werling 2011, 3.5 / 3.6 / 5.3). |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [geometry](../geometry/index.md), [world](../world/index.md)
- genutzt von: –
- externe Bibliotheken: `__future__`, `dataclasses`, `numpy`

## Designentscheidungen

_Noch nicht dokumentiert._

## Implementierung

_Keine Implementierungshinweise in module.yaml._

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`behavior_planner/rule_based`](components/behavior_planner__rule_based.md) | Regelbasierte Verhaltensplanung | 1.0.0 | Zustandsautomat für Spurhalten, Spurwechsel, Einfädeln, Überholen, Kreuzung/Kreisverkehr und Einparken; erzeugt Referenzkurve, Längsmodi und Box-Restriktion für den Trajektorienplaner. |

### Verfahren und Konzepte

- [Behavior state machine](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Box restriction](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Hazard indicator](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Einfädeln](../planning/theory.md#merging_mode)
- [Mobil](../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Erweiterungspunkte

_Keine angegeben._
