# Kammscher Kreis

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/tire_force` · Version 1.0.0

**Kammscher Kreis √(a² + (v²κ)²) ≤ η μ g.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `tire_force` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.TireForceConstraint`](../../../../vdsim/planning/constraints.py#L226) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `eta` | Ausnutzungsgrad η des Kammschen Kreises | - | 0.9 | 0.1 | 1 |
| `mu` | Reibwert μ (≤ 0: aus Reifenparametern) | - | -1 | -1 | 2 |

## Umgesetzte Gleichungen

- `werling2011:(A.6)`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
