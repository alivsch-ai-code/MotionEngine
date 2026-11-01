# Desktop-Anwendung (PySide6) – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


**Noch nicht dokumentiert.** Es gibt keine handgeschriebene `theory.md` (`vdsim/gui/docs/theory.md`).

## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}

Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt `## … {#concept-id}`:

- `frenet_frame`

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Zeitliche Konsistenz (Bellman-Prinzip)](../planning/theory.md#bellman_principle) | [`planner.WerlingPlanner._compose_output`](../../../vdsim/planning/planner.py#L419), [`metrics.consistency_deviation`](../../../vdsim/research/metrics.py#L264) | [`trajectory_planner/frenet_naive`](../planning/components/trajectory_planner__frenet_naive.md), [`trajectory_planner/werling`](../planning/components/trajectory_planner__werling.md) | [Bellman (1957)](../references.md#bellman1957), [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Frenet frame](../README.md#konzepte-ohne-dokumentation) | – | [`predictor/constant_acceleration`](../prediction/components/predictor__constant_acceleration.md) | [Werling (2011)](../references.md#werling2011) |
| [Vollfaktorieller Versuchsplan](../research/theory.md#full_factorial_design) | [`experiments.parameter_sweep`](../../../vdsim/research/experiments.py#L98) | – | [Montgomery (2017)](../references.md#montgomery2017) |
| [Monte-Carlo-Simulation und Sensitivität](../research/theory.md#monte_carlo) | [`experiments.monte_carlo`](../../../vdsim/research/experiments.py#L133) | – | [Saltelli et al. (2008)](../references.md#saltelli2008) |
