"""Regression tests: every scenario preset of configs/scenarios against stored KPI values.

The golden file pins the behavior of the reviewed code base (first 4 s of every preset). A change
of a value is not automatically a bug, but it must be explained in the pull request. Regenerate
deliberately with

    MOTIONENGINE_UPDATE_GOLDEN=1 pytest tests/regression -m integration
"""

import json
import os
from pathlib import Path

import numpy as np
import pytest

from vdsim.reporting import evaluate
from vdsim.simulation.scenario import ScenarioManager
from vdsim.simulation.simulator import Simulator

GOLDEN = Path(__file__).with_name("golden_kpis.json")
DURATION = 4.0
REL_TOL = 1e-2   # cross-platform floating-point spread, see the assertion below
KEYS = ("max_ay", "max_ax", "min_ax", "max_yaw_rate", "max_beta", "max_roll", "max_steer", "max_lateral_error",
        "rms_lateral_error")
SCENARIOS = ScenarioManager().names()


def _run(name):
    sim = Simulator.from_scenario(ScenarioManager().load(name))
    sim.duration = min(sim.duration, DURATION)
    result = sim.run()
    kpis = {k.key: k.value for k in evaluate(result)}
    return sim, result, {k: float(kpis[k]) for k in KEYS if k in kpis}


@pytest.fixture(scope="module")
def golden():
    if os.environ.get("MOTIONENGINE_UPDATE_GOLDEN"):
        data = {name: _run(name)[2] for name in SCENARIOS}
        GOLDEN.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.mark.integration
@pytest.mark.parametrize("name", SCENARIOS)
def test_scenario_kpis_match_golden(name, golden):
    sim, result, kpis = _run(name)
    assert sim.stop_reason == "Simulationsdauer erreicht"
    for key in ("x", "y", "vx", "vy", "r", "ax", "ay"):
        assert np.all(np.isfinite(result[key])), key
    # physical envelope: no road vehicle exceeds ~1.5 g in the plane on mu <= 1.3
    assert np.max(np.hypot(result["ax"], result["ay"])) < 1.5 * 9.81
    assert name in golden, "new preset: regenerate the golden file"
    assert set(kpis) == set(golden[name])
    for key, value in kpis.items():
        # 1 %: identical code reproduced the golden values on one CI runner and missed them by 0.1 % (min_ax of
        # rennstrecke_sportwagen, gear shifts) on another; the physics fixes of this review moved KPIs by 6-37 %
        assert value == pytest.approx(golden[name][key], rel=REL_TOL, abs=1e-6), key
