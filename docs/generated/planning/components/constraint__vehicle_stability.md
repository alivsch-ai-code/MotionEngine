# Fahrstabilität (lineares ESM)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/vehicle_stability` · Version 1.0.0

**Stationärer Schwimmwinkel und Querbeschleunigung im linearen Bereich des Einspurmodells.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `vehicle_stability` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.VehicleStability`](../../../../vdsim/planning/constraints.py#L286) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `beta_max` | Max. stationärer Schwimmwinkel (dynamischer Anteil) | rad | 0.12 | 0.01 | 0.5 |
| `ay_linear_max` | Querbeschleunigung im linearen Bereich, Anteil von μ g | - | 0.8 | 0.1 | 1 |
| `v_min` | Prüfung erst ab Geschwindigkeit | m/s | 5 | 0 | 30 |

## Theorie

$\beta_{ss} = \kappa\,(l_h - m l_v v^2/(c_h l))$; der Anteil $-m l_v v^2\kappa/(c_h l)$ ist der fahrdynamische Schwimmwinkel. Zusätzlich $|v^2\kappa| \le f\,\mu g$.

## Annahmen

- lineares Einspurmodell, stationäre Kurvenfahrt
- Achs-Schräglaufsteifigkeit = 2 x Reifen

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
