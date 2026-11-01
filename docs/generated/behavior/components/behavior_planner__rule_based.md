# Regelbasierte Verhaltensplanung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [behavior](../index.md) · `behavior_planner/rule_based` · Version 1.0.0

**Zustandsautomat für Spurhalten, Spurwechsel, Einfädeln, Überholen, Kreuzung/Kreisverkehr und Einparken; erzeugt Referenzkurve, Längsmodi und Box-Restriktion für den Trajektorienplaner.**

## Zweck

Verhaltensebene nach Werling 3.6: Sollvorgaben so wählen, dass die reaktive Trajektorienplanung möglichst selten eine Kollision vermeiden muss.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `behavior_planner` |
| Name | `rule_based` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.behavior.rule_based.RuleBasedBehavior`](../../../../vdsim/behavior/rule_based.py#L49) |
| Schnittstelle | – |
| Sprache | python |
| Periode | 0.1 s |
| Direkter Durchgriff | ja |

## Ports

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

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_lat_max` | max. Querbeschleunigung (Kurvengeschwindigkeit) | m/s² | 2 | 0.5 | 8 |
| `b_comf` | Vorausschau-Verzögerung (Tempolimit, Kurven) | m/s² | 1.5 | 0.3 | 5 |
| `speed_lookahead` | Vorausschau Geschwindigkeit | m | 250 | 20 | 1000 |
| `k0` | Folgen: Mindestabstand k0 (Stoßstange) | m | 5 | 0.5 | 30 |
| `kv` | Folgen: Zeitlücke kv | s | 1.2 | 0.2 | 4 |
| `lead_lookahead_time` | Vorausschau Vorderfahrzeug | s | 6 | 1 | 20 |
| `lead_lookahead_min` | min. Vorausschau Vorderfahrzeug | m | 60 | 10 | 300 |
| `lateral_margin` | Querzuschlag Fahrschlauch | m | 0.3 | 0 | 2 |
| `intrusion_time` | Prädiktionszeit für Einscherer | s | 2 | 0 | 6 |
| `clearance_vru` | Seitenabstand Rad/Fußgänger (StVO §5) | m | 1.5 | 0.3 | 3 |
| `clearance_static` | Seitenabstand stehende Objekte | m | 0.5 | 0.1 | 3 |
| `max_pass_offset` | max. Versatz d_ref zum Vorbeifahren | m | 1.5 | 0 | 4 |
| `lc_politeness` | Spurwechsel: Höflichkeit p | - | 0.2 | 0 | 1 |
| `lc_threshold` | Spurwechsel: Schwelle Δa_th | m/s² | 0.3 | 0 | 3 |
| `lc_bias_right` | Spurwechsel: Rechtsfahrgebot | m/s² | 0.25 | 0 | 2 |
| `lc_b_safe` | Spurwechsel: zumutbare Verzögerung des Hintermanns | m/s² | 3 | 0.5 | 9 |
| `lc_safety_horizon` | Spurwechsel: Prüfhorizont der Prädiktion | s | 4 | 0.5 | 10 |
| `lc_gap_min` | Spurwechsel: Mindestlücke | m | 3 | 0 | 30 |
| `lc_front_time` | Spurwechsel: Zeitlücke nach vorn | s | 0.6 | 0 | 3 |
| `lc_rear_time` | Spurwechsel: Zeitlücke nach hinten | s | 0.8 | 0 | 3 |
| `lc_cooldown` | Spurwechsel: Sperrzeit | s | 4 | 0 | 30 |
| `lc_done_d` | Spurwechsel abgeschlossen bei \|d\| < | m | 0.4 | 0.05 | 2 |
| `lc_abort_unsafe` | unsicheren Spurwechsel vor Spurgrenze abbrechen | – | True | – | – |
| `lc_min_speed` | min. Geschwindigkeit für Spurwechsel | m/s | 5 | 0 | 30 |
| `exit_prepare_distance` | Ausfahrt: Vorbereitungsstrecke je Spur | m | 800 | 50 | 5000 |
| `adopt_time` | Spurübernahme nach Ausweichen | s | 1 | 0.1 | 10 |
| `idm_a` | Ego-IDM: Beschleunigung | m/s² | 1.5 | 0.1 | 5 |
| `idm_b` | Ego-IDM: komfortable Verzögerung | m/s² | 2 | 0.1 | 9 |
| `idm_T` | Ego-IDM: Zeitlücke | s | 1.2 | 0.1 | 5 |
| `idm_s0` | Ego-IDM: Mindestabstand | m | 3 | 0 | 20 |
| `overtake_min_dv` | Überholen: min. Geschwindigkeitsvorteil | m/s | 3 | 0.5 | 20 |
| `overtake_margin_time` | Überholen: Sicherheitszeit Gegenverkehr | s | 3 | 0 | 20 |
| `overtake_return_gap` | Überholen: Abstand vor dem Wiedereinscheren | m | 10 | 0 | 100 |
| `overtake_max_distance` | Überholen: max. Überholweg | m | 600 | 50 | 3000 |
| `merge_horizon` | Einfädeln: max. Planungshorizont | s | 8 | 1 | 30 |
| `merge_margin` | Einfädeln: Sicherheitsabstand in der Lücke | m | 3 | 0 | 20 |
| `merge_time_gap` | Einfädeln: Zeitlücke je Seite | s | 0.6 | 0 | 3 |
| `merge_a_max` | Einfädeln: max. Beschleunigung | m/s² | 3 | 0.1 | 5 |
| `merge_a_min` | Einfädeln: max. Verzögerung | m/s² | -3 | -9 | 0 |
| `merge_switch_time` | Einfädeln: Vorausschau für Referenzwechsel | s | 2 | 0 | 10 |
| `merge_hysteresis` | Einfädeln: Hysterese Lückenwahl | m/s² | 0.5 | 0 | 5 |
| `stop_margin` | Anhalten: Abstand vor der Haltelinie | m | 1 | 0 | 10 |
| `yield_gap_time` | Vorfahrt: Zeitreserve der Lücke | s | 2 | 0 | 10 |
| `stop_hold` | Stoppschild: Haltezeit | s | 1 | 0 | 10 |
| `yellow_decel` | Gelb: max. Verzögerung zum Anhalten | m/s² | 3 | 0.5 | 9 |
| `standstill_v` | Stillstandsschwelle | m/s | 0.1 | 0.01 | 1 |
| `end_of_lane_margin` | Anhalten vor Spurende | m | 5 | 0 | 50 |
| `park_hold` | Einparken: Haltezeit vor Richtungswechsel | s | 0.5 | 0 | 10 |
| `park_tol` | Einparken: Positionstoleranz | m | 0.6 | 0.05 | 3 |
| `box_lookahead_time` | Korridor: Vorausschau | s | 2 | 0 | 10 |
| `use_opposite_lane` | Gegenfahrbahn bei gestrichelter Linie im Korridor | – | True | – | – |
| `use_parking_lane` | Parkstreifen im Korridor | – | True | – | – |
| `hazard_cost_threshold` | Gefahrenindikator: Kostenschwelle | - | 1e+06 | 0 | – |
| `hazard_on_invalid` | Gefahrenindikator: ungültige Trajektorie | – | True | – | – |
| `hazard_hold` | Gefahrenindikator: Spurwechselsperre | s | 1 | 0 | 10 |
| `route_ahead` | Länge der Referenzkurve voraus | m | 1500 | 100 | 10000 |

