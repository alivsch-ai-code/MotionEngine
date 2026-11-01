# Forschungsmodus

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.research` · Quellcode: [vdsim/research/](../../../vdsim/research) · Paketdoku: [vdsim/research/docs/](../../../vdsim/research/docs)

## Übersicht

**Kennwerte, Sicherheitsmetriken, Batch-Simulation, Parameter-Sweeps, Monte Carlo, Controller- und Planer-Vergleiche sowie Laufzeit-Benchmarking.**

Algorithmen für automatisiertes Fahren lassen sich nur über viele reproduzierbare Simulationen bewerten.
Das Modul macht aus einzelnen Läufen (ADResult) vergleichbare Kennwerte und orchestriert Versuchsreihen.
Jeder Job ist ein einfaches dict; deshalb läuft dieselbe Versuchsreihe aus GUI, API und Kommandozeile.

Paket-Docstring:

```text
Research mode: KPIs, safety metrics, batch runs, parameter sweeps, Monte Carlo, comparisons, benchmarking.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 4 |
| Komponenten | 0 |
| Verfahren/Konzepte | 5 |
| @trace-Einträge | 5 |
| Tests | 1 |
| Beispiele | 1 |

## Architektur

- `metrics.py`: ADResult → Kennwerte (Sicherheit, Komfort, Tracking, Planer, Kosten, Mission)
- `experiments.py`: Jobs, Batch (Prozesspool), vollfaktorielle Sweeps, Monte Carlo, Vergleiche, BatchResult mit Statistik und Sensitivität
- `benchmark.py`: Laufzeit je Knoten des Ausführungsgraphen, Planungszyklus, Echtzeitfaktor

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.research`](../../../vdsim/research/__init__.py) | 11 | – | Research mode: KPIs, safety metrics, batch runs, parameter sweeps, Monte Carlo, comparisons, benchmarking. |
| [`vdsim.research.benchmark`](../../../vdsim/research/benchmark.py) | 56 | – | Runtime benchmarking of the automated-driving stack (per node, planner cycles, real-time factor). |
| [`vdsim.research.experiments`](../../../vdsim/research/experiments.py) | 265 | BatchResult | Research mode: batch simulation, parameter sweeps, Monte Carlo, controller/planner comparison. |
| [`vdsim.research.metrics`](../../../vdsim/research/metrics.py) | 347 | – | Research metrics of an automated-driving run (ADResult -> KPI dict). |

### Abhängigkeiten

- nutzt: [ad](../ad/index.md), [framework](../framework/index.md)
- genutzt von: [ad](../ad/index.md), [api](../api/index.md), [gui](../gui/index.md)
- externe Bibliotheken: `__future__`, `concurrent`, `copy`, `itertools`, `json`, `numpy`, `pathlib`, `re`, `time`, `traceback`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Jobs als JSON-fähige dicts mit Pfad-Overrides ("stack.planner.params.cost.k_jerk") | dieselbe Definition für GUI, REST-API, CLI und Prozesspool (picklebar), versionierbar | Python-Objekte mit Callbacks (nicht serialisierbar) |
| Seeds sind Teil des Jobs, Monte-Carlo-Seeds werden deterministisch aus Basis-Seed und Laufindex abgeleitet | Ergebnisse sind unabhängig von der Anzahl der Worker reproduzierbar | globaler Zufallsgenerator (Reihenfolgeabhängig) |
| Konsistenzmaß als Kennwert | zeitliche Konsistenz ist die zentrale Eigenschaft der Werling-Planung (Bellman-Prinzip) und muss im Planervergleich sichtbar sein | nur Endergebnisse vergleichen (Konsistenzverlust bliebe unbemerkt) |

## Implementierung

- Sicherheitsmetriken werden auf der Ego-Zeitbasis mit den interpolierten Objekthistorien berechnet; Abstände über orientierte Rechtecke (SAT + Kantenabstände).
- Monte-Carlo-Statistik mit Perzentilen und Kollisionsrate; Sensitivität als standardisierte Regressionskoeffizienten.

### Verfahren und Konzepte

- [Zeitliche Konsistenz (Bellman-Prinzip)](../planning/theory.md#bellman_principle)
- [Vollfaktorieller Versuchsplan](theory.md#full_factorial_design)
- [Monte-Carlo-Simulation und Sensitivität](theory.md#monte_carlo)
- [Abstand orientierter Rechtecke](theory.md#rectangle_distance)
- [Surrogate Safety Measures](theory.md#surrogate_safety_measures)

## Erweiterungspunkte

- Neue Kennwerte als Funktion ADResult → dict in metrics.evaluate ergänzen
- Neue Versuchspläne (z. B. Latin Hypercube) als Job-Generator neben parameter_sweep/monte_carlo

## Verwandte Module

[ad](../ad/index.md), [planning](../planning/index.md), [stabilization](../stabilization/index.md), [world](../world/index.md), [api](../api/index.md)

## Hauptquellen

[Allen et al. (1978)](../references.md#allen1978), [Ericson (2004)](../references.md#ericson2004), [Hayward (1972)](../references.md#hayward1972), [Montgomery (2017)](../references.md#montgomery2017), [Saltelli et al. (2008)](../references.md#saltelli2008), [Vogel (2003)](../references.md#vogel2003), [Werling (2011)](../references.md#werling2011)
