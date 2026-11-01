# prediction – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`ca_motion`](../../../vdsim/prediction/predictors.py#L51) | Abschn. 3.5.2 s_v(t) = s_v(0) + ṡ_v(0) t + ½ s̈_v(0) t² | [Ca prediction](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py) | Code (@trace) |
| [`lateral_convergence`](../../../vdsim/prediction/predictors.py#L75) | Abschn. 3.5.2 | [Lateral intent](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py) | Code (@trace) |
