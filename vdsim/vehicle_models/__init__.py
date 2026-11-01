"""Vehicle models: single-track (kinematic, linear, nonlinear), double-track, multibody."""

from ..core.registry import get
from .bicycle_model import KinematicBicycleModel, LinearBicycleModel, NonlinearBicycleModel
from .double_track_model import DoubleTrackModel
from .multibody_model import MultibodyModel
from .werling_models import WERLING_MODEL_LABELS, WerlingDynamicModel, WerlingKinematicModel  # noqa: F401

__all__ = ["DoubleTrackModel", "KinematicBicycleModel", "LinearBicycleModel", "MultibodyModel",
           "NonlinearBicycleModel", "create_vehicle_model"]

MODEL_LABELS = {
    "bicycle_kinematic": "Einspurmodell kinematisch",
    "bicycle_linear": "Einspurmodell linear",
    "bicycle_nonlinear": "Einspurmodell nichtlinear",
    "double_track": "Zweispurmodell (12 Zustände)",
    "multibody": "Mehrkörpermodell (24 Zustände)",
}
MODEL_LABELS.update(WERLING_MODEL_LABELS)


def create_vehicle_model(name, config):
    return get("vehicle_model", name)(config)
