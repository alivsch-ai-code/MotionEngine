"""Traffic participants and their deterministic simulation.

    LaneVehicle      lane-bound vehicle: IDM longitudinal (Treiber 2000), MOBIL lane changes
                     (Kesting 2007) as smooth quintic lateral motion, routes over successor lanes,
                     traffic lights / yield lines, scripted actions via triggers
    Truck, Cyclist   LaneVehicle with typical dimensions and parameters
    Pedestrian       walks along a polyline (start / stop by trigger)
    StaticObstacle   parked car, broken-down vehicle, obstacle (optionally hidden until a trigger:
                     "suddenly appearing")
    TrafficSimulator synchronous update of all actors (accelerations from the state at t, then
                     integration), occupancy per lane for leader / follower search

Triggers (Trigger.kind): time, ego_distance, ego_gap (actor ahead of the ego along the actor's lane),
ego_s (ego position on a lane), ego_x, self_s, after (another action fired + value s), always.
Actions (dict "type"): lane_change (direction | lane, duration), speed (v, accel), brake (decel, v),
stop (decel), route (lanes), lateral_offset (d, duration), visible (value), start / halt (pedestrian),
ignore_rules (value), react (value).
Randomness only enters through the scenario builders (seeded generators); the simulation itself is
deterministic.
"""

from __future__ import annotations

import copy
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field, replace

import numpy as np

from ..framework.types import ObjectState
from ..geometry.reference_line import wrap_angle
from .traffic_models import IDMParams, MOBILParams, idm, mobil_incentive, smoothstep5, smoothstep5_d

EGO_ID = 0


# ----------------------------------------------------------------------------- triggers / actions
@dataclass
class Trigger:
    kind: str = "time"
    value: float = 0.0
    lane: str | None = None
    ref: int | None = None        # index of another action of the same actor (kind "after")
    delay: float = 0.0

    def condition(self, t, actor, sim):
        k, ego = self.kind, sim.ego
        if k == "always":
            return True
        if k == "time":
            return t >= self.value
        if k == "after":
            other = actor.actions[self.ref] if self.ref is not None and self.ref < len(actor.actions) else None
            return other is not None and other.fired_at is not None and t >= other.fired_at + self.value
        if k == "self_s":
            return actor.s is not None and (self.lane is None or actor.lane_id == self.lane) and actor.s >= self.value
        if ego is None:
            return False
        if k == "ego_distance":
            return float(np.hypot(ego.x - actor.x, ego.y - actor.y)) <= self.value
        if k == "ego_x":
            return ego.x >= self.value
        if k == "ego_s":
            lane = sim.road.lanes.get(self.lane)
            if lane is None:
                return False
            s, d = lane.center.project(ego.x, ego.y)
            return abs(d) < lane.width and s >= self.value
        if k == "ego_gap":
            lane = sim.road.lanes.get(self.lane or actor.lane_id) if (self.lane or actor.lane_id) else None
            if lane is None:
                return False
            s_e, d_e = lane.center.project(ego.x, ego.y)
            s_a = actor.s if (actor.lane_id == lane.id and actor.s is not None) else lane.center.project(actor.x, actor.y)[0]
            if abs(d_e) > 20.0:
                return False
            gap = s_a - s_e
            if lane.closed:
                gap = (gap + 0.5 * lane.length) % lane.length - 0.5 * lane.length
            return gap <= self.value
        raise ValueError(f"unknown trigger kind '{k}'")


class ScriptAction:
    def __init__(self, trigger, action, label=""):
        self.trigger = trigger if isinstance(trigger, Trigger) else Trigger(**(trigger or {}))
        self.action = dict(action)
        self.label = label
        self.condition_at = None
        self.fired_at = None

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        trig = data.pop("trigger", {"kind": "always"})
        label = data.pop("label", "")
        return cls(trig, data, label)

    def to_dict(self):
        from dataclasses import asdict
        return {"trigger": asdict(self.trigger), **self.action, "label": self.label}


