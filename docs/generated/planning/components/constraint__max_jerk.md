# Max. Ruck

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/max_jerk` · Version 1.0.0

**Begrenzt den Bahnruck ȧ (Differenzenquotient auf dem Prüfraster).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `max_jerk` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.MaxJerk`](../../../../vdsim/planning/constraints.py#L124) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `j_max` | Max. Längsruck \|ȧ\| | m/s³ | 25 | 1 | 200 |

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
