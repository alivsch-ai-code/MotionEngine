# Spurhalteassistent (LKA)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `lateral_controller/lane_keeping` · klassische Registry

**Spurhalteassistent mit unaufmerksamem Fahrermodell (Pure Pursuit plus Lenkdrift) und begrenztem Lenkeingriff.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `lateral_controller` |
| Name | `lane_keeping` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.lane_keeping.LaneKeepingAssist`](../../../../vdsim/controllers/lane_keeping.py#L17) |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lane_width` | – | m | 3.75 | – | – |
| `activation_margin` | Abstand zur Markierung | m | 0.3 | – | – |
| `drift_start` | Beginn der Unaufmerksamkeit | s | 2 | – | – |
| `drift_bias_deg` | Lenkdrift des Fahrers | ° | 0.4 | – | – |
| `gain` | Verstärkung der Querablage | - | 0.6 | – | – |
| `heading_gain` | Verstärkung des Kurswinkelfehlers | - | 1.5 | – | – |
| `max_overlay_deg` | maximaler Zusatzlenkwinkel | ° | 3 | – | – |
| `enabled` | Assistent aktiv | – | True | – | – |

## Verfahren

[Spurhalteassistent mit Fahrermodell](../theory.md#lane_keeping_assist), [Pure Pursuit](../theory.md#pure_pursuit)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)

Konfigurationen: [configs/scenarios/autobahn_spurhalteassistent.json](../../../../configs/scenarios/autobahn_spurhalteassistent.json)
