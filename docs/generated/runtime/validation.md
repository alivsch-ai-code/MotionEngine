# Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/runtime/test_runtime_graph.py](../../../tests/runtime/test_runtime_graph.py) | Typfehler, unverbundene Eingänge, algebraische Schleifen, Schleife über UnitDelay/Rückführung erlaubt |
| [tests/runtime/test_runtime_executor.py](../../../tests/runtime/test_runtime_executor.py) | exaktes Multi-Rate-Timing, Zweiphasen-Regelkreis gegen geschlossene Lösung, bitgleiche Läufe, Debugging, Profiler |
| [tests/runtime/test_runtime_versioning.py](../../../tests/runtime/test_runtime_versioning.py) | Schnappschuss, Diff, Wiederherstellung, Git-Commit |
| [tests/runtime/test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py) | Python-Hot-Reload mit Zustandsübertragung, Fehlerfall, Portänderung |
| [tests/runtime/test_runtime_native.py](../../../tests/runtime/test_runtime_native.py) | Rust/C++ bauen, laden, Codec-Rundreise aller Typen, bitgleich zum Python-Regler, Hot Reload |

## Tests, die dieses Paket verwenden

### [tests/runtime/test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py)

**Zeigt:** Python-Hot-Reload mit Zustandsübertragung, Fehlerfall, Portänderung

Importiert: `vdsim.runtime`, `vdsim.runtime.executor`, `vdsim.runtime.graph`, `vdsim.runtime.scaffold`

Komponenten: `node/constant`

| Testfunktion | Beschreibung |
|---|---|
| `test_python_loader_and_hot_reload_with_state_transfer` | – |
| `test_hot_reload_error_keeps_old_instance` | – |
| `test_hot_reload_port_change_revalidates` | – |
| `test_python_example_nodes_have_layer_ports` | – |
| `test_example_chain_closed_loop_and_deterministic` | – |
| `test_sensor_fusion_reduces_noise_and_is_reproducible` | – |
| `test_create_custom_node_python_runs` | – |

### [tests/runtime/test_runtime_executor.py](../../../tests/runtime/test_runtime_executor.py)

**Zeigt:** exaktes Multi-Rate-Timing, Zweiphasen-Regelkreis gegen geschlossene Lösung, bitgleiche Läufe, Debugging, Profiler

Importiert: `vdsim.runtime`, `vdsim.runtime.debug`, `vdsim.runtime.executor`, `vdsim.runtime.graph`, `vdsim.runtime.recorder`

Komponenten: `node/clock`, `node/constant`, `node/demux`, `node/gain`, `node/integrator`, `node/lowpass`, `node/mux`, `node/probe`, `node/ramp`, `node/saturation`, `node/scope`, `node/sine`, `node/sum`, `node/switch`

| Testfunktion | Beschreibung |
|---|---|
| `test_two_phase_integrator_loop_exact` | – |
| `test_multirate_timing_exact_and_zoh` | – |
| `test_long_run_has_no_drift` | – |
| `test_feedback_port_reads_previous_step` | – |
| `test_determinism_bit_identical` | – |
| `test_breakpoint_single_step_pause_resume` | – |
| `test_step_and_pause_in_realtime_mode` | – |
| `test_stop_condition_request_stop_and_events` | – |
| `test_listeners_probes_and_profiler` | – |
| `test_runtime_type_check_and_node_errors` | – |
| `test_runtime_graph_changes_and_parameters` | – |
| `test_scope_and_vector_blocks` | – |

### [tests/runtime/test_runtime_graph.py](../../../tests/runtime/test_runtime_graph.py)

**Zeigt:** Typfehler, unverbundene Eingänge, algebraische Schleifen, Schleife über UnitDelay/Rückführung erlaubt

Importiert: `vdsim.runtime`, `vdsim.runtime.graph`

Komponenten: `node/constant`, `node/gain`, `node/product`, `node/saturation`, `node/scope`, `node/sum`, `node/typed_default`, `node/unit_delay`

| Testfunktion | Beschreibung |
|---|---|
| `test_valid_graph_and_order` | – |
| `test_type_mismatch_is_rejected_and_reported` | – |
| `test_unconnected_input_unknown_port_and_multiple_drivers` | – |
| `test_algebraic_loop_detected` | – |
| `test_loop_through_unit_delay_or_feedback_port_is_allowed` | – |
| `test_self_loop_detected` | – |
| `test_unknown_component_version_and_parameter` | – |
| `test_period_must_be_multiple_of_base_dt` | – |
| `test_editing_api_and_dynamic_ports` | – |
| `test_json_roundtrip_and_contract_format` | – |
| `test_version_pinning_warning` | – |
| `test_validation_report_iterable_for_api` | – |

### [tests/runtime/test_runtime_native.py](../../../tests/runtime/test_runtime_native.py)

**Zeigt:** Rust/C++ bauen, laden, Codec-Rundreise aller Typen, bitgleich zum Python-Regler, Hot Reload

Importiert: `vdsim.runtime`, `vdsim.runtime.build`, `vdsim.runtime.codecs`, `vdsim.runtime.codegen`, `vdsim.runtime.executor`, `vdsim.runtime.graph`, `vdsim.runtime.scaffold`

Komponenten: `node/typed_default`

| Testfunktion | Beschreibung |
|---|---|
| `test_codegen_layouts_match_python_codecs` | – |
| `test_example_headers_are_current` | – |
| `test_scaffold_rejects_layers_without_codec` | – |
| `test_rust_example_build_load_run_matches_python` | codec round trip through the native interface: EgoState + PlannedTrajectory in, ControlCommand out |
| `test_rust_codec_roundtrip_all_types` | – |
| `test_rust_hot_reload_in_graph` | – |
| `test_rust_scaffold_compiles_and_runs` | – |
| `test_cpp_example_build_load_run_matches_python` | – |
| `test_cpp_codec_roundtrip_all_types` | – |
| `test_cpp_scaffold_compiles_and_runs` | – |

### [tests/runtime/test_runtime_versioning.py](../../../tests/runtime/test_runtime_versioning.py)

**Zeigt:** Schnappschuss, Diff, Wiederherstellung, Git-Commit

Importiert: `vdsim.runtime`, `vdsim.runtime.graph`, `vdsim.runtime.versioning`

Komponenten: `node/constant`, `node/gain`, `node/scope`

| Testfunktion | Beschreibung |
|---|---|
| `test_snapshot_diff_restore` | – |
| `test_component_configuration_diff` | – |
| `test_diff_graphs_direct` | – |
| `test_git_commit_in_temporary_repo` | – |
