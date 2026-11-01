# Beschleunigung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/acceleration` · Version 1.0.0

**Quadratintegral der straßenrelativen Beschleunigungen über den Prüfhorizont.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `acceleration` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.AccelerationCost`](../../../../vdsim/planning/cost.py#L159) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight_lat` | Gewicht ∫ d̈² dt (bzw. ∫ d''² ds) | s³/m² | 0 | 0 | – |
| `weight_lon` | Gewicht ∫ s̈² dt | s³/m² | 0 | 0 | – |

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
