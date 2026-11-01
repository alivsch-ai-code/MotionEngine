# Simulationskern – Löser, Regelkreis, Szenarien, Ergebnisse – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Reglertakt und Modellschritt sind fest gekoppelt; Multi-Rate-Komponenten der AD-Plattform laufen über vdsim.runtime.
- Das vorausfahrende Fahrzeug fährt auf derselben Bahn (eindimensional entlang s).
- Das Fahrbahnprofil hängt nur von x ab (nicht von y, keine Wankanregung).

## Anwendungsgrenzen der Verfahren

### [Fahrbahnprofil nach ISO 8608](theory.md#iso8608_road_profile)

Wellenlängen zwischen etwa 0,35 m und 90 m; Klassen F–H der Norm sind nicht vorgesehen.

### [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta)

Für steife Systeme (Raddrehung bei sehr kleiner Geschwindigkeit) sind sehr kleine Schritte nötig; ein impliziter Löser wäre effizienter.

### [Ablauf eines Simulationsschritts](theory.md#simulation_loop)

Ein einziger Takt für alle Regler; Mehrfachraten und Komponentengraphen bietet die AD-Plattform (`vdsim.runtime`).

### [Stabilitätsbegrenzte Teilschritte (stable_dt)](theory.md#stable_substeps)

Die Schätzung gilt für die eingebauten Modelle. Eigene Modelle ohne `stable_dt` laufen mit `recommended_dt` oder `dt_control`.
