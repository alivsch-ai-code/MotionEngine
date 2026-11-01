# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.matlab` · Quellcode: [vdsim/matlab/](../../../vdsim/matlab) · Paketdoku: [vdsim/matlab/docs/](../../../vdsim/matlab/docs)

## Übersicht

**Importiert MATLAB-Regler- und Simulationscode, führt die originale Logik ohne MATLAB aus, analysiert die Regelstruktur und übersetzt nach Python, C++17 und Rust.**

Bestehende Regler liegen oft als MATLAB-Skripte vor, z. B. der Lyapunov-Trackingregler aus
Werling 2011, Anh. A.5. Das Modul macht diese Logik in der Plattform nutzbar. Sie lässt sich
als Komponente im Graphen verwenden, als Datenfluss und LaTeX darstellen und in Zielsprachen
für Echtzeit- und Steuergeräte übertragen. Die Übereinstimmung mit dem Original wird
rückverfolgbar verifiziert.

Paket-Docstring:

```text
MATLAB integration: import, interpret, analyze and convert MATLAB code.

    parse / parse_file           lexer + recursive-descent parser -> AST (vdsim.matlab.nodes)
    Interpreter                  executes the AST (numpy semantics, 1-based, built-in registry)
    analyze                      signatures, data flow, call graph, equations, control structure, JSON/DOT
    generate / convert_file      code generators Python (numpy), C++17, Rust with diagnostics
    load_matlab_component        MATLAB function -> Component ("matlab:datei.m[:funktion]" loader)
    toolchains / verify          compiler detection and back-to-back verification

CLI: ``python -m vdsim.matlab convert|analyze|run|toolchains``.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 22 |
| Komponenten | 0 |
| Verfahren/Konzepte | 8 |
| @trace-Einträge | 7 |
| Tests | 5 |
| Beispiele | 1 |

## Architektur

`lexer` → `parser` (rekursiver Abstieg) → AST (`nodes`) bildet die Kette vom Quelltext zum Syntaxbaum.
Auf dem AST arbeiten mehrere Bausteine:
- `interpreter` mit `builtins` und `pyruntime`, der MATLAB-Semantik auf numpy
- `typeinfer`: Skalar/Bool/Matrix mit Größen
- `analysis`: Datenfluss, Aufrufgraph, Gleichungen, Regelstruktur, JSON/DOT, mit `latex` als Formelausgabe
- `codegen` (`python`, `cpp`, `rust` über die gemeinsame Basis `native`) mit Diagnoseliste
- `component`: Loader `matlab:` und Komponente
- `convert` und die CLI (`__main__`)
- `toolchains` und `verify` für Compiler-Erkennung und Back-to-Back-Test

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.matlab`](../../../vdsim/matlab/__init__.py) | 31 | – | MATLAB integration: import, interpret, analyze and convert MATLAB code. |
| [`vdsim.matlab.__main__`](../../../vdsim/matlab/__main__.py) | 89 | – | CLI of the MATLAB integration. |
| [`vdsim.matlab.analysis`](../../../vdsim/matlab/analysis.py) | 660 | VariableInfo, FunctionAnalysis, FileAnalysis, _Analyzer | Static analysis of MATLAB control code ("Regellogik darstellen und analysieren"). |
| [`vdsim.matlab.builtins`](../../../vdsim/matlab/builtins.py) | 860 | BuiltinSpec, MStruct, MCell, MFunction | Built-in function registry of the interpreter. |
| [`vdsim.matlab.codegen`](../../../vdsim/matlab/codegen/__init__.py) | 32 | – | Code generators MATLAB -> Python / C++17 / Rust. |
| [`vdsim.matlab.codegen.base`](../../../vdsim/matlab/codegen/base.py) | 276 | GeneratedCode, Unsupported, BaseGenerator | Common machinery of the code generators (Python, C++17, Rust). |
| [`vdsim.matlab.codegen.cpp`](../../../vdsim/matlab/codegen/cpp.py) | 545 | CppGenerator | MATLAB -> C++17 code generator (header + implementation + small runtime header). |
| [`vdsim.matlab.codegen.native`](../../../vdsim/matlab/codegen/native.py) | 665 | NativeGenerator | Shared translation logic of the statically typed targets (C++17, Rust). |
| [`vdsim.matlab.codegen.python`](../../../vdsim/matlab/codegen/python.py) | 833 | PythonGenerator | MATLAB -> Python (numpy) code generator. |
| [`vdsim.matlab.codegen.rust`](../../../vdsim/matlab/codegen/rust.py) | 574 | RustGenerator | MATLAB -> Rust code generator (f64, std only, one self-contained module file). |
| [`vdsim.matlab.component`](../../../vdsim/matlab/component.py) | 182 | MatlabComponent | MATLAB functions as platform components (``matlab:datei.m`` spec strings). |
| [`vdsim.matlab.convert`](../../../vdsim/matlab/convert.py) | 26 | – | File conversion MATLAB -> Python / C++ / Rust (used by the CLI). |
| [`vdsim.matlab.errors`](../../../vdsim/matlab/errors.py) | 51 | MatlabError, MatlabSyntaxError, MatlabRuntimeError, UnsupportedConstruct, Diagnostic | Error and diagnostic types of the MATLAB toolchain (messages for users are German). |
| [`vdsim.matlab.interpreter`](../../../vdsim/matlab/interpreter.py) | 950 | _Break, _Continue, _Return, Frame, Interpreter | Tree-walking interpreter for the MATLAB AST (numpy semantics, 1-based indexing). |
| [`vdsim.matlab.latex`](../../../vdsim/matlab/latex.py) | 302 | _VarsHint | Pretty printers for AST expressions: MATLAB text and LaTeX (matplotlib mathtext subset). |
| [`vdsim.matlab.lexer`](../../../vdsim/matlab/lexer.py) | 324 | Token, Comment, Lexer | Lexer for the MATLAB subset used in controller and simulation code. |
| [`vdsim.matlab.nodes`](../../../vdsim/matlab/nodes.py) | 302 | Node, Expr, Number, String, Ident, Colon | AST node classes of the MATLAB subset. |
| [`vdsim.matlab.parser`](../../../vdsim/matlab/parser.py) | 620 | Parser | Recursive-descent parser: MATLAB tokens -> AST (``nodes``). |
| [`vdsim.matlab.pyruntime`](../../../vdsim/matlab/pyruntime.py) | 390 | _MColon | MATLAB semantics helpers on top of numpy (std + numpy only). |
| [`vdsim.matlab.toolchains`](../../../vdsim/matlab/toolchains.py) | 247 | ToolchainError, Toolchain | Detection and invocation of native toolchains (rustc/cargo, MSVC cl.exe, g++/clang++). |
| [`vdsim.matlab.typeinfer`](../../../vdsim/matlab/typeinfer.py) | 525 | MType, FunctionTypes, TypeInference | Type and shape inference for the code generators. |
| [`vdsim.matlab.verify`](../../../vdsim/matlab/verify.py) | 213 | – | Back-to-back verification of the converters against the interpreter. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md)
- genutzt von: [api](../api/index.md)
- externe Bibliotheken: `__future__`, `argparse`, `bisect`, `cmath`, `dataclasses`, `functools`, `inspect`, `json`, `keyword`, `math`, `numpy`, `os`, `pathlib`, `re`, `scipy`, `shutil`, `subprocess`, `sys`, `tempfile`, `types`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Gemeinsame Laufzeitfunktionen (pyruntime) für Interpreter und generierten Python-Code | Gleiche Implementierung von Indizierung, Colon-Operator, mod, round und sprintf liefert bitgleiche Ergebnisse | getrennte Implementierungen (Abweichungen in Randfällen) |
| Skalare im Interpreter als Python-float über math-Funktionen | identische Rechenwege wie der generierte Code, schneller als 1x1-Arrays | alles als numpy-Array (langsamer, Rundungsunterschiede durch SIMD-Pfade) |
| Nicht übersetzbare Konstrukte erzeugen Diagnosen (Fehler mit Zeile und Spalte) | keine stille Fehlübersetzung; Dateien werden bei Fehlern nicht geschrieben (außer --force) | Best-Effort-Übersetzung |
| Persistente Variablen als expliziter Zustand (SimpleNamespace / Struct mit optional / Option) | Rücksetzbar (reset), Hot Reload, mehrere Instanzen möglich | statische Variablen (nicht rücksetzbar) |
| Kleine generierte Matrixklasse Mat (spaltenweise, 1-basierte Zugriffe) statt Eigen/nalgebra | nur Standardbibliothek, keine Abhängigkeiten | Eigen (C++), nalgebra (Rust) |

