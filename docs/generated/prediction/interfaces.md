# prediction – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.prediction` gibt es noch keine handgeschriebene Dokumentation (`vdsim/prediction/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init prediction`


## Komponenten

### [Konstante Beschleunigung (Frenet, Werling 3.5.2)](components/predictor__constant_acceleration.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `predictor/constant_acceleration`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.prediction.predictors.ConstantAccelerationPredictor` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `objects` | `ObjectList` | – | – | – |
| `world` | `WorldState` | – | – | optional |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `prediction` | `Prediction` | – | – | – |

### [Konstante Geschwindigkeit (kartesisch)](components/predictor__constant_velocity.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `predictor/constant_velocity`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.prediction.predictors.ConstantVelocityPredictor` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `objects` | `ObjectList` | – | – | – |
| `world` | `WorldState` | – | – | optional |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `prediction` | `Prediction` | – | – | – |

### [Spurfolge mit Querabsicht](components/predictor__lane_following.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `predictor/lane_following`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.prediction.predictors.LaneFollowingPredictor` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `objects` | `ObjectList` | – | – | – |
| `world` | `WorldState` | – | – | optional |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `prediction` | `Prediction` | – | – | – |

## Öffentliche API

### `vdsim.prediction.predictors`

| Name | Art | Beschreibung |
|---|---|---|
| [`PredictorParams`](../../../vdsim/prediction/predictors.py#L28) | Klasse | – |
| [`LaneFollowingParams`](../../../vdsim/prediction/predictors.py#L38) | Klasse | – |
| [`ConstantVelocityParams`](../../../vdsim/prediction/predictors.py#L45) | Klasse | – |
| [`ConstantAccelerationPredictor`](../../../vdsim/prediction/predictors.py#L143) | Klasse | – |
| [`ConstantVelocityPredictor`](../../../vdsim/prediction/predictors.py#L174) | Klasse | – |
| [`LaneFollowingPredictor`](../../../vdsim/prediction/predictors.py#L201) | Klasse | – |
| [`ca_motion(s0, v0, a0, tau, v_max)`](../../../vdsim/prediction/predictors.py#L51) | Funktion | 1d motion with constant acceleration, clamped at standstill (no reversing) and at v_max |
| [`lateral_convergence(d0, d_dot0, d_target, tau, T)`](../../../vdsim/prediction/predictors.py#L75) | Funktion | critically damped lateral motion with initial value and slope (closed form) |
