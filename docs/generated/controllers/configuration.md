# Regler, Fahrerassistenz und Fahrwerksregelsysteme – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `lateral_controller, lateral_params` | Querregler und dessen Konstruktorparameter im Szenario | – | – |
| `longitudinal_controller, longitudinal_params` | Längsregler und dessen Parameter | – | – |
| `systems.*` | Schalter und Parameter der Regelsysteme (VehicleConfig.systems) | – | – |

## Parameter von [ABS](components/chassis_system__abs.md)

_Keine Parameter._

Zugehörige Fahrzeugparameter (`VehicleConfig`):

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.abs_enabled` | ABS aktiv | – | True | – | – |
| `systems.abs_target_slip` | ABS Zielschlupf | - | 0.12 | 0.02 | 0.4 |

## Parameter von [Aktive Dämpfung (Skyhook)](components/chassis_system__active_damping.md)

_Keine Parameter._

Zugehörige Fahrzeugparameter (`VehicleConfig`):

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.active_damping_enabled` | Aktive Dämpfung (Skyhook) aktiv | – | False | – | – |
| `systems.skyhook_gain` | Skyhook-Dämpfung | N s/m | 2500 | 0 | – |

## Parameter von [Aktive Wankstabilisierung](components/chassis_system__active_roll.md)

_Keine Parameter._

Zugehörige Fahrzeugparameter (`VehicleConfig`):

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.active_roll_enabled` | Aktive Wankstabilisierung aktiv | – | False | – | – |
| `systems.active_roll_gain` | Wankkompensationsgrad | - | 0.8 | 0 | 1.2 |

## Parameter von [ESP](components/chassis_system__esp.md)

_Keine Parameter._

Zugehörige Fahrzeugparameter (`VehicleConfig`):

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.esp_enabled` | ESP aktiv | – | False | – | – |
| `systems.esp_gain` | ESP Verstärkung Giermoment | N m s/rad | 20000 | 0 | – |
| `systems.esp_deadband` | ESP Totband Gierrate | rad/s | 0.03 | 0 | – |

## Parameter von [Hinterachslenkung](components/chassis_system__rear_steering.md)

_Keine Parameter._

Zugehörige Fahrzeugparameter (`VehicleConfig`):

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.rear_steering_enabled` | Hinterachslenkung aktiv | – | False | – | – |
| `systems.rear_steering_ratio_low` | HAL Verhältnis niedrige Geschw. (gegensinnig < 0) | - | -0.2 | -1 | 1 |
| `systems.rear_steering_ratio_high` | HAL Verhältnis hohe Geschw. (gleichsinnig > 0) | - | 0.1 | -1 | 1 |
| `systems.rear_steering_speed_low` | HAL Übergang Beginn | m/s | 8 | 0 | – |
| `systems.rear_steering_speed_high` | HAL Übergang Ende | m/s | 22 | 0 | – |

## Parameter von [Antriebsschlupfregelung (ASR/TCS)](components/chassis_system__tcs.md)

_Keine Parameter._

Zugehörige Fahrzeugparameter (`VehicleConfig`):

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.tcs_enabled` | ASR/TCS aktiv | – | True | – | – |
| `systems.tcs_target_slip` | TCS Zielschlupf | - | 0.1 | 0.02 | 0.4 |

## Parameter von [Torque Vectoring](components/chassis_system__torque_vectoring.md)

_Keine Parameter._

Zugehörige Fahrzeugparameter (`VehicleConfig`):

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `systems.torque_vectoring_enabled` | Torque Vectoring aktiv | – | False | – | – |
| `systems.torque_vectoring_gain` | Torque Vectoring Verstärkung | N m s/rad | 30000 | 0 | – |
| `systems.torque_vectoring_target` | TV Ziel-Eigenlenkverhalten (0 = neutral, 1 = passiv) | - | 0 | -0.5 | 1 |
| `powertrain.torque_vectoring_max_torque` | Torque Vectoring max. Differenzmoment (Rad) | N m | 800 | 0 | – |

