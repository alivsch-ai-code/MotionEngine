"""Prediction layer: constant acceleration in Frenet coordinates (Werling 3.5.2), constant velocity, lane following."""

from ..framework.plugins import component
from .predictors import (
                         ConstantAccelerationPredictor,
                         ConstantVelocityPredictor,
                         LaneFollowingPredictor,
                         PredictorParams,
                         ca_motion,
                         lateral_convergence,
)

component(ConstantAccelerationPredictor)
component(ConstantVelocityPredictor)
component(LaneFollowingPredictor)

__all__ = ["ConstantAccelerationPredictor", "ConstantVelocityPredictor", "LaneFollowingPredictor", "PredictorParams",
           "ca_motion", "lateral_convergence"]
