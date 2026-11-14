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

import logging  # noqa: E402

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


# ----------------------------------------------------------------------------- automated-driving stack
AD_SCENARIOS_EN = {
    "ausscherer_stauende": ("Cut-out at the end of a queue", "The vehicle ahead pulls out shortly before a standing vehicle; the ego has to react."),
    "autobahn_ausfahrt": ("Highway exit", "The ego starts on the left lane, changes two lanes to the right in time and leaves the highway over the deceleration lane."),
    "autobahn_ueberholen": ("Highway overtaking", "Three-lane highway: a slower vehicle on the right lane is overtaken on the left, then the ego returns to the right lane (keep-right rule)."),
    "einfaedeln_lkw": ("Highway entry", "Highway entry after Werling 5.3.2: merging from the acceleration lane into the gap between two trucks."),
    "einscherer": ("Cut-in", "A slower vehicle cuts in from the left 22 m ahead of the ego."),
    "innerorts_werling": ("Urban drive", "Urban road after Werling 5.3.1 at 30 km/h: parked cars, two pedestrians step onto the road from between parked cars and are visible late, an oncoming vehicle turns left wrongly at the junction, two cyclists at the roadside."),
    "kreisverkehr": ("Roundabout", "Single-lane roundabout: entry from the west, yielding to the traffic in the ring, exit to the east."),
    "kreuzung_ampel_geradeaus": ("Intersection with traffic light", "The ego approaches at red, stops at the stop line and drives straight on at green; cross traffic drives during the ego's red phase."),
    "kreuzung_vorfahrt_links": ("Intersection with right of way", "The ego comes from the minor road, yields to the cross traffic and turns left."),
    "laengsparken_rueckwaerts": ("Reverse parallel parking", "Reverse parallel parking into an 8.5 m gap: forward beside the gap, stop, change of direction at standstill, reverse to the middle of the gap."),
    "landstrasse_ueberholen": ("Overtaking on a country road", "Country road with a slow truck and oncoming traffic: overtaking over the oncoming lane only with a sufficient gap; no overtaking in the section with a solid center line."),
    "notausweichen_hindernis": ("Emergency evasion", "A broken-down vehicle becomes visible only 60 m ahead; evasion onto the free left lane."),
    "verkehrsdichte_20": ("Traffic density", "Three-lane ring road with 20 vehicles per km and lane, IDM car following and MOBIL lane changes, 10 % trucks."),
    "werling_autobahnversuch": ("Werling highway experiment", "Highway experiment after Werling 5.3.2: merging between trucks, a delayed lane change because of a fast approaching car, a truck pulling out and a side-wind gust (lateral_impulse) at t = 38.5 s."),
}
AD_KPIS_EN = {
    "collision": "Collision", "off_road": "Left the road", "min_distance": "Min. distance to objects", "min_ttc": "Min. time to collision",
    "min_thw": "Min. time headway", "max_drac": "Max. DRAC", "min_pet": "Min. post-encroachment time", "max_ay": "Max. lateral acceleration",
    "max_ax": "Max. longitudinal acceleration", "min_ax": "Max. deceleration", "rms_jerk_long": "RMS longitudinal jerk",
    "rms_jerk_lat": "RMS lateral jerk", "max_jerk": "Max. jerk", "rms_steer_rate": "RMS steering rate", "rms_e_n": "RMS lateral error",
    "max_e_n": "Max. lateral error", "rms_e_t": "RMS longitudinal error", "max_e_t": "Max. longitudinal error",
    "max_e_theta": "Max. heading error", "reinit_count": "Re-initializations", "plan_time_mean": "Planning time, mean",
    "plan_time_p95": "Planning time, p95", "plan_time_max": "Planning time, max", "fallback_share": "Share of fallback trajectories",
    "consistency_mean": "Consistency deviation, mean", "consistency_max": "Consistency deviation, max",
    "candidates_mean": "Candidates per cycle", "cost_mean": "Mean trajectory cost", "distance": "Distance driven",
    "mean_speed": "Mean speed", "final_speed": "Final speed", "goal_reached": "Goal reached", "duration": "Simulated time",
    "real_time_factor": "Real-time factor",
}
AD_GROUPS_EN = {"Sicherheit": "Safety", "Komfort": "Comfort", "Tracking": "Tracking", "Planer": "Planner", "Kosten": "Cost",
                "Mission": "Mission", "Laufzeit": "Runtime"}