## Parameter von [Spurhalteassistent (LKA)](components/lateral_controller__lane_keeping.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lane_width` | – | m | 3.75 | – | – |
| `activation_margin` | Abstand zur Markierung | m | 0.3 | – | – |
| `drift_start` | Beginn der Unaufmerksamkeit | s | 2 | – | – |
| `drift_bias_deg` | Lenkdrift des Fahrers | ° | 0.4 | – | – |
| `gain` | Verstärkung der Querablage | - | 0.6 | – | – |
| `heading_gain` | Verstärkung des Kurswinkelfehlers | - | 1.5 | – | – |
| `max_overlay_deg` | maximaler Zusatzlenkwinkel | ° | 3 | – | – |
| `enabled` | Assistent aktiv | – | True | – | – |

## Parameter von [MPC](components/lateral_controller__mpc.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Horizontlänge N in Schritten | - | 25 | – | – |
| `dt` | Diskretisierung des Vorhersagemodells | s | 0.05 | – | – |
| `q_lateral` | Gewicht der Querablage | 1/m² | 10 | – | – |
| `q_heading` | Gewicht des Kurswinkelfehlers | 1/rad² | 5 | – | – |
| `r_steer` | Gewicht des Lenkwinkels | 1/rad² | 1 | – | – |
| `r_rate` | Gewicht der Lenkwinkeländerung je Schritt | 1/rad² | 20 | – | – |
| `update_period` | Neuberechnungsperiode | s | 0.01 | – | – |

## Parameter von [Pure Pursuit](components/lateral_controller__pure_pursuit.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lookahead_gain` | Vorausschauzeit (l_d = k v) | s | 0.6 | – | – |
| `lookahead_min` | minimale Vorausschaudistanz | m | 4 | – | – |

## Parameter von [Stanley](components/lateral_controller__stanley.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `gain` | Verstärkung der Querablage k | - | 1.2 | – | – |
| `softening` | Softening-Geschwindigkeit im Nenner | m/s | 2 | – | – |
| `yaw_damping` | Gewicht der Gierratenabweichung | s | 0.05 | – | – |
| `feedforward` | Krümmungsvorsteuerung ein/aus | – | True | – | – |

## Parameter von [Abstandsregeltempomat (ACC)](components/longitudinal_controller__acc.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `time_gap` | – | s | 1.8 | – | – |
| `standstill_gap` | – | m | 5 | – | – |
| `k_gap` | – | 1/s² | 0.23 | – | – |
| `k_speed` | – | 1/s | 0.7 | – | – |
| `a_max` | – | m/s² | 2 | – | – |
| `a_min` | – | m/s² | -3.5 | – | – |

## Parameter von [Notbremsassistent (AEB)](components/longitudinal_controller__aeb.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `base` | – | – | acc | – | – |
| `ttc_warning` | – | s | 2.6 | – | – |
| `ttc_partial` | – | s | 2 | – | – |
| `ttc_full` | – | s | 1.3 | – | – |
| `partial_decel` | – | m/s² | 5 | – | – |
| `full_decel` | – | m/s² | 9.5 | – | – |

## Parameter von [Geschwindigkeitsregler (PI)](components/longitudinal_controller__speed_pi.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `kp` | – | 1/s | 1.2 | – | – |
| `ki` | – | 1/s² | 0.3 | – | – |
| `a_max` | – | m/s² | 4 | – | – |
| `a_min` | – | m/s² | -9 | – | – |
| `preview` | Vorausschauzeit der Vorsteuerung | s | 0.6 | – | – |

## Konfigurationsdateien, die Komponenten dieses Pakets verwenden

