# Max. Querbeschleunigung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/max_lateral_acceleration` · Version 1.0.0

**Begrenzt die Querbeschleunigung v²κ entlang der Trajektorie.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `max_lateral_acceleration` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.MaxLateralAcceleration`](../../../../vdsim/planning/constraints.py#L88) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `a_max` | Max. Querbeschleunigung \|v²κ\| | m/s² | 6 | 0.5 | 15 |

## Umgesetzte Gleichungen

- `werling2011:(A.2)`
- `werling2011:(A.5)`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
