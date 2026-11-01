"""Builders for typical road networks (highway, rural road, urban street, intersection, roundabout, ring road).

Every center line is a curvature profile built with ReferenceLine.from_segments (smoothstep
curvature transitions, continuous dkappa/ds); junction and roundabout connectors come from
`connect_poses`, which keeps curvature and curvature derivative continuous at both ends.
Coordinates: x east, y north, right-hand traffic.
"""

from __future__ import annotations

import numpy as np

from ..geometry.reference_line import ReferenceLine
from .road import (ConflictZone, Lane, ParkingSpot, RoadNetwork, StopLine, TrafficLight, connect_poses,
                   transform_line)

ARM_ANGLES = {"E": 0.0, "N": np.pi / 2, "W": np.pi, "S": -np.pi / 2}
OPPOSITE_ARM = {"E": "W", "W": "E", "N": "S", "S": "N"}


def _straight(length, x0, y0, th0, ds=0.25, name=""):
    return ReferenceLine.straight(length, x0, y0, th0, ds, name)


def _project_s(line, x, y):
    return float(line.project(x, y)[0])


# ----------------------------------------------------------------------------- carriageways
def carriageway(net, prefix, ref, n_lanes, width, speed, lane_type="driving"):
    # n same-direction lanes right of `ref` (ref = left edge, e.g. median); ids prefix_0 = leftmost
    ids = []
    for i in range(n_lanes):
        center = ref.offset(-(i + 0.5) * width, name=f"{prefix}_{i}")
        lane = Lane(f"{prefix}_{i}", center, width, lane_type, speed,
                    marking_left="solid" if i == 0 else "dashed",
                    marking_right="solid" if i == n_lanes - 1 else "dashed")
        net.add_lane(lane)
        ids.append(lane.id)
    for a, b in zip(ids[:-1], ids[1:]):
        net.set_neighbors(a, b, "dashed")
    return ids


def two_way(net, fwd_id, bwd_id, ref, width, speed, center_marking="dashed", edge="solid"):
    # two-way road around the center line `ref`: forward lane right of it, oncoming lane left of it
    fwd = Lane(fwd_id, ref.offset(-0.5 * width, name=fwd_id), width, "driving", speed,
               marking_left=center_marking, marking_right=edge)
    bwd_center = ref.offset(0.5 * width).reversed(name=bwd_id).resample(0.25)
    bwd_marking = center_marking
    if not isinstance(center_marking, str):
        # profile in the forward s -> reversed s of the oncoming lane
        L = ref.length
        pts = sorted(center_marking)
        starts = [p[0] for p in pts] + [L]
        bwd_marking = [(L - starts[i + 1], pts[i][1]) for i in range(len(pts))]
    bwd = Lane(bwd_id, bwd_center, width, "driving", speed, marking_left=bwd_marking, marking_right=edge)
    net.add_lane(fwd)
    net.add_lane(bwd)
    net.set_opposite(fwd_id, bwd_id, None)
    return fwd, bwd


def _parallel_lane_w(net, lane_id, base_id, s_from, s_to, lane_type, speed, side, width):
    base = net.lanes[base_id]
    sign = -1.0 if side == "right" else 1.0
    center = base.center.segment(s_from, s_to).offset(sign * 0.5 * (base.width + width), name=lane_id)
    lane = Lane(lane_id, center, width, lane_type, speed,
                marking_left="dashed" if side == "right" else "solid",
                marking_right="solid" if side == "right" else "dashed")
    net.add_lane(lane)
    if side == "right":
        lane.left = base_id
    else:
        lane.right = base_id
    base.neighbor_segments.append((side, lane_id, s_from, s_to))
    base.add_dashed_section(side, s_from, s_to)
    return lane


