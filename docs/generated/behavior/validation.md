# behavior – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

_Keine Validierungsangaben in module.yaml._

## Tests, die dieses Paket verwenden

### [tests/behavior/test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py)

Importiert: `vdsim.behavior.closed_loop`

Komponenten: `behavior_planner/rule_based`

| Testfunktion | Beschreibung |
|---|---|
| `test_following_after_cut_in` | – |
| `test_merge_selects_gap_and_moves_reference` | – |
| `test_stop_at_red_light` | – |
| `test_box_restriction_markings` | – |
| `test_parking_direction_change_only_at_standstill` | – |
| `test_hazard_indicator_postpones_lane_change` | – |

## Validierung von [behavior_planner/rule_based](components/behavior_planner__rule_based.md)

- tests/behavior/test_behavior_rule_based.py
