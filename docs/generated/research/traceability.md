# Forschungsmodus – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`monte_carlo`](../../../vdsim/research/experiments.py#L133) | – | [Monte-Carlo-Simulation und Sensitivität](theory.md#monte_carlo) | [Saltelli et al. (2008)](../references.md#saltelli2008) | [test_research_metrics.py](../../../tests/research/test_research_metrics.py) | Code (@trace) |
| [`parameter_sweep`](../../../vdsim/research/experiments.py#L98) | – | [Vollfaktorieller Versuchsplan](theory.md#full_factorial_design) | [Montgomery (2017)](../references.md#montgomery2017) | [test_research_metrics.py](../../../tests/research/test_research_metrics.py) | Code (@trace) |
| [`consistency_deviation`](../../../vdsim/research/metrics.py#L264) | Abschn. 3.2 | [Zeitliche Konsistenz (Bellman-Prinzip)](../planning/theory.md#bellman_principle) | [Werling (2011)](../references.md#werling2011) | [test_research_metrics.py](../../../tests/research/test_research_metrics.py) | Code (@trace) |
| [`rectangle_distance`](../../../vdsim/research/metrics.py#L94) | Abschn. 4.4 | [Abstand orientierter Rechtecke](theory.md#rectangle_distance) | [Ericson (2004)](../references.md#ericson2004) | [test_research_metrics.py](../../../tests/research/test_research_metrics.py) | Code (@trace) |
| [`safety_metrics`](../../../vdsim/research/metrics.py#L127) | – | [Surrogate Safety Measures](theory.md#surrogate_safety_measures) | [Vogel (2003)](../references.md#vogel2003) | [test_research_metrics.py](../../../tests/research/test_research_metrics.py) | Code (@trace) |

## Warum es diese Implementierungen gibt

### `monte_carlo`

- **Warum:** Streuende Einflüsse wie Verkehr, Reibwert oder Sensorrauschen abbilden und die Verteilung der Kennwerte schätzen.
- **Theorie:** [Monte-Carlo-Simulation und Sensitivität](theory.md#monte_carlo)
- **Annahmen:** Die Läufe sind unabhängig.
- **Quelle:** [Saltelli et al. (2008)](../references.md#saltelli2008)
- **Hinweis:** Monte-Carlo-Stichprobe der Eingangsparameter

### `parameter_sweep`

- **Warum:** Den Einfluss weniger Parameter systematisch über alle Kombinationen untersuchen.
- **Theorie:** [Vollfaktorieller Versuchsplan](theory.md#full_factorial_design)
- **Annahmen:** Die Parameter sind unabhängig einstellbar.
- **Quelle:** [Montgomery (2017)](../references.md#montgomery2017)
- **Hinweis:** vollfaktorieller Versuchsplan

### `consistency_deviation`

- **Warum:** Bei zyklischer Neuplanung soll sich die verbleibende Trajektorie nur verkürzen, nicht verändern.
- **Theorie:** [Zeitliche Konsistenz (Bellman-Prinzip)](../planning/theory.md#bellman_principle)
- **Annahmen:** Die Restriktionen sind inaktiv, und nur konsistente Kostenterme sind aktiv.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Messung der zeitlichen Konsistenz: Abweichung neuer Plan vs. Rest des alten Plans

### `rectangle_distance`

- **Warum:** Den kleinsten Abstand der Fahrzeugumrisse bestimmen bzw.
- **Theorie:** [Abstand orientierter Rechtecke](theory.md#rectangle_distance)
- **Annahmen:** Fahrzeuge sind Rechtecke (Länge × Breite) um den geometrischen Mittelpunkt.
- **Quelle:** [Ericson (2004)](../references.md#ericson2004)
- **Hinweis:** Abstand orientierter Rechtecke (SAT + Kantenabstände)

### `safety_metrics`

- **Warum:** Kollisionen sind seltene Ereignisse.
- **Theorie:** [Surrogate Safety Measures](theory.md#surrogate_safety_measures)
- **Annahmen:** - Lücke $g$ von Stoßstange zu Stoßstange in Ego-Längsrichtung.
- **Quelle:** [Vogel (2003)](../references.md#vogel2003)
- **Hinweis:** TTC, Zeitlücke, DRAC und PET als Surrogate Safety Measures
