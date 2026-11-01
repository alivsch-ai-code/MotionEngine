# Aktorik – Latenzkette, Lenkaktor, Kennlinienfehler – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`DeadTime`](../../../vdsim/actuators/latency.py#L19) | – | [Latenzkette aus Totzeit und PT1](theory.md#latency_chain) | – | – | module.yaml |
| [`LatencyChain`](../../../vdsim/actuators/latency.py#L42) | – | [Latenzkette aus Totzeit und PT1](theory.md#latency_chain) | – | [test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | module.yaml |
| [`PT1`](../../../vdsim/actuators/latency.py#L31) | – | [Latenzkette aus Totzeit und PT1](theory.md#latency_chain) | – | – | module.yaml |
| [`SteeringActuator.step`](../../../vdsim/actuators/steering_actuator.py#L46) | – | [Wirkkette des Lenkaktors](theory.md#steering_actuator_chain) | – | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | module.yaml |
| [`correction_factor`](../../../vdsim/actuators/steering_characteristic.py#L21) | – | [Kennlinienfehler des Lenkaktors](theory.md#steering_characteristic_error) | – | – | module.yaml |
| [`steering_characteristic`](../../../vdsim/actuators/steering_characteristic.py#L6) | – | [Kennlinienfehler des Lenkaktors](theory.md#steering_characteristic_error) | – | [test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `DeadTime`

- **Warum:** Nachbildung der Signallaufzeiten in der Wirkkette Planer → Gateway → Aktuator → Fahrzeug → Odometrie → Gateway → Planer.
- **Theorie:** [Latenzkette aus Totzeit und PT1](theory.md#latency_chain)
- **Annahmen:** Konstante, bekannte Latenzen; lineare Aktordynamik.
- **Quelle:** –

### `LatencyChain`

- **Warum:** Nachbildung der Signallaufzeiten in der Wirkkette Planer → Gateway → Aktuator → Fahrzeug → Odometrie → Gateway → Planer.
- **Theorie:** [Latenzkette aus Totzeit und PT1](theory.md#latency_chain)
- **Annahmen:** Konstante, bekannte Latenzen; lineare Aktordynamik.
- **Quelle:** –

### `PT1`

- **Warum:** Nachbildung der Signallaufzeiten in der Wirkkette Planer → Gateway → Aktuator → Fahrzeug → Odometrie → Gateway → Planer.
- **Theorie:** [Latenzkette aus Totzeit und PT1](theory.md#latency_chain)
- **Annahmen:** Konstante, bekannte Latenzen; lineare Aktordynamik.
- **Quelle:** –

### `SteeringActuator.step`

- **Warum:** Verbindet Korrektur, Latenz, Kennlinie und Ratenbegrenzung zu einem Aktormodell für den Simulator.
- **Theorie:** [Wirkkette des Lenkaktors](theory.md#steering_actuator_chain)
- **Annahmen:** Gemessene Krümmung $r/\max(v_x, 1)$; Latenzmodell des Schätzers identisch zur realen Kette.
- **Quelle:** –

### `correction_factor`

- **Warum:** Systematischer Fehler zwischen angeforderter und gestellter Krümmung, z.
- **Theorie:** [Kennlinienfehler des Lenkaktors](theory.md#steering_characteristic_error)
- **Annahmen:** Symmetrisch links/rechts, zeitinvariant.
- **Quelle:** –

### `steering_characteristic`

- **Warum:** Systematischer Fehler zwischen angeforderter und gestellter Krümmung, z.
- **Theorie:** [Kennlinienfehler des Lenkaktors](theory.md#steering_characteristic_error)
- **Annahmen:** Symmetrisch links/rechts, zeitinvariant.
- **Quelle:** –
