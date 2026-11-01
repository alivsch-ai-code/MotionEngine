# Max. Gierrate

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/max_yaw_rate` · Version 1.0.0

**Gierrate ψ̇ = vκ des Referenzpunkts begrenzt.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `max_yaw_rate` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.MaxYawRate`](../../../../vdsim/planning/constraints.py#L209) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `r_max` | Max. Gierrate \|vκ\| | rad/s | 1.2 | 0.05 | 5 |

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
