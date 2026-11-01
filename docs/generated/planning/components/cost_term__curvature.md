# Krümmung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/curvature` · Version 1.0.0

**Geometrische Krümmungsenergie ∫ κ² dℓ = ∫ κ² v dt.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `curvature` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.CurvatureCost`](../../../../vdsim/planning/cost.py#L260) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ κ² dℓ | m | 0 | 0 | – |

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
