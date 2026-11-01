# Produkt

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/product` · Version 1.0.0

**Produkt bzw. Quotient der Eingänge ('*' multipliziert, '/' dividiert).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `product` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Product`](../../../../vdsim/runtime/blocks.py#L209) |
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
| `ops` | Operationen (z. B. '*/') | – | ** | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py)
