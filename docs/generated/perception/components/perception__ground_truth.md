# Ground Truth (ungestört)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [perception](../index.md) · `perception/ground_truth` · Version 1.0.0

**Gibt die Objekte der Szenario-Engine und den wahren Eigenzustand unverändert weiter.**

## Zweck

Referenz für die Entwicklung von Prädiktion, Verhalten und Planung ohne Wahrnehmungsfehler.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `perception` |
| Name | `ground_truth` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.perception.sensor.GroundTruthPerception`](../../../../vdsim/perception/sensor.py#L175) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `world` | `WorldState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego_estimate` | `EgoState` | – | geschätzter Eigenzustand | – |
| `objects` | `ObjectList` | – | – | – |

## Parameter

_Keine Parameter._

## Verfahren

[Sensor model](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Validierung

- tests/perception/test_perception_sensor.py

## Verwendung

Tests: [tests/perception/test_perception_sensor.py](../../../../tests/perception/test_perception_sensor.py)