AD_CRITERIA = {  # mission criteria: (English, German)
    "no_collision": ("No collision", "Keine Kollision"), "stay_on_road": ("Stay on the road", "Auf der Fahrbahn bleiben"),
    "reach_goal": ("Reach the goal", "Ziel erreichen"), "final_speed_max": ("Final speed below the limit", "Endgeschwindigkeit unter der Grenze"),
    "final_lane": ("End on the required lane", "Auf der geforderten Spur enden"), "parked": ("Parked in the spot", "In der Lücke geparkt"),
    "min_progress": ("Minimum distance driven", "Mindeststrecke gefahren"),
}
STACK_KINDS = ("world", "perception", "predictor", "behavior_planner", "trajectory_planner", "tracking_controller",
               "vehicle_dynamics", "actuator", "vehicle_plant")
COMPONENTS_EN = {
    "actuator/steering_powertrain": "Steering actuator and drive/brake",
    "behavior_planner/rule_based": "Rule-based behavior planning",
    "perception/ground_truth": "Ground truth (undisturbed)",
    "perception/object_sensor": "Object sensor (range, noise, latency)",
    "predictor/constant_acceleration": "Constant acceleration (Frenet, Werling 3.5.2)",
    "predictor/constant_velocity": "Constant velocity (Cartesian)",
    "predictor/lane_following": "Lane following with lateral intention",
    "tracking_controller/acc": "Adaptive cruise control (ACC)",
    "tracking_controller/composite": "Combination of a lateral and a longitudinal controller",
    "tracking_controller/ff_fb": "Feedforward + feedback (longitudinal)",
    "tracking_controller/lqr": "LQR (gain scheduled over speed)",
    "tracking_controller/mpc": "MPC (linear time-varying)",
    "tracking_controller/pi": "PI speed controller",
    "tracking_controller/pid": "PID speed controller",
    "tracking_controller/pure_pursuit": "Pure Pursuit",
    "tracking_controller/speed_pi": "Vehicle speed controller (PI with anti-windup)",
    "tracking_controller/stanley": "Stanley",
    "tracking_controller/werling_bilevel": "Werling: bi-level stabilization (switching + re-initialization)",
    "tracking_controller/werling_dynamic": "Werling: exact input-output linearization (theorem 8)",
    "tracking_controller/werling_kinematic_center": "Werling: Lyapunov without orientation stabilization (theorem 6)",
    "tracking_controller/werling_kinematic_orientation": "Werling: Lyapunov with orientation stabilization (theorem 4)",
    "trajectory_planner/frenet_naive": "Frenet planner (naive, without consistency)",
    "trajectory_planner/learned": "Trajectory planner (learned, verified by Werling)",
    "trajectory_planner/sequential": "Sequential planner (longitudinal first, then lateral)",
    "trajectory_planner/werling": "Trajectory planner (Werling)",
    "trajectory_planner/werling_parking": "Trajectory planner (Werling + parking planner)",
    "vehicle_dynamics/split_range": "Split-range longitudinal force allocation (Werling 5.1.2.2)",
    "vehicle_plant/vehicle_model": "Vehicle model (vdsim)",
    "world/scenario_engine": "Scenario engine",
}


