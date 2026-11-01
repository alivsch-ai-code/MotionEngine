# Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Keine kontinuierlichen Zustände mit variabler Schrittweite; Integration erfolgt in den Komponenten
- Algebraische Schleifen werden gemeldet, nicht gelöst
- Hot Reload lädt nur die Node-Datei neu, nicht von ihr importierte Hilfsmodule
- Native Nodes nur für Typen mit flachem Codec (BehaviorCommand, PlannerDebug fehlen)
- Native Eingänge werden als unveränderlich betrachtet (Kodierungs-Cache bei identischem Objekt)
- C++-Build benötigt das Windows SDK (UCRT-Header) bzw. g++/clang++

## Anwendungsgrenzen der Verfahren

### [Algebraische Schleifen](theory.md#algebraic_loop)

Schleifen werden nicht iterativ gelöst; echte algebraische Gleichungssysteme müssen in einer Komponente gelöst werden.

### [C-ABI der nativen Custom Nodes](theory.md#c_abi)

Typen mit Zeichenketten oder verschachtelten Objekten (BehaviorCommand, PlannerDebug) haben noch keinen Codec.

### [Versionierungsmodell](theory.md#content_addressed_versioning)

Keine Verzweigungen oder Zusammenführungen; dafür ist Git zuständig.

### [Determinismus](theory.md#deterministic_execution)

Ein Echtzeitlauf mit `advance()` ist bis auf die Anzahl der gerechneten Schritte deterministisch.

### [Diskrete Grundblöcke](theory.md#discrete_blocks)

Der Euler-Integrator ist für $K T_s > 2$ in einem Regelkreis mit Verstärkung 1 instabil.

### [Hot Reload](theory.md#hot_reload)

Von der Node-Datei importierte Hilfsmodule werden nicht neu geladen.

### [Multi-Rate und Halteglied](theory.md#multirate_zoh)

Keine Ratenübergangsblöcke mit Interpolation; Aliasing beim Unterabtasten wird nicht verhindert.

### [Ausführungsmodell und Zeitdiskretisierung](theory.md#synchronous_dataflow)

Steife oder ereignisgetriebene Systeme mit variabler Schrittweite werden nicht unterstützt; Nulldurchgänge werden nicht detektiert.
