# Schnittstellenverträge der AD-Plattform

Verbindliche Verträge zwischen den Paketen der Plattform für automatisierte Fahrfunktionen. Wer eine Komponente schreibt, ob nativ oder als Custom Node, hält sich an diese Ports, Typen und Konventionen. Dann sind Komponenten derselben Ebene austauschbar.

## 1. Ebenen und Ports

Die Ebenen bilden die Wirkkette:

```
ScenarioWorld → Perception → Prediction → Behavior Planning → Trajectory Planning
   → Vehicle Control → Vehicle Dynamics → Actuators → Vehicle Plant → (EgoState zurück)
```

| Ebene (KIND) | Basisklasse (`vdsim.framework.layers`) | Eingänge | Ausgänge |
|---|---|---|---|
| `world` | `ScenarioWorldBase` | `ego: EgoState` | `world: WorldState` |
| `perception` | `PerceptionBase` | `world: WorldState`, `ego: EgoState` | `objects: ObjectList`, `ego_estimate: EgoState` |
| `predictor` | `PredictionBase` | `objects: ObjectList`, `world: WorldState` (optional) | `prediction: Prediction` |
| `behavior_planner` | `BehaviorPlannerBase` | `ego`, `objects`, `prediction`, `world`, `trajectory` (Rückführung) | `behavior: BehaviorCommand` |
| `trajectory_planner` | `TrajectoryPlannerBase` | `ego`, `behavior`, `prediction`, `status: ControllerStatus` (Rückführung) | `trajectory: PlannedTrajectory`, `debug: PlannerDebug` |
| `tracking_controller` | `TrackingControllerBase` | `ego`, `trajectory` | `command: ControlCommand`, `status: ControllerStatus` |
| `vehicle_dynamics` | `VehicleDynamicsBase` | `command`, `ego` | `demand: ActuatorCommand` |
| `actuator` | `ActuatorBase` | `demand`, `ego` | `control: ControlInput` |
| `vehicle_plant` | `VehiclePlantBase` (kein Durchgriff) | `control: ControlInput` | `ego: EgoState` |

### Aufteilung der Fahrzeugebenen

Die Aufteilung folgt der vorgegebenen Kette Vehicle Control → Vehicle Dynamics → Actuators:

- **Vehicle Control** ist die Trajektorienregelung. Sie setzt die Solltrajektorie in δ̇ bzw. δ und F_l bzw. a um.
- **Vehicle Dynamics** ist die Fahrdynamik-Ebene. Sie übernimmt die Split-Range-Längskraftumsetzung (Werling 5.1.2.2) mit Fahrwiderstandskompensation und Integrator mit Anti-Windup. Außerdem verteilt sie Antriebs- und Bremsmomente auf die Räder und bindet optional die Fahrdynamiksysteme ein (ABS, ESP, TV aus `vdsim.controllers`).
- **Actuators** sind Lenkaktor und Antrieb bzw. Bremse. Dazu gehört die Integration von δ̇, die Latenzkette, die Kennlinie und die Ratenbegrenzung (`vdsim.actuators`).
- **Vehicle Plant** ist ein beliebiges Fahrzeugmodell aus `vdsim.core.registry` ("vehicle_model"), das mit Teilschritten integriert wird.

### Rückführungs-Ports

Rückführungs-Ports (`Port(..., feedback=True)`) lesen den Wert des vorherigen Executor-Schritts und brechen so algebraische Schleifen auf. Der Planer liest so die Reinitialisierungsanforderung des Reglers, gemäß der Bi-level-Stabilisierung (Werling 2.3, 4.5).

## 2. Datentypen

Alle Datentypen sind in `vdsim/framework/types.py` definiert und bindend.

- `EgoState`:
  - Positionen beziehen sich auf den Schwerpunkt (CoG).
  - `vx`, `vy` liegen im Fahrzeugsystem.
  - `delta` ist der Radlenkwinkel vorne.
  - `gear` ist ±1.
  - Hilfsfunktionen: `rear_axle(l_h)` und `point_ahead(λ)`.
- `PlannedTrajectory`:
  - Arrays über die **absolute** Zeit `t`.
  - `theta` ist die Bewegungsrichtung, `v ≥ 0` die Bahngeschwindigkeit, `direction` ist ς = ±1.
  - `reference_point` ist `"cog"` (schnelle Fahrt) oder `"rear_axle"` (langsame Fahrt).
  - `lateral_mode` ist `"time"` für d(t) oder `"arc"` für d(s).
  - `sample(t)` liefert einen `TrajectoryPoint` mit `psi`, also der Fahrzeugausrichtung (θ + π bei Rückwärtsfahrt), und `v_signed` = ς·v.