## Theorie

Spurwechsel MOBIL-artig: $\tilde a_c - a_c + p(\tilde a_n - a_n) \pm a_{bias} > \Delta a_{th}$ mit IDM-Beschleunigungen und Sicherheitsprüfung über die Prädiktion. Einfädeln: Lückenmitte $s_{ref} = \tfrac12 (s_a + s_b)$ (3.15), Lückenwahl nach erforderlicher Beschleunigung. Vorfahrt: Zeitlückenannahme mit prädizierten Konfliktzonenbelegungen.

## Verfahren

[Behavior state machine](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Box restriction](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Hazard indicator](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Einfädeln](../../planning/theory.md#merging_mode), [Mobil](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Kartenwissen (Spuren, Markierungen, Haltelinien) ist exakt bekannt
- Objekte tragen lane_id/s/d der Szenario-Engine bzw. Perception

## Einschränkungen

- keine Neuplanung der Route bei verpasster Ausfahrt
- Linksabbiegen bei Grün: einfache Zeitlückenprüfung gegen den Gegenverkehr

## Validierung

- tests/behavior/test_behavior_rule_based.py

## Umgesetzte Gleichungen

- `werling2011:(3.15)`
- `kesting2007:(3)`

## Quellen

[kesting2007 (fehlt in docs/references)](../../references.md#kesting2007), [stvo (fehlt in docs/references)](../../references.md#stvo), [treiber2000 (fehlt in docs/references)](../../references.md#treiber2000), [Werling (2011)](../../references.md#werling2011)

## Designentscheidungen

- Referenzkurve = Spurkette ab BehaviorCommand.lane_id (konsistent mit PredictedObject.s)
- Gegenfahrbahn-Überholen über d_ref statt Referenzkurvenwechsel (Werling 3.5.1)

## Erweiterungspunkte

- weitere Verhaltensplaner als Komponente der Ebene behavior_planner

## Verwendung

Tests: [tests/behavior/test_behavior_rule_based.py](../../../../tests/behavior/test_behavior_rule_based.py)
