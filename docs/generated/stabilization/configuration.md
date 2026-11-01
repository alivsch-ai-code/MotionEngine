# Trajektorienstabilisierung nach Werling und Fahrzeugebenen – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `werling_bilevel.c_t / c_n` | Schwellwerte des elliptischen Maßes (4.5.1), Standard 1.0 / 0.5 m/s | – | – |
| `werling_bilevel.dynamic.zeta` | Dämpfungsgrad der Nulldynamik für lambda(zeta, v_d) (4.70) | – | – |
| `configs/stabilization/*.json` | Parametersätze (Werling-Standard, klassische Regler, Fahrzeugebenen) | – | – |

## Parameter von [Lenkaktor und Antrieb/Bremse](components/actuator__steering_powertrain.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `steering` | Lenkaktor (SteeringActuatorParameters) | – | {…} | – | – |
| `max_steer_angle` | Lenkwinkelgrenze (<0: aus Fahrzeug) | rad | -1 | – | – |
| `drive_dead_time` | Totzeit Antrieb | s | 0 | 0 | – |
| `drive_tau` | PT1 Antrieb | s | 0 | 0 | – |
| `brake_dead_time` | Totzeit Bremse | s | 0 | 0 | – |
| `brake_tau` | PT1 Bremse | s | 0 | 0 | – |

## Parameter von [Abstandsregeltempomat (ACC)](components/tracking_controller__acc.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `time_gap` | Zeitlücke | s | 1.8 | 0 | – |
| `standstill_gap` | Abstand im Stand | m | 5 | 0 | – |
| `k_gap` | Verstärkung Abstandsfehler | 1/s² | 0.25 | 0 | – |
| `k_speed` | Verstärkung Relativgeschwindigkeit | 1/s | 0.7 | 0 | – |
| `k_v` | Verstärkung Wunschgeschwindigkeit | 1/s | 1 | 0 | – |
| `lead_gap0` | virtuelles Vorderfahrzeug: Startabstand (<0: keins) | m | -1 | – | – |
| `lead_speed` | virtuelles Vorderfahrzeug: Geschwindigkeit | m/s | 15 | 0 | – |
| `lane_width` | Halbbreite des Fahrschlauchs für Objekte | m | 2 | 0.1 | – |

## Parameter von [Kombination Quer- + Längsregler](components/tracking_controller__composite.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lateral` | Querregler | – | stanley | – | – |
| `longitudinal` | Längsregler | – | ff_fb | – | – |
| `lateral_params` | Parameter Querregler | – | {…} | – | – |
| `longitudinal_params` | Parameter Längsregler | – | {…} | – | – |

## Parameter von [Vorsteuerung + Rückführung (längs)](components/tracking_controller__ff_fb.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `k_v` | Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |

## Parameter von [LQR (geschwindigkeitsgeplant)](components/tracking_controller__lqr.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `q_e` | Gewicht Querfehler | 1/m² | 1 | 0 | – |
| `q_e_dot` | Gewicht Querfehlerrate | s²/m² | 0 | 0 | – |
| `q_psi` | Gewicht Kursfehler | 1/rad² | 1 | 0 | – |
| `q_psi_dot` | Gewicht Kursfehlerrate | s²/rad² | 0 | 0 | – |
| `r_delta` | Gewicht Lenkwinkel | 1/rad² | 10 | 1e-06 | – |
| `dt` | Diskretisierung | s | 0.01 | 0.001 | – |
| `v_min` | untere Stützstelle Gain-Scheduling | m/s | 2 | 0.5 | – |
| `v_max` | obere Stützstelle Gain-Scheduling | m/s | 50 | 5 | – |

## Parameter von [MPC (linear zeitvariant)](components/tracking_controller__mpc.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `horizon` | Prädiktionsschritte N | - | 20 | 3 | 100 |
| `dt` | Prädiktionsschrittweite | s | 0.05 | 0.005 | – |
| `q_e` | Gewicht Querfehler | 1/m² | 4 | 0 | – |
| `q_psi` | Gewicht Kursfehler | 1/rad² | 4 | 0 | – |
| `r_delta` | Gewicht Lenkwinkel gegenüber Vorsteuerung | 1/rad² | 1 | 0 | – |
| `r_rate` | Gewicht Lenkrate | s²/rad² | 0.5 | 1e-06 | – |
| `max_rate` | max. Lenkrate | rad/s | 0.6 | 0.01 | – |
| `max_angle` | max. Lenkwinkel (<0: Fahrzeug) | rad | -1 | – | – |
| `update_period` | Neuberechnungsperiode | s | 0.05 | 0 | – |

