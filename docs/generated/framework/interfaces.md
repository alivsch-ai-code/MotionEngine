# Komponenten-Framework der AD-Plattform – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Datentypen

### `ActuatorCommand`

Radindividuelle Stellanforderungen

Definiert in `vdsim.framework.types.ActuatorCommand`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `steer_angle` | float | 0.0 |
| `steer_rate` | float | 0.0 |
| `steer_rear` | float | 0.0 |
| `drive_torque` | np.ndarray | array([0., 0., 0., 0.]) |
| `brake_torque` | np.ndarray | array([0., 0., 0., 0.]) |
| `info` | dict | {} |

### `BehaviorCommand`

Vorgaben der Verhaltensebene (Referenzkurve, Längsmodi, Korridor)

Definiert in `vdsim.framework.types.BehaviorCommand`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `reference_line` | Any | None |
| `lane_id` | str \| None | None |
| `target_speed` | float | 0.0 |
| `modes` | list | [] |
| `d_ref` | float | 0.0 |
| `d_min` | float | -1000000000.0 |
| `d_max` | float | 1000000000.0 |
| `direction` | int | 1 |
| `reinit` | bool | False |
| `maneuver` | str | 'lane_keeping' |
| `info` | dict | {} |

### `ControlCommand`

Stellgrößen der Trajektorienregelung

Definiert in `vdsim.framework.types.ControlCommand`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `steer_rate` | float \| None | None |
| `steer_angle` | float \| None | None |
| `force` | float \| None | None |
| `accel` | float \| None | None |
| `direction` | int | 1 |
| `controller` | str | '' |
| `info` | dict | {} |

### `ControllerStatus`

Trackingfehler und Reinitialisierungsanforderung

Definiert in `vdsim.framework.types.ControllerStatus`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `e_t` | float | 0.0 |
| `e_n` | float | 0.0 |
| `e_theta` | float | 0.0 |
| `e_v` | float | 0.0 |
| `e_t_dot` | float | 0.0 |
| `e_n_dot` | float | 0.0 |
| `reinit_request` | bool | False |
| `active_controller` | str | '' |
| `lookahead` | float | 0.0 |
| `prediction` | Any | None |
| `info` | dict | {} |
| `horizon_x` | np.ndarray \| None | None |
| `horizon_y` | np.ndarray \| None | None |

### `EgoState`

Fahrzeugzustand im Schwerpunkt

Definiert in `vdsim.framework.types.EgoState`.

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
| `delta` | float | 0.0 |
| `delta_rate` | float | 0.0 |
| `gear` | int | 1 |

### `ObjectList`

erkannte Objekte

Definiert in `vdsim.framework.types.ObjectList`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `objects` | list | [] |

### `PlannedTrajectory`

Solltrajektorie

Definiert in `vdsim.framework.types.PlannedTrajectory`.

| Feld | Typ | Default |
|---|---|---|
| `t` | np.ndarray | array([], dtype=float64) |
| `x` | np.ndarray | array([], dtype=float64) |
| `y` | np.ndarray | array([], dtype=float64) |
| `theta` | np.ndarray | array([], dtype=float64) |
| `kappa` | np.ndarray | array([], dtype=float64) |
| `dkappa` | np.ndarray | array([], dtype=float64) |
| `v` | np.ndarray | array([], dtype=float64) |
| `a` | np.ndarray | array([], dtype=float64) |
| `s` | np.ndarray | array([], dtype=float64) |
| `d` | np.ndarray | array([], dtype=float64) |
| `direction` | int | 1 |
| `reference_point` | str | 'cog' |
| `lateral_mode` | str | 'time' |
| `longitudinal_mode` | str | 'velocity' |
| `cost` | float | 0.0 |
| `valid` | bool | True |
| `reinitialized` | bool | False |
| `plan` | Any | None |
| `reference_line` | Any | None |
| `metadata` | dict | {} |

### `PlannerDebug`

Planer-Momentaufnahme (Kandidaten, Kosten, Restriktionen)

Definiert in `vdsim.framework.types.PlannerDebug`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `start_state` | dict | {} |
| `candidates_x` | np.ndarray | array([], shape=(0, 0), dtype=float32) |
| `candidates_y` | np.ndarray | array([], shape=(0, 0), dtype=float32) |
| `candidates_s` | np.ndarray | array([], shape=(0, 0), dtype=float32) |
| `candidates_d` | np.ndarray | array([], shape=(0, 0), dtype=float32) |
| `candidates_cost` | np.ndarray | array([], dtype=float64) |
| `candidates_status` | np.ndarray | array([], dtype=int8) |
| `candidates_reason` | list | [] |
| `best_index` | int | -1 |
| `cost_terms` | dict | {} |
| `constraint_violations` | dict | {} |
| `n_candidates` | int | 0 |
| `n_checked` | int | 0 |
| `mode` | str | '' |
| `modes` | dict | {} |
| `reinitialized` | bool | False |
| `fallback` | bool | False |
| `compute_time` | float | 0.0 |
| `collision_circles` | dict | {} |
| `info` | dict | {} |

