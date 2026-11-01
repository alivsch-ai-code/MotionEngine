# behavior – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


**Noch nicht dokumentiert.** Es gibt keine handgeschriebene `theory.md` (`vdsim/behavior/docs/theory.md`).

## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}

Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt `## … {#concept-id}`:

- `behavior_state_machine`
- `box_restriction`
- `hazard_indicator`
- `mobil`

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Behavior state machine](../README.md#konzepte-ohne-dokumentation) | – | [`behavior_planner/rule_based`](components/behavior_planner__rule_based.md) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Box restriction](../README.md#konzepte-ohne-dokumentation) | [`road.RoadNetwork.corridor`](../../../vdsim/world/road.py#L405) | [`behavior_planner/rule_based`](components/behavior_planner__rule_based.md) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Hazard indicator](../README.md#konzepte-ohne-dokumentation) | – | [`behavior_planner/rule_based`](components/behavior_planner__rule_based.md) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Einfädeln](../planning/theory.md#merging_mode) | [`rule_based.RuleBasedBehavior._update_merge`](../../../vdsim/behavior/rule_based.py#L761), [`longitudinal.MergingTarget.state`](../../../vdsim/planning/longitudinal.py#L116) | [`behavior_planner/rule_based`](components/behavior_planner__rule_based.md) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Mobil](../README.md#konzepte-ohne-dokumentation) | [`rule_based.RuleBasedBehavior._lane_change_eval`](../../../vdsim/behavior/rule_based.py#L241), [`traffic_models.mobil_incentive`](../../../vdsim/world/traffic_models.py#L75) | [`behavior_planner/rule_based`](components/behavior_planner__rule_based.md), [`world/scenario_engine`](../world/components/world__scenario_engine.md) | [asam_openscenario (fehlt in docs/references)](../references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](../references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
