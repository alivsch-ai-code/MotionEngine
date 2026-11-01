# perception

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.perception` gibt es noch keine handgeschriebene Dokumentation (`vdsim/perception/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init perception`


`vdsim.perception` · Quellcode: [vdsim/perception/](../../../vdsim/perception)

## Übersicht

Paket-Docstring:

```text
Perception layer: object sensor model (range, field of view, occlusion, noise, latency) and ground truth.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 2 |
| Komponenten | 2 |
| Verfahren/Konzepte | 1 |
| @trace-Einträge | 1 |
| Tests | 1 |
| Beispiele | 0 |

## Architektur

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.perception`](../../../vdsim/perception/__init__.py) | 10 | – | Perception layer: object sensor model (range, field of view, occlusion, noise, latency) and ground truth. |
| [`vdsim.perception.sensor`](../../../vdsim/perception/sensor.py) | 191 | ObjectSensorParams, ObjectSensor, GroundTruthPerception | Object sensor model and ground-truth perception. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [geometry](../geometry/index.md), [world](../world/index.md)
- genutzt von: –
- externe Bibliotheken: `__future__`, `collections`, `copy`, `dataclasses`, `numpy`

## Designentscheidungen

_Noch nicht dokumentiert._

## Implementierung

_Keine Implementierungshinweise in module.yaml._

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`perception/ground_truth`](components/perception__ground_truth.md) | Ground Truth (ungestört) | 1.0.0 | Gibt die Objekte der Szenario-Engine und den wahren Eigenzustand unverändert weiter. |
| [`perception/object_sensor`](components/perception__object_sensor.md) | Objektsensor (Reichweite, Rauschen, Latenz) | 1.0.0 | Erzeugt aus der Ground Truth eine gestörte Objektliste und eine Eigenzustandsschätzung. |

### Verfahren und Konzepte

- [Sensor model](../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Erweiterungspunkte

_Keine angegeben._
