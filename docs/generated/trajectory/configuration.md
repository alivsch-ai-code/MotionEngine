# Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `maneuver, maneuver_params` | Manöver und seine Parameter (km/h, m, s) im Szenario | – | – |
| `trajectory_file, trajectory_options` | Importdatei und Optionen (z. B. speed, road_id, lane_id) | – | – |

## Parameter von [Beschleunigen (0-100 km/h)](components/maneuver__acceleration.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `target_kmh` | Zielgeschwindigkeit | km/h | 100 | – | – |
| `request` | Angeforderte Beschleunigung | m/s² | 12 | – | – |

## Parameter von [Bremsen in der Kurve (ISO 7975)](components/maneuver__brake_in_turn.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `radius` | Radius | m | 100 | – | – |
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `deceleration` | Verzögerung | m/s² | 4 | – | – |
| `brake_time` | Bremsbeginn | s | 6 | – | – |

## Parameter von [Bremsen (Geradeaus)](components/maneuver__braking.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Anfangsgeschwindigkeit | km/h | 100 | – | – |
| `deceleration` | Verzögerung | m/s² | 10 | – | – |
| `brake_time` | Bremsbeginn | s | 1 | – | – |

## Parameter von [Kreisfahrt (ISO 4138)](components/maneuver__circle.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `radius` | Radius | m | 40 | – | – |
| `laps` | Runden | - | 3 | – | – |
| `speed_start_kmh` | Startgeschwindigkeit | km/h | 20 | – | – |
| `speed_end_kmh` | Endgeschwindigkeit | km/h | 70 | – | – |

## Parameter von [Stadtverkehr](components/maneuver__city.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Höchstgeschwindigkeit | km/h | 50 | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 2.5 | – | – |

## Parameter von [Kundenspezifischer Testzyklus](components/maneuver__custom.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `segments` | Segmente (JSON) | – | [["straight", 100, 50], ["turn", 30, 90, 40], ["straight"… | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 4 | – | – |

## Parameter von [Notausweichen](components/maneuver__emergency_evasion.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 60 | – | – |
| `offset` | Ausweichversatz | m | 3 | – | – |
| `evade_length` | Ausweichstrecke | m | 22 | – | – |
| `hold_length` | Haltestrecke | m | 8 | – | – |
| `return_length` | Rückkehrstrecke | m | 28 | – | – |

## Parameter von [Acht](components/maneuver__figure_eight.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `radius` | Radius | m | 20 | – | – |
| `speed_kmh` | Geschwindigkeit | km/h | 30 | – | – |
| `laps` | Durchgänge | - | 1 | – | – |

