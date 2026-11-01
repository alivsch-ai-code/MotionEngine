# api – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.api` gibt es noch keine handgeschriebene Dokumentation (`vdsim/api/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init api`


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.api`

| Name | Art | Beschreibung |
|---|---|---|
| [`info()`](../../../vdsim/api/__init__.py#L14) | Funktion | – |
| [`list_components(kind)`](../../../vdsim/api/__init__.py#L20) | Funktion | – |
| [`describe_component(spec)`](../../../vdsim/api/__init__.py#L25) | Funktion | – |
| [`create_component(spec, params)`](../../../vdsim/api/__init__.py#L30) | Funktion | – |
| [`list_scenarios()`](../../../vdsim/api/__init__.py#L36) | Funktion | – |
| [`default_stack()`](../../../vdsim/api/__init__.py#L41) | Funktion | – |
| [`build_graph(stack)`](../../../vdsim/api/__init__.py#L47) | Funktion | – |
| [`run(scenario, stack, seed, duration, scenario_params, snapshots, progress)`](../../../vdsim/api/__init__.py#L52) | Funktion | – |
| [`run_batch(jobs, workers)`](../../../vdsim/api/__init__.py#L58) | Funktion | – |
| [`sweep(base_job, grid, workers)`](../../../vdsim/api/__init__.py#L63) | Funktion | – |
| [`monte_carlo(base_job, distributions, n, seed, workers)`](../../../vdsim/api/__init__.py#L68) | Funktion | – |
| [`compare(base_job, layer, variants, workers)`](../../../vdsim/api/__init__.py#L73) | Funktion | – |
| [`benchmark(scenario, stack, repeats, duration)`](../../../vdsim/api/__init__.py#L78) | Funktion | – |
| [`load_graph(path)`](../../../vdsim/api/__init__.py#L84) | Funktion | – |
| [`validate_graph(graph_dict)`](../../../vdsim/api/__init__.py#L89) | Funktion | – |
| [`matlab_analyze(path_or_source)`](../../../vdsim/api/__init__.py#L96) | Funktion | – |
| [`matlab_convert(path_or_source, target)`](../../../vdsim/api/__init__.py#L101) | Funktion | – |
| [`create_custom_node(language, name, layer, dest)`](../../../vdsim/api/__init__.py#L107) | Funktion | – |
| [`references()`](../../../vdsim/api/__init__.py#L113) | Funktion | – |
| [`knowledge_graph()`](../../../vdsim/api/__init__.py#L118) | Funktion | – |
| [`build_docs(out_dir)`](../../../vdsim/api/__init__.py#L123) | Funktion | – |

### `vdsim.api.server`

| Name | Art | Beschreibung |
|---|---|---|
| [`JobStore`](../../../vdsim/api/server.py#L46) | Klasse | – |
| [`openapi_spec()`](../../../vdsim/api/server.py#L84) | Funktion | – |
| [`make_handler(store, token)`](../../../vdsim/api/server.py#L115) | Funktion | – |
| [`serve(host, port, token, workers)`](../../../vdsim/api/server.py#L218) | Funktion | – |
| [`main(argv)`](../../../vdsim/api/server.py#L224) | Funktion | – |
