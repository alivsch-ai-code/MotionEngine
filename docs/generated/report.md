# Prüfbericht

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

78 Referenzen definiert, 83 verwendet.

## Fehlende Referenz-IDs

IDs, die in `ComponentDoc.references`, `@trace`, module.yaml, theory.md oder links.yaml vorkommen, aber in `docs/references/*.yaml` fehlen. Das ist ein Hinweis, kein Fehler (Pakete sind teils noch in Arbeit).

| ID | verwendet in |
|---|---|
| `asam_openscenario` | component:world/scenario_engine |
| `bar_shalom2001` | component:perception/object_sensor |
| `gottschalk1996` | @trace:vdsim.world.collision.sat_overlap, component:world/scenario_engine |
| `kesting2007` | @trace:vdsim.behavior.rule_based.RuleBasedBehavior._lane_change_eval, @trace:vdsim.world.traffic_models.mobil_incentive, component:behavior_planner/rule_based, component:world/scenario_engine |
| `stvo` | component:behavior_planner/rule_based |
| `treiber2000` | @trace:vdsim.world.traffic_models.idm_acceleration, component:behavior_planner/rule_based, component:world/scenario_engine |
| `vdsim` | @trace:vdsim.perception.sensor.visibility |

## Prüfung der Referenzdatenbank

- `[error] ieee754_2019: Pflichtfeld fehlt: number oder organization (matlab.yaml)`
- `[error] iso_cpp17: Pflichtfeld fehlt: number oder organization (matlab.yaml)`

## Hinweise des Sammlers

- `Konzept 'acc' ohne theory.md-Abschnitt`
- `Konzept 'anti_windup' ohne theory.md-Abschnitt`
- `Konzept 'backstepping' ohne theory.md-Abschnitt`
- `Konzept 'behavior_state_machine' ohne theory.md-Abschnitt`
- `Konzept 'bellman_principle' mehrfach dokumentiert (vdsim/planning/docs/theory.md, vdsim/research/docs/theory.md)`
- `Konzept 'box_restriction' ohne theory.md-Abschnitt`
- `Konzept 'ca_prediction' ohne theory.md-Abschnitt`
- `Konzept 'composite' ohne theory.md-Abschnitt`
- `Konzept 'continuous_curvature_road' ohne theory.md-Abschnitt`
- `Konzept 'cv_prediction' ohne theory.md-Abschnitt`
- `Konzept 'desm' ohne theory.md-Abschnitt`
- `Konzept 'dynamic_reference_transform' ohne theory.md-Abschnitt`
- `Konzept 'feedforward' ohne theory.md-Abschnitt`
- `Konzept 'flat_reference_transform' ohne theory.md-Abschnitt`
- `Konzept 'frenet_frame' ohne theory.md-Abschnitt`
- `Konzept 'frenet_transformation' mehrfach dokumentiert (vdsim/geometry/docs/theory.md, vdsim/planning/docs/theory.md)`
- `Konzept 'hazard_indicator' ohne theory.md-Abschnitt`
- `Konzept 'idm' ohne theory.md-Abschnitt`
- `Konzept 'invariant_tracking_error' ohne theory.md-Abschnitt`
- `Konzept 'lane_following_prediction' ohne theory.md-Abschnitt`
- `Konzept 'lateral_intent' ohne theory.md-Abschnitt`
- `Konzept 'lqr_lateral' ohne theory.md-Abschnitt`
- `Konzept 'matlab_analysis' ohne theory.md-Abschnitt`
- `Konzept 'matlab_codegen' ohne theory.md-Abschnitt`
- `Konzept 'matlab_codegen_verification' ohne theory.md-Abschnitt`
- `Konzept 'matlab_control_structure' ohne theory.md-Abschnitt`
- `Konzept 'matlab_import' ohne theory.md-Abschnitt`
- `Konzept 'matlab_interpreter' ohne theory.md-Abschnitt`
- `Konzept 'matlab_parser' ohne theory.md-Abschnitt`
- `Konzept 'matlab_type_inference' ohne theory.md-Abschnitt`
- `Konzept 'mobil' ohne theory.md-Abschnitt`
- `Konzept 'mpc_lateral' ohne theory.md-Abschnitt`
- `Konzept 'pid' ohne theory.md-Abschnitt`
- `Konzept 'sat_collision' ohne theory.md-Abschnitt`
- `Konzept 'scenario_engine' ohne theory.md-Abschnitt`
- `Konzept 'sensor_model' ohne theory.md-Abschnitt`
- `Konzept 'stanley' ohne theory.md-Abschnitt`
- `Konzept 'steering_actuator' ohne theory.md-Abschnitt`
- `Konzept 'vehicle_plant' ohne theory.md-Abschnitt`
- `Konzept 'zero_dynamics_desm' ohne theory.md-Abschnitt`
- `Konzept 'zero_dynamics_kesm' ohne theory.md-Abschnitt`
- `Paket 'ad' ohne vdsim/ad/docs/module.yaml (automatischer Stub)`
- `Paket 'api' ohne vdsim/api/docs/module.yaml (automatischer Stub)`
- `Paket 'behavior' ohne vdsim/behavior/docs/module.yaml (automatischer Stub)`
- `Paket 'perception' ohne vdsim/perception/docs/module.yaml (automatischer Stub)`
- `Paket 'prediction' ohne vdsim/prediction/docs/module.yaml (automatischer Stub)`
- `Paket 'world' ohne vdsim/world/docs/module.yaml (automatischer Stub)`
- `vdsim/matlab/docs/module.yaml: Beispiel 'examples/matlab/README.md' nicht gefunden`