# ----------------------------------------------------------------------------- highway
def build_highway(length=3000.0, n_lanes=3, width=3.75, speed=36.1, segments=None, merge=None, exit=None,
                  prefix="hw", name="Autobahn"):
    # Multi-lane carriageway (eastbound), optional acceleration lane with on-ramp and exit lane with ramp.
    #   merge = {"s": start on the right lane, "length", "ramp_length", "ramp_angle", "ramp_radius", "speed"}
    #   exit  = {"s", "length", "ramp_length", "ramp_angle", "ramp_radius", "speed"}
    net = RoadNetwork(name)
    ref = ReferenceLine.from_segments(segments or [("straight", length)], ds=0.5, name="median")
    lanes = carriageway(net, prefix, ref, n_lanes, width, speed)
    right = lanes[-1]
    net.metadata.update({"lanes": lanes, "prefix": prefix, "lane_width": width})
    if merge is not None:
        m = {"s": 200.0, "length": 300.0, "ramp_length": 150.0, "ramp_angle": 0.25, "ramp_radius": 300.0,
             "speed": 22.2, **merge}
        lane = _parallel_lane_w(net, "merge", right, m["s"], m["s"] + m["length"], "merge", speed, "right", width)
        x0, y0, th0 = lane.pose(0.0)
        back = ReferenceLine.from_segments([("straight", 20.0), ("turn", m["ramp_angle"], m["ramp_radius"]),
                                            ("straight", m["ramp_length"])], x0, y0, th0 + np.pi, 10.0, 0.25)
        ramp = Lane("onramp", back.reversed(name="onramp").resample(0.25), width, "driving", m["speed"],
                    marking_left="solid", marking_right="solid")
        net.add_lane(ramp)
        net.connect("onramp", "merge")
        net.metadata["merge"] = m
    if exit is not None:
        e = {"s": 1800.0, "length": 250.0, "ramp_length": 200.0, "ramp_angle": 0.35, "ramp_radius": 250.0,
             "speed": 22.2, **exit}
        lane = _parallel_lane_w(net, "exit", right, e["s"], e["s"] + e["length"], "exit", speed, "right", width)
        x0, y0, th0 = lane.pose(lane.length)
        ramp_line = ReferenceLine.from_segments([("straight", 20.0), ("turn", -e["ramp_angle"], e["ramp_radius"]),
                                                 ("straight", e["ramp_length"])], x0, y0, th0, 10.0, 0.25,
                                                name="exit_ramp")
        net.add_lane(Lane("exit_ramp", ramp_line, width, "driving", e["speed"], marking_left="solid",
                          marking_right="solid"))
        net.connect("exit", "exit_ramp")
        net.metadata["exit"] = e
    return net


def build_ring_road(radius=500.0, n_lanes=3, width=3.75, speed=36.1, prefix="ring", name="Ringstraße"):
    # closed multi-lane ring (counter-clockwise, lane 0 = inner/left); periodic boundary for traffic studies
    net = RoadNetwork(name)
    ids = []
    for i in range(n_lanes):
        r = radius + (i + 0.5) * width
        lid = f"{prefix}_{i}"
        line = ReferenceLine.circle(r, 0.0, 0.0, -np.pi / 2, True, 0.5, lid)
        net.add_lane(Lane(lid, line, width, "driving", speed, marking_left="solid" if i == 0 else "dashed",
                          marking_right="solid" if i == n_lanes - 1 else "dashed"))
        net.connect(lid, lid)
        ids.append(lid)
    for a, b in zip(ids[:-1], ids[1:]):
        net.set_neighbors(a, b, "dashed")
    net.metadata.update({"lanes": ids, "radius": radius, "lane_width": width})
    return net


# ----------------------------------------------------------------------------- rural / urban roads
def build_rural_road(length=2500.0, width=3.5, speed=27.8, segments=None, solid_sections=(), name="Landstraße"):
    # two-way road; center line dashed except for the given (s_from, s_to) sections (no overtaking)
    net = RoadNetwork(name)
    ref = ReferenceLine.from_segments(segments or [("straight", length)], ds=0.5, name="center")
    marking = "dashed"
    if solid_sections:
        prof = [(0.0, "dashed")]
        for a, b in sorted(solid_sections):
            prof += [(a, "solid"), (b, "dashed")]
        marking = prof
    two_way(net, "fwd", "bwd", ref, width, speed, marking)
    net.metadata.update({"lane_width": width, "solid_sections": [list(x) for x in solid_sections]})
    return net


