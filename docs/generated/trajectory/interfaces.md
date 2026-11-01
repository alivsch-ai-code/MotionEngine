# Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

### [Beschleunigen (0-100 km/h)](components/maneuver__acceleration.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/acceleration` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.acceleration` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Bremsen in der Kurve (ISO 7975)](components/maneuver__brake_in_turn.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/brake_in_turn` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.brake_in_turn` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Bremsen (Geradeaus)](components/maneuver__braking.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/braking` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.braking` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Kreisfahrt (ISO 4138)](components/maneuver__circle.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/circle` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.circle` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Stadtverkehr](components/maneuver__city.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/city` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.city` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Kundenspezifischer Testzyklus](components/maneuver__custom.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/custom` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.custom` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Notausweichen](components/maneuver__emergency_evasion.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/emergency_evasion` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.emergency_evasion` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Acht](components/maneuver__figure_eight.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/figure_eight` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.figure_eight` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Frequenzgang (Sinus-Sweep)](components/maneuver__frequency_sweep.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/frequency_sweep` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.frequency_sweep` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Autobahnfahrt](components/maneuver__highway.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/highway` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.highway` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [ISO-Doppelspurwechsel (ISO 3888-1)](components/maneuver__iso_double_lane_change.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/iso_double_lane_change` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.iso_double_lane_change` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [ISO-Ausweichtest (ISO 3888-2)](components/maneuver__iso_obstacle_avoidance.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/iso_obstacle_avoidance` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.iso_obstacle_avoidance` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Spurwechsel](components/maneuver__lane_change.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/lane_change` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.lane_change` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Rennstrecke (Ideallinie)](components/maneuver__race_track.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/race_track` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.race_track` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Lenkwinkelrampe (ISO 4138)](components/maneuver__ramp_steer.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/ramp_steer` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.ramp_steer` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Sinus mit Haltezeit (FMVSS 126)](components/maneuver__sine_with_dwell.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/sine_with_dwell` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.sine_with_dwell` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Slalom](components/maneuver__slalom.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/slalom` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.slalom` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Lenkwinkelsprung (ISO 7401)](components/maneuver__step_steer.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/step_steer` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.step_steer` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [Geradeausfahrt](components/maneuver__straight.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `maneuver/straight` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_generator.straight` |
| Schnittstelle | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [trajectory_loader/csv](components/trajectory_loader__csv.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_loader/csv` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_loader.load_csv` |
| Schnittstelle | – |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [trajectory_loader/gpx](components/trajectory_loader__gpx.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_loader/gpx` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_loader.load_gpx` |
| Schnittstelle | – |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [trajectory_loader/json](components/trajectory_loader__json.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_loader/json` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_loader.load_json` |
| Schnittstelle | – |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [trajectory_loader/matlab](components/trajectory_loader__matlab.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_loader/matlab` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_loader.load_matlab` |
| Schnittstelle | – |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [trajectory_loader/nmea](components/trajectory_loader__nmea.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_loader/nmea` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_loader.load_nmea` |
| Schnittstelle | – |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [trajectory_loader/opendrive](components/trajectory_loader__opendrive.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_loader/opendrive` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_loader.load_xodr` |
| Schnittstelle | – |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

### [trajectory_loader/ros](components/trajectory_loader__ros.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `trajectory_loader/ros` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.trajectory.trajectory_loader.load_ros` |
| Schnittstelle | – |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `path` | `Any` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `trajectory` | `Trajectory` | – | – | – |

## Datentypen

### `Projection`

Ergebnis der Pfadprojektion

Definiert in `vdsim.trajectory.trajectory.Projection`.

| Feld | Typ | Default |
|---|---|---|
| `s` | float | – |
| `index` | int | – |
| `lateral_error` | float | – |
| `heading` | float | – |
| `kappa` | float | – |
| `speed` | float | – |
| `x` | float | – |
| `y` | float | – |

### `Trajectory`

Referenzpfad mit Geschwindigkeitsprofil

Definiert in `vdsim.trajectory.trajectory.Trajectory`.

| Feld | Typ | Default |
|---|---|---|
| `x` | np.ndarray | – |
| `y` | np.ndarray | – |
| `v` | np.ndarray | None |
| `name` | str | '' |
| `cones` | list | field(default_factory=list) |
| `boundaries` | list | field(default_factory=list) |
| `metadata` | dict | field(default_factory=dict) |
| `steer_table` | tuple | None |
| `accel_table` | tuple | None |

## Öffentliche API

### `vdsim.trajectory.opendrive`

| Name | Art | Beschreibung |
|---|---|---|
| [`load_opendrive(path, road_id, lane_id, ds, speed_kmh)`](../../../vdsim/trajectory/opendrive.py#L84) | Funktion | – |

### `vdsim.trajectory.speed_profile`

| Name | Art | Beschreibung |
|---|---|---|
| [`speed_profile(s, kappa, v_max, ay_max, ax_max, ax_min, v_start, v_end)`](../../../vdsim/trajectory/speed_profile.py#L6) | Funktion | – |
| [`lap_time(s, v)`](../../../vdsim/trajectory/speed_profile.py#L29) | Funktion | – |

### `vdsim.trajectory.trajectory`

| Name | Art | Beschreibung |
|---|---|---|
| [`Projection`](../../../vdsim/trajectory/trajectory.py#L15) | Klasse | – |
| [`Trajectory`](../../../vdsim/trajectory/trajectory.py#L27) | Klasse | – |

### `vdsim.trajectory.trajectory_generator`

| Name | Art | Beschreibung |
|---|---|---|
| [`PathBuilder`](../../../vdsim/trajectory/trajectory_generator.py#L31) | Klasse | Path from curvature segments (straight, arc, clothoid, offset); integrated exactly per segment |
| [`maneuver(name, label, category, description, **param_labels)`](../../../vdsim/trajectory/trajectory_generator.py#L22) | Funktion | – |
| [`straight(length, speed_kmh)`](../../../vdsim/trajectory/trajectory_generator.py#L164) | Funktion | – |
| [`lane_change(speed_kmh, width, duration, pre_length, post_length)`](../../../vdsim/trajectory/trajectory_generator.py#L173) | Funktion | – |
| [`iso_double_lane_change(speed_kmh, vehicle_width)`](../../../vdsim/trajectory/trajectory_generator.py#L189) | Funktion | – |
| [`iso_obstacle_avoidance(speed_kmh, vehicle_width)`](../../../vdsim/trajectory/trajectory_generator.py#L204) | Funktion | – |
| [`slalom(speed_kmh, spacing, n_cones, amplitude)`](../../../vdsim/trajectory/trajectory_generator.py#L221) | Funktion | cones at x_i = pre + spacing * (i + 0.5); full lateral amplitude from half a spacing before the first to half a spacing after the last cone, smooth ramps outside |
| [`circle(radius, laps, speed_start_kmh, speed_end_kmh)`](../../../vdsim/trajectory/trajectory_generator.py#L239) | Funktion | – |
| [`figure_eight(radius, speed_kmh, laps)`](../../../vdsim/trajectory/trajectory_generator.py#L250) | Funktion | – |
| [`emergency_evasion(speed_kmh, offset, evade_length, hold_length, return_length)`](../../../vdsim/trajectory/trajectory_generator.py#L263) | Funktion | – |
| [`braking(speed_kmh, deceleration, brake_time)`](../../../vdsim/trajectory/trajectory_generator.py#L275) | Funktion | – |
| [`acceleration(target_kmh, request)`](../../../vdsim/trajectory/trajectory_generator.py#L286) | Funktion | – |
| [`brake_in_turn(radius, speed_kmh, deceleration, brake_time)`](../../../vdsim/trajectory/trajectory_generator.py#L297) | Funktion | – |
| [`step_steer(speed_kmh, steering_wheel_deg, rise_time, duration, steering_ratio)`](../../../vdsim/trajectory/trajectory_generator.py#L321) | Funktion | – |
| [`ramp_steer(speed_kmh, steer_rate_deg, duration, steering_ratio)`](../../../vdsim/trajectory/trajectory_generator.py#L330) | Funktion | – |
| [`sine_with_dwell(speed_kmh, amplitude_deg, frequency, dwell, steering_ratio)`](../../../vdsim/trajectory/trajectory_generator.py#L338) | Funktion | – |
| [`frequency_sweep(speed_kmh, amplitude_deg, f_start, f_end, duration, steering_ratio)`](../../../vdsim/trajectory/trajectory_generator.py#L354) | Funktion | – |
| [`highway(speed_kmh, ay_max)`](../../../vdsim/trajectory/trajectory_generator.py#L367) | Funktion | – |
| [`city(speed_kmh, ay_max)`](../../../vdsim/trajectory/trajectory_generator.py#L380) | Funktion | – |
| [`racing_line(center, width, margin, iterations)`](../../../vdsim/trajectory/trajectory_generator.py#L406) | Funktion | Minimum-curvature line inside the track (linearized least squares with bounds) |
| [`race_track(track_width, ay_max, ax_max, ax_min, v_max_kmh, laps)`](../../../vdsim/trajectory/trajectory_generator.py#L436) | Funktion | – |
| [`custom(segments, ay_max)`](../../../vdsim/trajectory/trajectory_generator.py#L462) | Funktion | – |
| [`generate(name, **params)`](../../../vdsim/trajectory/trajectory_generator.py#L492) | Funktion | – |

### `vdsim.trajectory.trajectory_loader`

| Name | Art | Beschreibung |
|---|---|---|
| [`geodetic_to_local(lat, lon, lat0, lon0)`](../../../vdsim/trajectory/trajectory_loader.py#L17) | Funktion | Equirectangular projection around the first point (accurate for test tracks of a few km) |
| [`load_csv(path, speed, **_)`](../../../vdsim/trajectory/trajectory_loader.py#L41) | Funktion | – |
| [`load_json(path, speed, **_)`](../../../vdsim/trajectory/trajectory_loader.py#L78) | Funktion | – |
| [`load_ros(path, speed, **_)`](../../../vdsim/trajectory/trajectory_loader.py#L110) | Funktion | nav_msgs/Path as YAML (rostopic echo / ros2 topic echo) or JSON |
| [`load_gpx(path, speed, **_)`](../../../vdsim/trajectory/trajectory_loader.py#L121) | Funktion | – |
| [`load_nmea(path, speed, **_)`](../../../vdsim/trajectory/trajectory_loader.py#L142) | Funktion | $GPRMC / $GNRMC sentences (position + speed over ground) |
| [`load_matlab(path, speed, **_)`](../../../vdsim/trajectory/trajectory_loader.py#L160) | Funktion | .mat (v5/v7) with variables x, y[, v] or a struct with these fields, or an N x 2/3 matrix |
| [`load_xodr(path, speed, road_id, lane_id, **_)`](../../../vdsim/trajectory/trajectory_loader.py#L185) | Funktion | – |
| [`load_trajectory(path, speed, **options)`](../../../vdsim/trajectory/trajectory_loader.py#L195) | Funktion | speed (m/s) is used when the file has no speed information |

### `vdsim.trajectory.waypoint_editor`

| Name | Art | Beschreibung |
|---|---|---|
| [`Waypoint`](../../../vdsim/trajectory/waypoint_editor.py#L17) | Klasse | – |
| [`WaypointEditor`](../../../vdsim/trajectory/waypoint_editor.py#L24) | Klasse | – |
