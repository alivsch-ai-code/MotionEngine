# Trajektorienstabilisierung nach Werling und Fahrzeugebenen – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

### [Lenkaktor und Antrieb/Bremse](components/actuator__steering_powertrain.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `actuator/steering_powertrain`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.vehicle_layers.SteeringPowertrainActuator` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `demand` | `ActuatorCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `control` | `ControlInput` | – | – | – |

### [Abstandsregeltempomat (ACC)](components/tracking_controller__acc.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/acc`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_longitudinal.ACC` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `objects` | `ObjectList` | – | Objekte für das Vorderfahrzeug | optional |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Kombination Quer- + Längsregler](components/tracking_controller__composite.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/composite`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.composite.CompositeController` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `objects` | `ObjectList` | – | Objekte (für ACC) | optional |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Vorsteuerung + Rückführung (längs)](components/tracking_controller__ff_fb.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/ff_fb`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_longitudinal.FeedForwardFeedback` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [LQR (geschwindigkeitsgeplant)](components/tracking_controller__lqr.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/lqr`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_lateral.LQR` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [MPC (linear zeitvariant)](components/tracking_controller__mpc.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/mpc`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_lateral.MPC` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [PI-Geschwindigkeitsregler](components/tracking_controller__pi.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/pi`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_longitudinal.PI` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [PID-Geschwindigkeitsregler](components/tracking_controller__pid.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/pid`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_longitudinal.PID` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Pure Pursuit](components/tracking_controller__pure_pursuit.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/pure_pursuit`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_lateral.PurePursuit` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Fahrzeug-Geschwindigkeitsregler (PI mit Anti-Windup)](components/tracking_controller__speed_pi.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/speed_pi`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_longitudinal.VehicleSpeedController` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Stanley](components/tracking_controller__stanley.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/stanley`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.classic_lateral.Stanley` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Werling: Bi-level-Stabilisierung (Umschaltung + Reinitialisierung)](components/tracking_controller__werling_bilevel.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/werling_bilevel`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.switching.WerlingBilevel` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Werling: exakte E/A-Linearisierung (Satz 8)](components/tracking_controller__werling_dynamic.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/werling_dynamic`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.werling_dynamic.WerlingDynamic` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | Fahrzeugzustand (Schwerpunkt) | – |
| `trajectory` | `PlannedTrajectory` | – | Solltrajektorie des Schwerpunkts | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Werling: Lyapunov ohne Orientierungsstabilisierung (Satz 6)](components/tracking_controller__werling_kinematic_center.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/werling_kinematic_center`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.werling_kinematic.WerlingKinematicCenter` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | Fahrzeugzustand (Schwerpunkt) | – |
| `trajectory` | `PlannedTrajectory` | – | Solltrajektorie der Hinterachsmitte | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Werling: Lyapunov mit Orientierungsstabilisierung (Satz 4)](components/tracking_controller__werling_kinematic_orientation.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tracking_controller/werling_kinematic_orientation`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.werling_kinematic.WerlingKinematicOrientation` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | Fahrzeugzustand (Schwerpunkt) | – |
| `trajectory` | `PlannedTrajectory` | – | Solltrajektorie der Hinterachsmitte | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

### [Split-Range-Längskraftumsetzung (Werling 5.1.2.2)](components/vehicle_dynamics__split_range.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_dynamics/split_range`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.vehicle_layers.SplitRangeDynamics` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `demand` | `ActuatorCommand` | – | – | – |

### [Fahrzeugmodell (vdsim)](components/vehicle_plant__vehicle_model.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `vehicle_plant/vehicle_model`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.stabilization.plant.VehicleModelPlant` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | nein |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `control` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |

## Öffentliche API

### `vdsim.stabilization.classic_lateral`

| Name | Art | Beschreibung |
|---|---|---|
| [`ClassicBase`](../../../vdsim/stabilization/classic_lateral.py#L96) | Klasse | – |
| [`PurePursuitParams`](../../../vdsim/stabilization/classic_lateral.py#L157) | Klasse | – |
| [`PurePursuit`](../../../vdsim/stabilization/classic_lateral.py#L163) | Klasse | – |
| [`StanleyParams`](../../../vdsim/stabilization/classic_lateral.py#L194) | Klasse | – |
| [`Stanley`](../../../vdsim/stabilization/classic_lateral.py#L202) | Klasse | – |
| [`LQRParams`](../../../vdsim/stabilization/classic_lateral.py#L238) | Klasse | – |
| [`LQR`](../../../vdsim/stabilization/classic_lateral.py#L261) | Klasse | – |
| [`MPCParams`](../../../vdsim/stabilization/classic_lateral.py#L340) | Klasse | – |
| [`MPC`](../../../vdsim/stabilization/classic_lateral.py#L353) | Klasse | – |
| [`project(traj, px, py, hint, window)`](../../../vdsim/stabilization/classic_lateral.py#L37) | Funktion | Nearest point of the trajectory polyline: dict(index, s, e_y (left +), theta, kappa, v, a, x, y). |
| [`point_along(traj, index, w, distance)`](../../../vdsim/stabilization/classic_lateral.py#L66) | Funktion | point `distance` further along the polyline from (index, w) |
| [`time_index(traj, t)`](../../../vdsim/stabilization/classic_lateral.py#L84) | Funktion | – |
| [`lateral_error_model(v, P)`](../../../vdsim/stabilization/classic_lateral.py#L250) | Funktion | – |
| [`admm_qp(H, g, A, lo, hi, rho, sigma, alpha, iters, eps, warm)`](../../../vdsim/stabilization/classic_lateral.py#L317) | Funktion | min 1/2 x'Hx + g'x s.t. |

### `vdsim.stabilization.classic_longitudinal`

| Name | Art | Beschreibung |
|---|---|---|
| [`LongitudinalBase`](../../../vdsim/stabilization/classic_longitudinal.py#L35) | Klasse | – |
| [`PIDParams`](../../../vdsim/stabilization/classic_longitudinal.py#L57) | Klasse | – |
| [`PID`](../../../vdsim/stabilization/classic_longitudinal.py#L64) | Klasse | – |
| [`PIParams`](../../../vdsim/stabilization/classic_longitudinal.py#L81) | Klasse | – |
| [`PI`](../../../vdsim/stabilization/classic_longitudinal.py#L87) | Klasse | – |
| [`FFFBParams`](../../../vdsim/stabilization/classic_longitudinal.py#L103) | Klasse | – |
| [`FeedForwardFeedback`](../../../vdsim/stabilization/classic_longitudinal.py#L109) | Klasse | – |
| [`ACCParams`](../../../vdsim/stabilization/classic_longitudinal.py#L124) | Klasse | – |
| [`ACC`](../../../vdsim/stabilization/classic_longitudinal.py#L136) | Klasse | – |
| [`SpeedPIParams`](../../../vdsim/stabilization/classic_longitudinal.py#L194) | Klasse | – |
| [`VehicleSpeedController`](../../../vdsim/stabilization/classic_longitudinal.py#L202) | Klasse | – |

### `vdsim.stabilization.common`

| Name | Art | Beschreibung |
|---|---|---|
| [`Desired`](../../../vdsim/stabilization/common.py#L65) | Klasse | desired values of the reference point in Werling's notation (signed) |
| [`StepTimer`](../../../vdsim/stabilization/common.py#L118) | Klasse | wall-clock time of the controller steps (diagnostics only, never used in the control logic) |
| [`wrap(a)`](../../../vdsim/stabilization/common.py#L26) | Funktion | – |
| [`vehicle_config(context)`](../../../vdsim/stabilization/common.py#L30) | Funktion | – |
| [`environment_mu(context)`](../../../vdsim/stabilization/common.py#L35) | Funktion | – |
| [`design_parameters(context, mu)`](../../../vdsim/stabilization/common.py#L45) | Funktion | WerlingParameters of the vehicle in the context; mu < 0: tire mu times the road base friction |
| [`drive_share(config)`](../../../vdsim/stabilization/common.py#L53) | Funktion | force ratio gamma = F_vl / F_l when driving (Werling 5.1.2.2: front-wheel drive -> 1.0) |
| [`force_ratio(F_l, varsigma, gamma_drive, gamma_brake)`](../../../vdsim/stabilization/common.py#L59) | Funktion | driving when the force acts in the direction of travel, braking otherwise |
| [`desired_from_point(pt)`](../../../vdsim/stabilization/common.py#L82) | Funktion | – |
| [`cog_point_as_rear_axle(pt, lh)`](../../../vdsim/stabilization/common.py#L89) | Funktion | quasi-static conversion of a CoG trajectory point to the rear-axle center (kinematic model, circular motion: sin(beta) = l_h kappa_cog); fallback for "cog" trajectories at very low speed |
| [`sample(traj, t)`](../../../vdsim/stabilization/common.py#L103) | Funktion | – |
| [`hold_command(t, ego, name, varsigma)`](../../../vdsim/stabilization/common.py#L107) | Funktion | no trajectory: keep the steering, brake gently to standstill |
| [`empty_status(t, name)`](../../../vdsim/stabilization/common.py#L113) | Funktion | – |

### `vdsim.stabilization.composite`

| Name | Art | Beschreibung |
|---|---|---|
| [`CompositeParams`](../../../vdsim/stabilization/composite.py#L26) | Klasse | – |
| [`CompositeController`](../../../vdsim/stabilization/composite.py#L34) | Klasse | – |

### `vdsim.stabilization.errors`

| Name | Art | Beschreibung |
|---|---|---|
| [`rear_axle_errors(y1, y2, psi, delta, y1_d, y2_d, psi_d, l)`](../../../vdsim/stabilization/errors.py#L21) | Funktion | – |
| [`rear_axle_error_rates(e_t, e_n, e_psi, v, kappa_delta, v_d, kappa_d)`](../../../vdsim/stabilization/errors.py#L28) | Funktion | – |
| [`taylor_terms(x)`](../../../vdsim/stabilization/errors.py#L35) | Funktion | (cos x - 1)/x, sin x / x, d/dx (cos x - 1)/x, d/dx sin x / x (Taylor series, Werling A.3) |
| [`series_terms(x, switch)`](../../../vdsim/stabilization/errors.py#L44) | Funktion | removable singularities (Remark 5): Taylor series for \|x\| < switch, exact expressions otherwise |
| [`flat_reference_transform(y1_d, y2_d, psi_d, kappa_d, kappa_d_dot, kappa_d_prime, v_d, v_d_dot, lam)`](../../../vdsim/stabilization/errors.py#L53) | Funktion | Desired motion of the point lambda ahead of the rear axle (Satz 5, proof in A.4). |
| [`center_errors(x1, x2, psi, v, delta, ref, lam, l)`](../../../vdsim/stabilization/errors.py#L67) | Funktion | errors of the point lambda ahead of the rear axle w.r.t. |
| [`frenet_errors(px, py, course, speed, ref_x, ref_y, ref_theta, ref_v, ref_kappa)`](../../../vdsim/stabilization/errors.py#L78) | Funktion | errors of a moving point (position, course, speed) w.r.t. |

### `vdsim.stabilization.plant`

| Name | Art | Beschreibung |
|---|---|---|
| [`PlantParams`](../../../vdsim/stabilization/plant.py#L34) | Klasse | – |
| [`VehicleModelPlant`](../../../vdsim/stabilization/plant.py#L47) | Klasse | – |

### `vdsim.stabilization.reinit`

| Name | Art | Beschreibung |
|---|---|---|
| [`ReinitMonitor`](../../../vdsim/stabilization/reinit.py#L23) | Klasse | – |
| [`elliptic_measure(e_t_dot, e_n_dot, c_t, c_n)`](../../../vdsim/stabilization/reinit.py#L19) | Funktion | – |
| [`predict_motion(x0, y0, theta0, v0, theta_dot, v_dot, dt)`](../../../vdsim/stabilization/reinit.py#L65) | Funktion | Taylor series of the motion with constant v_dot and theta_dot (local frame, then rotated back) |
| [`predict_reference_point(ego, P, reference_point, dt, v_switch, direction)`](../../../vdsim/stabilization/reinit.py#L73) | Funktion | Predicted state (dict t, x, y, theta, v, reference_point, ...) of the trajectory reference point. |

### `vdsim.stabilization.simulate`

| Name | Art | Beschreibung |
|---|---|---|
| [`make_context(config, environment, ego_initial, dt, seed)`](../../../vdsim/stabilization/simulate.py#L34) | Funktion | – |
| [`run_closed_loop(controller, trajectory, config, duration, dt, plant, plant_params, dynamics_params, actuator_params, controller_params, environment, ego_initial, provider, on_step)`](../../../vdsim/stabilization/simulate.py#L40) | Funktion | Simulate the full chain; returns (log dict of arrays, components dict). |
| [`run_design_loop(controller, trajectory, config, duration, dt, model, x0, controller_params, environment)`](../../../vdsim/stabilization/simulate.py#L93) | Funktion | Controller on its design model (RK4, zero-order hold); returns the log dict. |
| [`max_abs(a, mask)`](../../../vdsim/stabilization/simulate.py#L146) | Funktion | – |

### `vdsim.stabilization.switching`

| Name | Art | Beschreibung |
|---|---|---|
| [`BilevelParams`](../../../vdsim/stabilization/switching.py#L30) | Klasse | – |
| [`WerlingBilevel`](../../../vdsim/stabilization/switching.py#L60) | Klasse | – |
| [`select_controller(reference_point, direction, v_d, v_min_dynamic, forward_slow)`](../../../vdsim/stabilization/switching.py#L51) | Funktion | – |

### `vdsim.stabilization.trajectories`

| Name | Art | Beschreibung |
|---|---|---|
| [`Path`](../../../vdsim/stabilization/trajectories.py#L24) | Klasse | – |
| [`SpeedProfile`](../../../vdsim/stabilization/trajectories.py#L91) | Klasse | Piecewise smooth speed v(t): knots [(t_i, v_i)], quintic smootherstep between the knots. |
| [`path_from_curvature(kappa_fn, length, ds, x0, y0, theta0)`](../../../vdsim/stabilization/trajectories.py#L39) | Funktion | integrates theta' = kappa, x' = cos theta, y' = sin theta (trapezoidal, fine grid) |
| [`quintic_step(u)`](../../../vdsim/stabilization/trajectories.py#L51) | Funktion | – |
| [`smooth_bump(s, s0, s1, ramp, height)`](../../../vdsim/stabilization/trajectories.py#L56) | Funktion | plateau `height` on [s0, s1] with quintic ramps of length `ramp` (C2 curvature profiles) |
| [`quintic_step_derivatives(u)`](../../../vdsim/stabilization/trajectories.py#L61) | Funktion | – |
| [`path_from_lateral_offset(segments, length, dx, x0, y0)`](../../../vdsim/stabilization/trajectories.py#L67) | Funktion | Path y(x) = sum of quintic offset transitions; segments = [(x_start, x_length, dy), ...]. |
| [`build_trajectory(path, profile, t0, duration, dt, reference_point, direction, s0, lateral_mode)`](../../../vdsim/stabilization/trajectories.py#L129) | Funktion | PlannedTrajectory over absolute time t0 + profile time |
| [`transform_rear_to_point(traj, lam, reference_point)`](../../../vdsim/stabilization/trajectories.py#L142) | Funktion | trajectory of the point lambda ahead of the rear axle for the same kinematic motion (4.20)-(4.24) |
| [`replan_from_prediction(old, prediction, blend_time, dt, horizon)`](../../../vdsim/stabilization/trajectories.py#L164) | Funktion | New trajectory starting at the predicted state that merges back into `old` (stand-in planner). |

### `vdsim.stabilization.vehicle_layers`

| Name | Art | Beschreibung |
|---|---|---|
| [`SplitRangeParams`](../../../vdsim/stabilization/vehicle_layers.py#L35) | Klasse | – |
| [`SplitRangeDynamics`](../../../vdsim/stabilization/vehicle_layers.py#L47) | Klasse | – |
| [`ActuatorParams`](../../../vdsim/stabilization/vehicle_layers.py#L151) | Klasse | – |
| [`SteeringPowertrainActuator`](../../../vdsim/stabilization/vehicle_layers.py#L178) | Klasse | – |

### `vdsim.stabilization.werling_dynamic`

| Name | Art | Beschreibung |
|---|---|---|
| [`ZeroDynamicsReference`](../../../vdsim/stabilization/werling_dynamic.py#L165) | Klasse | Online simulation of a reference vehicle tracking the CoG trajectory exactly (4.71)-(4.74). |
| [`DynamicParams`](../../../vdsim/stabilization/werling_dynamic.py#L223) | Klasse | – |
| [`WerlingDynamic`](../../../vdsim/stabilization/werling_dynamic.py#L249) | Klasse | – |
| [`minimum_phase_bound(P)`](../../../vdsim/stabilization/werling_dynamic.py#L40) | Funktion | Satz 9: the linearized zero dynamics is stable for lambda > max(-l_h, -J/(l_v m)) |
| [`zero_dynamics_coefficients(lam, v_d, P)`](../../../vdsim/stabilization/werling_dynamic.py#L46) | Funktion | p0, p1 of the linearized zero dynamics [psi, r]' = [[0, 1], [-p0, -p1]] [psi, r] and its damping |
| [`lookahead_for_damping(zeta, v_d, P)`](../../../vdsim/stabilization/werling_dynamic.py#L56) | Funktion | lambda(zeta, v_d) for a constant damping ratio of the zero dynamics; NaN if not reachable |
| [`point_kinematics(v, beta, r, lam, v_dot, beta_dot, r_dot)`](../../../vdsim/stabilization/werling_dynamic.py#L66) | Funktion | side slip, speed and their derivatives of the point lambda ahead of the CoG |
| [`solve_linearizing_input(vx, vy, r, lam, a_req, P, gammas, guess, n, tol, max_iter, sat_tol)`](../../../vdsim/stabilization/werling_dynamic.py#L88) | Funktion | Inputs u = [delta, F_l] that produce the required acceleration a_req (vehicle frame) of the point lambda. |
| [`gains_from_poles(p1, p2)`](../../../vdsim/stabilization/werling_dynamic.py#L243) | Funktion | characteristic polynomial (s - p1)(s - p2) = s^2 + k2 s + k1 |

### `vdsim.stabilization.werling_kinematic`

| Name | Art | Beschreibung |
|---|---|---|
| [`OrientationParams`](../../../vdsim/stabilization/werling_kinematic.py#L152) | Klasse | – |
| [`CenterParams`](../../../vdsim/stabilization/werling_kinematic.py#L164) | Klasse | – |
| [`WerlingKinematicOrientation`](../../../vdsim/stabilization/werling_kinematic.py#L221) | Klasse | – |
| [`WerlingKinematicCenter`](../../../vdsim/stabilization/werling_kinematic.py#L258) | Klasse | – |
| [`normalize_angle(a)`](../../../vdsim/stabilization/werling_kinematic.py#L35) | Funktion | – |
| [`kin_tracking_with_orientation_stab(y1_d, y2_d, theta_d, kappa_d, kappa_d_dot, v_d, v_d_dot, varsigma, y1, y2, psi, v, delta, l_v, l_h, m, J, gam, k1, k2, k3, k4)`](../../../vdsim/stabilization/werling_kinematic.py#L41) | Funktion | y1_d, ..., varsigma: desired values in rear axle coordinates y1, ..., delta: measured states l_v, ..., gam: vehicular parameters k1, ..., k4: control design parameters |
| [`force_from_acceleration(w2, u1, v, delta, P, varsigma, gamma_drive, gamma_brake)`](../../../vdsim/stabilization/werling_kinematic.py#L85) | Funktion | inverse input substitution (4.7); gamma follows from the sign of the force (drive / brake) |
| [`orientation_law(d, x1, x2, psi, v, delta, P, k1, k2, k3, k4, gamma_drive, gamma_brake, switch)`](../../../vdsim/stabilization/werling_kinematic.py#L95) | Funktion | Lyapunov tracking with orientation stabilization of the rear-axle center (Satz 4). |
| [`center_law(d, x1, x2, psi, v, delta, P, k1, k3, k4, lam, gamma_drive, gamma_brake, switch, sign_variant)`](../../../vdsim/stabilization/werling_kinematic.py#L124) | Funktion | Lyapunov tracking of the point lambda ahead of the rear axle without orientation stabilization (Satz 6). |
