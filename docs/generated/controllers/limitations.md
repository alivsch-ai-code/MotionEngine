# Regler, Fahrerassistenz und Fahrwerksregelsysteme – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Die MPC rechnet mit linearen Reifen; am Haftlimit ist Stanley robuster.
- Die Regler sehen den wahren Fahrzeugzustand (keine Sensormodelle, kein Rauschen).
- ABS/ASR benötigen ein Modell mit Raddynamik (double_track, multibody).
- ESP greift nur an einem Rad gleichzeitig ein und reduziert das Antriebsmoment pauschal um 30 %.
- Der Krümmungsschätzer kennt die Latenz der Wirkkette; in der Praxis muss sie geschätzt werden.

## [MPC](components/lateral_controller__mpc.md)

Grenzen:

- Lineare Reifen im Vorhersagemodell
- konstante Geschwindigkeit über den Horizont

## [Pure Pursuit](components/lateral_controller__pure_pursuit.md)

Grenzen:

- Schneidet Kurven bei großer Vorausschau
- kein Schwimmwinkel berücksichtigt

## [Stanley](components/lateral_controller__stanley.md)

Annahmen:

- Vorwärtsfahrt
- Referenzbahn mit Krümmung

Grenzen:

- Bei sehr kleiner Geschwindigkeit begrenzt nur die Softening-Konstante die Verstärkung

## Anwendungsgrenzen der Verfahren

### [Abstandsregeltempomat und Notbremsassistent](theory.md#acc_aeb)

Ein Vorderfahrzeug, keine Einscherer, keine Sensorlatenz.

### [Aktives Fahrwerk: Wankstabilisierung und Skyhook](theory.md#active_suspension)

Unbegrenzte Aktorkraft; keine Energiebetrachtung.

### [Rückkanal-Korrektur des Krümmungsfehlers](theory.md#curvature_feedback_correction)

Nichtlineare Kennlinien werden nur lokal korrigiert; unbekannte oder veränderliche Latenz verfälscht die Schätzung.

### [ESP – Gierratenregelung durch Einzelradbremsung](theory.md#esp_yaw_control)

Keine Schwimmwinkelregelung, keine Schätzung des Reibwerts.

### [Spurhalteassistent mit Fahrermodell](theory.md#lane_keeping_assist)

Keine Fahrerübersteuerung, keine Markierungserkennung.

### [Modellprädiktive Bahnregelung (lineare MPC)](theory.md#path_mpc)

Am Haftlimit falsch (lineare Reifen); Geschwindigkeitsänderungen innerhalb des Horizonts werden ignoriert.

### [Pure Pursuit](theory.md#pure_pursuit)

Kurvenschneiden bei großer Vorausschau; ohne Schwimmwinkel- und Dynamikmodell.

### [Hinterachslenkung](theory.md#rear_axle_steering)

Keine dynamische (zustandsabhängige) Ansteuerung.

### [Geschwindigkeitsregelung (PI mit Vorsteuerung)](theory.md#speed_control)

Keine Ruckbegrenzung.

### [Stanley-Bahnregler](theory.md#stanley_controller)

Bis in den Grenzbereich robust; bei Rückwärtsfahrt nicht definiert.

### [Torque Vectoring](theory.md#torque_vectoring)

Wirkt nur bei Antriebsmoment; im Schub keine Momentenverteilung.

### [Schlupfregelung ABS und ASR](theory.md#wheel_slip_control)

Keine Fahrzeugreferenzgeschwindigkeits-Schätzung, keine Select-Low-Logik an der Hinterachse.
