"""Example: own cost term for the Werling trajectory planner (kind="cost_term").

Usage in a planner configuration (configs/planning/*.json or API):

    "cost": {"custom": [{"spec": "python:examples/custom_nodes/python/my_cost_function.py:KeepRightCost",
                         "params": {"weight": 2.0}}]}

A separable term implements lateral() and/or longitudinal() and is evaluated on the candidate
sets (cheap, enters the cost sorting). A term with SCOPE = "combined" implements combined()
and is evaluated in the re-ranking window on world trajectories. Only the consistent Werling
terms keep the Bellman guarantee; an additional term shifts the optimum (see theory.md).
"""

from dataclasses import dataclass

import numpy as np

from vdsim.core.parameters import param
from vdsim.framework.knowledge import ComponentDoc
from vdsim.planning.cost import CostTerm


@dataclass
class KeepRightParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(1.0, "1/(m s)", "Gewicht Rechtsfahrgebot ∫ max(0, d − d_rechts) dt", min=0.0)
    d_right: float = param(0.0, "m", "Bevorzugter Querversatz (rechts der Referenz < 0)", min=-5.0, max=5.0)


class KeepRightCost(CostTerm):
    NAME, VERSION, LABEL = "keep_right", "1.0.0", "Rechtsfahrgebot (Beispiel)"
    PARAMS = KeepRightParams
    SCOPE = "separable"
    DOC = ComponentDoc(summary="Bestraft Querversätze links von d_rechts (separierbarer Querterm).",
                       limitations=["nicht konsistent im Sinne von Werling Satz 3"])

    def lateral(self, lat, ctx):
        # lat.d: (n, k) lateral offsets on the evaluation grid lat.grid (time for d(t), arc length for d(s))
        dx = lat.grid[1] - lat.grid[0] if len(lat.grid) > 1 else 0.0
        excess = np.maximum(0.0, lat.d - self.params.d_right)
        return self.params.weight * dx * excess.sum(axis=1)