def build_urban_street(length=400.0, width=3.25, parking_width=2.2, speed=13.89, junction_x=None, junction_half=9.0,
                       side_length=80.0, parking=True, center_marking="dashed", name="Innerortsstraße"):
    # Two-way street along x (eastbound lane E_*, westbound W_*), parking lane on the right of the
    # eastbound lane and optionally a T-junction with a side street to the south (yield line).
    net = RoadNetwork(name)
    w, c = width, junction_half
    if junction_x is None:
        sections = [(0.0, length, "")]
    else:
        sections = [(0.0, junction_x - c, "1"), (junction_x - c, junction_x + c, "J"), (junction_x + c, length, "2")]
    e_ids, w_ids, p_ids = [], [], []
    for x0, x1, tag in sections:
        eid, wid = f"E{('_' + tag) if tag else ''}", f"W{('_' + tag) if tag else ''}"
        mark = "none" if tag == "J" else center_marking
        E = Lane(eid, _straight(x1 - x0, x0, -0.5 * w, 0.0, 0.25, eid), w, "driving", speed,
                 marking_left=mark, marking_right="none" if parking and tag != "J" else "curb",
                 junction="TJ" if tag == "J" else None)
        net.add_lane(E)
        e_ids.append(eid)
        if parking and tag != "J":
            pid = f"P{('_' + tag) if tag else ''}"
            P = Lane(pid, _straight(x1 - x0, x0, -w - 0.5 * parking_width, 0.0, 0.25, pid), parking_width, "parking",
                     speed, marking_left="none", marking_right="curb")
            net.add_lane(P)
            E.right, P.left = pid, eid
            p_ids.append(pid)
    # westbound: sections in reverse order (W_2 is the western part, W_1 the eastern part)
    rev = [(x0, x1, {"1": "2", "2": "1", "J": "J", "": ""}[tag]) for x0, x1, tag in sections]
    for (x0, x1, tag), eid in zip(rev, e_ids):
        wid = f"W{('_' + tag) if tag else ''}"
        mark = "none" if tag == "J" else center_marking
        Wl = Lane(wid, _straight(x1 - x0, x1, 0.5 * w, np.pi, 0.25, wid), w, "driving", speed,
                  marking_left=mark, marking_right="curb", junction="TJ" if tag == "J" else None)
        net.add_lane(Wl)
        w_ids.append(wid)
        net.set_opposite(eid, wid, None)
    for a, b in zip(e_ids[:-1], e_ids[1:]):
        net.connect(a, b)
    w_order = sorted(w_ids, key=lambda i: -net.lanes[i].center.x[0])     # east -> west
    for a, b in zip(w_order[:-1], w_order[1:]):
        net.connect(a, b)
    net.metadata.update({"lane_width": w, "parking_width": parking_width, "east": e_ids, "west": w_order,
                         "parking": p_ids})
    if junction_x is not None:
        xj = junction_x
        S_in = Lane("S_in", _straight(side_length, xj + 0.5 * w, -c - side_length, np.pi / 2, 0.25, "S_in"), w,
                    "driving", speed, marking_left="dashed", marking_right="curb")
        S_out = Lane("S_out", _straight(side_length, xj - 0.5 * w, -c, -np.pi / 2, 0.25, "S_out"), w, "driving",
                     speed, marking_left="dashed", marking_right="curb")
        net.add_lane(S_in)
        net.add_lane(S_out)
        net.set_opposite("S_in", "S_out", None)
        conns = {
            "E_1>S_out": ("E_1", "S_out"), "W_1>S_out": ("W_1", "S_out"),
            "S_in>E_2": ("S_in", "E_2"), "S_in>W_2": ("S_in", "W_2"),
        }
        for cid, (a, b) in conns.items():
            la, lb = net.lanes[a], net.lanes[b]
            xa, ya, tha = la.pose(la.length)
            xb, yb, thb = lb.pose(0.0)
            line = connect_poses((xa, ya), tha, (xb, yb), thb, transition=4.0, name=cid)
            net.add_lane(Lane(cid, line, w, "driving", speed, marking_left="none", marking_right="none",
                              junction="TJ"))
            net.connect(a, cid)
            net.connect(cid, b)
        net.add_conflict_zone(ConflictZone("TJ", "intersection", xj, 0.0, 1.3 * c,
                                           lanes=["E_J", "W_J", *conns], priority=["E_J", "W_J", "E_1>S_out",
                                                                                    "W_1>S_out"]))
        net.add_stop_line(StopLine("yield_S", "S_in", side_length - 0.5, "yield", zone_id="TJ"))
        net.metadata["junction_x"] = xj
    return net


def build_parking_street(length=140.0, width=3.5, parking_width=2.3, speed=8.33, gap_center=70.0, gap_length=8.5,
                         name="Parkstraße"):
    # two-way street with a parking lane on the right of the eastbound lane and one free parking spot
    net = RoadNetwork(name)
    ref = _straight(length, 0.0, 0.0, 0.0, 0.25, "center")
    fwd, _ = two_way(net, "E", "W", ref, width, speed, "dashed", "none")
    P = Lane("P", _straight(length, 0.0, -width - 0.5 * parking_width, 0.0, 0.25, "P"), parking_width, "parking",
             speed, marking_left="none", marking_right="curb")
    net.add_lane(P)
    fwd.right, P.left = "P", "E"
    net.lanes["W"].set_marking("right", "curb")
    net.add_parking_spot(ParkingSpot("spot_1", gap_center, -width - 0.5 * parking_width, 0.0, gap_length,
                                     parking_width, "P"))
    net.metadata.update({"lane_width": width, "parking_width": parking_width})
    return net


