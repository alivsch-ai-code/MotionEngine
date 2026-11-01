# Begrenzung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/saturation` · Version 1.0.0

**Begrenzt u auf [lower, upper].**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `saturation` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Saturation`](../../../../vdsim/runtime/blocks.py#L240) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lower` | Untere Grenze | – | -1 | – | – |
| `upper` | Obere Grenze | – | 1 | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py), [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py)

Konfigurationen: [configs/graphs/examples/integrator_regelkreis.json](../../../../configs/graphs/examples/integrator_regelkreis.json)
