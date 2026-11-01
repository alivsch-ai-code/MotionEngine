# prediction – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

_Keine Validierungsangaben in module.yaml._

## Tests, die dieses Paket verwenden

### [tests/behavior/test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py)

Komponenten: `predictor/constant_acceleration`

| Testfunktion | Beschreibung |
|---|---|
| `test_following_after_cut_in` | – |
| `test_merge_selects_gap_and_moves_reference` | – |
| `test_stop_at_red_light` | – |
| `test_box_restriction_markings` | – |
| `test_parking_direction_change_only_at_standstill` | – |
| `test_hazard_indicator_postpones_lane_change` | – |

### [tests/prediction/test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py)

Importiert: `vdsim.prediction`, `vdsim.prediction.predictors`

Komponenten: `predictor/constant_acceleration`, `predictor/constant_velocity`, `predictor/lane_following`

| Testfunktion | Beschreibung |
|---|---|
| `test_ca_exact_and_clamped` | – |
| `test_ca_frenet_along_lane` | – |
| `test_cv_and_lane_following` | – |

## Validierung von [predictor/constant_acceleration](components/predictor__constant_acceleration.md)

- tests/prediction/test_prediction_predictors.py

## Validierung von [predictor/constant_velocity](components/predictor__constant_velocity.md)

- tests/prediction/test_prediction_predictors.py

## Validierung von [predictor/lane_following](components/predictor__lane_following.md)

- tests/prediction/test_prediction_predictors.py
