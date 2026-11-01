"""Road network of the automated-driving scenarios: lanes, traffic control and drivable areas.

    Lane            center line (vdsim.geometry.ReferenceLine), width, neighbors (incl. oncoming lane),
                    successors / predecessors, speed limit, type and lane markings (dashed / solid),
                    the markings define the box restriction d_min <= d(t) <= d_max (Werling 5.3.1, footnote 8)
    RoadNetwork     lanes + stop lines, traffic lights, yield lines, conflict zones, parking spots and
                    additional drivable corridors; helpers lane_at(), corridor(), route_line()

All builders (road_builders.py) compose the center lines from curvature profiles with smooth
(C1) curvature transitions, so dkappa/ds is continuous along a lane and across lane connections
(Werling 2011, remark 4: the trajectory curvature and acceleration are only continuous if the
reference curve has a continuous curvature derivative). `connect_poses` builds such connectors
(junction turns, roundabout entries/exits) between two given poses.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field

import numpy as np

from ..framework.knowledge import trace
from ..geometry.reference_line import ReferenceLine, wrap_angle

LANE_TYPES = ("driving", "merge", "exit", "parking", "crosswalk")
MARKINGS = ("dashed", "solid", "none", "curb")
CROSSABLE = ("dashed", "none")        # markings the drivable corridor may extend across
SIDES = ("left", "right")


def _profile(value):
    # marking given as "kind" or [(s_start, kind), ...] -> sorted list of (s_start, kind)
    if value is None or isinstance(value, str):
        return [(-np.inf, value or "none")]
    items = sorted((float(s), str(k)) for s, k in value)
    items[0] = (-np.inf, items[0][1])
    return items


# ----------------------------------------------------------------------------- lanes
@dataclass
class Lane:
    id: str
    center: ReferenceLine
    width: float = 3.5
    type: str = "driving"
    speed_limit: float = 13.89                 # m/s
    left: str | None = None                    # neighbor lane ids
    right: str | None = None
    left_opposite: bool = False                # left neighbor is an oncoming lane
    right_opposite: bool = False
    left_range: tuple | None = None            # (s_from, s_to) on this lane where the neighbor exists (None = all)
    right_range: tuple | None = None
    marking_left: object = "solid"             # "dashed" | "solid" | "none" | "curb" or [(s_start, kind), ...]
    marking_right: object = "solid"
    successors: list = field(default_factory=list)     # first entry = default continuation
    predecessors: list = field(default_factory=list)
    junction: str | None = None                # id of the conflict zone the lane belongs to (connectors)
    neighbor_segments: list = field(default_factory=list)   # extra neighbors [(side, lane_id, s_from, s_to)]
    name: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.type not in LANE_TYPES:
            raise ValueError(f"unknown lane type '{self.type}'")
        self._update()

    def _update(self):
        self._marks = {"left": _profile(self.marking_left), "right": _profile(self.marking_right)}
        c, pad = self.center, self.width
        self.bbox = (float(c.x.min() - pad), float(c.x.max() + pad), float(c.y.min() - pad), float(c.y.max() + pad))
        self.kappa_max = float(np.max(np.abs(c.kappa)))

    def set_marking(self, side, value):
        setattr(self, f"marking_{side}", value)
        self._update()

    @property
    def length(self):
        return self.center.length

    @property
    def closed(self):
        return self.center.closed

    def marking(self, side, s):
        prof = self._marks[side]
        i = bisect_right([p[0] for p in prof], float(s)) - 1
        return prof[max(i, 0)][1]

    def neighbor(self, side, s=None):
        for seg_side, nb_id, s0, s1 in self.neighbor_segments:
            if seg_side == side and (s is None or s0 <= s <= s1):
                return nb_id
        nb = self.left if side == "left" else self.right
        rng = self.left_range if side == "left" else self.right_range
        if nb is None:
            return None
        if s is not None and rng is not None and not (rng[0] <= s <= rng[1]):
            return None
        return nb

    def opposite(self, side, s=None):
        for seg_side, _, s0, s1 in self.neighbor_segments:
            if seg_side == side and (s is None or s0 <= s <= s1):
                return False
        return self.left_opposite if side == "left" else self.right_opposite

    def add_dashed_section(self, side, s_from, s_to, kind="dashed"):
        # insert a section with marking `kind` into the marking profile of `side`
        prof = [(max(s, -1e18), k) for s, k in self._marks[side]]
        after = self.marking(side, s_to)
        prof = [(s, k) for s, k in prof if not (s_from <= s <= s_to)]
        prof += [(s_from, kind), (s_to, after)]
        prof.sort()
        self.set_marking(side, [(max(s, 0.0), k) for s, k in prof])

    def pose(self, s, d=0.0):
        x, y, th, _, _ = self.center.evaluate(s)
        return x - d * np.sin(th), y + d * np.cos(th), th

    def boundary(self, side):
        # sampled boundary line (x, y) arrays
        sign = 1.0 if side == "left" else -1.0
        c = self.center
        return c.x - sign * 0.5 * self.width * np.sin(c.theta), c.y + sign * 0.5 * self.width * np.cos(c.theta)

    def to_dict(self):
        out = {k: getattr(self, k) for k in ("id", "width", "type", "speed_limit", "left", "right", "left_opposite",
                                              "right_opposite", "left_range", "right_range", "marking_left",
                                              "marking_right", "successors", "predecessors", "junction",
                                              "neighbor_segments", "name",
                                              "metadata")}
        out["center"] = self.center.to_dict()
        return out

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        data["center"] = ReferenceLine.from_dict(data["center"])
        for k in ("left_range", "right_range"):
            if data.get(k) is not None:
                data[k] = tuple(data[k])
        return cls(**data)


@dataclass
class LaneLocation:
    lane_id: str
    s: float
    d: float
    heading_error: float = 0.0


# ----------------------------------------------------------------------------- traffic control
@dataclass
class StopLine:
    # stop / yield line on a lane; kind "stop" (sign: stop, then yield), "yield" or "traffic_light"
    id: str
    lane_id: str
    s: float
    kind: str = "stop"
    light_id: str | None = None
    zone_id: str | None = None        # conflict zone protected by the line (yield gap check)


@dataclass
class TrafficLight:
    # fixed-time signal (RiLSA): red-yellow before green, yellow after green, red otherwise
    id: str
    x: float = 0.0
    y: float = 0.0
    cycle: float = 60.0               # s
    green_start: float = 0.0          # s within the cycle
    green: float = 25.0
    yellow: float = 3.0
    red_yellow: float = 1.0
    offset: float = 0.0               # shifts the cycle (phase at t = 0)

    def phase(self, t):
        tau = (t + self.offset - self.green_start) % self.cycle
        if tau < self.green:
            return "green"
        if tau < self.green + self.yellow:
            return "yellow"
        if tau >= self.cycle - self.red_yellow:
            return "red_yellow"
        return "red"

    def state(self, t):
        # contract states red / yellow / green (red-yellow still forbids entering)
        ph = self.phase(t)
        return "red" if ph == "red_yellow" else ph

    def time_to_change(self, t):
        tau = (t + self.offset - self.green_start) % self.cycle
        for bound in (self.green, self.green + self.yellow, self.cycle - self.red_yellow, self.cycle):
            if tau < bound:
                return bound - tau
        return 0.0


@dataclass
class ConflictZone:
    # area shared by crossing / merging lanes (intersection, roundabout entry)
    id: str
    kind: str = "intersection"        # intersection | roundabout | merge
    x: float = 0.0
    y: float = 0.0
    radius: float = 10.0
    lanes: list = field(default_factory=list)       # lane ids inside the zone
    priority: list = field(default_factory=list)    # lane ids with right of way

    def contains(self, x, y, margin=0.0):
        return np.hypot(np.asarray(x) - self.x, np.asarray(y) - self.y) <= self.radius + margin


@dataclass
class ParkingSpot:
    id: str
    x: float = 0.0
    y: float = 0.0
    psi: float = 0.0
    length: float = 6.0
    width: float = 2.2
    lane_id: str | None = None

    def corners(self):
        c, s = np.cos(self.psi), np.sin(self.psi)
        hl, hw = 0.5 * self.length, 0.5 * self.width
        loc = np.array([[hl, hw], [-hl, hw], [-hl, -hw], [hl, -hw]])
        return np.column_stack([self.x + loc[:, 0] * c - loc[:, 1] * s, self.y + loc[:, 0] * s + loc[:, 1] * c])


@dataclass
class Corridor:
    # additional drivable area next to a lane (shoulder, widened junction), lane-relative bounds
    lane_id: str
    s_from: float
    s_to: float
    d_min: float
    d_max: float
    description: str = ""


# ----------------------------------------------------------------------------- network
class RoadNetwork:
    def __init__(self, name=""):
        self.name = name
        self.lanes = {}
        self.stop_lines = []
        self.traffic_lights = {}
        self.conflict_zones = {}
        self.parking_spots = {}
        self.corridors = []
        self.metadata = {}
        self._line_cache = {}

    # ------------------------------------------------------------------ construction
    def add_lane(self, lane):
        self.lanes[lane.id] = lane
        self._line_cache.clear()
        return lane

    def lane(self, lane_id):
        return self.lanes[lane_id]

    def connect(self, a, b, first=False):
        # b is a successor of a (first=True: b becomes the default continuation)
        la, lb = self.lanes[a], self.lanes[b]
        for lst, item in ((la.successors, b), (lb.predecessors, a)):
            if item not in lst:
                if first:
                    lst.insert(0, item)
                else:
                    lst.append(item)
        self._line_cache.clear()

    def set_neighbors(self, left_id, right_id, marking="dashed", left_range=None, right_range=None):
        # same-direction neighbors: left_id lies left of right_id; ranges in the respective lane's s
        l, r = self.lanes[left_id], self.lanes[right_id]
        r.left, r.left_range, r.left_opposite = left_id, right_range, False
        l.right, l.right_range, l.right_opposite = right_id, left_range, False
        if marking is not None:
            r.set_marking("left", marking)
            l.set_marking("right", marking)

    def set_opposite(self, a, b, marking="dashed"):
        # oncoming lanes sharing their left boundary (center line of a two-way road)
        la, lb = self.lanes[a], self.lanes[b]
        la.left, la.left_opposite = b, True
        lb.left, lb.left_opposite = a, True
        if marking is not None:
            la.set_marking("left", marking)
            lb.set_marking("left", marking)

    def add_stop_line(self, line):
        self.stop_lines.append(line)
        return line

    def add_traffic_light(self, light):
        self.traffic_lights[light.id] = light
        return light

    def add_conflict_zone(self, zone):
        self.conflict_zones[zone.id] = zone
        return zone

    def add_parking_spot(self, spot):
        self.parking_spots[spot.id] = spot
        return spot

    # ------------------------------------------------------------------ queries
    def stop_lines_on(self, lane_id):
        return [sl for sl in self.stop_lines if sl.lane_id == lane_id]

    def light_states(self, t):
        return {lid: tl.state(t) for lid, tl in self.traffic_lights.items()}

    def light_phases(self, t):
        return {lid: tl.phase(t) for lid, tl in self.traffic_lights.items()}

    def bounds(self, margin=10.0):
        b = np.array([lane.bbox for lane in self.lanes.values()])
        return b[:, 0].min() - margin, b[:, 1].max() + margin, b[:, 2].min() - margin, b[:, 3].max() + margin

    def _candidates(self, x, y):
        out = []
        for lane in self.lanes.values():
            x0, x1, y0, y1 = lane.bbox
            if x0 <= x <= x1 and y0 <= y <= y1:
                out.append(lane)
        return out

    def locate_all(self, x, y, margin=0.0, psi=None, max_heading=np.pi / 2):
        # all lanes containing the point (|d| <= width/2 + margin); with psi only aligned lanes
        found = []
        for lane in self._candidates(x, y):
            s, d = lane.center.project(x, y)
            if not lane.closed and (s < -margin or s > lane.length + margin):
                continue
            if abs(d) > 0.5 * lane.width + margin:
                continue
            herr = 0.0
            if psi is not None:
                herr = abs(float(wrap_angle(psi - lane.center.evaluate(s)[2])))
                if herr > max_heading:
                    continue
            found.append(LaneLocation(lane.id, float(s), float(d), herr))
        return found

    def lane_at(self, x, y, psi=None, margin=0.0, prefer=None):
        # best lane at (x, y): preferred lanes first, then the smallest |d| (+ heading error)
        found = self.locate_all(x, y, margin, psi)
        if not found:
            return None
        prefer = set(prefer or ())

        def score(loc):
            lane = self.lanes[loc.lane_id]
            return (0 if loc.lane_id in prefer else 1, abs(loc.d) / max(lane.width, 0.1) + 0.5 * loc.heading_error)
        return min(found, key=score)

    def drivable(self, xs, ys, tol=0.0):
        # vectorized check of points against lanes, conflict zones, parking spots and corridors
        xs, ys = np.atleast_1d(np.asarray(xs, dtype=float)), np.atleast_1d(np.asarray(ys, dtype=float))
        ok = np.zeros(len(xs), dtype=bool)
        for lane in self.lanes.values():
            x0, x1, y0, y1 = lane.bbox
            m = ~ok & (xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1)
            if not np.any(m):
                continue
            s, d = lane.center.project_many(xs[m], ys[m])
            inside = np.abs(d) <= 0.5 * lane.width + tol
            if not lane.closed:
                inside &= (s >= lane.center.s0 - tol) & (s <= lane.center.s[-1] + tol)
            for c in self.corridors:
                if c.lane_id == lane.id:
                    inside |= (s >= c.s_from) & (s <= c.s_to) & (d >= c.d_min - tol) & (d <= c.d_max + tol)
            idx = np.flatnonzero(m)
            ok[idx[inside]] = True
        for z in self.conflict_zones.values():
            ok |= z.contains(xs, ys, tol)
        for p in self.parking_spots.values():
            c, sn = np.cos(p.psi), np.sin(p.psi)
            lx = (xs - p.x) * c + (ys - p.y) * sn
            ly = -(xs - p.x) * sn + (ys - p.y) * c
            ok |= (np.abs(lx) <= 0.5 * p.length + tol) & (np.abs(ly) <= 0.5 * p.width + tol)
        return ok

    def neighbor_s(self, lane_id, s, side):
        # s on the neighbor lane at the same longitudinal position
        lane = self.lanes[lane_id]
        nb_id = lane.neighbor(side, s)
        if nb_id is None:
            return None
        nb = self.lanes[nb_id]
        sign = 1.0 if side == "left" else -1.0
        x, y, _ = lane.pose(s, sign * 0.5 * (lane.width + nb.width))
        return nb.center.project(x, y)[0]

    @trace("werling2011", section="5.3.1", concept="box_restriction",
           note="Box-Restriktion für d(t) aus Markierungen und Nachbarspuren (Fußnote 8)")
    def corridor(self, lane_id, s, include_opposite=True, include_parking=True, max_lanes=4, allowed_types=None):
        # drivable corridor (d_min, d_max) relative to the lane center at s: extends across crossable
        # markings (dashed / none) onto existing neighbor lanes, stops at solid lines and curbs
        lane = self.lanes[lane_id]
        bounds = {}
        for side, sign in (("left", 1.0), ("right", -1.0)):
            edge = 0.5 * lane.width
            cur, cur_s, rel = lane, s, side
            for _ in range(max_lanes):
                nb_id = cur.neighbor(rel, cur_s)
                if nb_id is None or cur.marking(rel, cur_s) not in CROSSABLE:
                    break
                nb = self.lanes[nb_id]
                opposite = cur.opposite(rel, cur_s)
                if opposite and not include_opposite:
                    break
                if nb.type == "parking" and not include_parking:
                    break
                if allowed_types is not None and nb.type not in allowed_types:
                    break
                x, y, _ = cur.pose(cur_s, (1.0 if rel == "left" else -1.0) * 0.5 * (cur.width + nb.width))
                nb_s = nb.center.project(x, y)[0]
                edge += nb.width
                if opposite:
                    rel = "right" if rel == "left" else "left"
                cur, cur_s = nb, nb_s
            bounds[side] = sign * edge
        d_min, d_max = bounds["right"], bounds["left"]
        for c in self.corridors:
            if c.lane_id == lane_id and c.s_from <= s <= c.s_to:
                d_min, d_max = min(d_min, c.d_min), max(d_max, c.d_max)
        return float(d_min), float(d_max)

    # ------------------------------------------------------------------ routes
    def default_successor(self, lane_id, route=None, exclude=()):
        lane = self.lanes[lane_id]
        succ = [s for s in lane.successors if s not in exclude]
        if not succ:
            return None
        if route:
            for sid in succ:
                if sid in route:
                    return sid
        return succ[0]

    def chain(self, lane_id, route=None, ahead=1500.0, behind=0.0):
        # longitudinal lane sequence through lane_id: unique / route predecessors up to `behind` m,
        # successors (route first, else the default continuation) up to `ahead` m
        lane = self.lanes[lane_id]
        if lane.closed:
            return (lane_id,)
        ids, seen = [lane_id], {lane_id}
        total, cur = 0.0, lane
        while total < behind:
            preds = [p for p in cur.predecessors if p not in seen and not self.lanes[p].closed]
            if route:
                in_route = [p for p in preds if p in route]
                preds = in_route or preds
            if not preds:
                break
            cur = self.lanes[preds[0]]
            ids.insert(0, cur.id)
            seen.add(cur.id)
            total += cur.length
        total, cur = lane.length, lane
        while total < ahead:
            nxt = self.default_successor(cur.id, route, exclude=seen)
            if nxt is None or self.lanes[nxt].closed:
                break
            cur = self.lanes[nxt]
            ids.append(nxt)
            seen.add(nxt)
            total += cur.length
        return tuple(ids)

    @trace("werling2011", section="3.5.3", concept="continuous_curvature_road",
           note="Route über mehrere Spuren als eine Referenzkurve mit stetigem kappa' (Bemerkung 4)")
    def route_line(self, lane_ids, ds=0.25, tol=0.05):
        # concatenated center lines of consecutive lanes as one ReferenceLine (cached per lane tuple);
        # the result carries .lane_ids and .lane_offsets {lane_id: s of the lane start}
        key = (tuple(lane_ids), float(ds))
        if key in self._line_cache:
            return self._line_cache[key]
        ids = list(lane_ids)
        if len(ids) == 1:
            line = self.lanes[ids[0]].center
            line.lane_ids, line.lane_offsets = (ids[0],), {ids[0]: 0.0}
            self._line_cache[key] = line
            return line
        parts, offsets, offset = {k: [] for k in ("s", "x", "y", "theta", "kappa", "dkappa")}, {}, 0.0
        prev = None
        for lid in ids:
            c = self.lanes[lid].center
            start = 0
            if prev is not None:
                gap = np.hypot(c.x[0] - prev.x[-1], c.y[0] - prev.y[-1])
                if gap > tol:
                    raise ValueError(f"lanes {prev.name or '?'} -> {lid} are not connected (gap {gap:.3f} m)")
                start = 1
            offsets[lid] = offset
            parts["s"].append(c.s[start:] - c.s[0] + offset)
            for k in ("x", "y", "theta", "kappa", "dkappa"):
                parts[k].append(getattr(c, k)[start:])
            offset += c.length
            prev = c
        arr = {k: np.concatenate(v) for k, v in parts.items()}
        theta = np.unwrap(arr["theta"])
        keep = np.concatenate([[True], np.diff(arr["s"]) > 1e-9])
        line = ReferenceLine(arr["s"][keep], arr["x"][keep], arr["y"][keep], theta[keep], arr["kappa"][keep],
                             arr["dkappa"][keep], name="+".join(ids)).resample(ds)
        line.lane_ids, line.lane_offsets = tuple(ids), offsets
        self._line_cache[key] = line
        return line

    def reversed_line(self, lane_id, ds=0.25):
        # lane center traversed backwards (reverse driving, e.g. parking), cached
        key = ("reversed", lane_id, float(ds))
        if key not in self._line_cache:
            line = self.lanes[lane_id].center.reversed().resample(ds)
            line.lane_ids, line.lane_offsets = (lane_id,), {lane_id: 0.0}
            self._line_cache[key] = line
        return self._line_cache[key]

    def validate(self, tol_pos=0.05, tol_heading=1e-2, tol_kappa=5e-3, tol_dkappa=5e-3):
        # continuity of position, heading, curvature and curvature derivative across all connections
        problems = []
        for lane in self.lanes.values():
            if lane.closed:
                continue
            xa, ya, tha, ka, dka = lane.center.evaluate(lane.center.s[-1])
            for sid in lane.successors:
                c = self.lanes[sid].center
                xb, yb, thb, kb, dkb = c.evaluate(c.s0)
                errs = {"pos": float(np.hypot(xb - xa, yb - ya)), "heading": abs(float(wrap_angle(thb - tha))),
                        "kappa": abs(kb - ka), "dkappa": abs(dkb - dka)}
                lim = {"pos": tol_pos, "heading": tol_heading, "kappa": tol_kappa, "dkappa": tol_dkappa}
                bad = {k: v for k, v in errs.items() if v > lim[k]}
                if bad:
                    problems.append((lane.id, sid, bad))
        return problems

    def to_dict(self):
        from dataclasses import asdict
        return {"name": self.name, "lanes": [lane.to_dict() for lane in self.lanes.values()],
                "stop_lines": [asdict(x) for x in self.stop_lines],
                "traffic_lights": [asdict(x) for x in self.traffic_lights.values()],
                "conflict_zones": [asdict(x) for x in self.conflict_zones.values()],
                "parking_spots": [asdict(x) for x in self.parking_spots.values()],
                "corridors": [asdict(x) for x in self.corridors], "metadata": self.metadata}

    @classmethod
    def from_dict(cls, data):
        net = cls(data.get("name", ""))
        for ld in data.get("lanes", []):
            net.add_lane(Lane.from_dict(ld))
        net.stop_lines = [StopLine(**x) for x in data.get("stop_lines", [])]
        for x in data.get("traffic_lights", []):
            net.add_traffic_light(TrafficLight(**x))
        for x in data.get("conflict_zones", []):
            net.add_conflict_zone(ConflictZone(**x))
        for x in data.get("parking_spots", []):
            net.add_parking_spot(ParkingSpot(**x))
        net.corridors = [Corridor(**x) for x in data.get("corridors", [])]
        net.metadata = dict(data.get("metadata", {}))
        return net


# ----------------------------------------------------------------------------- geometry helpers
def transform_line(line, dx=0.0, dy=0.0, rotation=0.0, name=None):
    # rigid motion of a reference line (rotation about the origin, then translation)
    c, s = np.cos(rotation), np.sin(rotation)
    return ReferenceLine(line.s, c * line.x - s * line.y + dx, s * line.x + c * line.y + dy, line.theta + rotation,
                         line.kappa, line.dkappa, line.closed, name or line.name)


@trace("werling2011", section="3.5.3", concept="continuous_curvature_road",
       note="Konnektor mit glatten Krümmungsübergängen (from_segments) zwischen zwei Posen")
def connect_poses(p0, th0, p1, th1, k0=0.0, k1=0.0, radius=None, transition=6.0, ds=0.25, name="",
                  min_straight=None):
    # Curve from pose (p0, th0, curvature k0) to (p1, th1, curvature k1) as curvature profile
    #   [arc(a, k0), turn(phi_mid, radius), arc(b, k1)]   with C1 smoothstep transitions,
    # the lengths a, b are solved so that the end point hits p1 (heading change exact by construction).
    from scipy.optimize import least_squares
    p0, p1 = np.asarray(p0, dtype=float), np.asarray(p1, dtype=float)
    phi = float(wrap_angle(th1 - th0))
    delta = p1 - p0
    e0 = np.array([np.cos(th0), np.sin(th0)])
    if abs(phi) < 1e-6 and abs(k0) < 1e-9 and abs(k1) < 1e-9:
        lateral = float(-delta[0] * e0[1] + delta[1] * e0[0])
        if abs(lateral) > 1e-3:
            raise ValueError("parallel poses with lateral offset need an S-curve (not supported)")
        return ReferenceLine.straight(float(delta @ e0), p0[0], p0[1], th0, ds, name)
    e1 = np.array([np.cos(th1), np.sin(th1)])
    if radius is None:
        # fillet radius from the tangent intersection (pure-arc estimate, 85 % of the shorter tangent)
        mat = np.column_stack([e0, e1])
        t0, t1 = np.linalg.solve(mat, delta) if abs(np.linalg.det(mat)) > 1e-9 else (delta @ e0, delta @ e0)
        radius = 0.85 * max(min(t0, t1), 1.0) / max(np.tan(abs(phi) / 2), 1e-3)
    radius_pref = max(float(radius), 3.0)
    lo = float(min_straight if min_straight is not None else 1.15 * transition)

    def build(x):
        a, b, r = float(x[0]), float(x[1]), float(x[2])
        mid = phi - k0 * a - k1 * b
        segs = [("arc", a, k0)]
        if abs(mid) * r > 0.05:
            segs.append(("arc", abs(mid) * r, np.sign(mid) / r))
        segs.append(("arc", b, k1))
        return ReferenceLine.from_segments(segs, p0[0], p0[1], th0, transition, ds, name)

    def residual(x):
        line = build(x)
        # end point error; weak preference for the requested radius (third unknown)
        return np.array([line.x[-1] - p1[0], line.y[-1] - p1[1], 1e-3 * (x[2] - radius_pref)])

    # initial guess from the pure-arc fillet
    mat = np.column_stack([e0, e1])
    try:
        guess = np.linalg.solve(mat, delta - radius_pref * np.tan(abs(phi) / 2) * (e0 + e1))
    except np.linalg.LinAlgError:
        guess = np.array([lo, lo])
    guess = np.concatenate([np.maximum(guess, lo + 0.5), [radius_pref]])
    r_lo = max(0.3 * radius_pref, 2.0)
    guess[2] = np.clip(guess[2], r_lo + 1e-6, 5.0 * radius_pref - 1e-6)
    sol = least_squares(residual, guess, bounds=([lo, lo, r_lo], [np.inf, np.inf, 5.0 * radius_pref]),
                        xtol=1e-12, ftol=1e-12)
    if np.hypot(*sol.fun[:2]) > 1e-3:
        raise ValueError(f"connector {name}: end pose not reachable (residual {np.hypot(*sol.fun[:2]):.3f} m)")
    line = build(sol.x)
    # remove the residual numerically (sub-millimeter) by a smooth linear blend of the position
    err = p1 - np.array([line.x[-1], line.y[-1]])
    w = (line.s - line.s[0]) / line.length
    return ReferenceLine(line.s, line.x + w * err[0], line.y + w * err[1], line.theta, line.kappa, line.dkappa,
                         False, name)
