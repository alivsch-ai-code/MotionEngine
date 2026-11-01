# Fahrzeugumriss im Korridor

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/vehicle_envelope` · Version 1.0.0

**Alle vier Fahrzeugecken liegen im Korridor d_min ≤ d ≤ d_max.**

## Zweck

Box-Restriktion der Verhaltensebene für d(t) (Werling 5.3, Fußnote 8).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `vehicle_envelope` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.VehicleEnvelope`](../../../../vdsim/planning/constraints.py#L250) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `margin` | Zusätzlicher Abstand zum Korridorrand | m | 0 | 0 | 2 |

## Annahmen

- Ecken in Frenet-Koordinaten mit der Ausrichtung relativ zur Straße genähert (Krümmung der Referenzkurve über die Fahrzeuglänge vernachlässigt)

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
