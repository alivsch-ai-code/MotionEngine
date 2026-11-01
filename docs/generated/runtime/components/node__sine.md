# Sinus

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/sine` · Version 1.0.0

**y = A sin(2π f t + φ) + Offset.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `sine` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Sine`](../../../../vdsim/runtime/blocks.py#L86) |
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
| `amplitude` | Amplitude | – | 1 | – | – |
| `frequency` | Frequenz | Hz | 1 | 0 | – |
| `phase` | Phase | rad | 0 | – | – |
| `offset` | Offset | – | 0 | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)

Konfigurationen: [configs/graphs/examples/multirate_zoh.json](../../../../configs/graphs/examples/multirate_zoh.json)
