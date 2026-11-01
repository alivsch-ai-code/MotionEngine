import os
import sys
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vdsim.core.parameters import load_vehicle_preset  # noqa: E402
from vdsim.simulation.scenario import Scenario  # noqa: E402
from vdsim.simulation.simulator import Simulator  # noqa: E402


@pytest.fixture
def sedan():
    return load_vehicle_preset("mid_size_sedan")


@pytest.fixture
def run():
    # run a scenario given as keyword arguments, returns (result, simulator)
    def _run(**kwargs):
        kwargs.setdefault("name", "test")
        sim = Simulator.from_scenario(Scenario(**kwargs))
        return sim.run(), sim
    return _run


@pytest.fixture
def samples():
    return ROOT / "configs" / "trajectories"
