"""Scenario library of the automated-driving platform (registered scenario types).

Every builder gets the merged parameters and a seeded numpy Generator and returns a dict with
road, actors, ego (lane/s/d/v), mission, success, duration, metadata and disturbances.
The scenarios follow the test drives of Werling (2011), section 5.3, where applicable.
"""

from __future__ import annotations

from .actors import Cyclist, LaneVehicle, Pedestrian, StaticObstacle, Truck
from .road_builders import (
    build_highway,
    build_intersection,
    build_parking_street,
    build_ring_road,
    build_roundabout,
    build_rural_road,
    build_urban_street,
    ring_route,
)
from .scenario import scenario_type
from .traffic_models import IDMParams, MOBILParams, idm_equilibrium_speed

KMH = 1.0 / 3.6


def _car(aid, lane, s, v, v_des=None, mobil=False, **kw):
    p = IDMParams(v0=v if v_des is None else v_des)
    return LaneVehicle(aid, lane, s, v, idm_params=p, mobil=MOBILParams() if mobil else None, **kw)


def _traffic(net, lanes, rng, start_id, n, s_range, v_range, keep_out=(), mobil=True, min_gap=35.0):
    # n random IDM/MOBIL cars on the given lanes, keeping min_gap and away from keep_out=(lane, s, dist)
    actors, placed = [], {lid: [] for lid in lanes}
    aid = start_id
    tries = 0
    while len(actors) < n and tries < 50 * max(n, 1):
        tries += 1
        lane = lanes[int(rng.integers(len(lanes)))]
        s = float(rng.uniform(*s_range))
        if any(abs(s - q) < min_gap for q in placed[lane]):
            continue
        if any(abs(s - ks) < kd and (kl is None or kl == lane) for kl, ks, kd in keep_out):
            continue
        v = float(rng.uniform(*v_range))
        actors.append(_car(aid, lane, s, v, mobil=mobil))
        placed[lane].append(s)
        aid += 1
    return actors


# ----------------------------------------------------------------------------- highway driving
@scenario_type("highway_driving", "Autobahnfahrt",
               "Mehrspurige Autobahn mit langsamerem Vorderfahrzeug: Überholen links und Rückkehr nach rechts.",
               defaults={"n_lanes": 3, "length": 3000.0, "ego_v": 27.0, "target_speed": 33.3, "slow_v": 22.0,
                         "slow_gap": 120.0, "traffic": 6}, duration=40.0)
def _highway_driving(p, rng):
    net = build_highway(p["length"], int(p["n_lanes"]))
    lanes = net.metadata["lanes"]
    ego_lane, s_ego = lanes[-1], 100.0
    actors = [_car(1, ego_lane, s_ego + p["slow_gap"], p["slow_v"], name="langsames Fahrzeug")]
    actors += _traffic(net, lanes[:-1], rng, 2, int(p["traffic"]), (0.0, 900.0), (28.0, 36.0),
                       keep_out=[(None, s_ego, 50.0)])
    return {"road": net, "actors": actors, "ego": {"lane": ego_lane, "s": s_ego, "v": p["ego_v"]},
            "mission": {"route": [ego_lane], "target_speed": p["target_speed"],
                        "permissions": {"lane_change": True, "overtake": True}},
            "success": {"min_progress": 600.0}}


# ----------------------------------------------------------------------------- urban driving
@scenario_type("urban_driving", "Innerortsfahrt",
               "Innerortsstraße nach Werling 5.3.1: parkende Autos, Fußgänger zwischen parkenden Autos, "
               "Linksabbieger-Fehler des Gegenverkehrs an einer Einmündung und Radfahrer am Straßenrand.",
               defaults={"length": 520.0, "junction_x": 250.0, "speed": 30 * KMH, "pedestrians": 2,
                         "pedestrian_hidden": True, "pedestrian_trigger": 28.0, "left_turn_error": True,
                         "cyclists": 2, "side_street_error": False}, duration=75.0)
