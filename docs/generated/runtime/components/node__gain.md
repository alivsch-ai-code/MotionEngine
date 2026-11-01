# Verstärkung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/gain` · Version 1.0.0

**y = k · u (Skalar oder Vektor).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `gain` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Gain`](../../../../vdsim/runtime/blocks.py#L161) |
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
| `k` | Verstärkung | – | 1 | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py), [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py), [tests/runtime/test_runtime_versioning.py](../../../../tests/runtime/test_runtime_versioning.py)

Konfigurationen: [configs/graphs/examples/integrator_regelkreis.json](../../../../configs/graphs/examples/integrator_regelkreis.json), [configs/graphs/examples/multirate_zoh.json](../../../../configs/graphs/examples/multirate_zoh.json)
