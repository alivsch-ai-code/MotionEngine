# Max. Lenkwinkelgeschwindigkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/max_steering_velocity` · Version 1.0.0

**δ̇ = l κ̇ / (1 + (lκ)²) begrenzt (Lenkaktor-Dynamik).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `max_steering_velocity` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.MaxSteeringVelocity`](../../../../vdsim/planning/constraints.py#L191) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `rate_max` | Max. Radlenkwinkelgeschwindigkeit | rad/s | 0.7 | 0.05 | 5 |

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