def _urban_driving(p, rng):
    net = build_urban_street(p["length"], junction_x=p["junction_x"], speed=p["speed"])
    w, wp = net.metadata["lane_width"], net.metadata["parking_width"]
    actors, aid = [], 1
    # parked cars on the parking lane before the junction (gap with pedestrians at x ~ 74)
    for s in (40.0, 46.5, 60.0, 66.5, 82.0, 88.5, 130.0, 137.0, 180.0):
        actors.append(StaticObstacle(aid, lane="P_1", s=s, d=float(rng.uniform(-0.15, 0.15)), length=4.5,
                                     width=1.8, obj_type="car", name="parkendes Auto"))
        aid += 1
    y_walk = -(w + wp) - 1.2
    for k in range(int(p["pedestrians"])):
        x = 74.0 + 1.2 * k
        actors.append(Pedestrian(aid, [(x, y_walk), (x + 0.3, 0.5 * w + 2.5)], speed=1.3 + 0.2 * k,
                                 visible=not p["pedestrian_hidden"], name=f"Fußgänger {k + 1}",
                                 actions=[{"trigger": {"kind": "ego_distance", "value": p["pedestrian_trigger"],
                                                       "delay": 0.6 * k}, "type": "start", "label": "Fahrbahn betreten"}]))
        aid += 1
    if p["left_turn_error"]:
        # two oncoming cars waiting until the ego passes x = 150, the rear one turns left illegally
        for k, (s, turn) in enumerate(((60.0, False), (73.0, True))):
            acts = [{"trigger": {"kind": "ego_x", "value": 150.0}, "type": "speed", "v": p["speed"], "accel": 1.5,
                     "label": "Anfahren"}]
            if turn:
                acts.append({"trigger": {"kind": "ego_x", "value": 170.0}, "type": "route",
                             "lanes": ["W_1", "W_1>S_out", "S_out"], "label": "Linksabbiegen (Fahrfehler)"})
            actors.append(_car(aid, "W_1", s, 0.0, v_des=0.0, route=["W_1", "W_J", "W_2"], name="Gegenverkehr",
                               actions=acts))
            aid += 1
    for k in range(int(p["cyclists"])):
        actors.append(Cyclist(aid, "E_2", 40.0 + 9.0 * k, v=4.0, d=-0.5 * w + 0.45, name=f"Radfahrer {k + 1}",
                              actions=[{"trigger": {"kind": "ego_distance", "value": 45.0}, "type": "lateral_offset",
                                        "d": -0.5 * w + 0.9, "duration": 2.5, "label": "drängt auf die Fahrbahn"}]))
        aid += 1
    if p["side_street_error"]:
        actors.append(_car(aid, "S_in", 20.0, p["speed"], route=["S_in", "S_in>E_2", "E_2"], obey_rules=False,
                           name="Vorfahrtsfehler Seitenstraße"))
        aid += 1
    return {"road": net, "actors": actors, "ego": {"lane": "E_1", "s": 10.0, "d": 0.3, "v": 4.0},
            "mission": {"route": ["E_1", "E_J", "E_2"], "target_speed": p["speed"],
                        "goal": {"lane": "E_2", "s": p["length"] - p["junction_x"] - 30.0, "stop": True},
                        "permissions": {"lane_change": False, "overtake": False, "use_opposite_lane": True}},
            "success": {"reach_goal": True}}


# ----------------------------------------------------------------------------- intersection
@scenario_type("intersection", "Kreuzung",
               "Vierarmige Kreuzung mit Ampel (oder Vorfahrtregelung) und Querverkehr; Ego geradeaus oder abbiegend.",
               defaults={"control": "traffic_light", "maneuver": "straight", "ego_distance": 70.0, "ego_v": 10.0,
                         "cross_traffic": 3, "oncoming": 2, "green": 12.0, "light_offset": 13.0},
               duration=45.0)
