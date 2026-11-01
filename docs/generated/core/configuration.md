# Kern – Konventionen, Parameter, Schnittstellen, Registry – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `configs/vehicles/*.json` | Fahrzeug-Presets (Mittelklasse-Limousine, Elektro-Limousine, Sportwagen, SUV) im Format von VehicleConfig.to_dict() | – | – |
| `VehicleConfig.vehicle / tires / chassis / powertrain / brakes / systems` | Parametergruppen; Einheiten und Grenzen stehen in configuration.md des Pakets | – | – |

## Parametersatz `VehicleParameters` (`vdsim.core.parameters`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `name` | Bezeichnung | – | Mittelklasse-Limousine | – | – |
| `mass` | Masse | kg | 1600 | 500 | 5000 |
| `wheelbase` | Radstand | m | 2.8 | 1.5 | 4.5 |
| `cg_to_front` | Schwerpunkt - Vorderachse | m | 1.25 | 0.3 | 3.5 |
| `track_front` | Spurweite vorne | m | 1.6 | 1 | 2.2 |
| `track_rear` | Spurweite hinten | m | 1.6 | 1 | 2.2 |
| `cg_height` | Schwerpunkthöhe | m | 0.55 | 0.2 | 1.5 |
| `inertia_x` | Wankträgheit (aufgebaut) | kg m² | 600 | 50 | – |
| `inertia_y` | Nickträgheit | kg m² | 2800 | 100 | – |
| `inertia_z` | Gierträgheit | kg m² | 2700 | 100 | – |
| `unsprung_mass_front` | Ungefederte Masse vorne (je Rad) | kg | 45 | 5 | – |
| `unsprung_mass_rear` | Ungefederte Masse hinten (je Rad) | kg | 40 | 5 | – |
| `drag_coefficient` | Luftwiderstandsbeiwert cw | - | 0.28 | 0.1 | 1.5 |
| `frontal_area` | Stirnfläche | m² | 2.2 | 0.5 | 10 |
| `rolling_resistance` | Rollwiderstandsbeiwert | - | 0.012 | 0 | 0.05 |
| `wheel_radius` | Dynamischer Radradius | m | 0.32 | 0.15 | 0.6 |
| `wheel_inertia` | Radträgheit (je Rad) | kg m² | 1.2 | 0.1 | – |
| `steering_ratio` | Lenkübersetzung | - | 15 | 5 | 30 |
| `max_steer_angle` | Max. Radlenkwinkel | rad | 0.6 | 0.1 | 1.2 |
| `length` | Fahrzeuglänge | m | 4.8 | 2 | 12 |
| `width` | Fahrzeugbreite | m | 1.85 | 1 | 2.6 |

## Parametersatz `TireParameters` (`vdsim.core.parameters`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `model` | Reifenmodell (linear / pacejka / brush) | – | pacejka | – | – |
| `mu` | Reibwert (Referenz) | - | 1 | 0.05 | 2 |
| `nominal_load` | Nennlast | N | 4000 | 500 | – |
| `cornering_stiffness_front` | Schräglaufsteifigkeit vorne (je Reifen, Nennlast) | N/rad | 80000 | 1000 | – |
| `cornering_stiffness_rear` | Schräglaufsteifigkeit hinten (je Reifen, Nennlast) | N/rad | 110000 | 1000 | – |
| `longitudinal_stiffness` | Längssteifigkeit (je Reifen, Nennlast) | N | 100000 | 1000 | – |
| `camber_stiffness` | Sturzsteifigkeit (je Reifen) | N/rad | 5000 | 0 | – |
| `load_sensitivity_stiffness` | Lastabhängigkeit Schräglaufsteifigkeit (Pacejka p_Ky2) | - | 2 | 0.5 | 5 |
| `load_sensitivity_mu` | Lastabhängigkeit Reibwert | - | -0.1 | -0.5 | 0 |
| `shape_lateral` | Formfaktor C lateral | - | 1.3 | 1 | 2 |
| `curvature_lateral` | Krümmungsfaktor E lateral | - | -0.5 | -5 | 1 |
| `shape_longitudinal` | Formfaktor C longitudinal | - | 1.65 | 1 | 2 |
| `curvature_longitudinal` | Krümmungsfaktor E longitudinal | - | 0 | -5 | 1 |
| `combined_lateral_reduction` | Kombinierter Schlupf: Abbau Fy durch kappa (B_yk) | - | 10 | 0 | – |
| `combined_longitudinal_reduction` | Kombinierter Schlupf: Abbau Fx durch alpha (B_xa) | - | 12 | 0 | – |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |
| `vertical_stiffness` | Vertikalsteifigkeit Reifen | N/m | 250000 | 10000 | – |

