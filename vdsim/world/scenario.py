"""AD scenario specification (JSON), scenario-type registry and scenario instances.

    ADScenario        serializable specification: type, parameters, seed, duration, vehicle preset,
                      ego start, mission and success criteria (configs/ad_scenarios/*.json)
    ScenarioInstance  built scenario (docs/specs/contracts.md, section 8): road, actors, ego_initial,
                      mission, duration, success, metadata (+ disturbances, name, seed, vehicle)
    build_scenario    spec / file name / type name -> ScenarioInstance (deterministic for a seed)

Mission format (dict):
    route          [lane ids] in driving order; consecutive entries are successors or lateral
                   neighbors (lane change required), e.g. ["hw_2", "exit", "exit_ramp"]
    target_speed   m/s (default: speed limit)
    goal           {"lane", "s"} and/or {"x", "y", "radius"}, "stop": bool (stop at the goal)
    permissions    {"lane_change", "overtake", "use_opposite_lane", "reverse"} (bool)
    speed_profile  [[t, v], ...] piecewise constant target speed over time
    parking        {"spot", "drive_lane", "parking_lane", "v_approach", "v_reverse", "reverse_length"}
"""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

import numpy as np

from ..core.logging_setup import get_logger
from ..core.parameters import default_config_dir
from ..framework.context import stable_seed

log = get_logger("world.scenario")

SCENARIO_DIR = default_config_dir() / "ad_scenarios"
_TYPES = {}


@dataclass
class ScenarioType:
    name: str
    label: str
    description: str
    builder: object
    defaults: dict = field(default_factory=dict)
    duration: float = 30.0


def scenario_type(name, label, description="", defaults=None, duration=30.0):
    # decorator registering a scenario builder: builder(params, rng) -> dict
    def deco(fn):
        _TYPES[name] = ScenarioType(name, label, description, fn, dict(defaults or {}), duration)
        return fn
    return deco


def scenario_types():
    _ensure_library()
    return dict(_TYPES)


def list_scenario_types():
    _ensure_library()
    return [{"name": t.name, "label": t.label, "description": t.description, "defaults": dict(t.defaults),
             "duration": t.duration} for t in _TYPES.values()]


def _ensure_library():
    from . import library  # noqa: F401  (registers the scenario types)


# ----------------------------------------------------------------------------- specification
@dataclass
class ADScenario:
    name: str = ""
    type: str = "highway_driving"
    description: str = ""
    params: dict = field(default_factory=dict)
    seed: int = 0
    duration: float = 0.0                 # 0 = default of the scenario type
    vehicle: str = "mid_size_sedan"       # vehicle preset (configs/vehicles)
    ego: dict = field(default_factory=dict)       # overrides: {"lane", "s", "d", "v"} or {"x", "y", "psi", "v"}
    mission: dict = field(default_factory=dict)   # merged into the mission of the type
    success: dict = field(default_factory=dict)   # merged into the success criteria of the type
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            log.warning("ignoring unknown AD scenario keys %s", sorted(unknown))
        return cls(**{k: copy.deepcopy(v) for k, v in data.items() if k in known})

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        spec = cls.from_dict(data)
        spec.name = spec.name or Path(path).stem
        return spec


@dataclass
class ScenarioInstance:
    road: object
    actors: list
    ego_initial: dict
    mission: dict
    duration: float
    success: dict
    metadata: dict = field(default_factory=dict)
    name: str = ""
    seed: int = 0
    vehicle: str = "mid_size_sedan"
    disturbances: list = field(default_factory=list)   # scheduled events (e.g. lateral_impulse)
    spec: object = None

    def fresh_actors(self):
        # independent copies (the instance stays reusable for repeated runs)
        return copy.deepcopy(self.actors)

    def simulator(self, max_dt=0.05, ego_length=4.8, ego_width=1.85):
        from .actors import TrafficSimulator
        return TrafficSimulator(self.road, self.fresh_actors(), max_dt, ego_length, ego_width)


def load_ad_scenario(name_or_path):
    path = Path(name_or_path)
    if not path.suffix:
        path = SCENARIO_DIR / f"{name_or_path}.json"
    return ADScenario.load(path)


def list_ad_scenarios():
    # library scenarios (configs/ad_scenarios) with type label and description
    _ensure_library()
    out = []
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        try:
            spec = ADScenario.load(path)
        except Exception as exc:  # broken files must not break the list
            log.warning("cannot read %s: %s", path, exc)
            continue
        t = _TYPES.get(spec.type)
        out.append({"name": spec.name, "type": spec.type, "label": t.label if t else spec.type,
                    "description": spec.description, "path": str(path), "duration": spec.duration,
                    "seed": spec.seed})
    return out


def _resolve_spec(spec_or_name):
    _ensure_library()
    if isinstance(spec_or_name, ADScenario):
        return copy.deepcopy(spec_or_name)
    if isinstance(spec_or_name, dict):
        return ADScenario.from_dict(spec_or_name)
    text = str(spec_or_name)
    path = Path(text)
    if path.suffix and path.exists():
        return ADScenario.load(path)
    if (SCENARIO_DIR / f"{text}.json").exists():
        return load_ad_scenario(text)
    if text in _TYPES:
        return ADScenario(name=text, type=text, description=_TYPES[text].description)
    raise KeyError(f"unknown AD scenario '{text}' (types: {sorted(_TYPES)})")


