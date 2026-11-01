# prediction – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.prediction` gibt es noch keine handgeschriebene Dokumentation (`vdsim/prediction/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init prediction`


## Konfigurationsmöglichkeiten (Paketdoku)

_Keine Einträge in module.yaml._

## Parameter von [Konstante Beschleunigung (Frenet, Werling 3.5.2)](components/predictor__constant_acceleration.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Prädiktionshorizont | s | 6 | 0.1 | 20 |
| `dt` | Zeitschritt | s | 0.1 | 0.01 | 1 |
| `v_max` | max. prädizierte Geschwindigkeit | m/s | 70 | 1 | 100 |
| `max_heading_error_deg` | max. Winkel zur Spur für Frenet-Prädiktion | ° | 60 | 0 | 90 |
| `use_lanes` | spurbasierte Prädiktion (falls Spur bekannt) | – | True | – | – |
| `chain_length` | Länge der Spurfolge | m | 400 | 50 | 3000 |

## Parameter von [Konstante Geschwindigkeit (kartesisch)](components/predictor__constant_velocity.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Prädiktionshorizont | s | 6 | 0.1 | 20 |
| `dt` | Zeitschritt | s | 0.1 | 0.01 | 1 |
| `v_max` | max. prädizierte Geschwindigkeit | m/s | 70 | 1 | 100 |
| `max_heading_error_deg` | max. Winkel zur Spur für Frenet-Prädiktion | ° | 60 | 0 | 90 |
| `use_lanes` | spurbasierte Prädiktion (falls Spur bekannt) | – | True | – | – |
| `chain_length` | Länge der Spurfolge | m | 400 | 50 | 3000 |
| `use_yaw_rate` | konstante Gierrate (CTRV) | – | False | – | – |

## Parameter von [Spurfolge mit Querabsicht](components/predictor__lane_following.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Prädiktionshorizont | s | 6 | 0.1 | 20 |
| `dt` | Zeitschritt | s | 0.1 | 0.01 | 1 |
| `v_max` | max. prädizierte Geschwindigkeit | m/s | 70 | 1 | 100 |
| `max_heading_error_deg` | max. Winkel zur Spur für Frenet-Prädiktion | ° | 60 | 0 | 90 |
| `use_lanes` | spurbasierte Prädiktion (falls Spur bekannt) | – | True | – | – |
| `chain_length` | Länge der Spurfolge | m | 400 | 50 | 3000 |
| `tau_lateral` | Zeitkonstante Querbewegung | s | 1.2 | 0.1 | 10 |
| `lateral_intent_speed` | Quergeschwindigkeit für Spurwechselabsicht | m/s | 0.35 | 0 | 3 |
| `use_acceleration` | Längsbeschleunigung berücksichtigen | – | False | – | – |

## Parametersatz `PredictorParams` (`vdsim.prediction.predictors`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Prädiktionshorizont | s | 6 | 0.1 | 20 |
| `dt` | Zeitschritt | s | 0.1 | 0.01 | 1 |
| `v_max` | max. prädizierte Geschwindigkeit | m/s | 70 | 1 | 100 |
| `max_heading_error_deg` | max. Winkel zur Spur für Frenet-Prädiktion | ° | 60 | 0 | 90 |
| `use_lanes` | spurbasierte Prädiktion (falls Spur bekannt) | – | True | – | – |
| `chain_length` | Länge der Spurfolge | m | 400 | 50 | 3000 |

## Parametersatz `LaneFollowingParams` (`vdsim.prediction.predictors`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Prädiktionshorizont | s | 6 | 0.1 | 20 |
| `dt` | Zeitschritt | s | 0.1 | 0.01 | 1 |
| `v_max` | max. prädizierte Geschwindigkeit | m/s | 70 | 1 | 100 |
| `max_heading_error_deg` | max. Winkel zur Spur für Frenet-Prädiktion | ° | 60 | 0 | 90 |
| `use_lanes` | spurbasierte Prädiktion (falls Spur bekannt) | – | True | – | – |
| `chain_length` | Länge der Spurfolge | m | 400 | 50 | 3000 |
| `tau_lateral` | Zeitkonstante Querbewegung | s | 1.2 | 0.1 | 10 |
| `lateral_intent_speed` | Quergeschwindigkeit für Spurwechselabsicht | m/s | 0.35 | 0 | 3 |
| `use_acceleration` | Längsbeschleunigung berücksichtigen | – | False | – | – |

## Parametersatz `ConstantVelocityParams` (`vdsim.prediction.predictors`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Prädiktionshorizont | s | 6 | 0.1 | 20 |
| `dt` | Zeitschritt | s | 0.1 | 0.01 | 1 |
| `v_max` | max. prädizierte Geschwindigkeit | m/s | 70 | 1 | 100 |
| `max_heading_error_deg` | max. Winkel zur Spur für Frenet-Prädiktion | ° | 60 | 0 | 90 |
| `use_lanes` | spurbasierte Prädiktion (falls Spur bekannt) | – | True | – | – |
| `chain_length` | Länge der Spurfolge | m | 400 | 50 | 3000 |
| `use_yaw_rate` | konstante Gierrate (CTRV) | – | False | – | – |