## Parametersatz `ChassisParameters` (`vdsim.core.parameters`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `spring_rate_front` | Federrate vorne (am Rad) | N/m | 32000 | 1000 | – |
| `spring_rate_rear` | Federrate hinten (am Rad) | N/m | 35000 | 1000 | – |
| `damper_velocity` | Dämpfer-Stützstellen Geschwindigkeit (+ = Druck) | m/s | [-1, -0.3, -0.1, 0, 0.1, 0.3, 1] | – | – |
| `damper_force_front` | Dämpferkennlinie vorne | N | [-1900, -850, -320, 0, 180, 450, 1000] | – | – |
| `damper_force_rear` | Dämpferkennlinie hinten | N | [-1800, -800, -300, 0, 170, 420, 950] | – | – |
| `anti_roll_bar_front` | Stabilisator-Wanksteifigkeit vorne | N m/rad | 30000 | 0 | – |
| `anti_roll_bar_rear` | Stabilisator-Wanksteifigkeit hinten | N m/rad | 12000 | 0 | – |
| `roll_center_height_front` | Rollzentrumshöhe vorne | m | 0.06 | -0.2 | 0.5 |
| `roll_center_height_rear` | Rollzentrumshöhe hinten | m | 0.12 | -0.2 | 0.5 |
| `camber_gain_front` | Sturzänderung vorne pro Federweg | rad/m | -0.35 | -2 | 2 |
| `camber_gain_rear` | Sturzänderung hinten pro Federweg | rad/m | -0.3 | -2 | 2 |
| `bump_steer_front` | Vorspuränderung vorne pro Federweg | rad/m | 0 | -1 | 1 |
| `bump_steer_rear` | Vorspuränderung hinten pro Federweg | rad/m | 0 | -1 | 1 |
| `roll_steer_front` | Rolllenken vorne | rad/rad | -0.05 | -0.5 | 0.5 |
| `roll_steer_rear` | Rolllenken hinten | rad/rad | 0.02 | -0.5 | 0.5 |
| `anti_dive` | Bremsnickausgleich vorne | - | 0.2 | 0 | 1 |
| `anti_squat` | Anfahrnickausgleich hinten | - | 0.3 | 0 | 1 |

## Parametersatz `PowertrainParameters` (`vdsim.core.parameters`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `type` | Antriebsart (ev / ice) | – | ev | – | – |
| `layout` | Antriebslayout (fwd / rwd / awd) | – | awd | – | – |
| `front_torque_split` | Momentenanteil Vorderachse (AWD) | - | 0.4 | 0 | 1 |
| `driveline_efficiency` | Wirkungsgrad Triebstrang | - | 0.92 | 0.5 | 1 |
| `engine_speed_rpm` | Motordrehzahl-Stützstellen | 1/min | [800, 1500, 2500, 3500, 4500, 5500, 6500] | – | – |
| `engine_torque_nm` | Volllast-Drehmomentkennlinie | N m | [180, 300, 380, 400, 390, 360, 300] | – | – |
| `gear_ratios` | Getriebeübersetzungen | - | [3.6, 2.3, 1.6, 1.2, 1, 0.82, 0.68] | – | – |
| `final_drive` | Achsübersetzung | - | 3.2 | 1 | – |
| `upshift_rpm` | Hochschaltdrehzahl | 1/min | 6000 | – | – |
| `downshift_rpm` | Rückschaltdrehzahl | 1/min | 2000 | – | – |
| `motor_max_torque` | E-Motor max. Moment | N m | 450 | 0 | – |
| `motor_max_power` | E-Motor max. Leistung | W | 220000 | 0 | – |
| `motor_gear_ratio` | E-Motor Übersetzung | - | 9 | 1 | – |
| `motor_max_rpm` | E-Motor max. Drehzahl | 1/min | 16000 | 1000 | – |
| `motor_efficiency` | E-Motor Wirkungsgrad | - | 0.9 | 0.5 | 1 |
| `regen_max_power` | Max. Rekuperationsleistung | W | 120000 | 0 | – |
| `regen_max_torque` | Max. Rekuperationsmoment (Motor) | N m | 300 | 0 | – |
| `battery_capacity_kwh` | Batteriekapazität | kWh | 80 | 1 | – |
| `auxiliary_power` | Nebenverbraucher | W | 500 | 0 | – |
| `torque_vectoring_max_torque` | Torque Vectoring max. Differenzmoment (Rad) | N m | 800 | 0 | – |

