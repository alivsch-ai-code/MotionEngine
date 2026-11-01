# Forschungsmodus – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `Job.scenario / scenario_params / stack / seed / duration / snapshots / save_dir` | Definition eines Laufs | – | – |
| `monte_carlo(distributions)` | Verteilungen je Pfad: uniform(low, high), normal(mean, std, low?, high?), lognormal, choice, integer | – | – |
