# Mux

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/mux` · Version 1.0.0

**Fasst n Skalare zu einem Vektor zusammen.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `mux` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Mux`](../../../../vdsim/runtime/blocks.py#L279) |
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
| `y` | `Vector` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n` | Anzahl Eingänge | – | 2 | 1 | 64 |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)
