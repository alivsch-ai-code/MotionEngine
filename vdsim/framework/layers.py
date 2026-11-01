"""Layer contracts of the automated-driving architecture.

    ScenarioWorld -> Perception -> Prediction -> Behavior Planning -> Trajectory Planning
        -> Vehicle Control -> Vehicle Dynamics -> Actuators -> Vehicle Plant -> (ego state back)

Each base class fixes the port names and types; implementations (native or custom)
must keep them, so that components of the same layer are exchangeable.
"""

from .component import Component, Port


class ScenarioWorldBase(Component):
    KIND, CATEGORY = "world", "Szenario"
    INPUTS = {"ego": Port("EgoState", "wahrer Fahrzeugzustand")}
    OUTPUTS = {"world": Port("WorldState", "Ground Truth")}


class PerceptionBase(Component):
    KIND, CATEGORY = "perception", "Perception"
    INPUTS = {"world": Port("WorldState"), "ego": Port("EgoState")}
    OUTPUTS = {"objects": Port("ObjectList"), "ego_estimate": Port("EgoState", "geschätzter Eigenzustand")}


class PredictionBase(Component):
    KIND, CATEGORY = "predictor", "Prediction"
    INPUTS = {"objects": Port("ObjectList"), "world": Port("WorldState", optional=True)}
    OUTPUTS = {"prediction": Port("Prediction")}


class BehaviorPlannerBase(Component):
    KIND, CATEGORY = "behavior_planner", "Behavior Planning"
    INPUTS = {"ego": Port("EgoState"), "objects": Port("ObjectList"), "prediction": Port("Prediction"),
              "world": Port("WorldState"),
              "trajectory": Port("PlannedTrajectory", "letzte Solltrajektorie (Gefahrenindikator)", optional=True,
                                 feedback=True)}
    OUTPUTS = {"behavior": Port("BehaviorCommand")}


class TrajectoryPlannerBase(Component):
    KIND, CATEGORY = "trajectory_planner", "Trajectory Planning"
    INPUTS = {"ego": Port("EgoState"), "behavior": Port("BehaviorCommand"), "prediction": Port("Prediction"),
              "status": Port("ControllerStatus", "Trackingfehler / Reinitialisierung", optional=True, feedback=True)}
    OUTPUTS = {"trajectory": Port("PlannedTrajectory"), "debug": Port("PlannerDebug")}


class TrackingControllerBase(Component):
    KIND, CATEGORY = "tracking_controller", "Vehicle Control"
    INPUTS = {"ego": Port("EgoState"), "trajectory": Port("PlannedTrajectory")}
    OUTPUTS = {"command": Port("ControlCommand"), "status": Port("ControllerStatus")}


class VehicleDynamicsBase(Component):
    KIND, CATEGORY = "vehicle_dynamics", "Vehicle Dynamics"
    INPUTS = {"command": Port("ControlCommand"), "ego": Port("EgoState")}
    OUTPUTS = {"demand": Port("ActuatorCommand")}


class ActuatorBase(Component):
    KIND, CATEGORY = "actuator", "Actuators"
    INPUTS = {"demand": Port("ActuatorCommand"), "ego": Port("EgoState")}
    OUTPUTS = {"control": Port("ControlInput")}


class VehiclePlantBase(Component):
    KIND, CATEGORY = "vehicle_plant", "Fahrzeug"
    INPUTS = {"control": Port("ControlInput")}
    OUTPUTS = {"ego": Port("EgoState")}
    DIRECT_FEEDTHROUGH = False


LAYER_ORDER = ("world", "perception", "predictor", "behavior_planner", "trajectory_planner", "tracking_controller",
               "vehicle_dynamics", "actuator", "vehicle_plant")

LAYER_BASES = {
    "world": ScenarioWorldBase, "perception": PerceptionBase, "predictor": PredictionBase,
    "behavior_planner": BehaviorPlannerBase, "trajectory_planner": TrajectoryPlannerBase,
    "tracking_controller": TrackingControllerBase, "vehicle_dynamics": VehicleDynamicsBase,
    "actuator": ActuatorBase, "vehicle_plant": VehiclePlantBase,
}
