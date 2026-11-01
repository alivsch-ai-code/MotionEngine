# Antriebsstrang, Bremse und Längsaktuierung – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `powertrain.*` | Antriebsart, Layout, Kennlinien, Übersetzungen, E-Motor- und Rekuperationsgrenzen (Parametersatz PowertrainParameters im Paket core) | – | – |
| `brakes.*` | maximale Bremsmomente, Bremskraftverteilung, EBV (BrakeParameters) | – | – |
