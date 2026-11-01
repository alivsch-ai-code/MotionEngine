# Ratenbegrenzer

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/rate_limiter` · Version 1.0.0

**Begrenzt die Änderungsrate des Signals.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `rate_limiter` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.RateLimiter`](../../../../vdsim/runtime/blocks.py#L414) |
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
| `rising` | Max. Anstiegsrate | 1/s | 1 | 0 | – |
| `falling` | Max. Abfallrate | 1/s | 1 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |

## Verwendung

Konfigurationen: [configs/graphs/examples/multirate_zoh.json](../../../../configs/graphs/examples/multirate_zoh.json)
