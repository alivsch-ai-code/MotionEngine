# Komponenten-Framework der AD-Plattform – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `Spec-String` | kind/name, kind/name@1.2.0, kind/name@^1, kind/name@~1.2, kind/name@>=1.0; python:datei.py:Klasse, cpp:, rust:, matlab: | – | – |
| `PERIOD` | Aufrufperiode einer Komponente, None = jeder Executor-Schritt | s | – |
