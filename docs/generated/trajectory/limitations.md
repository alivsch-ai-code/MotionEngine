# Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Ideallinie nur als minimale Krümmung (kein Zeitoptimum, keine Fahrzeugdynamik).
- Projektion auf die Polylinie ist stückweise linear (Kurswinkel linear interpoliert); für Planungsaufgaben ist vdsim.geometry.ReferenceLine genauer.
- GPS-Import mit äquirektangulärer Projektion (genau für wenige Kilometer).
- {'OpenDRIVE': 'nur Referenzlinie und Fahrstreifenmitten einer Straße, keine Kreuzungen und Höhenprofile.'}

## Anwendungsgrenzen der Verfahren

### [GGV-begrenztes Geschwindigkeitsprofil](theory.md#ggv_speed_profile)

Keine Fahrzeugdynamik (Lastverlagerung, Gierträgheit).

### [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction)

Kleine-Winkel-Näherung des Versatzes: bei großem $w/L$ weicht der tatsächliche Versatz leicht ab.

### [Projektion auf die Polylinie](theory.md#polyline_projection)

Kurswinkel und Krümmung sind stückweise linear; für Werling-Planung ist die Hermite-Referenzkurve in vdsim.geometry vorgesehen.

### [Ideallinie mit minimaler Krümmung](theory.md#racing_line)

Minimale Krümmung ist nicht gleich minimaler Rundenzeit (kürzester Weg wird ignoriert).

### [Import von GPS- und OpenDRIVE-Daten](theory.md#trajectory_import)

Fehler wachsen mit der Entfernung vom Bezugspunkt; Höhen werden ignoriert.
