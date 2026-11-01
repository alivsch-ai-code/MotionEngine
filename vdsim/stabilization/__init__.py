"""Trajectory stabilization after Werling (2011), chapter 4, plus classical tracking controllers and the
vehicle layers of the AD chain (contracts.md section 1).

Components (registered on import):
    tracking_controller/werling_bilevel              switching (Fig. 4.13) + re-initialization (4.5), default
    tracking_controller/werling_kinematic_orientation  Satz 4 (rear axle, forward/reverse)
    tracking_controller/werling_kinematic_center     Satz 6 (geometric center, forward)
    tracking_controller/werling_dynamic              Satz 8 (exact I/O linearization, fast driving)
    tracking_controller/pure_pursuit, stanley, lqr, mpc          classical lateral controllers
    tracking_controller/pid, pi, ff_fb, acc, speed_pi            classical longitudinal controllers
    tracking_controller/composite                    lateral + longitudinal
    vehicle_dynamics/split_range                     Werling 5.1.2.2
    actuator/steering_powertrain                     steering actuator, drive/brake delays
    vehicle_plant/vehicle_model                      any vdsim vehicle model
"""

from . import classic_lateral, classic_longitudinal, composite, plant, switching, vehicle_layers  # noqa: F401
from . import werling_dynamic, werling_kinematic  # noqa: F401
from .classic_lateral import LQR, MPC, PurePursuit, Stanley
from .classic_longitudinal import ACC, PI, PID, FeedForwardFeedback, VehicleSpeedController
from .composite import CompositeController
from .plant import VehicleModelPlant
from .reinit import ReinitMonitor, elliptic_measure, predict_motion, predict_reference_point
from .switching import WerlingBilevel, select_controller
from .vehicle_layers import SplitRangeDynamics, SteeringPowertrainActuator
from .werling_dynamic import (WerlingDynamic, ZeroDynamicsReference, lookahead_for_damping, minimum_phase_bound,
                              solve_linearizing_input, zero_dynamics_coefficients)
from .werling_kinematic import (WerlingKinematicCenter, WerlingKinematicOrientation, center_law,
                                kin_tracking_with_orientation_stab, orientation_law)

DEFAULT_CONTROLLER = "tracking_controller/werling_bilevel"

__all__ = ["ACC", "CompositeController", "DEFAULT_CONTROLLER", "FeedForwardFeedback", "LQR", "MPC", "PI", "PID",
           "PurePursuit", "ReinitMonitor", "SplitRangeDynamics", "Stanley", "SteeringPowertrainActuator",
           "VehicleModelPlant", "VehicleSpeedController", "WerlingBilevel", "WerlingDynamic",
           "WerlingKinematicCenter", "WerlingKinematicOrientation", "ZeroDynamicsReference", "center_law",
           "elliptic_measure", "kin_tracking_with_orientation_stab", "lookahead_for_damping", "minimum_phase_bound",
           "orientation_law", "predict_motion", "predict_reference_point", "select_controller",
           "solve_linearizing_input", "zero_dynamics_coefficients"]
