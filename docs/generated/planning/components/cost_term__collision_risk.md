# Kollisionsrisiko

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/collision_risk` · Version 1.0.0

**Gaußförmiges Risikomaß über den kleinsten Abstand zu den prädizierten Objekten.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `collision_risk` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.CollisionRiskCost`](../../../../vdsim/planning/cost.py#L299) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ exp(−Abstand²/(2σ²)) dt | 1/s | 0 | 0 | – |
| `sigma` | Unsicherheit σ der Objektposition | m | 1 | 0.05 | 10 |

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
