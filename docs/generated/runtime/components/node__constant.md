# Konstante

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/constant` · Version 1.0.0

**Konstanter Wert y = c.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `constant` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Constant`](../../../../vdsim/runtime/blocks.py#L48) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `value` | Wert | – | 1 | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_custom_python.py](../../../../tests/runtime/test_runtime_custom_python.py), [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py), [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py), [tests/runtime/test_runtime_versioning.py](../../../../tests/runtime/test_runtime_versioning.py)
