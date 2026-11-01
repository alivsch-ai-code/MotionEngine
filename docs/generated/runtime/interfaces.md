# Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

### [Uhr](components/node__clock.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/clock`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Clock` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `t` | `float` | s | Simulationszeit | – |

### [Konstante](components/node__constant.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/constant`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Constant` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Demux](components/node__demux.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/demux`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Demux` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `Vector` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y1` | `float` | – | – | – |
| `y2` | `float` | – | – | – |

### [Verstärkung](components/node__gain.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/gain`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Gain` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Integrator](components/node__integrator.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/integrator`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Integrator` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | nein |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Tiefpass (PT1)](components/node__lowpass.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/lowpass`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.LowPass` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Mux](components/node__mux.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/mux`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Mux` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u1` | `float` | – | – | – |
| `u2` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Vector` | – | – | – |

### [Messpunkt](components/node__probe.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/probe`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.ProbeBlock` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Any` | – | – | – |

### [Produkt](components/node__product.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/product`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Product` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u1` | `float` | – | – | – |
| `u2` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Rampe](components/node__ramp.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/ramp`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Ramp` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Ratenbegrenzer](components/node__rate_limiter.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/rate_limiter`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.RateLimiter` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Begrenzung](components/node__saturation.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/saturation`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Saturation` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Scope](components/node__scope.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/scope`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Scope` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u1` | `Any` | – | – | optional |

### [Sinus](components/node__sine.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/sine`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Sine` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Sprung](components/node__step.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/step`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Step` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Summe](components/node__sum.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/sum`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Sum` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u1` | `float` | – | – | – |
| `u2` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

### [Schalter](components/node__switch.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/switch`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.Switch` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `control` | `float` | – | – | – |
| `u1` | `Any` | – | – | – |
| `u2` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Any` | – | – | – |

### [Standardwert](components/node__typed_default.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/typed_default`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.TypedDefault` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Any` | – | – | – |

### [Verzögerung (z⁻¹)](components/node__unit_delay.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `node/unit_delay`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.runtime.blocks.UnitDelay` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | nein |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Any` | – | – | – |

## Öffentliche API

### `vdsim.runtime`

| Name | Art | Beschreibung |
|---|---|---|
| [`create_custom_node(language, name, kind, dest, **kw)`](../../../vdsim/runtime/__init__.py#L46) | Funktion | – |

### `vdsim.runtime.blocks`

| Name | Art | Beschreibung |
|---|---|---|
| [`Block`](../../../vdsim/runtime/blocks.py#L27) | Klasse | – |
| [`ConstantParams`](../../../vdsim/runtime/blocks.py#L43) | Klasse | – |
| [`Constant`](../../../vdsim/runtime/blocks.py#L48) | Klasse | – |
| [`StepParams`](../../../vdsim/runtime/blocks.py#L59) | Klasse | – |
| [`Step`](../../../vdsim/runtime/blocks.py#L66) | Klasse | – |
| [`SineParams`](../../../vdsim/runtime/blocks.py#L78) | Klasse | – |
| [`Sine`](../../../vdsim/runtime/blocks.py#L86) | Klasse | – |
| [`RampParams`](../../../vdsim/runtime/blocks.py#L98) | Klasse | – |
| [`Ramp`](../../../vdsim/runtime/blocks.py#L105) | Klasse | – |
| [`Clock`](../../../vdsim/runtime/blocks.py#L117) | Klasse | – |
| [`TypedDefaultParams`](../../../vdsim/runtime/blocks.py#L127) | Klasse | – |
| [`TypedDefault`](../../../vdsim/runtime/blocks.py#L132) | Klasse | – |
| [`GainParams`](../../../vdsim/runtime/blocks.py#L156) | Klasse | – |
| [`Gain`](../../../vdsim/runtime/blocks.py#L161) | Klasse | – |
| [`SumParams`](../../../vdsim/runtime/blocks.py#L174) | Klasse | – |
| [`Sum`](../../../vdsim/runtime/blocks.py#L179) | Klasse | – |
| [`ProductParams`](../../../vdsim/runtime/blocks.py#L204) | Klasse | – |
| [`Product`](../../../vdsim/runtime/blocks.py#L209) | Klasse | – |
| [`SaturationParams`](../../../vdsim/runtime/blocks.py#L234) | Klasse | – |
| [`Saturation`](../../../vdsim/runtime/blocks.py#L240) | Klasse | – |
| [`SwitchParams`](../../../vdsim/runtime/blocks.py#L256) | Klasse | – |
| [`Switch`](../../../vdsim/runtime/blocks.py#L261) | Klasse | – |
| [`MuxParams`](../../../vdsim/runtime/blocks.py#L274) | Klasse | – |
| [`Mux`](../../../vdsim/runtime/blocks.py#L279) | Klasse | – |
| [`Demux`](../../../vdsim/runtime/blocks.py#L296) | Klasse | – |
| [`DelayParams`](../../../vdsim/runtime/blocks.py#L315) | Klasse | – |
| [`UnitDelay`](../../../vdsim/runtime/blocks.py#L320) | Klasse | – |
| [`IntegratorParams`](../../../vdsim/runtime/blocks.py#L342) | Klasse | – |
| [`Integrator`](../../../vdsim/runtime/blocks.py#L350) | Klasse | – |
| [`LowPassParams`](../../../vdsim/runtime/blocks.py#L376) | Klasse | – |
| [`LowPass`](../../../vdsim/runtime/blocks.py#L383) | Klasse | – |
| [`RateLimiterParams`](../../../vdsim/runtime/blocks.py#L407) | Klasse | – |
| [`RateLimiter`](../../../vdsim/runtime/blocks.py#L414) | Klasse | – |
| [`ScopeParams`](../../../vdsim/runtime/blocks.py#L439) | Klasse | – |
| [`Scope`](../../../vdsim/runtime/blocks.py#L445) | Klasse | – |
| [`ProbeBlock`](../../../vdsim/runtime/blocks.py#L477) | Klasse | – |

### `vdsim.runtime.build`

| Name | Art | Beschreibung |
|---|---|---|
| [`NativeBuildError`](../../../vdsim/runtime/build.py#L49) | Klasse | – |
| [`BuildResult`](../../../vdsim/runtime/build.py#L58) | Klasse | – |
| [`CppCompiler`](../../../vdsim/runtime/build.py#L298) | Klasse | – |
| [`BuildJob`](../../../vdsim/runtime/build.py#L460) | Klasse | Background build (thread); result available via .result / wait(). |
| [`get_build_root()`](../../../vdsim/runtime/build.py#L76) | Funktion | – |
| [`set_build_root(path)`](../../../vdsim/runtime/build.py#L83) | Funktion | – |
| [`build_dir_for(language, project_dir)`](../../../vdsim/runtime/build.py#L88) | Funktion | – |
| [`toolchain_cache_dir()`](../../../vdsim/runtime/build.py#L94) | Funktion | – |
| [`source_files(language, project_dir)`](../../../vdsim/runtime/build.py#L99) | Funktion | – |
| [`source_stamp(language, project_dir)`](../../../vdsim/runtime/build.py#L113) | Funktion | – |
| [`rust_lib_name(crate_dir)`](../../../vdsim/runtime/build.py#L118) | Funktion | – |
| [`artifact_path(language, project_dir, build_dir)`](../../../vdsim/runtime/build.py#L129) | Funktion | – |
| [`needs_rebuild(language, project_dir, build_dir)`](../../../vdsim/runtime/build.py#L138) | Funktion | – |
| [`find_vs_installation()`](../../../vdsim/runtime/build.py#L146) | Funktion | – |
| [`msvc_environment()`](../../../vdsim/runtime/build.py#L169) | Funktion | Environment of vcvars64.bat (cached in memory and on disk), or None. |
| [`windows_sdk_libs_available(env)`](../../../vdsim/runtime/build.py#L222) | Funktion | – |
| [`ucrt_headers_available(env)`](../../../vdsim/runtime/build.py#L226) | Funktion | – |
| [`ensure_import_libs(env)`](../../../vdsim/runtime/build.py#L230) | Funktion | Generate import libraries for system DLLs (fallback without Windows SDK). |
| [`rust_environment()`](../../../vdsim/runtime/build.py#L270) | Funktion | (env overrides or None, note) for cargo on this machine. |
| [`find_cargo()`](../../../vdsim/runtime/build.py#L289) | Funktion | – |
| [`find_cpp_compiler()`](../../../vdsim/runtime/build.py#L306) | Funktion | Best available C++ compiler (CppCompiler with usable/problem) or None. |
| [`toolchain_status(language)`](../../../vdsim/runtime/build.py#L339) | Funktion | (available: bool, message) - checks that a trivial library can be built (cached per process). |
| [`build_rust(crate_dir, build_dir, release, timeout)`](../../../vdsim/runtime/build.py#L388) | Funktion | – |
| [`build_cpp(src_dir, build_dir, compiler, timeout, extra_flags)`](../../../vdsim/runtime/build.py#L417) | Funktion | – |
| [`build(language, project_dir, build_dir, force, **kw)`](../../../vdsim/runtime/build.py#L445) | Funktion | Build if sources are newer than the artifact (force=True: always). |
| [`build_async(language, project_dir, callback, **kw)`](../../../vdsim/runtime/build.py#L486) | Funktion | – |

### `vdsim.runtime.codecs`

| Name | Art | Beschreibung |
|---|---|---|
| [`has_codec(type_name)`](../../../vdsim/runtime/codecs.py#L41) | Funktion | – |
| [`encode(type_name, value)`](../../../vdsim/runtime/codecs.py#L69) | Funktion | – |
| [`decode(type_name, arr)`](../../../vdsim/runtime/codecs.py#L91) | Funktion | – |

### `vdsim.runtime.codegen`

| Name | Art | Beschreibung |
|---|---|---|
| [`cpp_header()`](../../../vdsim/runtime/codegen.py#L531) | Funktion | – |
| [`rust_module()`](../../../vdsim/runtime/codegen.py#L1221) | Funktion | – |
| [`write_headers(dest, cpp, rust)`](../../../vdsim/runtime/codegen.py#L1234) | Funktion | Write vdsim_node.h and/or vdsim_node.rs into dest; returns the written paths. |
| [`header_is_current(path)`](../../../vdsim/runtime/codegen.py#L1250) | Funktion | True if a project's copy of the header equals the generated text |

### `vdsim.runtime.debug`

| Name | Art | Beschreibung |
|---|---|---|
| [`Breakpoint`](../../../vdsim/runtime/debug.py#L18) | Klasse | Pause before a node is computed (or at the start of a step if node is None). |
| [`BreakHit`](../../../vdsim/runtime/debug.py#L65) | Klasse | – |
| [`NodeStep`](../../../vdsim/runtime/debug.py#L79) | Klasse | result of Executor.step_node(): which action was executed |
| [`Probe`](../../../vdsim/runtime/debug.py#L90) | Klasse | Live value of one port ("node.port"), updated whenever the node writes it. |
| [`NodeProfile`](../../../vdsim/runtime/debug.py#L115) | Klasse | – |
| [`Profiler`](../../../vdsim/runtime/debug.py#L139) | Klasse | Per-node computation time (all phases of a node within one step are summed). |

### `vdsim.runtime.executor`

| Name | Art | Beschreibung |
|---|---|---|
| [`ExecutionError`](../../../vdsim/runtime/executor.py#L36) | Klasse | Exception inside a node (German message, original exception as __cause__). |
| [`RuntimeTypeError`](../../../vdsim/runtime/executor.py#L44) | Klasse | – |
| [`RunResult`](../../../vdsim/runtime/executor.py#L49) | Klasse | – |
| [`Executor`](../../../vdsim/runtime/executor.py#L83) | Klasse | Runs a Graph. |

### `vdsim.runtime.graph`

| Name | Art | Beschreibung |
|---|---|---|
| [`GraphError`](../../../vdsim/runtime/graph.py#L44) | Klasse | Invalid graph operation (German message). |
| [`GraphValidationError`](../../../vdsim/runtime/graph.py#L48) | Klasse | – |
| [`ValidationIssue`](../../../vdsim/runtime/graph.py#L56) | Klasse | – |
| [`ValidationReport`](../../../vdsim/runtime/graph.py#L72) | Klasse | – |
| [`Node`](../../../vdsim/runtime/graph.py#L128) | Klasse | – |
| [`Connection`](../../../vdsim/runtime/graph.py#L162) | Klasse | – |
| [`Graph`](../../../vdsim/runtime/graph.py#L241) | Klasse | – |
| [`split_endpoint(text)`](../../../vdsim/runtime/graph.py#L207) | Funktion | – |
| [`resolve_spec(spec, base_dir)`](../../../vdsim/runtime/graph.py#L214) | Funktion | Make relative paths of custom-node specs absolute (graph dir, cwd, project root). |

### `vdsim.runtime.hot_reload`

| Name | Art | Beschreibung |
|---|---|---|
| [`ReloadEvent`](../../../vdsim/runtime/hot_reload.py#L26) | Klasse | – |
| [`HotReloader`](../../../vdsim/runtime/hot_reload.py#L37) | Klasse | – |

### `vdsim.runtime.native`

| Name | Art | Beschreibung |
|---|---|---|
| [`NativeNodeError`](../../../vdsim/runtime/native.py#L69) | Klasse | – |
| [`NativeLibrary`](../../../vdsim/runtime/native.py#L104) | Klasse | One loaded (shadow-copied) node library, shared by all instances of that build. |
| [`NativeComponent`](../../../vdsim/runtime/native.py#L212) | Klasse | Base class of the generated component classes (one per loaded library). |
| [`NativeSource`](../../../vdsim/runtime/native.py#L434) | Klasse | Reload information for a native node (rebuild on source change, shadow-copy reload). |
| [`library(path, language)`](../../../vdsim/runtime/native.py#L201) | Funktion | – |
| [`make_native_class(lib, language)`](../../../vdsim/runtime/native.py#L397) | Funktion | – |
| [`load_native_node(language, path, params, build_dir)`](../../../vdsim/runtime/native.py#L493) | Funktion | Loader for "rust:" / "cpp:" specs: build if needed, load, instantiate. |

### `vdsim.runtime.python_nodes`

| Name | Art | Beschreibung |
|---|---|---|
| [`PythonSource`](../../../vdsim/runtime/python_nodes.py#L111) | Klasse | Reload information attached to an instance as `_vdsim_source`. |
| [`parse_python_spec(rest)`](../../../vdsim/runtime/python_nodes.py#L27) | Funktion | "dir/file.py:Class" / "C:/dir/file.py:Class" / "dir/file.py" -> (path, class name or None) |
| [`resolve_path(path, roots)`](../../../vdsim/runtime/python_nodes.py#L35) | Funktion | – |
| [`file_stamp(path)`](../../../vdsim/runtime/python_nodes.py#L48) | Funktion | – |
| [`load_class(path, class_name)`](../../../vdsim/runtime/python_nodes.py#L53) | Funktion | Execute the file under a fresh module name and return (class, module). |
| [`transfer_params(old_params, new_cls)`](../../../vdsim/runtime/python_nodes.py#L101) | Funktion | carry parameter values over to a (possibly changed) parameter dataclass |
| [`load_python_node(rest, params, roots)`](../../../vdsim/runtime/python_nodes.py#L149) | Funktion | Loader for "python:" specs (registered by vdsim.runtime). |

### `vdsim.runtime.recorder`

| Name | Art | Beschreibung |
|---|---|---|
| [`Event`](../../../vdsim/runtime/recorder.py#L27) | Klasse | – |
| [`Recorder`](../../../vdsim/runtime/recorder.py#L57) | Klasse | – |
| [`flatten(name, value, out)`](../../../vdsim/runtime/recorder.py#L38) | Funktion | value -> scalar columns (dataclasses expanded one level) |

### `vdsim.runtime.scaffold`

| Name | Art | Beschreibung |
|---|---|---|
| [`ScaffoldResult`](../../../vdsim/runtime/scaffold.py#L32) | Klasse | – |
| [`layer_ports(kind)`](../../../vdsim/runtime/scaffold.py#L47) | Funktion | – |
| [`node_info(name, kind, label, ins, outs, ft)`](../../../vdsim/runtime/scaffold.py#L56) | Funktion | – |
| [`create_custom_node(language, name, kind, dest, label, overwrite)`](../../../vdsim/runtime/scaffold.py#L270) | Funktion | Create a runnable custom-node skeleton with the ports of layer `kind`. |

### `vdsim.runtime.versioning`

| Name | Art | Beschreibung |
|---|---|---|
| [`Version`](../../../vdsim/runtime/versioning.py#L34) | Klasse | – |
| [`GraphDiff`](../../../vdsim/runtime/versioning.py#L51) | Klasse | – |
| [`ConfigDiff`](../../../vdsim/runtime/versioning.py#L156) | Klasse | – |
| [`VersionStore`](../../../vdsim/runtime/versioning.py#L179) | Klasse | – |
| [`canonical(doc)`](../../../vdsim/runtime/versioning.py#L25) | Funktion | – |
| [`content_hash(doc)`](../../../vdsim/runtime/versioning.py#L29) | Funktion | – |
| [`flatten_dict(d, prefix)`](../../../vdsim/runtime/versioning.py#L99) | Funktion | – |
| [`diff_dicts(a, b)`](../../../vdsim/runtime/versioning.py#L110) | Funktion | flattened {key: (old, new)}; _MISSING for absent keys |
| [`diff_graphs(a, b)`](../../../vdsim/runtime/versioning.py#L121) | Funktion | Structured diff of two graph documents (dicts in the contracts.md format). |
| [`diff_documents(a, b)`](../../../vdsim/runtime/versioning.py#L172) | Funktion | – |
