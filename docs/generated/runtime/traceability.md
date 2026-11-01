# Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`Integrator.update`](../../../vdsim/runtime/blocks.py#L367) | Abschn. 2 | [Diskrete Grundblöcke](theory.md#discrete_blocks) | [Lee und Seshia (2017)](../references.md#lee_seshia2017) | – | Code (@trace) |
| [`LowPass.step`](../../../vdsim/runtime/blocks.py#L396) | – | [Diskrete Grundblöcke](theory.md#discrete_blocks) | [Lee und Seshia (2017)](../references.md#lee_seshia2017) | – | Code (@trace) |

## Warum es diese Implementierungen gibt

### `Integrator.update`

- **Warum:** Integrator und PT1-Glied sind die Grundbausteine einfacher Regelkreise im Editor.
- **Theorie:** [Diskrete Grundblöcke](theory.md#discrete_blocks)
- **Annahmen:** Eingang konstant über das Abtastintervall (Halteglied).
- **Quelle:** [Lee und Seshia (2017)](../references.md#lee_seshia2017)
- **Hinweis:** explizites Euler-Verfahren

### `LowPass.step`

- **Warum:** Integrator und PT1-Glied sind die Grundbausteine einfacher Regelkreise im Editor.
- **Theorie:** [Diskrete Grundblöcke](theory.md#discrete_blocks)
- **Annahmen:** Eingang konstant über das Abtastintervall (Halteglied).
- **Quelle:** [Lee und Seshia (2017)](../references.md#lee_seshia2017)
- **Hinweis:** sprunginvariante Diskretisierung des PT1
