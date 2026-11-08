"""Parameter sets of the vehicle, tires, chassis, powertrain, brakes and control systems.

Every field carries a German label and a unit as metadata; the GUI builds its
parameter editors from it. All values are SI (see conventions.py).
"""

import json
import os
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path

from .conventions import G
from .logging_setup import get_logger

log = get_logger("parameters")


def param(default, unit="", label="", **limits):
    # Dataclass field with GUI metadata (label, unit, optional min/max/step)
    meta = {"unit": unit, "label": label, **limits}
    if isinstance(default, list):
        return field(default_factory=lambda: list(default), metadata=meta)
    return field(default=default, metadata=meta)


@dataclass
class VehicleParameters:
    name: str = param("Mittelklasse-Limousine", "", "Bezeichnung")
    mass: float = param(1600.0, "kg", "Masse", min=500, max=5000)
    wheelbase: float = param(2.80, "m", "Radstand", min=1.5, max=4.5)
    cg_to_front: float = param(1.25, "m", "Schwerpunkt - Vorderachse", min=0.3, max=3.5)
    track_front: float = param(1.60, "m", "Spurweite vorne", min=1.0, max=2.2)
    track_rear: float = param(1.60, "m", "Spurweite hinten", min=1.0, max=2.2)
    cg_height: float = param(0.55, "m", "Schwerpunkthöhe", min=0.2, max=1.5)
    inertia_x: float = param(600.0, "kg m²", "Wankträgheit (aufgebaut)", min=50)
    inertia_y: float = param(2800.0, "kg m²", "Nickträgheit", min=100)
    inertia_z: float = param(2700.0, "kg m²", "Gierträgheit", min=100)
    unsprung_mass_front: float = param(45.0, "kg", "Ungefederte Masse vorne (je Rad)", min=5)
    unsprung_mass_rear: float = param(40.0, "kg", "Ungefederte Masse hinten (je Rad)", min=5)
    drag_coefficient: float = param(0.28, "-", "Luftwiderstandsbeiwert cw", min=0.1, max=1.5)
    frontal_area: float = param(2.2, "m²", "Stirnfläche", min=0.5, max=10)
    rolling_resistance: float = param(0.012, "-", "Rollwiderstandsbeiwert", min=0, max=0.05)
    wheel_radius: float = param(0.32, "m", "Dynamischer Radradius", min=0.15, max=0.6)
    wheel_inertia: float = param(1.2, "kg m²", "Radträgheit (je Rad)", min=0.1)
    steering_ratio: float = param(15.0, "-", "Lenkübersetzung", min=5, max=30)
    max_steer_angle: float = param(0.60, "rad", "Max. Radlenkwinkel", min=0.1, max=1.2)
    length: float = param(4.80, "m", "Fahrzeuglänge", min=2, max=12)
    width: float = param(1.85, "m", "Fahrzeugbreite", min=1, max=2.6)

    @property
    def cg_to_rear(self):
        return self.wheelbase - self.cg_to_front

    @property
    def static_axle_loads(self):
        # (front, rear) axle load in N
        weight = self.mass * G
        return weight * self.cg_to_rear / self.wheelbase, weight * self.cg_to_front / self.wheelbase


