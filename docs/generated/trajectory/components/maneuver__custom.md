# Kundenspezifischer Testzyklus

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [trajectory](../index.md) · `maneuver/custom` · klassische Registry

**Segmentliste als JSON: [["straight", L, v_kmh], ["arc", R, Winkel°, v_kmh], ["clothoid", L, kappa_end, v_kmh], ["offset", L, Versatz, v_kmh]]**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `maneuver` |
| Name | `custom` |
| Versionen | legacy |
| Implementierung | [`vdsim.trajectory.trajectory_generator.custom`](../../../../vdsim/trajectory/trajectory_generator.py#L462) |
| Schnittstelle | – |
| Sprache | python |

## Ports

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `segments` | Segmente (JSON) | – | [["straight", 100, 50], ["turn", 30, 90, 40], ["straight"… | – | – |
| `ay_max` | Max. Querbeschleunigung | m/s² | 4 | – | – |

## Verwendung

Tests: [tests/test_trajectory.py](../../../../tests/test_trajectory.py)

Konfigurationen: [configs/scenarios/testzyklus_kunde.json](../../../../configs/scenarios/testzyklus_kunde.json)
