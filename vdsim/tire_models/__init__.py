"""Tire models: linear, Pacejka Magic Formula, brush model."""

from dataclasses import asdict

from ..core.registry import get
from .brush_model import BrushTire
from .isotropic import IsotropicPacejkaTire  # noqa: F401  (Werling 4.3.2, registered as "isotropic")
from .linear_tire import LinearTire
from .pacejka import PacejkaTire

__all__ = ["BrushTire", "LinearTire", "PacejkaTire", "create_tire_set", "create_tires"]


def create_tires(tire_params):
    # (front, rear) tire model instances from TireParameters
    kwargs = asdict(tire_params)
    model = kwargs.pop("model")
    front = kwargs.pop("cornering_stiffness_front")
    rear = kwargs.pop("cornering_stiffness_rear")
    cls = get("tire_model", model)
    return cls(cornering_stiffness=front, **kwargs), cls(cornering_stiffness=rear, **kwargs)


def create_tire_set(tire_params):
    # one tire model instance for all four wheels (FL, FR, RL, RR) with per-wheel stiffness
    import numpy as np
    kwargs = asdict(tire_params)
    model = kwargs.pop("model")
    front = kwargs.pop("cornering_stiffness_front")
    rear = kwargs.pop("cornering_stiffness_rear")
    return get("tire_model", model)(cornering_stiffness=np.array([front, front, rear, rear]), **kwargs)
