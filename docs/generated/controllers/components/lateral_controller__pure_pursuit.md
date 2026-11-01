# Pure Pursuit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `lateral_controller/pure_pursuit` · klassische Registry

**Geometrischer Pure-Pursuit-Regler mit Hinterachs-Referenz und geschwindigkeitsabhängiger Vorausschau.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `lateral_controller` |
| Name | `pure_pursuit` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.pure_pursuit.PurePursuitController`](../../../../vdsim/controllers/pure_pursuit.py#L11) |
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
| `lookahead_gain` | Vorausschauzeit (l_d = k v) | s | 0.6 | – | – |
| `lookahead_min` | minimale Vorausschaudistanz | m | 4 | – | – |

## Verfahren

[Pure Pursuit](../theory.md#pure_pursuit)

## Einschränkungen

- Schneidet Kurven bei großer Vorausschau
- kein Schwimmwinkel berücksichtigt

## Quellen

[Coulter (1992)](../../references.md#coulter1992), [Snider (2009)](../../references.md#snider2009)
