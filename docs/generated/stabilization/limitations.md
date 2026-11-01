# Trajektorienstabilisierung nach Werling und Fahrzeugebenen – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Stellgrößenbeschränkungen nicht in den Werling-Regelgesetzen (Reserve durch Planung/Reinitialisierung)
- Dynamischer Regler nur vorwärts und für v_d >= v_min_dynamic; darunter kinematischer Rückfall
- Rückwärtsfahrt nur mit Strecken, die rückwärts fahren können (werling_kesm, bicycle_kinematic; werling_desm nur langsam)
- Klassische Regler nur vorwärts

## [Lenkaktor und Antrieb/Bremse](components/actuator__steering_powertrain.md)

Annahmen:

- Konstanter Schritt dt (Komponentenperiode bzw. Executor-Schritt)

Grenzen:

- Kennlinienfehler wirkt auf die Krümmung tan(delta)/l (wie vdsim.actuators)

## [Abstandsregeltempomat (ACC)](components/tracking_controller__acc.md)

Annahmen:

- Vorderfahrzeug im Fahrschlauch der Trajektorie

Grenzen:

- Keine Kollisionsfreiheit garantiert

## [Kombination Quer- + Längsregler](components/tracking_controller__composite.md)

Annahmen:

- Quer- und Längsdynamik entkoppelt

Grenzen:

- Kopplung (Kammscher Kreis) unberücksichtigt

## [Vorsteuerung + Rückführung (längs)](components/tracking_controller__ff_fb.md)

Annahmen:

- Vorwärtsfahrt

Grenzen:

- Stellbeschränkungen nur geklemmt

## [LQR (geschwindigkeitsgeplant)](components/tracking_controller__lqr.md)

Annahmen:

- Lineare Reifen, kleine Winkel, Vorwärtsfahrt

Grenzen:

- Linearisierung, Modell singulär bei v -> 0 (v_min)

## [MPC (linear zeitvariant)](components/tracking_controller__mpc.md)

Annahmen:

- Kinematik mit Untersteuergradient (quasi-stationäre Gierdynamik)
- Vorwärtsfahrt

Grenzen:

- Kein Stabilitätsbeweis ohne Endkosten/Endbeschränkung
- Rechenaufwand höher

## [PI-Geschwindigkeitsregler](components/tracking_controller__pi.md)

Annahmen:

- Vorwärtsfahrt

Grenzen:

- Keine Vorsteuerung

## [PID-Geschwindigkeitsregler](components/tracking_controller__pid.md)

Annahmen:

- Vorwärtsfahrt

Grenzen:

- Keine Vorsteuerung, Schleppfehler in e_t

## [Pure Pursuit](components/tracking_controller__pure_pursuit.md)

Annahmen:

- Kinematisches Fahrzeug, Vorwärtsfahrt

Grenzen:

- Schneidet Kurven, stationärer Querfehler bei großer Vorausschau
- Keine Rückwärtsfahrt

## [Fahrzeug-Geschwindigkeitsregler (PI mit Anti-Windup)](components/tracking_controller__speed_pi.md)

Annahmen:

- Vorwärtsfahrt

Grenzen:

- Kein Positionsfehler

## [Stanley](components/tracking_controller__stanley.md)

Annahmen:

- Vorwärtsfahrt

Grenzen:

- Keine Rückwärtsfahrt, kinematische Herleitung

## [Werling: Bi-level-Stabilisierung (Umschaltung + Reinitialisierung)](components/tracking_controller__werling_bilevel.md)

Annahmen:

- Planer setzt reference_point mit Hysterese um v_s (contracts.md Abschnitt 7)
- Planer beantwortet reinit_request mit einer Trajektorie mit reinitialized=True

Grenzen:

- Harte Umschaltung: kleine Stellgrößensprünge möglich, Verstärkungen abgestimmt
- Schwellwerte c_t, c_n experimentell (Standardwerte für die Mittelklasselimousine)

## [Werling: exakte E/A-Linearisierung (Satz 8)](components/tracking_controller__werling_dynamic.md)

Annahmen:

- Ebene Fahrbahn, keine dynamischen Radlasten (Einspurmodell)
- Reifenparameter A, B, C je Achse bekannt (Certainty Equivalence)
- Antriebs-/Bremskräfte schnell eingeregelt, Kräfteverhältnis gamma bekannt
- v > 0 (Vorwärtsfahrt, singulär bei v = 0)

