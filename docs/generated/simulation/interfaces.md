# Simulationskern – Löser, Regelkreis, Szenarien, Ergebnisse – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Datentypen

### `ControlInput`

an der Strecke wirksame Stellgrößen

Definiert in `vdsim.simulation.vehicle_state.ControlInput`.

| Feld | Typ | Default |
|---|---|---|
| `steer_front` | <class 'float'> | 0.0 |
| `steer_rear` | <class 'float'> | 0.0 |
| `drive_torque` | <class 'numpy.ndarray'> | array([0., 0., 0., 0.]) |
| `brake_torque` | <class 'numpy.ndarray'> | array([0., 0., 0., 0.]) |
| `roll_moment` | <class 'float'> | 0.0 |
| `damper_force` | <class 'numpy.ndarray'> | array([0., 0., 0., 0.]) |

### `Environment`

Reibwertkarte, Fahrbahn, Wind, Verkehr

Definiert in `vdsim.simulation.environment.Environment`.

| Feld | Typ | Default |
|---|---|---|
| `friction` | FrictionMap | field(default_factory=FrictionMap) |
| `wind_speed` | float | 0.0 |
| `road` | RoadProfile | field(default_factory=RoadProfile) |
| `lead_vehicle` | LeadVehicle | None |

### `SimulationResult`

Zeitreihen und Metadaten eines Laufs

Definiert in `vdsim.simulation.results.SimulationResult`.

### `VehicleState`

modellunabhängiger Fahrzeugzustand (klassischer Simulator)

Definiert in `vdsim.simulation.vehicle_state.VehicleState`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `x` | float | 0.0 |
| `y` | float | 0.0 |
| `psi` | float | 0.0 |
| `vx` | float | 0.0 |
| `vy` | float | 0.0 |
| `r` | float | 0.0 |
| `ax` | float | 0.0 |
| `ay` | float | 0.0 |
| `delta_f` | float | 0.0 |
| `delta_r` | float | 0.0 |
| `roll` | float | 0.0 |
| `roll_rate` | float | 0.0 |
| `pitch` | float | 0.0 |
| `pitch_rate` | float | 0.0 |
| `heave` | float | 0.0 |
| `heave_rate` | float | 0.0 |
| `wheel_speed` | np.ndarray | field(default_factory=_zeros4) |
| `slip_ratio` | np.ndarray | field(default_factory=_zeros4) |
| `slip_angle` | np.ndarray | field(default_factory=_zeros4) |
| `fx` | np.ndarray | field(default_factory=_zeros4) |
| `fy` | np.ndarray | field(default_factory=_zeros4) |
| `fz` | np.ndarray | field(default_factory=_zeros4) |
| `mu` | np.ndarray | field(default_factory=lambda : np.ones(4)) |

## Öffentliche API

### `vdsim.simulation.environment`

| Name | Art | Beschreibung |
|---|---|---|
| [`FrictionPatch`](../../../vdsim/simulation/environment.py#L9) | Klasse | Rectangular area with its own friction coefficient (later patches override earlier ones) |
| [`FrictionMap`](../../../vdsim/simulation/environment.py#L20) | Klasse | Road friction factor relative to dry asphalt (1.0); multiplied with the tire's mu |
| [`RoadProfile`](../../../vdsim/simulation/environment.py#L80) | Klasse | Road height z(x): discrete bumps plus optional ISO 8608 random roughness |
| [`LeadVehicle`](../../../vdsim/simulation/environment.py#L121) | Klasse | Vehicle driving ahead on the same path; speed given as a (time, speed) table |
| [`Environment`](../../../vdsim/simulation/environment.py#L137) | Klasse | – |
| [`iso8608_profile(roughness_class, length, dx, seed)`](../../../vdsim/simulation/environment.py#L108) | Funktion | Random road profile from the ISO 8608 displacement PSD Gd(n) = Gd(n0) (n/n0)^-2, n0 = 0.1 cycles/m |

### `vdsim.simulation.results`

| Name | Art | Beschreibung |
|---|---|---|
| [`SimulationResult`](../../../vdsim/simulation/results.py#L11) | Klasse | – |

### `vdsim.simulation.scenario`

| Name | Art | Beschreibung |
|---|---|---|
| [`Scenario`](../../../vdsim/simulation/scenario.py#L16) | Klasse | – |
| [`ScenarioManager`](../../../vdsim/simulation/scenario.py#L81) | Klasse | – |

### `vdsim.simulation.simulator`

| Name | Art | Beschreibung |
|---|---|---|
| [`Simulator`](../../../vdsim/simulation/simulator.py#L29) | Klasse | – |
| [`run_scenario(scenario, progress)`](../../../vdsim/simulation/simulator.py#L207) | Funktion | – |

### `vdsim.simulation.solver`

| Name | Art | Beschreibung |
|---|---|---|
| [`Solver`](../../../vdsim/simulation/solver.py#L6) | Klasse | – |
| [`EulerSolver`](../../../vdsim/simulation/solver.py#L25) | Klasse | – |
| [`HeunSolver`](../../../vdsim/simulation/solver.py#L32) | Klasse | – |
| [`RK4Solver`](../../../vdsim/simulation/solver.py#L41) | Klasse | – |
| [`AdaptiveSolver`](../../../vdsim/simulation/solver.py#L52) | Klasse | scipy solve_ivp (RK45/LSODA) over each step; accurate reference, slower |
| [`create_solver(name, substeps)`](../../../vdsim/simulation/solver.py#L68) | Funktion | – |

### `vdsim.simulation.vehicle_state`

| Name | Art | Beschreibung |
|---|---|---|
| [`VehicleState`](../../../vdsim/simulation/vehicle_state.py#L13) | Klasse | Common, model-independent view of the vehicle (earth frame position, vehicle frame velocities) |
| [`ControlInput`](../../../vdsim/simulation/vehicle_state.py#L56) | Klasse | – |
