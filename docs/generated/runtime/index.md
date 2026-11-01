# Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.runtime` · Quellcode: [vdsim/runtime/](../../../vdsim/runtime) · Paketdoku: [vdsim/runtime/docs/](../../../vdsim/runtime/docs)

## Übersicht

**Führt Komponentengraphen der offenen Fahrzeugarchitektur deterministisch und mehrratig aus und bindet Custom Nodes in Python, Rust und C++ mit Hot Reload ein.**

Die Plattform setzt automatisierte Fahrfunktionen aus austauschbaren Komponenten zusammen
(Perception bis Fahrzeugstrecke). Das Paket runtime liefert das Graphmodell, das der
Architektur-Editor bearbeitet, die Validierung mit verständlichen Meldungen, den Executor
mit Simulink-ähnlicher Semantik (Zweiphasen-Ausführung, Rückführungs-Ports, Multi-Rate mit
Halteglied), Werkzeuge für Echtzeit-Debugging und Laufzeitmessung, einen Versionsspeicher
für Graphen sowie die Anbindung eigener Algorithmen als Custom Nodes mit denselben
Schnittstellen wie native Komponenten.

Paket-Docstring:

```text
Runtime of the component platform: graph model, executor, debugging, versioning, custom nodes.

    graph        Graph / Node / Connection, validation (German messages), execution order, JSON
    executor     deterministic multi-rate executor (two-phase, feedback ports, ZOH), real-time mode
    debug        breakpoints, probes, profiler
    recorder     time series of ports / component signals, events
    blocks       Simulink-like basic blocks (KIND "node")
    versioning   snapshot store (.history), diff, restore, optional git commit
    python_nodes "python:file.py:Class" loader with hot reload
    native       C ABI nodes ("rust:crate", "cpp:dir") via ctypes, shadow-copy hot reload
    build        cargo / MSVC / g++ build orchestration
    codegen      vdsim_node.h / vdsim_node.rs generated from framework.types
    scaffold     create_custom_node(): project templates for python / rust / cpp
    hot_reload   HotReloader (mtime polling, state transfer via get_state/set_state)

Importing this package registers the blocks and the loaders "python", "rust" and "cpp".
```

| Kennzahl | Anzahl |
|---|---|
| Module | 14 |
| Komponenten | 19 |
| Verfahren/Konzepte | 8 |
| @trace-Einträge | 2 |
| Tests | 5 |
| Beispiele | 5 |

## Architektur

- `graph.py`: `Graph` mit `Node`/`Connection`, JSON nach contracts.md (Abschn. 4), Validierung
  (`ValidationReport`), Abhängigkeitsgraph, topologische Sortierung (Kahn, deterministisch),
  algebraische Schleifen (Tarjan), Änderungs-Listener für den Editor.
- `executor.py`: `Executor` mit ganzzahligem Zeitraster, Aktionsliste output → step → update,
  Rückführungs-Latch, Breakpoints/Single-Step über einen Programmzähler innerhalb des Schritts,
  `advance(wall_dt)` für den Echtzeitmodus.
