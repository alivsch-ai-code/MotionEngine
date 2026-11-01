# MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.matlab.__main__`

| Name | Art | Beschreibung |
|---|---|---|
| [`main(argv)`](../../../vdsim/matlab/__main__.py#L16) | Funktion | – |

### `vdsim.matlab.analysis`

| Name | Art | Beschreibung |
|---|---|---|
| [`VariableInfo`](../../../vdsim/matlab/analysis.py#L39) | Klasse | – |
| [`FunctionAnalysis`](../../../vdsim/matlab/analysis.py#L50) | Klasse | – |
| [`FileAnalysis`](../../../vdsim/matlab/analysis.py#L78) | Klasse | – |
| [`analyze(source, input_types)`](../../../vdsim/matlab/analysis.py#L582) | Funktion | Analyze an MFile, a path or MATLAB source text -> FileAnalysis. |
| [`dataflow_dot(fa)`](../../../vdsim/matlab/analysis.py#L622) | Funktion | Graphviz DOT of the data-flow graph of one function (inputs -> intermediates -> outputs). |
| [`callgraph_dot(file_analysis)`](../../../vdsim/matlab/analysis.py#L649) | Funktion | – |

### `vdsim.matlab.builtins`

| Name | Art | Beschreibung |
|---|---|---|
| [`BuiltinSpec`](../../../vdsim/matlab/builtins.py#L30) | Klasse | – |
| [`MStruct`](../../../vdsim/matlab/builtins.py#L53) | Klasse | Scalar MATLAB struct (ordered fields, value semantics through copy on assignment). |
| [`MCell`](../../../vdsim/matlab/builtins.py#L66) | Klasse | Cell array: 2-D numpy object array. |
| [`MFunction`](../../../vdsim/matlab/builtins.py#L97) | Klasse | Function handle: named (@sin, @local) or anonymous (@(x) x.^2 with captured workspace). |
| [`register_builtin(name, func, multi, ctx)`](../../../vdsim/matlab/builtins.py#L40) | Funktion | – |
| [`builtin(multi, ctx, *names)`](../../../vdsim/matlab/builtins.py#L45) | Funktion | – |
| [`elementwise(name, fn, npfn, domain)`](../../../vdsim/matlab/builtins.py#L132) | Funktion | scalar via math (bitwise identical to generated Python), arrays via numpy |
| [`format_value(v)`](../../../vdsim/matlab/builtins.py#L701) | Funktion | short display like MATLAB's 'format short' |

### `vdsim.matlab.codegen`

| Name | Art | Beschreibung |
|---|---|---|
| [`generate(mfile, target, function, input_types, **options)`](../../../vdsim/matlab/codegen/__init__.py#L18) | Funktion | Translate ``function`` (default: main function) of an MFile/path into ``target``. |

### `vdsim.matlab.codegen.base`

| Name | Art | Beschreibung |
|---|---|---|
| [`GeneratedCode`](../../../vdsim/matlab/codegen/base.py#L26) | Klasse | – |
| [`Unsupported`](../../../vdsim/matlab/codegen/base.py#L55) | Klasse | – |
| [`BaseGenerator`](../../../vdsim/matlab/codegen/base.py#L69) | Klasse | – |
| [`snake(name)`](../../../vdsim/matlab/codegen/base.py#L61) | Funktion | – |
| [`camel(name)`](../../../vdsim/matlab/codegen/base.py#L65) | Funktion | – |
| [`first_assignments(f)`](../../../vdsim/matlab/codegen/base.py#L212) | Funktion | Variables whose first occurrence is an unconditional top-level 'x = expr' (inline declaration). |
| [`assigned_count(f)`](../../../vdsim/matlab/codegen/base.py#L237) | Funktion | – |
| [`index_mutated(f)`](../../../vdsim/matlab/codegen/base.py#L252) | Funktion | – |
| [`uses_name(f, name)`](../../../vdsim/matlab/codegen/base.py#L266) | Funktion | – |
| [`int_literal(e)`](../../../vdsim/matlab/codegen/base.py#L270) | Funktion | – |

### `vdsim.matlab.codegen.cpp`

| Name | Art | Beschreibung |
|---|---|---|
| [`CppGenerator`](../../../vdsim/matlab/codegen/cpp.py#L261) | Klasse | – |

### `vdsim.matlab.codegen.native`

| Name | Art | Beschreibung |
|---|---|---|
| [`NativeGenerator`](../../../vdsim/matlab/codegen/native.py#L26) | Klasse | Subclasses define the syntax hooks (see CppGenerator / RustGenerator). |

### `vdsim.matlab.codegen.python`

| Name | Art | Beschreibung |
|---|---|---|
| [`PythonGenerator`](../../../vdsim/matlab/codegen/python.py#L54) | Klasse | – |

### `vdsim.matlab.codegen.rust`

| Name | Art | Beschreibung |
|---|---|---|
| [`RustGenerator`](../../../vdsim/matlab/codegen/rust.py#L322) | Klasse | – |

### `vdsim.matlab.component`

| Name | Art | Beschreibung |
|---|---|---|
| [`MatlabComponent`](../../../vdsim/matlab/component.py#L34) | Klasse | Base class of the dynamically created MATLAB components. |
| [`load_matlab_component(path, function, backend, params, input_types, name, version)`](../../../vdsim/matlab/component.py#L124) | Funktion | Load a MATLAB function file as Component instance (see module docstring). |
| [`matlab_loader(spec, params)`](../../../vdsim/matlab/component.py#L171) | Funktion | Loader for 'matlab:pfad/datei.m[:funktion]' (registered in vdsim.matlab). |

### `vdsim.matlab.convert`

| Name | Art | Beschreibung |
|---|---|---|
| [`convert_file(path, target, out_dir, function, input_types, force)`](../../../vdsim/matlab/convert.py#L11) | Funktion | Convert ``path`` and write the sources to ``out_dir`` (one sub folder per target for 'all'). |

### `vdsim.matlab.errors`

| Name | Art | Beschreibung |
|---|---|---|
| [`MatlabError`](../../../vdsim/matlab/errors.py#L8) | Klasse | Base class; carries an optional source position. |
| [`MatlabSyntaxError`](../../../vdsim/matlab/errors.py#L24) | Klasse | Lexer / parser error (line and column of the offending token). |
| [`MatlabRuntimeError`](../../../vdsim/matlab/errors.py#L28) | Klasse | Error raised while interpreting MATLAB code (also MATLAB's error()). |
| [`UnsupportedConstruct`](../../../vdsim/matlab/errors.py#L32) | Klasse | A construct the code generator cannot translate. |
| [`Diagnostic`](../../../vdsim/matlab/errors.py#L37) | Klasse | – |

### `vdsim.matlab.interpreter`

| Name | Art | Beschreibung |
|---|---|---|
| [`Frame`](../../../vdsim/matlab/interpreter.py#L177) | Klasse | – |
| [`Interpreter`](../../../vdsim/matlab/interpreter.py#L185) | Klasse | Executes MATLAB functions and scripts; see module docstring. |
| [`to_value(a)`](../../../vdsim/matlab/interpreter.py#L41) | Funktion | Python/numpy argument -> interpreter value (1-D sequences become column vectors) |
| [`binary_op(op, a, b)`](../../../vdsim/matlab/interpreter.py#L60) | Funktion | – |
| [`unary_op(op, v)`](../../../vdsim/matlab/interpreter.py#L162) | Funktion | – |
| [`run_function(path, function, nargout, *args, **kw)`](../../../vdsim/matlab/interpreter.py#L943) | Funktion | Convenience: parse ``path`` and call ``function`` (default: main function). |

### `vdsim.matlab.latex`

| Name | Art | Beschreibung |
|---|---|---|
| [`prec_of(e)`](../../../vdsim/matlab/latex.py#L30) | Funktion | – |
| [`to_matlab(e)`](../../../vdsim/matlab/latex.py#L47) | Funktion | – |
| [`stmt_to_matlab(s)`](../../../vdsim/matlab/latex.py#L102) | Funktion | – |
| [`latex_name(name)`](../../../vdsim/matlab/latex.py#L118) | Funktion | Typeset an identifier (see module docstring). |
| [`to_latex(e, functions)`](../../../vdsim/matlab/latex.py#L167) | Funktion | LaTeX of an expression; ``functions`` = names that are calls (not array indexing). |
| [`assignment_latex(stmt, functions, arrays)`](../../../vdsim/matlab/latex.py#L281) | Funktion | LaTeX of an assignment statement (``arrays``: names indexed as arrays, not calls). |
| [`expr_latex(e, functions, arrays)`](../../../vdsim/matlab/latex.py#L295) | Funktion | – |

### `vdsim.matlab.lexer`

| Name | Art | Beschreibung |
|---|---|---|
| [`Token`](../../../vdsim/matlab/lexer.py#L37) | Klasse | – |
| [`Comment`](../../../vdsim/matlab/lexer.py#L58) | Klasse | – |
| [`Lexer`](../../../vdsim/matlab/lexer.py#L67) | Klasse | – |
| [`tokenize(source, path)`](../../../vdsim/matlab/lexer.py#L321) | Funktion | – |

### `vdsim.matlab.nodes`

| Name | Art | Beschreibung |
|---|---|---|
| [`Node`](../../../vdsim/matlab/nodes.py#L14) | Klasse | – |
| [`Expr`](../../../vdsim/matlab/nodes.py#L41) | Klasse | – |
| [`Number`](../../../vdsim/matlab/nodes.py#L46) | Klasse | – |
| [`String`](../../../vdsim/matlab/nodes.py#L52) | Klasse | – |
| [`Ident`](../../../vdsim/matlab/nodes.py#L58) | Klasse | – |
| [`Colon`](../../../vdsim/matlab/nodes.py#L63) | Klasse | Magic colon ':' in an index (all elements). |
| [`End`](../../../vdsim/matlab/nodes.py#L68) | Klasse | 'end' inside an index: last index of the indexed dimension. |
| [`Placeholder`](../../../vdsim/matlab/nodes.py#L73) | Klasse | '~' output placeholder in [~, i] = max(x). |
| [`Binary`](../../../vdsim/matlab/nodes.py#L78) | Klasse | – |
| [`Unary`](../../../vdsim/matlab/nodes.py#L85) | Klasse | – |
| [`Postfix`](../../../vdsim/matlab/nodes.py#L91) | Klasse | – |
| [`Range`](../../../vdsim/matlab/nodes.py#L97) | Klasse | – |
| [`Matrix`](../../../vdsim/matlab/nodes.py#L104) | Klasse | – |
| [`CellArray`](../../../vdsim/matlab/nodes.py#L109) | Klasse | – |
| [`Index`](../../../vdsim/matlab/nodes.py#L114) | Klasse | x(args): array indexing or function call (resolved at run time / by analysis). |
| [`CellIndex`](../../../vdsim/matlab/nodes.py#L121) | Klasse | – |
| [`Field`](../../../vdsim/matlab/nodes.py#L127) | Klasse | – |
| [`DynField`](../../../vdsim/matlab/nodes.py#L133) | Klasse | – |
| [`AnonFunc`](../../../vdsim/matlab/nodes.py#L139) | Klasse | – |
| [`FuncHandle`](../../../vdsim/matlab/nodes.py#L145) | Klasse | – |
| [`Stmt`](../../../vdsim/matlab/nodes.py#L151) | Klasse | – |
| [`ExprStmt`](../../../vdsim/matlab/nodes.py#L158) | Klasse | – |
| [`Assign`](../../../vdsim/matlab/nodes.py#L164) | Klasse | – |
| [`If`](../../../vdsim/matlab/nodes.py#L172) | Klasse | – |
| [`For`](../../../vdsim/matlab/nodes.py#L178) | Klasse | – |
| [`While`](../../../vdsim/matlab/nodes.py#L185) | Klasse | – |
| [`Switch`](../../../vdsim/matlab/nodes.py#L191) | Klasse | – |
| [`TryCatch`](../../../vdsim/matlab/nodes.py#L198) | Klasse | – |
| [`Break`](../../../vdsim/matlab/nodes.py#L205) | Klasse | – |
| [`Continue`](../../../vdsim/matlab/nodes.py#L210) | Klasse | – |
| [`Return`](../../../vdsim/matlab/nodes.py#L215) | Klasse | – |
| [`Global`](../../../vdsim/matlab/nodes.py#L220) | Klasse | – |
| [`Persistent`](../../../vdsim/matlab/nodes.py#L225) | Klasse | – |
| [`Command`](../../../vdsim/matlab/nodes.py#L230) | Klasse | – |
| [`Function`](../../../vdsim/matlab/nodes.py#L237) | Klasse | – |
| [`MFile`](../../../vdsim/matlab/nodes.py#L249) | Klasse | – |
| [`body_statements(body)`](../../../vdsim/matlab/nodes.py#L283) | Funktion | all statements in a body, recursively (including nested blocks) |

### `vdsim.matlab.parser`

| Name | Art | Beschreibung |
|---|---|---|
| [`Parser`](../../../vdsim/matlab/parser.py#L27) | Klasse | – |
| [`parse(source, path)`](../../../vdsim/matlab/parser.py#L607) | Funktion | Parse MATLAB source text into an ``MFile`` AST (raises MatlabSyntaxError). |
| [`parse_file(path)`](../../../vdsim/matlab/parser.py#L613) | Funktion | – |

### `vdsim.matlab.pyruntime`

| Name | Art | Beschreibung |
|---|---|---|
| [`m_norm(v)`](../../../vdsim/matlab/pyruntime.py#L26) | Funktion | 1x1 arrays -> Python scalars, drop all-zero imaginary parts (MATLAB does the same) |
| [`m_arr(v)`](../../../vdsim/matlab/pyruntime.py#L52) | Funktion | any numeric value -> 2-D numpy array (strings -> char codes) |
| [`m_div(a, b)`](../../../vdsim/matlab/pyruntime.py#L65) | Funktion | scalar right division with IEEE semantics (1/0 = Inf, 0/0 = NaN) |
| [`m_pow(a, b)`](../../../vdsim/matlab/pyruntime.py#L75) | Funktion | scalar power, MATLAB semantics (0^-1 = Inf, overflow -> Inf, complex for negative^fraction) |
| [`m_round(x)`](../../../vdsim/matlab/pyruntime.py#L86) | Funktion | round half away from zero (Python's round() rounds half to even) |
| [`m_mod(a, m)`](../../../vdsim/matlab/pyruntime.py#L99) | Funktion | mod(a, m) = a - floor(a/m)*m, mod(a, 0) = a (result has the sign of m) |
| [`m_rem(a, b)`](../../../vdsim/matlab/pyruntime.py#L115) | Funktion | rem(a, b) = a - fix(a/b)*b (sign of a), rem(a, 0) = NaN |
| [`m_sign(x)`](../../../vdsim/matlab/pyruntime.py#L125) | Funktion | – |
| [`m_wrap_to_pi(x)`](../../../vdsim/matlab/pyruntime.py#L133) | Funktion | wrapToPi: [-pi, pi], positive odd multiples of pi map to +pi |
| [`m_columns(x)`](../../../vdsim/matlab/pyruntime.py#L141) | Funktion | iteration of a MATLAB for loop: the columns of x (scalars for row vectors) |
| [`m_colon(a, s, b)`](../../../vdsim/matlab/pyruntime.py#L147) | Funktion | a:s:b as row vector; elements a + k*s (k = 0..n), last element clipped to b |
| [`m_truth(v)`](../../../vdsim/matlab/pyruntime.py#L159) | Funktion | condition of if/while: all elements nonzero and not empty |
| [`m_get(x, *idx)`](../../../vdsim/matlab/pyruntime.py#L192) | Funktion | x(i), x(i, j): 1-based, column-major, result shape following MATLAB's rules |
| [`m_set(x, idx, value, delete)`](../../../vdsim/matlab/pyruntime.py#L231) | Funktion | x(idx...) = value with MATLAB growth rules; returns the new array (copy semantics) |
| [`m_cat(rows)`](../../../vdsim/matlab/pyruntime.py#L311) | Funktion | [a, b; c, d] (rows: list of lists of values); strings concatenate to strings |
| [`m_sprintf(fmt, *args)`](../../../vdsim/matlab/pyruntime.py#L341) | Funktion | MATLAB sprintf: C format specifiers, escapes, format recycling over all arguments |

### `vdsim.matlab.toolchains`

| Name | Art | Beschreibung |
|---|---|---|
| [`ToolchainError`](../../../vdsim/matlab/toolchains.py#L27) | Klasse | Compilation failed (message contains the compiler output). |
| [`Toolchain`](../../../vdsim/matlab/toolchains.py#L32) | Klasse | – |
| [`find_rustc()`](../../../vdsim/matlab/toolchains.py#L48) | Funktion | – |
| [`find_cargo()`](../../../vdsim/matlab/toolchains.py#L60) | Funktion | – |
| [`find_vcvars()`](../../../vdsim/matlab/toolchains.py#L77) | Funktion | Path of vcvars64.bat of the newest Visual Studio with C++ tools (or None). |
| [`msvc_environment(vcvars)`](../../../vdsim/matlab/toolchains.py#L99) | Funktion | Environment variables after 'call vcvars64.bat' (captured once). |
| [`find_cpp_compiler()`](../../../vdsim/matlab/toolchains.py#L114) | Funktion | C++17 compiler: $VDSIM_CXX, g++ or clang++ on PATH, else MSVC via vswhere/vcvars64. |
| [`compile_cpp(sources, output, include_dirs, toolchain, cwd)`](../../../vdsim/matlab/toolchains.py#L136) | Funktion | Compile C++17 sources to an executable; raises ToolchainError with the compiler log. |
| [`compile_rust(source, output, toolchain, cwd, optimize)`](../../../vdsim/matlab/toolchains.py#L155) | Funktion | Compile a Rust crate root file with rustc (std only). |
| [`msvc_linker()`](../../../vdsim/matlab/toolchains.py#L176) | Funktion | MSVC link.exe (Windows); avoids a foreign 'link' on PATH (e.g. |
| [`available()`](../../../vdsim/matlab/toolchains.py#L194) | Funktion | Summary of the detected toolchains (CLI 'toolchains'). |
| [`probe_rust_link()`](../../../vdsim/matlab/toolchains.py#L204) | Funktion | (ok, message): can rustc build and link an executable here? |
| [`probe_cpp()`](../../../vdsim/matlab/toolchains.py#L210) | Funktion | (ok, message): can the C++ compiler build and link an executable here (e.g. |
| [`check_rust(source, cwd)`](../../../vdsim/matlab/toolchains.py#L235) | Funktion | Type-check a Rust module without linking (rustc --emit=metadata). |

### `vdsim.matlab.typeinfer`

| Name | Art | Beschreibung |
|---|---|---|
| [`MType`](../../../vdsim/matlab/typeinfer.py#L49) | Klasse | – |
| [`FunctionTypes`](../../../vdsim/matlab/typeinfer.py#L167) | Klasse | Inferred types of one function for a given input signature. |
| [`TypeInference`](../../../vdsim/matlab/typeinfer.py#L177) | Klasse | – |
| [`array(rows, cols)`](../../../vdsim/matlab/typeinfer.py#L81) | Funktion | – |
| [`parse_type(text, size)`](../../../vdsim/matlab/typeinfer.py#L87) | Funktion | – |
| [`join(a, b)`](../../../vdsim/matlab/typeinfer.py#L109) | Funktion | – |
| [`broadcast(a, b)`](../../../vdsim/matlab/typeinfer.py#L127) | Funktion | – |
| [`const_value(e)`](../../../vdsim/matlab/typeinfer.py#L145) | Funktion | constant folding for literal sizes (zeros(3, 1), 1:4, 2*n with literal n) |
| [`builtin_type(name, ts, nodes, nargout, inf)`](../../../vdsim/matlab/typeinfer.py#L422) | Funktion | – |
| [`infer_types(mfile, function, input_types)`](../../../vdsim/matlab/typeinfer.py#L521) | Funktion | Infer the types of all variables of ``function`` (default: main) -> FunctionTypes. |

### `vdsim.matlab.verify`

| Name | Art | Beschreibung |
|---|---|---|
| [`flatten(value)`](../../../vdsim/matlab/verify.py#L32) | Funktion | Output value -> list of floats (column-major). |
| [`write_inputs(path, cases, signature)`](../../../vdsim/matlab/verify.py#L39) | Funktion | – |
| [`read_outputs(text)`](../../../vdsim/matlab/verify.py#L54) | Funktion | – |
| [`rust_main(sig)`](../../../vdsim/matlab/verify.py#L59) | Funktion | – |
| [`cpp_main(sig)`](../../../vdsim/matlab/verify.py#L93) | Funktion | – |
| [`load_python(code)`](../../../vdsim/matlab/verify.py#L122) | Funktion | Exec generated Python code into a fresh module object. |
| [`run_interpreter(path, cases, function)`](../../../vdsim/matlab/verify.py#L129) | Funktion | – |
| [`run_python(code, cases)`](../../../vdsim/matlab/verify.py#L135) | Funktion | – |
| [`build_native(code, workdir)`](../../../vdsim/matlab/verify.py#L146) | Funktion | Write the generated sources plus a test main into workdir and compile -> executable path. |
| [`run_native(code, cases, workdir, exe)`](../../../vdsim/matlab/verify.py#L163) | Funktion | – |
| [`deviation(ref, other)`](../../../vdsim/matlab/verify.py#L174) | Funktion | – |
| [`verify_file(path, cases, targets, workdir, function, input_types)`](../../../vdsim/matlab/verify.py#L194) | Funktion | Compare the generated code of all ``targets`` with the interpreter on ``cases``. |