# ----------------------------------------------------------------------------- base actor
class Actor:
    TYPE = "car"

    def __init__(self, id, length=4.5, width=1.8, actions=(), visible=True, name="", color=None):
        self.id = int(id)
        self.length, self.width = float(length), float(width)
        self.actions = [a if isinstance(a, ScriptAction) else ScriptAction.from_dict(a) for a in actions]
        self.visible = bool(visible)
        self.name = name
        self.color = color
        self.active = True
        self.obey_rules = True
        self.x = self.y = self.psi = self.v = self.a = self.yaw_rate = 0.0
        self.lane_id, self.s, self.d = None, None, None

    def init(self, road):
        self._road = road

    def update_triggers(self, t, sim):
        events = []
        for i, act in enumerate(self.actions):
            if act.fired_at is not None:
                continue
            if act.condition_at is None and act.trigger.condition(t, self, sim):
                act.condition_at = t
            if act.condition_at is not None and t >= act.condition_at + act.trigger.delay - 1e-9:
                act.fired_at = t
                info = self.apply(act.action, t, sim) or {}
                events.append({"t": round(float(t), 6), "type": "trigger", "actor": self.id, "action": act.action.get("type"),
                               "label": act.label, "index": i, **info})
        return events

    def apply(self, action, t, sim):
        kind = action.get("type")
        if kind == "visible":
            self.visible = bool(action.get("value", True))
        elif kind == "ignore_rules":
            self.obey_rules = not bool(action.get("value", True))
        else:
            return {"ignored": True}
        return {}

    def compute(self, t, sim):
        pass

    def advance(self, t, dt, sim):
        pass

    def object_state(self):
        return ObjectState(id=self.id, type=self.TYPE, x=float(self.x), y=float(self.y), psi=float(self.psi),
                           v=float(self.v), a=float(self.a), length=self.length, width=self.width,
                           yaw_rate=float(self.yaw_rate), lane_id=self.lane_id,
                           s=None if self.s is None else float(self.s), d=None if self.d is None else float(self.d))