COMPONENT_DOCS_EN = {  # (summary, purpose)
    "actuator/steering_powertrain": (
        "Integrates the steering rate or takes the steering angle, and models the steering actuator (latency, characteristic, rate limit) and delayed drive and brake torques.",
        "Connects the outputs of the trajectory controller with the plant."),
    "behavior_planner/rule_based": (
        "State machine for lane keeping, lane changes, merging, overtaking, intersections, roundabouts and parking; it provides the reference curve, the longitudinal modes and the corridor for the trajectory planner.",
        "Behavior layer after Werling 3.6: choose the targets so that the reactive trajectory planning rarely has to avoid a collision."),
    "perception/ground_truth": (
        "Passes on the objects of the scenario engine and the true ego state unchanged.",
        "Reference for developing prediction, behavior and planning without perception errors."),
    "perception/object_sensor": (
        "Creates a disturbed object list and an estimate of the ego state from the ground truth.",
        "More realistic inputs for prediction and behavior: limited range, occlusion, measurement noise, missed detections and latency; reproducible through the scenario seed."),
    "predictor/constant_acceleration": (
        "Predicts objects with constant acceleration along their lane in Frenet coordinates.",
        "Prediction of leading and gap vehicles for the following and merging modes after Werling 3.5.2."),
    "predictor/constant_velocity": (
        "Straight-line prediction with constant speed (optionally constant yaw rate).",
        "Simple reference prediction that needs no map, for example for pedestrians."),
    "predictor/lane_following": (
        "Constant speed along the lane sequence; the lateral offset converges to the center of the target lane.",
        "Detects lane changes (cut-ins) early from the lateral speed relative to the lane."),
    "tracking_controller/acc": (
        "Distance-based longitudinal control with a constant time gap.",
        "Comparison of trajectory-based longitudinal control with a classical ACC without a planner."),
    "tracking_controller/composite": (
        "Combines any lateral and any longitudinal controller into one tracking controller.",
        "Classical decoupled lateral and longitudinal control as a comparison with the coupled Werling control."),
    "tracking_controller/ff_fb": (
        "Acceleration feedforward from the trajectory with feedback of the speed and longitudinal errors.",
        "Time-based longitudinal tracking (trajectory instead of path)."),
    "tracking_controller/lqr": (
        "State feedback on the lateral error model of the single-track model with a discrete Riccati solution, gain scheduling over speed and a steady-state feedforward.",
        "Optimal linear comparison controller (Rajamani 3.2)."),
    "tracking_controller/mpc": (
        "Linear time-varying model predictive lateral control along the trajectory horizon with limits on steering angle and steering rate.",
        "Comparison controller that takes actuator limits into account explicitly (Werling Tab. 4.1)."),
    "tracking_controller/pi": (
        "PI controller on the speed error.",
        "Classical longitudinal controller."),
    "tracking_controller/pid": (
        "PID controller on the speed error of the planned trajectory.",
        "Classical longitudinal controller for comparison."),
    "tracking_controller/pure_pursuit": (
        "Geometric lateral controller: a circular arc from the rear axle to a target point on the path.",
        "Simple, robust comparison controller (Snider 2009)."),
    "tracking_controller/speed_pi": (
        "PI speed controller with back-calculation anti-windup and feedforward.",
        "Robust speed controller under actuator saturation."),
    "tracking_controller/stanley": (
        "Lateral controller on the lateral error of the front axle and the heading error (Stanley, DARPA Grand Challenge).",
        "Comparison controller with good tracking at medium speeds."),
    "tracking_controller/werling_bilevel": (
        "Default tracking controller: bumpless switching between the three Werling controllers by reference point and driving direction, plus the trigger of re-initializations and the motion prediction for the planner.",
        "Combines the low-level stabilization (permanent disturbances, model errors) with the high-level stabilization by re-initialization after impulse disturbances (Werling 2.3, 4.4, 4.5)."),
    "tracking_controller/werling_dynamic": (
        "Exactly input-output linearizing tracking controller on the dynamic single-track model with an isotropic Pacejka tire, for fast driving.",
        "Stabilizes a reference point ahead of the center of gravity on the planned trajectory; the speed-dependent look-ahead keeps the damping of the zero dynamics constant (Werling 4.3)."),
    "tracking_controller/werling_kinematic_center": (
        "Lyapunov-based tracking controller of the geometric vehicle center without orientation stabilization, for slow forward driving.",
        "Stabilizes the point about half a wheelbase ahead of the rear axle directly, so the vehicle steers more calmly (Werling 4.2.4)."),
    "tracking_controller/werling_kinematic_orientation": (
        "Lyapunov-based tracking controller of the rear-axle center with orientation stabilization, for slow forward and reverse driving.",
        "Stabilizes position, orientation, speed and steering angle of the extended kinematic single-track model along the trajectory, also at standstill and in reverse (Werling 4.2.3)."),
    "trajectory_planner/frenet_naive": (
        "Comparison planner: Frenet sampling with a relative end-time grid and replanning from the measured state.",
        "Shows the benefit of temporal consistency (Werling Fig. 3.2) in planner comparisons."),
    "trajectory_planner/learned": (
        "A network proposes the trajectory (end offset, end speed, end times); the Werling planner builds only the candidates next to the proposal and checks them with its restrictions and collision check.",
        "Learned planning with the safety of the Werling planner: if no local candidate is valid, or the best one lies on the border of the local set, the cycle searches completely."),
    "trajectory_planner/sequential": (
        "Comparison planner: the longitudinal motion without knowledge of the lateral motion, then the lateral motion (Werling 3.1).",
        "Shows the advantage of the combined lateral and longitudinal optimization (evasion with matched braking)."),
    "trajectory_planner/werling": (
        "Trajectory planning after Werling: optimal polynomials in Frenet coordinates, discretized target manifolds on an absolute time grid, temporal consistency and bi-level stabilization.",
        "Reactive, time-critical collision avoidance with combined longitudinal and lateral optimization, temporally consistent by Bellman's principle while no restriction is active (Werling 2011, ch. 3)."),
    "trajectory_planner/werling_parking": (
        "Werling planner for normal driving; for a parking task a Hybrid A* / Reeds-Shepp planner plans the parking path and hands it to the controller one move at a time.",
        "Parking maneuvers with changes of direction, which the Frenet planner cannot represent on the reference line."),
    "vehicle_dynamics/split_range": (
        "Converts the desired longitudinal force or acceleration into wheel torques through drive or brake.",
        "The design models of the tracking controllers neglect rolling and air resistance; this layer compensates them and removes remaining errors (head wind, slope) with an integrator."),
    "vehicle_plant/vehicle_model": (
        "Wraps a registered vdsim vehicle model as the plant of the control chain.",
        "Any vehicle model (Werling design models, single-track, double-track, multibody) as the plant for controller development and robustness studies."),
    "world/scenario_engine": (
        "Simulates the road users of a scenario and provides the ground truth.",
        "Reproducible test scenarios for the whole chain: actors with IDM/MOBIL, scripted triggers, traffic lights, collision and off-road detection, and disturbance events."),
}


