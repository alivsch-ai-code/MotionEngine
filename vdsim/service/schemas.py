"""Request and response models of the REST service (pydantic v2, SI units, ISO 8855)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ScalarValue = float | int | bool | str


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ----------------------------------------------------------------------------- health
class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    name: str
    version: str
    uptime_s: float


# ----------------------------------------------------------------------------- vehicle
class VehicleCatalog(BaseModel):
    presets: list[str]
    vehicle_models: list[str]
    tire_models: list[str]
    lateral_controllers: list[str]
    longitudinal_controllers: list[str]


class SpeedAnalysis(BaseModel):
    speed: float = Field(description="m/s")
    yaw_gain: float = Field(description="steady-state yaw rate per road-wheel angle, 1/s")
    ay_gain: float = Field(description="steady-state lateral acceleration per road-wheel angle, m/s^2/rad")
    natural_frequency: float = Field(description="Hz")
    damping: float


class VehicleAnalysis(BaseModel):
    understeer_gradient: float = Field(description="rad/(m/s^2)")
    understeer_gradient_deg_per_g: float
    characteristic_speed: float | None = Field(description="m/s, None if oversteering")
    critical_speed: float | None = Field(description="m/s, None if understeering")
    cornering_stiffness_front: float = Field(description="axle, N/rad")
    cornering_stiffness_rear: float = Field(description="axle, N/rad")
    per_speed: list[SpeedAnalysis]


class ParameterInfo(BaseModel):
    key: str = Field(description="group.field, also the translation key of the label")
    value: float | int | bool | str | list | None
    unit: str = ""
    min: float | None = None
    max: float | None = None


class VehicleResponse(BaseModel):
    name: str
    parameters: dict
    schema_: list[ParameterInfo] = Field(alias="schema", serialization_alias="schema")
    analysis: VehicleAnalysis


# ----------------------------------------------------------------------------- trajectory
class TrajectoryRequest(_Strict):
    maneuver: str = Field("iso_double_lane_change", description="name from GET /trajectory/maneuvers")
    params: dict[str, ScalarValue] = Field(default_factory=dict, description="maneuver parameters")
    vehicle: str = Field("mid_size_sedan", description="vehicle preset (steering ratio, width)")
    max_points: int = Field(2000, ge=2, le=20000)


class TrajectoryResponse(BaseModel):
    name: str
    length: float = Field(description="m")
    open_loop: bool
    n_points: int
    s: list[float]
    x: list[float]
    y: list[float]
    psi: list[float]
    kappa: list[float]
    v: list[float]


class WaypointModel(_Strict):
    x: float = Field(ge=-1e5, le=1e5, description="m")
    y: float = Field(ge=-1e5, le=1e5, description="m")
    v_kmh: float = Field(50.0, ge=0.0, le=400.0)
    radius: float = Field(0.0, ge=0.0, le=5000.0, description="corner radius at this waypoint, m (0 = sharp)")


class WaypointPath(_Strict):
    waypoints: list[WaypointModel] = Field(min_length=2, max_length=200)
    ay_max: float | None = Field(None, ge=0.0, le=15.0,
                                 description="m/s^2: limit the speed profile by lateral acceleration (0 = off)")


class WaypointsRequest(WaypointPath):
    max_points: int = Field(2000, ge=2, le=20000)


class WaypointsFromManeuver(TrajectoryRequest):
    n_points: int = Field(25, ge=2, le=200)


# ----------------------------------------------------------------------------- simulate
DEFAULT_SIGNALS = ["t", "x", "y", "psi", "vx", "vy", "r", "ax", "ay", "beta", "delta_f", "lateral_error"]


class SimulateRequest(_Strict):
    scenario: str | None = Field(None, description="preset from configs/scenarios; the fields below override it")
    vehicle: str | None = Field(None, description="vehicle preset (default mid_size_sedan)")
    vehicle_overrides: dict[str, ScalarValue] | None = Field(None, examples=[{"tires.mu": 0.8}])
    model: str | None = Field(None, description="vehicle model (default double_track)")
    maneuver: str | None = None
    maneuver_params: dict[str, ScalarValue] | None = None
    waypoints: WaypointPath | None = Field(None, description="drive this waypoint path instead of a maneuver")
    lateral_controller: str | None = None
    lateral_params: dict[str, ScalarValue] | None = None
    longitudinal_controller: str | None = None
    longitudinal_params: dict[str, ScalarValue] | None = None
    environment: dict | None = Field(None, description="friction, wind_speed (head wind > 0), road, lead_vehicle")
    duration: float | None = Field(None, ge=0.0, description="s, 0 = automatic; capped by the server limit")
    dt_control: float | None = Field(None, ge=1e-3, le=0.1)
    solver: Literal["euler", "heun", "rk4", "adaptive"] | None = None
    initial_speed: float | None = Field(None, ge=0.0, le=100.0)
    signals: list[str] = Field(default_factory=lambda: list(DEFAULT_SIGNALS))
    max_points: int = Field(1000, ge=2, le=20000, description="signals are decimated to at most this many samples")


class KPIModel(BaseModel):
    key: str = Field(description="language-neutral KPI key (translation key)")
    label: str = Field(description="German label of the library")
    value: float | str | None
    value_code: str | None = Field(None, description="language-neutral code of a textual value")
    unit: str = ""
    group: str = ""
    group_code: str = Field("", description="language-neutral key of the KPI group")
    rating: str = ""


class SimulateResponse(BaseModel):
    run_id: str = Field("", description="id of the stored result, for POST /simulate/report")
    name: str
    model: str
    stop_reason: str
    stop_code: str = Field(description="language-neutral key of the stop reason")
    simulated_time: float = Field(description="s")
    wall_time: float = Field(description="s")
    n_samples: int
    kpis: list[KPIModel]
    signals: dict[str, list]


class ReportRequest(_Strict):
    run_ids: list[str] = Field(min_length=1, max_length=6, description="run_id values of POST /simulate")
    format: Literal["pdf", "summary"] = "pdf"
    title: str = Field("Vehicle dynamics simulation report", max_length=120)


# ----------------------------------------------------------------------------- objects and prediction
class ObjectModel(_Strict):
    id: int = 0
    type: Literal["car", "truck", "cyclist", "pedestrian", "static", "unknown"] = "car"
    x: float = 0.0
    y: float = 0.0
    psi: float = Field(0.0, description="rad")
    v: float = Field(0.0, ge=0.0, description="speed along psi, m/s")
    a: float = Field(0.0, description="m/s^2")
    yaw_rate: float = Field(0.0, description="rad/s")
    length: float = Field(4.5, gt=0.0)
    width: float = Field(1.8, gt=0.0)


class PredictRequest(_Strict):
    predictor: Literal["constant_velocity", "constant_acceleration", "ctrv"] = "constant_velocity"
    t0: float = 0.0
    horizon: float = Field(6.0, gt=0.0, le=20.0)
    dt: float = Field(0.1, ge=0.01, le=1.0)
    objects: list[ObjectModel] = Field(default_factory=list, max_length=500)


class PredictedObjectModel(BaseModel):
    id: int
    type: str
    length: float
    width: float
    t: list[float]
    x: list[float]
    y: list[float]
    psi: list[float]
    v: list[float]


class PredictResponse(BaseModel):
    t0: float
    predictor: str
    objects: list[PredictedObjectModel]


# ----------------------------------------------------------------------------- plan
class RoadSegment(_Strict):
    kind: Literal["straight", "arc"] = "straight"
    length: float = Field(gt=0.0, le=5000.0)
    curvature: float = Field(0.0, ge=-0.5, le=0.5, description="1/m, left > 0")


class EgoModel(_Strict):
    x: float = 0.0
    y: float = 0.0
    psi: float = 0.0
    vx: float = Field(15.0, ge=0.0, le=70.0)
    ax: float = 0.0


class PlanRequest(_Strict):
    config: str = Field("default", description="planner configuration from configs/planning")
    vehicle: str = Field("mid_size_sedan", description="vehicle preset (geometry, limits, tires)")
    road: list[RoadSegment] = Field(default_factory=lambda: [RoadSegment(kind="straight", length=500.0,
                                                                         curvature=0.0)],
                                    min_length=1, max_length=50)
    ego: EgoModel = Field(default_factory=lambda: EgoModel(x=0.0, y=0.0, psi=0.0, vx=15.0, ax=0.0), description="start state of the CoG")
    target_speed: float = Field(15.0, ge=0.0, le=70.0)
    target_offset: float = Field(0.0, ge=-20.0, le=20.0, description="lateral offset of the target lane, m (left > 0)")
    d_min: float = Field(-5.25, description="right corridor bound relative to the target lane, m")
    d_max: float = Field(5.25, description="left corridor bound relative to the target lane, m")
    stop_at: float | None = Field(None, gt=0.0, description="arc length of a stop line on the target lane, m")
    obstacles: list[ObjectModel] = Field(default_factory=list, max_length=100,
                                         description="predicted with constant velocity/acceleration")
    cycles: int = Field(1, ge=1, le=300, description=">1: closed loop with ideal tracking")
    max_points: int = Field(200, ge=2, le=5000)
    model: str | None = Field(None, description="id of a trained trajectory planner model: the network proposes, "
                                                "the Werling planner verifies")


class PlannedTrajectoryModel(BaseModel):
    valid: bool
    cost: float | None
    longitudinal_mode: str
    reference_point: str
    t: list[float]
    x: list[float]
    y: list[float]
    theta: list[float]
    kappa: list[float]
    v: list[float]
    a: list[float]


class PlanCycle(BaseModel):
    t: float
    x: float
    y: float
    v: float
    valid: bool
    n_candidates: int
    compute_time: float = Field(description="s")


class RoadGeometry(BaseModel):
    x: list[float]
    y: list[float]
    left_x: list[float]
    left_y: list[float]
    right_x: list[float]
    right_y: list[float]
    target_x: list[float]
    target_y: list[float]


class PlanResponse(BaseModel):
    source: str = Field("teacher", description="first cycle: network (learned proposal accepted), teacher "
                                               "(complete Werling search), out_of_scope or infeasible")
    network_share: float | None = Field(None, description="share of the cycles solved by the network path")
    road: RoadGeometry | None = None
    trajectory: PlannedTrajectoryModel
    n_candidates: int
    fallback: bool
    compute_time: float = Field(description="s, first cycle")
    cycles: list[PlanCycle]


class ExplainResponse(BaseModel):
    road: RoadGeometry
    obstacles: list[ObjectModel]
    steps: list[dict]
    series: dict[str, list]
    candidates: list[dict]
    weights: dict
    compute_time: float = Field(description="s, planner cycle")


# ----------------------------------------------------------------------------- parking
class ParkRequest(_Strict):
    vehicle: str = Field("mid_size_sedan", description="vehicle preset")
    kind: Literal["parallel", "perpendicular", "angled"] = "parallel"
    entry: Literal["reverse", "forward"] = "reverse"
    side: Literal["right", "left"] = "right"
    steering: Literal["front", "rear", "counter", "in_phase"] = Field(
        "front", description="which wheels steer: front, rear only, four-wheel counter-phase or in-phase")
    ratio: float | None = Field(None, ge=-1.0, le=0.99, description="tan(delta_r)/tan(delta_f) for four-wheel steering")
    max_rear_angle: float | None = Field(None, gt=0.0, le=1.0, description="rad, rear road-wheel angle limit")
    layout: Literal["fwd", "rwd", "awd"] = Field("fwd", description="driven axle(s) in the closed loop")
    mu: float = Field(0.9, ge=0.05, le=1.5, description="tire-road friction")
    slope: float = Field(0.0, ge=-0.3, le=0.3, description="road gradient along the street, rise per meter")
    gap_length: float | None = Field(None, ge=3.0, le=15.0, description="parallel: length of the gap, m")
    spot_width: float | None = Field(None, ge=2.0, le=4.0, description="perpendicular/angled: spot width, m")
    aisle_width: float | None = Field(None, ge=3.0, le=12.0, description="perpendicular/angled: aisle width, m")
    angle_deg: float | None = Field(None, ge=30.0, le=75.0, description="angled: spot angle, deg")
    time_limit: float = Field(10.0, gt=0.0, le=30.0, description="s, planning time limit")
    simulate: bool = Field(True, description="drive the plan in closed loop")
    max_points: int = Field(1500, ge=50, le=20000)


# ----------------------------------------------------------------------------- chat
class ChatRequest(_Strict):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(None, max_length=64, description="continue a conversation; omit to start one")


# ----------------------------------------------------------------------------- neural models
class SituationSettings(_Strict):
    curve_share: float = Field(0.55, ge=0.0, le=1.0, description="share of situations on a curve or S-curve")
    max_objects: int = Field(3, ge=0, le=3)
    speed_min: float = Field(6.0, ge=4.0, le=40.0, description="m/s")
    speed_max: float = Field(33.0, ge=5.0, le=45.0, description="m/s")
    lane_change_share: float = Field(0.25, ge=0.0, le=0.75, description="share of situations starting on the neighbor lane")


class TrainRequest(_Strict):
    kind: Literal["vehicle_dynamics", "trajectory_planner"] = Field(
        "vehicle_dynamics", description="vehicle_dynamics: surrogate of a physics model; trajectory_planner: "
                                        "imitation of the Werling planner (proposal + verified local search)")
    planner_config: str = Field("default", description="trajectory_planner: planner configuration of the teacher")
    approach: Literal["regression", "classification", "dagger"] = Field(
        "regression", description="trajectory_planner: regression of the teacher's choice, classes for end offset and "
                                  "end speed, or data aggregation (the learner drives, the teacher labels)")
    situations: SituationSettings | None = Field(None, description="trajectory_planner: training situations")
    vehicle: str = "mid_size_sedan"
    teacher: Literal["bicycle_nonlinear", "bicycle_linear"] = "bicycle_nonlinear"
    n_samples: int = Field(20000, ge=500, le=200000)
    hidden: list[int] = Field(default_factory=lambda: [64, 64], min_length=1, max_length=4)
    epochs: int = Field(150, ge=1, le=1000)
    learning_rate: float = Field(2e-3, gt=0.0, le=0.1)
    seed: int = 0
    name: str = Field("", max_length=80)


class TrainJob(BaseModel):
    id: str
    state: Literal["queued", "running", "done", "failed", "cancelled"]
    phase: str = ""
    progress: float = 0.0
    history: list[dict] = Field(default_factory=list)
    model_id: str | None = None
    error: str | None = None
    created: float = Field(0.0, description="Unix time the job was started")
    name: str = ""


class ConnectRequest(_Strict):
    name: str = Field(..., min_length=1, max_length=80)
    backend: Literal["onnx", "http"]
    onnx_base64: str | None = Field(None, description="ONNX graph, base64 (max. 20 MB)")
    url: str | None = Field(None, description="HTTP endpoint: POST {inputs} -> {outputs}")
    vehicle: str = "mid_size_sedan"
    kind: Literal["vehicle_dynamics", "trajectory_planner"] = Field(
        "vehicle_dynamics", description="vehicle_dynamics: 5 inputs -> 3 outputs; trajectory_planner: 31 inputs -> "
                                        "4 outputs (end offset, lateral end time, end speed offset, longitudinal end time)")
    planner_config: str = Field("default", description="trajectory_planner: configuration of the verifying planner")


class DriveRequest(_Strict):
    situation: PlanRequest | None = Field(None, description="road, ego, target speed, corridor and obstacles; "
                                                            "omit to draw a random situation from `seed`")
    seed: int = Field(0, ge=0, le=2**31 - 1)
    cycles: int = Field(60, ge=1, le=200, description="planning cycles of 0.1 s")


class EvaluateRequest(_Strict):
    maneuver: str = "iso_double_lane_change"
    maneuver_params: dict[str, ScalarValue] = Field(default_factory=dict)
    duration: float | None = Field(None, gt=0.0, le=60.0)