## Parameter von [PI-Geschwindigkeitsregler](components/tracking_controller__pi.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `kp` | K_P | 1/s | 1.5 | 0 | – |
| `ki` | K_I | 1/s² | 0.5 | 0 | – |

## Parameter von [PID-Geschwindigkeitsregler](components/tracking_controller__pid.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `kp` | K_P | 1/s | 1.5 | 0 | – |
| `ki` | K_I | 1/s² | 0.5 | 0 | – |
| `kd` | K_D | - | 0.05 | 0 | – |

## Parameter von [Pure Pursuit](components/tracking_controller__pure_pursuit.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `lookahead_gain` | Vorausschauzeit k (L_d = k v) | s | 0.8 | 0 | – |
| `lookahead_min` | minimale Vorausschau | m | 4 | 0.5 | – |

## Parameter von [Fahrzeug-Geschwindigkeitsregler (PI mit Anti-Windup)](components/tracking_controller__speed_pi.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `kp` | K_P | 1/s | 1.2 | 0 | – |
| `ki` | K_I | 1/s² | 0.4 | 0 | – |
| `k_aw` | Anti-Windup Rückrechnung | 1/s | 2 | 0 | – |
| `feedforward` | Beschleunigungsvorsteuerung a_d | – | True | – | – |

## Parameter von [Stanley](components/tracking_controller__stanley.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `gain` | Stanley-Verstärkung k | 1/s | 1.5 | 0 | – |
| `softening` | Weichmachung k_soft | m/s | 1 | 0 | – |
| `yaw_damping` | Gierratendämpfung | s | 0.08 | 0 | – |
| `feedforward` | Krümmungsvorsteuerung | – | True | – | – |

## Parameter von [Werling: Bi-level-Stabilisierung (Umschaltung + Reinitialisierung)](components/tracking_controller__werling_bilevel.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `v_switch` | Umschaltgeschwindigkeit v_s | m/s | 3 | 0.5 | 15 |
| `v_min_dynamic` | Mindestgeschwindigkeit des dynamischen Reglers | m/s | 1 | 0.1 | – |
| `forward_slow` | Regler langsam vorwärts: center / orientation | – | center | – | – |
| `c_t` | Schwellwert c_t (Längsfehleränderung) | m/s | 1 | 0.01 | – |
| `c_n` | Schwellwert c_n (Querfehleränderung) | m/s | 0.5 | 0.01 | – |
| `e_t_max` | absoluter Längsfehler e_max (0 = aus) | m | 0 | 0 | – |
| `e_n_max` | absoluter Querfehler e_max (0 = aus) | m | 0 | 0 | – |
| `e_theta_max` | absoluter Orientierungsfehler (0 = aus) | rad | 0 | 0 | – |
| `reinit_enabled` | Reinitialisierungsauslösung aktiv | – | True | – | – |
| `cooldown` | Sperrzeit nach einer Reinitialisierung | s | 0.3 | 0 | – |
| `max_hold` | max. Haltedauer der Anforderung | s | 0.5 | 0 | – |
| `prediction_dt` | Prädiktionszeit Delta t (Planungslatenz) | s | 0.1 | 0 | 1 |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |
| `orientation` | Parameter Satz 4 | – | {…} | – | – |
| `center` | Parameter Satz 6 | – | {…} | – | – |
| `dynamic` | Parameter Satz 8 | – | {…} | – | – |

