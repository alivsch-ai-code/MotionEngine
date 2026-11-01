# Energieeffizienz

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/energy` · Version 1.0.0

**Traktionsenergie je Masse ∫ ṡ (s̈ + c_r g + ρ c_w A ṡ²/(2m)) dt mit Rekuperation.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `energy` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.EnergyCost`](../../../../vdsim/planning/cost.py#L219) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht Traktionsenergie je Masse | s²/m² | 0 | 0 | – |
| `regen_efficiency` | Rückgewinnungsgrad beim Verzögern | - | 0 | 0 | 1 |

## Annahmen

- Bahngeschwindigkeit ≈ ṡ
- ebene Straße

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
