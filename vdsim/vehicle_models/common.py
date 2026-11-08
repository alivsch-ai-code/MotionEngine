"""Helpers shared by the vehicle models: resistances, longitudinal force estimate, axle stiffness."""

import numpy as np

from ..core.conventions import AIR_DENSITY, G


def aero_drag(vehicle, vx, wind=0.0):
    # wind > 0 is head wind (see Environment.wind_speed): it raises the air speed over the body
    v_rel = vx + wind
    return 0.5 * AIR_DENSITY * vehicle.drag_coefficient * vehicle.frontal_area * v_rel * abs(v_rel)


def rolling_resistance(vehicle, vx):
    return vehicle.rolling_resistance * vehicle.mass * G * np.tanh(vx / 0.5)


def wheel_force_request(u, vehicle, vx):
    # Longitudinal force per wheel from drive and brake torques (no wheel dynamics);
    # brakes act against the direction of travel and cannot reverse the vehicle
    return (u.drive_torque - u.brake_torque * np.tanh(vx / 0.2)) / vehicle.wheel_radius


def axle_cornering_stiffness(tire, fz_tire, delta_alpha=1e-4):
    # Small-slip cornering stiffness of one axle (two tires) at the given tire load
    _, fy, _ = tire.forces(delta_alpha, 0.0, fz_tire)
    return 2.0 * float(fy) / delta_alpha
