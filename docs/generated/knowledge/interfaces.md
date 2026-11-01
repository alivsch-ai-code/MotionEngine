# Wissens-, Dokumentations- und Rückverfolgbarkeitssystem – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.knowledge`

| Name | Art | Beschreibung |
|---|---|---|
| [`build_graph(kb, **kwargs)`](../../../vdsim/knowledge/__init__.py#L22) | Funktion | – |
| [`generate_docs(kb, out_dir, **kwargs)`](../../../vdsim/knowledge/__init__.py#L27) | Funktion | – |

### `vdsim.knowledge.cli`

| Name | Art | Beschreibung |
|---|---|---|
| [`main(argv)`](../../../vdsim/knowledge/cli.py#L21) | Funktion | – |

### `vdsim.knowledge.collector`

| Name | Art | Beschreibung |
|---|---|---|
| [`FunctionInfo`](../../../vdsim/knowledge/collector.py#L87) | Klasse | – |
| [`ClassInfo`](../../../vdsim/knowledge/collector.py#L103) | Klasse | – |
| [`ModuleInfo`](../../../vdsim/knowledge/collector.py#L120) | Klasse | – |
| [`ConceptSection`](../../../vdsim/knowledge/collector.py#L143) | Klasse | – |
| [`DocFile`](../../../vdsim/knowledge/collector.py#L162) | Klasse | – |
| [`ComponentInfo`](../../../vdsim/knowledge/collector.py#L172) | Klasse | – |
| [`UsageInfo`](../../../vdsim/knowledge/collector.py#L205) | Klasse | a test file, example or configuration file and what it refers to |
| [`DataTypeInfo`](../../../vdsim/knowledge/collector.py#L219) | Klasse | – |
| [`ParamSet`](../../../vdsim/knowledge/collector.py#L230) | Klasse | parameter dataclass defined in a package (fields with unit / label / limits) |
| [`ConceptInfo`](../../../vdsim/knowledge/collector.py#L239) | Klasse | – |
| [`PackageInfo`](../../../vdsim/knowledge/collector.py#L255) | Klasse | – |
| [`KnowledgeBase`](../../../vdsim/knowledge/collector.py#L301) | Klasse | – |
| [`Collector`](../../../vdsim/knowledge/collector.py#L591) | Klasse | – |
| [`first_sentence(text)`](../../../vdsim/knowledge/collector.py#L379) | Funktion | – |
| [`as_list(value)`](../../../vdsim/knowledge/collector.py#L387) | Funktion | – |
| [`package_name(module)`](../../../vdsim/knowledge/collector.py#L395) | Funktion | – |
| [`humanize(concept_id)`](../../../vdsim/knowledge/collector.py#L402) | Funktion | – |
| [`parse_module(path, name, package, root)`](../../../vdsim/knowledge/collector.py#L450) | Funktion | – |
| [`parse_markdown_doc(path, package, root)`](../../../vdsim/knowledge/collector.py#L547) | Funktion | – |
| [`collect(root, import_modules, packages)`](../../../vdsim/knowledge/collector.py#L1326) | Funktion | Build the KnowledgeBase of the repository (never raises for broken or missing files) |

### `vdsim.knowledge.generator`

| Name | Art | Beschreibung |
|---|---|---|
| [`Linker`](../../../vdsim/knowledge/generator.py#L46) | Klasse | file mode: relative Markdown links from the page directory; gui mode: "node:<graph id>" links |
| [`md_escape(text)`](../../../vdsim/knowledge/generator.py#L109) | Funktion | – |
| [`table(header, rows)`](../../../vdsim/knowledge/generator.py#L113) | Funktion | – |
| [`fmt_value(value)`](../../../vdsim/knowledge/generator.py#L122) | Funktion | – |
| [`bullet(items)`](../../../vdsim/knowledge/generator.py#L136) | Funktion | – |
| [`cite_text(kb, text, linker)`](../../../vdsim/knowledge/generator.py#L146) | Funktion | "[@werling2011, Abschn. |
| [`ref_links(kb, ids, linker)`](../../../vdsim/knowledge/generator.py#L162) | Funktion | – |
| [`concept_links(kb, ids, linker)`](../../../vdsim/knowledge/generator.py#L170) | Funktion | – |
| [`nav(pkg_name, linker, current)`](../../../vdsim/knowledge/generator.py#L179) | Funktion | – |
| [`header(pkg, linker, page)`](../../../vdsim/knowledge/generator.py#L187) | Funktion | – |
| [`stub_notice(pkg)`](../../../vdsim/knowledge/generator.py#L193) | Funktion | – |
| [`page_index(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L200) | Funktion | – |
| [`page_interfaces(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L285) | Funktion | – |
| [`page_configuration(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L328) | Funktion | – |
| [`param_table(params)`](../../../vdsim/knowledge/generator.py#L361) | Funktion | – |
| [`page_theory(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L372) | Funktion | – |
| [`page_examples(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L406) | Funktion | – |
| [`page_limitations(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L427) | Funktion | – |
| [`page_validation(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L454) | Funktion | – |
| [`package_reference_ids(kb, pkg)`](../../../vdsim/knowledge/generator.py#L486) | Funktion | – |
| [`page_references(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L510) | Funktion | – |
| [`trace_tests(kb, trace)`](../../../vdsim/knowledge/generator.py#L527) | Funktion | – |
| [`trace_rows(kb, traces, linker, with_package)`](../../../vdsim/knowledge/generator.py#L536) | Funktion | – |
| [`page_traceability(kb, pkg, linker)`](../../../vdsim/knowledge/generator.py#L551) | Funktion | – |
| [`package_page(kb, pkg_name, page, linker)`](../../../vdsim/knowledge/generator.py#L583) | Funktion | – |
| [`component_page(kb, cid, linker)`](../../../vdsim/knowledge/generator.py#L590) | Funktion | – |
| [`concept_page(kb, cid, linker)`](../../../vdsim/knowledge/generator.py#L649) | Funktion | – |
| [`node_page(kb, graph, node_id, linker)`](../../../vdsim/knowledge/generator.py#L671) | Funktion | generic page for any graph node (modules, classes, functions, references, tests, ...) |
| [`readme(kb, graph, linker)`](../../../vdsim/knowledge/generator.py#L740) | Funktion | – |
| [`traceability_matrix(kb, linker)`](../../../vdsim/knowledge/generator.py#L777) | Funktion | – |
| [`bibliography(kb, linker)`](../../../vdsim/knowledge/generator.py#L795) | Funktion | – |
| [`report(kb)`](../../../vdsim/knowledge/generator.py#L814) | Funktion | – |
| [`write_if_changed(path, content)`](../../../vdsim/knowledge/generator.py#L832) | Funktion | – |
| [`render_all(kb, graph)`](../../../vdsim/knowledge/generator.py#L847) | Funktion | {relative path inside docs/generated: content} |
| [`generate(kb, out_dir, graph, clean, check)`](../../../vdsim/knowledge/generator.py#L867) | Funktion | write docs/generated; returns {"written": [...], "unchanged": [...], "removed": [...], "stats": {...}} |
| [`init_package_docs(kb, name, overwrite)`](../../../vdsim/knowledge/generator.py#L929) | Funktion | write template module.yaml / theory.md for a package without hand-written docs |

### `vdsim.knowledge.graph`

| Name | Art | Beschreibung |
|---|---|---|
| [`Node`](../../../vdsim/knowledge/graph.py#L44) | Klasse | – |
| [`Edge`](../../../vdsim/knowledge/graph.py#L59) | Klasse | – |
| [`KnowledgeGraph`](../../../vdsim/knowledge/graph.py#L72) | Klasse | – |
| [`build_graph(kb)`](../../../vdsim/knowledge/graph.py#L352) | Funktion | – |
| [`component_file(component_id)`](../../../vdsim/knowledge/graph.py#L545) | Funktion | – |
| [`force_layout(n, edges, iterations, seed, size, positions)`](../../../vdsim/knowledge/graph.py#L551) | Funktion | Fruchterman-Reingold layout (deterministic for a given seed); returns an (n, 2) array |

### `vdsim.knowledge.gui`

| Name | Art | Beschreibung |
|---|---|---|
| [`main(argv)`](../../../vdsim/knowledge/gui.py#L6) | Funktion | – |

### `vdsim.knowledge.markdown`

| Name | Art | Beschreibung |
|---|---|---|
| [`MarkdownRenderer`](../../../vdsim/knowledge/markdown.py#L82) | Klasse | – |
| [`is_expert_heading(title)`](../../../vdsim/knowledge/markdown.py#L50) | Funktion | – |
| [`filter_expert(text, expert)`](../../../vdsim/knowledge/markdown.py#L55) | Funktion | remove (expert=False) or keep expert sections / blocks |
| [`slugify(text)`](../../../vdsim/knowledge/markdown.py#L77) | Funktion | – |
| [`markdown_to_html(text, render_math, expert, cite, link, css, math_color, mark_expert)`](../../../vdsim/knowledge/markdown.py#L300) | Funktion | – |

### `vdsim.knowledge.mathrender`

| Name | Art | Beschreibung |
|---|---|---|
| [`RenderResult`](../../../vdsim/knowledge/mathrender.py#L31) | Klasse | – |
| [`normalize(latex)`](../../../vdsim/knowledge/mathrender.py#L38) | Funktion | map LaTeX commands to the matplotlib mathtext subset |
| [`render_formula(latex, fmt, fontsize, color, dpi, scale, cache)`](../../../vdsim/knowledge/mathrender.py#L79) | Funktion | Render one formula (without the surrounding $) and return a RenderResult or None |
| [`can_render(latex)`](../../../vdsim/knowledge/mathrender.py#L116) | Funktion | True if mathtext can parse the formula (no file is written) |
| [`extract_formulas(text)`](../../../vdsim/knowledge/mathrender.py#L126) | Funktion | [(display: bool, latex)] in document order |

### `vdsim.knowledge.paths`

| Name | Art | Beschreibung |
|---|---|---|
| [`root_dir(root)`](../../../vdsim/knowledge/paths.py#L22) | Funktion | – |
| [`references_dir(root)`](../../../vdsim/knowledge/paths.py#L26) | Funktion | – |
| [`generated_dir(root)`](../../../vdsim/knowledge/paths.py#L30) | Funktion | – |
| [`rel(path, root)`](../../../vdsim/knowledge/paths.py#L34) | Funktion | repository-relative POSIX path (stable across machines -> deterministic output) |
| [`cache_dir(name)`](../../../vdsim/knowledge/paths.py#L43) | Funktion | per-user cache folder (VDSIM_CACHE_DIR overrides, e.g. |

### `vdsim.knowledge.references`

| Name | Art | Beschreibung |
|---|---|---|
| [`Issue`](../../../vdsim/knowledge/references.py#L60) | Klasse | – |
| [`Reference`](../../../vdsim/knowledge/references.py#L72) | Klasse | – |
| [`ReferenceDB`](../../../vdsim/knowledge/references.py#L285) | Klasse | – |
| [`last_name(author)`](../../../vdsim/knowledge/references.py#L236) | Funktion | – |
| [`abbreviate(author)`](../../../vdsim/knowledge/references.py#L252) | Funktion | "Moritz Werling" -> "Werling, M."; organizations (no blank) stay unchanged |
| [`bibtex_type(ref)`](../../../vdsim/knowledge/references.py#L265) | Funktion | – |
| [`validate_reference(ref)`](../../../vdsim/knowledge/references.py#L500) | Funktion | – |
| [`parse_citations(text)`](../../../vdsim/knowledge/references.py#L525) | Funktion | "[@werling2011, Abschn. |
