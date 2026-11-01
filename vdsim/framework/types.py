"""Signal data types exchanged between components.

Every port of a Component declares one of the type names registered in TYPES. The
graph editor and the executor use `compatible()` for the data type check. Native
(C++/Rust) nodes exchange flat float64 arrays; `encode()` / `decode()` define the
layout of every type (see docs/specs/contracts.md, section "Codecs").

Conventions (SI units, earth-fixed frame x east / y north, angles counter-clockwise):
    EgoState            center of gravity (CoG), velocities in the vehicle frame
    PlannedTrajectory   reference point given by `reference_point` ("cog" or "rear_axle"),
                        theta = direction of motion, v >= 0 = speed along the motion,
                        direction = +1 forward / -1 reverse (Werling: varsigma)
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any

import numpy as np

from ..simulation.vehicle_state import ControlInput


# ----------------------------------------------------------------------------- ego / objects
@dataclass
class EgoState:
    t: float = 0.0
    x: float = 0.0            # CoG position
    y: float = 0.0
    psi: float = 0.0          # vehicle orientation (yaw)
    vx: float = 0.0           # longitudinal velocity, vehicle frame (negative when reversing)
    vy: float = 0.0           # lateral velocity at the CoG, vehicle frame
    r: float = 0.0            # yaw rate
    ax: float = 0.0           # longitudinal acceleration, vehicle frame
    ay: float = 0.0           # lateral acceleration, vehicle frame
    delta: float = 0.0        # front road-wheel angle
    delta_rate: float = 0.0   # front road-wheel angle rate
    gear: int = 1             # +1 forward, -1 reverse, 0 neutral

    @property
    def speed(self):
        return float(np.hypot(self.vx, self.vy))

    @property
    def beta(self):
        # side slip angle at the CoG (defined for forward motion)
        return float(np.arctan2(self.vy, max(abs(self.vx), 0.1)))

    @property
    def course(self):
        # direction of motion of the CoG
        if self.vx < -0.05:
            return float(self.psi + np.pi + np.arctan2(-self.vy, -self.vx))
        return float(self.psi + self.beta)

    def rear_axle(self, cg_to_rear):
        # position of the rear-axle center (reference point of the kinematic controllers)
        return (self.x - cg_to_rear * np.cos(self.psi), self.y - cg_to_rear * np.sin(self.psi))

    def point_ahead(self, distance):
        # vehicle-fixed point on the longitudinal axis `distance` ahead of the CoG
        return (self.x + distance * np.cos(self.psi), self.y + distance * np.sin(self.psi))

    @classmethod
    def from_vehicle_state(cls, vs, delta_rate=0.0, gear=1):
        # vdsim.simulation.vehicle_state.VehicleState -> EgoState
        return cls(t=vs.t, x=vs.x, y=vs.y, psi=vs.psi, vx=vs.vx, vy=vs.vy, r=vs.r, ax=vs.ax, ay=vs.ay,
                   delta=vs.delta_f, delta_rate=delta_rate, gear=gear)


OBJECT_TYPES = ("car", "truck", "pedestrian", "cyclist", "static", "unknown")


@dataclass
class ObjectState:
    id: int = 0
    type: str = "car"
    x: float = 0.0            # geometric center
    y: float = 0.0
    psi: float = 0.0
    v: float = 0.0            # speed along psi
    a: float = 0.0
    length: float = 4.5
    width: float = 1.8
    yaw_rate: float = 0.0
    lane_id: str | None = None
    s: float | None = None    # Frenet position on lane_id (if known)
    d: float | None = None


@dataclass
class ObjectList:
    t: float = 0.0
    objects: list = field(default_factory=list)   # list[ObjectState]

    def by_id(self, obj_id):
        for o in self.objects:
            if o.id == obj_id:
                return o
        return None


@dataclass
class PredictedObject:
    # predicted motion of one object; arrays share the time base t (absolute time)
    id: int = 0
    type: str = "car"
    length: float = 4.5
    width: float = 1.8
    t: np.ndarray = field(default_factory=lambda: np.zeros(0))
    x: np.ndarray = field(default_factory=lambda: np.zeros(0))
    y: np.ndarray = field(default_factory=lambda: np.zeros(0))
    psi: np.ndarray = field(default_factory=lambda: np.zeros(0))
    v: np.ndarray = field(default_factory=lambda: np.zeros(0))
    probability: float = 1.0
    lane_id: str | None = None
    s: np.ndarray | None = None      # Frenet prediction on lane_id (Werling 3.5.2: s_v(t))
    s_dot: np.ndarray | None = None

    def state_at(self, t):
        # (x, y, psi, v) at absolute time t (held constant outside the prediction horizon)
        if len(self.t) == 0:
            return 0.0, 0.0, 0.0, 0.0
        psi = np.unwrap(self.psi)
        return (float(np.interp(t, self.t, self.x)), float(np.interp(t, self.t, self.y)),
                float(np.interp(t, self.t, psi)), float(np.interp(t, self.t, self.v)))


@dataclass
class Prediction:
    t0: float = 0.0
    objects: list = field(default_factory=list)   # list[PredictedObject]

    def by_id(self, obj_id):
        for o in self.objects:
            if o.id == obj_id:
                return o
        return None


# ----------------------------------------------------------------------------- behavior -> planner
LONGITUDINAL_MODES = ("velocity", "following", "merging", "stopping")


@dataclass
class LongitudinalMode:
    # One active longitudinal operating mode (Werling Tab. 3.1):
    #   velocity   params: v_ref
    #   following  params: lead_id, k0 (standstill gap), kv (time gap)
    #   merging    params: front_id, rear_id (gap between two vehicles, eq. 3.15)
    #   stopping   params: s_stop (Frenet position on the reference line)
    kind: str = "velocity"
    params: dict = field(default_factory=dict)


@dataclass
class BehaviorCommand:
    t: float = 0.0
    reference_line: Any = None        # vdsim.geometry.ReferenceLine of the target lane
    lane_id: str | None = None
    target_speed: float = 0.0
    modes: list = field(default_factory=list)   # list[LongitudinalMode]
    d_ref: float = 0.0                # lateral reference offset (Werling 3.5.1)
    d_min: float = -1e9               # box restriction for d(t) (drivable corridor, right bound)
    d_max: float = 1e9                # (left bound); the vehicle footprint must stay inside
    direction: int = 1                # +1 forward, -1 reverse
    reinit: bool = False              # request a re-initialization of the planner
    maneuver: str = "lane_keeping"    # lane_keeping / lane_change_left / ... (for display)
    info: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- planner output
TRAJECTORY_FIELDS = ("t", "x", "y", "theta", "kappa", "dkappa", "v", "a", "s", "d")


@dataclass
class TrajectoryPoint:
    t: float = 0.0
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0       # direction of motion
    kappa: float = 0.0       # curvature of the path, signed w.r.t. the direction of motion
    dkappa: float = 0.0      # d kappa / d arc length
    v: float = 0.0           # speed along the motion (>= 0)
    a: float = 0.0           # dv/dt
    s: float = 0.0           # Frenet coordinates on the planner's reference line
    d: float = 0.0
    direction: int = 1

    @property
    def psi(self):
        # vehicle orientation of the reference point (Werling psi_d = atan2(sigma*y2', sigma*y1'))
        return self.theta if self.direction > 0 else self.theta + np.pi

    @property
    def v_signed(self):
        # Werling v_d = sigma * s_dot_d
        return self.direction * self.v

    @property
    def a_signed(self):
        return self.direction * self.a


@dataclass
class PlannedTrajectory:
    t: np.ndarray = field(default_factory=lambda: np.zeros(0))   # absolute time
    x: np.ndarray = field(default_factory=lambda: np.zeros(0))
    y: np.ndarray = field(default_factory=lambda: np.zeros(0))
    theta: np.ndarray = field(default_factory=lambda: np.zeros(0))
    kappa: np.ndarray = field(default_factory=lambda: np.zeros(0))
    dkappa: np.ndarray = field(default_factory=lambda: np.zeros(0))
    v: np.ndarray = field(default_factory=lambda: np.zeros(0))
    a: np.ndarray = field(default_factory=lambda: np.zeros(0))
    s: np.ndarray = field(default_factory=lambda: np.zeros(0))
    d: np.ndarray = field(default_factory=lambda: np.zeros(0))
    direction: int = 1
    reference_point: str = "cog"      # "cog" (fast driving) or "rear_axle" (slow driving)
    lateral_mode: str = "time"        # "time" = d(t), "arc" = d(s)   (Werling 3.5.1)
    longitudinal_mode: str = "velocity"
    cost: float = 0.0
    valid: bool = True                # False: fallback trajectory (no candidate satisfied all restrictions)
    reinitialized: bool = False       # planned from the predicted vehicle state (high-level stabilization)
    plan: Any = None                  # exact Frenet representation (planner specific, optional)
    reference_line: Any = None
    metadata: dict = field(default_factory=dict)

    def __len__(self):
        return len(self.t)

    @property
    def empty(self):
        return len(self.t) == 0

    @property
    def t_start(self):
        return float(self.t[0]) if len(self.t) else 0.0

    @property
    def t_end(self):
        return float(self.t[-1]) if len(self.t) else 0.0

    def sample(self, t):
        # Interpolated TrajectoryPoint at absolute time t (clamped to the trajectory)
        if self.empty:
            return TrajectoryPoint(t=t, direction=self.direction)
        tt = self.t
        if t <= tt[0]:
            i, w = 0, 0.0
        elif t >= tt[-1]:
            i, w = len(tt) - 2, 1.0
        else:
            i = int(np.searchsorted(tt, t, side="right") - 1)
            w = (t - tt[i]) / max(tt[i + 1] - tt[i], 1e-12)
        if len(tt) == 1:
            return TrajectoryPoint(t, float(self.x[0]), float(self.y[0]), float(self.theta[0]), float(self.kappa[0]),
                                   float(self.dkappa[0]), float(self.v[0]), float(self.a[0]), float(self.s[0]),
                                   float(self.d[0]), self.direction)

        def lerp(arr):
            return float(arr[i] + w * (arr[i + 1] - arr[i]))

        dth = (self.theta[i + 1] - self.theta[i] + np.pi) % (2 * np.pi) - np.pi
        return TrajectoryPoint(t=float(t), x=lerp(self.x), y=lerp(self.y), theta=float(self.theta[i] + w * dth),
                               kappa=lerp(self.kappa), dkappa=lerp(self.dkappa), v=lerp(self.v), a=lerp(self.a),
                               s=lerp(self.s), d=lerp(self.d), direction=self.direction)

    def arrays(self):
        return {name: getattr(self, name) for name in TRAJECTORY_FIELDS}

    def copy(self):
        out = PlannedTrajectory(**{n: np.array(getattr(self, n), dtype=float) for n in TRAJECTORY_FIELDS})
        for f in fields(self):
            if f.name not in TRAJECTORY_FIELDS:
                setattr(out, f.name, getattr(self, f.name))
        out.metadata = dict(self.metadata)
        return out


@dataclass
class PlannerDebug:
    # Snapshot of one planning cycle for visualization / analysis (kept small: subsampled candidates)
    t: float = 0.0
    start_state: dict = field(default_factory=dict)
    candidates_x: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.float32))  # (n, k)
    candidates_y: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.float32))
    candidates_s: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.float32))  # Frenet view
    candidates_d: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.float32))
    candidates_cost: np.ndarray = field(default_factory=lambda: np.zeros(0))
    candidates_status: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int8))   # 0 valid, 1 constraint, 2 collision, 3 not checked
    candidates_reason: list = field(default_factory=list)      # violated constraint / colliding object per candidate
    best_index: int = -1
    cost_terms: dict = field(default_factory=dict)             # cost breakdown of the selected trajectory
    constraint_violations: dict = field(default_factory=dict)  # constraint name -> number of rejected candidates
    n_candidates: int = 0
    n_checked: int = 0
    mode: str = ""
    modes: dict = field(default_factory=dict)                  # per longitudinal mode: best cost, initial jerk
    reinitialized: bool = False
    fallback: bool = False
    compute_time: float = 0.0
    collision_circles: dict = field(default_factory=dict)      # ego/obstacle circle radii and safety margin ramp
    info: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- control
@dataclass
class ControlCommand:
    # Output of the trajectory tracking controller. Unused fields are None.
    t: float = 0.0
    steer_rate: float | None = None     # front road-wheel angle rate (Werling input u1 = delta_dot)
    steer_angle: float | None = None    # front road-wheel angle (classical controllers)
    force: float | None = None          # total longitudinal tire force F_l (Werling input u2)
    accel: float | None = None          # longitudinal acceleration request
    direction: int = 1
    controller: str = ""
    info: dict = field(default_factory=dict)


@dataclass
class ControllerStatus:
    # Invariant tracking errors and the re-initialization request (bi-level stabilization, Werling 2.3/4.5)
    t: float = 0.0
    e_t: float = 0.0          # longitudinal tracking error (Frenet frame of the desired trajectory)
    e_n: float = 0.0          # lateral tracking error
    e_theta: float = 0.0      # orientation / course error
    e_v: float = 0.0          # speed error
    e_t_dot: float = 0.0
    e_n_dot: float = 0.0
    reinit_request: bool = False
    active_controller: str = ""
    lookahead: float = 0.0    # lambda of the reference point
    prediction: Any = None    # predicted vehicle state for the re-initialization (dict), Werling 4.5.2
    info: dict = field(default_factory=dict)
    horizon_x: np.ndarray | None = None   # MPC prediction horizon (if the controller has one)
    horizon_y: np.ndarray | None = None


@dataclass
class ActuatorCommand:
    # Wheel-level demands produced by the vehicle-dynamics layer
    t: float = 0.0
    steer_angle: float = 0.0
    steer_rate: float = 0.0
    steer_rear: float = 0.0
    drive_torque: np.ndarray = field(default_factory=lambda: np.zeros(4))
    brake_torque: np.ndarray = field(default_factory=lambda: np.zeros(4))
    info: dict = field(default_factory=dict)


@dataclass
class WorldState:
    # Ground truth produced by the scenario engine
    t: float = 0.0
    objects: list = field(default_factory=list)       # list[ObjectState] (ground truth)
    road: Any = None                                   # vdsim.world RoadNetwork
    traffic_lights: dict = field(default_factory=dict)  # id -> "red" / "yellow" / "green"
    collision: bool = False
    collision_with: int | None = None
    off_road: bool = False
    events: list = field(default_factory=list)
    info: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- type registry
TYPES = {
    "Any": object,
    "float": float,
    "Vector": np.ndarray,
    "bool": bool,
    "EgoState": EgoState,
    "ObjectList": ObjectList,
    "Prediction": Prediction,
    "BehaviorCommand": BehaviorCommand,
    "PlannedTrajectory": PlannedTrajectory,
    "PlannerDebug": PlannerDebug,
    "ControlCommand": ControlCommand,
    "ControllerStatus": ControllerStatus,
    "ActuatorCommand": ActuatorCommand,
    "ControlInput": ControlInput,
    "WorldState": WorldState,
    "ReferenceLine": object,     # vdsim.geometry.ReferenceLine (kept generic to avoid an import cycle)
}

TYPE_DESCRIPTIONS = {
    "Any": "beliebiger Wert (keine Typprüfung)",
    "float": "Skalar",
    "Vector": "Zahlenvektor (numpy)",
    "bool": "Wahrheitswert",
    "EgoState": "Fahrzeugzustand im Schwerpunkt",
    "ObjectList": "erkannte Objekte",
    "Prediction": "prädizierte Objekttrajektorien",
    "BehaviorCommand": "Vorgaben der Verhaltensebene (Referenzkurve, Längsmodi, Korridor)",
    "PlannedTrajectory": "Solltrajektorie",
    "PlannerDebug": "Planer-Momentaufnahme (Kandidaten, Kosten, Restriktionen)",
    "ControlCommand": "Stellgrößen der Trajektorienregelung",
    "ControllerStatus": "Trackingfehler und Reinitialisierungsanforderung",
    "ActuatorCommand": "Radindividuelle Stellanforderungen",
    "ControlInput": "an der Strecke wirksame Stellgrößen",
    "WorldState": "Ground Truth der Szenario-Engine",
    "ReferenceLine": "Referenzkurve",
}

# color per type in the graph editor (categorical, fixed order)
TYPE_COLORS = {
    "Any": "#9a9ca3", "float": "#c8c8c8", "Vector": "#c8c8c8", "bool": "#c8c8c8",
    "EgoState": "#3987e5", "ObjectList": "#d29922", "Prediction": "#e3a33b", "BehaviorCommand": "#a371f7",
    "PlannedTrajectory": "#3fb950", "PlannerDebug": "#6e7681", "ControlCommand": "#f85149",
    "ControllerStatus": "#ff7b72", "ActuatorCommand": "#db61a2", "ControlInput": "#f778ba",
    "WorldState": "#56d4dd", "ReferenceLine": "#8b949e",
}


def register_type(name, py_type, description="", color="#c8c8c8"):
    # Plugins may add their own signal types (custom nodes with new interfaces)
    TYPES[name] = py_type
    TYPE_DESCRIPTIONS[name] = description
    TYPE_COLORS[name] = color


def compatible(output_type, input_type):
    # Data type check of a connection output -> input
    if output_type not in TYPES:
        raise KeyError(f"unknown signal type '{output_type}'")
    if input_type not in TYPES:
        raise KeyError(f"unknown signal type '{input_type}'")
    if "Any" in (output_type, input_type) or output_type == input_type:
        return True
    return {output_type, input_type} <= {"float", "Vector"}


def check_value(type_name, value):
    # Runtime check of a value against a port type (used by the debugger / custom nodes)
    if value is None or type_name == "Any":
        return True
    py = TYPES.get(type_name, object)
    if type_name == "float":
        return isinstance(value, (int, float, np.floating, np.integer))
    if type_name == "Vector":
        return isinstance(value, (np.ndarray, list, tuple, int, float))
    return isinstance(value, py) or py is object


def summarize(value, max_len=60):
    # Short human-readable description of a signal value (live wire labels, tooltips)
    if value is None:
        return "-"
    if isinstance(value, (float, int, np.floating, np.integer)):
        return f"{float(value):.4g}"
    if isinstance(value, np.ndarray):
        return f"array{value.shape}"
    if isinstance(value, EgoState):
        return f"v={value.speed:.2f} m/s  psi={np.degrees(value.psi):.1f}°"
    if isinstance(value, PlannedTrajectory):
        return f"{len(value)} Pkt, {value.longitudinal_mode}, J={value.cost:.3g}{'' if value.valid else ' (Fallback)'}"
    if isinstance(value, ControlCommand):
        parts = [f"{k}={getattr(value, k):.3g}" for k in ("steer_rate", "steer_angle", "force", "accel")
                 if getattr(value, k) is not None]
        return ", ".join(parts) or "-"
    if isinstance(value, (ObjectList, Prediction, WorldState)):
        return f"{len(value.objects)} Objekte"
    if isinstance(value, BehaviorCommand):
        return f"{value.maneuver}, v_soll={value.target_speed:.1f}, Modi={[m.kind for m in value.modes]}"
    if isinstance(value, ControllerStatus):
        return f"e_n={value.e_n:.3f} e_t={value.e_t:.3f} {value.active_controller}"
    text = repr(value)
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


# ----------------------------------------------------------------------------- flat codecs (native nodes)
EGO_FIELDS = ("t", "x", "y", "psi", "vx", "vy", "r", "ax", "ay", "delta", "delta_rate", "gear")
COMMAND_FIELDS = ("t", "steer_rate", "steer_angle", "force", "accel", "direction")
OBJECT_FIELDS = ("id", "type", "x", "y", "psi", "v", "a", "length", "width")
REFERENCE_FIELDS = ("s", "x", "y", "theta", "kappa", "dkappa")
PREDICTION_FIELDS = ("t", "x", "y", "psi", "v")
CODEC_VERSION = 1


def _nan_if_none(v):
    return np.nan if v is None else float(v)


def encode(type_name, value):
    # Python value -> flat float64 array (layout documented in docs/specs/contracts.md)
    if value is None:
        return np.zeros(0)
    if type_name in ("float", "bool"):
        return np.array([float(value)])
    if type_name == "Vector":
        return np.asarray(value, dtype=float).ravel()
    if type_name == "EgoState":
        return np.array([float(getattr(value, f)) for f in EGO_FIELDS])
    if type_name == "ControlCommand":
        return np.array([_nan_if_none(getattr(value, f)) for f in COMMAND_FIELDS])
    if type_name == "PlannedTrajectory":
        n = len(value)
        head = [n, value.direction, 0.0 if value.reference_point == "cog" else 1.0, value.cost, float(value.valid)]
        arrs = value.arrays()
        body = np.column_stack([arrs[f] for f in TRAJECTORY_FIELDS]).ravel() if n else np.zeros(0)
        return np.concatenate([head, body])
    if type_name in ("ObjectList", "WorldState"):
        objs = value.objects
        rows = [[o.id, OBJECT_TYPES.index(o.type) if o.type in OBJECT_TYPES else 5, o.x, o.y, o.psi, o.v, o.a,
                 o.length, o.width] for o in objs]
        return np.concatenate([[len(objs)], np.asarray(rows, dtype=float).ravel()])
    if type_name == "Prediction":
        out = [len(value.objects)]
        for o in value.objects:
            k = len(o.t)
            out += [o.id, OBJECT_TYPES.index(o.type) if o.type in OBJECT_TYPES else 5, o.length, o.width, k]
            out += list(np.column_stack([o.t, o.x, o.y, o.psi, o.v]).ravel())
        return np.asarray(out, dtype=float)
    if type_name == "ReferenceLine":
        arr = np.column_stack([value.s, value.x, value.y, value.theta, value.kappa, value.dkappa])
        return np.concatenate([[len(value.s)], arr.ravel()])
    raise TypeError(f"no flat codec for type '{type_name}'")


def decode(type_name, arr):
    # flat float64 array -> Python value
    arr = np.asarray(arr, dtype=float)
    if type_name == "float":
        return float(arr[0]) if arr.size else 0.0
    if type_name == "bool":
        return bool(arr[0]) if arr.size else False
    if type_name == "Vector":
        return arr.copy()
    if type_name == "EgoState":
        vals = {k: float(v) for k, v in zip(EGO_FIELDS, arr)}
        vals["gear"] = int(round(vals["gear"]))
        return EgoState(**vals)
    if type_name == "ControlCommand":
        vals = {f: (None if np.isnan(v) else float(v)) for f, v in zip(COMMAND_FIELDS, arr)}
        vals["t"] = vals["t"] or 0.0
        vals["direction"] = int(vals["direction"] or 1)
        return ControlCommand(**vals)
    if type_name == "PlannedTrajectory":
        n = int(arr[0])
        body = arr[5:5 + n * len(TRAJECTORY_FIELDS)].reshape(n, len(TRAJECTORY_FIELDS))
        traj = PlannedTrajectory(**{f: body[:, i].copy() for i, f in enumerate(TRAJECTORY_FIELDS)})
        traj.direction = int(arr[1])
        traj.reference_point = "cog" if arr[2] == 0 else "rear_axle"
        traj.cost, traj.valid = float(arr[3]), bool(arr[4])
        return traj
    if type_name in ("ObjectList", "WorldState"):
        n = int(arr[0])
        rows = arr[1:1 + n * len(OBJECT_FIELDS)].reshape(n, len(OBJECT_FIELDS))
        objs = [ObjectState(id=int(r[0]), type=OBJECT_TYPES[int(r[1])], x=r[2], y=r[3], psi=r[4], v=r[5], a=r[6],
                            length=r[7], width=r[8]) for r in rows]
        return ObjectList(objects=objs) if type_name == "ObjectList" else WorldState(objects=objs)
    if type_name == "Prediction":
        n, i, objs = int(arr[0]), 1, []
        for _ in range(n):
            oid, otype, length, width, k = arr[i:i + 5]
            k = int(k)
            data = arr[i + 5:i + 5 + 5 * k].reshape(k, 5)
            objs.append(PredictedObject(id=int(oid), type=OBJECT_TYPES[int(otype)], length=length, width=width,
                                        t=data[:, 0], x=data[:, 1], y=data[:, 2], psi=data[:, 3], v=data[:, 4]))
            i += 5 + 5 * k
        return Prediction(objects=objs)
    if type_name == "ReferenceLine":
        from ..geometry.reference_line import ReferenceLine
        n = int(arr[0])
        data = arr[1:1 + 6 * n].reshape(n, 6)
        return ReferenceLine(*[data[:, i] for i in range(6)])
    raise TypeError(f"no flat codec for type '{type_name}'")
