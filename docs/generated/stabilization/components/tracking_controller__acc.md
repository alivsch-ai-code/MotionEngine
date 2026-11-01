# Abstandsregeltempomat (ACC)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/acc` · Version 1.0.0

**Abstandsbasierte Längsregelung mit konstanter Zeitlücke.**

## Zweck

Vergleich der trajektorienbasierten Längsführung mit klassischem ACC ohne Planer (Werling 4.1.3: bei Trajektorienfolge implizit enthalten).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `acc` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_longitudinal.ACC`](../../../../vdsim/stabilization/classic_longitudinal.py#L136) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `objects` | `ObjectList` | – | Objekte für das Vorderfahrzeug | optional |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `time_gap` | Zeitlücke | s | 1.8 | 0 | – |
| `standstill_gap` | Abstand im Stand | m | 5 | 0 | – |
| `k_gap` | Verstärkung Abstandsfehler | 1/s² | 0.25 | 0 | – |
| `k_speed` | Verstärkung Relativgeschwindigkeit | 1/s | 0.7 | 0 | – |
| `k_v` | Verstärkung Wunschgeschwindigkeit | 1/s | 1 | 0 | – |
| `lead_gap0` | virtuelles Vorderfahrzeug: Startabstand (<0: keins) | m | -1 | – | – |
| `lead_speed` | virtuelles Vorderfahrzeug: Geschwindigkeit | m/s | 15 | 0 | – |
| `lane_width` | Halbbreite des Fahrschlauchs für Objekte | m | 2 | 0.1 | – |

## Theorie

$a=\min(a_{cruise},k_g(d-d_0-\tau v)+k_v(v_l-v))$

## Verfahren

[Acc](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Vorderfahrzeug im Fahrschlauch der Trajektorie

## Einschränkungen

- Keine Kollisionsfreiheit garantiert

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012)

## Expertenmodus: Herleitungen und Hinweise

String-Stabilität für $\tau>0$ und geeignete Verstärkungen (Rajamani Kap. 5).
