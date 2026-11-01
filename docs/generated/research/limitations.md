# Forschungsmodus – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- TTC/Zeitlücke betrachten Objekte im vom Ego überstrichenen Korridor in Fahrzeuglängsrichtung (keine Kurvenprädiktion).
- PET wird über die minimale Zeitdifferenz an räumlich nahen Bahnpunkten (Abtastung 0.2 s) bestimmt.
- Die Sensitivität ist linear (keine Wechselwirkungen, keine Sobol-Indizes).

## Anwendungsgrenzen der Verfahren

### [Vollfaktorieller Versuchsplan](theory.md#full_factorial_design)

Ab etwa 3–4 Parametern ist Monte Carlo oder ein teilfaktorieller Plan sinnvoller.

### [Monte-Carlo-Simulation und Sensitivität](theory.md#monte_carlo)

Die Sensitivität ist linear. Nichtlineare Effekte erfordern varianzbasierte Indizes, z. B. Sobol.

### [Abstand orientierter Rechtecke](theory.md#rectangle_distance)

Spiegel und Anhänger werden nicht abgebildet.

### [Surrogate Safety Measures](theory.md#surrogate_safety_measures)

TTC unterstellt konstante Geschwindigkeiten. Bei stark bremsendem Vorderfahrzeug unterschätzt sie das Risiko.
