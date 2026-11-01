# Wissens-, Dokumentations- und Rückverfolgbarkeitssystem – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Konzepte werden über ihre ID verknüpft; gleiche Verfahren mit verschiedenen IDs erkennt das System nicht.
- Die Testzuordnung über Importe ist grob (ein Test, der ein Modul importiert, gilt als dessen Test).
- Formeln nur im matplotlib-mathtext-Umfang (keine Umgebungen wie aligned oder Matrizen).
- Der Markdown-Konverter unterstützt kein eingebettetes HTML und keine verschachtelten Blockelemente in Listen.

## Anwendungsgrenzen der Verfahren

### [Kräftebasiertes Graphlayout](theory.md#force_directed_layout)

Große, dichte Graphen werden unübersichtlich; deshalb Filter und Nachbarschaftsansicht.

### [Graphmodell des Wissens](theory.md#knowledge_graph_model)

Semantische Ähnlichkeit (gleiches Verfahren unter anderem Namen) wird nicht erkannt.

### [Rückverfolgbarkeitsmodell](theory.md#traceability_model)

Keine Anforderungsebene (Lastenheft); Tests werden über Importe zugeordnet, nicht über Abdeckung.
