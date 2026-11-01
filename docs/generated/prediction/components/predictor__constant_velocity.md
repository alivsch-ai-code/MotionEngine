# Konstante Geschwindigkeit (kartesisch)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [prediction](../index.md) · `predictor/constant_velocity` · Version 1.0.0

**Geradlinige Prädiktion mit konstanter Geschwindigkeit (optional konstanter Gierrate).**

## Zweck

Einfache, kartenunabhängige Referenzprädiktion, z. B. für Fußgänger oder ohne Straßenkarte.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `predictor` |
| Name | `constant_velocity` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.prediction.predictors.ConstantVelocityPredictor`](../../../../vdsim/prediction/predictors.py#L174) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `objects` | `ObjectList` | – | – | – |
| `world` | `WorldState` | – | – | optional |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `prediction` | `Prediction` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `horizon` | Prädiktionshorizont | s | 6 | 0.1 | 20 |
| `dt` | Zeitschritt | s | 0.1 | 0.01 | 1 |
| `v_max` | max. prädizierte Geschwindigkeit | m/s | 70 | 1 | 100 |
| `max_heading_error_deg` | max. Winkel zur Spur für Frenet-Prädiktion | ° | 60 | 0 | 90 |
| `use_lanes` | spurbasierte Prädiktion (falls Spur bekannt) | – | True | – | – |
| `chain_length` | Länge der Spurfolge | m | 400 | 50 | 3000 |
| `use_yaw_rate` | konstante Gierrate (CTRV) | – | False | – | – |

## Theorie

$x(t) = x_0 + v \cos\psi\, t$, $y(t) = y_0 + v \sin\psi\, t$; mit CTRV $\psi(t) = \psi_0 + \dot\psi t$.

## Verfahren

[Cv prediction](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Validierung

- tests/prediction/test_prediction_predictors.py

## Verwendung

Tests: [tests/prediction/test_prediction_predictors.py](../../../../tests/prediction/test_prediction_predictors.py)
