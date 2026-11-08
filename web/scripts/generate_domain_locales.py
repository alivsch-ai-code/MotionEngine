"""Generate the domain translations of the web app (vehicle parameters, KPIs, maneuvers).

German texts come from the library labels (vdsim parameter metadata, KPI and maneuver definitions),
so they cannot drift from the code. English texts are maintained in this file. The script fails
if the library has a key without an English text.

    python web/scripts/generate_domain_locales.py      # writes web/src/locales/{en,de}/domain.json
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from vdsim.core.parameters import VehicleConfig  # noqa: E402
from vdsim.trajectory import MANEUVER_INFO  # noqa: E402

PARAMS_EN = {
    "vehicle.name": "Name",
    "vehicle.mass": "Mass",
    "vehicle.wheelbase": "Wheelbase",
    "vehicle.cg_to_front": "CoG to front axle",
    "vehicle.track_front": "Track width front",
    "vehicle.track_rear": "Track width rear",
    "vehicle.cg_height": "CoG height",
    "vehicle.inertia_x": "Roll inertia (sprung)",
    "vehicle.inertia_y": "Pitch inertia",
    "vehicle.inertia_z": "Yaw inertia",
    "vehicle.unsprung_mass_front": "Unsprung mass front (per wheel)",
    "vehicle.unsprung_mass_rear": "Unsprung mass rear (per wheel)",
    "vehicle.drag_coefficient": "Drag coefficient c_w",
    "vehicle.frontal_area": "Frontal area",
    "vehicle.rolling_resistance": "Rolling resistance coefficient",
    "vehicle.wheel_radius": "Dynamic wheel radius",
    "vehicle.wheel_inertia": "Wheel inertia (per wheel)",
    "vehicle.steering_ratio": "Steering ratio",
    "vehicle.max_steer_angle": "Max. road-wheel angle",
    "vehicle.length": "Vehicle length",
    "vehicle.width": "Vehicle width",
    "tires.model": "Tire model (linear / pacejka / brush)",
    "tires.mu": "Friction coefficient (reference)",
    "tires.nominal_load": "Nominal load",
    "tires.cornering_stiffness_front": "Cornering stiffness front (per tire, nominal load)",
    "tires.cornering_stiffness_rear": "Cornering stiffness rear (per tire, nominal load)",
    "tires.longitudinal_stiffness": "Longitudinal stiffness (per tire, nominal load)",
    "tires.camber_stiffness": "Camber stiffness (per tire)",
    "tires.load_sensitivity_stiffness": "Load sensitivity of cornering stiffness (Pacejka p_Ky2)",
    "tires.load_sensitivity_mu": "Load sensitivity of friction",
    "tires.shape_lateral": "Shape factor C lateral",
    "tires.curvature_lateral": "Curvature factor E lateral",
    "tires.shape_longitudinal": "Shape factor C longitudinal",
    "tires.curvature_longitudinal": "Curvature factor E longitudinal",
    "tires.combined_lateral_reduction": "Combined slip: reduction of Fy by kappa (B_yk)",
    "tires.combined_longitudinal_reduction": "Combined slip: reduction of Fx by alpha (B_xa)",
    "tires.pneumatic_trail": "Pneumatic trail",
    "tires.vertical_stiffness": "Tire vertical stiffness",
    "chassis.spring_rate_front": "Spring rate front (at wheel)",
    "chassis.spring_rate_rear": "Spring rate rear (at wheel)",
    "chassis.damper_velocity": "Damper curve velocities (+ = compression)",
    "chassis.damper_force_front": "Damper curve front",
    "chassis.damper_force_rear": "Damper curve rear",
    "chassis.anti_roll_bar_front": "Anti-roll bar stiffness front",
    "chassis.anti_roll_bar_rear": "Anti-roll bar stiffness rear",
    "chassis.roll_center_height_front": "Roll center height front",
    "chassis.roll_center_height_rear": "Roll center height rear",
    "chassis.camber_gain_front": "Camber gain front per travel",
    "chassis.camber_gain_rear": "Camber gain rear per travel",
    "chassis.bump_steer_front": "Bump steer front per travel",
    "chassis.bump_steer_rear": "Bump steer rear per travel",
    "chassis.roll_steer_front": "Roll steer front",
    "chassis.roll_steer_rear": "Roll steer rear",
    "chassis.anti_dive": "Anti-dive front",
    "chassis.anti_squat": "Anti-squat rear",
    "powertrain.type": "Powertrain type (ev / ice)",
    "powertrain.layout": "Drive layout (fwd / rwd / awd)",
    "powertrain.front_torque_split": "Front torque share (AWD)",
    "powertrain.driveline_efficiency": "Driveline efficiency",
    "powertrain.engine_speed_rpm": "Engine speed breakpoints",
    "powertrain.engine_torque_nm": "Full-load torque curve",
    "powertrain.gear_ratios": "Gear ratios",
    "powertrain.final_drive": "Final drive ratio",
    "powertrain.upshift_rpm": "Upshift speed",
    "powertrain.downshift_rpm": "Downshift speed",
    "powertrain.motor_max_torque": "E-motor max. torque",
    "powertrain.motor_max_power": "E-motor max. power",
    "powertrain.motor_gear_ratio": "E-motor gear ratio",
    "powertrain.motor_max_rpm": "E-motor max. speed",
    "powertrain.motor_efficiency": "E-motor efficiency",
    "powertrain.regen_max_power": "Max. regenerative power",
    "powertrain.regen_max_torque": "Max. regenerative torque (motor)",
    "powertrain.battery_capacity_kwh": "Battery capacity",
    "powertrain.auxiliary_power": "Auxiliary load",
    "powertrain.torque_vectoring_max_torque": "Torque vectoring max. differential torque (wheel)",
    "brakes.max_torque_front": "Max. brake torque front (per wheel)",
    "brakes.max_torque_rear": "Max. brake torque rear (per wheel)",
    "brakes.brake_balance": "Brake balance (front share)",
    "brakes.ebd_enabled": "Electronic brake-force distribution (EBD)",
    "systems.abs_enabled": "ABS enabled",
    "systems.abs_target_slip": "ABS target slip",
    "systems.tcs_enabled": "TCS enabled",
    "systems.tcs_target_slip": "TCS target slip",
    "systems.esp_enabled": "ESC enabled",
    "systems.esp_gain": "ESC yaw moment gain",
    "systems.esp_deadband": "ESC yaw rate deadband",
    "systems.rear_steering_enabled": "Rear-wheel steering enabled",
    "systems.rear_steering_ratio_low": "RWS ratio at low speed (counter-phase < 0)",
    "systems.rear_steering_ratio_high": "RWS ratio at high speed (in-phase > 0)",
    "systems.rear_steering_speed_low": "RWS transition start",
    "systems.rear_steering_speed_high": "RWS transition end",
    "systems.torque_vectoring_enabled": "Torque vectoring enabled",
    "systems.torque_vectoring_gain": "Torque vectoring gain",
    "systems.torque_vectoring_target": "TV target self-steer (0 = neutral, 1 = passive)",
    "systems.active_damping_enabled": "Active damping (skyhook) enabled",
    "systems.skyhook_gain": "Skyhook damping",
    "systems.active_roll_enabled": "Active roll stabilization enabled",
    "systems.active_roll_gain": "Roll compensation ratio",
}

GROUPS = {
    "vehicle": ("Vehicle", "Fahrzeug"),
    "tires": ("Tires", "Reifen"),
    "chassis": ("Chassis", "Fahrwerk"),
    "powertrain": ("Powertrain", "Antrieb"),
    "brakes": ("Brakes", "Bremsen"),
    "systems": ("Control systems", "Regelsysteme"),
}

KPIS_EN = {
    "max_ay": "Max. lateral acceleration",
    "max_ax": "Max. longitudinal acceleration",
    "min_ax": "Max. deceleration",
    "max_yaw_rate": "Max. yaw rate",
    "max_beta": "Max. side-slip angle",
    "max_roll": "Max. roll angle",
    "max_steer": "Max. road-wheel angle",
    "max_lateral_error": "Max. path deviation",
    "rms_lateral_error": "RMS path deviation",
    "max_friction_utilization": "Max. friction utilization",
    "stability_reserve": "Stability reserve (1 - utilization)",
    "mean_speed": "Mean speed",
    "distance": "Distance",
    "duration": "Simulated time",
    "iso2631_aw": "Weighted vertical accel. a_w (ISO 2631)",
    "iso2631_rating": "Comfort rating (ISO 2631)",
    "max_pitch": "Max. pitch angle",
    "rms_ay": "RMS lateral acceleration",
    "rms_lateral_jerk": "RMS lateral jerk",
    "max_lateral_jerk": "Max. lateral jerk",
    "energy_drive": "Energy demand (drive)",
    "energy_regen": "Recuperated energy",
    "consumption": "Consumption",
    "cone_hits": "Lane gate violations",
    "test_passed": "Test passed",
    "entry_speed": "Entry speed",
    "understeer_gradient": "Understeer gradient",
    "understeer_gradient_g": "Understeer gradient",
    "max_ay_steady": "Max. steady-state lateral acceleration",
    "yaw_gain": "Steady-state yaw gain",
    "ay_gain": "Steady-state lateral acceleration gain",
    "response_time": "Yaw rate response time (90 %)",
    "peak_response_time": "Time to yaw rate peak",
    "yaw_overshoot": "Yaw rate overshoot",
    "yaw_ratio_1s": "Yaw rate 1.0 s after steering end",
    "yaw_ratio_175s": "Yaw rate 1.75 s after steering end",
    "lateral_displacement": "Lateral displacement 1.07 s after steering start",
    "stopping_distance": "Stopping distance",
    "brake_speed": "Initial braking speed",
    "mfdd": "Mean fully developed deceleration (MFDD)",
    "max_yaw_deviation": "Max. yaw angle deviation",
    "lap_time": "Lap time",
    "yaw_resonance": "Frequency of max. yaw gain",
    "yaw_gain_peak_ratio": "Yaw gain peak ratio",
    "yaw_gain_1hz_ratio": "Yaw gain 1 Hz / steady state",
    "min_gap": "Min. gap",
    "min_time_gap": "Min. time gap",
    "collision": "Collision",
    "aeb_trigger_ttc": "AEB triggered at TTC",
    "min_distance_to_line": "Min. distance to lane marking",
    "lane_departure": "Lane departure",
    "lka_active_time": "LKA intervention time",
}

MANEUVERS_EN = {
    "straight": ("Straight", "Straight road at constant speed"),
    "lane_change": ("Lane change", "Single lane change with sinusoidal curvature (heading 0 at the end)"),
    "iso_double_lane_change": (
        "ISO double lane change (ISO 3888-1)",
        "Double lane change through cone gates per ISO 3888-1 (offset 3.5 m)",
    ),
    "iso_obstacle_avoidance": (
        "ISO obstacle avoidance (ISO 3888-2)",
        'Avoidance maneuver per ISO 3888-2 ("moose test")',
    ),
    "slalom": ("Slalom", "Slalom around equally spaced cones"),
    "circle": (
        "Steady-state circle (ISO 4138)",
        "Constant-radius circle with slowly rising speed (understeer gradient)",
    ),
    "figure_eight": ("Figure eight", "Figure eight from two circles"),
    "emergency_evasion": ("Emergency evasion", "Fast evasion around an obstacle and return to the lane"),
    "braking": ("Straight-line braking", "Braking from constant speed"),
    "acceleration": ("Acceleration (0-100 km/h)", "Full-load acceleration from standstill"),
    "brake_in_turn": ("Braking in a turn (ISO 7975)", "Steady-state circle, then braking with constant deceleration"),
    "step_steer": ("Step steer (ISO 7401)", "Step steering input at constant speed"),
    "ramp_steer": ("Ramp steer (ISO 4138)", "Slowly increasing steering angle at constant speed"),
    "sine_with_dwell": ("Sine with dwell (FMVSS 126)", "ESC test: 0.7 Hz sine with 500 ms dwell"),
    "frequency_sweep": (
        "Frequency response (sine sweep)",
        "Steering sweep to identify the frequency response (ISO 7401)",
    ),
    "highway": ("Highway", "Highway with clothoid curves and a lane change"),
    "city": ("City traffic", "Urban circuit with turns"),
    "race_track": ("Race track (racing line)", "Circuit with a computed minimum-curvature line and GGV speed profile"),
    "custom": (
        "Custom test cycle",
        'Segment list as JSON: [["straight", L, v_kmh], ["arc", R, angle_deg, v_kmh], ...]',
    ),
}
MANEUVER_PARAMS_EN = {
    "length": "Length",
    "speed_kmh": "Speed",
    "width": "Lateral offset",
    "duration": "Duration",
    "pre_length": "Lead-in",
    "post_length": "Run-out",
    "vehicle_width": "Vehicle width",
    "spacing": "Cone spacing",
    "n_cones": "Number of cones",
    "amplitude": "Lateral amplitude",
    "radius": "Radius",
    "laps": "Laps",
    "speed_start_kmh": "Start speed",
    "speed_end_kmh": "End speed",
    "offset": "Evasion offset",
    "evade_length": "Evasion length",
    "hold_length": "Hold length",
    "return_length": "Return length",
    "deceleration": "Deceleration",
    "brake_time": "Braking start",
    "target_kmh": "Target speed",
    "request": "Requested acceleration",
    "steering_wheel_deg": "Steering-wheel angle",
    "rise_time": "Rise time",
    "steering_ratio": "Steering ratio",
    "steer_rate_deg": "Steering-wheel rate",
    "amplitude_deg": "Steering-wheel amplitude",
    "frequency": "Frequency",
    "dwell": "Dwell time",
    "f_start": "Start frequency",
    "f_end": "End frequency",
    "ay_max": "Max. lateral acceleration",
    "track_width": "Track width",
    "ax_max": "Max. longitudinal acceleration",
    "ax_min": "Max. deceleration",
    "v_max_kmh": "Top speed",
    "segments": "Segments (JSON)",
}
CATEGORIES = {
    "Basis": ("Basic", "Basis"),
    "ISO": ("Standard tests", "Normtests"),
    "Fahrmanöver": ("Driving maneuvers", "Fahrmanöver"),
    "Strecke": ("Routes", "Strecken"),
}


def kpi_labels_de():
    import vdsim.reporting.kpi_evaluator as kpi

    src = inspect.getsource(kpi)
    return {m.group(1): m.group(2) for m in re.finditer(r'KPI\("([a-z0-9_]+)",\s*"([^"]+)"', src)}


def _nest(flat):
    # "vehicle.mass" -> {"vehicle": {"mass": ...}} (i18next reads dots as nesting)
    out = {}
    for key, value in flat.items():
        group, name = key.split(".", 1)
        out.setdefault(group, {})[name] = value
    return out


def build():
    cfg = VehicleConfig()
    params_de, units = {}, {}
    for group in fields(cfg):
        for f in fields(getattr(cfg, group.name)):
            key = f"{group.name}.{f.name}"
            params_de[key] = f.metadata.get("label", key)
            units[key] = f.metadata.get("unit", "")
    kpis_de = kpi_labels_de()
    missing = (
        sorted(set(params_de) - set(PARAMS_EN))
        + sorted(set(kpis_de) - set(KPIS_EN))
        + sorted(set(MANEUVER_INFO) - set(MANEUVERS_EN))
    )
    missing += sorted({p for info in MANEUVER_INFO.values() for p in info["params"]} - set(MANEUVER_PARAMS_EN))
    if missing:
        raise SystemExit(f"missing English texts: {missing}")
    out = {}
    for lang in ("en", "de"):
        en = lang == "en"
        out[lang] = {
            "paramGroup": {g: v[0 if en else 1] for g, v in GROUPS.items()},
            "param": _nest({k: (PARAMS_EN[k] if en else params_de[k]) for k in params_de}),
            "kpi": {k: (KPIS_EN[k] if en else kpis_de[k]) for k in kpis_de},
            "maneuver": {
                k: {
                    "label": MANEUVERS_EN[k][0] if en else v["label"],
                    "description": MANEUVERS_EN[k][1] if en else v["description"],
                    "category": CATEGORIES.get(v["category"], (v["category"],) * 2)[0 if en else 1],
                }
                for k, v in MANEUVER_INFO.items()
            },
            "maneuverParam": {
                p: (MANEUVER_PARAMS_EN[p] if en else lab)
                for info in MANEUVER_INFO.values()
                for p, (lab, _) in info["params"].items()
            },
        }
    return out


def main():
    data = build()
    for lang, content in data.items():
        path = ROOT / "web" / "src" / "locales" / lang / "domain.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
