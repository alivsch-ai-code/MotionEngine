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


class VehicleResponse(BaseModel):
    name: str
    parameters: dict
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


# ----------------------------------------------------------------------------- simulate
DEFAULT_SIGNALS = ["t", "x", "y", "psi", "vx", "vy", "r", "ax", "ay", "beta", "delta_f", "lateral_error"]


class SimulateRequest(_Strict):
    scenario: str | None = Field(None, description="preset from configs/scenarios; the fields below override it")
    vehicle: str | None = Field(None, description="vehicle preset (default mid_size_sedan)")
    vehicle_overrides: dict[str, ScalarValue] | None = Field(None, examples=[{"tires.mu": 0.8}])
    model: str | None = Field(None, description="vehicle model (default double_track)")
    maneuver: str | None = None
    maneuver_params: dict[str, ScalarValue] | None = None
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
    key: str
    label: str
    value: float | str | None
    unit: str = ""
    group: str = ""
    rating: str = ""


class SimulateResponse(BaseModel):
    name: str
    model: str
    stop_reason: str
    simulated_time: float = Field(description="s")
    wall_time: float = Field(description="s")
    n_samples: int
    kpis: list[KPIModel]
    signals: dict[str, list]


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


class PlanResponse(BaseModel):
    trajectory: PlannedTrajectoryModel
    n_candidates: int
    fallback: bool
    compute_time: float = Field(description="s, first cycle")
    cycles: list[PlanCycle]