# ----------------------------------------------------------------------------- intersection
def build_intersection(arm_length=120.0, half=15.0, width=3.5, speed=13.89, control="traffic_light",
                       priority=("W", "E"), cycle=None, name="Kreuzung"):
    # Four-arm intersection (one lane per direction). Lanes <arm>_in (toward the center), <arm>_out,
    # connectors "<a>><b>" for all turns. control: traffic_light | yield (minor arms yield) | none
    net = RoadNetwork(name)
    w, L = width, arm_length
    for arm, beta in ARM_ANGLES.items():
        rot = beta - np.pi
        lin = transform_line(_straight(L, -(half + L), -0.5 * w, 0.0, 0.25), rotation=rot, name=f"{arm}_in")
        lout = transform_line(_straight(L, -half, 0.5 * w, np.pi, 0.25), rotation=rot, name=f"{arm}_out")
        net.add_lane(Lane(f"{arm}_in", lin, w, "driving", speed, marking_left="dashed", marking_right="curb"))
        net.add_lane(Lane(f"{arm}_out", lout, w, "driving", speed, marking_left="dashed", marking_right="curb"))
        net.set_opposite(f"{arm}_in", f"{arm}_out", None)
    conns = []
    for a in ARM_ANGLES:
        order = [OPPOSITE_ARM[a]]
        # right turn first (shorter), then left
        ba = ARM_ANGLES[a]
        for b in ARM_ANGLES:
            if b == a or b == OPPOSITE_ARM[a]:
                continue
            order.append(b)
        order[1:] = sorted(order[1:], key=lambda b: (np.sin(ARM_ANGLES[b] - ba) < 0))   # right turn first
        for b in order:
            la, lb = net.lanes[f"{a}_in"], net.lanes[f"{b}_out"]
            xa, ya, tha = la.pose(la.length)
            xb, yb, thb = lb.pose(0.0)
            cid = f"{a}>{b}"
            line = connect_poses((xa, ya), tha, (xb, yb), thb, transition=4.0, name=cid)
            net.add_lane(Lane(cid, line, w, "driving", speed, marking_left="none", marking_right="none",
                              junction="J"))
            net.connect(la.id, cid)
            net.connect(cid, lb.id)
            conns.append(cid)
    prio = [c for c in conns if c.split(">")[0] in priority] if control == "yield" else []
    net.add_conflict_zone(ConflictZone("J", "intersection", 0.0, 0.0, 1.25 * half, lanes=conns, priority=prio))
    if control == "traffic_light":
        cyc = {"green": 20.0, "yellow": 3.0, "all_red": 2.0, "red_yellow": 1.0, **(cycle or {})}
        period = 2 * (cyc["green"] + cyc["yellow"] + cyc["all_red"] + cyc["red_yellow"])
        for arm in ARM_ANGLES:
            group_b = arm in ("N", "S")
            start = (cyc["green"] + cyc["yellow"] + cyc["all_red"] + cyc["red_yellow"]) if group_b else 0.0
            lane = net.lanes[f"{arm}_in"]
            x, y, _ = lane.pose(lane.length, -0.5 * w - 0.5)
            net.add_traffic_light(TrafficLight(f"TL_{arm}", x, y, period, start, cyc["green"], cyc["yellow"],
                                               cyc["red_yellow"], cyc.get("offset", 0.0)))
            net.add_stop_line(StopLine(f"stop_{arm}", lane.id, lane.length - 1.0, "traffic_light", f"TL_{arm}", "J"))
    elif control == "yield":
        for arm in ARM_ANGLES:
            if arm in priority:
                continue
            lane = net.lanes[f"{arm}_in"]
            net.add_stop_line(StopLine(f"yield_{arm}", lane.id, lane.length - 1.0, "yield", zone_id="J"))
    net.metadata.update({"lane_width": w, "half": half, "arm_length": L, "control": control,
                         "priority": list(priority)})
    return net


