# Auswertung und Berichte – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Die ISO-2631-Bewertung nutzt nur die Vertikalbeschleunigung des Aufbauschwerpunkts (kein Sitz, keine Mehrachsenbewertung) und lässt die Bandbegrenzung bei 100 Hz weg.
- Die Komfortskala ist als nicht überlappende Stufen vereinfacht (die Norm nennt überlappende Bereiche).
- Normtests werden nach den Hauptkriterien bewertet, nicht nach allen Durchführungsbestimmungen (z. B. Einfahrgeschwindigkeitstoleranz, Wiederholungen).

## Anwendungsgrenzen der Verfahren

### [Frequenzgang aus dem Sinus-Sweep](theory.md#frequency_response_estimation)

Im nichtlinearen Bereich (große Amplituden) ist der Frequenzgang amplitudenabhängig.

### [Reibwertausnutzung und Stabilitätsreserve](theory.md#friction_utilization)

Die Magic Formula kann Werte leicht über 1 erzeugen (kombinierter Schlupf).

### [Komfortbewertung nach ISO 2631-1](theory.md#iso2631_comfort)

Bandbegrenzung bei 100 Hz ($f_2$) fehlt; keine Sitzübertragung, keine Mehrachsen-Gesamtbewertung, kein Crest-Faktor/VDV.

### [Kennwerte der Normversuche](theory.md#iso_test_kpis)

Hauptkriterien ohne vollständige Durchführungsregeln (Toleranzen, Wiederholungen, Fahrerkorrekturen).
