# world – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.world` gibt es noch keine handgeschriebene Dokumentation (`vdsim/world/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init world`


## Komponenten

### [Szenario-Engine](components/world__scenario_engine.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `world/scenario_engine`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.world.engine.ScenarioEngine` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | wahrer Fahrzeugzustand | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `world` | `WorldState` | – | Ground Truth | – |

## Öffentliche API

### `vdsim.world.actors`

| Name | Art | Beschreibung |
|---|---|---|
| [`Trigger`](../../../vdsim/world/actors.py#L39) | Klasse | – |
| [`ScriptAction`](../../../vdsim/world/actors.py#L84) | Klasse | – |
| [`Actor`](../../../vdsim/world/actors.py#L105) | Klasse | – |
| [`LaneVehicle`](../../../vdsim/world/actors.py#L161) | Klasse | – |
| [`Truck`](../../../vdsim/world/actors.py#L355) | Klasse | – |
| [`Cyclist`](../../../vdsim/world/actors.py#L364) | Klasse | – |
| [`Pedestrian`](../../../vdsim/world/actors.py#L373) | Klasse | – |
| [`StaticObstacle`](../../../vdsim/world/actors.py#L422) | Klasse | – |
| [`TrafficSimulator`](../../../vdsim/world/actors.py#L453) | Klasse | – |
| [`project_near(lane, x, y, s_guess, window)`](../../../vdsim/world/actors.py#L758) | Funktion | projection onto a lane with a sample-index hint (cheap for long lanes) |
| [`clone_actors(actors)`](../../../vdsim/world/actors.py#L765) | Funktion | – |

### `vdsim.world.collision`

| Name | Art | Beschreibung |
|---|---|---|
| [`rect_corners(x, y, psi, length, width)`](../../../vdsim/world/collision.py#L14) | Funktion | corners (N, 4, 2) of rectangles centered at (x, y) with orientation psi |
| [`sat_overlap(a, b)`](../../../vdsim/world/collision.py#L28) | Funktion | a: (4, 2) corners of one rectangle, b: (N, 4, 2) corners of N rectangles -> bool array (N,) |
| [`collisions(x, y, psi, length, width, objects, margin)`](../../../vdsim/world/collision.py#L47) | Funktion | ids of objects (ObjectState-like) overlapping the rectangle (x, y, psi, length, width) |
| [`pairwise_collisions(objects)`](../../../vdsim/world/collision.py#L65) | Funktion | all colliding pairs (id_a, id_b) among the objects (O(N^2) prefilter by distance) |

### `vdsim.world.ego_stub`

| Name | Art | Beschreibung |
|---|---|---|
| [`KinematicEgoStub`](../../../vdsim/world/ego_stub.py#L17) | Klasse | – |

### `vdsim.world.engine`

| Name | Art | Beschreibung |
|---|---|---|
| [`ScenarioEngineParams`](../../../vdsim/world/engine.py#L25) | Klasse | – |
| [`ScenarioEngine`](../../../vdsim/world/engine.py#L37) | Klasse | – |

### `vdsim.world.render`

| Name | Art | Beschreibung |
|---|---|---|
| [`draw_road(ax, road, t, centerlines, zorder)`](../../../vdsim/world/render.py#L28) | Funktion | – |
| [`draw_objects(ax, objects, colors, hidden, labels, zorder)`](../../../vdsim/world/render.py#L68) | Funktion | – |
| [`draw_ego(ax, x, y, psi, length, width, zorder)`](../../../vdsim/world/render.py#L82) | Funktion | – |
| [`render_scenario(scenario, objects, t, ax, ego, trails, hidden, bounds, title, show_ego, figsize)`](../../../vdsim/world/render.py#L90) | Funktion | Draw a ScenarioInstance (or RoadNetwork): road, objects (default: initial actor states), ego (dict or EgoState-like with x, y, psi), trails {id: (xs, ys)}. |

### `vdsim.world.road`

| Name | Art | Beschreibung |
|---|---|---|
| [`Lane`](../../../vdsim/world/road.py#L43) | Klasse | – |
| [`LaneLocation`](../../../vdsim/world/road.py#L149) | Klasse | – |
| [`StopLine`](../../../vdsim/world/road.py#L158) | Klasse | stop / yield line on a lane; kind "stop" (sign: stop, then yield), "yield" or "traffic_light" |
| [`TrafficLight`](../../../vdsim/world/road.py#L169) | Klasse | fixed-time signal (RiLSA): red-yellow before green, yellow after green, red otherwise |
| [`ConflictZone`](../../../vdsim/world/road.py#L205) | Klasse | area shared by crossing / merging lanes (intersection, roundabout entry) |
| [`ParkingSpot`](../../../vdsim/world/road.py#L220) | Klasse | – |
| [`Corridor`](../../../vdsim/world/road.py#L237) | Klasse | additional drivable area next to a lane (shoulder, widened junction), lane-relative bounds |
| [`RoadNetwork`](../../../vdsim/world/road.py#L248) | Klasse | – |
| [`transform_line(line, dx, dy, rotation, name)`](../../../vdsim/world/road.py#L573) | Funktion | rigid motion of a reference line (rotation about the origin, then translation) |
| [`connect_poses(p0, th0, p1, th1, k0, k1, radius, transition, ds, name, min_straight)`](../../../vdsim/world/road.py#L582) | Funktion | Curve from pose (p0, th0, curvature k0) to (p1, th1, curvature k1) as curvature profile [arc(a, k0), turn(phi_mid, radius), arc(b, k1)] with C1 smoothstep transitions, the lengths a, b are solved so that the end point hits p1 (heading change exact by construction). |

### `vdsim.world.road_builders`

| Name | Art | Beschreibung |
|---|---|---|
| [`carriageway(net, prefix, ref, n_lanes, width, speed, lane_type)`](../../../vdsim/world/road_builders.py#L30) | Funktion | n same-direction lanes right of `ref` (ref = left edge, e.g. |
| [`two_way(net, fwd_id, bwd_id, ref, width, speed, center_marking, edge)`](../../../vdsim/world/road_builders.py#L45) | Funktion | two-way road around the center line `ref`: forward lane right of it, oncoming lane left of it |
| [`build_highway(length, n_lanes, width, speed, segments, merge, exit, prefix, name)`](../../../vdsim/world/road_builders.py#L82) | Funktion | Multi-lane carriageway (eastbound), optional acceleration lane with on-ramp and exit lane with ramp. |
| [`build_ring_road(radius, n_lanes, width, speed, prefix, name)`](../../../vdsim/world/road_builders.py#L119) | Funktion | closed multi-lane ring (counter-clockwise, lane 0 = inner/left); periodic boundary for traffic studies |
| [`build_rural_road(length, width, speed, segments, solid_sections, name)`](../../../vdsim/world/road_builders.py#L138) | Funktion | two-way road; center line dashed except for the given (s_from, s_to) sections (no overtaking) |
| [`build_urban_street(length, width, parking_width, speed, junction_x, junction_half, side_length, parking, center_marking, name)`](../../../vdsim/world/road_builders.py#L153) | Funktion | Two-way street along x (eastbound lane E_*, westbound W_*), parking lane on the right of the eastbound lane and optionally a T-junction with a side street to the south (yield line). |
| [`build_parking_street(length, width, parking_width, speed, gap_center, gap_length, name)`](../../../vdsim/world/road_builders.py#L226) | Funktion | two-way street with a parking lane on the right of the eastbound lane and one free parking spot |
| [`build_intersection(arm_length, half, width, speed, control, priority, cycle, name)`](../../../vdsim/world/road_builders.py#L244) | Funktion | Four-arm intersection (one lane per direction). |
| [`build_roundabout(radius, arm_length, arm_offset, width, ring_width, speed, ring_speed, node_angle, entry_radius, exit_radius, arms, name)`](../../../vdsim/world/road_builders.py#L303) | Funktion | Single-lane roundabout (counter-clockwise ring of center-line radius `radius`). |
| [`ring_route(net, entry_arm, exit_arm)`](../../../vdsim/world/road_builders.py#L365) | Funktion | lane sequence <entry>_in -> entry -> ring pieces -> exit -> <exit>_out |

### `vdsim.world.scenario`

| Name | Art | Beschreibung |
|---|---|---|
| [`ScenarioType`](../../../vdsim/world/scenario.py#L39) | Klasse | – |
| [`ADScenario`](../../../vdsim/world/scenario.py#L73) | Klasse | – |
| [`ScenarioInstance`](../../../vdsim/world/scenario.py#L109) | Klasse | – |
| [`scenario_type(name, label, description, defaults, duration)`](../../../vdsim/world/scenario.py#L48) | Funktion | decorator registering a scenario builder: builder(params, rng) -> dict |
| [`scenario_types()`](../../../vdsim/world/scenario.py#L56) | Funktion | – |
| [`list_scenario_types()`](../../../vdsim/world/scenario.py#L61) | Funktion | – |
| [`load_ad_scenario(name_or_path)`](../../../vdsim/world/scenario.py#L132) | Funktion | – |
| [`list_ad_scenarios()`](../../../vdsim/world/scenario.py#L139) | Funktion | library scenarios (configs/ad_scenarios) with type label and description |
| [`ego_on_lane(road, lane, s, d, v, psi_offset)`](../../../vdsim/world/scenario.py#L173) | Funktion | ego start pose (CoG) on a lane |
| [`build_scenario(spec_or_name, seed)`](../../../vdsim/world/scenario.py#L180) | Funktion | ADScenario \| dict \| file / library name \| type name -> ScenarioInstance |
| [`evaluate_success(instance, ego_states, worlds)`](../../../vdsim/world/scenario.py#L219) | Funktion | check the success criteria against a run: ego_states = list of EgoState (or dicts x, y, psi, v), worlds = list of WorldState; returns {"passed": bool, "criteria": {name: (ok, detail)}} |

### `vdsim.world.traffic_models`

| Name | Art | Beschreibung |
|---|---|---|
| [`IDMParams`](../../../vdsim/world/traffic_models.py#L21) | Klasse | – |
| [`MOBILParams`](../../../vdsim/world/traffic_models.py#L32) | Klasse | – |
| [`idm_acceleration(v, v0, gap, dv, a, b, T, s0, delta, b_max)`](../../../vdsim/world/traffic_models.py#L44) | Funktion | v: own speed, v0: desired speed, gap: bumper-to-bumper distance (inf = free road), dv = v - v_leader (approaching rate) |
| [`idm(v, v0, gap, dv, p)`](../../../vdsim/world/traffic_models.py#L56) | Funktion | convenience wrapper with an IDMParams instance |
| [`idm_equilibrium_speed(gap, p, v0)`](../../../vdsim/world/traffic_models.py#L61) | Funktion | steady-state speed for a given gap (dv = 0), solved by bisection (vectorized) |
| [`mobil_incentive(a_c, a_c_new, a_n, a_n_new, a_o, a_o_new, politeness, threshold, bias, b_safe)`](../../../vdsim/world/traffic_models.py#L75) | Funktion | returns (accept, incentive, safe); bias > 0 favors the change (keep-right rule: + for right, - for left) |
| [`smoothstep5(u)`](../../../vdsim/world/traffic_models.py#L86) | Funktion | quintic transition 0 -> 1 with zero slope and curvature at both ends (smooth lateral motion) |
| [`smoothstep5_d(u)`](../../../vdsim/world/traffic_models.py#L92) | Funktion | – |
