# Trajektorienstabilisierung nach Werling und Fahrzeugebenen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.stabilization` · Quellcode: [vdsim/stabilization/](../../../vdsim/stabilization) · Paketdoku: [vdsim/stabilization/docs/](../../../vdsim/stabilization/docs)

## Übersicht

**Setzt Solltrajektorien mit den drei Werling-Trackingreglern (Bi-level-Stabilisierung) oder klassischen Reglern in Lenkrate/Lenkwinkel und Längskraft/Beschleunigung um und stellt Vehicle Dynamics, Actuators und Vehicle Plant bereit.**

Die Trajektorienplanung (vdsim.planning) liefert eine zeitparametrierte Solltrajektorie. Dieses Paket
stabilisiert sie gegen permanente Störungen und Modellfehler (Low-level, Werling Kap. 4) und löst bei
Impulsstörungen die Reinitialisierung der Planung aus (High-level, Werling 2.3/4.5). Klassische Regler
dienen als Vergleich; die Fahrzeugebenen schließen die Wirkkette bis zum Fahrzeugmodell.

Paket-Docstring:

```text
Trajectory stabilization after Werling (2011), chapter 4, plus classical tracking controllers and the
vehicle layers of the AD chain (contracts.md section 1).

Components (registered on import):
    tracking_controller/werling_bilevel              switching (Fig. 4.13) + re-initialization (4.5), default
    tracking_controller/werling_kinematic_orientation  Satz 4 (rear axle, forward/reverse)
    tracking_controller/werling_kinematic_center     Satz 6 (geometric center, forward)
    tracking_controller/werling_dynamic              Satz 8 (exact I/O linearization, fast driving)
    tracking_controller/pure_pursuit, stanley, lqr, mpc          classical lateral controllers
    tracking_controller/pid, pi, ff_fb, acc, speed_pi            classical longitudinal controllers
    tracking_controller/composite                    lateral + longitudinal
    vehicle_dynamics/split_range                     Werling 5.1.2.2
    actuator/steering_powertrain                     steering actuator, drive/brake delays
    vehicle_plant/vehicle_model                      any vdsim vehicle model
```

| Kennzahl | Anzahl |
|---|---|
| Module | 14 |
| Komponenten | 17 |
| Verfahren/Konzepte | 29 |
| @trace-Einträge | 28 |
| Tests | 6 |
| Beispiele | 5 |

## Architektur

