# Auswertung und Berichte – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`KPIEvaluator._braking`](../../../vdsim/reporting/kpi_evaluator.py#L244) | – | [Kennwerte der Normversuche](theory.md#iso_test_kpis) | [UN-ECE-Regelung Nr. 13-H](../references.md#unece_r13h) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`KPIEvaluator._cone_test`](../../../vdsim/reporting/kpi_evaluator.py#L163) | – | [Kennwerte der Normversuche](theory.md#iso_test_kpis) | [ISO 3888-1:2018 (2018)](../references.md#iso3888_1) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`KPIEvaluator._frequency_response`](../../../vdsim/reporting/kpi_evaluator.py#L272) | – | [Frequenzgang aus dem Sinus-Sweep](theory.md#frequency_response_estimation) | [Welch (1967)](../references.md#welch1967) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`KPIEvaluator._general`](../../../vdsim/reporting/kpi_evaluator.py#L88) | – | [Reibwertausnutzung und Stabilitätsreserve](theory.md#friction_utilization) | [Milliken und Milliken (1995)](../references.md#milliken1995) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`KPIEvaluator._sine_dwell`](../../../vdsim/reporting/kpi_evaluator.py#L224) | – | [Kennwerte der Normversuche](theory.md#iso_test_kpis) | [FMVSS No. 126 (49 CFR 571.126) (2007)](../references.md#fmvss126) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`KPIEvaluator._step_steer`](../../../vdsim/reporting/kpi_evaluator.py#L206) | – | [Kennwerte der Normversuche](theory.md#iso_test_kpis) | [ISO 7401:2011 (2011)](../references.md#iso7401) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`KPIEvaluator._understeer`](../../../vdsim/reporting/kpi_evaluator.py#L189) | – | [Kennwerte der Normversuche](theory.md#iso_test_kpis) | [ISO 4138:2021 (2021)](../references.md#iso4138) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`iso2631_rating`](../../../vdsim/reporting/kpi_evaluator.py#L57) | – | [Komfortbewertung nach ISO 2631-1](theory.md#iso2631_comfort) | [ISO 2631-1:1997 (1997)](../references.md#iso2631_1) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`iso2631_weighted_rms`](../../../vdsim/reporting/kpi_evaluator.py#L43) | – | [Komfortbewertung nach ISO 2631-1](theory.md#iso2631_comfort) | [ISO 2631-1:1997 (1997)](../references.md#iso2631_1) | [test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `KPIEvaluator._braking`

- **Warum:** Objektive Bewertung der genormten Fahrmanöver.
- **Theorie:** [Kennwerte der Normversuche](theory.md#iso_test_kpis)
- **Annahmen:** Manöver laut Metadaten korrekt gefahren; ISO 7401 mit Lenkrampe ~0,15 s.
- **Quelle:** [UN-ECE-Regelung Nr. 13-H](../references.md#unece_r13h)

### `KPIEvaluator._cone_test`

- **Warum:** Objektive Bewertung der genormten Fahrmanöver.
- **Theorie:** [Kennwerte der Normversuche](theory.md#iso_test_kpis)
- **Annahmen:** Manöver laut Metadaten korrekt gefahren; ISO 7401 mit Lenkrampe ~0,15 s.
- **Quelle:** [ISO 3888-1:2018 (2018)](../references.md#iso3888_1)

### `KPIEvaluator._frequency_response`

- **Warum:** Schätzung der Übertragungsfunktion Gierrate/Lenkwinkel aus einem simulierten Versuch (ISO 7401, Sweep).
- **Theorie:** [Frequenzgang aus dem Sinus-Sweep](theory.md#frequency_response_estimation)
- **Annahmen:** Näherungsweise lineares, zeitinvariantes Verhalten während des Sweeps.
- **Quelle:** [Welch (1967)](../references.md#welch1967)

### `KPIEvaluator._general`

- **Warum:** Wie nah ist das Fahrzeug an der Haftgrenze?
- **Theorie:** [Reibwertausnutzung und Stabilitätsreserve](theory.md#friction_utilization)
- **Annahmen:** Isotroper Reibkreis; $\mu$ aus Reifen- und Fahrbahnreibwert.
- **Quelle:** [Milliken und Milliken (1995)](../references.md#milliken1995)

### `KPIEvaluator._sine_dwell`

- **Warum:** Objektive Bewertung der genormten Fahrmanöver.
- **Theorie:** [Kennwerte der Normversuche](theory.md#iso_test_kpis)
- **Annahmen:** Manöver laut Metadaten korrekt gefahren; ISO 7401 mit Lenkrampe ~0,15 s.
- **Quelle:** [FMVSS No. 126 (49 CFR 571.126) (2007)](../references.md#fmvss126)

### `KPIEvaluator._step_steer`

- **Warum:** Objektive Bewertung der genormten Fahrmanöver.
- **Theorie:** [Kennwerte der Normversuche](theory.md#iso_test_kpis)
- **Annahmen:** Manöver laut Metadaten korrekt gefahren; ISO 7401 mit Lenkrampe ~0,15 s.
- **Quelle:** [ISO 7401:2011 (2011)](../references.md#iso7401)

### `KPIEvaluator._understeer`

- **Warum:** Objektive Bewertung der genormten Fahrmanöver.
- **Theorie:** [Kennwerte der Normversuche](theory.md#iso_test_kpis)
- **Annahmen:** Manöver laut Metadaten korrekt gefahren; ISO 7401 mit Lenkrampe ~0,15 s.
- **Quelle:** [ISO 4138:2021 (2021)](../references.md#iso4138)

### `iso2631_rating`

- **Warum:** Bewertung der Ganzkörperschwingungen über einen frequenzbewerteten Effektivwert der Vertikalbeschleunigung.
- **Theorie:** [Komfortbewertung nach ISO 2631-1](theory.md#iso2631_comfort)
- **Annahmen:** Sitzende Person, vertikale Richtung, Aufbauschwerpunkt als Messort.
- **Quelle:** [ISO 2631-1:1997 (1997)](../references.md#iso2631_1)

### `iso2631_weighted_rms`

- **Warum:** Bewertung der Ganzkörperschwingungen über einen frequenzbewerteten Effektivwert der Vertikalbeschleunigung.
- **Theorie:** [Komfortbewertung nach ISO 2631-1](theory.md#iso2631_comfort)
- **Annahmen:** Sitzende Person, vertikale Richtung, Aufbauschwerpunkt als Messort.
- **Quelle:** [ISO 2631-1:1997 (1997)](../references.md#iso2631_1)
