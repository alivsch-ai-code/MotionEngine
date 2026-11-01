# Simulationskern – Löser, Regelkreis, Szenarien, Ergebnisse

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.simulation` · Quellcode: [vdsim/simulation/](../../../vdsim/simulation) · Paketdoku: [vdsim/simulation/docs/](../../../vdsim/simulation/docs)

## Übersicht

**Schließt den Regelkreis Referenz → Regler → Aktorik → Regelsysteme → Fahrzeugmodell, integriert die Bewegungsgleichungen und zeichnet alle Signale auf.**

Der Simulator verbindet die austauschbaren Komponenten zu einem geschlossenen Regelkreis mit festem
Reglertakt und stabilitätsabhängigen Teilschritten des Fahrzeugmodells. Szenarien beschreiben einen
Versuch vollständig als JSON (Fahrzeug, Modell, Manöver, Regler, Aktorik, Umgebung, Löser), Ergebnisse
lassen sich exportieren, vergleichen und auswerten.

Paket-Docstring:

```text
Simulation core: solver, vehicle state, environment, simulator, scenarios and results.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 7 |
| Komponenten | 0 |
| Verfahren/Konzepte | 4 |
| @trace-Einträge | 7 |
| Tests | 6 |
| Beispiele | 2 |

## Architektur

- `solver.py`: `EulerSolver`, `HeunSolver`, `RK4Solver` mit Teilschritten, `AdaptiveSolver` (scipy solve_ivp).
- `simulator.Simulator`: ein Reglerschritt = Querregler, Längsregler, Längsaktuierung, Lenkaktor,
  Regelsysteme, Integration, Ausgangsgrößen, Logging, Abbruchprüfung. `from_scenario()` baut alles über
  die Registry auf.
- `scenario.Scenario` / `ScenarioManager`: JSON-Szenarien in `configs/scenarios/`.
- `environment.py`: Reibwertkarte (Flächen, Gitter, Split-µ), Fahrbahnprofil (Bodenwellen, ISO 8608), Wind, vorausfahrendes Fahrzeug.
- `results.SimulationResult`: Zeitreihen und Metadaten, Export CSV/JSON/NPZ.
- `vehicle_state.py`: `VehicleState` (modellunabhängige Sicht) und `ControlInput` (Stellgrößen).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.simulation`](../../../vdsim/simulation/__init__.py) | 2 | – | Simulation core: solver, vehicle state, environment, simulator, scenarios and results. |
| [`vdsim.simulation.environment`](../../../vdsim/simulation/environment.py) | 161 | FrictionPatch, FrictionMap, RoadProfile, LeadVehicle, Environment | Environment: road friction maps, wind, road profile and other traffic (lead vehicle). |
| [`vdsim.simulation.results`](../../../vdsim/simulation/results.py) | 113 | SimulationResult | Simulation result: time series of all signals plus metadata; CSV/JSON/NPZ export and import. |
| [`vdsim.simulation.scenario`](../../../vdsim/simulation/scenario.py) | 110 | Scenario, ScenarioManager | Scenario definition (JSON) and scenario management. |
| [`vdsim.simulation.simulator`](../../../vdsim/simulation/simulator.py) | 209 | Simulator | Simulator: closes the loop reference -> controllers -> actuators -> chassis systems -> vehicle model. |
| [`vdsim.simulation.solver`](../../../vdsim/simulation/solver.py) | 72 | Solver, EulerSolver, HeunSolver, RK4Solver, AdaptiveSolver | Numerical integrators for the vehicle model ODE: Euler, Heun, RK4 and an adaptive scipy solver. |
| [`vdsim.simulation.vehicle_state`](../../../vdsim/simulation/vehicle_state.py) | 67 | VehicleState, ControlInput | Vehicle state seen by controllers/sensors and the control input sent to the vehicle model. |

### Abhängigkeiten

- nutzt: [actuators](../actuators/index.md), [controllers](../controllers/index.md), [core](../core/index.md), [powertrain](../powertrain/index.md), [trajectory](../trajectory/index.md)
- genutzt von: [framework](../framework/index.md), [gui](../gui/index.md), [stabilization](../stabilization/index.md), [vehicle_models](../vehicle_models/index.md)
- externe Bibliotheken: `dataclasses`, `inspect`, `json`, `numpy`, `pathlib`, `scipy`, `time`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Fester Reglertakt dt_control, Fahrzeugmodell mit n = ceil(dt_control / dt_model) Teilschritten | Regler arbeiten wie im Steuergerät zeitdiskret; das Modell bleibt numerisch stabil | gemeinsamer adaptiver Löser für alles (Regler müssten zeitkontinuierlich formuliert sein) |
| Schrittweite des Modells aus stable_dt() des Modells | Die Raddrehdynamik ist bei kleiner Geschwindigkeit steif; bei Autobahntempo genügen 2 ms | implizite Löser (aufwendiger, Jacobi-Matrix nötig) |
| Alle Signale der Komponenten über deren signals-Dict automatisch protokollieren | neue Regler erscheinen ohne Änderung am Simulator in Plots und KPIs | – |

## Implementierung

- Die Lenkanforderung läuft durch den `SteeringActuator` (Kennlinie, Latenz, Rückkanal-Korrektur); als gemessene Krümmung dient r / max(v_x, 1).
- Abbruch bei NaN, Ende der Dauer, Ende der Trajektorie, Stillstand nach Bremsung, Zielgeschwindigkeit, Kollision mit dem vorausfahrenden Fahrzeug oder Instabilität (|β| > 60°, |φ| > 0,35 rad).
- Die Dauer wird ohne Angabe aus Trajektorienlänge und mittlerer Sollgeschwindigkeit geschätzt (Faktor 1,2 plus 5 s, höchstens 1200 s).

### Verfahren und Konzepte

- [Fahrbahnprofil nach ISO 8608](theory.md#iso8608_road_profile)
- [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](theory.md#runge_kutta)
- [Ablauf eines Simulationsschritts](theory.md#simulation_loop)
- [Stabilitätsbegrenzte Teilschritte (stable_dt)](theory.md#stable_substeps)

## Erweiterungspunkte

- Neuer Löser als Unterklasse von Solver mit _single_step, Eintrag in SOLVERS
- Neue Umgebungsgröße als Feld in Environment (to_dict/from_dict ergänzen)

## Verwandte Module

[vehicle_models](../vehicle_models/index.md), [controllers](../controllers/index.md), [actuators](../actuators/index.md), [powertrain](../powertrain/index.md), [reporting](../reporting/index.md), [trajectory](../trajectory/index.md)

## Hauptquellen

[Butcher (2016)](../references.md#butcher2016), [Hairer et al. (1993)](../references.md#hairer1993), [Hairer und Wanner (1996)](../references.md#hairer1996), [ISO 8608:2016 (2016)](../references.md#iso8608), [Virtanen et al. (2020)](../references.md#virtanen2020)
