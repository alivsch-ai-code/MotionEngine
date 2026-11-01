# Trajektorienplanung nach Werling – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- zeitliche Konsistenz nur bei inaktiven Restriktionen und ausschließlich konsistenten Kostentermen
- Funktionenklasse auf doppelte Kursänderung beschränkt; enge, labyrinthartige Situationen sind nicht lösbar (3.5.4)
- in blockierten Situationen (viele kollidierende Kandidaten) steigt die Rechenzeit auf 100–300 ms
- zeitdiskrete Kollisionsprüfung (Raster 0.1 s), Kreisapproximation konservativ
- Richtungswechsel nur im Stillstand über die Verhaltensebene; Ein- und Ausparken mit großen Differenzwinkeln nicht vorgesehen
- Regimewechsel cog ↔ rear_axle mit kleinem Positionssprung (vernachlässigter Schwimmwinkel l_h κ)

## [Kreisapproximation (Ziegler/Stiller)](components/collision_checker__circles.md)

Annahmen:

- Schwimmwinkel am Referenzpunkt = 0 (Ausrichtung = Trajektorienrichtung)
- Objekte als Rechtecke entlang ihrer prädizierten Ausrichtung

Grenzen:

- zeitdiskrete Prüfung: bei sehr hohen Relativgeschwindigkeiten kann ein Durchtunneln zwischen zwei Abtastpunkten auftreten (Raster collision.dt verkleinern)

## [Fahrzeugumriss im Korridor](components/constraint__vehicle_envelope.md)

Annahmen:

- Ecken in Frenet-Koordinaten mit der Ausrichtung relativ zur Straße genähert (Krümmung der Referenzkurve über die Fahrzeuglänge vernachlässigt)

## [Fahrstabilität (lineares ESM)](components/constraint__vehicle_stability.md)

Annahmen:

- lineares Einspurmodell, stationäre Kurvenfahrt
- Achs-Schräglaufsteifigkeit = 2 x Reifen

## [Energieeffizienz](components/cost_term__energy.md)

Annahmen:

- Bahngeschwindigkeit ≈ ṡ
- ebene Straße

## [Frenet-Planer (naiv, ohne Konsistenz)](components/trajectory_planner__frenet_naive.md)

Grenzen:

- keine zeitliche Konsistenz: Ergebnis hängt von der Neuplanungsfrequenz ab
- Regelfehler werden in jedem Zyklus zu Null gesetzt (keine Low-level-Robustheit)

## [Sequentieller Planer (erst längs, dann quer)](components/trajectory_planner__sequential.md)

Grenzen:

- Längskandidaten lexikographisch vor Querkandidaten sortiert

## [Trajektorienplaner (Werling)](components/trajectory_planner__werling.md)

Annahmen:

- Schwimmwinkel am Referenzpunkt = 0 für die Kollisionsprüfung
- Vorderfahrzeuge mit konstanter Beschleunigung (geklemmt im Stillstand)
- Referenzkurve mit stetiger Krümmungsänderung (Bemerkung 4)

Grenzen:

- zeitliche Konsistenz nur bei inaktiven Restriktionen und rein konsistenten Kostentermen
- Funktionenklasse auf doppelte Kursänderung beschränkt (keine Labyrinth-Manöver)
- Richtungswechsel (ς) nur im Stillstand über die Verhaltensebene

## Anwendungsgrenzen der Verfahren

### [Absolutes Endzeitraster](theory.md#absolute_time_grid)

Die Konsistenz bleibt nur bei gleicher Referenzkurve und gleichem Quermodus erhalten.

### [Zeitliche Konsistenz (Bellman-Prinzip)](theory.md#bellman_principle)

Aktive Restriktionen, Änderungen der Referenzkurve, Reinitialisierung und Zusatzkostenterme brechen die Konsistenz.

### [Bi-level-Stabilisierung (Planerseite)](theory.md#bilevel_stabilization)

Ohne Reglerrückführung (Rückführungs-Port) gibt es nur Low-level-Verhalten.

### [Kombination und Rücktransformation](theory.md#candidate_combination)

Bei $N_d\cdot N_s$ Kombinationen (etwa 10⁴) entscheidet die Lazy-Strategie über die Laufzeit.

### [Kollisionsprüfung mit Kreisen](theory.md#collision_circles)

Die Prüfung ist zeitdiskret und konservativ an den Ecken.

### [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold)

(3.13) ist für allgemeine $\xi_{ref}$ nicht geschlossen lösbar. Der Planer verwendet daher die diskretisierte Mannigfaltigkeit, `analysis` die kontinuierliche Lösung.

### [Korridor-Restriktion](theory.md#corridor_constraint)

In engen Kurven mit großer Fahrzeuglänge ist die Prüfung ungenau.

### [Rückfallebene](theory.md#fallback)

Ist eine Kollision physikalisch unvermeidbar, wird nur die Aufprallgeschwindigkeit reduziert.

### [Folgemodus](theory.md#following_mode)

Die Annahme konstanter Beschleunigung verliert bei langen Horizonten an Genauigkeit.

### [Ruckintegral in geschlossener Form](theory.md#jerk_integral)

Im d(s)-Modus ist es ein Integral über die Bogenlänge mit der Einheit m⁻³.

### [Fahrphysikalische Restriktionen](theory.md#kinematic_constraints)

Ruck und Lenkrate werden über Differenzenquotienten auf dem Raster bestimmt.

### [Querkandidaten d(t) und d(s)](theory.md#lateral_sampling)

d(s) erzeugt nur Querbewegung bei Längsbewegung; im Stillstand bleibt d konstant.

### [Lazy-Auswahl](theory.md#lazy_selection)

Bei blockierter freier Lösung werden Tausende Kandidaten geprüft (Werling: z. B. Trajektorie 3621 von 4847).

### [Einrasten auf der Referenz](theory.md#lock_in)

Die Prüfung ist konservativ, weil das Verharren mit $\tau_{min}$ angesetzt wird.

### [Längskandidaten](theory.md#longitudinal_sampling)

Ein Modus ohne Prädiktion des Bezugsobjekts entfällt (`PlannerDebug.modes[...]["reason"]`).

### [Einfädeln](theory.md#merging_mode)

Ob die Lücke ausreicht, bewertet die Verhaltensebene.

### [Bewegungsprädiktion für die Reinitialisierung](theory.md#motion_prediction)

Nur kurze Zeiträume (Rechenzeit, etwa 0.1 s).

### [Mehrzielige Kostenfunktion](theory.md#multi_objective_cost)

Das Re-Ranking optimiert nur innerhalb des Fensters.

### [Quartische Optimalpolynome](theory.md#quartic_polynomial)

Nur für den Modus Geschwindigkeithalten.

### [Quintische Optimalpolynome](theory.md#quintic_polynomial)

Für sehr kleine $\tau$ werden die Koeffizienten numerisch extrem ($\tau^{-5}$). Solche Kandidaten sortiert der Vorfilter aus.

### [Referenzpunkt und Geschwindigkeitsregime](theory.md#reference_point)

Der Schwimmwinkel wird für die Geometrie vernachlässigt.

### [Ablösestrategie](theory.md#replacement_strategy)

Kann ein Modus wegen grober Abtastung nur stark bremsen, setzt er sich durch. Deshalb gibt es das grobe ν-Raster bis zum Stillstand.

### [Rampe des Sicherheitsabstands](theory.md#safety_margin_ramp)

Ein zu kleines $\Delta t$ wirkt schreckhaft, ein zu großes träge.

### [Abschätzung des Sampling-Horizonts](theory.md#sampling_horizon)

Heuristische Wahl der Repräsentanten.
