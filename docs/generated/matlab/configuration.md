# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `backend` | interpreter (Originallogik) oder python (generierter Code) beim Laden als Komponente | – | – |
| `params` | Eingänge der MATLAB-Funktion, die als konstante Komponentenparameter gesetzt werden | – | – |
| `input_types` | Typhinweise für Eingänge (scalar, vector, row, matrix) | – | – |
| `VDSIM_CXX` | Umgebungsvariable mit dem Pfad zu einem C++-Compiler | – | – |
