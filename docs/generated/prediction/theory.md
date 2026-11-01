# prediction – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


**Noch nicht dokumentiert.** Es gibt keine handgeschriebene `theory.md` (`vdsim/prediction/docs/theory.md`).

## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}

Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt `## … {#concept-id}`:

- `ca_prediction`
- `cv_prediction`
- `frenet_frame`
- `lane_following_prediction`
- `lateral_intent`

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Ca prediction](../README.md#konzepte-ohne-dokumentation) | [`predictors.ca_motion`](../../../vdsim/prediction/predictors.py#L51) | [`predictor/constant_acceleration`](components/predictor__constant_acceleration.md) | [Werling (2011)](../references.md#werling2011) |
| [Cv prediction](../README.md#konzepte-ohne-dokumentation) | – | [`predictor/constant_velocity`](components/predictor__constant_velocity.md) | – |
| [Frenet frame](../README.md#konzepte-ohne-dokumentation) | – | [`predictor/constant_acceleration`](components/predictor__constant_acceleration.md) | [Werling (2011)](../references.md#werling2011) |
| [Lane following prediction](../README.md#konzepte-ohne-dokumentation) | – | [`predictor/lane_following`](components/predictor__lane_following.md) | [Werling (2011)](../references.md#werling2011) |
| [Lateral intent](../README.md#konzepte-ohne-dokumentation) | [`predictors.lateral_convergence`](../../../vdsim/prediction/predictors.py#L75) | [`predictor/lane_following`](components/predictor__lane_following.md) | [Werling (2011)](../references.md#werling2011) |
