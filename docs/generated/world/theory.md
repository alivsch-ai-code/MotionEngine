# world – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


**Noch nicht dokumentiert.** Es gibt keine handgeschriebene `theory.md` (`vdsim/world/docs/theory.md`).

## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}

Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt `## … {#concept-id}`:

- `box_restriction`
- `continuous_curvature_road`
- `idm`
- `mobil`
- `sat_collision`
- `scenario_engine`

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Box restriction](../README.md#konzepte-ohne-dokumentation) | [`road.RoadNetwork.corridor`](../../../vdsim/world/road.py#L405) | [`behavior_planner/rule_based`](../behavior/components/behavior_planner__rule_based.md) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Continuous curvature road](../README.md#konzepte-ohne-dokumentation) | [`road.RoadNetwork.route_line`](../../../vdsim/world/road.py#L482), [`road.connect_poses`](../../../vdsim/world/road.py#L582) | – | [Werling (2011)](../references.md#werling2011) |
| [Idm](../README.md#konzepte-ohne-dokumentation) | [`traffic_models.idm_acceleration`](../../../vdsim/world/traffic_models.py#L44) | [`world/scenario_engine`](components/world__scenario_engine.md) | [asam_openscenario (fehlt in docs/references)](../references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](../references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Mobil](../README.md#konzepte-ohne-dokumentation) | [`rule_based.RuleBasedBehavior._lane_change_eval`](../../../vdsim/behavior/rule_based.py#L241), [`traffic_models.mobil_incentive`](../../../vdsim/world/traffic_models.py#L75) | [`behavior_planner/rule_based`](../behavior/components/behavior_planner__rule_based.md), [`world/scenario_engine`](components/world__scenario_engine.md) | [asam_openscenario (fehlt in docs/references)](../references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](../references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Sat collision](../README.md#konzepte-ohne-dokumentation) | [`collision.sat_overlap`](../../../vdsim/world/collision.py#L28) | [`world/scenario_engine`](components/world__scenario_engine.md) | [asam_openscenario (fehlt in docs/references)](../references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](../references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Scenario engine](../README.md#konzepte-ohne-dokumentation) | – | [`world/scenario_engine`](components/world__scenario_engine.md) | [asam_openscenario (fehlt in docs/references)](../references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](../references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
