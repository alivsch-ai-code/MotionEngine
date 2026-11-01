# Komfort

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/comfort` · Version 1.0.0

**Beschleunigungsbelastung der Insassen in Weltkoordinaten (inkl. Straßenkrümmung).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `comfort` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.ComfortCost`](../../../../vdsim/planning/cost.py#L243) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `weight` | Gewicht ∫ (a_quer² + a_längs²) dt (Weltkoordinaten) | s³/m² | 0 | 0 | – |

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