# ----------------------------------------------------------------------------- lane-bound vehicles
class LaneVehicle(Actor):
    TYPE = "car"

    def __init__(self, id, lane, s, v=None, d=0.0, route=None, idm_params=None, mobil=None, v_des=None, react=True,
                 obey_rules=True, length=4.5, width=1.8, lc_duration=4.0, a_lat_max=3.0, actions=(), visible=True,
                 name="", color=None):
        super().__init__(id, length, width, actions, visible, name, color)
        self.lane_id, self.s, self.d = lane, float(s), float(d)
        self.idm = idm_params or IDMParams()
        self.mobil = mobil
        self.v_des = float(self.idm.v0 if v_des is None else v_des)
        self.v = float(self.v_des if v is None else v)
        self.route = list(route or [])
        self.react, self.obey_rules = bool(react), bool(obey_rules)
        self.lc_duration, self.a_lat_max = float(lc_duration), float(a_lat_max)
        self.lat = None              # active lateral maneuver
        self.brake = None            # (decel, v_target) override
        self.a_cmd = 0.0
        self.last_lc = -1e9
        self.committed = set()       # stop lines already passed / released
        self.stopped_at = {}         # stop-sign line id -> time of the full stop

    def init(self, road):
        super().init(road)
        if self.lane_id not in road.lanes:
            raise KeyError(f"actor {self.id}: unknown lane '{self.lane_id}'")
        self._mobil_phase = (self.id * 0.37) % 1.0
        self._update_pose(0.0, 1.0)

    @property
    def lane(self):
        return self._road.lanes[self.lane_id]

    # ------------------------------------------------------------------ actions
    def apply(self, action, t, sim):
        kind = action.get("type")
        if kind == "lane_change":
            target = action.get("lane") or self.lane.neighbor(action.get("direction", "left"), self.s)
            if target is None:
                return {"failed": "keine Nachbarspur"}
            self.start_lane_change(target, t, float(action.get("duration", self.lc_duration)))
            return {"target_lane": target}
        if kind == "speed":
            self.v_des = float(action["v"])
            if "accel" in action:
                self.idm = replace(self.idm, a=float(action["accel"]))
            self.brake = None
        elif kind == "brake":
            self.brake = (float(action.get("decel", 6.0)), float(action.get("v", 0.0)))
        elif kind == "stop":
            self.brake = (float(action.get("decel", 3.0)), 0.0)
        elif kind == "route":
            self.route = list(action["lanes"])
        elif kind == "lateral_offset":
            self.lat = {"t0": t, "T": float(action.get("duration", 2.0)), "d0": self.d, "d1": float(action["d"]),
                        "src": None}
        elif kind == "react":
            self.react = bool(action.get("value", True))
        else:
            return super().apply(action, t, sim)
        return {}

    def start_lane_change(self, target, t, duration):
        lane_t = self._road.lanes[target]
        s_t, d_t = project_near(lane_t, self.x, self.y, self.s * lane_t.length / max(self.lane.length, 1e-6))
        self.lat = {"t0": t, "T": duration, "d0": float(d_t), "d1": 0.0, "src": self.lane_id,
                    "src_s0": float(self.s), "s_t0": float(s_t), "src_d0": float(self.d)}
        self.lane_id, self.s, self.d = target, float(s_t), float(d_t)
        self.last_lc = t

    # ------------------------------------------------------------------ longitudinal decision
    def desired_speed(self):
        # desired speed limited by the curvature ahead (a_lat_max), re-evaluated every 0.5 s of travel
        v0 = self.v_des
        if self.a_lat_max <= 0:
            return v0
        lane = self.lane
        k_bound = max([lane.kappa_max] + [self._road.lanes[x].kappa_max for x in lane.successors[:2]])
        if v0 * v0 * k_bound <= self.a_lat_max:
            return v0
        key = (self.lane_id, round(self.s / max(0.5 * max(self.v, 1.0), 1.0)))
        if getattr(self, "_curve_key", None) != key:
            self._curve_key = key
            self._curve_k = self._road_curvature_ahead(max(15.0, 3.0 * self.v))
        if self._curve_k > 1e-4:
            v0 = min(v0, np.sqrt(self.a_lat_max / self._curve_k))
        return v0

    def _road_curvature_ahead(self, dist):
        ss = self.s + np.linspace(0.0, dist, 6)
        lane, kmax = self.lane, 0.0
        inside = ss <= lane.length
        if np.any(inside):
            kmax = float(np.max(np.abs(lane.center.evaluate(ss[inside])[3])))
        if not np.all(inside):
            nxt = self._road.default_successor(self.lane_id, self.route)
            if nxt is not None:
                c = self._road.lanes[nxt].center
                kmax = max(kmax, float(np.max(np.abs(c.evaluate(ss[~inside] - lane.length)[3]))))
        return kmax

    def compute(self, t, sim):
        p = self.idm
        v0 = self.desired_speed()
        gap, v_lead = np.inf, self.v
        if self.react:
            lead = sim.leader(self.lane_id, self.s, self.id, max(150.0, 6.0 * self.v), self.route)
            if lead is not None:
                dist, item = lead
                gap, v_lead = dist - 0.5 * (self.length + item.length), item.v
        acc = idm(self.v, v0, gap, self.v - v_lead, p)
        if self.obey_rules:
            stop_gap = sim.stop_distance(self, t)
            if stop_gap is not None:
                acc = min(acc, idm(self.v, v0, stop_gap, self.v, p))
        self.a_idm = acc
        if self.brake is not None:
            decel, v_target = self.brake
            if self.v > v_target + 1e-3:
                acc = min(acc, -decel)
            else:
                self.v_des, self.brake = v_target, None
                acc = min(acc, 0.0) if v_target <= 1e-3 else acc
        if self.v_des <= 1e-3 and self.v <= 1e-3:
            acc = min(acc, 0.0)
        self.a_cmd = float(acc)
        if self.mobil is not None and self.lat is None and self.brake is None:
            m = self.mobil
            due = (t / m.interval + self._mobil_phase) % 1.0
            step = sim.h / m.interval
            if due < step and t - self.last_lc > m.cooldown:
                sim.mobil_decision(self, t)

    def advance(self, t, dt, sim):
        a, v = self.a_cmd, self.v
        v_new = v + a * dt
        if v_new < 0.0:
            ds = -0.5 * v * v / a if a < 0 else 0.0
            v_new = 0.0
        else:
            ds = v * dt + 0.5 * a * dt * dt
        self.v, self.a = v_new, a
        self.s += max(ds, 0.0)
        u_d = 0.0
        if self.lat is not None:
            lat = self.lat
            u = (t + dt - lat["t0"]) / lat["T"]
            self.d = lat["d0"] + (lat["d1"] - lat["d0"]) * float(smoothstep5(u))
            u_d = (lat["d1"] - lat["d0"]) * float(smoothstep5_d(u)) / lat["T"]
            if u >= 1.0:
                self.d, self.lat, u_d = lat["d1"], None, 0.0
        lane = self.lane
        if lane.closed:
            self.s %= lane.length
        else:
            while self.s > lane.length:
                nxt = self._road.default_successor(self.lane_id, self.route)
                if nxt is None:
                    self.active = False
                    return
                self.s -= lane.length
                self.lane_id = nxt
                lane = self.lane
                if self.lat is not None:
                    self.lat["src"] = None
        self._d_dot = u_d
        if not sim.batch_poses:
            self._update_pose(u_d, dt)

    def _update_pose(self, d_dot, dt):
        x, y, th, k, _ = self.lane.center.evaluate(self.s)
        psi = th + np.arctan2(d_dot, max(self.v * (1.0 - k * self.d), 0.5))
        self.yaw_rate = float(wrap_angle(psi - self.psi) / dt) if dt > 0 and hasattr(self, "_posed") else 0.0
        self._posed = True
        self.x, self.y, self.psi = x - self.d * np.sin(th), y + self.d * np.cos(th), float(psi)

    def source_position(self):
        # (lane, s) in the source lane during a lane change (occupancy of both lanes)
        lat = self.lat
        if lat is None or lat.get("src") is None:
            return None
        return lat["src"], lat["src_s0"] + (self.s - lat["s_t0"])

    def object_state(self):
        o = super().object_state()
        src = self.source_position()
        if src is not None and abs(self.d) > 0.5 * self.lane.width:
            # center still in the source lane: report the physically occupied lane
            src_lane = self._road.lanes[src[0]]
            s, d = src_lane.center.project(self.x, self.y)
            o.lane_id, o.s, o.d = src[0], float(s), float(d)
        return o


