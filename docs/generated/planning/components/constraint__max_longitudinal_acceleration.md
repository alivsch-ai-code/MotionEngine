# Max. Längsbeschleunigung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/max_longitudinal_acceleration` · Version 1.0.0

**Getrennte Grenzen für Beschleunigen und Verzögern.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `max_longitudinal_acceleration` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.MaxLongitudinalAcceleration`](../../../../vdsim/planning/constraints.py#L107) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `a_accel_max` | Max. Beschleunigung | m/s² | 3 | 0.2 | 10 |
| `a_decel_max` | Max. Verzögerung | m/s² | 8 | 0.5 | 12 |

## Umgesetzte Gleichungen

- `werling2011:(A.6)`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
