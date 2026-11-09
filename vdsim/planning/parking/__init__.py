"""Parking: path planning into parallel, perpendicular and angled spots for any steering configuration.

    steering      which wheels steer (front, rear, four-wheel counter-/in-phase): reference point and
                  turning limit (steering.py)
    reeds_shepp   shortest forward/backward paths with bounded curvature (Reeds and Shepp 1990)
    planner       Hybrid A* with Reeds-Shepp analytic expansion, multi-maneuver way out of tight spots,
                  shortcut smoothing, exact footprint collision check (planner.py)
    scenarios     parking situations (scenarios.py)
    tracking      closed loop: path tracking controller on a low-speed model with drive layout and traction

`park()` runs a complete parking task and returns the plan, the driven trajectory and KPIs.
Background and references: docs/planning/parking.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from .planner import Footprint, ParkingPath, ParkingPlanner, PlannerSettings
from .reeds_shepp import RSPath, all_paths, sample, shortest_path
from .scenarios import ENTRIES, KINDS, SIDES, ParkingScenario, build_scenario, center_to_reference, reference_to_center
from .steering import STEERING_MODES, SteeringGeometry, steering_geometry
from .tracking import LAYOUTS, DriveResult, DriveSettings, drive

__all__ = [
    "ENTRIES", "KINDS", "LAYOUTS", "SIDES", "STEERING_MODES", "DriveResult", "DriveSettings", "Footprint",
    "ParkingOutcome", "ParkingPath", "ParkingPlanner", "ParkingScenario", "PlannerSettings", "RSPath",
    "SteeringGeometry", "all_paths", "build_scenario", "center_to_reference", "drive", "park",
    "reference_to_center", "sample", "shortest_path", "steering_geometry",
]


@dataclass
class ParkingOutcome:
    scenario: ParkingScenario
    geometry: SteeringGeometry
    footprint: Footprint
    path: ParkingPath
    driven: DriveResult | None
    planner: ParkingPlanner


def park(vehicle, kind="parallel", entry="reverse", side="right", steering="front", layout="fwd",
         ratio=None, max_rear_angle=None, scenario_params=None, planner_settings: PlannerSettings | None = None,
         drive_settings: DriveSettings | None = None, simulate=True) -> ParkingOutcome:
    """Plan (and drive) a parking maneuver for a VehicleConfig.

    kind: parallel / perpendicular / angled; entry: reverse / forward; side: right / left;
    steering: front / rear / counter / in_phase; layout: fwd / rwd / awd (closed loop only).
    scenario_params: dimensions passed to the scenario builder (gap_length, aisle_width, angle_deg, ...).
    """
    v = getattr(vehicle, "vehicle", vehicle)
    geo = steering_geometry(vehicle, steering, ratio=ratio, max_rear_angle=max_rear_angle)
    fp = Footprint.from_vehicle(vehicle, geo)
    params = {"vehicle_length": float(v.length), "vehicle_width": float(v.width), **(scenario_params or {})}
    sc = build_scenario(kind, entry, side, **params)
    planner = ParkingPlanner(geo, fp, sc.polygons, sc.bounds, planner_settings)
    path = planner.plan(center_to_reference(sc.start, fp), center_to_reference(sc.goal, fp), sc.final_direction)
    driven = None
    if simulate and path.success:
        ds = drive_settings or DriveSettings()
        ds.layout = layout
        driven = drive(path, vehicle, geo, ds, planner.check)
    return ParkingOutcome(sc, geo, fp, path, driven, planner)
