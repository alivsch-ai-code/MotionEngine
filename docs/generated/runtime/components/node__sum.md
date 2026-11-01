# Summe

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/sum` · Version 1.0.0

**Summe der Eingänge mit Vorzeichen aus dem Parameter 'signs'.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `sum` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Sum`](../../../../vdsim/runtime/blocks.py#L179) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u1` | `float` | – | – | – |
| `u2` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `signs` | Vorzeichen (z. B. '+-') | – | ++ | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py), [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py)

Konfigurationen: [configs/graphs/examples/integrator_regelkreis.json](../../../../configs/graphs/examples/integrator_regelkreis.json)
