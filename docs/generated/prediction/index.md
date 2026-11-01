# prediction

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.prediction` gibt es noch keine handgeschriebene Dokumentation (`vdsim/prediction/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init prediction`


`vdsim.prediction` · Quellcode: [vdsim/prediction/](../../../vdsim/prediction)

## Übersicht

Paket-Docstring:

```text
Prediction layer: constant acceleration in Frenet coordinates (Werling 3.5.2), constant velocity, lane following.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 2 |
| Komponenten | 3 |
| Verfahren/Konzepte | 5 |
| @trace-Einträge | 2 |
| Tests | 2 |
| Beispiele | 0 |

## Architektur

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.prediction`](../../../vdsim/prediction/__init__.py) | 13 | – | Prediction layer: constant acceleration in Frenet coordinates (Werling 3.5.2), constant velocity, lane following. |
| [`vdsim.prediction.predictors`](../../../vdsim/prediction/predictors.py) | 244 | PredictorParams, LaneFollowingParams, ConstantVelocityParams, _BasePredictor, ConstantAccelerationPredictor, ConstantVelocityPredictor | Motion prediction of the perceived objects (absolute time base t0 ... |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [geometry](../geometry/index.md)
- genutzt von: –
- externe Bibliotheken: `__future__`, `dataclasses`, `numpy`

## Designentscheidungen

_Noch nicht dokumentiert._

## Implementierung

_Keine Implementierungshinweise in module.yaml._

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`predictor/constant_acceleration`](components/predictor__constant_acceleration.md) | Konstante Beschleunigung (Frenet, Werling 3.5.2) | 1.0.0 | Prädiziert Objekte mit konstanter Beschleunigung entlang ihrer Spur in Frenet-Koordinaten. |
| [`predictor/constant_velocity`](components/predictor__constant_velocity.md) | Konstante Geschwindigkeit (kartesisch) | 1.0.0 | Geradlinige Prädiktion mit konstanter Geschwindigkeit (optional konstanter Gierrate). |
| [`predictor/lane_following`](components/predictor__lane_following.md) | Spurfolge mit Querabsicht | 1.0.0 | Konstante Geschwindigkeit entlang der Spurfolge, Querablage konvergiert zur Zielspurmitte. |

### Verfahren und Konzepte

- [Ca prediction](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Cv prediction](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Frenet frame](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Lane following prediction](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Lateral intent](../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Erweiterungspunkte

_Keine angegeben._
