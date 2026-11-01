# Uhr

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/clock` · Version 1.0.0

**Gibt die Simulationszeit aus.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `clock` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Clock`](../../../../vdsim/runtime/blocks.py#L117) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `t` | `float` | s | Simulationszeit | – |

## Parameter

_Keine Parameter._

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)

Konfigurationen: [configs/graphs/examples/multirate_zoh.json](../../../../configs/graphs/examples/multirate_zoh.json)
