# Spurfolge mit Querabsicht

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [prediction](../index.md) · `predictor/lane_following` · Version 1.0.0

**Konstante Geschwindigkeit entlang der Spurfolge, Querablage konvergiert zur Zielspurmitte.**

## Zweck

Erkennt Spurwechsel (Einscherer) frühzeitig aus der Quergeschwindigkeit relativ zur Spur.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `predictor` |
| Name | `lane_following` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.prediction.predictors.LaneFollowingPredictor`](../../../../vdsim/prediction/predictors.py#L201) |
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
| `tau_lateral` | Zeitkonstante Querbewegung | s | 1.2 | 0.1 | 10 |
| `lateral_intent_speed` | Quergeschwindigkeit für Spurwechselabsicht | m/s | 0.35 | 0 | 3 |
| `use_acceleration` | Längsbeschleunigung berücksichtigen | – | False | – | – |

## Theorie

Längs: $s(t) = s_0 + \dot s_0 t$ (optional mit $\ddot s_0$). Quer: kritisch gedämpft $d(t) = d_z + (e_0 + (\dot d_0 + e_0/\tau) t) e^{-t/\tau}$ mit $e_0 = d_0 - d_z$. Die Zielablage $d_z$ ist die Mitte der Nachbarspur, wenn $|\dot d_0|$ die Absichtsschwelle überschreitet und das Objekt auf sie zuläuft, sonst die eigene Spurmitte.

## Verfahren

[Lane following prediction](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Lateral intent](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Objekte folgen der Standardfortsetzung der Spur

## Einschränkungen

- Abbiegeabsichten an Kreuzungen werden nicht geschätzt

## Validierung

- tests/prediction/test_prediction_predictors.py

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/prediction/test_prediction_predictors.py](../../../../tests/prediction/test_prediction_predictors.py)
