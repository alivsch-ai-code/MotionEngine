"""RunContext: everything a component may need from its environment (dependency injection target).

Components never read global state. They receive a RunContext in reset(), which provides
the base time step, the vehicle configuration, the road network, deterministic random
number generators and a logger.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..core.logging_setup import get_logger


def stable_seed(*parts):
    # Deterministic 32 bit seed from strings/ints (independent of PYTHONHASHSEED)
    text = "/".join(str(p) for p in parts).encode()
    return int.from_bytes(hashlib.sha256(text).digest()[:4], "little")


@dataclass
class RunContext:
    dt: float = 0.01                 # base time step of the executor
    seed: int = 0                    # scenario seed (reproducibility)
    vehicle: Any = None              # vdsim.core.parameters.VehicleConfig
    road: Any = None                 # vdsim.world RoadNetwork
    scenario: Any = None             # scenario specification
    container: Any = None            # vdsim.framework.container.Container
    services: dict = field(default_factory=dict)
    recorder: Any = None             # optional result recorder
    t: float = 0.0

    def rng(self, name):
        # independent, reproducible random stream per component name
        return np.random.default_rng(stable_seed(self.seed, name))

    def logger(self, name):
        return get_logger(name)

    def service(self, key, default=None):
        if key in self.services:
            return self.services[key]
        if self.container is not None and self.container.has(key):
            return self.container.resolve(key)
        return default
