# Komponenten-Framework der AD-Plattform – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`Component.describe`](../../../vdsim/framework/component.py#L140) | – | [Komponentenmodell mit typisierten Ports](theory.md#component_model) | – | [test_matlab_component.py](../../../tests/matlab/test_matlab_component.py), [test_runtime_executor.py](../../../tests/runtime/test_runtime_executor.py), [test_runtime_graph.py](../../../tests/runtime/test_runtime_graph.py) | module.yaml |
| [`params_schema`](../../../vdsim/framework/component.py#L154) | – | [Komponentenmodell mit typisierten Ports](theory.md#component_model) | – | [test_matlab_component.py](../../../tests/matlab/test_matlab_component.py), [test_runtime_executor.py](../../../tests/runtime/test_runtime_executor.py), [test_runtime_graph.py](../../../tests/runtime/test_runtime_graph.py) | module.yaml |
| [`Container.resolve`](../../../vdsim/framework/container.py#L36) | – | [Dependency Injection und Laufzeitkontext](theory.md#dependency_injection) | [Fowler (2004)](../references.md#fowler2004) | – | module.yaml |
| [`RunContext.rng`](../../../vdsim/framework/context.py#L37) | – | [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding) | – | [test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py), [test_perception_sensor.py](../../../tests/perception/test_perception_sensor.py), [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py), [test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py), [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py), [test_world_scenarios.py](../../../tests/world/test_world_scenarios.py) | module.yaml |
| [`stable_seed`](../../../vdsim/framework/context.py#L19) | – | [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding) | – | [test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py), [test_perception_sensor.py](../../../tests/perception/test_perception_sensor.py), [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py), [test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py), [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py), [test_world_scenarios.py](../../../tests/world/test_world_scenarios.py) | module.yaml |
| [`trace`](../../../vdsim/framework/knowledge.py#L41) | – | [Rückverfolgbarkeitsmodell](../knowledge/theory.md#traceability_model) | [Gotel und Finkelstein (1994)](../references.md#gotel1994) | [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py) | module.yaml |
| [`get_component`](../../../vdsim/framework/plugins.py#L118) | – | [Versionierte Plugin-Registry](theory.md#plugin_registry) | – | [test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py), [test_matlab_component.py](../../../tests/matlab/test_matlab_component.py), [test_perception_sensor.py](../../../tests/perception/test_perception_sensor.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py), [test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py), [test_runtime_executor.py](../../../tests/runtime/test_runtime_executor.py), [test_runtime_graph.py](../../../tests/runtime/test_runtime_graph.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py), [test_stabilization_classic.py](../../../tests/stabilization/test_stabilization_classic.py), [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py), [test_world_scenarios.py](../../../tests/world/test_world_scenarios.py) | module.yaml |
| [`version_matches`](../../../vdsim/framework/plugins.py#L51) | – | [Versionierte Plugin-Registry](theory.md#plugin_registry) | [Preston-Werner](../references.md#semver2) | [test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py), [test_matlab_component.py](../../../tests/matlab/test_matlab_component.py), [test_perception_sensor.py](../../../tests/perception/test_perception_sensor.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py), [test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py), [test_runtime_executor.py](../../../tests/runtime/test_runtime_executor.py), [test_runtime_graph.py](../../../tests/runtime/test_runtime_graph.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py), [test_stabilization_classic.py](../../../tests/stabilization/test_stabilization_classic.py), [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py), [test_world_scenarios.py](../../../tests/world/test_world_scenarios.py) | module.yaml |
| [`manifest`](../../../vdsim/framework/provenance.py#L27) | – | [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding) | – | – | module.yaml |
| [`compatible`](../../../vdsim/framework/types.py#L422) | – | [Signaltypen und Codecs](theory.md#signal_type_system) | – | [test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py), [test_perception_sensor.py](../../../tests/perception/test_perception_sensor.py), [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py), [test_research_metrics.py](../../../tests/research/test_research_metrics.py), [test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py), [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py), [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py), [test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py), [test_world_actors.py](../../../tests/world/test_world_actors.py), [test_world_scenarios.py](../../../tests/world/test_world_scenarios.py) | module.yaml |
| [`encode`](../../../vdsim/framework/types.py#L484) | – | [Signaltypen und Codecs](theory.md#signal_type_system) | – | [test_behavior_rule_based.py](../../../tests/behavior/test_behavior_rule_based.py), [test_perception_sensor.py](../../../tests/perception/test_perception_sensor.py), [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_prediction_predictors.py](../../../tests/prediction/test_prediction_predictors.py), [test_research_metrics.py](../../../tests/research/test_research_metrics.py), [test_runtime_custom_python.py](../../../tests/runtime/test_runtime_custom_python.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py), [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py), [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py), [test_stabilization_switching.py](../../../tests/stabilization/test_stabilization_switching.py), [test_world_actors.py](../../../tests/world/test_world_actors.py), [test_world_scenarios.py](../../../tests/world/test_world_scenarios.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `Component.describe`

- **Warum:** Einheitliche Beschreibung aller Bausteine der Wirkkette, damit Komponenten derselben Ebene austauschbar, prüfbar und dokumentierbar sind.
- **Theorie:** [Komponentenmodell mit typisierten Ports](theory.md#component_model)
- **Annahmen:** Jede Komponente kennt ihre Ports statisch (Klassenattribute); Custom Nodes dürfen Ports dynamisch über `ports()` melden.
- **Quelle:** –

### `params_schema`

- **Warum:** Einheitliche Beschreibung aller Bausteine der Wirkkette, damit Komponenten derselben Ebene austauschbar, prüfbar und dokumentierbar sind.
- **Theorie:** [Komponentenmodell mit typisierten Ports](theory.md#component_model)
- **Annahmen:** Jede Komponente kennt ihre Ports statisch (Klassenattribute); Custom Nodes dürfen Ports dynamisch über `ports()` melden.
- **Quelle:** –

### `Container.resolve`

- **Warum:** Komponenten erhalten alles, was sie aus der Umgebung brauchen (Zeitschritt, Fahrzeug, Straße, Dienste), statt globalen Zustand zu lesen.
- **Theorie:** [Dependency Injection und Laufzeitkontext](theory.md#dependency_injection)
- **Annahmen:** Fabriken sind seiteneffektfrei bis auf die Objekterzeugung.
- **Quelle:** [Fowler (2004)](../references.md#fowler2004)

### `RunContext.rng`

- **Warum:** Bitgenau reproduzierbare Läufe, auch mit Rauschen und Monte-Carlo-Studien.
- **Theorie:** [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding)
- **Annahmen:** Keine Wanduhrzeit und kein globaler Zufall in der Logik.
- **Quelle:** –

### `stable_seed`

- **Warum:** Bitgenau reproduzierbare Läufe, auch mit Rauschen und Monte-Carlo-Studien.
- **Theorie:** [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding)
- **Annahmen:** Keine Wanduhrzeit und kein globaler Zufall in der Logik.
- **Quelle:** –

### `trace`

- **Warum:** Für jede wesentliche Implementierung erkennbar machen, warum sie existiert, welches Problem sie löst, welche Theorie und Annahmen dahinterstehen, auf welchen Quellen sie beruht und welche Tests sie prüfen.
- **Theorie:** [Rückverfolgbarkeitsmodell](../knowledge/theory.md#traceability_model)
- **Annahmen:** Konzept- und Referenz-IDs sind stabil; Annotationen werden bei Änderungen gepflegt.
- **Quelle:** [Gotel und Finkelstein (1994)](../references.md#gotel1994)

### `get_component`

- **Warum:** Komponenten über Namen und Versionsbereiche finden und erzeugen; mehrere Versionen parallel.
- **Theorie:** [Versionierte Plugin-Registry](theory.md#plugin_registry)
- **Annahmen:** Versionen im Format MAJOR.MINOR.PATCH; fehlende Teile werden mit 0 ergänzt.
- **Quelle:** –

### `version_matches`

- **Warum:** Komponenten über Namen und Versionsbereiche finden und erzeugen; mehrere Versionen parallel.
- **Theorie:** [Versionierte Plugin-Registry](theory.md#plugin_registry)
- **Annahmen:** Versionen im Format MAJOR.MINOR.PATCH; fehlende Teile werden mit 0 ergänzt.
- **Quelle:** [Preston-Werner](../references.md#semver2)

### `manifest`

- **Warum:** Bitgenau reproduzierbare Läufe, auch mit Rauschen und Monte-Carlo-Studien.
- **Theorie:** [Deterministische Zufallszahlen und Reproduzierbarkeit](theory.md#deterministic_seeding)
- **Annahmen:** Keine Wanduhrzeit und kein globaler Zufall in der Logik.
- **Quelle:** –

### `compatible`

- **Warum:** Verbindliche Datentypen zwischen den Ebenen und flache Darstellung für native Komponenten (C++/Rust).
- **Theorie:** [Signaltypen und Codecs](theory.md#signal_type_system)
- **Annahmen:** SI-Einheiten, erdfestes System x Osten, y Norden.
- **Quelle:** –

### `encode`

- **Warum:** Verbindliche Datentypen zwischen den Ebenen und flache Darstellung für native Komponenten (C++/Rust).
- **Theorie:** [Signaltypen und Codecs](theory.md#signal_type_system)
- **Annahmen:** SI-Einheiten, erdfestes System x Osten, y Norden.
- **Quelle:** –
