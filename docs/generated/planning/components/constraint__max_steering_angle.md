# Max. Lenkwinkel

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/max_steering_angle` · Version 1.0.0

**Kinematischer Lenkwinkel δ = atan(lκ) innerhalb des Lenkanschlags.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `max_steering_angle` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.MaxSteeringAngle`](../../../../vdsim/planning/constraints.py#L167) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `delta_max` | Max. Radlenkwinkel (≤ 0: aus Fahrzeug) | rad | -1 | -1 | 1.2 |

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