@dataclass
class TireParameters:
    model: str = param("pacejka", "", "Reifenmodell (linear / pacejka / brush)")
    mu: float = param(1.0, "-", "Reibwert (Referenz)", min=0.05, max=2.0)
    nominal_load: float = param(4000.0, "N", "Nennlast", min=500)
    cornering_stiffness_front: float = param(80000.0, "N/rad", "Schräglaufsteifigkeit vorne (je Reifen, Nennlast)", min=1000)
    cornering_stiffness_rear: float = param(110000.0, "N/rad", "Schräglaufsteifigkeit hinten (je Reifen, Nennlast)", min=1000)
    longitudinal_stiffness: float = param(100000.0, "N", "Längssteifigkeit (je Reifen, Nennlast)", min=1000)
    camber_stiffness: float = param(5000.0, "N/rad", "Sturzsteifigkeit (je Reifen)", min=0)
    load_sensitivity_stiffness: float = param(2.0, "-", "Lastabhängigkeit Schräglaufsteifigkeit (Pacejka p_Ky2)", min=0.5, max=5)
    load_sensitivity_mu: float = param(-0.10, "-", "Lastabhängigkeit Reibwert", min=-0.5, max=0)
    shape_lateral: float = param(1.30, "-", "Formfaktor C lateral", min=1.0, max=2.0)
    curvature_lateral: float = param(-0.5, "-", "Krümmungsfaktor E lateral", min=-5, max=1)
    shape_longitudinal: float = param(1.65, "-", "Formfaktor C longitudinal", min=1.0, max=2.0)
    curvature_longitudinal: float = param(0.0, "-", "Krümmungsfaktor E longitudinal", min=-5, max=1)
    combined_lateral_reduction: float = param(10.0, "-", "Kombinierter Schlupf: Abbau Fy durch kappa (B_yk)", min=0)
    combined_longitudinal_reduction: float = param(12.0, "-", "Kombinierter Schlupf: Abbau Fx durch alpha (B_xa)", min=0)
    pneumatic_trail: float = param(0.04, "m", "Reifennachlauf", min=0, max=0.2)
    vertical_stiffness: float = param(250000.0, "N/m", "Vertikalsteifigkeit Reifen", min=1e4)


@dataclass
class ChassisParameters:
    spring_rate_front: float = param(32000.0, "N/m", "Federrate vorne (am Rad)", min=1000)
    spring_rate_rear: float = param(35000.0, "N/m", "Federrate hinten (am Rad)", min=1000)
    damper_velocity: list = param([-1.0, -0.3, -0.1, 0.0, 0.1, 0.3, 1.0], "m/s", "Dämpfer-Stützstellen Geschwindigkeit (+ = Druck)")
    damper_force_front: list = param([-1900.0, -850.0, -320.0, 0.0, 180.0, 450.0, 1000.0], "N", "Dämpferkennlinie vorne")
    damper_force_rear: list = param([-1800.0, -800.0, -300.0, 0.0, 170.0, 420.0, 950.0], "N", "Dämpferkennlinie hinten")
    anti_roll_bar_front: float = param(30000.0, "N m/rad", "Stabilisator-Wanksteifigkeit vorne", min=0)
    anti_roll_bar_rear: float = param(12000.0, "N m/rad", "Stabilisator-Wanksteifigkeit hinten", min=0)
    roll_center_height_front: float = param(0.06, "m", "Rollzentrumshöhe vorne", min=-0.2, max=0.5)
    roll_center_height_rear: float = param(0.12, "m", "Rollzentrumshöhe hinten", min=-0.2, max=0.5)
    camber_gain_front: float = param(-0.35, "rad/m", "Sturzänderung vorne pro Federweg", min=-2, max=2)
    camber_gain_rear: float = param(-0.30, "rad/m", "Sturzänderung hinten pro Federweg", min=-2, max=2)
    bump_steer_front: float = param(0.0, "rad/m", "Vorspuränderung vorne pro Federweg", min=-1, max=1)
    bump_steer_rear: float = param(0.0, "rad/m", "Vorspuränderung hinten pro Federweg", min=-1, max=1)
    roll_steer_front: float = param(-0.05, "rad/rad", "Rolllenken vorne", min=-0.5, max=0.5)
    roll_steer_rear: float = param(0.02, "rad/rad", "Rolllenken hinten", min=-0.5, max=0.5)
    anti_dive: float = param(0.20, "-", "Bremsnickausgleich vorne", min=0, max=1)
    anti_squat: float = param(0.30, "-", "Anfahrnickausgleich hinten", min=0, max=1)

    def roll_stiffness(self, track_front, track_rear):
        # (front, rear) roll stiffness in N m/rad: springs (k t^2 / 2) plus anti-roll bars
        front = self.spring_rate_front * track_front**2 / 2 + self.anti_roll_bar_front
        rear = self.spring_rate_rear * track_rear**2 / 2 + self.anti_roll_bar_rear
        return front, rear

    def roll_damping(self, track_front, track_rear, velocity=0.1):
        # Linearized (front, rear) roll damping in N m s/rad around `velocity`
        import numpy as np
        slope_f = np.interp(velocity, self.damper_velocity, self.damper_force_front) / velocity
        slope_r = np.interp(velocity, self.damper_velocity, self.damper_force_rear) / velocity
        return slope_f * track_front**2 / 2, slope_r * track_rear**2 / 2


