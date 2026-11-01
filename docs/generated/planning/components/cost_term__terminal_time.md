# Endzeit k_τ τ (konsistent)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `cost_term/terminal_time` · Version 1.0.0

**Endkosten k_τ τ (bzw. k_s [s(τ)−s(0)] im d(s)-Modus) gegen langsames Annähern.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `cost_term` |
| Name | `terminal_time` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.cost.TerminalTimeCost`](../../../../vdsim/planning/cost.py#L109) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_tau_lat` | k_τ quer (d(t)) | 1/s | 5 | 0 | – |
| `k_s_arc` | k_s quer (d(s)): k_s [s(τ) − s(0)] | 1/m | 8 | 0 | – |
| `k_tau_lon` | k_τ längs | 1/s | 2 | 0 | – |

## Umgesetzte Gleichungen

- `werling2011:(3.10)`
- `werling2011:Tab. 3.1`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_analysis.py](../../../../tests/planning/test_planning_analysis.py), [tests/planning/test_planning_polynomials.py](../../../../tests/planning/test_planning_polynomials.py)

Beispiele: [examples/custom_nodes/python/my_cost_function.py](../../../../examples/custom_nodes/python/my_cost_function.py)
