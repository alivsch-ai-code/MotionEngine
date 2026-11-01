# Sprung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [runtime](../index.md) · `node/step` · Version 1.0.0

**Sprungfunktion: Anfangswert für t < t_step, sonst Endwert.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `node` |
| Name | `step` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.runtime.blocks.Step`](../../../../vdsim/runtime/blocks.py#L66) |
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
| `t_step` | Sprungzeit | s | 1 | 0 | – |
| `initial` | Anfangswert | – | 0 | – | – |
| `final` | Endwert | – | 1 | – | – |

## Verwendung

Konfigurationen: [configs/graphs/examples/integrator_regelkreis.json](../../../../configs/graphs/examples/integrator_regelkreis.json), [configs/graphs/examples/pt1_sprungantwort.json](../../../../configs/graphs/examples/pt1_sprungantwort.json)