## Implementierung

- Kontextabhängiger Lexer, der ' als Transpose oder String erkennt, im Matrixliteral Kommas einfügt und `end` im Index markiert
- Funktionsdateien mit oder ohne end; der Stil wird über die Zählung von Blocköffnern und end bestimmt
- Kommentare werden Anweisungen zugeordnet; eine reine Gleichungsnummer in eigener Zeile gehört zur Anweisung darüber
- **Typinferenz flussunabhängig mit Fixpunkt und interprozedural pro Argumentsignatur; Hinweise per input_types oder Kommentar `%#type x:** vector(3)`
- Built-in-Registry (`register_builtin`) für eigene Funktionen

### Verfahren und Konzepte

- [Matlab analysis](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Matlab codegen](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Matlab codegen verification](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Matlab control structure](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Matlab import](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Matlab interpreter](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Matlab parser](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Matlab type inference](../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Erweiterungspunkte

- Eigene Built-ins über vdsim.matlab.register_builtin(name, func, multi=, ctx=)
- Weitere Zielsprachen als Unterklasse von codegen.base.BaseGenerator (statisch typisiert über codegen.native.NativeGenerator)
- Typregeln für eigene Built-ins in typeinfer.builtin_type

## Verwandte Module

[framework](../framework/index.md), [stabilization](../stabilization/index.md)

## Hauptquellen

[Aho et al. (2006)](../references.md#aho2006), [IEEE (2019)](../references.md#ieee754_2019), [JTC1/SC22/WG21 (2017)](../references.md#iso_cpp17), [MathWorks und Inc. (2024)](../references.md#mathworks_matlab), [MathWorks und Inc. (2024)](../references.md#mathworks_precedence), [Developers (2024)](../references.md#rust_reference), [Werling (2011)](../references.md#werling2011)
