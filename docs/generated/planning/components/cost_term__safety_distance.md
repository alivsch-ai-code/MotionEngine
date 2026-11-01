# Sicherheitsabstand

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/safety_distance` · Version 1.0.0

**Weiche Abstandskosten zusätzlich zur harten Kollisionsrestriktion.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `safety_distance` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.SafetyDistanceCost`](../../../../vdsim/planning/cost.py#L278) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ max(0, d_soll − Abstand)² dt | 1/(m² s) | 0 | 0 | – |
| `distance` | Weicher Wunschabstand zu Objekten | m | 2 | 0 | 20 |

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
