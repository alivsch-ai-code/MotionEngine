# Standardwert

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/typed_default` · Version 1.0.0

**Liefert den Standardwert eines Datentyps (z. B. leere ObjectList).**

## Zweck

Platzhalter für noch nicht vorhandene Ebenen beim Aufbau eines Graphen.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `typed_default` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.TypedDefault`](../../../../vdsim/runtime/blocks.py#L132) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `Any` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `type_name` | Datentyp | – | ObjectList | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py), [tests/runtime/test_runtime_native.py](../../../../tests/runtime/test_runtime_native.py)

Konfigurationen: [configs/graphs/examples/custom_nodes_kette.json](../../../../configs/graphs/examples/custom_nodes_kette.json)
