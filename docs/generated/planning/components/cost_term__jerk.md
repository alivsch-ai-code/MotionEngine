# Ruck (konsistent)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/jerk` · Version 1.0.0

**Ruckintegral ∫½u² dt des Optimalsteuerproblems (3.4), geschlossen ausgewertet.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `jerk` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.JerkCost`](../../../../vdsim/planning/cost.py#L86) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_lat` | Gewicht Querruck d(t)  ∫½ d⃛² dt | - | 1 | 0 | – |
| `k_arc` | Gewicht Querruck d(s)  ∫½ d‴² ds | - | 1000 | 0 | – |
| `k_lon` | Gewicht Längsruck ∫½ s⃛² dt | - | 1 | 0 | – |

## Verfahren

[Ruckintegral in geschlossener Form](../theory.md#jerk_integral)

## Umgesetzte Gleichungen

- `werling2011:(3.4)`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
