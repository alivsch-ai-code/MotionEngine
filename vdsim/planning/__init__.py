"""Trajectory planning after Werling (2011), chapters 2-3 and appendix A.

    polynomials   optimal quintic/quartic polynomials (3.3)-(3.8), closed-form jerk integral
    sampling      discretized target manifolds on an absolute time / arc-length grid (Satz 3)
    lateral       d(t) and d(s) candidate sets (3.5.1)
    longitudinal  velocity / following / merging / stopping modes (3.5.2, Tab. 3.1)
    combination   combination (3.2) and lazy world transformation (3.1, A.1)
    cost          multi-objective cost terms (kind="cost_term"), consistent Werling terms
    constraints   restrictions (kind="constraint")
    collision     circle based collision checking (kind="collision_checker", 3.5.4)
    selection     lazy selection, replacement strategy, fallback (3.5.5)
    plan          exact polynomial representation of the selected trajectory
    kinematics    ego geometry, reference points, motion prediction (4.5.2)
    analysis      continuous solution (3.12), (3.13), lock-in (3.14), sampling horizon
    planner       trajectory_planner/werling
    baselines     trajectory_planner/frenet_naive, trajectory_planner/sequential
    config        configs/planning/*.json

Importing the package registers all components.
"""

from . import collision, constraints, cost  # noqa: F401  (plugin registration)
from .analysis import (continuous_solution, estimate_sampling_horizon, lock_in_check, lock_in_distance,
                       optimal_end_time, transversality_residual)
from .baselines import FrenetNaivePlanner, SequentialPlanner
from .collision import CircleCollisionChecker, CollisionChecker, CollisionResult, CollisionSettings
from .combination import CandidateEvaluator, PlanningContext, TrajectoryBatch
from .config import available_configs, create_planner, load_planner_config
from .constraints import Constraint, ConstraintResult, ConstraintSettings
from .cost import CostModel, CostSettings, CostTerm
from .kinematics import EgoGeometry, convert_reference, taylor_prediction
from .plan import TrajectoryPlan
from .planner import WerlingPlanner, WerlingPlannerParams
from .polynomials import PolynomialSet, jerk_integral, quartic_coefficients, quintic_coefficients

__all__ = ["WerlingPlanner", "WerlingPlannerParams", "FrenetNaivePlanner", "SequentialPlanner", "TrajectoryPlan",
           "PolynomialSet", "quintic_coefficients", "quartic_coefficients", "jerk_integral", "CostTerm", "CostModel",
           "CostSettings", "Constraint", "ConstraintResult", "ConstraintSettings", "CollisionChecker",
           "CircleCollisionChecker", "CollisionResult", "CollisionSettings", "TrajectoryBatch", "CandidateEvaluator",
           "PlanningContext", "EgoGeometry", "convert_reference", "taylor_prediction", "continuous_solution",
           "transversality_residual", "optimal_end_time", "lock_in_distance", "lock_in_check",
           "estimate_sampling_horizon", "create_planner", "load_planner_config", "available_configs"]
