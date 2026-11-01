# Regler, Fahrerassistenz und Fahrwerksregelsysteme – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`ActiveRollStabilization.apply`](../../../vdsim/controllers/active_suspension.py#L23) | – | [Aktives Fahrwerk: Wankstabilisierung und Skyhook](theory.md#active_suspension) | – | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`SkyhookDamping.apply`](../../../vdsim/controllers/active_suspension.py#L42) | – | [Aktives Fahrwerk: Wankstabilisierung und Skyhook](theory.md#active_suspension) | [Karnopp et al. (1974)](../references.md#karnopp1974) | – | module.yaml |
| [`CurvatureCorrection.update`](../../../vdsim/controllers/curvature_feedback.py#L18) | – | [Rückkanal-Korrektur des Krümmungsfehlers](theory.md#curvature_feedback_correction) | [Ljung (1999)](../references.md#ljung1999) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | module.yaml |
| [`ElectronicStabilityProgram.apply`](../../../vdsim/controllers/esp_controller.py#L42) | – | [ESP – Gierratenregelung durch Einzelradbremsung](theory.md#esp_yaw_control) | [van Zanten et al. (1995)](../references.md#vanzanten1995) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py), [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`reference_yaw_rate`](../../../vdsim/controllers/esp_controller.py#L22) | – | [ESP – Gierratenregelung durch Einzelradbremsung](theory.md#esp_yaw_control) | [Rajamani (2012)](../references.md#rajamani2012) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | module.yaml |
| [`understeer_gradient`](../../../vdsim/controllers/esp_controller.py#L12) | – | [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py) | module.yaml |
| [`LaneKeepingAssist.steer`](../../../vdsim/controllers/lane_keeping.py#L38) | – | [Spurhalteassistent mit Fahrermodell](theory.md#lane_keeping_assist) | – | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`MPCController._matrices`](../../../vdsim/controllers/mpc_controller.py#L45) | Abschn. 2.5 | [Modellprädiktive Bahnregelung (lineare MPC)](theory.md#path_mpc) | [Rajamani (2012)](../references.md#rajamani2012) | – | module.yaml |
| [`MPCController.steer`](../../../vdsim/controllers/mpc_controller.py#L82) | – | [Modellprädiktive Bahnregelung (lineare MPC)](theory.md#path_mpc) | [Borrelli et al. (2017)](../references.md#borrelli2017) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`PurePursuitController.steer`](../../../vdsim/controllers/pure_pursuit.py#L20) | – | [Pure Pursuit](theory.md#pure_pursuit) | [Coulter (1992)](../references.md#coulter1992) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`RearAxleSteering.apply`](../../../vdsim/controllers/rear_axle_steering.py#L18) | – | [Hinterachslenkung](theory.md#rear_axle_steering) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`AntiLockBraking.apply`](../../../vdsim/controllers/slip_control.py#L32) | – | [Schlupfregelung ABS und ASR](theory.md#wheel_slip_control) | [Reif (2010)](../references.md#reif2010) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`TractionControl.apply`](../../../vdsim/controllers/slip_control.py#L50) | – | [Schlupfregelung ABS und ASR](theory.md#wheel_slip_control) | [Reif (2010)](../references.md#reif2010) | – | module.yaml |
| [`AdaptiveCruiseControl.acceleration`](../../../vdsim/controllers/speed_controller.py#L69) | – | [Abstandsregeltempomat und Notbremsassistent](theory.md#acc_aeb) | [Rajamani (2012)](../references.md#rajamani2012) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`EmergencyBrakeAssist.acceleration`](../../../vdsim/controllers/speed_controller.py#L104) | – | [Abstandsregeltempomat und Notbremsassistent](theory.md#acc_aeb) | – | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`SpeedController.acceleration`](../../../vdsim/controllers/speed_controller.py#L24) | – | [Geschwindigkeitsregelung (PI mit Vorsteuerung)](theory.md#speed_control) | – | – | module.yaml |
| [`StanleyController.steer`](../../../vdsim/controllers/stanley_controller.py#L31) | – | [Stanley-Bahnregler](theory.md#stanley_controller) | [Hoffmann et al. (2007)](../references.md#hoffmann2007) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`TorqueVectoring.apply`](../../../vdsim/controllers/torque_vectoring.py#L20) | – | [Torque Vectoring](theory.md#torque_vectoring) | – | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `ActiveRollStabilization.apply`

- **Warum:** Reduziert Wankwinkel in Kurven und Aufbaubewegungen auf unebener Straße.
- **Theorie:** [Aktives Fahrwerk: Wankstabilisierung und Skyhook](theory.md#active_suspension)
- **Annahmen:** Ideale Aktoren ohne Dynamik und Leistungsgrenze.
- **Quelle:** –

### `SkyhookDamping.apply`

- **Warum:** Reduziert Wankwinkel in Kurven und Aufbaubewegungen auf unebener Straße.
- **Theorie:** [Aktives Fahrwerk: Wankstabilisierung und Skyhook](theory.md#active_suspension)
- **Annahmen:** Ideale Aktoren ohne Dynamik und Leistungsgrenze.
- **Quelle:** [Karnopp et al. (1974)](../references.md#karnopp1974)

### `CurvatureCorrection.update`

- **Warum:** Schätzt laufend den multiplikativen Fehler der Aktuator-Kennlinie aus gesendeter und gemessener Krümmung und korrigiert die Sollkrümmung.
- **Theorie:** [Rückkanal-Korrektur des Krümmungsfehlers](theory.md#curvature_feedback_correction)
- **Annahmen:** Latenz der Wirkkette bekannt; Fehler näherungsweise multiplikativ und langsam veränderlich.
- **Quelle:** [Ljung (1999)](../references.md#ljung1999)

### `ElectronicStabilityProgram.apply`

- **Warum:** Stabilisiert das Fahrzeug beim Über- und Untersteuern durch ein Giermoment aus gezielten Bremseingriffen.
- **Theorie:** [ESP – Gierratenregelung durch Einzelradbremsung](theory.md#esp_yaw_control)
- **Annahmen:** Reibwert als Mittel der Radreibwerte bekannt; ein Rad pro Eingriff.
- **Quelle:** [van Zanten et al. (1995)](../references.md#vanzanten1995)

### `reference_yaw_rate`

- **Warum:** Stabilisiert das Fahrzeug beim Über- und Untersteuern durch ein Giermoment aus gezielten Bremseingriffen.
- **Theorie:** [ESP – Gierratenregelung durch Einzelradbremsung](theory.md#esp_yaw_control)
- **Annahmen:** Reibwert als Mittel der Radreibwerte bekannt; ein Rad pro Eingriff.
- **Quelle:** [Rajamani (2012)](../references.md#rajamani2012)

### `understeer_gradient`

- **Warum:** Kennzahl für das stationäre Eigenlenkverhalten: Wie viel zusätzlicher Lenkwinkel ist pro Querbeschleunigung nötig?
- **Theorie:** [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient)
- **Annahmen:** Lineare Reifen, statische Achslasten, kleine Winkel.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `LaneKeepingAssist.steer`

- **Warum:** Verhindert das ungewollte Verlassen der Spur bei einem abgelenkten Fahrer.
- **Theorie:** [Spurhalteassistent mit Fahrermodell](theory.md#lane_keeping_assist)
- **Annahmen:** Spurmitte gleich Referenzbahn, konstante Spurbreite.
- **Quelle:** –

### `MPCController._matrices`

- **Warum:** Optimale Lenkfolge über einen Horizont unter Lenkwinkelgrenzen, mit Vorausschau auf die Bahnkrümmung.
- **Theorie:** [Modellprädiktive Bahnregelung (lineare MPC)](theory.md#path_mpc)
- **Annahmen:** Konstante Geschwindigkeit über den Horizont, lineare Reifen (Achssteifigkeit aus dem Reifenmodell), Vorschau der Krümmung entlang $s + v\, k\, \Delta t$.
- **Quelle:** [Rajamani (2012)](../references.md#rajamani2012)

### `MPCController.steer`

- **Warum:** Optimale Lenkfolge über einen Horizont unter Lenkwinkelgrenzen, mit Vorausschau auf die Bahnkrümmung.
- **Theorie:** [Modellprädiktive Bahnregelung (lineare MPC)](theory.md#path_mpc)
- **Annahmen:** Konstante Geschwindigkeit über den Horizont, lineare Reifen (Achssteifigkeit aus dem Reifenmodell), Vorschau der Krümmung entlang $s + v\, k\, \Delta t$.
- **Quelle:** [Borrelli et al. (2017)](../references.md#borrelli2017)

### `PurePursuitController.steer`

- **Warum:** Geometrischer Bahnregler: Ein Kreisbogen durch die Hinterachse trifft einen Zielpunkt im Abstand $l_d$ auf der Bahn.
- **Theorie:** [Pure Pursuit](theory.md#pure_pursuit)
- **Annahmen:** Kinematisches Fahrzeug, Zielpunkt auf der Bahn bei $s_{proj} + l_d$.
- **Quelle:** [Coulter (1992)](../references.md#coulter1992)

### `RearAxleSteering.apply`

- **Warum:** Verbessert Wendigkeit bei niedriger und Stabilität bei hoher Geschwindigkeit.
- **Theorie:** [Hinterachslenkung](theory.md#rear_axle_steering)
- **Annahmen:** Statische Kennlinie ohne Aktordynamik.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `AntiLockBraking.apply`

- **Warum:** ABS verhindert blockierende Räder beim Bremsen, ASR durchdrehende Räder beim Antreiben, damit Seitenführung und Kraftschluss erhalten bleiben.
- **Theorie:** [Schlupfregelung ABS und ASR](theory.md#wheel_slip_control)
- **Annahmen:** Schlupf je Rad messbar (Modell mit Raddynamik).
- **Quelle:** [Reif (2010)](../references.md#reif2010)

### `TractionControl.apply`

- **Warum:** ABS verhindert blockierende Räder beim Bremsen, ASR durchdrehende Räder beim Antreiben, damit Seitenführung und Kraftschluss erhalten bleiben.
- **Theorie:** [Schlupfregelung ABS und ASR](theory.md#wheel_slip_control)
- **Annahmen:** Schlupf je Rad messbar (Modell mit Raddynamik).
- **Quelle:** [Reif (2010)](../references.md#reif2010)

### `AdaptiveCruiseControl.acceleration`

- **Warum:** ACC hält eine Zeitlücke zum vorausfahrenden Fahrzeug, AEB vermeidet Auffahrunfälle durch gestufte Bremsung.
- **Theorie:** [Abstandsregeltempomat und Notbremsassistent](theory.md#acc_aeb)
- **Annahmen:** Ideale Objekterkennung (Abstand und Geschwindigkeit des Vorderfahrzeugs bekannt), gleiche Fahrspur.
- **Quelle:** [Rajamani (2012)](../references.md#rajamani2012)

### `EmergencyBrakeAssist.acceleration`

- **Warum:** ACC hält eine Zeitlücke zum vorausfahrenden Fahrzeug, AEB vermeidet Auffahrunfälle durch gestufte Bremsung.
- **Theorie:** [Abstandsregeltempomat und Notbremsassistent](theory.md#acc_aeb)
- **Annahmen:** Ideale Objekterkennung (Abstand und Geschwindigkeit des Vorderfahrzeugs bekannt), gleiche Fahrspur.
- **Quelle:** –

### `SpeedController.acceleration`

- **Warum:** Folgen des Geschwindigkeitsprofils der Trajektorie.
- **Theorie:** [Geschwindigkeitsregelung (PI mit Vorsteuerung)](theory.md#speed_control)
- **Annahmen:** Profil entlang der Bahn bekannt; Fahrwiderstände kompensiert die Längsaktuierung.
- **Quelle:** –

### `StanleyController.steer`

- **Warum:** Robuste Bahnfolge über einen weiten Geschwindigkeitsbereich mit nichtlinearer Rückführung der Querablage an der Vorderachse.
- **Theorie:** [Stanley-Bahnregler](theory.md#stanley_controller)
- **Annahmen:** Vorwärtsfahrt; die Bahn ist glatt und ihre Krümmung bekannt.
- **Quelle:** [Hoffmann et al. (2007)](../references.md#hoffmann2007)

### `TorqueVectoring.apply`

- **Warum:** Erzeugt ein Giermoment durch Umverteilung des Antriebsmoments zwischen linkem und rechtem Rad, um das Eigenlenkverhalten agiler zu machen.
- **Theorie:** [Torque Vectoring](theory.md#torque_vectoring)
- **Annahmen:** Ideales Differenzial mit begrenztem Differenzmoment.
- **Quelle:** –