- `BehaviorCommand`:
  - `reference_line` ist eine `vdsim.geometry.ReferenceLine` der Zielspur.
  - `modes` ist eine Liste von `LongitudinalMode` mit den Arten `velocity`, `following`, `merging`, `stopping` (Werling Tab. 3.1).
  - `d_min`, `d_max` bilden die Box-Restriktion für d(t), also den befahrbaren Korridor, den der Fahrzeugumriss nicht verlassen darf.
  - Weitere Felder: `d_ref`, `direction`, `reinit`.
- `ControlCommand`: Die Felder `steer_rate`, `steer_angle`, `force` und `accel` sind optional (None). Die Werling-Regler liefern `steer_rate` und `force`, klassische Regler `steer_angle` und `accel`.
- `ControllerStatus`: invariante Trackingfehler `e_t`, `e_n`, `e_theta` und deren Änderungen, `reinit_request`, `prediction` als Dict mit dem prädizierten Zustand nach 4.5.2, sowie `horizon_x`/`horizon_y` für den MPC-Horizont.
- `PlannerDebug`: unterabgetastete Kandidaten mit Kosten und Status, Kostenaufteilung, Restriktionsverletzungen und Rechenzeit. Wird für Visualisierung und Zeitleiste genutzt.
- Die Typprüfung im Editor nutzt `compatible(out, in)`. Neue Typen kommen über `register_type()` hinzu.

## 3. Komponenten

Basisklasse ist `vdsim.framework.component.Component`. Pflichtattribute:

- `KIND`, `NAME`, `VERSION` (SemVer), `LABEL` (deutsch)
- `INPUTS`, `OUTPUTS`
- `PARAMS` als Dataclass, deren Felder mit `vdsim.core.parameters.param(default, unit, label, min=, max=)` angelegt werden
- `PERIOD` (s), `DOC` (`ComponentDoc`)

Lebenszyklus:

- `reset(context)`: Der `RunContext` enthält `dt`, `seed`, `vehicle` (VehicleConfig), `road` und `rng(name)`.
- `step(t, inputs) -> dict` für alle Komponenten mit Durchgriff.
- `output(t)` und `update(t, inputs, dt)` für Komponenten ohne Durchgriff.

Weitere Regeln:

- **Registrierung:** Dekorator `@component` aus `vdsim.framework.plugins`. Mehrere Versionen dürfen parallel existieren. Ein Paket registriert seine Komponenten in seinem `__init__.py`; `vdsim.framework.plugins.BUILTIN_MODULES` listet die Pakete.
- **Spec-Strings:** `kind/name`, `kind/name@1.2.0`, `kind/name@^1`, außerdem `python:datei.py:Klasse`, `rust:pfad/crate`, `cpp:pfad/ordner` und `matlab:datei.m` (Loader per `register_loader`).
- **Determinismus:** Zufall ausschließlich über `context.rng(name)`, keine Wanduhrzeit in der Logik.
- **Hot Reload:** `get_state()` und `set_state()` übertragen den Zustand auf die neue Instanz.

## 4. Graph-Format (JSON)

```json
{
  "format_version": 1,
  "name": "werling_stack",
  "base_dt": 0.01,
  "nodes": [
    {"id": "planner", "component": "trajectory_planner/werling@^1", "params": {}, "period": 0.1,
     "position": [600, 100]}
  ],
  "connections": [{"from": "plant.ego", "to": "planner.ego"}],
  "metadata": {}
}
```

## 5. Codecs für native Nodes (C++/Rust)

Native Nodes tauschen flache float64-Arrays aus (`types.encode` / `types.decode`):

| Typ | Layout |
|---|---|
| `float`, `bool` | `[v]` |
| `Vector` | Werte |
| `EgoState` | `[t, x, y, psi, vx, vy, r, ax, ay, delta, delta_rate, gear]` |
| `ControlCommand` | `[t, steer_rate, steer_angle, force, accel, direction]`, NaN = nicht gesetzt |
| `PlannedTrajectory` | `[n, direction, ref(0=cog, 1=rear_axle), cost, valid]`, dann n × `[t, x, y, theta, kappa, dkappa, v, a, s, d]` |
| `ObjectList` / `WorldState` | `[n]`, dann n × `[id, type_code, x, y, psi, v, a, length, width]`; Typcodes nach `OBJECT_TYPES` |
| `Prediction` | `[n]`, dann je Objekt `[id, type, length, width, k]` + k × `[t, x, y, psi, v]` |
| `ReferenceLine` | `[n]`, dann n × `[s, x, y, theta, kappa, dkappa]` |

