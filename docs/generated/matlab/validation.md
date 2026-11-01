# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/matlab/test_matlab_codegen.py](../../../tests/matlab/test_matlab_codegen.py) | Generiertes Python ist auf A.5 und allen Fixtures bitgleich zum Interpreter; Rust wird typgeprüft; Rust und C++ werden numerisch verglichen, wenn die Toolchain linken kann |
| [tests/matlab/test_matlab_component.py](../../../tests/matlab/test_matlab_component.py) | A.5 stimmt mit der Python-Referenz vdsim.stabilization.werling_kinematic überein; Komponente, Loader und CLI |
| [tests/matlab/test_matlab_analysis.py](../../../tests/matlab/test_matlab_analysis.py) | Gleichungen, Abhängigkeiten, Rückführung und Vorsteuerung von A.5, PID-Erkennung |

## Tests, die dieses Paket verwenden

### [tests/matlab/test_matlab_analysis.py](../../../tests/matlab/test_matlab_analysis.py)

**Zeigt:** Gleichungen, Abhängigkeiten, Rückführung und Vorsteuerung von A.5, PID-Erkennung

Importiert: `vdsim.matlab`, `vdsim.matlab.analysis`

| Testfunktion | Beschreibung |
|---|---|
| `test_a5_analysis` | – |
| `test_pid_and_pure_feedback_structures` | – |
| `test_unused_and_complexity` | – |

### [tests/matlab/test_matlab_codegen.py](../../../tests/matlab/test_matlab_codegen.py)

**Zeigt:** Generiertes Python ist auf A.5 und allen Fixtures bitgleich zum Interpreter; Rust wird typgeprüft; Rust und C++ werden numerisch verglichen, wenn die Toolchain linken kann

Importiert: `vdsim.matlab`, `vdsim.matlab.codegen`, `vdsim.matlab.parser`, `vdsim.matlab.toolchains`, `vdsim.matlab.verify`

| Testfunktion | Beschreibung |
|---|---|
| `test_python_bitwise_equal_to_interpreter` | – |
| `test_python_strings_cells` | – |
| `test_unsupported_constructs_reported` | – |
| `test_unsupported_slice_has_line` | – |
| `test_comments_and_equations_transferred` | – |
| `test_rust_typechecks` | – |
| `test_native_numerically_equal` | – |

### [tests/matlab/test_matlab_component.py](../../../tests/matlab/test_matlab_component.py)

**Zeigt:** A.5 stimmt mit der Python-Referenz vdsim.stabilization.werling_kinematic überein; Komponente, Loader und CLI

Importiert: `vdsim.matlab`, `vdsim.matlab.component`, `vdsim.matlab.convert`, `vdsim.matlab.interpreter`

| Testfunktion | Beschreibung |
|---|---|
| `test_a5_component` | – |
| `test_loader_spec_vector_ports_and_state` | – |
| `test_unconnected_input_and_bad_params` | – |
| `test_convert_file_and_cli` | – |
| `test_reference_implementation` | – |

### [tests/matlab/test_matlab_interpreter.py](../../../tests/matlab/test_matlab_interpreter.py)

Importiert: `vdsim.matlab`, `vdsim.matlab.builtins`, `vdsim.matlab.errors`, `vdsim.matlab.interpreter`

| Testfunktion | Beschreibung |
|---|---|
| `test_indexing_growth_and_end` | – |
| `test_copy_semantics_and_column_vectors` | – |
| `test_builtins` | – |
| `test_fixtures` | – |
| `test_pid_persistent_and_reset` | – |
| `test_script_and_registry` | – |
| `test_runtime_error_position` | – |

### [tests/matlab/test_matlab_parser.py](../../../tests/matlab/test_matlab_parser.py)

Importiert: `vdsim.matlab.errors`, `vdsim.matlab.lexer`, `vdsim.matlab.nodes`, `vdsim.matlab.parser`

| Testfunktion | Beschreibung |
|---|---|
| `test_transpose_vs_string_and_matrix_whitespace` | – |
| `test_comments_block_and_continuation` | – |
| `test_precedence_and_ranges` | – |
| `test_statements_and_multi_assign` | – |
| `test_end_terminated_and_nested_functions` | – |
| `test_script_with_local_function` | – |
| `test_a5_structure` | – |
| `test_errors_with_position` | – |
