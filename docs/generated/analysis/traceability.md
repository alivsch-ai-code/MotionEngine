# Fahrzeuganalyse – linear und quasi-statisch – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`LinearSingleTrackAnalysis.characteristic_speed`](../../../vdsim/analysis/linear_analysis.py#L20) | – | [Eigenlenkgradient und charakteristische Geschwindigkeit](theory.md#understeer_gradient) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py), [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`LinearSingleTrackAnalysis.critical_speed`](../../../vdsim/analysis/linear_analysis.py#L26) | – | [Eigenlenkgradient und charakteristische Geschwindigkeit](theory.md#understeer_gradient) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py), [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`LinearSingleTrackAnalysis.eigen`](../../../vdsim/analysis/linear_analysis.py#L40) | – | [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis) | [Rajamani (2012)](../references.md#rajamani2012) | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py), [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`LinearSingleTrackAnalysis.frequency_response`](../../../vdsim/analysis/linear_analysis.py#L48) | – | [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis) | – | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py), [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`LinearSingleTrackAnalysis.steady_state_gains`](../../../vdsim/analysis/linear_analysis.py#L31) | – | [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py), [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`QuasiStaticAnalysis.ackermann_angles`](../../../vdsim/analysis/quasi_static.py#L74) | – | [Ackermann-Lenkgeometrie und Wendekreis](theory.md#ackermann_steering) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`QuasiStaticAnalysis.roll_gradient`](../../../vdsim/analysis/quasi_static.py#L28) | – | [Quasi-statische Radlasten und Wankgradient](theory.md#quasi_static_wheel_loads) | [Milliken und Milliken (1995)](../references.md#milliken1995) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`QuasiStaticAnalysis.turning_circle`](../../../vdsim/analysis/quasi_static.py#L79) | – | [Ackermann-Lenkgeometrie und Wendekreis](theory.md#ackermann_steering) | – | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`QuasiStaticAnalysis.wheel_loads`](../../../vdsim/analysis/quasi_static.py#L41) | – | [Quasi-statische Radlasten und Wankgradient](theory.md#quasi_static_wheel_loads) | [Milliken und Milliken (1995)](../references.md#milliken1995) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `LinearSingleTrackAnalysis.characteristic_speed`

- **Warum:** Kennzahl für das stationäre Eigenlenkverhalten: Wie viel zusätzlicher Lenkwinkel ist pro Querbeschleunigung nötig?
- **Theorie:** [Eigenlenkgradient und charakteristische Geschwindigkeit](theory.md#understeer_gradient)
- **Annahmen:** Lineare Reifen, statische Achslasten, kleine Winkel.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `LinearSingleTrackAnalysis.critical_speed`

- **Warum:** Kennzahl für das stationäre Eigenlenkverhalten: Wie viel zusätzlicher Lenkwinkel ist pro Querbeschleunigung nötig?
- **Theorie:** [Eigenlenkgradient und charakteristische Geschwindigkeit](theory.md#understeer_gradient)
- **Annahmen:** Lineare Reifen, statische Achslasten, kleine Winkel.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `LinearSingleTrackAnalysis.eigen`

- **Warum:** Stationäre Verstärkungen, Eigenwerte (Eigenfrequenz, Dämpfung) und Frequenzgang der Gier- und Querdynamik.
- **Theorie:** [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis)
- **Annahmen:** Konstante Geschwindigkeit, lineares Modell.
- **Quelle:** [Rajamani (2012)](../references.md#rajamani2012)

### `LinearSingleTrackAnalysis.frequency_response`

- **Warum:** Stationäre Verstärkungen, Eigenwerte (Eigenfrequenz, Dämpfung) und Frequenzgang der Gier- und Querdynamik.
- **Theorie:** [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis)
- **Annahmen:** Konstante Geschwindigkeit, lineares Modell.
- **Quelle:** –

### `LinearSingleTrackAnalysis.steady_state_gains`

- **Warum:** Stationäre Verstärkungen, Eigenwerte (Eigenfrequenz, Dämpfung) und Frequenzgang der Gier- und Querdynamik.
- **Theorie:** [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis)
- **Annahmen:** Konstante Geschwindigkeit, lineares Modell.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `QuasiStaticAnalysis.ackermann_angles`

- **Warum:** Lenkwinkel der Vorderräder ohne Schräglauf und Wendekreisdurchmesser.
- **Theorie:** [Ackermann-Lenkgeometrie und Wendekreis](theory.md#ackermann_steering)
- **Annahmen:** Kein Schräglauf, Überhänge vorn und hinten gleich groß.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `QuasiStaticAnalysis.roll_gradient`

- **Warum:** Radlasten, Wankwinkel und Querlastverteilung bei konstanter Längs- und Querbeschleunigung.
- **Theorie:** [Quasi-statische Radlasten und Wankgradient](theory.md#quasi_static_wheel_loads)
- **Annahmen:** Kleine Wankwinkel, lineare Federn, feste Rollzentren.
- **Quelle:** [Milliken und Milliken (1995)](../references.md#milliken1995)

### `QuasiStaticAnalysis.turning_circle`

- **Warum:** Lenkwinkel der Vorderräder ohne Schräglauf und Wendekreisdurchmesser.
- **Theorie:** [Ackermann-Lenkgeometrie und Wendekreis](theory.md#ackermann_steering)
- **Annahmen:** Kein Schräglauf, Überhänge vorn und hinten gleich groß.
- **Quelle:** –

### `QuasiStaticAnalysis.wheel_loads`

- **Warum:** Radlasten, Wankwinkel und Querlastverteilung bei konstanter Längs- und Querbeschleunigung.
- **Theorie:** [Quasi-statische Radlasten und Wankgradient](theory.md#quasi_static_wheel_loads)
- **Annahmen:** Kleine Wankwinkel, lineare Federn, feste Rollzentren.
- **Quelle:** [Milliken und Milliken (1995)](../references.md#milliken1995)
