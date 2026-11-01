"""Restrictions of the trajectory planner as plugins (kind="constraint", Werling 2011, 3.5.4).

Every constraint evaluates a TrajectoryBatch (B candidates x K samples on the common check
horizon) and reports per candidate whether it is admissible, the time of the first violation
and the reason. Each built-in constraint can be enabled and parametrized individually; new
ones are added with

    @component
    class MyConstraint(Constraint):
        NAME = "my_constraint"
        PARAMS = MyParams                 # dataclass with at least `enabled`
        def violation(self, batch):       # (B, K) array, > 0 means violated
            ...

and listed in ConstraintSettings.custom = [{"spec": "constraint/my_constraint", "params": {...}}].
Limits come exclusively from parameters (or the vehicle configuration for "auto" values <= 0).
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields

import numpy as np

from ..core.conventions import G
from ..core.parameters import param
from ..framework.component import Component
from ..framework.knowledge import ComponentDoc, trace
from ..framework.plugins import component, create_component, get_component


def group(cls, label):
    # nested parameter group (dataclass field with a GUI label)
    return field(default_factory=cls, metadata={"label": label, "unit": ""})


@dataclass
class ConstraintResult:
    name: str
    valid: np.ndarray            # (B,) bool
    t_violation: np.ndarray      # (B,) absolute time of the first violation (inf if valid)
    reason: str = ""


class Constraint(Component):
    KIND, CATEGORY = "constraint", "Planer-Restriktionen"
    LABEL = "Restriktion"

    def __init__(self, params=None, **overrides):
        super().__init__(params, **overrides)
        self.vehicle = None
        self.geometry = None

    def setup(self, vehicle, geometry):
        # called by the planner with the VehicleConfig and the EgoGeometry
        self.vehicle, self.geometry = vehicle, geometry

    @property
    def enabled(self):
        return bool(getattr(self.params, "enabled", True))

    def violation(self, batch):
        raise NotImplementedError

    def check(self, batch):
        viol = np.asarray(self.violation(batch), dtype=float) > 0.0
        bad = np.any(viol, axis=1)
        first = np.argmax(viol, axis=1)
        t_v = np.where(bad, batch.t[first], np.inf)
        return ConstraintResult(self.NAME, ~bad, t_v, self.LABEL or self.NAME)

    def step(self, t, inputs):
        return {}


def _vehicle(obj):
    return getattr(obj.vehicle, "vehicle", None)


# ----------------------------------------------------------------------------- built-in restrictions
@dataclass
class LateralAccelerationParams:
    enabled: bool = param(True, "", "aktiv")
    a_max: float = param(6.0, "m/s²", "Max. Querbeschleunigung |v²κ|", min=0.5, max=15.0)


@component
class MaxLateralAcceleration(Constraint):
    NAME, VERSION, LABEL = "max_lateral_acceleration", "1.0.0", "Max. Querbeschleunigung"
    PARAMS = LateralAccelerationParams
    DOC = ComponentDoc(summary="Begrenzt die Querbeschleunigung v²κ entlang der Trajektorie.",
                       references=["werling2011"], equations=["werling2011:(A.2)", "werling2011:(A.5)"])

    @trace("werling2011", section="3.5.4", concept="kinematic_constraints", note="|v^2 kappa| <= a_y,max")
    def violation(self, batch):
        return np.abs(batch.a_lat) - self.params.a_max


@dataclass
class LongitudinalAccelerationParams:
    enabled: bool = param(True, "", "aktiv")
    a_accel_max: float = param(3.0, "m/s²", "Max. Beschleunigung", min=0.2, max=10.0)
    a_decel_max: float = param(8.0, "m/s²", "Max. Verzögerung", min=0.5, max=12.0)


@component
class MaxLongitudinalAcceleration(Constraint):
    NAME, VERSION, LABEL = "max_longitudinal_acceleration", "1.0.0", "Max. Längsbeschleunigung"
    PARAMS = LongitudinalAccelerationParams
    DOC = ComponentDoc(summary="Getrennte Grenzen für Beschleunigen und Verzögern.", references=["werling2011"],
                       equations=["werling2011:(A.6)"])

    def violation(self, batch):
        return np.maximum(batch.a - self.params.a_accel_max, -batch.a - self.params.a_decel_max)


@dataclass
class JerkParams:
    enabled: bool = param(True, "", "aktiv")
    j_max: float = param(25.0, "m/s³", "Max. Längsruck |ȧ|", min=1.0, max=200.0)


@component
class MaxJerk(Constraint):
    NAME, VERSION, LABEL = "max_jerk", "1.0.0", "Max. Ruck"
    PARAMS = JerkParams
    DOC = ComponentDoc(summary="Begrenzt den Bahnruck ȧ (Differenzenquotient auf dem Prüfraster).",
                       references=["werling2011"])

    def violation(self, batch):
        return np.abs(batch.jerk) - self.params.j_max


@dataclass
class CurvatureParams:
    enabled: bool = param(True, "", "aktiv")
    kappa_max: float = param(-1.0, "1/m", "Max. Krümmung (≤ 0: aus Lenkanschlag und Radstand)", min=-1.0, max=2.0)
    auto_factor: float = param(0.95, "-", "Faktor auf tan(δ_max)/l (automatisch)", min=0.1, max=1.0)


@component
class MaxCurvature(Constraint):
    NAME, VERSION, LABEL = "max_curvature", "1.0.0", "Max. Krümmung"
    PARAMS = CurvatureParams
    DOC = ComponentDoc(summary="Minimaler Kurvenradius (kinematische Restriktion).", references=["werling2011"],
                       equations=["werling2011:(A.5)"])

    def limit(self):
        if self.params.kappa_max > 0:
            return self.params.kappa_max
        v = _vehicle(self)
        if v is None:
            return 0.2
        return self.params.auto_factor * np.tan(v.max_steer_angle) / v.wheelbase

    def violation(self, batch):
        return np.abs(batch.kappa) - self.limit()


@dataclass
class SteeringAngleParams:
    enabled: bool = param(True, "", "aktiv")
    delta_max: float = param(-1.0, "rad", "Max. Radlenkwinkel (≤ 0: aus Fahrzeug)", min=-1.0, max=1.2)


@component
class MaxSteeringAngle(Constraint):
    NAME, VERSION, LABEL = "max_steering_angle", "1.0.0", "Max. Lenkwinkel"
    PARAMS = SteeringAngleParams
    DOC = ComponentDoc(summary="Kinematischer Lenkwinkel δ = atan(lκ) innerhalb des Lenkanschlags.",
                       references=["werling2011"])

    def limit(self):
        if self.params.delta_max > 0:
            return self.params.delta_max
        v = _vehicle(self)
        return v.max_steer_angle if v is not None else 0.6

    def violation(self, batch):
        wb = self.geometry.wheelbase if self.geometry is not None else 2.8
        return np.abs(np.arctan(wb * batch.kappa)) - self.limit()


@dataclass
class SteeringRateParams:
    enabled: bool = param(True, "", "aktiv")
    rate_max: float = param(0.7, "rad/s", "Max. Radlenkwinkelgeschwindigkeit", min=0.05, max=5.0)


@component
class MaxSteeringVelocity(Constraint):
    NAME, VERSION, LABEL = "max_steering_velocity", "1.0.0", "Max. Lenkwinkelgeschwindigkeit"
    PARAMS = SteeringRateParams
    DOC = ComponentDoc(summary="δ̇ = l κ̇ / (1 + (lκ)²) begrenzt (Lenkaktor-Dynamik).", references=["werling2011"])

    def violation(self, batch):
        wb = self.geometry.wheelbase if self.geometry is not None else 2.8
        rate = wb * batch.kappa_dot / (1.0 + (wb * batch.kappa) ** 2)
        return np.abs(rate) - self.params.rate_max


@dataclass
class YawRateParams:
    enabled: bool = param(True, "", "aktiv")
    r_max: float = param(1.2, "rad/s", "Max. Gierrate |vκ|", min=0.05, max=5.0)


@component
class MaxYawRate(Constraint):
    NAME, VERSION, LABEL = "max_yaw_rate", "1.0.0", "Max. Gierrate"
    PARAMS = YawRateParams
    DOC = ComponentDoc(summary="Gierrate ψ̇ = vκ des Referenzpunkts begrenzt.", references=["werling2011"])

    def violation(self, batch):
        return np.abs(batch.v * batch.kappa) - self.params.r_max


@dataclass
class TireForceParams:
    enabled: bool = param(True, "", "aktiv")
    eta: float = param(0.9, "-", "Ausnutzungsgrad η des Kammschen Kreises", min=0.1, max=1.0)
    mu: float = param(-1.0, "-", "Reibwert μ (≤ 0: aus Reifenparametern)", min=-1.0, max=2.0)


@component
class TireForceConstraint(Constraint):
    NAME, VERSION, LABEL = "tire_force", "1.0.0", "Kammscher Kreis"
    PARAMS = TireForceParams
    DOC = ComponentDoc(summary="Kammscher Kreis √(a² + (v²κ)²) ≤ η μ g.", references=["werling2011"],
                       equations=["werling2011:(A.6)"])

    def mu(self):
        if self.params.mu > 0:
            return self.params.mu
        tires = getattr(self.vehicle, "tires", None)
        return tires.mu if tires is not None else 1.0

    @trace("werling2011", section="3.5.4", concept="kinematic_constraints", note="sqrt(a^2 + (v^2 kappa)^2) <= eta mu g")
    def violation(self, batch):
        return np.hypot(batch.a, batch.a_lat) - self.params.eta * self.mu() * G


@dataclass
class EnvelopeParams:
    enabled: bool = param(True, "", "aktiv")
    margin: float = param(0.0, "m", "Zusätzlicher Abstand zum Korridorrand", min=0.0, max=2.0)


@component
class VehicleEnvelope(Constraint):
    NAME, VERSION, LABEL = "vehicle_envelope", "1.0.0", "Fahrzeugumriss im Korridor"
    PARAMS = EnvelopeParams
    DOC = ComponentDoc(summary="Alle vier Fahrzeugecken liegen im Korridor d_min ≤ d ≤ d_max.",
                       purpose="Box-Restriktion der Verhaltensebene für d(t) (Werling 5.3, Fußnote 8).",
                       assumptions=["Ecken in Frenet-Koordinaten mit der Ausrichtung relativ zur Straße genähert "
                                    "(Krümmung der Referenzkurve über die Fahrzeuglänge vernachlässigt)"],
                       references=["werling2011"])

    @trace("werling2011", section="5.3", note="Fußnote 8: Box-Restriktion für d(t)", concept="corridor_constraint")
    def violation(self, batch):
        ctx = batch.ctx
        if ctx.d_min <= -1e8 and ctx.d_max >= 1e8:
            return np.full(batch.x.shape, -1.0)
        front, rear = self.geometry.extent(ctx.reference_point)
        hw = 0.5 * self.geometry.width
        dpsi = batch.heading_error
        sn, cs = np.sin(dpsi), np.cos(dpsi)
        lo, hi = np.full(batch.d.shape, np.inf), np.full(batch.d.shape, -np.inf)
        for xc in (front, -rear):
            for yc in (hw, -hw):
                dc = batch.d + xc * sn + yc * cs
                lo, hi = np.minimum(lo, dc), np.maximum(hi, dc)
        m = self.params.margin
        return np.maximum(ctx.d_min + m - lo, hi - (ctx.d_max - m))


@dataclass
class StabilityParams:
    enabled: bool = param(True, "", "aktiv")
    beta_max: float = param(0.12, "rad", "Max. stationärer Schwimmwinkel (dynamischer Anteil)", min=0.01, max=0.5)
    ay_linear_max: float = param(0.8, "-", "Querbeschleunigung im linearen Bereich, Anteil von μ g", min=0.1, max=1.0)
    v_min: float = param(5.0, "m/s", "Prüfung erst ab Geschwindigkeit", min=0.0, max=30.0)


@component
class VehicleStability(Constraint):
    NAME, VERSION, LABEL = "vehicle_stability", "1.0.0", "Fahrstabilität (lineares ESM)"
    PARAMS = StabilityParams
    DOC = ComponentDoc(
        summary="Stationärer Schwimmwinkel und Querbeschleunigung im linearen Bereich des Einspurmodells.",
        theory="$\\beta_{ss} = \\kappa\\,(l_h - m l_v v^2/(c_h l))$; der Anteil $-m l_v v^2\\kappa/(c_h l)$ "
               "ist der fahrdynamische Schwimmwinkel. Zusätzlich $|v^2\\kappa| \\le f\\,\\mu g$.",
        assumptions=["lineares Einspurmodell, stationäre Kurvenfahrt", "Achs-Schräglaufsteifigkeit = 2 x Reifen"],
        references=["werling2011"])

    def violation(self, batch):
        veh = _vehicle(self)
        tires = getattr(self.vehicle, "tires", None)
        if veh is None or tires is None:
            return np.full(batch.x.shape, -1.0)
        c_r = 2.0 * tires.cornering_stiffness_rear
        beta_dyn = -veh.mass * veh.cg_to_front * batch.v ** 2 * batch.kappa / (c_r * veh.wheelbase)
        ay = np.abs(batch.a_lat) - self.params.ay_linear_max * tires.mu * G
        viol = np.maximum(np.abs(beta_dyn) - self.params.beta_max, ay)
        return np.where(batch.v >= self.params.v_min, viol, -1.0)


@dataclass
class SpeedParams:
    enabled: bool = param(True, "", "aktiv")
    v_max: float = param(60.0, "m/s", "Max. Bahngeschwindigkeit", min=1.0, max=100.0)
    allow_reversal: bool = param(False, "", "Richtungsumkehr innerhalb einer Trajektorie zulassen")


@component
class SpeedRange(Constraint):
    NAME, VERSION, LABEL = "speed_range", "1.0.0", "Geschwindigkeitsbereich"
    PARAMS = SpeedParams
    DOC = ComponentDoc(summary="0 ≤ v ≤ v_max: keine Richtungsumkehr innerhalb einer Trajektorie.",
                       purpose="Die Fahrtrichtung ς wird von der Verhaltensebene festgelegt (Werling 2.1.1, "
                               "Fußnote 3); quintische Anhaltetrajektorien mit Überschwingen werden verworfen.",
                       references=["werling2011"])

    def violation(self, batch):
        lower = -np.inf if self.params.allow_reversal else -0.05
        return np.maximum(batch.v - self.params.v_max, lower - batch.v)


BUILTIN_CONSTRAINTS = ("speed_range", "max_lateral_acceleration", "max_longitudinal_acceleration", "max_jerk",
                       "max_curvature", "max_steering_angle", "max_steering_velocity", "max_yaw_rate", "tire_force",
                       "vehicle_envelope", "vehicle_stability")


@dataclass
class ConstraintSettings:
    speed_range: SpeedParams = group(SpeedParams, "Geschwindigkeitsbereich")
    max_lateral_acceleration: LateralAccelerationParams = group(LateralAccelerationParams, "Max. Querbeschleunigung")
    max_longitudinal_acceleration: LongitudinalAccelerationParams = group(LongitudinalAccelerationParams,
                                                                          "Max. Längsbeschleunigung")
    max_jerk: JerkParams = group(JerkParams, "Max. Ruck")
    max_curvature: CurvatureParams = group(CurvatureParams, "Max. Krümmung")
    max_steering_angle: SteeringAngleParams = group(SteeringAngleParams, "Max. Lenkwinkel")
    max_steering_velocity: SteeringRateParams = group(SteeringRateParams, "Max. Lenkwinkelgeschwindigkeit")
    max_yaw_rate: YawRateParams = group(YawRateParams, "Max. Gierrate")
    tire_force: TireForceParams = group(TireForceParams, "Kammscher Kreis")
    vehicle_envelope: EnvelopeParams = group(EnvelopeParams, "Fahrzeugumriss im Korridor")
    vehicle_stability: StabilityParams = group(StabilityParams, "Fahrstabilität")
    custom: list = param([], "", "Weitere Restriktionen [{spec, params}]")


class ConstraintSet:
    """Instantiated, enabled constraints of one planner."""

    def __init__(self, settings, vehicle, geometry):
        self.constraints = []
        for f in fields(settings):
            if f.name == "custom":
                continue
            cls = get_component("constraint", f.name)
            c = cls(getattr(settings, f.name))
            c.setup(vehicle, geometry)
            if c.enabled:
                self.constraints.append(c)
        for entry in settings.custom or []:
            spec = entry["spec"] if isinstance(entry, dict) else str(entry)
            c = create_component(spec, entry.get("params") if isinstance(entry, dict) else None)
            c.setup(vehicle, geometry)
            if c.enabled:
                self.constraints.append(c)

    @property
    def names(self):
        return [c.NAME for c in self.constraints]

    def check(self, batch):
        # -> valid (B,), t_violation (B,), reason list, per-constraint violation mask dict
        n = len(batch)
        valid = np.ones(n, dtype=bool)
        t_v = np.full(n, np.inf)
        reason = np.array([""] * n, dtype=object)
        per = {}
        for c in self.constraints:
            r = c.check(batch)
            bad = ~r.valid
            per[c.NAME] = bad
            first = bad & (r.t_violation < t_v)
            reason[first] = c.NAME
            t_v = np.minimum(t_v, r.t_violation)
            valid &= r.valid
        return valid, t_v, reason, per


def limits_for_prefilter(settings, factor):
    # longitudinal (a_min, a_max, v_max) and lateral |d_ddot| bounds for the Frenet pre-filter (step 3)
    lon = settings.max_longitudinal_acceleration
    lat = settings.max_lateral_acceleration
    tire = settings.tire_force
    a_cap = tire.eta * (tire.mu if tire.mu > 0 else 1.0) * G
    a_max = min(lon.a_accel_max, a_cap) if lon.enabled else a_cap
    a_dec = min(lon.a_decel_max, a_cap) if lon.enabled else a_cap
    a_lat = min(lat.a_max, a_cap) if lat.enabled else a_cap
    v_max = settings.speed_range.v_max if settings.speed_range.enabled else np.inf
    return (-factor * a_dec, factor * a_max, factor * v_max), factor * a_lat
