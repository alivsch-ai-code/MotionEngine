# Pure Pursuit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/pure_pursuit` · Version 1.0.0

**Geometrischer Querregler: Kreisbogen von der Hinterachse zu einem Zielpunkt auf der Bahn.**

## Zweck

Einfacher, robuster Vergleichsregler (Snider 2009).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `pure_pursuit` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_lateral.PurePursuit`](../../../../vdsim/stabilization/classic_lateral.py#L163) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `lookahead_gain` | Vorausschauzeit k (L_d = k v) | s | 0.8 | 0 | – |
| `lookahead_min` | minimale Vorausschau | m | 4 | 0.5 | – |

## Theorie

$\delta=\arctan(2l\sin\alpha/L_d)$, $L_d=\max(L_{min},kv)$, $\alpha$ Winkel zum Zielpunkt.

## Verfahren

[Pure Pursuit](../../controllers/theory.md#pure_pursuit)

## Annahmen

- Kinematisches Fahrzeug, Vorwärtsfahrt

## Einschränkungen

- Schneidet Kurven, stationärer Querfehler bei großer Vorausschau
- Keine Rückwärtsfahrt

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012), [Snider (2009)](../../references.md#snider2009)

## Expertenmodus: Herleitungen und Hinweise

Für kleine Fehler entspricht Pure Pursuit einem P-Regler auf den Querfehler mit Verstärkung $2/L_d^2$; die Stabilität folgt aus der positiven Vorausschau (Snider 2009).
