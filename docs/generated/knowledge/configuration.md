# Wissens-, Dokumentations- und Rückverfolgbarkeitssystem – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `python tools/build_docs.py [--check] [--report] [--explain X] [--path A B] [--search T] [--bibtex F] [--init P] [--no-import]` | Kommandozeile (siehe docs/KNOWLEDGE.md) | – | – |
| `VDSIM_CACHE_DIR` | Ordner für den Formel-Cache (Standard %LOCALAPPDATA%/vdsim/cache bzw. ~/.cache/vdsim) | – | – |
| `docs/references/user.yaml, docs/references/links.yaml` | Benutzerreferenzen und Verknüpfungen Referenz → Ziel | – | – |
