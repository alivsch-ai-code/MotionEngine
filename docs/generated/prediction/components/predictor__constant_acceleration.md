# Konstante Beschleunigung (Frenet, Werling 3.5.2)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [prediction](../index.md) · `predictor/constant_acceleration` · Version 1.0.0

**Prädiziert Objekte mit konstanter Beschleunigung entlang ihrer Spur in Frenet-Koordinaten.**

## Zweck

Prädiktion der Vorder- und Lückenfahrzeuge für Folge- und Einfädelmodus nach Werling 3.5.2.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `predictor` |
| Name | `constant_acceleration` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.prediction.predictors.ConstantAccelerationPredictor`](../../../../vdsim/prediction/predictors.py#L143) |
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

## Theorie

$s_v(t) = s_v(0) + \dot s_v(0) t + \tfrac12 \ddot s_v(0) t^2$, $d(t) = d(0)$; bei $\dot s_v(t) \le 0$ wird der Stillstand gehalten. Objekte ohne Spur werden kartesisch entlang ihrer Orientierung prädiziert.

## Verfahren

[Ca prediction](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Frenet frame](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Beschleunigung über den Horizont konstant
- keine Querbewegung relativ zur Spur
- an Verzweigungen folgt das Objekt der Standardfortsetzung der Spur

## Einschränkungen

- Spurwechsel und Abbiegen anderer Verkehrsteilnehmer werden nicht vorhergesagt

## Validierung

- tests/prediction/test_prediction_predictors.py

## Umgesetzte Gleichungen

- `werling2011:3.5.2`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/behavior/test_behavior_rule_based.py](../../../../tests/behavior/test_behavior_rule_based.py), [tests/prediction/test_prediction_predictors.py](../../../../tests/prediction/test_prediction_predictors.py)
