# Verzögerung (z⁻¹)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/unit_delay` · Version 1.0.0

**Verzögert das Eingangssignal um einen Abtastschritt: y_k = u_{k-1}.**

## Zweck

Bricht algebraische Schleifen auf (kein Durchgriff).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `unit_delay` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.UnitDelay`](../../../../vdsim/runtime/blocks.py#L320) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | nein |

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

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `initial` | Anfangswert | – | 0 | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_graph.py](../../../../tests/runtime/test_runtime_graph.py)

Konfigurationen: [configs/graphs/examples/multirate_zoh.json](../../../../configs/graphs/examples/multirate_zoh.json)