@dataclass
class PowertrainParameters:
    type: str = param("ev", "", "Antriebsart (ev / ice)")
    layout: str = param("awd", "", "Antriebslayout (fwd / rwd / awd)")
    front_torque_split: float = param(0.40, "-", "Momentenanteil Vorderachse (AWD)", min=0, max=1)
    driveline_efficiency: float = param(0.92, "-", "Wirkungsgrad Triebstrang", min=0.5, max=1)
    # combustion engine
    engine_speed_rpm: list = param([800.0, 1500.0, 2500.0, 3500.0, 4500.0, 5500.0, 6500.0], "1/min", "Motordrehzahl-Stützstellen")
    engine_torque_nm: list = param([180.0, 300.0, 380.0, 400.0, 390.0, 360.0, 300.0], "N m", "Volllast-Drehmomentkennlinie")
    gear_ratios: list = param([3.6, 2.3, 1.6, 1.2, 1.0, 0.82, 0.68], "-", "Getriebeübersetzungen")
    final_drive: float = param(3.2, "-", "Achsübersetzung", min=1)
    upshift_rpm: float = param(6000.0, "1/min", "Hochschaltdrehzahl")
    downshift_rpm: float = param(2000.0, "1/min", "Rückschaltdrehzahl")
    # electric drive
    motor_max_torque: float = param(450.0, "N m", "E-Motor max. Moment", min=0)
    motor_max_power: float = param(220000.0, "W", "E-Motor max. Leistung", min=0)
    motor_gear_ratio: float = param(9.0, "-", "E-Motor Übersetzung", min=1)
    motor_max_rpm: float = param(16000.0, "1/min", "E-Motor max. Drehzahl", min=1000)
    motor_efficiency: float = param(0.90, "-", "E-Motor Wirkungsgrad", min=0.5, max=1)
    regen_max_power: float = param(120000.0, "W", "Max. Rekuperationsleistung", min=0)
    regen_max_torque: float = param(300.0, "N m", "Max. Rekuperationsmoment (Motor)", min=0)
    battery_capacity_kwh: float = param(80.0, "kWh", "Batteriekapazität", min=1)
    auxiliary_power: float = param(500.0, "W", "Nebenverbraucher", min=0)
    # torque vectoring
    torque_vectoring_max_torque: float = param(800.0, "N m", "Torque Vectoring max. Differenzmoment (Rad)", min=0)


@dataclass
class BrakeParameters:
    max_torque_front: float = param(2500.0, "N m", "Max. Bremsmoment vorne (je Rad)", min=0)
    max_torque_rear: float = param(1500.0, "N m", "Max. Bremsmoment hinten (je Rad)", min=0)
    brake_balance: float = param(0.65, "-", "Bremskraftverteilung (Anteil vorne)", min=0, max=1)
    ebd_enabled: bool = param(True, "", "Elektronische Bremskraftverteilung (EBV)")