# ----------------------------------------------------------------------------- roundabout
def build_roundabout(radius=20.0, arm_length=100.0, arm_offset=20.0, width=3.5, ring_width=5.0, speed=13.89,
                     ring_speed=8.33, node_angle=0.6, entry_radius=12.0, exit_radius=14.0, arms=("E", "N", "W", "S"),
                     name="Kreisverkehr"):
    # Single-lane roundabout (counter-clockwise ring of center-line radius `radius`). Entries and exits
    # join the ring tangentially with the ring curvature (continuous kappa and dkappa).
    net = RoadNetwork(name)
    w, R = width, radius
    r_arm = R + arm_offset
    # canonical entry (arm W) and exit (arm E)
    phi_e = np.pi + node_angle
    entry = connect_poses((-r_arm, -0.5 * w), 0.0, (R * np.cos(phi_e), R * np.sin(phi_e)), phi_e + np.pi / 2,
                          0.0, 1.0 / R, entry_radius, transition=4.0)
    phi_x = -node_angle
    exitc = connect_poses((R * np.cos(phi_x), R * np.sin(phi_x)), phi_x + np.pi / 2, (r_arm, -0.5 * w), 0.0,
                          1.0 / R, 0.0, exit_radius, transition=4.0)
    nodes = []          # (angle, kind, arm)
    for arm in arms:
        beta = ARM_ANGLES[arm]
        rot_in, rot_out = beta - np.pi, beta
        lin = transform_line(_straight(arm_length, -(r_arm + arm_length), -0.5 * w, 0.0, 0.25), rotation=rot_in,
                             name=f"{arm}_in")
        lout = transform_line(_straight(arm_length, r_arm, -0.5 * w, 0.0, 0.25), rotation=rot_out, name=f"{arm}_out")
        net.add_lane(Lane(f"{arm}_in", lin, w, "driving", speed, marking_left="solid", marking_right="curb"))
        net.add_lane(Lane(f"{arm}_out", lout, w, "driving", speed, marking_left="solid", marking_right="curb"))
        net.set_opposite(f"{arm}_in", f"{arm}_out", None)
        net.add_lane(Lane(f"{arm}_entry", transform_line(entry, rotation=rot_in, name=f"{arm}_entry"), w, "driving",
                          ring_speed, marking_left="none", marking_right="curb", junction="RB"))
        net.add_lane(Lane(f"{arm}_exit", transform_line(exitc, rotation=rot_out, name=f"{arm}_exit"), w, "driving",
                          ring_speed, marking_left="none", marking_right="curb", junction="RB"))
        net.connect(f"{arm}_in", f"{arm}_entry")
        net.connect(f"{arm}_exit", f"{arm}_out")
        nodes.append(((phi_e + rot_in) % (2 * np.pi), "entry", arm))
        nodes.append(((phi_x + rot_out) % (2 * np.pi), "exit", arm))
    nodes.sort()
    ring_ids = [f"ring_{k}" for k in range(len(nodes))]
    for k, (ang, kind, arm) in enumerate(nodes):
        ang_next = nodes[(k + 1) % len(nodes)][0]
        dphi = (ang_next - ang) % (2 * np.pi)
        line = ReferenceLine.from_segments([("arc", R * dphi, 1.0 / R)], R * np.cos(ang), R * np.sin(ang),
                                           ang + np.pi / 2, 4.0, 0.25, name=ring_ids[k])
        net.add_lane(Lane(ring_ids[k], line, ring_width, "driving", ring_speed, marking_left="curb",
                          marking_right="none", junction="RB"))
    for k, (ang, kind, arm) in enumerate(nodes):
        nxt = ring_ids[(k + 1) % len(nodes)]
        net.connect(ring_ids[k], nxt)
        if kind == "entry":
            net.connect(f"{arm}_entry", ring_ids[k])
            zone_xy = (R * np.cos(ang), R * np.sin(ang))
            zid = f"RB_{arm}"
            net.add_conflict_zone(ConflictZone(zid, "roundabout", zone_xy[0], zone_xy[1], 9.0,
                                               lanes=[ring_ids[k - 1], ring_ids[k], f"{arm}_entry"],
                                               priority=list(ring_ids)))
            lane = net.lanes[f"{arm}_entry"]
            net.add_stop_line(StopLine(f"yield_{arm}", lane.id, lane.length - 13.0, "yield", zone_id=zid))
        else:
            # ring piece ending at this exit node -> exit connector as second successor
            prev = ring_ids[k - 1]
            net.connect(prev, f"{arm}_exit")
    net.metadata.update({"lane_width": w, "radius": R, "ring": ring_ids, "arms": list(arms)})
    return net


def ring_route(net, entry_arm, exit_arm):
    # lane sequence <entry>_in -> entry -> ring pieces -> exit -> <exit>_out
    start = net.lanes[f"{entry_arm}_entry"].successors[0]
    route = [f"{entry_arm}_in", f"{entry_arm}_entry"]
    cur = start
    for _ in range(64):
        route.append(cur)
        if f"{exit_arm}_exit" in net.lanes[cur].successors:
            route += [f"{exit_arm}_exit", f"{exit_arm}_out"]
            return route
        cur = net.lanes[cur].successors[0]
    raise ValueError("exit not reachable")
