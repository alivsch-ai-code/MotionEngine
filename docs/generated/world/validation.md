# world – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

_Keine Validierungsangaben in module.yaml._

## Tests, die dieses Paket verwenden

### [tests/behavior/test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py)

Importiert: `vdsim.world`, `vdsim.world.scenario`

Komponenten: `world/scenario_engine`

| Testfunktion | Beschreibung |
|---|---|
| `test_following_after_cut_in` | – |
| `test_merge_selects_gap_and_moves_reference` | – |
| `test_stop_at_red_light` | – |
| `test_box_restriction_markings` | – |
| `test_parking_direction_change_only_at_standstill` | – |
| `test_hazard_indicator_postpones_lane_change` | – |

### [tests/prediction/test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py)

Importiert: `vdsim.world.road_builders`

| Testfunktion | Beschreibung |
|---|---|
| `test_ca_exact_and_clamped` | – |
| `test_ca_frenet_along_lane` | – |
| `test_cv_and_lane_following` | – |

### [tests/world/test_world_actors.py](../../../tests/world/test_world_actors.py)

Importiert: `vdsim.world`, `vdsim.world.collision`, `vdsim.world.road`, `vdsim.world.scenario`

| Testfunktion | Beschreibung |
|---|---|
| `test_sat` | – |
| `test_traffic_light_cycle` | – |
| `test_density_no_collisions_60s` | – |
| `test_cut_in_trigger_deterministic` | – |
| `test_pedestrian_trigger` | – |
| `test_vehicles_stop_at_red_light` | – |

### [tests/world/test_world_road.py](../../../tests/world/test_world_road.py)

Importiert: `vdsim.world.road_builders`

| Testfunktion | Beschreibung |
|---|---|
| `test_connections_continuous` | – |
| `test_routes_are_single_continuous_lines` | – |
| `test_corridor_markings` | – |
| `test_lane_at_and_drivable` | – |

### [tests/world/test_world_scenarios.py](../../../tests/world/test_world_scenarios.py)

Importiert: `vdsim.world`, `vdsim.world.render`, `vdsim.world.scenario`

Komponenten: `world/scenario_engine`

| Testfunktion | Beschreibung |
|---|---|
| `test_library_complete` | – |
| `test_scenario_builds_and_renders` | – |
| `test_spec_roundtrip_and_seed` | – |
| `test_engine_collision_offroad_events` | – |
| `test_lateral_impulse_event` | – |

## Validierung von [world/scenario_engine](components/world__scenario_engine.md)

- tests/world/test_world_engine.py
- tests/world/test_world_actors.py