def _intersection(p, rng):
    control = p["control"]
    cyc = {"green": p["green"], "offset": p["light_offset"]}
    net = build_intersection(control=control, priority=("W", "E"), cycle=cyc)
    arm = "W" if control == "traffic_light" else "S"
    turn = {"straight": {"W": "E", "S": "N"}, "left": {"W": "N", "S": "W"}, "right": {"W": "S", "S": "E"}}
    target = turn[p["maneuver"]][arm]
    L = net.metadata["arm_length"]
    actors, aid = [], 1
    cross_arms = ("S", "N") if arm == "W" else ("W", "E")
    for k in range(int(p["cross_traffic"])):
        a = cross_arms[k % 2]
        s = L - 25.0 - 22.0 * (k // 2) - float(rng.uniform(0, 6))
        actors.append(_car(aid, f"{a}_in", s, 10.0, route=[f"{a}_in", f"{a}>{OPP[a]}", f"{OPP[a]}_out"],
                           name="Querverkehr"))
        aid += 1
    opp = OPP[arm]
    for k in range(int(p["oncoming"])):
        s = L - 60.0 - 25.0 * k
        actors.append(_car(aid, f"{opp}_in", s, 10.0, route=[f"{opp}_in", f"{opp}>{arm}", f"{arm}_out"],
                           name="Gegenverkehr"))
        aid += 1
    route = [f"{arm}_in", f"{arm}>{target}", f"{target}_out"]
    return {"road": net, "actors": actors, "ego": {"lane": f"{arm}_in", "s": L - p["ego_distance"], "v": p["ego_v"]},
            "mission": {"route": route, "target_speed": 13.89,
                        "goal": {"lane": f"{target}_out", "s": 60.0, "stop": False},
                        "permissions": {"lane_change": False}},
            "success": {"reach_goal": True}}


OPP = {"E": "W", "W": "E", "N": "S", "S": "N"}


# ----------------------------------------------------------------------------- roundabout
@scenario_type("roundabout", "Kreisverkehr",
               "Einspuriger Kreisverkehr: Einfahrt mit Wartepflicht (Yield), Fahrt im Ring, Ausfahrt.",
               defaults={"entry": "W", "exit": "E", "ring_traffic": 4, "ego_v": 8.0}, duration=40.0)
def _roundabout(p, rng):
    net = build_roundabout()
    actors, aid = [], 1
    arms = net.metadata["arms"]
    count = {}
    for k in range(int(p["ring_traffic"])):
        a_in = ["S", "N", "E", "S"][k % 4]
        a_out = [x for x in arms if x != a_in][int(rng.integers(3))]
        route = ring_route(net, a_in, a_out)
        n = count[a_in] = count.get(a_in, -1) + 1
        s = 100.0 - 15.0 - 16.0 * n - float(rng.uniform(0, 4))
        actors.append(_car(aid, f"{a_in}_in", s, 7.0, v_des=11.0, route=route, name="Kreisverkehr"))
        aid += 1
    route = ring_route(net, p["entry"], p["exit"])
    return {"road": net, "actors": actors, "ego": {"lane": f"{p['entry']}_in", "s": 45.0, "v": p["ego_v"]},
            "mission": {"route": route, "target_speed": 13.89,
                        "goal": {"lane": f"{p['exit']}_out", "s": 50.0, "stop": False}},
            "success": {"reach_goal": True}}


# ----------------------------------------------------------------------------- highway merge
@scenario_type("highway_merge", "Autobahnauffahrt",
               "Beschleunigungsstreifen: Einfädeln zwischen zwei Lkw nach Werling 5.3.2 "
               "(Längsreferenz in der Lückenmitte, gleichzeitiges Verlegen der Referenzkurve).",
               defaults={"merge_start": 300.0, "merge_length": 350.0, "ego_v": 12.5, "truck_v": 22.0,
                         "truck_gap": 55.0, "rear_truck_offset": 45.0, "target_speed": 33.3, "left_traffic": 3},
               duration=35.0)
def _highway_merge(p, rng):
    net = build_highway(3000.0, 2, merge={"s": p["merge_start"], "length": p["merge_length"]})
    right = net.metadata["lanes"][-1]
    s0 = p["merge_start"]
    rear = s0 + 10.0 + p["rear_truck_offset"]
    actors = [Truck(1, right, rear + p["truck_gap"] + 16.5, p["truck_v"], name="roter Lkw", color="#d62728"),
              Truck(2, right, rear, p["truck_v"], name="blauer Lkw", color="#1f77b4"),
              Truck(3, right, rear - p["truck_gap"] - 16.5, p["truck_v"], name="Lkw")]
    for a in actors:
        a.v_des = p["truck_v"]
    actors += _traffic(net, net.metadata["lanes"][:1], rng, 4, int(p["left_traffic"]), (0.0, 900.0), (28.0, 34.0),
                       mobil=False)
    return {"road": net, "actors": actors, "ego": {"lane": "merge", "s": 10.0, "v": p["ego_v"]},
            "mission": {"route": ["merge", right], "target_speed": p["target_speed"]},
            "success": {"final_lane": net.metadata["lanes"]}}


# ----------------------------------------------------------------------------- highway exit
@scenario_type("highway_exit", "Autobahnausfahrt",
               "Dreispurige Autobahn: rechtzeitige Spurwechsel nach rechts und Abfahrt über den Verzögerungsstreifen.",
               defaults={"exit_s": 1100.0, "exit_length": 250.0, "ego_lane": 0, "ego_v": 30.0, "traffic": 6},
               duration=55.0)
def _highway_exit(p, rng):
    net = build_highway(2500.0, 3, exit={"s": p["exit_s"], "length": p["exit_length"]})
    lanes = net.metadata["lanes"]
    ego_lane = lanes[int(p["ego_lane"])]
    actors = _traffic(net, lanes, rng, 1, int(p["traffic"]), (0.0, 1000.0), (25.0, 33.0),
                      keep_out=[(None, 100.0, 45.0)])
    return {"road": net, "actors": actors, "ego": {"lane": ego_lane, "s": 100.0, "v": p["ego_v"]},
            "mission": {"route": [lanes[-1], "exit", "exit_ramp"], "target_speed": 33.3,
                        "goal": {"lane": "exit_ramp", "s": 150.0, "stop": False}},
            "success": {"reach_goal": True}}


# ----------------------------------------------------------------------------- parking
@scenario_type("parking", "Längsparken rückwärts",
               "Einparken rückwärts in eine Längsparklücke (~8,5 m): Phase 1 vorwärts neben die Lücke, Halt, "
               "Phase 2 rückwärts auf der umgedrehten Referenzkurve der Parkspur bis zur Lückenmitte.",
               defaults={"gap_length": 8.5, "gap_center": 70.0, "ego_v": 2.0, "v_approach": 2.5, "v_reverse": 1.0,
                         "reverse_length": 9.0}, duration=50.0)
def _parking(p, rng):
    net = build_parking_street(gap_center=p["gap_center"], gap_length=p["gap_length"])
    gc, half = p["gap_center"], 0.5 * p["gap_length"]
    actors, aid = [], 1
    for s in (gc - half - 2.3, gc - half - 2.3 - 6.0, gc + half + 2.3, gc + half + 2.3 + 6.5, gc + half + 15.5):
        actors.append(StaticObstacle(aid, lane="P", s=s, length=4.5, width=1.8, obj_type="car", name="parkendes Auto"))
        aid += 1
    mission = {"route": ["E"], "target_speed": p["v_approach"],
               "parking": {"spot": "spot_1", "drive_lane": "E", "parking_lane": "P", "v_approach": p["v_approach"],
                           "v_reverse": p["v_reverse"], "reverse_length": p["reverse_length"]},
               "permissions": {"lane_change": False, "reverse": True}}
    return {"road": net, "actors": actors, "ego": {"lane": "E", "s": 25.0, "v": p["ego_v"]}, "mission": mission,
            "success": {"parked": {"spot": "spot_1", "pos_tol": 0.6, "yaw_tol": 0.15}, "final_speed_max": 0.2}}


# ----------------------------------------------------------------------------- overtaking (rural road)
@scenario_type("overtaking", "Überholen auf der Landstraße",
               "Zweistreifige Landstraße mit langsamem Lkw und Gegenverkehr: Überholen nur bei ausreichender Lücke "
               "im Gegenverkehr und gestrichelter Mittellinie.",
               defaults={"length": 2500.0, "truck_v": 16.0, "truck_gap": 60.0, "ego_v": 20.0, "target_speed": 25.0,
                         "oncoming": 4, "oncoming_v": 22.0, "solid_from": 1600.0, "solid_to": 1900.0},
               duration=60.0)
def _overtaking(p, rng):
    net = build_rural_road(p["length"], solid_sections=[(p["solid_from"], p["solid_to"])])
    s_ego = 50.0
    actors = [Truck(1, "fwd", s_ego + p["truck_gap"], p["truck_v"], name="langsamer Lkw")]
    actors[0].v_des = p["truck_v"]
    L = net.lanes["bwd"].length
    s_on = L - 450.0
    for k in range(int(p["oncoming"])):
        actors.append(_car(2 + k, "bwd", s_on, p["oncoming_v"], name="Gegenverkehr"))
        s_on -= float(rng.uniform(180.0, 900.0)) if k == 0 else float(rng.uniform(60.0, 400.0))
        if s_on < 0:
            break
    return {"road": net, "actors": actors, "ego": {"lane": "fwd", "s": s_ego, "v": p["ego_v"]},
            "mission": {"route": ["fwd"], "target_speed": p["target_speed"],
                        "permissions": {"lane_change": True, "overtake": True, "use_opposite_lane": True}},
            "success": {"min_progress": 900.0}}


# ----------------------------------------------------------------------------- emergency evasion
@scenario_type("emergency_evasion", "Notausweichen",
               "Spät sichtbares liegengebliebenes Fahrzeug auf der eigenen Spur, die Nachbarspur ist frei.",
               defaults={"ego_v": 25.0, "obstacle_s": 400.0, "visible_distance": 60.0, "left_traffic": False},
               duration=25.0)
def _emergency_evasion(p, rng):
    net = build_highway(2000.0, 2, speed=27.8)
    left, right = net.metadata["lanes"]
    actors = [StaticObstacle(1, lane=right, s=p["obstacle_s"], length=4.6, width=1.9, obj_type="car",
                             visible=False, name="liegengebliebenes Fahrzeug",
                             actions=[{"trigger": {"kind": "ego_distance", "value": p["visible_distance"]},
                                       "type": "visible", "value": True, "label": "wird sichtbar"}])]
    if p["left_traffic"]:
        actors.append(_car(2, left, p["obstacle_s"] - 60.0, 22.0, name="Nachbarspur"))
    return {"road": net, "actors": actors, "ego": {"lane": right, "s": 50.0, "v": p["ego_v"]},
            "mission": {"route": [right], "target_speed": p["ego_v"]}, "success": {"min_progress": 400.0}}


# ----------------------------------------------------------------------------- cut-in / cut-out
@scenario_type("cut_in", "Einscherer",
               "Fahrzeug auf der linken Spur schert knapp vor dem Ego ein (Auslöser: Abstand zum Ego).",
               defaults={"ego_v": 25.0, "cutter_v": 21.0, "cutter_s": 120.0, "trigger_gap": 22.0,
                         "duration_lc": 3.0}, duration=25.0)
def _cut_in(p, rng):
    net = build_highway(2000.0, 2)
    left, right = net.metadata["lanes"]
    actors = [_car(1, left, p["cutter_s"], p["cutter_v"], name="Einscherer",
                   actions=[{"trigger": {"kind": "ego_gap", "value": p["trigger_gap"]}, "type": "lane_change",
                             "direction": "right", "duration": p["duration_lc"], "label": "schert ein"}])]
    return {"road": net, "actors": actors, "ego": {"lane": right, "s": 50.0, "v": p["ego_v"]},
            "mission": {"route": [right], "target_speed": p["ego_v"], "permissions": {"lane_change": False}}}


@scenario_type("cut_out", "Ausscherer",
               "Vorderfahrzeug schert aus, dahinter steht ein Fahrzeug auf der eigenen Spur.",
               defaults={"ego_v": 25.0, "lead_gap": 40.0, "standing_s": 500.0, "cutout_distance": 55.0,
                         "duration_lc": 2.5}, duration=30.0)
def _cut_out(p, rng):
    net = build_highway(2000.0, 2)
    left, right = net.metadata["lanes"]
    s_ego = 50.0
    actors = [_car(1, right, s_ego + p["lead_gap"], p["ego_v"], react=False, name="Vorderfahrzeug",
                   actions=[{"trigger": {"kind": "self_s", "value": p["standing_s"] - p["cutout_distance"]},
                             "type": "lane_change", "direction": "left", "duration": p["duration_lc"],
                             "label": "schert aus"}]),
              StaticObstacle(2, lane=right, s=p["standing_s"], length=4.6, width=1.9, obj_type="car",
                             name="stehendes Fahrzeug")]
    return {"road": net, "actors": actors, "ego": {"lane": right, "s": s_ego, "v": p["ego_v"]},
            "mission": {"route": [right], "target_speed": p["ego_v"]}}


# ----------------------------------------------------------------------------- traffic density
@scenario_type("traffic_density", "Verkehrsdichte",
               "Mehrspurige Ringstraße (periodischer Rand) mit IDM- und MOBIL-Fahrzeugen; Dichte in Fz/km/Spur.",
               defaults={"density": 20.0, "radius": 400.0, "n_lanes": 3, "truck_share": 0.1, "v0_mean": 30.0,
                         "v0_std": 3.0, "ego_lane": 1, "ego_v": 25.0}, duration=60.0)
def _traffic_density(p, rng):
    net = build_ring_road(p["radius"], int(p["n_lanes"]))
    lanes = net.metadata["lanes"]
    ego_lane = lanes[int(p["ego_lane"])]
    actors, aid = [], 1
    for i, lid in enumerate(lanes):
        L = net.lanes[lid].length
        n = int(round(p["density"] * L / 1000.0))
        if n == 0:
            continue
        spacing = L / n
        phase = float(rng.uniform(0, spacing))
        for k in range(n):
            s = (phase + k * spacing + float(rng.uniform(-0.15, 0.15)) * spacing) % L
            s_ego_lane = s * net.lanes[ego_lane].length / L
            if min(s_ego_lane, net.lanes[ego_lane].length - s_ego_lane) < 30.0:
                continue                                        # keep the ego start free
            truck = rng.random() < p["truck_share"]
            v0 = float(max(rng.normal(p["v0_mean"], p["v0_std"]), 15.0))
            if truck:
                idm_p = IDMParams(v0=min(v0, 24.0), T=1.6, s0=3.0, a=0.6, b=1.5)
                veh = Truck(aid, lid, s, idm_params=idm_p, mobil=MOBILParams(politeness=0.5, duration=6.0))
            else:
                idm_p = IDMParams(v0=v0)
                veh = LaneVehicle(aid, lid, s, idm_params=idm_p, mobil=MOBILParams())
            gap = spacing - veh.length
            veh.v = float(min(idm_equilibrium_speed(gap, idm_p)[0], v0))
            actors.append(veh)
            aid += 1
    return {"road": net, "actors": actors, "ego": {"lane": ego_lane, "s": 0.0, "v": p["ego_v"]},
            "mission": {"route": [ego_lane], "target_speed": p["v0_mean"]},
            "metadata": {"density": p["density"], "n_vehicles": len(actors)}}


# ----------------------------------------------------------------------------- Werling highway test
@scenario_type("werling_highway", "Werling-Autobahnversuch",
               "Nachbildung von Werling 5.3.2: Einfädeln zwischen Lkw vom Beschleunigungsstreifen, verzögerter "
               "Spurwechsel bei schnell herannahendem Pkw, ausscherender Lkw und starke Seitenwindböe "
               "(Ereignis lateral_impulse).",
               defaults={"ego_v": 12.5, "truck_v": 22.0, "fast_v": 45.0, "fast_visible_t": 19.0, "gust_t": 38.5,
                         "gust_force": 9000.0, "gust_duration": 0.3, "orange_v": 70 * KMH},
               duration=48.0)
def _werling_highway(p, rng):
    net = build_highway(5000.0, 3, merge={"s": 250.0, "length": 450.0})
    l0, l1, l2 = net.metadata["lanes"]
    tv = p["truck_v"]
    red = Truck(1, l2, 320.0, tv, name="roter Lkw", color="#d62728")
    blue = Truck(2, l2, 250.0, tv, name="blauer Lkw", color="#1f77b4")
    for t in (red, blue):
        t.v_des = tv
    # fast car on the middle lane approaching from behind, "perceived" only when it becomes visible
    fast = _car(3, l1, 20.0, p["fast_v"], name="schneller Pkw", color="#2ca02c", visible=False,
                actions=[{"trigger": {"kind": "time", "value": p["fast_visible_t"]}, "type": "visible", "value": True,
                          "label": "wird wahrgenommen"}])
    fast.idm.v0 = fast.v_des = p["fast_v"]
    lila = Truck(4, l2, 800.0, 20.0, name="lila Lkw", color="#9467bd")
    lila.v_des = 20.0
    orange = Truck(5, l2, 1050.0, p["orange_v"], name="oranger Lkw", color="#ff7f0e",
                   actions=[{"trigger": {"kind": "ego_gap", "value": 45.0, "lane": l1}, "type": "lane_change",
                             "direction": "left", "duration": 4.0, "label": "schert aus"}])
    orange.v_des = p["orange_v"]
    actors = [red, blue, fast, lila, orange]
    disturbances = [{"t": p["gust_t"], "type": "lateral_impulse", "duration": p["gust_duration"],
                     "force_y": p["gust_force"], "yaw_moment": 0.15 * p["gust_force"],
                     "description": "starke Seitenwindböe (Werling 5.3.2)"}]
    return {"road": net, "actors": actors, "ego": {"lane": "merge", "s": 15.0, "v": p["ego_v"]},
            "mission": {"route": ["merge", l2], "target_speed": 120 * KMH,
                        "permissions": {"lane_change": True, "overtake": True}},
            "disturbances": disturbances, "success": {"min_progress": 900.0}}
