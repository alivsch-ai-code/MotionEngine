# Fahrzeugmodelle – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

### [Einspurmodell kinematisch](components/vehicle_model__bicycle_kinematic.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_model/bicycle_kinematic` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.vehicle_models.bicycle_model.KinematicBicycleModel` |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

### [Einspurmodell linear](components/vehicle_model__bicycle_linear.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_model/bicycle_linear` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.vehicle_models.bicycle_model.LinearBicycleModel` |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

### [Einspurmodell nichtlinear](components/vehicle_model__bicycle_nonlinear.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_model/bicycle_nonlinear` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.vehicle_models.bicycle_model.NonlinearBicycleModel` |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

### [Zweispurmodell (12 Zustände)](components/vehicle_model__double_track.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_model/double_track` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.vehicle_models.double_track_model.DoubleTrackModel` |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

### [Mehrkörpermodell (24 Zustände)](components/vehicle_model__multibody.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_model/multibody` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.vehicle_models.multibody_model.MultibodyModel` |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

### [Dynamisches Einspurmodell, isotroper Reifen (Werling Modell 4)](components/vehicle_model__werling_desm.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_model/werling_desm` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.vehicle_models.werling_models.WerlingDynamicModel` |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

### [Erweitertes kinematisches Einspurmodell (Werling Modell 1)](components/vehicle_model__werling_kesm.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_model/werling_kesm` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.vehicle_models.werling_models.WerlingKinematicModel` |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

## Öffentliche API

### `vdsim.vehicle_models`

| Name | Art | Beschreibung |
|---|---|---|
| [`create_vehicle_model(name, config)`](../../../vdsim/vehicle_models/__init__.py#L22) | Funktion | – |

### `vdsim.vehicle_models.bicycle_model`

| Name | Art | Beschreibung |
|---|---|---|
| [`KinematicBicycleModel`](../../../vdsim/vehicle_models/bicycle_model.py#L36) | Klasse | – |
| [`LinearBicycleModel`](../../../vdsim/vehicle_models/bicycle_model.py#L65) | Klasse | – |
| [`NonlinearBicycleModel`](../../../vdsim/vehicle_models/bicycle_model.py#L121) | Klasse | – |

### `vdsim.vehicle_models.common`

| Name | Art | Beschreibung |
|---|---|---|
| [`aero_drag(vehicle, vx, wind)`](../../../vdsim/vehicle_models/common.py#L8) | Funktion | – |
| [`rolling_resistance(vehicle, vx)`](../../../vdsim/vehicle_models/common.py#L13) | Funktion | – |
| [`wheel_force_request(u, vehicle, vx)`](../../../vdsim/vehicle_models/common.py#L17) | Funktion | Longitudinal force per wheel from drive and brake torques (no wheel dynamics); brakes act against the direction of travel and cannot reverse the vehicle |
| [`axle_cornering_stiffness(tire, fz_tire, delta_alpha)`](../../../vdsim/vehicle_models/common.py#L23) | Funktion | Small-slip cornering stiffness of one axle (two tires) at the given tire load |

### `vdsim.vehicle_models.double_track_model`

| Name | Art | Beschreibung |
|---|---|---|
| [`DoubleTrackModel`](../../../vdsim/vehicle_models/double_track_model.py#L23) | Klasse | – |

### `vdsim.vehicle_models.multibody_model`

| Name | Art | Beschreibung |
|---|---|---|
| [`MultibodyModel`](../../../vdsim/vehicle_models/multibody_model.py#L25) | Klasse | – |

### `vdsim.vehicle_models.werling_models`

| Name | Art | Beschreibung |
|---|---|---|
| [`WerlingParameters`](../../../vdsim/vehicle_models/werling_models.py#L43) | Klasse | vehicle and axle tire parameters of the Werling design models (SI) |
| [`WerlingKinematicModel`](../../../vdsim/vehicle_models/werling_models.py#L197) | Klasse | – |
| [`WerlingDynamicModel`](../../../vdsim/vehicle_models/werling_models.py#L246) | Klasse | – |
| [`werling_parameters(config, mu)`](../../../vdsim/vehicle_models/werling_models.py#L92) | Funktion | WerlingParameters from a VehicleConfig: A = mu F_z,axle, c = A B C = axle cornering stiffness |
| [`slip_angles(vx, vy, r, delta, lv, lh, v_floor)`](../../../vdsim/vehicle_models/werling_models.py#L108) | Funktion | front/rear slip angles; equals (4.45) for vx > 0, physically signed for reverse driving |
| [`desm_forces(vx, vy, r, delta, F_vl, F_hl, P, mode, n, v_floor, mu_v, mu_h, mode_h)`](../../../vdsim/vehicle_models/werling_models.py#L120) | Funktion | Body forces of model 4: returns (Fx, Fy, Mz, info) in vehicle coordinates at the CoG. |
| [`werling_model4(x, delta, F_l, gamma, P, mode, n)`](../../../vdsim/vehicle_models/werling_models.py#L141) | Funktion | Model 4 in the original coordinates x = [x1, x2, psi, r, beta, v] (v > 0), input u = [delta, F_l] |
| [`werling_model1(x, u1, u2, gamma, P)`](../../../vdsim/vehicle_models/werling_models.py#L156) | Funktion | Model 1 (extended KESM), x = [x1, x2, psi, delta, v] of the rear-axle center, u1 = delta_dot, u2 = F_l |
