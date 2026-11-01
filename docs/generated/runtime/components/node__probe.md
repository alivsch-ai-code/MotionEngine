# Messpunkt

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/probe` · Version 1.0.0

**Durchschleifender Messpunkt: y = u, Skalare erscheinen als Signal 'value'.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `probe` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.ProbeBlock`](../../../../vdsim/runtime/blocks.py#L477) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Any` | – | – | – |

## Parameter

_Keine Parameter._

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)
