# Regler, Fahrerassistenz und Fahrwerksregelsysteme

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.controllers` · Quellcode: [vdsim/controllers/](../../../vdsim/controllers) · Paketdoku: [vdsim/controllers/docs/](../../../vdsim/controllers/docs)

## Übersicht

**Bahnführung (Stanley, Pure Pursuit, MPC), Längsführung (PI, ACC, AEB), Spurhalteassistent, Rückkanal-Schätzer sowie ABS, ASR, ESP, Torque Vectoring, Hinterachslenkung und aktives Fahrwerk.**

Das Paket enthält alle Regler des klassischen Simulators. Querregler setzen eine Referenzbahn in einen
Radlenkwinkel um, Längsregler in eine Beschleunigungsanforderung, Fahrwerksregelsysteme verändern die
Stellgrößen (`ControlInput`) radindividuell. Damit lassen sich Bahnführungsverfahren, Assistenzfunktionen
und Fahrdynamikregelsysteme im geschlossenen Kreis mit allen Fahrzeugmodellen vergleichen.

Paket-Docstring:

```text
Controllers: path tracking (Stanley, Pure Pursuit, MPC), ADAS (ACC, AEB, LKA), longitudinal
control, curvature feedback and chassis control systems (ABS, TCS, ESP, rear steering,
torque vectoring, active suspension).
```

| Kennzahl | Anzahl |
|---|---|
| Module | 15 |
| Komponenten | 16 |
| Verfahren/Konzepte | 15 |
| @trace-Einträge | 18 |
| Tests | 5 |
| Beispiele | 1 |

## Architektur

- Querregler (`LateralController.steer`): `stanley_controller`, `pure_pursuit`, `mpc_controller`,
  `open_loop` (Lenktabelle, Krümmungsvorsteuerung), `lane_keeping` (LKA mit Fahrermodell).
- Längsregler (`LongitudinalController.acceleration`): `speed_controller` (PI + Vorsteuerung, ACC, AEB).
- Regelsysteme (`ChassisSystem.apply`): `slip_control` (ABS, ASR), `esp_controller` (ESP, Referenzgierrate,
  Eigenlenkgradient), `torque_vectoring`, `rear_axle_steering`, `active_suspension` (Wankstabilisierung, Skyhook).
- `chassis_systems.enabled_systems()` legt fest, welche Systeme aktiv sind und in welcher Reihenfolge sie wirken.
- `curvature_feedback.CurvatureCorrection`: Rückkanal-Schätzer des Aktuatorfehlers (genutzt vom Lenkaktor).
- `path_tracking.py`: Hilfsfunktionen (Winkel wickeln, Achspunkt, Lenkwinkelbegrenzung).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.controllers`](../../../vdsim/controllers/__init__.py) | 11 | – | Controllers: path tracking (Stanley, Pure Pursuit, MPC), ADAS (ACC, AEB, LKA), longitudinal control, curvature feedback and chassis control systems (ABS, TCS, ESP, rear steering, torque vectoring, active suspension). |
| [`vdsim.controllers.active_suspension`](../../../vdsim/controllers/active_suspension.py) | 47 | ActiveRollStabilization, SkyhookDamping | Active suspension: roll stabilization and skyhook damping. |
| [`vdsim.controllers.chassis_systems`](../../../vdsim/controllers/chassis_systems.py) | 14 | – | Chassis control systems: which ones are switched on and in which order they act. |
| [`vdsim.controllers.curvature_feedback`](../../../vdsim/controllers/curvature_feedback.py) | 28 | CurvatureCorrection | Feedback correction: estimates the curvature error and corrects the desired curvature. |
| [`vdsim.controllers.esp_controller`](../../../vdsim/controllers/esp_controller.py) | 62 | ElectronicStabilityProgram | ESP: yaw-rate control by single-wheel braking, plus the reference yaw-rate model. |
| [`vdsim.controllers.lane_keeping`](../../../vdsim/controllers/lane_keeping.py) | 59 | LaneKeepingAssist | Lane keeping assist (LKA) with an inattentive-driver model. |
| [`vdsim.controllers.mpc_controller`](../../../vdsim/controllers/mpc_controller.py) | 109 | MPCController | Linear lateral MPC on the path-error dynamics of the single-track model (Rajamani, ch. |
| [`vdsim.controllers.open_loop`](../../../vdsim/controllers/open_loop.py) | 40 | OpenLoopSteering, CurvatureFeedforward | Open-loop steering from the maneuver's steering table and pure curvature feedforward. |
| [`vdsim.controllers.path_tracking`](../../../vdsim/controllers/path_tracking.py) | 18 | – | Shared helpers for the path-tracking controllers. |
| [`vdsim.controllers.pure_pursuit`](../../../vdsim/controllers/pure_pursuit.py) | 31 | PurePursuitController | Pure Pursuit path tracking (geometric, rear-axle reference, speed-dependent look-ahead). |
| [`vdsim.controllers.rear_axle_steering`](../../../vdsim/controllers/rear_axle_steering.py) | 25 | RearAxleSteering | Rear-axle steering: speed-dependent ratio to the front steering angle. |
| [`vdsim.controllers.slip_control`](../../../vdsim/controllers/slip_control.py) | 60 | _SlipModulation, AntiLockBraking, TractionControl | Wheel-slip control: ABS (brake slip) and TCS (drive slip). |
| [`vdsim.controllers.speed_controller`](../../../vdsim/controllers/speed_controller.py) | 132 | SpeedController, AdaptiveCruiseControl, EmergencyBrakeAssist | Longitudinal control: speed tracking (PI + feedforward), ACC and emergency brake assist (AEB). |
| [`vdsim.controllers.stanley_controller`](../../../vdsim/controllers/stanley_controller.py) | 46 | StanleyController | Stanley path-tracking controller (Hoffmann et al. |
| [`vdsim.controllers.torque_vectoring`](../../../vdsim/controllers/torque_vectoring.py) | 41 | TorqueVectoring | Torque vectoring: yaw moment from a left/right drive-torque difference. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [tire_models](../tire_models/index.md), [vehicle_models](../vehicle_models/index.md)
- genutzt von: [actuators](../actuators/index.md), [core](../core/index.md), [lane_change](../lane_change/index.md), [simulation](../simulation/index.md), [stabilization](../stabilization/index.md)
- externe Bibliotheken: `numpy`, `scipy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Stanley mit Kurswinkelfehler (Gierwinkel plus Schwimmwinkel) und Vorsteuerung L kappa + EG v² kappa | stationäre Kurvenfahrt ohne bleibende Querablage auch bei großem Schwimmwinkel | klassischer Stanley mit Gierwinkelfehler (bleibende Ablage in engen Kurven) |
| Lineare MPC auf der Fehlerdynamik mit exakter ZOH-Diskretisierung und Box-Restriktionen über BVLS | kleine, gut konditionierte Kleinste-Quadrate-Aufgabe ohne QP-Solver-Abhängigkeit | allgemeiner QP-Solver (OSQP), nichtlineare MPC |
| Schlupfregelung über Modulationsfaktor mit Hysterese | bildet die Druckabbau-/Druckaufbau-Logik realer ABS-Hydraulik qualitativ nach und ist robust | kontinuierliche Schlupfregelung (PI), Sliding Mode |
| Referenzgierrate aus dem linearen Einspurmodell, begrenzt auf 0,85 mu g / v | gängiger Ansatz der ESP-Literatur; Ziel ist ein lineares, beherrschbares Fahrverhalten | – |

## Implementierung

- Alle Regler protokollieren ihre internen Größen in `self.signals`; der Simulator zeichnet sie automatisch auf.
- Pfadprojektionen nutzen einen Suchhinweis (`_hint`) je Regler, damit geschlossene Strecken und Schleifen eindeutig bleiben.
- Die MPC rechnet nur alle `update_period` neu und speichert die Prädiktionsmatrizen, solange sich die Geschwindigkeit um weniger als 0,5 m/s ändert.

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`chassis_system/abs`](components/chassis_system__abs.md) | ABS | legacy | Antiblockiersystem über radindividuellen Modulationsfaktor des Bremsmoments. |
| [`chassis_system/active_damping`](components/chassis_system__active_damping.md) | Aktive Dämpfung (Skyhook) | legacy | skyhook: damper force proportional to the absolute body velocity at each corner |
| [`chassis_system/active_roll`](components/chassis_system__active_roll.md) | Aktive Wankstabilisierung | legacy | counteracts the roll moment of the lateral acceleration (gain 1 = full compensation) |
| [`chassis_system/esp`](components/chassis_system__esp.md) | ESP | legacy | yaw-rate control by single-wheel braking (oversteer: outer front, understeer: inner rear) |
| [`chassis_system/rear_steering`](components/chassis_system__rear_steering.md) | Hinterachslenkung | legacy | speed-dependent ratio: counter-phase at low speed (agility), in-phase at high speed (stability) |
| [`chassis_system/tcs`](components/chassis_system__tcs.md) | Antriebsschlupfregelung (ASR/TCS) | legacy | Antriebsschlupfregelung über Modulationsfaktor des Antriebsmoments. |
| [`chassis_system/torque_vectoring`](components/chassis_system__torque_vectoring.md) | Torque Vectoring | legacy | yaw moment from left/right drive-torque difference on the driven axles |
| [`lateral_controller/curvature_feedforward`](components/lateral_controller__curvature_feedforward.md) | Krümmungsvorsteuerung (ohne Rückführung) | legacy | Steers the kinematic angle of the path curvature at the current position, no feedback |
| [`lateral_controller/lane_keeping`](components/lateral_controller__lane_keeping.md) | Spurhalteassistent (LKA) | legacy | Spurhalteassistent mit unaufmerksamem Fahrermodell (Pure Pursuit plus Lenkdrift) und begrenztem Lenkeingriff. |
| [`lateral_controller/mpc`](components/lateral_controller__mpc.md) | MPC | legacy | Lineare modellprädiktive Bahnregelung auf der Fehlerdynamik des Einspurmodells mit Krümmungsvorschau und Lenkwinkelgrenzen. |
| [`lateral_controller/open_loop`](components/lateral_controller__open_loop.md) | Lenkung nach Tabelle (open loop) | legacy | Lenkung nach Zeittabelle des Manövers (ISO-Lenkmanöver ohne Rückführung). |
| [`lateral_controller/pure_pursuit`](components/lateral_controller__pure_pursuit.md) | Pure Pursuit | legacy | Geometrischer Pure-Pursuit-Regler mit Hinterachs-Referenz und geschwindigkeitsabhängiger Vorausschau. |
| [`lateral_controller/stanley`](components/lateral_controller__stanley.md) | Stanley | legacy | Stanley-Bahnregler mit Kurswinkelfehler, Querablage an der Vorderachse, Krümmungsvorsteuerung und Gierdämpfung. |
| [`longitudinal_controller/acc`](components/longitudinal_controller__acc.md) | Abstandsregeltempomat (ACC) | legacy | Abstandsregeltempomat mit konstanter Zeitlücke. |
| [`longitudinal_controller/aeb`](components/longitudinal_controller__aeb.md) | Notbremsassistent (AEB) | legacy | Time-to-collision based staged braking on top of a base longitudinal controller |
| [`longitudinal_controller/speed_pi`](components/longitudinal_controller__speed_pi.md) | Geschwindigkeitsregler (PI) | legacy | PI-Geschwindigkeitsregler mit Vorsteuerung aus dem Geschwindigkeitsprofil und Anti-Windup. |

### Verfahren und Konzepte

- [Abstandsregeltempomat und Notbremsassistent](theory.md#acc_aeb)
- [Aktives Fahrwerk: Wankstabilisierung und Skyhook](theory.md#active_suspension)
- [Rückkanal-Korrektur des Krümmungsfehlers](theory.md#curvature_feedback_correction)
- [ESP – Gierratenregelung durch Einzelradbremsung](theory.md#esp_yaw_control)
- [Kinematisches Einspurmodell](../vehicle_models/theory.md#kinematic_bicycle)
- [Spurhalteassistent mit Fahrermodell](theory.md#lane_keeping_assist)
- [Lineares Einspurmodell](../vehicle_models/theory.md#linear_bicycle)
- [Modellprädiktive Bahnregelung (lineare MPC)](theory.md#path_mpc)
- [Pure Pursuit](theory.md#pure_pursuit)
- [Hinterachslenkung](theory.md#rear_axle_steering)
- [Geschwindigkeitsregelung (PI mit Vorsteuerung)](theory.md#speed_control)
- [Stanley-Bahnregler](theory.md#stanley_controller)
- [Torque Vectoring](theory.md#torque_vectoring)
- [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient)
- [Schlupfregelung ABS und ASR](theory.md#wheel_slip_control)

## Erweiterungspunkte

- Neuer Querregler als LateralController mit "@register('lateral_controller', name)"; Signale über self.signals
- Neues Regelsystem als ChassisSystem; Schalter in ControlSystemsParameters, Eintrag in SYSTEM_FLAGS und in der Reihenfolge von enabled_systems

## Verwandte Module

[simulation](../simulation/index.md), [actuators](../actuators/index.md), [trajectory](../trajectory/index.md), [vehicle_models](../vehicle_models/index.md), [analysis](../analysis/index.md)

## Hauptquellen

[Borrelli et al. (2017)](../references.md#borrelli2017), [Coulter (1992)](../references.md#coulter1992), [Hoffmann et al. (2007)](../references.md#hoffmann2007), [Karnopp et al. (1974)](../references.md#karnopp1974), [Ljung (1999)](../references.md#ljung1999), [Rajamani (2012)](../references.md#rajamani2012), [Reif (2010)](../references.md#reif2010), [Snider (2009)](../references.md#snider2009), [Stark und Parker (1995)](../references.md#stark1995), [Thrun et al. (2006)](../references.md#thrun2006), [van Zanten et al. (1995)](../references.md#vanzanten1995)
