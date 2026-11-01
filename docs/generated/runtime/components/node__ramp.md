# Rampe

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/ramp` · Version 1.0.0

**Rampe: y = y0 + m (t - t_start) ab t_start.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `ramp` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Ramp`](../../../../vdsim/runtime/blocks.py#L105) |
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
| `slope` | Steigung | 1/s | 1 | – | – |
| `t_start` | Startzeit | s | 0 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)