| Datei | Titel | Komponenten |
|---|---|---|
| [configs/scenarios/acht_30.json](../../../configs/scenarios/acht_30.json) | Acht 30 km/h | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/autobahn_acc.json](../../../configs/scenarios/autobahn_acc.json) | Autobahn mit ACC | `lateral_controller/stanley`, `longitudinal_controller/acc` |
| [configs/scenarios/autobahn_spurhalteassistent.json](../../../configs/scenarios/autobahn_spurhalteassistent.json) | Autobahn mit Spurhalteassistent | `lateral_controller/lane_keeping`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/beschleunigen_0_100_ev.json](../../../configs/scenarios/beschleunigen_0_100_ev.json) | Beschleunigung 0-100 km/h (E-Antrieb) | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/bremsen_100_abs.json](../../../configs/scenarios/bremsen_100_abs.json) | Vollbremsung 100 km/h (ABS) | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/bremsen_in_der_kurve.json](../../../configs/scenarios/bremsen_in_der_kurve.json) | Bremsen in der Kurve | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/bremsen_split_mu.json](../../../configs/scenarios/bremsen_split_mu.json) | Bremsen auf Split-µ | `chassis_system/esp`, `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/frequenzgang_80.json](../../../configs/scenarios/frequenzgang_80.json) | Frequenzgang 80 km/h | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/iso_ausweichtest_60.json](../../../configs/scenarios/iso_ausweichtest_60.json) | ISO-Ausweichtest 60 km/h | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/iso_doppelspurwechsel_80.json](../../../configs/scenarios/iso_doppelspurwechsel_80.json) | ISO-Doppelspurwechsel 80 km/h | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../configs/scenarios/iso_doppelspurwechsel_mpc.json) | ISO-Doppelspurwechsel 80 km/h (MPC) | `lateral_controller/mpc`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/komfort_strasse_klasse_c.json](../../../configs/scenarios/komfort_strasse_klasse_c.json) | Komfort Straße Klasse C | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/kreisfahrt_r40.json](../../../configs/scenarios/kreisfahrt_r40.json) | Kreisfahrt R = 40 m | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/lenkwinkelsprung_80.json](../../../configs/scenarios/lenkwinkelsprung_80.json) | Lenkwinkelsprung 80 km/h | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/notausweichen_60.json](../../../configs/scenarios/notausweichen_60.json) | Notausweichen 60 km/h | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/notbremsassistent_70.json](../../../configs/scenarios/notbremsassistent_70.json) | Notbremsassistent 70 km/h | `lateral_controller/stanley`, `longitudinal_controller/aeb`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/rennstrecke_sportwagen.json](../../../configs/scenarios/rennstrecke_sportwagen.json) | Rennstrecke Sportwagen | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/sinus_haltezeit_esp.json](../../../configs/scenarios/sinus_haltezeit_esp.json) | Sinus mit Haltezeit (ESP) | `chassis_system/esp`, `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/slalom_45.json](../../../configs/scenarios/slalom_45.json) | Slalom 45 km/h | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/spurwechsel_latenzkette.json](../../../configs/scenarios/spurwechsel_latenzkette.json) | Spurwechsel mit Latenzkette | `lateral_controller/curvature_feedforward`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/stadtverkehr.json](../../../configs/scenarios/stadtverkehr.json) | Stadtverkehr | `lateral_controller/mpc`, `longitudinal_controller/speed_pi` |
| [configs/scenarios/testzyklus_kunde.json](../../../configs/scenarios/testzyklus_kunde.json) | Kundenspezifischer Testzyklus | `lateral_controller/stanley`, `longitudinal_controller/speed_pi` |
| [configs/vehicles/ev_sedan.json](../../../configs/vehicles/ev_sedan.json) | ev_sedan | `chassis_system/abs`, `chassis_system/tcs` |
| [configs/vehicles/mid_size_sedan.json](../../../configs/vehicles/mid_size_sedan.json) | mid_size_sedan | `chassis_system/abs`, `chassis_system/tcs` |
| [configs/vehicles/sports_car.json](../../../configs/vehicles/sports_car.json) | sports_car | `chassis_system/abs`, `chassis_system/tcs` |
| [configs/vehicles/suv.json](../../../configs/vehicles/suv.json) | suv | `chassis_system/abs`, `chassis_system/tcs` |
