# ad – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.ad` gibt es noch keine handgeschriebene Dokumentation (`vdsim/ad/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init ad`


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.ad`

| Name | Art | Beschreibung |
|---|---|---|
| [`run_scenario(*args, **kwargs)`](../../../vdsim/ad/__init__.py#L7) | Funktion | – |

### `vdsim.ad.results`

| Name | Art | Beschreibung |
|---|---|---|
| [`ADResult`](../../../vdsim/ad/results.py#L43) | Klasse | – |

### `vdsim.ad.runner`

| Name | Art | Beschreibung |
|---|---|---|
| [`run_scenario(scenario, stack, seed, duration, scenario_params, record_snapshots, vehicle, graph, progress, stop_on_collision, stop_on_goal, max_wall_time, name)`](../../../vdsim/ad/runner.py#L227) | Funktion | – |

### `vdsim.ad.stack`

| Name | Art | Beschreibung |
|---|---|---|
| [`merge_stack(*stacks)`](../../../vdsim/ad/stack.py#L79) | Funktion | later stacks override earlier ones; params are merged recursively |
| [`build_graph(stack, name, base_dt, extra_nodes, extra_connections)`](../../../vdsim/ad/stack.py#L109) | Funktion | stack dict -> graph dict (contracts.md section 4) |