class Truck(LaneVehicle):
    TYPE = "truck"

    def __init__(self, id, lane, s, v=None, length=16.5, width=2.55, idm_params=None, lc_duration=6.0, **kw):
        idm_params = idm_params or IDMParams(v0=22.2, T=1.6, s0=3.0, a=0.6, b=1.5)
        super().__init__(id, lane, s, v, length=length, width=width, idm_params=idm_params, lc_duration=lc_duration,
                         **kw)


class Cyclist(LaneVehicle):
    TYPE = "cyclist"

    def __init__(self, id, lane, s, v=5.0, d=0.0, length=1.8, width=0.7, idm_params=None, **kw):
        idm_params = idm_params or IDMParams(v0=v if v else 5.0, T=1.0, s0=1.0, a=0.8, b=1.5)
        super().__init__(id, lane, s, v, d=d, length=length, width=width, idm_params=idm_params, **kw)


# ----------------------------------------------------------------------------- pedestrians / static
class Pedestrian(Actor):
    TYPE = "pedestrian"

    def __init__(self, id, path, speed=1.4, start=False, length=0.5, width=0.6, actions=(), visible=True, name="",
                 color=None):
        super().__init__(id, length, width, actions, visible, name, color)
        self.path = np.asarray(path, dtype=float)
        seg = np.diff(self.path, axis=0)
        self._seg_len = np.hypot(seg[:, 0], seg[:, 1])
        self._cum = np.concatenate([[0.0], np.cumsum(self._seg_len)])
        self.speed = float(speed)
        self.walking = bool(start)
        self.pos = 0.0
        self._place()

    def _place(self):
        i = int(np.clip(np.searchsorted(self._cum, self.pos, side="right") - 1, 0, len(self._seg_len) - 1))
        u = (self.pos - self._cum[i]) / max(self._seg_len[i], 1e-9)
        p = self.path[i] + u * (self.path[i + 1] - self.path[i])
        self.x, self.y = float(p[0]), float(p[1])
        dx, dy = self.path[i + 1] - self.path[i]
        self.psi = float(np.arctan2(dy, dx))

    def apply(self, action, t, sim):
        kind = action.get("type")
        if kind == "start":
            self.walking = True
            if "speed" in action:
                self.speed = float(action["speed"])
            if action.get("visible", True):
                self.visible = True
        elif kind == "halt":
            self.walking = False
        elif kind == "speed":
            self.speed = float(action["v"])
        else:
            return super().apply(action, t, sim)
        return {}

    def compute(self, t, sim):
        self.v = self.speed if self.walking and self.pos < self._cum[-1] else 0.0

    def advance(self, t, dt, sim):
        self.pos = min(self.pos + self.v * dt, self._cum[-1])
        if self.pos >= self._cum[-1]:
            self.walking, self.v = False, 0.0
        self._place()


