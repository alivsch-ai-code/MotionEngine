# Komponenten-Framework der AD-Plattform

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.framework` · Quellcode: [vdsim/framework/](../../../vdsim/framework) · Paketdoku: [vdsim/framework/docs/](../../../vdsim/framework/docs)

## Übersicht

**Komponentenmodell mit typisierten Ports, versionierte Plugin-Registry, Dependency Injection, Laufzeitkontext, Signaltypen mit Codecs und Rückverfolgbarkeits-Metadaten.**

Die Plattform für automatisierte Fahrfunktionen besteht aus austauschbaren Komponenten derselben
Wirkkettenebene (Perception … Vehicle Plant). Das Framework legt dafür den gemeinsamen Vertrag fest
(docs/specs/contracts.md): Ports und Typen, Parameter mit Einheiten, Versionen, Lebenszyklus und
Dokumentationsmetadaten. Es hängt weder von der GUI noch von konkreten Algorithmen ab (Clean Architecture).

Paket-Docstring:

```text
Component framework of the automated-driving platform (Clean Architecture core).

    types       signal data types exchanged between components (+ flat codecs for native nodes)
    component   Component base class: typed ports, parameters, version, documentation metadata
    layers      abstract layer contracts (Perception ... VehiclePlant)
    plugins     versioned plugin registry and component factory ("kind/name@version", "python:...", ...)
    container   dependency injection container
    context     RunContext handed to components (time step, seeds, vehicle, road, logger)
    knowledge   traceability decorators and documentation metadata (ComponentDoc)

Nothing in this package depends on the GUI, the runtime or concrete algorithms.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 9 |
| Komponenten | 0 |
| Verfahren/Konzepte | 6 |
| @trace-Einträge | 11 |
| Tests | 19 |
| Beispiele | 12 |

## Architektur

- `component.py`: `Component` (KIND, NAME, VERSION, INPUTS, OUTPUTS, PARAMS, PERIOD, DOC; reset, step,
  output/update, get_state/set_state, describe), `Port`, Parameterhilfen (`params_schema`, `set_param`).
- `layers.py`: Basisklassen der Ebenen mit festen Ports, `LAYER_ORDER`.
- `plugins.py`: `@component`, `get_component`, `create_component`, `available_components`, Spec-Strings
  `kind/name@constraint`, Loader für `python:`, `cpp:`, `rust:`, `matlab:`; `BUILTIN_MODULES`.
