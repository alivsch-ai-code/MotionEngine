# Scope

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/scope` · Version 1.0.0

**Zeichnet seine Eingänge als Zeitreihen auf (data()).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `scope` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Scope`](../../../../vdsim/runtime/blocks.py#L445) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u1` | `Any` | – | – | optional |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n` | Anzahl Eingänge | – | 1 | 1 | 16 |
| `max_samples` | Max. Abtastwerte | – | 100000 | 1 | – |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py), [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py), [tests/runtime/test_runtime_versioning.py](../../../../tests/runtime/test_runtime_versioning.py)

Konfigurationen: [configs/graphs/examples/integrator_regelkreis.json](../../../../configs/graphs/examples/integrator_regelkreis.json), [configs/graphs/examples/multirate_zoh.json](../../../../configs/graphs/examples/multirate_zoh.json), [configs/graphs/examples/pt1_sprungantwort.json](../../../../configs/graphs/examples/pt1_sprungantwort.json)