### `Prediction`

prädizierte Objekttrajektorien

Definiert in `vdsim.framework.types.Prediction`.

| Feld | Typ | Default |
|---|---|---|
| `t0` | float | 0.0 |
| `objects` | list | [] |

### `WorldState`

Ground Truth der Szenario-Engine

Definiert in `vdsim.framework.types.WorldState`.

| Feld | Typ | Default |
|---|---|---|
| `t` | float | 0.0 |
| `objects` | list | [] |
| `road` | Any | None |
| `traffic_lights` | dict | {} |
| `collision` | bool | False |
| `collision_with` | int \| None | None |
| `off_road` | bool | False |
| `events` | list | [] |
| `info` | dict | {} |

## Öffentliche API

### `vdsim.framework.component`

| Name | Art | Beschreibung |
|---|---|---|
| [`Port`](../../../vdsim/framework/component.py#L35) | Klasse | – |
| [`NoParams`](../../../vdsim/framework/component.py#L55) | Klasse | – |
| [`Component`](../../../vdsim/framework/component.py#L59) | Klasse | – |
| [`params_schema(p_cls)`](../../../vdsim/framework/component.py#L154) | Funktion | GUI/API description of a parameter dataclass (label, unit, limits from field metadata) |
| [`params_from_dict(p_cls, data)`](../../../vdsim/framework/component.py#L169) | Funktion | – |
| [`set_param(p, dotted, value)`](../../../vdsim/framework/component.py#L176) | Funktion | "cost.k_jerk" style access into nested parameter dataclasses |
| [`params_to_dict(p)`](../../../vdsim/framework/component.py#L199) | Funktion | – |

### `vdsim.framework.container`

| Name | Art | Beschreibung |
|---|---|---|
| [`Container`](../../../vdsim/framework/container.py#L16) | Klasse | – |

### `vdsim.framework.context`

| Name | Art | Beschreibung |
|---|---|---|
| [`RunContext`](../../../vdsim/framework/context.py#L26) | Klasse | – |
| [`stable_seed(*parts)`](../../../vdsim/framework/context.py#L19) | Funktion | Deterministic 32 bit seed from strings/ints (independent of PYTHONHASHSEED) |

### `vdsim.framework.knowledge`

| Name | Art | Beschreibung |
|---|---|---|
| [`ComponentDoc`](../../../vdsim/framework/knowledge.py#L23) | Klasse | – |
| [`trace(source, section, equation, concept, note)`](../../../vdsim/framework/knowledge.py#L41) | Funktion | Decorator linking a function/class to its conceptual origin |
| [`traces_for(module_prefix)`](../../../vdsim/framework/knowledge.py#L56) | Funktion | – |
| [`doc_of(obj)`](../../../vdsim/framework/knowledge.py#L60) | Funktion | ComponentDoc of a class/instance (empty doc if none is declared) |
| [`wraps_trace(func)`](../../../vdsim/framework/knowledge.py#L66) | Funktion | helper for decorators that wrap traced functions |

### `vdsim.framework.layers`

| Name | Art | Beschreibung |
|---|---|---|
| [`ScenarioWorldBase`](../../../vdsim/framework/layers.py#L13) | Klasse | – |
| [`PerceptionBase`](../../../vdsim/framework/layers.py#L19) | Klasse | – |
| [`PredictionBase`](../../../vdsim/framework/layers.py#L25) | Klasse | – |
| [`BehaviorPlannerBase`](../../../vdsim/framework/layers.py#L31) | Klasse | – |
| [`TrajectoryPlannerBase`](../../../vdsim/framework/layers.py#L40) | Klasse | – |
| [`TrackingControllerBase`](../../../vdsim/framework/layers.py#L47) | Klasse | – |
| [`VehicleDynamicsBase`](../../../vdsim/framework/layers.py#L53) | Klasse | – |
| [`ActuatorBase`](../../../vdsim/framework/layers.py#L59) | Klasse | – |
| [`VehiclePlantBase`](../../../vdsim/framework/layers.py#L65) | Klasse | – |

### `vdsim.framework.plugins`

| Name | Art | Beschreibung |
|---|---|---|
| [`parse_version(text)`](../../../vdsim/framework/plugins.py#L46) | Funktion | – |
| [`version_matches(version, constraint)`](../../../vdsim/framework/plugins.py#L51) | Funktion | – |
| [`component(kind, name, version)`](../../../vdsim/framework/plugins.py#L66) | Funktion | Class decorator registering a Component subclass |
| [`unregister(kind, name, version)`](../../../vdsim/framework/plugins.py#L79) | Funktion | – |
| [`register_loader(prefix, loader)`](../../../vdsim/framework/plugins.py#L86) | Funktion | loader(path_spec: str, params: dict \| None) -> Component instance |
| [`load_builtins()`](../../../vdsim/framework/plugins.py#L91) | Funktion | – |
| [`split_spec(spec)`](../../../vdsim/framework/plugins.py#L108) | Funktion | "kind/name@constraint" -> (kind, name, constraint) |
| [`get_component(spec_or_kind, name, version)`](../../../vdsim/framework/plugins.py#L118) | Funktion | – |
| [`create_component(spec, params, **overrides)`](../../../vdsim/framework/plugins.py#L134) | Funktion | Instantiate a component from a spec string (native or custom node) |
| [`available_components(kind)`](../../../vdsim/framework/plugins.py#L144) | Funktion | list of describe() dicts, newest version first per component |
| [`component_kinds()`](../../../vdsim/framework/plugins.py#L156) | Funktion | – |
| [`versions_of(kind, name)`](../../../vdsim/framework/plugins.py#L161) | Funktion | – |

### `vdsim.framework.provenance`

| Name | Art | Beschreibung |
|---|---|---|
| [`config_hash(obj)`](../../../vdsim/framework/provenance.py#L14) | Funktion | – |
| [`manifest(config, components, seed)`](../../../vdsim/framework/provenance.py#L27) | Funktion | – |

### `vdsim.framework.types`

| Name | Art | Beschreibung |
|---|---|---|
| [`EgoState`](../../../vdsim/framework/types.py#L27) | Klasse | – |
| [`ObjectState`](../../../vdsim/framework/types.py#L76) | Klasse | – |
| [`ObjectList`](../../../vdsim/framework/types.py#L93) | Klasse | – |
| [`PredictedObject`](../../../vdsim/framework/types.py#L105) | Klasse | predicted motion of one object; arrays share the time base t (absolute time) |
| [`Prediction`](../../../vdsim/framework/types.py#L131) | Klasse | – |
| [`LongitudinalMode`](../../../vdsim/framework/types.py#L147) | Klasse | One active longitudinal operating mode (Werling Tab. |
| [`BehaviorCommand`](../../../vdsim/framework/types.py#L158) | Klasse | – |
| [`TrajectoryPoint`](../../../vdsim/framework/types.py#L178) | Klasse | – |
| [`PlannedTrajectory`](../../../vdsim/framework/types.py#L207) | Klasse | – |
| [`PlannerDebug`](../../../vdsim/framework/types.py#L282) | Klasse | Snapshot of one planning cycle for visualization / analysis (kept small: subsampled candidates) |
| [`ControlCommand`](../../../vdsim/framework/types.py#L309) | Klasse | Output of the trajectory tracking controller. |
| [`ControllerStatus`](../../../vdsim/framework/types.py#L322) | Klasse | Invariant tracking errors and the re-initialization request (bi-level stabilization, Werling 2.3/4.5) |
| [`ActuatorCommand`](../../../vdsim/framework/types.py#L341) | Klasse | Wheel-level demands produced by the vehicle-dynamics layer |
| [`WorldState`](../../../vdsim/framework/types.py#L353) | Klasse | Ground truth produced by the scenario engine |
| [`register_type(name, py_type, description, color)`](../../../vdsim/framework/types.py#L415) | Funktion | Plugins may add their own signal types (custom nodes with new interfaces) |
| [`compatible(output_type, input_type)`](../../../vdsim/framework/types.py#L422) | Funktion | Data type check of a connection output -> input |
| [`check_value(type_name, value)`](../../../vdsim/framework/types.py#L433) | Funktion | Runtime check of a value against a port type (used by the debugger / custom nodes) |
| [`summarize(value, max_len)`](../../../vdsim/framework/types.py#L445) | Funktion | Short human-readable description of a signal value (live wire labels, tooltips) |
| [`encode(type_name, value)`](../../../vdsim/framework/types.py#L484) | Funktion | Python value -> flat float64 array (layout documented in docs/specs/contracts.md) |
| [`decode(type_name, arr)`](../../../vdsim/framework/types.py#L520) | Funktion | flat float64 array -> Python value |