def ad_library():
    # German texts of the automated-driving stack, read from the library
    from vdsim import api
    from vdsim.research import KPI_INFO

    scenarios = {s["name"]: (s.get("label") or s["name"], s.get("description") or "") for s in api.list_scenarios()}
    kpis = {k: v[0] for k, v in KPI_INFO.items()}
    groups = sorted({v[2] for v in KPI_INFO.values()})
    components = {f"{c['kind']}/{c['name']}": c.get("label") or c["name"] for c in api.list_components()
                  if c["kind"] in STACK_KINDS}
    docs = {}
    for spec in components:
        doc = api.describe_component(spec).get("doc") or {}
        docs[spec] = (doc.get("summary") or "", doc.get("purpose") or "")
    return scenarios, kpis, groups, components, docs


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
    scenarios_de, ad_kpis_de, ad_groups, components_de, docs_de = ad_library()
    missing += sorted(set(scenarios_de) - set(AD_SCENARIOS_EN)) + sorted(set(ad_kpis_de) - set(AD_KPIS_EN))
    missing += sorted(set(ad_groups) - set(AD_GROUPS_EN)) + sorted(set(components_de) - set(COMPONENTS_EN))
    missing += sorted(set(docs_de) - set(COMPONENT_DOCS_EN))
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
            "adScenario": {k: (AD_SCENARIOS_EN[k][1] if en else v[1]) for k, v in scenarios_de.items()},
            "adScenarioLabel": {k: (AD_SCENARIOS_EN[k][0] if en else v[0]) for k, v in scenarios_de.items()},
            "adKpi": {k: (AD_KPIS_EN[k] if en else v) for k, v in ad_kpis_de.items()},
            "adKpiGroup": {g: (AD_GROUPS_EN[g] if en else g) for g in ad_groups},
            "adCriterion": {k: v[0 if en else 1] for k, v in AD_CRITERIA.items()},
            "component": _nest({k.replace("/", ".", 1): (COMPONENTS_EN[k] if en else v) for k, v in components_de.items()}),
            "componentDoc": _nest({k.replace("/", ".", 1): {"summary": (COMPONENT_DOCS_EN[k] if en else v)[0],
                                                             "purpose": (COMPONENT_DOCS_EN[k] if en else v)[1]}
                                   for k, v in docs_de.items()}),
            "maneuverParam": {
                p: (MANEUVER_PARAMS_EN[p] if en else lab)
                for info in MANEUVER_INFO.values()
                for p, (lab, _) in info["params"].items()
            },
        }
    return out


def main():
    logging.disable(logging.WARNING)
    data = build()
    for lang, content in data.items():
        path = ROOT / "web" / "src" / "locales" / lang / "domain.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
