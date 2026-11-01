# Geometrie – Referenzkurven und Frenet-Koordinaten – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Die Transformation ist singulär für 1 − kappa_r d = 0 (Punkt im Krümmungsmittelpunkt) und für Kurswinkelfehler ±90°.
- Die Projektion ist lokal; ohne Suchhinweis wird global gesucht, bei Kurven mit Selbstannäherung kann der falsche Ast gewählt werden.
- offset() wirft einen Fehler, wenn der Versatz den Krümmungsradius erreicht.

## Anwendungsgrenzen der Verfahren

### [Projektion auf die Referenzkurve](theory.md#curve_projection)

Mehrdeutig bei Punkten, die mehreren Kurvenästen gleich nahe sind.

### [Frenet-Transformation in geschlossener Form](theory.md#frenet_transformation)

Nahe dem Krümmungsmittelpunkt ($d \to 1/\kappa_r$) und bei Querfahrt ($\Delta\theta \to \pm 90°$) singulär; Rückwärtsfahrt wird über die Bewegungsrichtung $\theta$ und die Fahrtrichtung der Trajektorie behandelt.

### [Hermite-interpolierte Referenzkurve](theory.md#hermite_reference_curve)

Die Bogenlänge der interpolierten Kurve weicht bei grober Abtastung minimal von $s$ ab.

### [Glatte Krümmungsübergänge](theory.md#smooth_curvature_profile)

Keine echten Klothoiden (die Krümmung ändert sich nicht linear).
