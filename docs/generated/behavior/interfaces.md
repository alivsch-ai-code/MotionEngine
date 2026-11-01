# behavior – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.behavior` gibt es noch keine handgeschriebene Dokumentation (`vdsim/behavior/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init behavior`


## Komponenten

### [Regelbasierte Verhaltensplanung](components/behavior_planner__rule_based.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `behavior_planner/rule_based`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.behavior.rule_based.RuleBasedBehavior` |
| Schnittstelle | – |
| Periode | 0.1 s |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `objects` | `ObjectList` | – | – | – |
| `prediction` | `Prediction` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | letzte Solltrajektorie (Gefahrenindikator) | optional, Rückführung |
| `world` | `WorldState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `behavior` | `BehaviorCommand` | – | – | – |

## Öffentliche API

### `vdsim.behavior.closed_loop`

| Name | Art | Beschreibung |
|---|---|---|
| [`run_closed_loop(scenario, duration, dt, seed, behavior_params, perception, perception_params, predictor, stop_on_collision)`](../../../vdsim/behavior/closed_loop.py#L16) | Funktion | returns a list of dicts {t, ego, behavior, world, objects} |

### `vdsim.behavior.params`

| Name | Art | Beschreibung |
|---|---|---|
| [`RuleBasedParams`](../../../vdsim/behavior/params.py#L11) | Klasse | target speed |

### `vdsim.behavior.rule_based`

| Name | Art | Beschreibung |
|---|---|---|
| [`RuleBasedBehavior`](../../../vdsim/behavior/rule_based.py#L49) | Klasse | – |
