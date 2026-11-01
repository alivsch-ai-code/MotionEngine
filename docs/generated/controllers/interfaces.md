# Regler, Fahrerassistenz und Fahrwerksregelsysteme – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

### [ABS](components/chassis_system__abs.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `chassis_system/abs` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.slip_control.AntiLockBraking` |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

### [Aktive Dämpfung (Skyhook)](components/chassis_system__active_damping.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `chassis_system/active_damping` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.active_suspension.SkyhookDamping` |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

### [Aktive Wankstabilisierung](components/chassis_system__active_roll.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `chassis_system/active_roll` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.active_suspension.ActiveRollStabilization` |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

### [ESP](components/chassis_system__esp.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `chassis_system/esp` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.esp_controller.ElectronicStabilityProgram` |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

### [Hinterachslenkung](components/chassis_system__rear_steering.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `chassis_system/rear_steering` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.rear_axle_steering.RearAxleSteering` |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

### [Antriebsschlupfregelung (ASR/TCS)](components/chassis_system__tcs.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `chassis_system/tcs` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.slip_control.TractionControl` |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

### [Torque Vectoring](components/chassis_system__torque_vectoring.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `chassis_system/torque_vectoring` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.torque_vectoring.TorqueVectoring` |
| Schnittstelle | `vdsim.core.interfaces.ChassisSystem` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `u` | `ControlInput` | – | – | – |

### [Krümmungsvorsteuerung (ohne Rückführung)](components/lateral_controller__curvature_feedforward.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `lateral_controller/curvature_feedforward` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.open_loop.CurvatureFeedforward` |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

### [Spurhalteassistent (LKA)](components/lateral_controller__lane_keeping.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `lateral_controller/lane_keeping` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.lane_keeping.LaneKeepingAssist` |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

### [MPC](components/lateral_controller__mpc.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `lateral_controller/mpc` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.mpc_controller.MPCController` |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

### [Lenkung nach Tabelle (open loop)](components/lateral_controller__open_loop.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `lateral_controller/open_loop` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.open_loop.OpenLoopSteering` |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

### [Pure Pursuit](components/lateral_controller__pure_pursuit.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `lateral_controller/pure_pursuit` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.pure_pursuit.PurePursuitController` |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

### [Stanley](components/lateral_controller__stanley.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `lateral_controller/stanley` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.stanley_controller.StanleyController` |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

### [Abstandsregeltempomat (ACC)](components/longitudinal_controller__acc.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `longitudinal_controller/acc` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.speed_controller.AdaptiveCruiseControl` |
| Schnittstelle | `vdsim.core.interfaces.LongitudinalController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `acceleration` | `float` | – | Beschleunigungsanforderung in m/s² | – |

### [Notbremsassistent (AEB)](components/longitudinal_controller__aeb.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `longitudinal_controller/aeb` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.speed_controller.EmergencyBrakeAssist` |
| Schnittstelle | `vdsim.core.interfaces.LongitudinalController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `acceleration` | `float` | – | Beschleunigungsanforderung in m/s² | – |

### [Geschwindigkeitsregler (PI)](components/longitudinal_controller__speed_pi.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `longitudinal_controller/speed_pi` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.controllers.speed_controller.SpeedController` |
| Schnittstelle | `vdsim.core.interfaces.LongitudinalController` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `acceleration` | `float` | – | Beschleunigungsanforderung in m/s² | – |

## Öffentliche API

### `vdsim.controllers.active_suspension`

