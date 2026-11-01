# Tiefpass (PT1)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/lowpass` · Version 1.0.0

**PT1-Glied, exakt diskretisiert (Sprunginvarianz).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `lowpass` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.LowPass`](../../../../vdsim/runtime/blocks.py#L383) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `float` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `y` | `float` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `T` | Zeitkonstante | s | 0.1 | 0 | – |
| `K` | Verstärkung | – | 1 | – | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Theorie

$y_k = a\,y_{k-1} + (1-a)\,K\,u_k$, $a = e^{-T_s/T}$

## Verfahren

[Diskrete Grundblöcke](../theory.md#discrete_blocks)

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)

Konfigurationen: [configs/graphs/examples/pt1_sprungantwort.json](../../../../configs/graphs/examples/pt1_sprungantwort.json)