Grenzen:

- Nur lokal (Reifensättigung, Bedingung (4.49))
- Stellgrößenbeschränkungen nicht im Regelgesetz
- Nulldynamik nur für Geradeausfahrt linear analysiert (Satz 9)

## [Werling: Lyapunov ohne Orientierungsstabilisierung (Satz 6)](components/tracking_controller__werling_kinematic_center.md)

Annahmen:

- Kinematisches Einspurmodell, |beta~| < pi/2 (durch die Lenkwinkelgrenze erfüllt)
- Nur Vorwärtsfahrt, |kappa_d| < 1/lambda (Satz 7)

Grenzen:

- Rückwärts instabile Nulldynamik (Taschenmessereffekt)
- Orientierung nur über die Nulldynamik stabil (|psi - psi_d| <= pi/2 zu Beginn)

## [Werling: Lyapunov mit Orientierungsstabilisierung (Satz 4)](components/tracking_controller__werling_kinematic_orientation.md)

Annahmen:

- Keine Reifenschräglaufwinkel (langsame Fahrt, kinematisches Einspurmodell)
- Alle Zustände gemessen, Lenkwinkel |delta| < pi/2
- Antriebs- und Bremskräfte werden von unterlagerten Regelkreisen schnell eingestellt

Grenzen:

- Front schwenkt bei großen Korrekturen aus (Referenzpunkt Hinterachse)
- Keine Stellgrößenbeschränkung im Regelgesetz (Reserve durch die Planung)
- Für schnelle Fahrt ungeeignet (Schräglauf vernachlässigt)

## [Split-Range-Längskraftumsetzung (Werling 5.1.2.2)](components/vehicle_dynamics__split_range.md)

Annahmen:

- Antriebsstrangdynamik vernachlässigt (Momente wirken unverzögert, Werling 5.1.2.2)
- Bremskraftverteilung fest gamma (Standard 0.75)

Grenzen:

- Kein Motorkennfeld F_M^-1 / Getriebe-Schleppmoment (Momentenschnittstelle)

## [Fahrzeugmodell (vdsim)](components/vehicle_plant__vehicle_model.md)

Annahmen:

- Stellgrößen über einen Executor-Schritt konstant (Halteglied)

Grenzen:

- Rückwärtsfahrt nur mit werling_kesm, bicycle_kinematic (werling_desm nur langsam)
- Störkräfte nur bei Modellen mit Zuständen vy und r

## Anwendungsgrenzen der Verfahren

### [Klassische Trackingregler](theory.md#classic_tracking)

Keine Stabilitätsgarantie im Nichtlinearen (außer Stanley kinematisch), keine Rückwärtsfahrt.

### [Stoßfreie Reglerumschaltung](theory.md#controller_switching)

Harte Umschaltung; Sprünge klein, aber nicht null.

### [Exakte E/A-Linearisierung für schnelle Fahrt](theory.md#exact_io_linearization)

Lokal (Reifensättigung); Nulldynamik nur für Geradeausfahrt linear analysiert.

### [Dynamisches Einspurmodell mit isotropem Reifen](theory.md#isotropic_tire)

Mittlere bis hohe Geschwindigkeit; Rückwärtsfahrt nur langsam (kinematischer Bereich).

### [Erweitertes kinematisches Einspurmodell](theory.md#kesm)

Bis etwa 3 m/s bzw. kleine Querbeschleunigung; bei schneller Fahrt wird der Schräglauf relevant.

### [Lyapunov-Tracking ohne Orientierungsstabilisierung](theory.md#lyapunov_center)

Nur vorwärts; Orientierung nur über die Nulldynamik stabil.

### [Lyapunov-Tracking mit Orientierungsstabilisierung](theory.md#lyapunov_orientation)

Langsame Fahrt; die Fahrzeugfront schwenkt bei großen Korrekturen aus.

### [Reinitialisierung und Bewegungsprädiktion](theory.md#reinitialization_trigger)

Schwellwerte fahrzeug- und reglerspezifisch (hier für die Mittelklasselimousine eingestellt).

### [Split-Range-Längskraftumsetzung](theory.md#split_range)

Kein Motorkennfeld/Schleppmoment (Momentenschnittstelle der vdsim-Strecken).