- `werling_kinematic.py`: Satz 4 (Hinterachse, vor-/rückwärts) und Satz 6 (Fahrzeugmitte), A.5-Port
- `werling_dynamic.py`: Satz 8 (exakte E/A-Linearisierung), lambda(zeta, v), Nulldynamik-Online-Simulation
- `switching.py`: `werling_bilevel` = Umschaltung nach Abb. 4.13 + `reinit.py` (Auslösung, Prädiktion)
- `errors.py`: invariante Fehler und Sollgrößentransformation; `common.py`: Vorzeichenkonventionen
- `classic_lateral.py`, `classic_longitudinal.py`, `composite.py`: Vergleichsregler
- `vehicle_layers.py`: `vehicle_dynamics/split_range`, `actuator/steering_powertrain`; `plant.py`: `vehicle_plant/vehicle_model`
- `simulate.py`, `trajectories.py`: schlanke Regelkreis-Simulation und Solltrajektorien für Tests/Beispiele
- Streckenmodelle `werling_kesm`, `werling_desm` in `vdsim/vehicle_models/werling_models.py`, isotroper Reifen in `vdsim/tire_models/isotropic.py`
Datenfluss: ego + trajectory -> ControlCommand (steer_rate, force) -> ActuatorCommand -> ControlInput -> EgoState.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.stabilization`](../../../vdsim/stabilization/__init__.py) | 40 | – | Trajectory stabilization after Werling (2011), chapter 4, plus classical tracking controllers and the vehicle layers of the AD chain (contracts.md section 1). |
| [`vdsim.stabilization.classic_lateral`](../../../vdsim/stabilization/classic_lateral.py) | 437 | _SpeedLoopParams, ClassicBase, PurePursuitParams, PurePursuit, StanleyParams, Stanley | Classical lateral trajectory tracking controllers (for comparison with the Werling controllers). |
| [`vdsim.stabilization.classic_longitudinal`](../../../vdsim/stabilization/classic_longitudinal.py) | 224 | _LongParams, LongitudinalBase, PIDParams, PID, PIParams, PI | Classical longitudinal trajectory tracking controllers (output: acceleration request). |
| [`vdsim.stabilization.common`](../../../vdsim/stabilization/common.py) | 130 | Desired, StepTimer | Shared helpers of the trajectory tracking controllers. |
| [`vdsim.stabilization.composite`](../../../vdsim/stabilization/composite.py) | 76 | CompositeParams, CompositeController | tracking_controller/composite: combination of a lateral and a longitudinal tracking controller. |
| [`vdsim.stabilization.errors`](../../../vdsim/stabilization/errors.py) | 87 | – | Invariant tracking errors in the Frenet frame of the desired trajectory (Werling 4.1.3, 4.2, 4.3). |
| [`vdsim.stabilization.plant`](../../../vdsim/stabilization/plant.py) | 159 | PlantParams, VehicleModelPlant | vehicle_plant/vehicle_model: any registered vdsim vehicle model as plant of the AD chain. |
| [`vdsim.stabilization.reinit`](../../../vdsim/stabilization/reinit.py) | 106 | ReinitMonitor | High-level part of the bi-level stabilization, controller side (Werling 2.3, 4.5). |
| [`vdsim.stabilization.simulate`](../../../vdsim/stabilization/simulate.py) | 151 | – | Lightweight closed-loop runners for tests and examples (independent of the graph executor). |
| [`vdsim.stabilization.switching`](../../../vdsim/stabilization/switching.py) | 139 | BilevelParams, WerlingBilevel | Speed dependent, bumpless switching of the Werling controllers and the re-initialization monitor (Werling 4.4, Fig. |
| [`vdsim.stabilization.trajectories`](../../../vdsim/stabilization/trajectories.py) | 213 | Path, SpeedProfile | Reference trajectories for tests and examples (no planner needed). |
| [`vdsim.stabilization.vehicle_layers`](../../../vdsim/stabilization/vehicle_layers.py) | 231 | SplitRangeParams, SplitRangeDynamics, ActuatorParams, _VectorDelay, SteeringPowertrainActuator | Vehicle dynamics and actuator layers (contracts.md section 1). |
| [`vdsim.stabilization.werling_dynamic`](../../../vdsim/stabilization/werling_dynamic.py) | 394 | ZeroDynamicsReference, DynamicParams, WerlingDynamic | Exact input/output linearization of the dynamic single-track model for fast driving (Werling 4.3.3). |
| [`vdsim.stabilization.werling_kinematic`](../../../vdsim/stabilization/werling_kinematic.py) | 296 | OrientationParams, CenterParams, _KinematicBase, WerlingKinematicOrientation, WerlingKinematicCenter | Lyapunov based trajectory tracking on the extended kinematic single-track model (Werling 4.2). |

### Abhängigkeiten

- nutzt: [actuators](../actuators/index.md), [controllers](../controllers/index.md), [core](../core/index.md), [framework](../framework/index.md), [powertrain](../powertrain/index.md), [simulation](../simulation/index.md), [tire_models](../tire_models/index.md), [vehicle_models](../vehicle_models/index.md)
- genutzt von: –
- externe Bibliotheken: `__future__`, `collections`, `dataclasses`, `math`, `numpy`, `scipy`, `time`, `types`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Vorzeichen in (4.31) als + e~n sin e~theta | nur so gilt die Kürzung im Lyapunov-Beweis; der gedruckte Ausdruck verletzt V_dot <= 0 für (k1 e_n)^2 > k3 k4 (numerisch im Test gezeigt) | gedrucktes Vorzeichen (Parameter sign_variant="printed", nur zu Demonstrationszwecken) |
| (4.60) über die Beschleunigung des Referenzpunkts in Fahrzeugkoordinaten gelöst | mathematisch äquivalent zu e~_dd = w~ (Kinematik des mitbewegten Frenet-Rahmens), vermeidet die symbolische zweite Ableitung | direkte Auswertung von L_f^2 e~ wie in Werling 4.3.3.1 |
| Reifeninversion über den Längsschlupfbetrag statt über F_q | äquivalent zu g(F_q) = 0 (4.43), monoton, ohne Wurzelsingularität und ohne Inverse der Kennlinie | Nullstellensuche in F_q mit inverser Kennlinie |
| Sättigungsmodifikation (Fußnote 17) nur an der Vorderachse im Regler, Strecke mit Kammschem Kreis | invertiert wird nach dem Eingang delta; Sättigung wird über den Modifikationsfaktor erkannt und der Lenkwinkel auf das Querkraftoptimum gesetzt | Modifikation an beiden Achsen (verfälscht die Hinterachskraft nahe dem Maximum) |
| DESM-Strecke in vx/vy-Koordinaten mit kinematischer Überblendung unter 1.5 m/s | identisch mit Modell 4 für v > 0, aber im Stand definiert (kein Schräglauf bei Stillstand) | Mindestgeschwindigkeit im Nenner (falsche Kräfte beim Lenken im Stand) |
| Reglerwahl nach PlannedTrajectory.reference_point und varsigma | Trajektorie und Regler bleiben konsistent (contracts.md Abschnitt 7) | reine Geschwindigkeitsschwelle v_d > v_s |

## Implementierung

- Skalare Hot-Path-Rechnung mit dem math-Modul (Regler 0.1-0.8 ms pro Schritt)
- Punktgrößen nach Bemerkung 6/8 aus den Modellgleichungen, nicht numerisch differenziert; nur die Vorsteuerung d delta0/dt und kappa~_d_dot numerisch
- Nulldynamik (4.72) mit Euler-Teilschritten <= 5 ms, Start mit den aktuellen Fahrzeugzuständen (Bemerkung 10)
- MPC-QP mit eigener dichter ADMM-Iteration (keine Zusatzpakete)

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`actuator/steering_powertrain`](components/actuator__steering_powertrain.md) | Lenkaktor und Antrieb/Bremse | 1.0.0 | Integriert die Lenkrate bzw. |
| [`tracking_controller/acc`](components/tracking_controller__acc.md) | Abstandsregeltempomat (ACC) | 1.0.0 | Abstandsbasierte Längsregelung mit konstanter Zeitlücke. |
| [`tracking_controller/composite`](components/tracking_controller__composite.md) | Kombination Quer- + Längsregler | 1.0.0 | Kombiniert einen beliebigen Quer- und Längsregler zu einem Trackingregler. |
| [`tracking_controller/ff_fb`](components/tracking_controller__ff_fb.md) | Vorsteuerung + Rückführung (längs) | 1.0.0 | Beschleunigungsvorsteuerung aus der Trajektorie mit Rückführung von Geschwindigkeits- und Längsfehler. |
| [`tracking_controller/lqr`](components/tracking_controller__lqr.md) | LQR (geschwindigkeitsgeplant) | 1.0.0 | Zustandsregler auf das Querfehlermodell des Einspurmodells mit diskreter Riccati-Lösung, Gain-Scheduling über die Geschwindigkeit und stationärer Vorsteuerung. |
| [`tracking_controller/mpc`](components/tracking_controller__mpc.md) | MPC (linear zeitvariant) | 1.0.0 | Linear zeitvariante modellprädiktive Querregelung entlang des Trajektorienhorizonts mit Lenkwinkel- und Lenkratenbeschränkung. |
| [`tracking_controller/pi`](components/tracking_controller__pi.md) | PI-Geschwindigkeitsregler | 1.0.0 | PI-Regler auf den Geschwindigkeitsfehler. |
| [`tracking_controller/pid`](components/tracking_controller__pid.md) | PID-Geschwindigkeitsregler | 1.0.0 | PID-Regler auf den Geschwindigkeitsfehler der Solltrajektorie. |
| [`tracking_controller/pure_pursuit`](components/tracking_controller__pure_pursuit.md) | Pure Pursuit | 1.0.0 | Geometrischer Querregler: Kreisbogen von der Hinterachse zu einem Zielpunkt auf der Bahn. |
| [`tracking_controller/speed_pi`](components/tracking_controller__speed_pi.md) | Fahrzeug-Geschwindigkeitsregler (PI mit Anti-Windup) | 1.0.0 | PI-Geschwindigkeitsregler mit Back-Calculation-Anti-Windup und Vorsteuerung. |
| [`tracking_controller/stanley`](components/tracking_controller__stanley.md) | Stanley | 1.0.0 | Querregler auf Vorderachs-Querfehler und Kurswinkelfehler (Stanley, DARPA Grand Challenge). |
| [`tracking_controller/werling_bilevel`](components/tracking_controller__werling_bilevel.md) | Werling: Bi-level-Stabilisierung (Umschaltung + Reinitialisierung) | 1.0.0 | Standard-Trackingregler: stoßfreie Umschaltung der drei Werling-Regler nach Referenzpunkt und Fahrtrichtung, dazu Reinitialisierungsauslösung und Bewegungsprädiktion für die Planung. |
| [`tracking_controller/werling_dynamic`](components/tracking_controller__werling_dynamic.md) | Werling: exakte E/A-Linearisierung (Satz 8) | 1.0.0 | Exakt E/A-linearisierender Trackingregler auf dem dynamischen Einspurmodell mit isotropem Pacejka-Reifen für schnelle Fahrt. |
| [`tracking_controller/werling_kinematic_center`](components/tracking_controller__werling_kinematic_center.md) | Werling: Lyapunov ohne Orientierungsstabilisierung (Satz 6) | 1.0.0 | Lyapunov-basierter Trackingregler der geometrischen Fahrzeugmitte ohne Orientierungsstabilisierung für langsame Vorwärtsfahrt. |
| [`tracking_controller/werling_kinematic_orientation`](components/tracking_controller__werling_kinematic_orientation.md) | Werling: Lyapunov mit Orientierungsstabilisierung (Satz 4) | 1.0.0 | Lyapunov-basierter Trackingregler der Hinterachsmitte mit Orientierungsstabilisierung für langsame Vorwärts- und Rückwärtsfahrt. |
| [`vehicle_dynamics/split_range`](components/vehicle_dynamics__split_range.md) | Split-Range-Längskraftumsetzung (Werling 5.1.2.2) | 1.0.0 | Setzt die Solllängskraft bzw. |
| [`vehicle_plant/vehicle_model`](components/vehicle_plant__vehicle_model.md) | Fahrzeugmodell (vdsim) | 1.0.0 | Umschließt ein registriertes vdsim-Fahrzeugmodell als Strecke der Wirkkette (ohne Durchgriff). |

### Verfahren und Konzepte

- [Acc](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Anti windup](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Backstepping](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Bi-level-Stabilisierung (Planerseite)](../planning/theory.md#bilevel_stabilization)
- [Klassische Trackingregler](theory.md#classic_tracking)
- [Composite](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Stoßfreie Reglerumschaltung](theory.md#controller_switching)
- [Desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Dynamic reference transform](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Exakte E/A-Linearisierung für schnelle Fahrt](theory.md#exact_io_linearization)
- [Feedforward](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Flat reference transform](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Invariant tracking error](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Dynamisches Einspurmodell mit isotropem Reifen](theory.md#isotropic_tire)
- [Erweitertes kinematisches Einspurmodell](theory.md#kesm)
- [Lqr lateral](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Lyapunov-Tracking ohne Orientierungsstabilisierung](theory.md#lyapunov_center)
- [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation)
- [Bewegungsprädiktion für die Reinitialisierung](../planning/theory.md#motion_prediction)
- [Mpc lateral](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Pid](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Pure Pursuit](../controllers/theory.md#pure_pursuit)
- [Reinitialisierung und Bewegungsprädiktion](theory.md#reinitialization_trigger)
- [Split-Range-Längskraftumsetzung](theory.md#split_range)
- [Stanley](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Steering actuator](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Vehicle plant](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Zero dynamics desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Zero dynamics kesm](../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Erweiterungspunkte

- Neue Trackingregler über @component(kind="tracking_controller") mit Basis TrackingControllerBase
- Weitere Strecken über vdsim.core.registry ("vehicle_model"), nutzbar via vehicle_plant/vehicle_model
- Fahrdynamiksysteme über split_range.systems (chassis_system-Registry)

## Verwandte Module

[planning](../planning/index.md), [geometry](../geometry/index.md), [framework](../framework/index.md), [vehicle_models](../vehicle_models/index.md), [tire_models](../tire_models/index.md), [actuators](../actuators/index.md), [controllers](../controllers/index.md)

## Hauptquellen

[Åström und Hägglund (2006)](../references.md#astrom2006), [Borrelli et al. (2017)](../references.md#borrelli2017), [Hoffmann et al. (2007)](../references.md#hoffmann2007), [Isidori (1995)](../references.md#isidori1995), [Khalil (2002)](../references.md#khalil2002), [Pacejka (2012)](../references.md#pacejka2012), [Rajamani (2012)](../references.md#rajamani2012), [Snider (2009)](../references.md#snider2009), [Stellato et al. (2020)](../references.md#stellato2020), [Werling et al. (2010)](../references.md#werling2010tro), [Werling (2011)](../references.md#werling2011)
