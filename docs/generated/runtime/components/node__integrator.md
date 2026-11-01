# Integrator

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/integrator` · Version 1.0.0

**Zeitdiskreter Integrator (explizites Euler-Verfahren) mit Begrenzung.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `integrator` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Integrator`](../../../../vdsim/runtime/blocks.py#L350) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | nein |

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
| `k` | Verstärkung | – | 1 | – | – |
| `initial` | Anfangswert | – | 0 | – | – |
| `lower` | Untere Grenze | – | -inf | – | – |
| `upper` | Obere Grenze | – | inf | – | – |

## Theorie

$y_{k+1} = \mathrm{sat}(y_k + K\,T_s\,u_k)$

## Verfahren

[Diskrete Grundblöcke](../theory.md#discrete_blocks)

## Verwendung

Tests: [tests/runtime/test_runtime_executor.py](../../../../tests/runtime/test_runtime_executor.py)

Konfigurationen: [configs/graphs/examples/integrator_regelkreis.json](../../../../configs/graphs/examples/integrator_regelkreis.json)