def ego_on_lane(road, lane, s, d=0.0, v=0.0, psi_offset=0.0):
    # ego start pose (CoG) on a lane
    x, y, th = road.lanes[lane].pose(float(s), float(d))
    return {"x": float(x), "y": float(y), "psi": float(th + psi_offset), "v": float(v), "lane": lane,
            "s": float(s), "d": float(d)}


def build_scenario(spec_or_name, seed=None):
    # ADScenario | dict | file / library name | type name -> ScenarioInstance
    spec = _resolve_spec(spec_or_name)
    if seed is not None:
        spec.seed = int(seed)
    if spec.type not in _TYPES:
        raise KeyError(f"unknown scenario type '{spec.type}'")
    st = _TYPES[spec.type]
    params = {**st.defaults, **(spec.params or {})}
    rng = np.random.default_rng(stable_seed(spec.seed, "scenario", spec.type))
    out = st.builder(params, rng)
    road = out["road"]
    ego = dict(out.get("ego", {}))
    ego.update(spec.ego or {})
    if "lane" in ego and not ({"x", "y"} <= set(spec.ego or {})):
        ego = ego_on_lane(road, ego["lane"], ego.get("s", 0.0), ego.get("d", 0.0), ego.get("v", 0.0),
                          ego.get("psi_offset", 0.0))
    mission = _deep_merge(out.get("mission", {}), spec.mission or {})
    duration = float(spec.duration or out.get("duration") or st.duration)
    success = {"no_collision": True, "stay_on_road": True, **out.get("success", {}), **(spec.success or {})}
    meta = {"type": spec.type, "label": st.label, "description": spec.description or st.description,
            "params": params, **out.get("metadata", {}), **(spec.metadata or {})}
    return ScenarioInstance(road=road, actors=out.get("actors", []), ego_initial=ego, mission=mission,
                            duration=duration, success=success, metadata=meta, name=spec.name or spec.type,
                            seed=spec.seed, vehicle=spec.vehicle, disturbances=list(out.get("disturbances", [])),
                            spec=spec)


def _deep_merge(a, b):
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


# ----------------------------------------------------------------------------- evaluation
def evaluate_success(instance, ego_states, worlds=()):
    # check the success criteria against a run: ego_states = list of EgoState (or dicts x, y, psi, v),
    # worlds = list of WorldState; returns {"passed": bool, "criteria": {name: (ok, detail)}}
    crit = instance.success or {}
    res = {}
    worlds = list(worlds)
    states = [e if not isinstance(e, dict) else type("E", (), e) for e in ego_states]
    last = states[-1] if states else None
    if crit.get("no_collision"):
        hits = [w.collision_with for w in worlds if w.collision]
        res["no_collision"] = (not hits, f"Kollision mit {hits[0]}" if hits else "keine Kollision")
    if crit.get("stay_on_road"):
        off = sum(1 for w in worlds if w.off_road)
        res["stay_on_road"] = (off == 0, f"{off} Schritte neben der Fahrbahn")
    goal = crit.get("reach_goal")
    if goal and last is not None:
        g = instance.mission.get("goal", {}) if goal is True else goal
        ok, detail = _goal_reached(instance.road, g, last)
        res["reach_goal"] = (ok, detail)
    if "final_speed_max" in crit and last is not None:
        v = float(np.hypot(getattr(last, "vx", getattr(last, "v", 0.0)), getattr(last, "vy", 0.0)))
        res["final_speed_max"] = (v <= crit["final_speed_max"], f"v_end = {v:.2f} m/s")
    if "final_lane" in crit and last is not None:
        lanes = crit["final_lane"] if isinstance(crit["final_lane"], list) else [crit["final_lane"]]
        loc = instance.road.lane_at(last.x, last.y, getattr(last, "psi", None), margin=0.3)
        res["final_lane"] = (loc is not None and loc.lane_id in lanes, f"Spur {loc.lane_id if loc else '-'}")
    if "parked" in crit and last is not None:
        p = crit["parked"]
        spot = instance.road.parking_spots[p["spot"]]
        err = float(np.hypot(last.x - spot.x, last.y - spot.y))
        yaw = abs(float((last.psi - spot.psi + np.pi) % (2 * np.pi) - np.pi))
        res["parked"] = (err <= p.get("pos_tol", 0.6) and yaw <= p.get("yaw_tol", 0.15),
                         f"Abstand {err:.2f} m, Winkel {np.degrees(yaw):.1f}°")
    if "min_progress" in crit and states:
        dist = float(np.sum(np.hypot(np.diff([e.x for e in states]), np.diff([e.y for e in states]))))
        res["min_progress"] = (dist >= crit["min_progress"], f"{dist:.0f} m gefahren")
    passed = all(ok for ok, _ in res.values())
    return {"passed": passed, "criteria": res}


def _goal_reached(road, goal, ego):
    if "x" in goal and "y" in goal:
        dist = float(np.hypot(ego.x - goal["x"], ego.y - goal["y"]))
        return dist <= goal.get("radius", 5.0), f"Abstand zum Ziel {dist:.1f} m"
    if "lane" in goal:
        lane = road.lanes[goal["lane"]]
        s, d = lane.center.project(ego.x, ego.y)
        ok = abs(d) <= 0.5 * lane.width + 0.5 and s >= goal.get("s", 0.0) - goal.get("radius", 5.0)
        return ok, f"s = {s:.1f} m auf {lane.id}"
    return False, "kein Ziel definiert"
