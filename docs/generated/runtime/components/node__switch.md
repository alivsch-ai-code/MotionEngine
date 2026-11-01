# Schalter

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/switch` · Version 1.0.0

**y = u1, falls control ≥ Schwelle, sonst u2.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `switch` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Switch`](../../../../vdsim/runtime/blocks.py#L261) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `control` | `float` | – | – | – |
| `u1` | `Any` | – | – | – |
| `u2` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Any` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `threshold` | Schwelle | – | 0 | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)
