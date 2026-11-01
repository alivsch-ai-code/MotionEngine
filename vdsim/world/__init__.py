"""Scenario world of the automated-driving platform: road network, traffic participants, scenario engine.

    road            Lane, RoadNetwork (stop lines, traffic lights, conflict zones, parking, corridors)
    road_builders   highway (merge / exit), rural road, urban street, intersection, roundabout, ring road
    traffic_models  IDM (Treiber 2000), MOBIL (Kesting 2007)
    actors          vehicles, trucks, cyclists, pedestrians, static obstacles, triggers, TrafficSimulator
    collision       SAT collision detection
    scenario        ADScenario (JSON), ScenarioInstance, build_scenario, list_ad_scenarios
    library         scenario types (Werling 5.3 test scenarios and more)
    engine          component "world/scenario_engine"
    render          top-view rendering (matplotlib)
    ego_stub        kinematic ego stand-in for tests without planner
"""

from ..framework.plugins import component
from .actors import (
                     EGO_ID,
                     Actor,
                     Cyclist,
                     LaneVehicle,
                     Pedestrian,
                     ScriptAction,
                     StaticObstacle,
                     TrafficSimulator,
                     Trigger,
                     Truck,
)
from .collision import collisions, pairwise_collisions, rect_corners, sat_overlap
from .engine import ScenarioEngine
from .road import (
                     ConflictZone,
                     Corridor,
                     Lane,
                     LaneLocation,
                     ParkingSpot,
                     RoadNetwork,
                     StopLine,
                     TrafficLight,
                     connect_poses,
)
from .scenario import (
                     ADScenario,
                     ScenarioInstance,
                     build_scenario,
                     ego_on_lane,
                     evaluate_success,
                     list_ad_scenarios,
                     list_scenario_types,
                     load_ad_scenario,
                     scenario_type,
)
from .traffic_models import IDMParams, MOBILParams, idm_acceleration, mobil_incentive

component(ScenarioEngine)

__all__ = [
    "Lane", "LaneLocation", "RoadNetwork", "StopLine", "TrafficLight", "ConflictZone", "ParkingSpot", "Corridor",
    "connect_poses", "Actor", "LaneVehicle", "Truck", "Cyclist", "Pedestrian", "StaticObstacle", "Trigger",
    "ScriptAction", "TrafficSimulator", "EGO_ID", "IDMParams", "MOBILParams", "idm_acceleration", "mobil_incentive",
    "sat_overlap", "rect_corners", "collisions", "pairwise_collisions", "ADScenario", "ScenarioInstance",
    "build_scenario", "list_ad_scenarios", "list_scenario_types", "load_ad_scenario", "ego_on_lane",
    "evaluate_success", "scenario_type", "ScenarioEngine",
]
