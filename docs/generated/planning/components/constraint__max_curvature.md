# Max. Krümmung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/max_curvature` · Version 1.0.0

**Minimaler Kurvenradius (kinematische Restriktion).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `max_curvature` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.MaxCurvature`](../../../../vdsim/planning/constraints.py#L142) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `kappa_max` | Max. Krümmung (≤ 0: aus Lenkanschlag und Radstand) | 1/m | -1 | -1 | 2 |
| `auto_factor` | Faktor auf tan(δ_max)/l (automatisch) | - | 0.95 | 0.1 | 1 |

## Umgesetzte Gleichungen

- `werling2011:(A.5)`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
