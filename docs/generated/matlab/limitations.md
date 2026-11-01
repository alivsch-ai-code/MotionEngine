# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Keine Klassen (classdef), kein eval, keine Struct-Arrays, Zellen nur eindimensional (Python), keine Ganzzahltypen (int32 usw.), keine N-D-Arrays (> 2 Dimensionen)
- C++/Rust nur Skalare, logische Skalare und reelle Matrizen; keine Strings außer Literalen in fprintf/disp/error, keine Zellen/Structs/globale Variablen/try-catch/verschachtelten Funktionen, keine Bereichs- oder logische Indizierung, kein Wachsen von Arrays
- Komplexe Zahlen nur im Interpreter
- Python-Ziel: Division durch 0 sowie Definitionsbereichsfehler (sqrt/log negativ) lösen Ausnahmen aus, wo MATLAB Inf/NaN bzw. komplexe Werte liefert