- `debug.py` (Breakpoint, Probe, Profiler), `recorder.py` (Zeitreihen, Ereignisse).
- `blocks.py`: Grundblöcke (Quellen, Mathematik, Diskret, Senken, Signalführung).
- `versioning.py`: `VersionStore` (.history, Inhalts-Hash, Diff, Restore, Git).
- `python_nodes.py`, `native.py`, `build.py`, `codegen.py`, `codecs.py`, `scaffold.py`,
  `hot_reload.py`: Custom Nodes (Loader, C-ABI über ctypes, Build, Header-Generator,
  Projektvorlagen, Hot Reload).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.runtime`](../../../vdsim/runtime/__init__.py) | 55 | – | Runtime of the component platform: graph model, executor, debugging, versioning, custom nodes. |
| [`vdsim.runtime.blocks`](../../../vdsim/runtime/blocks.py) | 492 | Block, ConstantParams, Constant, StepParams, Step, SineParams | Basic signal blocks (Simulink-like) as regular components (KIND "node"). |
| [`vdsim.runtime.build`](../../../vdsim/runtime/build.py) | 488 | NativeBuildError, BuildResult, CppCompiler, BuildJob | Build orchestration for native custom nodes (Rust via cargo, C++ via MSVC / g++ / clang++). |
| [`vdsim.runtime.codecs`](../../../vdsim/runtime/codecs.py) | 104 | – | Flat float64 codecs used by native nodes. |
| [`vdsim.runtime.codegen`](../../../vdsim/runtime/codegen.py) | 1257 | – | Code generator for the native node headers: vdsim_node.h (C++17) and vdsim_node.rs (Rust, std only). |
| [`vdsim.runtime.debug`](../../../vdsim/runtime/debug.py) | 182 | Breakpoint, BreakHit, NodeStep, Probe, NodeProfile, Profiler | Debugging aids of the executor: breakpoints, probes and the per-node runtime profiler. |
| [`vdsim.runtime.executor`](../../../vdsim/runtime/executor.py) | 553 | ExecutionError, RuntimeTypeError, RunResult, _RT, Executor | Deterministic multi-rate executor for component graphs. |
| [`vdsim.runtime.graph`](../../../vdsim/runtime/graph.py) | 888 | GraphError, GraphValidationError, ValidationIssue, ValidationReport, Node, Connection | Graph model of the open vehicle architecture. |
| [`vdsim.runtime.hot_reload`](../../../vdsim/runtime/hot_reload.py) | 160 | ReloadEvent, HotReloader | Hot reloading of custom nodes (Python and native). |
| [`vdsim.runtime.native`](../../../vdsim/runtime/native.py) | 513 | NativeNodeError, NativeLibrary, NativeComponent, NativeSource | Native custom nodes (C ABI) for Rust and C++, loaded with ctypes. |
| [`vdsim.runtime.python_nodes`](../../../vdsim/runtime/python_nodes.py) | 158 | PythonSource | Custom nodes in Python: spec "python:path/to/file.py:ClassName" (class name optional if unique). |
| [`vdsim.runtime.recorder`](../../../vdsim/runtime/recorder.py) | 188 | Event, Recorder | Recorder: time series of selected ports and component signals, plus events. |
| [`vdsim.runtime.scaffold`](../../../vdsim/runtime/scaffold.py) | 285 | ScaffoldResult | Project templates for custom nodes: create_custom_node(language, name, kind, dest). |
| [`vdsim.runtime.versioning`](../../../vdsim/runtime/versioning.py) | 300 | Version, GraphDiff, ConfigDiff, VersionStore | Version store for graphs and component configurations. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md)
- genutzt von: [ad](../ad/index.md), [api](../api/index.md)
- externe Bibliotheken: `__future__`, `_ctypes`, `collections`, `copy`, `ctypes`, `dataclasses`, `datetime`, `hashlib`, `heapq`, `importlib`, `inspect`, `itertools`, `json`, `math`, `numpy`, `os`, `pathlib`, `re`, `shutil`, `subprocess`, `sys`, `tempfile`, `threading`, `time`, `weakref`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Ganzzahlige Ticks, t_k = round(k·Δt, 12) | keine Akkumulation von Rundungsfehlern; Abtastzeitpunkte exakt reproduzierbar | t += Δt (Drift, Multi-Rate-Zeitpunkte verschieben sich) |
| Zweiphasen-Ausführung für Blöcke ohne Durchgriff, Rückführungs-Ports mit Wert des Vorschritts | bricht Regelkreise wie in Simulink auf, ohne algebraische Gleichungen lösen zu müssen | iterativer Löser für algebraische Schleifen (nicht deterministisch in der Laufzeit) |
| Aktionsliste mit Programmzähler statt rekursiver Ausführung | Breakpoints und Einzelschritte mitten im Basisschritt, Fortsetzen ohne Zustandsverlust | – |
| Natives Interface als schlanke C-ABI mit flachen float64-Puffern | sprachneutral (Rust, C++, C), ohne Abhängigkeiten, Layouts aus framework.types generiert | pybind11/PyO3 (Python-ABI-abhängig, Build-Abhängigkeiten) |
| Schattenkopie der DLL mit Versionszähler | Windows sperrt geladene Bibliotheken; so kann neu gebaut werden, während der Node läuft | – |
| Vollständige Schnappschüsse mit Inhalts-Hash statt Deltas | einfache, robuste Wiederherstellung; Graphen sind klein | – |

## Implementierung

- Pro Knoten vorkompilierte Eingangsliste (Quelle, Rückführung) und Ausgangsschlüssel "knoten.port"
- Profiler mit perf_counter_ns, p95 über einen Ringpuffer (20 000 Werte je Knoten)
- Python-Custom-Nodes werden ohne Bytecode-Cache unter eindeutigem Modulnamen ausgeführt
- Native Eingänge großer Typen (Trajektorie, Objektlisten) werden bei identischem Objekt nicht neu kodiert
- MSVC-Umgebung (vcvars64) wird einmalig ermittelt und zwischengespeichert; fehlt das Windows SDK, werden Import-Bibliotheken für Rust aus den System-DLLs erzeugt

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`node/clock`](components/node__clock.md) | Uhr | 1.0.0 | Gibt die Simulationszeit aus. |
| [`node/constant`](components/node__constant.md) | Konstante | 1.0.0 | Konstanter Wert y = c. |
| [`node/demux`](components/node__demux.md) | Demux | 1.0.0 | Zerlegt einen Vektor in n Skalare (fehlende Elemente: NaN). |
| [`node/gain`](components/node__gain.md) | Verstärkung | 1.0.0 | y = k · u (Skalar oder Vektor). |
| [`node/integrator`](components/node__integrator.md) | Integrator | 1.0.0 | Zeitdiskreter Integrator (explizites Euler-Verfahren) mit Begrenzung. |
| [`node/lowpass`](components/node__lowpass.md) | Tiefpass (PT1) | 1.0.0 | PT1-Glied, exakt diskretisiert (Sprunginvarianz). |
| [`node/mux`](components/node__mux.md) | Mux | 1.0.0 | Fasst n Skalare zu einem Vektor zusammen. |
| [`node/probe`](components/node__probe.md) | Messpunkt | 1.0.0 | Durchschleifender Messpunkt: y = u, Skalare erscheinen als Signal 'value'. |
| [`node/product`](components/node__product.md) | Produkt | 1.0.0 | Produkt bzw. |
| [`node/ramp`](components/node__ramp.md) | Rampe | 1.0.0 | Rampe: y = y0 + m (t - t_start) ab t_start. |
| [`node/rate_limiter`](components/node__rate_limiter.md) | Ratenbegrenzer | 1.0.0 | Begrenzt die Änderungsrate des Signals. |
| [`node/saturation`](components/node__saturation.md) | Begrenzung | 1.0.0 | Begrenzt u auf [lower, upper]. |
| [`node/scope`](components/node__scope.md) | Scope | 1.0.0 | Zeichnet seine Eingänge als Zeitreihen auf (data()). |
| [`node/sine`](components/node__sine.md) | Sinus | 1.0.0 | y = A sin(2π f t + φ) + Offset. |
| [`node/step`](components/node__step.md) | Sprung | 1.0.0 | Sprungfunktion: Anfangswert für t < t_step, sonst Endwert. |
| [`node/sum`](components/node__sum.md) | Summe | 1.0.0 | Summe der Eingänge mit Vorzeichen aus dem Parameter 'signs'. |
| [`node/switch`](components/node__switch.md) | Schalter | 1.0.0 | y = u1, falls control ≥ Schwelle, sonst u2. |
| [`node/typed_default`](components/node__typed_default.md) | Standardwert | 1.0.0 | Liefert den Standardwert eines Datentyps (z. |
| [`node/unit_delay`](components/node__unit_delay.md) | Verzögerung (z⁻¹) | 1.0.0 | Verzögert das Eingangssignal um einen Abtastschritt: y_k = u_{k-1}. |

### Verfahren und Konzepte

- [Algebraische Schleifen](theory.md#algebraic_loop)
- [C-ABI der nativen Custom Nodes](theory.md#c_abi)
- [Versionierungsmodell](theory.md#content_addressed_versioning)
- [Determinismus](theory.md#deterministic_execution)
- [Diskrete Grundblöcke](theory.md#discrete_blocks)
- [Hot Reload](theory.md#hot_reload)
- [Multi-Rate und Halteglied](theory.md#multirate_zoh)
- [Ausführungsmodell und Zeitdiskretisierung](theory.md#synchronous_dataflow)

## Erweiterungspunkte

- Neue Grundblöcke über @component(kind="node")
- Weitere Loader-Präfixe über vdsim.framework.plugins.register_loader
- Neue Datentypen für native Nodes über runtime.codecs und codegen
- Listener (vor/nach Knoten, nach Schritt) für Live-Anzeigen

## Verwandte Module

[framework](../framework/index.md), [ad](../ad/index.md), [gui](../gui/index.md)

## Hauptquellen

[Project (2024)](../references.md#cargo_book), [Edwards und Lee (2003)](../references.md#edwards_lee2003), [Lee und Seshia (2017)](../references.md#lee_seshia2017), [Microsoft (2024)](../references.md#msvc_dll), [Foundation (2024)](../references.md#python_ctypes), [Project (2024)](../references.md#rust_ffi), [MathWorks (2024)](../references.md#simulink_exec)