| Name | Art | Beschreibung |
|---|---|---|
| [`ActiveRollStabilization`](../../../vdsim/controllers/active_suspension.py#L10) | Klasse | counteracts the roll moment of the lateral acceleration (gain 1 = full compensation) |
| [`SkyhookDamping`](../../../vdsim/controllers/active_suspension.py#L31) | Klasse | skyhook: damper force proportional to the absolute body velocity at each corner |

### `vdsim.controllers.chassis_systems`

| Name | Art | Beschreibung |
|---|---|---|
| [`enabled_systems(config)`](../../../vdsim/controllers/chassis_systems.py#L10) | Funktion | names of the chassis systems switched on in the vehicle configuration, in execution order |

### `vdsim.controllers.curvature_feedback`

| Name | Art | Beschreibung |
|---|---|---|
| [`CurvatureCorrection`](../../../vdsim/controllers/curvature_feedback.py#L4) | Klasse | Estimates the factor g = k_measured / k_expected and sends k_des / g. |

### `vdsim.controllers.esp_controller`

| Name | Art | Beschreibung |
|---|---|---|
| [`ElectronicStabilityProgram`](../../../vdsim/controllers/esp_controller.py#L33) | Klasse | yaw-rate control by single-wheel braking (oversteer: outer front, understeer: inner rear) |
| [`understeer_gradient(config)`](../../../vdsim/controllers/esp_controller.py#L12) | Funktion | rad/(m/s^2) from the linear single-track model at static loads |
| [`reference_yaw_rate(config, speed, steer, mu, eg)`](../../../vdsim/controllers/esp_controller.py#L22) | Funktion | steady-state yaw rate of the linear model, limited by the friction (0.85 mu g / v) |

### `vdsim.controllers.lane_keeping`

| Name | Art | Beschreibung |
|---|---|---|
| [`LaneKeepingAssist`](../../../vdsim/controllers/lane_keeping.py#L17) | Klasse | – |

### `vdsim.controllers.mpc_controller`

| Name | Art | Beschreibung |
|---|---|---|
| [`MPCController`](../../../vdsim/controllers/mpc_controller.py#L20) | Klasse | – |

### `vdsim.controllers.open_loop`

| Name | Art | Beschreibung |
|---|---|---|
| [`OpenLoopSteering`](../../../vdsim/controllers/open_loop.py#L11) | Klasse | – |
| [`CurvatureFeedforward`](../../../vdsim/controllers/open_loop.py#L26) | Klasse | Steers the kinematic angle of the path curvature at the current position, no feedback |

### `vdsim.controllers.path_tracking`

| Name | Art | Beschreibung |
|---|---|---|
| [`wrap(angle)`](../../../vdsim/controllers/path_tracking.py#L6) | Funktion | – |
| [`axle_point(state, distance)`](../../../vdsim/controllers/path_tracking.py#L10) | Funktion | point on the vehicle axis `distance` ahead of the CG (negative = behind) |
| [`clip_steer(delta, config)`](../../../vdsim/controllers/path_tracking.py#L15) | Funktion | – |

### `vdsim.controllers.pure_pursuit`

| Name | Art | Beschreibung |
|---|---|---|
| [`PurePursuitController`](../../../vdsim/controllers/pure_pursuit.py#L11) | Klasse | – |

### `vdsim.controllers.rear_axle_steering`

| Name | Art | Beschreibung |
|---|---|---|
| [`RearAxleSteering`](../../../vdsim/controllers/rear_axle_steering.py#L10) | Klasse | speed-dependent ratio: counter-phase at low speed (agility), in-phase at high speed (stability) |

### `vdsim.controllers.slip_control`

| Name | Art | Beschreibung |
|---|---|---|
| [`AntiLockBraking`](../../../vdsim/controllers/slip_control.py#L29) | Klasse | – |
| [`TractionControl`](../../../vdsim/controllers/slip_control.py#L45) | Klasse | – |

### `vdsim.controllers.speed_controller`

| Name | Art | Beschreibung |
|---|---|---|
| [`SpeedController`](../../../vdsim/controllers/speed_controller.py#L10) | Klasse | – |
| [`AdaptiveCruiseControl`](../../../vdsim/controllers/speed_controller.py#L55) | Klasse | – |
| [`EmergencyBrakeAssist`](../../../vdsim/controllers/speed_controller.py#L86) | Klasse | Time-to-collision based staged braking on top of a base longitudinal controller |

### `vdsim.controllers.stanley_controller`

| Name | Art | Beschreibung |
|---|---|---|
| [`StanleyController`](../../../vdsim/controllers/stanley_controller.py#L17) | Klasse | – |

### `vdsim.controllers.torque_vectoring`

| Name | Art | Beschreibung |
|---|---|---|
| [`TorqueVectoring`](../../../vdsim/controllers/torque_vectoring.py#L11) | Klasse | yaw moment from left/right drive-torque difference on the driven axles |