class StaticObstacle(Actor):
    TYPE = "static"

    def __init__(self, id, x=None, y=None, psi=0.0, lane=None, s=None, d=0.0, length=4.5, width=1.8, obj_type="static",
                 actions=(), visible=True, name="", color=None):
        super().__init__(id, length, width, actions, visible, name, color)
        self.TYPE = obj_type
        self._spec = (x, y, psi, lane, s, d)

    def init(self, road):
        super().init(road)
        x, y, psi, lane, s, d = self._spec
        if lane is not None:
            px, py, th = road.lanes[lane].pose(s, d)
            self.x, self.y, self.psi = float(px), float(py), float(th + psi)
            self.lane_id, self.s, self.d = lane, float(s), float(d)
        else:
            self.x, self.y, self.psi = float(x), float(y), float(psi)
            loc = road.lane_at(self.x, self.y, margin=0.5 * self.width)
            if loc is not None:
                self.lane_id, self.s, self.d = loc.lane_id, loc.s, loc.d


# ----------------------------------------------------------------------------- simulator
class _Occ:
    __slots__ = ("id", "v", "length", "actor")

    def __init__(self, id, v, length, actor):
        self.id, self.v, self.length, self.actor = id, v, length, actor


class TrafficSimulator:
    def __init__(self, road, actors, max_dt=0.05, ego_length=4.8, ego_width=1.85):
        self.road = road
        self.actors = list(actors)
        self.by_id = {a.id: a for a in self.actors}
        if len(self.by_id) != len(self.actors) or EGO_ID in self.by_id:
            raise ValueError("actor ids must be unique and != 0 (ego)")
        self.max_dt = float(max_dt)
        self.ego = None
        self.ego_length, self.ego_width = ego_length, ego_width
        self.t, self.h = 0.0, max_dt
        self.batch_poses = True
        self.occ = {}
        self._stops = {}
        for sl in road.stop_lines:
            self._stops.setdefault(sl.lane_id, []).append(sl)
        self._yield_lanes = {}
        for sl in road.stop_lines:
            if sl.zone_id and sl.kind in ("yield", "stop"):
                self._yield_lanes.setdefault(sl.zone_id, set()).add(sl.lane_id)
        for a in self.actors:
            a.init(road)

    # ------------------------------------------------------------------ main loop
    def step(self, t, dt, ego=None):
        # advance all actors from t to t + dt (sub-steps <= max_dt); ego: ObjectState of the ego or None
        self.ego = ego
        events = []
        n = max(int(np.ceil(dt / self.max_dt - 1e-9)), 1)
        h = dt / n
        self.h = h
        tk = t
        for _ in range(n):
            active = [a for a in self.actors if a.active]
            self._build_occupancy(active)
            for a in active:
                events += a.update_triggers(tk, self)
            for a in active:
                a.compute(tk, self)
            for a in active:
                a.advance(tk, h, self)
            self._update_poses(active, h)
            tk += h
        self.t = t + dt
        return events

    def object_states(self, include_hidden=False):
        return [a.object_state() for a in self.actors if a.active and (include_hidden or a.visible)]

    def hidden_states(self):
        return [a.object_state() for a in self.actors if a.active and not a.visible]

    def _update_poses(self, active, dt):
        # vectorized pose update of the lane-bound vehicles (one curve evaluation per lane)
        groups = {}
        for a in active:
            if isinstance(a, LaneVehicle) and a.active:
                groups.setdefault(a.lane_id, []).append(a)
        for lane_id, vehs in groups.items():
            s = np.array([a.s for a in vehs])
            d = np.array([a.d for a in vehs])
            x, y, th, k, _ = self.road.lanes[lane_id].center.evaluate(s)
            v = np.array([a.v for a in vehs])
            ddot = np.array([getattr(a, "_d_dot", 0.0) for a in vehs])
            psi = th + np.arctan2(ddot, np.maximum(v * (1.0 - k * d), 0.5))
            px, py = x - d * np.sin(th), y + d * np.cos(th)
            for i, a in enumerate(vehs):
                a.yaw_rate = float(wrap_angle(psi[i] - a.psi) / dt) if dt > 0 else 0.0
                a.x, a.y, a.psi = float(px[i]), float(py[i]), float(psi[i])

    # ------------------------------------------------------------------ occupancy
    def _build_occupancy(self, active):
        occ = {}

        def add(lane, s, item):
            occ.setdefault(lane, []).append((float(s), item))

        for a in active:
            if isinstance(a, LaneVehicle):
                item = _Occ(a.id, a.v, a.length, a)
                add(a.lane_id, a.s, item)
                src = a.source_position()
                if src is not None:
                    add(src[0], src[1], item)
            elif isinstance(a, StaticObstacle):
                if a.lane_id is not None:
                    add(a.lane_id, a.s, _Occ(a.id, 0.0, a.length, a))
            else:
                for loc in self.road.locate_all(a.x, a.y, margin=0.5):
                    add(loc.lane_id, loc.s, _Occ(a.id, a.v, a.length, a))
        ego = self.ego
        if ego is not None:
            for loc in self.road.locate_all(ego.x, ego.y, margin=0.5 * self.ego_width, psi=ego.psi):
                add(loc.lane_id, loc.s, _Occ(EGO_ID, ego.v, self.ego_length, None))
        self.occ = {}
        for lane, items in occ.items():
            items.sort(key=lambda e: e[0])
            self.occ[lane] = ([e[0] for e in items], [e[1] for e in items])

    def leader(self, lane_id, s, self_id, lookahead=200.0, route=None):
        # nearest occupant ahead along the lane sequence: (center distance, _Occ) or None
        lane = self.road.lanes[lane_id]
        entry = self.occ.get(lane_id)
        if entry:
            ss, items = entry
            i = bisect_right(ss, s)
            for j in range(i, len(ss)):
                if items[j].id != self_id:
                    return ss[j] - s, items[j]
            if lane.closed:
                for j in range(i):
                    if items[j].id != self_id:
                        return ss[j] + lane.length - s, items[j]
        if lane.closed:
            return None
        offset, cur = lane.length - s, lane_id
        for _ in range(32):
            if offset > lookahead:
                return None
            nxt = self.road.default_successor(cur, route)
            if nxt is None or self.road.lanes[nxt].closed:
                return None
            entry = self.occ.get(nxt)
            if entry:
                ss, items = entry
                for j in range(len(ss)):
                    if items[j].id != self_id:
                        return offset + ss[j], items[j]
            offset += self.road.lanes[nxt].length
            cur = nxt
        return None

    def follower(self, lane_id, s, self_id):
        entry = self.occ.get(lane_id)
        if not entry:
            return None
        ss, items = entry
        lane = self.road.lanes[lane_id]
        i = bisect_left(ss, s) - 1
        for j in range(i, -1, -1):
            if items[j].id != self_id:
                return s - ss[j], items[j]
        if lane.closed:
            for j in range(len(ss) - 1, i, -1):
                if items[j].id != self_id:
                    return s + lane.length - ss[j], items[j]
        return None

    def alongside(self, lane_id, s, half_length, self_id):
        entry = self.occ.get(lane_id)
        if not entry:
            return False
        ss, items = entry
        lo, hi = bisect_left(ss, s - half_length - 20.0), bisect_right(ss, s + half_length + 20.0)
        for j in range(lo, hi):
            it = items[j]
            if it.id != self_id and abs(ss[j] - s) < half_length + 0.5 * it.length:
                return True
        return False

    # ------------------------------------------------------------------ traffic rules
    def stop_distance(self, veh, t):
        # bumper distance to the nearest stop line the vehicle has to respect (None = free)
        lane_id, s, offset = veh.lane_id, veh.s, 0.0
        front = 0.5 * veh.length
        for depth in range(3):
            for sl in self._stops.get(lane_id, ()):
                dist = offset + sl.s - s - front
                key = sl.id
                if key in veh.committed or dist < -0.5 or dist > 120.0:
                    continue
                if self._must_stop(veh, sl, dist, t):
                    return max(dist, 0.05)
                if dist < 2.0 + 0.5 * veh.v:
                    veh.committed.add(key)
            lane = self.road.lanes[lane_id]
            if lane.closed:
                return None
            offset += lane.length
            if offset - s > 120.0:
                return None
            nxt = self.road.default_successor(lane_id, veh.route)
            if nxt is None:
                return None
            lane_id = nxt
        return None

    def _must_stop(self, veh, sl, dist, t):
        if sl.kind == "traffic_light" and sl.light_id in self.road.traffic_lights:
            phase = self.road.traffic_lights[sl.light_id].phase(t)
            if phase in ("red", "red_yellow"):
                return True
            if phase == "yellow":
                return dist > veh.v ** 2 / (2 * 3.0)        # stop if possible with 3 m/s²
            return False
        if sl.kind == "stop":
            if sl.id not in veh.stopped_at:
                if veh.v < 0.1 and dist < 1.5:
                    veh.stopped_at[sl.id] = t
                return True
            if t - veh.stopped_at[sl.id] < 1.0:
                return True
        if sl.zone_id and sl.zone_id in self.road.conflict_zones:
            if dist > max(25.0, veh.v ** 2 / 2.0 + 10.0):
                return False                        # decide when close enough
            zone = self.road.conflict_zones[sl.zone_id]
            t_gap = 3.0 + float(np.hypot(zone.x - veh.x, zone.y - veh.y)) / max(veh.v, 4.0)
            return self.zone_blocked(sl.zone_id, veh.id, veh.x, veh.y, t_gap=t_gap)
        return False

    def zone_blocked(self, zone_id, self_id, x, y, t_gap=3.5):
        # gap acceptance: any vehicle (not waiting on a yielding lane) in the zone or reaching it within t_gap
        zone = self.road.conflict_zones[zone_id]
        yielding = self._yield_lanes.get(zone_id, set())
        cands = [(a.id, a.x, a.y, a.psi, a.v, a.lane_id) for a in self.actors
                 if a.active and a.id != self_id and isinstance(a, LaneVehicle)]
        if self.ego is not None and self_id != EGO_ID:
            e = self.ego
            cands.append((EGO_ID, e.x, e.y, e.psi, e.v, e.lane_id))
        for oid, ox, oy, opsi, ov, olane in cands:
            if olane in yielding:
                continue
            dx, dy = zone.x - ox, zone.y - oy
            dist = float(np.hypot(dx, dy))
            toward = dx * np.cos(opsi) + dy * np.sin(opsi) > 0
            if dist <= zone.radius and (toward or dist < 0.5 * zone.radius):
                return True
            if toward and dist - zone.radius < ov * t_gap:
                return True
        return False

    # ------------------------------------------------------------------ MOBIL
    def _idm_of(self, item):
        a = item.actor
        if isinstance(a, LaneVehicle):
            return a.idm, a.desired_speed()
        return IDMParams(), max(item.v, 1.0)

    def mobil_decision(self, veh, t):
        m = veh.mobil
        lane = veh.lane
        if lane.junction is not None or veh.v < 3.0:
            return False
        best = None
        lead = self.leader(veh.lane_id, veh.s, veh.id, 200.0, veh.route)
        fol = self.follower(veh.lane_id, veh.s, veh.id)
        for side in ("left", "right"):
            nb_id = lane.neighbor(side, veh.s)
            if nb_id is None or lane.opposite(side, veh.s) or lane.marking(side, veh.s) not in ("dashed", "none"):
                continue
            nb = self.road.lanes[nb_id]
            if nb.type != "driving" or lane.neighbor(side, veh.s + max(50.0, veh.v * m.duration)) != nb_id:
                continue
            s_t = float(project_near(nb, veh.x, veh.y, veh.s * nb.length / max(lane.length, 1e-6))[0])
            if self.alongside(nb_id, s_t, 0.5 * veh.length + veh.idm.s0, veh.id):
                continue
            # accelerations after / before the change
            lead_t = self.leader(nb_id, s_t, veh.id, 200.0, None)
            fol_t = self.follower(nb_id, s_t, veh.id)

            def acc(item_v, p, v0, gap_item):
                if gap_item is None:
                    return idm(item_v, v0, np.inf, 0.0, p)
                dist, other = gap_item
                return idm(item_v, v0, dist, item_v - other.v, p)

            def gap_of(dist_item, l_self):
                if dist_item is None:
                    return None
                dist, other = dist_item
                return dist - 0.5 * (l_self + other.length), other

            a_c = veh.a_idm
            a_c_new = acc(veh.v, veh.idm, veh.desired_speed(), gap_of(lead_t, veh.length))
            a_n = a_n_new = 0.0
            if fol_t is not None:
                dist_n, n_item = fol_t
                p_n, v0_n = self._idm_of(n_item)
                if isinstance(n_item.actor, (LaneVehicle,)) or n_item.id == EGO_ID:
                    lead_n = (dist_n + lead_t[0], lead_t[1]) if lead_t is not None else None
                    a_n = acc(n_item.v, p_n, v0_n, gap_of(lead_n, n_item.length))
                    gap_n = dist_n - 0.5 * (n_item.length + veh.length)
                    if gap_n < p_n.s0:
                        continue
                    a_n_new = idm(n_item.v, v0_n, gap_n, n_item.v - veh.v, p_n)
            a_o = a_o_new = 0.0
            if fol is not None and (isinstance(fol[1].actor, LaneVehicle) or fol[1].id == EGO_ID):
                dist_o, o_item = fol
                p_o, v0_o = self._idm_of(o_item)
                a_o = idm(o_item.v, v0_o, dist_o - 0.5 * (o_item.length + veh.length), o_item.v - veh.v, p_o)
                lead_o = (dist_o + lead[0], lead[1]) if lead is not None else None
                a_o_new = acc(o_item.v, p_o, v0_o, gap_of(lead_o, o_item.length))
            if lead_t is not None and lead_t[0] - 0.5 * (veh.length + lead_t[1].length) < veh.idm.s0:
                continue
            bias = m.bias_right if side == "right" else -m.bias_right
            ok, incentive, _ = mobil_incentive(a_c, a_c_new, a_n, a_n_new, a_o, a_o_new, m.politeness, m.threshold,
                                               bias, m.b_safe)
            if ok and (best is None or incentive > best[1]):
                best = (nb_id, incentive)
        if best is not None:
            veh.start_lane_change(best[0], t, m.duration)
            return True
        return False


def project_near(lane, x, y, s_guess, window=120):
    # projection onto a lane with a sample-index hint (cheap for long lanes)
    c = lane.center
    hint = int(np.clip((s_guess - c.s0) / max(c.length, 1e-9) * (len(c.s) - 1), 0, len(c.s) - 1))
    return c.project(x, y, hint=hint, window=window, max_jump=0.5 * lane.width + 5.0)


def clone_actors(actors):
    return copy.deepcopy(actors)
