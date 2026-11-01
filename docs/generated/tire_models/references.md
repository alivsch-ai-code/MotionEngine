# Reifenmodelle – Quellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · **Quellen** · [Rückverfolgbarkeit](traceability.md)


| Zitat | Quelle | Typ | Verwendet in |
|---|---|---|---|
| [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | Mitschke, M.; Wallentowitz, H. (2014): Dynamik der Kraftfahrzeuge. 5. Auflage. Springer Vieweg. | Fachbuch | LinearTire.forces (module.yaml), module.yaml, theory.md, tire_model/linear |
| [Pacejka (2012)](../references.md#pacejka2012) | Pacejka, H. B. (2012): Tire and Vehicle Dynamics. Butterworth-Heinemann, 3. Auflage. ISBN 978-0-08-097016-5. | Fachbuch | BrushTire.forces (module.yaml), PacejkaTire.cornering_stiffness (module.yaml), PacejkaTire.forces (module.yaml), magic_formula (module.yaml), module.yaml, theory.md, tire_model/brush, tire_model/pacejka |
| [Schramm et al. (2018)](../references.md#schramm2018) | Schramm, D.; Hiller, M.; Bardini, R. (2018): Modellbildung und Simulation der Dynamik von Kraftfahrzeugen. Springer Vieweg. | Fachbuch | module.yaml, theory.md |
| [Werling (2011)](../references.md#werling2011) | Werling, M. (2011): Ein neues Konzept für die Trajektoriengenerierung und -stabilisierung in zeitkritischen Verkehrsszenarien. Dissertation. KIT Scientific Publishing (Schriftenreihe des Instituts für Angewandte Informatik / Automatisierungstechnik, Band 34). ISBN 978-3-86644-631-1. https://publikationen.bibliothek.kit.edu/1000021738. | Dissertation / Abschlussarbeit | force_magnitude (@trace), lateral_force (@trace) |
