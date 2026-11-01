# Geometrie – Referenzkurven und Frenet-Koordinaten

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.geometry` · Quellcode: [vdsim/geometry/](../../../vdsim/geometry) · Paketdoku: [vdsim/geometry/docs/](../../../vdsim/geometry/docs)

## Übersicht

**Glatte Referenzkurve r(s) mit Projektion und geschlossener Frenet-Transformation nach Werling (2011), Anhang A.**

Trajektorienplanung, Trackingregelung und Szenario-Engine beschreiben Bewegungen relativ zu einer
Referenzkurve (Bahnkoordinaten s, d). Die Planung nach Werling verlangt dafür eine Kurve mit stetiger
Krümmungsableitung (Bemerkung 4, Abschn. 3.5.3) und eine Transformation ohne numerisches Differenzieren.
`ReferenceLine` liefert beides und wird von planning, stabilization, world und behavior genutzt.

Paket-Docstring:

```text
Geometry shared by planning, control and the scenario engine: reference curves and Frenet frames.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 2 |
| Komponenten | 0 |
| Verfahren/Konzepte | 4 |
| @trace-Einträge | 6 |
| Tests | 6 |
| Beispiele | 7 |

## Architektur

- `ReferenceLine`: Stützstellen (s, x, y, theta, kappa, dkappa); kubische Hermite-Interpolation von x, y mit
  exakten Tangenten, von theta mit kappa und von kappa mit dkappa.
- Projektion (A.2): Suche der nächsten Stützstelle, Sekantenverfahren auf linear interpolierten [x, y, theta],
  Newton-Verfeinerung auf der Hermite-Kurve; `project_many()` vektorisiert.
- Frenet-Transformation (A.1): `to_frenet()` und `to_cartesian()` in geschlossener Form, `time_to_arc()` / `arc_to_time()`.
- Abgeleitete Kurven: `offset()` (Parallelkurve), `segment()`, `reversed()`, `resample()`.
- Konstruktoren: `from_curvature()`, `from_segments()` (Smoothstep-Krümmungsübergänge), `from_points()` (quintischer Glättungsspline), `straight()`, `circle()`.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.geometry`](../../../vdsim/geometry/__init__.py) | 6 | – | Geometry shared by planning, control and the scenario engine: reference curves and Frenet frames. |
| [`vdsim.geometry.reference_line`](../../../vdsim/geometry/reference_line.py) | 458 | FrenetState, ReferenceLine | Reference curve r(s) with projection and Frenet <-> world transformations. |

### Abhängigkeiten

- nutzt: [framework](../framework/index.md)
- genutzt von: [behavior](../behavior/index.md), [framework](../framework/index.md), [perception](../perception/index.md), [planning](../planning/index.md), [prediction](../prediction/index.md), [world](../world/index.md)
- externe Bibliotheken: `__future__`, `dataclasses`, `numpy`, `scipy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Hermite-Interpolation mit exakten Ableitungen statt linearer Interpolation | Position, Kurswinkel und Krümmung sind zwischen den Stützstellen glatt; Werling Bemerkung 4 verlangt stetiges dkappa | lineare Interpolation (Krümmungssprünge), globale Splines (teurer bei Änderungen) |
| Sekantenverfahren nach Werling A.2 plus Newton-Schritte | robuster Startwert aus der Polylinie, dann quadratische Konvergenz auf der glatten Kurve | – |
| Gerade Fortsetzung außerhalb der Kurve | Projektionen bleiben auch hinter Anfang und Ende definiert | – |

## Implementierung

- Gleichmäßige Abtastung wird erkannt; der Segmentindex wird dann ohne Suche berechnet.
- Geschlossene Kurven wickeln s modulo Länge; die Projektion sucht zyklisch um den Hinweisindex.
- Smoothstep-Rampen 3u² − 2u³ für Krümmungsübergänge, zentriert auf die Segmentgrenzen, damit jeder Bogen exakt den Winkel kappa · L hat.

### Verfahren und Konzepte

- [Projektion auf die Referenzkurve](theory.md#curve_projection)
- [Frenet-Transformation in geschlossener Form](theory.md#frenet_transformation)
- [Hermite-interpolierte Referenzkurve](theory.md#hermite_reference_curve)
- [Glatte Krümmungsübergänge](theory.md#smooth_curvature_profile)

## Erweiterungspunkte

- Weitere Konstruktoren (z. B. aus OpenDRIVE-Fahrstreifen) als Klassenmethoden, die (s, x, y, theta, kappa, dkappa) liefern

## Verwandte Module

[framework](../framework/index.md), [trajectory](../trajectory/index.md)

## Hauptquellen

[de Boor (2001)](../references.md#deboor2001), [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011)
