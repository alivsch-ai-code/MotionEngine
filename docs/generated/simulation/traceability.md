# Simulationskern – Löser, Regelkreis, Szenarien, Ergebnisse – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`iso8608_profile`](../../../vdsim/simulation/environment.py#L108) | – | [Fahrbahnprofil nach ISO 8608](theory.md#iso8608_road_profile) | [ISO 8608:2016 (2016)](../references.md#iso8608) | [test_stabilization_layers.py](../../../tests/stabilization/test_stabilization_layers.py), [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py), [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`Simulator._substeps`](../../../vdsim/simulation/simulator.py#L70) | – | [Stabilitätsbegrenzte Teilschritte (stable_dt)](theory.md#stable_substeps) | [Hairer und Wanner (1996)](../references.md#hairer1996) | [conftest.py](../../../tests/conftest.py) | module.yaml |
| [`Simulator.step`](../../../vdsim/simulation/simulator.py#L113) | – | [Ablauf eines Simulationsschritts](theory.md#simulation_loop) | – | [conftest.py](../../../tests/conftest.py) | module.yaml |
| [`AdaptiveSolver`](../../../vdsim/simulation/solver.py#L52) | – | [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta) | [Virtanen et al. (2020)](../references.md#virtanen2020) | [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`EulerSolver`](../../../vdsim/simulation/solver.py#L25) | – | [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta) | [Butcher (2016)](../references.md#butcher2016) | [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`HeunSolver`](../../../vdsim/simulation/solver.py#L32) | – | [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta) | [Butcher (2016)](../references.md#butcher2016) | [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`RK4Solver`](../../../vdsim/simulation/solver.py#L41) | – | [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta) | [Hairer et al. (1993)](../references.md#hairer1993) | [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `iso8608_profile`

- **Warum:** Stochastische Fahrbahnunebenheit einer genormten Straßenklasse als Anregung für Komfort- und Radlastuntersuchungen.
- **Theorie:** [Fahrbahnprofil nach ISO 8608](theory.md#iso8608_road_profile)
- **Annahmen:** Stationäres, ergodisches, gaußsches Profil; die Werte $G_d(n_0)$ sind die geometrischen Klassenmitten der Norm.
- **Quelle:** [ISO 8608:2016 (2016)](../references.md#iso8608)

### `Simulator._substeps`

- **Warum:** Wahl der Modellschrittweite so, dass der explizite RK4 bei der steifen Raddrehdynamik stabil bleibt, ohne bei Autobahntempo unnötig klein zu werden.
- **Theorie:** [Stabilitätsbegrenzte Teilschritte (stable_dt)](theory.md#stable_substeps)
- **Annahmen:** - Maximale Längssteifigkeit bei doppelter statischer Radlast: $C_{\kappa,max} = 2 C_\kappa F_{z,stat,max}/F_{z0}$.
- **Quelle:** [Hairer und Wanner (1996)](../references.md#hairer1996)

### `Simulator.step`

- **Warum:** Reproduzierbarer, zeitdiskreter Regelkreis wie im Fahrzeug: Regler rechnen im festen Takt, die Strecke kontinuierlich.
- **Theorie:** [Ablauf eines Simulationsschritts](theory.md#simulation_loop)
- **Annahmen:** Alle Regler sehen den wahren Zustand (keine Sensorik), außer der verzögerten Krümmung im Lenkaktor.
- **Quelle:** –

### `AdaptiveSolver`

- **Warum:** Numerische Lösung der Bewegungsgleichungen $\dot{\mathbf{x}} = f(t, \mathbf{x}, \mathbf{u})$ bei während eines Reglerschritts konstanter Stellgröße $\mathbf{u}$.
- **Theorie:** [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta)
- **Annahmen:** - $f$ hinreichend glatt (die Modelle glätten Unstetigkeiten mit $\tanh$).
- **Quelle:** [Virtanen et al. (2020)](../references.md#virtanen2020)

### `EulerSolver`

- **Warum:** Numerische Lösung der Bewegungsgleichungen $\dot{\mathbf{x}} = f(t, \mathbf{x}, \mathbf{u})$ bei während eines Reglerschritts konstanter Stellgröße $\mathbf{u}$.
- **Theorie:** [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta)
- **Annahmen:** - $f$ hinreichend glatt (die Modelle glätten Unstetigkeiten mit $\tanh$).
- **Quelle:** [Butcher (2016)](../references.md#butcher2016)

### `HeunSolver`

- **Warum:** Numerische Lösung der Bewegungsgleichungen $\dot{\mathbf{x}} = f(t, \mathbf{x}, \mathbf{u})$ bei während eines Reglerschritts konstanter Stellgröße $\mathbf{u}$.
- **Theorie:** [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta)
- **Annahmen:** - $f$ hinreichend glatt (die Modelle glätten Unstetigkeiten mit $\tanh$).
- **Quelle:** [Butcher (2016)](../references.md#butcher2016)

### `RK4Solver`

- **Warum:** Numerische Lösung der Bewegungsgleichungen $\dot{\mathbf{x}} = f(t, \mathbf{x}, \mathbf{u})$ bei während eines Reglerschritts konstanter Stellgröße $\mathbf{u}$.
- **Theorie:** [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta)
- **Annahmen:** - $f$ hinreichend glatt (die Modelle glätten Unstetigkeiten mit $\tanh$).
- **Quelle:** [Hairer et al. (1993)](../references.md#hairer1993)
