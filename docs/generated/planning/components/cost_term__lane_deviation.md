# Spurabweichung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/lane_deviation` · Version 1.0.0

**Integrierte Querabweichung zur Referenz über den Prüfhorizont (bzw. die Prüfstrecke).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `lane_deviation` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.LaneDeviationCost`](../../../../vdsim/planning/cost.py#L181) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ (d − d_ref)² dt | 1/(m² s) | 0 | 0 | – |
| `relative_to_d_ref` | Abweichung zu d_ref (sonst zur Spurmitte d = 0) | – | True | – | – |

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