## 6. Konventionen

- **Einheiten und Koordinaten:** SI-Einheiten. Erdfestes System mit x nach Osten, y nach Norden, Winkel mathematisch positiv.
- **Sprache:**
  - Code und Kommentare auf Englisch, wie im bestehenden Code.
  - GUI-Texte, Labels und Dokumentation auf Deutsch.
- **Tests:**
  - liegen in `tests/<paket>/test_<paket>_*.py`, mit eindeutigen Dateinamen und ohne `__init__.py`.
  - Die gemeinsame `tests/conftest.py` setzt `sys.path`, `QT_QPA_PLATFORM=offscreen` und das Agg-Backend.
- **Beispiele:** liegen in `examples/<paket>/`.
- **Dokumentation pro Paket:** Siehe `docs/templates/MODULE_DOCS.md`. Zu jedem Paket gehören:
  - `vdsim/<paket>/docs/module.yaml` mit den Metadaten
  - `vdsim/<paket>/docs/theory.md` mit den Verfahren
  - Referenzen in `docs/references/<thema>.yaml`
- **Rückverfolgbarkeit:** Funktionen, die eine Gleichung umsetzen, erhalten `@trace(quelle, section=, equation=, concept=)` aus `vdsim.framework.knowledge`. Klassen erhalten `DOC = ComponentDoc(...)`.
- **Gemeinsame Dateien** außerhalb des eigenen Pakets ändert nur, wer dafür eingeteilt ist. Andere melden benötigte Änderungen zurück.

## 7. Geschwindigkeitsregime (Werling 3.5.1, 3.5.4, 4.4)

| Regime | Bedingung | Referenzpunkt der Trajektorie | Quermodus | Trackingregler |
|---|---|---|---|---|
| langsam rückwärts | ς = −1 | Hinterachsmitte (`rear_axle`) | d(s) | Lyapunov mit Orientierungsstabilisierung (Satz 4) |
| langsam vorwärts | 0 < v ≤ v_s | Hinterachsmitte (`rear_axle`) | d(s) | Lyapunov ohne Orientierungsstabilisierung (Satz 6, λ ≈ l/2) |
| schnell | v > v_s | Schwerpunkt (`cog`) | d(t) | exakte E/A-Linearisierung (Satz 8) |

- **Schwelle:** v_s = 3.0 m/s ist der Standardwert in Planer und Regler. Der Planer wählt das Regime anhand der Startgeschwindigkeit mit Hysterese ±0.5 m/s und setzt `PlannedTrajectory.reference_point`.
- **Reglerwahl:** Der Regler `werling_bilevel` entscheidet nach `reference_point`. Ist er `rear_axle`, entscheidet das Vorzeichen von v_d bzw. bei v_d = 0 die geplante Fahrtrichtung ς. So bleiben Trajektorie und Regler immer konsistent.

## 8. Szenario-Instanz (Kontext)

Der Runner (`vdsim.ad`) baut aus einer Szenario-Spezifikation eine `ScenarioInstance` (`vdsim.world`). Er legt sie als `context.scenario` und das Straßennetz als `context.road` ab. Die Instanz enthält:

- `road`: das `RoadNetwork`
- `actors`: die Verkehrsteilnehmer
- `ego_initial`: dict mit `x`, `y`, `psi`, `v` (Schwerpunkt)
- `mission`: Route, Zielgeschwindigkeit, Ziel, Erlaubnisse
- `duration`
- `success`: die Erfolgskriterien

## 9. Planer-interne Plugins

Kostenterme (`kind="cost_term"`), Restriktionen (`kind="constraint"`) und Kollisionsprüfer (`kind="collision_checker"`) sind Plugins von `vdsim.planning`. Ihre Basisklassen liegen in `vdsim/planning/cost.py`, `constraints.py` und `collision.py`. Gewichte und Grenzwerte stehen ausschließlich in Parametern, Config-Dateien oder der API, nie hart im Code.
