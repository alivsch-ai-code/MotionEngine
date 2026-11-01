# Zielerreichung ½kδ² (konsistent)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/terminal_deviation` · Version 1.0.0

**Endabweichung ½kδ δ², ½kσ σ², ½kν ν² von der Referenz (Zielerreichung).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `terminal_deviation` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.TerminalDeviationCost`](../../../../vdsim/planning/cost.py#L132) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_delta` | k_δ Endversatz quer (d(t)) | 1/m² | 200 | 0 | – |
| `k_delta_arc` | k_δ Endversatz quer (d(s)) | 1/m² | 600 | 0 | – |
| `k_sigma` | k_σ Positionsversatz (Folgen, Einfädeln, Anhalten) | 1/m² | 30 | 0 | – |
| `k_nu` | k_ν Geschwindigkeitsversatz | s²/m² | 20 | 0 | – |

## Umgesetzte Gleichungen

- `werling2011:(3.10)`
- `werling2011:Tab. 3.1`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