@dataclass
class ControlSystemsParameters:
    abs_enabled: bool = param(True, "", "ABS aktiv")
    abs_target_slip: float = param(0.12, "-", "ABS Zielschlupf", min=0.02, max=0.4)
    tcs_enabled: bool = param(True, "", "ASR/TCS aktiv")
    tcs_target_slip: float = param(0.10, "-", "TCS Zielschlupf", min=0.02, max=0.4)
    esp_enabled: bool = param(False, "", "ESP aktiv")
    esp_gain: float = param(20000.0, "N m s/rad", "ESP Verstärkung Giermoment", min=0)
    esp_deadband: float = param(0.03, "rad/s", "ESP Totband Gierrate", min=0)
    rear_steering_enabled: bool = param(False, "", "Hinterachslenkung aktiv")
    rear_steering_ratio_low: float = param(-0.20, "-", "HAL Verhältnis niedrige Geschw. (gegensinnig < 0)", min=-1, max=1)
    rear_steering_ratio_high: float = param(0.10, "-", "HAL Verhältnis hohe Geschw. (gleichsinnig > 0)", min=-1, max=1)
    rear_steering_speed_low: float = param(8.0, "m/s", "HAL Übergang Beginn", min=0)
    rear_steering_speed_high: float = param(22.0, "m/s", "HAL Übergang Ende", min=0)
    torque_vectoring_enabled: bool = param(False, "", "Torque Vectoring aktiv")
    torque_vectoring_gain: float = param(30000.0, "N m s/rad", "Torque Vectoring Verstärkung", min=0)
    torque_vectoring_target: float = param(0.0, "-", "TV Ziel-Eigenlenkverhalten (0 = neutral, 1 = passiv)", min=-0.5, max=1)
    active_damping_enabled: bool = param(False, "", "Aktive Dämpfung (Skyhook) aktiv")
    skyhook_gain: float = param(2500.0, "N s/m", "Skyhook-Dämpfung", min=0)
    active_roll_enabled: bool = param(False, "", "Aktive Wankstabilisierung aktiv")
    active_roll_gain: float = param(0.8, "-", "Wankkompensationsgrad", min=0, max=1.2)


@dataclass
class VehicleConfig:
    vehicle: VehicleParameters = field(default_factory=VehicleParameters)
    tires: TireParameters = field(default_factory=TireParameters)
    chassis: ChassisParameters = field(default_factory=ChassisParameters)
    powertrain: PowertrainParameters = field(default_factory=PowertrainParameters)
    brakes: BrakeParameters = field(default_factory=BrakeParameters)
    systems: ControlSystemsParameters = field(default_factory=ControlSystemsParameters)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return from_dict(cls, data)

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def copy(self):
        return VehicleConfig.from_dict(self.to_dict())


def from_dict(cls, data):
    # Build a (nested) dataclass from a dict; unknown keys are reported, missing keys keep defaults
    kwargs = {}
    known = {f.name: f for f in fields(cls)}
    for key, value in data.items():
        if key not in known:
            log.warning("ignoring unknown parameter '%s' for %s", key, cls.__name__)
            continue
        field_type = known[key].type
        if isinstance(field_type, type) and is_dataclass(field_type) and isinstance(value, dict):
            value = from_dict(field_type, value)
        kwargs[key] = value
    return cls(**kwargs)


def field_info(obj):
    # (name, value, metadata) of all fields of a parameter dataclass, for GUIs and reports
    return [(f.name, getattr(obj, f.name), dict(f.metadata)) for f in fields(obj)]


def load_vehicle_preset(name_or_path, preset_dir=None):
    # Load a vehicle preset by file path or by name from configs/vehicles
    path = Path(name_or_path)
    if not path.suffix:
        preset_dir = Path(preset_dir) if preset_dir else default_config_dir() / "vehicles"
        path = preset_dir / f"{name_or_path}.json"
    return VehicleConfig.load(path)


def default_config_dir():
    # configs/ of the source tree; MOTIONENGINE_CONFIG_DIR overrides it (wheel installs, containers)
    override = os.environ.get("MOTIONENGINE_CONFIG_DIR")
    return Path(override) if override else Path(__file__).resolve().parents[2] / "configs"