## Parameter von [Werling: exakte E/A-Linearisierung (Satz 8)](components/tracking_controller__werling_dynamic.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `zeta` | Dämpfungsgrad der Nulldynamik zeta (4.70) | - | 1 | 0.3 | 3 |
| `lam_fixed` | festes lambda (< -50: geschwindigkeitsabhängig nach (4.70)) | m | -100 | – | – |
| `lam_min` | minimales lambda | m | 0 | -1.5 | 30 |
| `lam_max` | maximales lambda | m | 20 | 0 | 50 |
| `lam_rate` | max. Änderungsrate von lambda | m/s | 4 | 0 | – |
| `pole_n1` | Pol 1 Querfehler | 1/s | -1.18 | – | 0 |
| `pole_n2` | Pol 2 Querfehler | 1/s | -3.82 | – | 0 |
| `pole_t1` | Pol 1 Längsfehler | 1/s | -0.29 | – | 0 |
| `pole_t2` | Pol 2 Längsfehler | 1/s | -1.71 | – | 0 |
| `k_delta` | Lenkwinkel-Rückführung k_delta (4.75) | 1/s | 10 | 0 | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `saturation_exponent` | Exponent n der Sättigungsmodifikation | - | 16 | 2 | 60 |
| `reference_transform` | Sollgrößentransformation: dynamic / static / none | – | dynamic | – | – |
| `v_floor` | Mindestgeschwindigkeit der Nulldynamik-Simulation | m/s | 1 | 0.1 | – |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Parameter von [Werling: Lyapunov ohne Orientierungsstabilisierung (Satz 6)](components/tracking_controller__werling_kinematic_center.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k1` | k~1 (Positionsfehler) | 1/m² | 0.5 | 0 | – |
| `k3` | k~3 (Geschwindigkeitsfehler) | 1/s | 2 | 0 | – |
| `k4` | k~4 (Kurswinkelfehler) | 1/s | 5 | 0 | – |
| `lam` | Abstand lambda von der Hinterachse (<0: l/2) | m | -1 | – | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `taylor_switch` | Grenze Taylor-Näherung | rad | 0.5 | 0 | 1.5 |
| `sign_variant` | Vorzeichen in (4.31): proof / printed | – | proof | – | – |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Parameter von [Werling: Lyapunov mit Orientierungsstabilisierung (Satz 4)](components/tracking_controller__werling_kinematic_orientation.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k1` | k1 (Positionsfehler) | 1/m² | 0.5 | 0 | – |
| `k2` | k2 (Orientierungsfehler) | 1/m | 2 | 0 | – |
| `k3` | k3 (Geschwindigkeitsfehler) | 1/s | 2 | 0 | – |
| `k4` | k4 (Lenkfehler, Backstepping) | 1/s | 10 | 0 | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `taylor_switch` | Grenze Taylor-Näherung | rad | 0.5 | 0 | 1.5 |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Parameter von [Split-Range-Längskraftumsetzung (Werling 5.1.2.2)](components/vehicle_dynamics__split_range.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_i` | Integratorverstärkung k_I (Beschleunigungsfehler) | 1/s | 0.5 | 0 | – |
| `integrator_limit` | Integratorgrenze (Anteil von m g) | - | 0.3 | 0 | 1 |
| `compensate_resistance` | Fahrwiderstand F_W(v) kompensieren | – | True | – | – |
| `gamma_brake` | Bremskraftverteilung vorne gamma | - | 0.75 | 0 | 1 |
| `max_decel` | max. Verzögerung | m/s² | 10 | 0 | – |
| `regen` | Rekuperation über den E-Antrieb (nur EV) | – | False | – | – |
| `systems` | Fahrdynamiksysteme (esp, abs, tcs, torque_vectoring) | – | [] | – | – |
| `integrator_min_speed` | Integrator nur oberhalb \|v\| bzw. bei Sollbeschleunigung | m/s | 0.3 | 0 | – |

## Parameter von [Fahrzeugmodell (vdsim)](components/vehicle_plant__vehicle_model.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `model` | Fahrzeugmodell (vdsim vehicle_model) | – | werling_desm | – | – |
| `solver` | Integrator | – | rk4 | – | – |
| `dt_model` | Modellschrittweite (0: Empfehlung des Modells) | s | 0 | 0 | – |
| `x0` | Startposition x (falls kein Szenario) | m | 0 | – | – |
| `y0` | Startposition y | m | 0 | – | – |
| `psi0` | Start-Gierwinkel | rad | 0 | – | – |
| `v0` | Startgeschwindigkeit (vorzeichenbehaftet) | m/s | 0 | – | – |
| `delta0` | Start-Lenkwinkel | rad | 0 | – | – |
| `disturbances` | Störkräfte [{t, duration, fx, fy, mz}] | – | [] | – | – |

## Parametersatz `_SpeedLoopParams` (`vdsim.stabilization.classic_lateral`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |

## Parametersatz `PurePursuitParams` (`vdsim.stabilization.classic_lateral`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `lookahead_gain` | Vorausschauzeit k (L_d = k v) | s | 0.8 | 0 | – |
| `lookahead_min` | minimale Vorausschau | m | 4 | 0.5 | – |

## Parametersatz `StanleyParams` (`vdsim.stabilization.classic_lateral`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `gain` | Stanley-Verstärkung k | 1/s | 1.5 | 0 | – |
| `softening` | Weichmachung k_soft | m/s | 1 | 0 | – |
| `yaw_damping` | Gierratendämpfung | s | 0.08 | 0 | – |
| `feedforward` | Krümmungsvorsteuerung | – | True | – | – |

## Parametersatz `LQRParams` (`vdsim.stabilization.classic_lateral`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `q_e` | Gewicht Querfehler | 1/m² | 1 | 0 | – |
| `q_e_dot` | Gewicht Querfehlerrate | s²/m² | 0 | 0 | – |
| `q_psi` | Gewicht Kursfehler | 1/rad² | 1 | 0 | – |
| `q_psi_dot` | Gewicht Kursfehlerrate | s²/rad² | 0 | 0 | – |
| `r_delta` | Gewicht Lenkwinkel | 1/rad² | 10 | 1e-06 | – |
| `dt` | Diskretisierung | s | 0.01 | 0.001 | – |
| `v_min` | untere Stützstelle Gain-Scheduling | m/s | 2 | 0.5 | – |
| `v_max` | obere Stützstelle Gain-Scheduling | m/s | 50 | 5 | – |

## Parametersatz `MPCParams` (`vdsim.stabilization.classic_lateral`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `horizon` | Prädiktionsschritte N | - | 20 | 3 | 100 |
| `dt` | Prädiktionsschrittweite | s | 0.05 | 0.005 | – |
| `q_e` | Gewicht Querfehler | 1/m² | 4 | 0 | – |
| `q_psi` | Gewicht Kursfehler | 1/rad² | 4 | 0 | – |
| `r_delta` | Gewicht Lenkwinkel gegenüber Vorsteuerung | 1/rad² | 1 | 0 | – |
| `r_rate` | Gewicht Lenkrate | s²/rad² | 0.5 | 1e-06 | – |
| `max_rate` | max. Lenkrate | rad/s | 0.6 | 0.01 | – |
| `max_angle` | max. Lenkwinkel (<0: Fahrzeug) | rad | -1 | – | – |
| `update_period` | Neuberechnungsperiode | s | 0.05 | 0 | – |

## Parametersatz `_LongParams` (`vdsim.stabilization.classic_longitudinal`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |

## Parametersatz `PIDParams` (`vdsim.stabilization.classic_longitudinal`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `kp` | K_P | 1/s | 1.5 | 0 | – |
| `ki` | K_I | 1/s² | 0.5 | 0 | – |
| `kd` | K_D | - | 0.05 | 0 | – |

## Parametersatz `PIParams` (`vdsim.stabilization.classic_longitudinal`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `kp` | K_P | 1/s | 1.5 | 0 | – |
| `ki` | K_I | 1/s² | 0.5 | 0 | – |

## Parametersatz `FFFBParams` (`vdsim.stabilization.classic_longitudinal`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `k_v` | Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |

## Parametersatz `ACCParams` (`vdsim.stabilization.classic_longitudinal`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `time_gap` | Zeitlücke | s | 1.8 | 0 | – |
| `standstill_gap` | Abstand im Stand | m | 5 | 0 | – |
| `k_gap` | Verstärkung Abstandsfehler | 1/s² | 0.25 | 0 | – |
| `k_speed` | Verstärkung Relativgeschwindigkeit | 1/s | 0.7 | 0 | – |
| `k_v` | Verstärkung Wunschgeschwindigkeit | 1/s | 1 | 0 | – |
| `lead_gap0` | virtuelles Vorderfahrzeug: Startabstand (<0: keins) | m | -1 | – | – |
| `lead_speed` | virtuelles Vorderfahrzeug: Geschwindigkeit | m/s | 15 | 0 | – |
| `lane_width` | Halbbreite des Fahrschlauchs für Objekte | m | 2 | 0.1 | – |

## Parametersatz `SpeedPIParams` (`vdsim.stabilization.classic_longitudinal`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `kp` | K_P | 1/s | 1.2 | 0 | – |
| `ki` | K_I | 1/s² | 0.4 | 0 | – |
| `k_aw` | Anti-Windup Rückrechnung | 1/s | 2 | 0 | – |
| `feedforward` | Beschleunigungsvorsteuerung a_d | – | True | – | – |

## Parametersatz `CompositeParams` (`vdsim.stabilization.composite`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lateral` | Querregler | – | stanley | – | – |
| `longitudinal` | Längsregler | – | ff_fb | – | – |
| `lateral_params` | Parameter Querregler | – | {…} | – | – |
| `longitudinal_params` | Parameter Längsregler | – | {…} | – | – |

## Parametersatz `PlantParams` (`vdsim.stabilization.plant`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `model` | Fahrzeugmodell (vdsim vehicle_model) | – | werling_desm | – | – |
| `solver` | Integrator | – | rk4 | – | – |
| `dt_model` | Modellschrittweite (0: Empfehlung des Modells) | s | 0 | 0 | – |
| `x0` | Startposition x (falls kein Szenario) | m | 0 | – | – |
| `y0` | Startposition y | m | 0 | – | – |
| `psi0` | Start-Gierwinkel | rad | 0 | – | – |
| `v0` | Startgeschwindigkeit (vorzeichenbehaftet) | m/s | 0 | – | – |
| `delta0` | Start-Lenkwinkel | rad | 0 | – | – |
| `disturbances` | Störkräfte [{t, duration, fx, fy, mz}] | – | [] | – | – |

## Parametersatz `BilevelParams` (`vdsim.stabilization.switching`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `v_switch` | Umschaltgeschwindigkeit v_s | m/s | 3 | 0.5 | 15 |
| `v_min_dynamic` | Mindestgeschwindigkeit des dynamischen Reglers | m/s | 1 | 0.1 | – |
| `forward_slow` | Regler langsam vorwärts: center / orientation | – | center | – | – |
| `c_t` | Schwellwert c_t (Längsfehleränderung) | m/s | 1 | 0.01 | – |
| `c_n` | Schwellwert c_n (Querfehleränderung) | m/s | 0.5 | 0.01 | – |
| `e_t_max` | absoluter Längsfehler e_max (0 = aus) | m | 0 | 0 | – |
| `e_n_max` | absoluter Querfehler e_max (0 = aus) | m | 0 | 0 | – |
| `e_theta_max` | absoluter Orientierungsfehler (0 = aus) | rad | 0 | 0 | – |
| `reinit_enabled` | Reinitialisierungsauslösung aktiv | – | True | – | – |
| `cooldown` | Sperrzeit nach einer Reinitialisierung | s | 0.3 | 0 | – |
| `max_hold` | max. Haltedauer der Anforderung | s | 0.5 | 0 | – |
| `prediction_dt` | Prädiktionszeit Delta t (Planungslatenz) | s | 0.1 | 0 | 1 |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |
| `orientation` | Parameter Satz 4 | – | {…} | – | – |
| `center` | Parameter Satz 6 | – | {…} | – | – |
| `dynamic` | Parameter Satz 8 | – | {…} | – | – |

## Parametersatz `SplitRangeParams` (`vdsim.stabilization.vehicle_layers`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_i` | Integratorverstärkung k_I (Beschleunigungsfehler) | 1/s | 0.5 | 0 | – |
| `integrator_limit` | Integratorgrenze (Anteil von m g) | - | 0.3 | 0 | 1 |
| `compensate_resistance` | Fahrwiderstand F_W(v) kompensieren | – | True | – | – |
| `gamma_brake` | Bremskraftverteilung vorne gamma | - | 0.75 | 0 | 1 |
| `max_decel` | max. Verzögerung | m/s² | 10 | 0 | – |
| `regen` | Rekuperation über den E-Antrieb (nur EV) | – | False | – | – |
| `systems` | Fahrdynamiksysteme (esp, abs, tcs, torque_vectoring) | – | [] | – | – |
| `integrator_min_speed` | Integrator nur oberhalb \|v\| bzw. bei Sollbeschleunigung | m/s | 0.3 | 0 | – |

## Parametersatz `ActuatorParams` (`vdsim.stabilization.vehicle_layers`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `steering` | Lenkaktor (SteeringActuatorParameters) | – | {…} | – | – |
| `max_steer_angle` | Lenkwinkelgrenze (<0: aus Fahrzeug) | rad | -1 | – | – |
| `drive_dead_time` | Totzeit Antrieb | s | 0 | 0 | – |
| `drive_tau` | PT1 Antrieb | s | 0 | 0 | – |
| `brake_dead_time` | Totzeit Bremse | s | 0 | 0 | – |
| `brake_tau` | PT1 Bremse | s | 0 | 0 | – |

## Parametersatz `DynamicParams` (`vdsim.stabilization.werling_dynamic`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `zeta` | Dämpfungsgrad der Nulldynamik zeta (4.70) | - | 1 | 0.3 | 3 |
| `lam_fixed` | festes lambda (< -50: geschwindigkeitsabhängig nach (4.70)) | m | -100 | – | – |
| `lam_min` | minimales lambda | m | 0 | -1.5 | 30 |
| `lam_max` | maximales lambda | m | 20 | 0 | 50 |
| `lam_rate` | max. Änderungsrate von lambda | m/s | 4 | 0 | – |
| `pole_n1` | Pol 1 Querfehler | 1/s | -1.18 | – | 0 |
| `pole_n2` | Pol 2 Querfehler | 1/s | -3.82 | – | 0 |
| `pole_t1` | Pol 1 Längsfehler | 1/s | -0.29 | – | 0 |
| `pole_t2` | Pol 2 Längsfehler | 1/s | -1.71 | – | 0 |
| `k_delta` | Lenkwinkel-Rückführung k_delta (4.75) | 1/s | 10 | 0 | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `saturation_exponent` | Exponent n der Sättigungsmodifikation | - | 16 | 2 | 60 |
| `reference_transform` | Sollgrößentransformation: dynamic / static / none | – | dynamic | – | – |
| `v_floor` | Mindestgeschwindigkeit der Nulldynamik-Simulation | m/s | 1 | 0.1 | – |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Parametersatz `OrientationParams` (`vdsim.stabilization.werling_kinematic`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k1` | k1 (Positionsfehler) | 1/m² | 0.5 | 0 | – |
| `k2` | k2 (Orientierungsfehler) | 1/m | 2 | 0 | – |
| `k3` | k3 (Geschwindigkeitsfehler) | 1/s | 2 | 0 | – |
| `k4` | k4 (Lenkfehler, Backstepping) | 1/s | 10 | 0 | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `taylor_switch` | Grenze Taylor-Näherung | rad | 0.5 | 0 | 1.5 |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Parametersatz `CenterParams` (`vdsim.stabilization.werling_kinematic`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k1` | k~1 (Positionsfehler) | 1/m² | 0.5 | 0 | – |
| `k3` | k~3 (Geschwindigkeitsfehler) | 1/s | 2 | 0 | – |
| `k4` | k~4 (Kurswinkelfehler) | 1/s | 5 | 0 | – |
| `lam` | Abstand lambda von der Hinterachse (<0: l/2) | m | -1 | – | – |
| `gamma_drive` | Kräfteverhältnis Antrieb (<0: aus Antriebslayout) | - | -1 | -1 | 1 |
| `gamma_brake` | Kräfteverhältnis Bremsen | - | 0.75 | 0 | 1 |
| `taylor_switch` | Grenze Taylor-Näherung | rad | 0.5 | 0 | 1.5 |
| `sign_variant` | Vorzeichen in (4.31): proof / printed | – | proof | – | – |
| `mu` | Reibwert (<0: aus Fahrzeug/Umgebung) | - | -1 | – | – |

## Konfigurationsdateien, die Komponenten dieses Pakets verwenden

| Datei | Titel | Komponenten |
|---|---|---|
| [configs/stabilization/classic_controllers.json](../../../configs/stabilization/classic_controllers.json) | classic_controllers | `tracking_controller/composite` |
| [configs/stabilization/werling_bilevel_default.json](../../../configs/stabilization/werling_bilevel_default.json) | werling_bilevel_default | `tracking_controller/werling_bilevel` |
| [configs/stabilization/werling_dynamic_highway.json](../../../configs/stabilization/werling_dynamic_highway.json) | werling_dynamic_highway | `tracking_controller/werling_dynamic` |
| [configs/stabilization/werling_slow_orientation.json](../../../configs/stabilization/werling_slow_orientation.json) | werling_slow_orientation | `tracking_controller/werling_bilevel` |