## Parametersatz `BrakeParameters` (`vdsim.core.parameters`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `max_torque_front` | Max. Bremsmoment vorne (je Rad) | N m | 2500 | 0 | – |
| `max_torque_rear` | Max. Bremsmoment hinten (je Rad) | N m | 1500 | 0 | – |
| `brake_balance` | Bremskraftverteilung (Anteil vorne) | - | 0.65 | 0 | 1 |
| `ebd_enabled` | Elektronische Bremskraftverteilung (EBV) | – | True | – | – |

## Parametersatz `ControlSystemsParameters` (`vdsim.core.parameters`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `abs_enabled` | ABS aktiv | – | True | – | – |
| `abs_target_slip` | ABS Zielschlupf | - | 0.12 | 0.02 | 0.4 |
| `tcs_enabled` | ASR/TCS aktiv | – | True | – | – |
| `tcs_target_slip` | TCS Zielschlupf | - | 0.1 | 0.02 | 0.4 |
| `esp_enabled` | ESP aktiv | – | False | – | – |
| `esp_gain` | ESP Verstärkung Giermoment | N m s/rad | 20000 | 0 | – |
| `esp_deadband` | ESP Totband Gierrate | rad/s | 0.03 | 0 | – |
| `rear_steering_enabled` | Hinterachslenkung aktiv | – | False | – | – |
| `rear_steering_ratio_low` | HAL Verhältnis niedrige Geschw. (gegensinnig < 0) | - | -0.2 | -1 | 1 |
| `rear_steering_ratio_high` | HAL Verhältnis hohe Geschw. (gleichsinnig > 0) | - | 0.1 | -1 | 1 |
| `rear_steering_speed_low` | HAL Übergang Beginn | m/s | 8 | 0 | – |
| `rear_steering_speed_high` | HAL Übergang Ende | m/s | 22 | 0 | – |
| `torque_vectoring_enabled` | Torque Vectoring aktiv | – | False | – | – |
| `torque_vectoring_gain` | Torque Vectoring Verstärkung | N m s/rad | 30000 | 0 | – |
| `torque_vectoring_target` | TV Ziel-Eigenlenkverhalten (0 = neutral, 1 = passiv) | - | 0 | -0.5 | 1 |
| `active_damping_enabled` | Aktive Dämpfung (Skyhook) aktiv | – | False | – | – |
| `skyhook_gain` | Skyhook-Dämpfung | N s/m | 2500 | 0 | – |
| `active_roll_enabled` | Aktive Wankstabilisierung aktiv | – | False | – | – |
| `active_roll_gain` | Wankkompensationsgrad | - | 0.8 | 0 | 1.2 |

## Parametersatz `VehicleConfig` (`vdsim.core.parameters`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `vehicle` | – | – | {…} | – | – |
| `tires` | – | – | {…} | – | – |
| `chassis` | – | – | {…} | – | – |
| `powertrain` | – | – | {…} | – | – |
| `brakes` | – | – | {…} | – | – |
| `systems` | – | – | {…} | – | – |