- `container.py`: Dependency-Injection-Container mit Singletons und Scopes.
- `context.py`: `RunContext` (dt, seed, vehicle, road, scenario, rng(name), service()).
- `types.py`: Signaltypen (`EgoState`, `PlannedTrajectory`, …), `TYPES`, `compatible()`, `encode/decode`.
- `knowledge.py`: `ComponentDoc`, `@trace`, `TRACES` – Grundlage des Wissenssystems (vdsim.knowledge).
- `provenance.py`: Reproduzierbarkeits-Manifest (Versionen, Konfigurations-Hash, Git-Commit).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.framework`](../../../vdsim/framework/__init__.py) | 21 | – | Component framework of the automated-driving platform (Clean Architecture core). |
| [`vdsim.framework.component`](../../../vdsim/framework/component.py) | 201 | Port, NoParams, Component | Component base class. |
| [`vdsim.framework.container`](../../../vdsim/framework/container.py) | 64 | Container | Minimal dependency injection container. |
| [`vdsim.framework.context`](../../../vdsim/framework/context.py) | 50 | RunContext | RunContext: everything a component may need from its environment (dependency injection target). |
| [`vdsim.framework.knowledge`](../../../vdsim/framework/knowledge.py) | 73 | ComponentDoc | Traceability and documentation metadata. |
| [`vdsim.framework.layers`](../../../vdsim/framework/layers.py) | 81 | ScenarioWorldBase, PerceptionBase, PredictionBase, BehaviorPlannerBase, TrajectoryPlannerBase, TrackingControllerBase | Layer contracts of the automated-driving architecture. |
| [`vdsim.framework.plugins`](../../../vdsim/framework/plugins.py) | 164 | – | Versioned plugin registry and component factory. |
| [`vdsim.framework.provenance`](../../../vdsim/framework/provenance.py) | 44 | – | Reproducibility manifest stored with every result (versions, configuration hash, seeds). |
| [`vdsim.framework.types`](../../../vdsim/framework/types.py) | 568 | EgoState, ObjectState, ObjectList, PredictedObject, Prediction, LongitudinalMode | Signal data types exchanged between components. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [geometry](../geometry/index.md), [simulation](../simulation/index.md)
- genutzt von: [ad](../ad/index.md), [api](../api/index.md), [behavior](../behavior/index.md), [geometry](../geometry/index.md), [gui](../gui/index.md), [knowledge](../knowledge/index.md), [matlab](../matlab/index.md), [perception](../perception/index.md), [planning](../planning/index.md), [prediction](../prediction/index.md), [research](../research/index.md), [runtime](../runtime/index.md), [stabilization](../stabilization/index.md), [tire_models](../tire_models/index.md), [vehicle_models](../vehicle_models/index.md), [world](../world/index.md)
- externe Bibliotheken: `__future__`, `collections`, `copy`, `dataclasses`, `datetime`, `functools`, `hashlib`, `importlib`, `json`, `numpy`, `pathlib`, `platform`, `scipy`, `subprocess`, `sys`, `typing`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Ports und Typen als Klassenattribute statt Laufzeitregistrierung | Editor, Typprüfung und Dokumentation lesen sie ohne Instanz (describe()) | Ports erst im Konstruktor (nicht statisch auswertbar) |
| Mehrere Versionen einer Komponente parallel, SemVer-Bereiche in Spec-Strings | Ergebnisse speichern die exakte Version; ältere Graphen bleiben lauffähig | nur eine Version je Name |
| Zufall ausschließlich über context.rng(name) mit SHA-256-Seed | bitgenau reproduzierbar, unabhängig von PYTHONHASHSEED und Aufrufreihenfolge | – |
| Komponenten ohne Durchgriff (output/update) und Rückführungs-Ports | bricht algebraische Schleifen wie in Simulink; Bi-level-Rückführung Regler → Planer (Werling 2.3) | – |

## Implementierung

- describe() liefert ein JSON-fähiges Dict inklusive Parameter-Schema und ComponentDoc; das Wissenssystem liest genau dieses.
- load_builtins() importiert BUILTIN_MODULES einmal; fehlende optionale Pakete werden übersprungen, defekte protokolliert.
- set_param() unterstützt verschachtelte Parameter per Punktnotation (z. B. cost.k_jerk) und konvertiert Typen.

### Verfahren und Konzepte

- [Komponentenmodell mit typisierten Ports](theory.md#component_model)
- [Dependency Injection und Laufzeitkontext](theory.md#dependency_injection)
- [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding)
- [Versionierte Plugin-Registry](theory.md#plugin_registry)
- [Signaltypen und Codecs](theory.md#signal_type_system)
- [Rückverfolgbarkeitsmodell](../knowledge/theory.md#traceability_model)

## Erweiterungspunkte

- Neue Komponente "@component class X(<Ebene>Base)" mit DOC = ComponentDoc(...) und @trace an Gleichungsfunktionen
- Neuer Signaltyp mit register_type(name, py_type, description, color) und Codec in encode/decode
- Neuer Loader für Custom Nodes mit register_loader(prefix, loader)

## Verwandte Module

[knowledge](../knowledge/index.md), [core](../core/index.md), [geometry](../geometry/index.md)

## Hauptquellen

[Fowler (2004)](../references.md#fowler2004), [Martin (2017)](../references.md#martin2017), [Preston-Werner](../references.md#semver2), [Werling (2011)](../references.md#werling2011)