## Parameter von [Frequenzgang (Sinus-Sweep)](components/maneuver__frequency_sweep.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `amplitude_deg` | Lenkradamplitude | ° | 20 | – | – |
| `f_start` | Startfrequenz | Hz | 0.1 | – | – |
| `f_end` | Endfrequenz | Hz | 3 | – | – |
| `duration` | Dauer | s | 30 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Parameter von [Autobahnfahrt](components/maneuver__highway.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Richtgeschwindigkeit | km/h | 130 | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 2 | – | – |

## Parameter von [ISO-Doppelspurwechsel (ISO 3888-1)](components/maneuver__iso_double_lane_change.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `vehicle_width` | Fahrzeugbreite | m | 1.85 | – | – |

## Parameter von [ISO-Ausweichtest (ISO 3888-2)](components/maneuver__iso_obstacle_avoidance.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Einfahrgeschwindigkeit | km/h | 60 | – | – |
| `vehicle_width` | Fahrzeugbreite | m | 1.85 | – | – |

## Parameter von [Spurwechsel](components/maneuver__lane_change.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 120 | – | – |
| `width` | Querversatz | m | 3.5 | – | – |
| `duration` | Dauer | s | 6 | – | – |
| `pre_length` | Vorlauf | m | 40 | – | – |
| `post_length` | Nachlauf | m | 150 | – | – |

## Parameter von [Rennstrecke (Ideallinie)](components/maneuver__race_track.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `track_width` | Streckenbreite | m | 12 | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 7 | – | – |
| `ax_max` | Max. Längsbeschleunigung | m/s² | 3.5 | – | – |
| `ax_min` | Max. Verzögerung | m/s² | -6.5 | – | – |
| `v_max_kmh` | Höchstgeschwindigkeit | km/h | 230 | – | – |
| `laps` | Runden | - | 1 | – | – |

## Parameter von [Lenkwinkelrampe (ISO 4138)](components/maneuver__ramp_steer.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `steer_rate_deg` | Lenkradwinkelgeschwindigkeit | °/s | 8 | – | – |
| `duration` | Dauer | s | 20 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Parameter von [Sinus mit Haltezeit (FMVSS 126)](components/maneuver__sine_with_dwell.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `amplitude_deg` | Lenkradamplitude | ° | 180 | – | – |
| `frequency` | Frequenz | Hz | 0.7 | – | – |
| `dwell` | Haltezeit | s | 0.5 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Parameter von [Slalom](components/maneuver__slalom.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 45 | – | – |
| `spacing` | Pylonenabstand | m | 18 | – | – |
| `n_cones` | Anzahl Pylonen | - | 8 | – | – |
| `amplitude` | Seitlicher Abstand | m | 1.3 | – | – |

## Parameter von [Lenkwinkelsprung (ISO 7401)](components/maneuver__step_steer.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `speed_kmh` | Geschwindigkeit | km/h | 80 | – | – |
| `steering_wheel_deg` | Lenkradwinkel | ° | 40 | – | – |
| `rise_time` | Anstiegszeit | s | 0.15 | – | – |
| `duration` | Dauer | s | 6 | – | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | – | – |

## Parameter von [Geradeausfahrt](components/maneuver__straight.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `length` | Länge | m | 300 | – | – |
| `speed_kmh` | Geschwindigkeit | km/h | 50 | – | – |

## Parameter von [trajectory_loader/csv](components/trajectory_loader__csv.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |

## Parameter von [trajectory_loader/gpx](components/trajectory_loader__gpx.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |

## Parameter von [trajectory_loader/json](components/trajectory_loader__json.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |

## Parameter von [trajectory_loader/matlab](components/trajectory_loader__matlab.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |

## Parameter von [trajectory_loader/nmea](components/trajectory_loader__nmea.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |

## Parameter von [trajectory_loader/opendrive](components/trajectory_loader__opendrive.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |
| `road_id` | – | – | – | – | – |
| `lane_id` | – | – | -1 | – | – |

## Parameter von [trajectory_loader/ros](components/trajectory_loader__ros.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `path` | – | – | – | – | – |
| `speed` | – | – | – | – | – |

## Konfigurationsdateien, die Komponenten dieses Pakets verwenden

| Datei | Titel | Komponenten |
|---|---|---|
| [configs/ad_scenarios/kreuzung_ampel_geradeaus.json](../../../configs/ad_scenarios/kreuzung_ampel_geradeaus.json) | kreuzung_ampel_geradeaus | `maneuver/straight` |
| [configs/scenarios/acht_30.json](../../../configs/scenarios/acht_30.json) | Acht 30 km/h | `maneuver/figure_eight` |
| [configs/scenarios/autobahn_acc.json](../../../configs/scenarios/autobahn_acc.json) | Autobahn mit ACC | `maneuver/straight` |
| [configs/scenarios/autobahn_spurhalteassistent.json](../../../configs/scenarios/autobahn_spurhalteassistent.json) | Autobahn mit Spurhalteassistent | `maneuver/highway` |
| [configs/scenarios/beschleunigen_0_100_ev.json](../../../configs/scenarios/beschleunigen_0_100_ev.json) | Beschleunigung 0-100 km/h (E-Antrieb) | `maneuver/acceleration` |
| [configs/scenarios/bremsen_100_abs.json](../../../configs/scenarios/bremsen_100_abs.json) | Vollbremsung 100 km/h (ABS) | `maneuver/braking` |
| [configs/scenarios/bremsen_in_der_kurve.json](../../../configs/scenarios/bremsen_in_der_kurve.json) | Bremsen in der Kurve | `maneuver/brake_in_turn` |
| [configs/scenarios/bremsen_split_mu.json](../../../configs/scenarios/bremsen_split_mu.json) | Bremsen auf Split-µ | `maneuver/braking` |
| [configs/scenarios/frequenzgang_80.json](../../../configs/scenarios/frequenzgang_80.json) | Frequenzgang 80 km/h | `maneuver/frequency_sweep` |
| [configs/scenarios/iso_ausweichtest_60.json](../../../configs/scenarios/iso_ausweichtest_60.json) | ISO-Ausweichtest 60 km/h | `maneuver/iso_obstacle_avoidance` |
| [configs/scenarios/iso_doppelspurwechsel_80.json](../../../configs/scenarios/iso_doppelspurwechsel_80.json) | ISO-Doppelspurwechsel 80 km/h | `maneuver/iso_double_lane_change` |
| [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../configs/scenarios/iso_doppelspurwechsel_mpc.json) | ISO-Doppelspurwechsel 80 km/h (MPC) | `maneuver/iso_double_lane_change` |
| [configs/scenarios/komfort_strasse_klasse_c.json](../../../configs/scenarios/komfort_strasse_klasse_c.json) | Komfort Straße Klasse C | `maneuver/straight` |
| [configs/scenarios/kreisfahrt_r40.json](../../../configs/scenarios/kreisfahrt_r40.json) | Kreisfahrt R = 40 m | `maneuver/circle` |
| [configs/scenarios/lenkwinkelsprung_80.json](../../../configs/scenarios/lenkwinkelsprung_80.json) | Lenkwinkelsprung 80 km/h | `maneuver/step_steer` |
| [configs/scenarios/notausweichen_60.json](../../../configs/scenarios/notausweichen_60.json) | Notausweichen 60 km/h | `maneuver/emergency_evasion` |
| [configs/scenarios/notbremsassistent_70.json](../../../configs/scenarios/notbremsassistent_70.json) | Notbremsassistent 70 km/h | `maneuver/straight` |
| [configs/scenarios/rennstrecke_sportwagen.json](../../../configs/scenarios/rennstrecke_sportwagen.json) | Rennstrecke Sportwagen | `maneuver/race_track` |
| [configs/scenarios/sinus_haltezeit_esp.json](../../../configs/scenarios/sinus_haltezeit_esp.json) | Sinus mit Haltezeit (ESP) | `maneuver/sine_with_dwell` |
| [configs/scenarios/slalom_45.json](../../../configs/scenarios/slalom_45.json) | Slalom 45 km/h | `maneuver/slalom` |
| [configs/scenarios/spurwechsel_latenzkette.json](../../../configs/scenarios/spurwechsel_latenzkette.json) | Spurwechsel mit Latenzkette | `maneuver/lane_change` |
| [configs/scenarios/stadtverkehr.json](../../../configs/scenarios/stadtverkehr.json) | Stadtverkehr | `maneuver/city` |
| [configs/scenarios/testzyklus_kunde.json](../../../configs/scenarios/testzyklus_kunde.json) | Kundenspezifischer Testzyklus | `maneuver/custom` |
