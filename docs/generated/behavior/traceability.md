# behavior – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`RuleBasedBehavior._lane_change_eval`](../../../vdsim/behavior/rule_based.py#L241) | Abschn. 3 | [Mobil](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007) | – | Code (@trace) |
| [`RuleBasedBehavior._update_merge`](../../../vdsim/behavior/rule_based.py#L761) | Abschn. 5.3.2 (3.15) | [Einfädeln](../planning/theory.md#merging_mode) | [Werling (2011)](../references.md#werling2011) | – | Code (@trace) |

## Warum es diese Implementierungen gibt

### `RuleBasedBehavior._update_merge`

- **Warum:** Positionierung in der Mitte einer Lücke auf der Zielspur.
- **Theorie:** [Einfädeln](../planning/theory.md#merging_mode)
- **Annahmen:** Beide Fahrzeuge bewegen sich mit konstanter Beschleunigung.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Lückenwahl, Längsreferenz in der Lückenmitte, gleichzeitiges Verlegen der Referenzkurve
