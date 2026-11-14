"""Single-track model against measured drives of a production car (vdsim.validation)."""

from pathlib import Path

import numpy as np
import pytest

from vdsim.analysis import LinearSingleTrackAnalysis
from vdsim.validation import PublicSpecs, calibrate_offset, compare, load_segments, predict, vehicle_config

SAMPLE = Path(__file__).parent / "data" / "comma_steering"
G70 = PublicSpecs(wheelbase=2.84, steer_ratio=13.56)


def test_public_specifications_give_the_reference_understeer_gradient():
    a = LinearSingleTrackAnalysis(vehicle_config(G70))
    # slip factor of the parameter source: sf = m (cF aF - cR aR) / (l^2 cF cR), understeer gradient = -sf l
    m, wb = 1600.0, 2.84
    af, ar = 0.4 * wb, 0.6 * wb
    cf, cr = 192150.0 / 1462.0 * m * (ar / wb) / 0.6, 202500.0 / 1462.0 * m * (af / wb) / 0.4
    sf = m * (cf * af - cr * ar) / (wb**2 * cf * cr)
    assert a.model.c_front == pytest.approx(cf, rel=1e-6) and a.model.c_rear == pytest.approx(cr, rel=1e-6)
    assert a.understeer_gradient == pytest.approx(-sf * wb, rel=1e-6)
    # the mass cancels in the lateral model
    heavy = LinearSingleTrackAnalysis(vehicle_config(PublicSpecs(wheelbase=2.84, steer_ratio=13.56, mass=2200.0)))
    assert heavy.understeer_gradient == pytest.approx(a.understeer_gradient, rel=1e-9)


def test_model_follows_measured_lateral_acceleration():
    segments = load_segments(SAMPLE)
    assert len(segments) == 3 and all(len(s["t"]) > 500 for s in segments)
    r = compare(vehicle_config(G70), segments)
    assert r["samples"] > 1000
    # no parameter is fitted: the model explains most of the measured lateral acceleration
    assert r["dynamic"]["r2"] > 0.7 and r["dynamic"]["rmse"] < 0.25
    # one steering angle offset per drive removes the bias
    assert r["dynamic_calibrated"]["rmse"] < r["dynamic"]["rmse"] and abs(r["dynamic_calibrated"]["bias"]) < 0.02
    assert 0.8 < r["dynamic_calibrated"]["slope"] < 1.2
    assert abs(r["offset_deg"]["mean"]) < 2.0


def test_dynamic_model_reduces_to_the_steady_state_gain():
    cfg = vehicle_config(G70)
    t = np.arange(0.0, 20.0, 0.1)
    seg = {"t": t, "vEgo": np.full_like(t, 25.0), "steeringAngleDeg": np.where(t > 2.0, 10.0, 0.0),
           "roll": np.zeros_like(t), "latAccelLocalizer": np.zeros_like(t), "latAccelSteeringAngle": np.zeros_like(t)}
    p = predict(cfg, seg)
    gain = LinearSingleTrackAnalysis(cfg).steady_state_gains(25.0)["lateral_acceleration"]
    expected = -gain * np.radians(10.0) / 13.56              # left steering gives a negative value in this data
    assert p["steady"][-1] == pytest.approx(expected, rel=1e-9)
    assert p["dynamic"][-1] == pytest.approx(expected, rel=1e-3)        # settled
    assert abs(p["dynamic"][21]) < abs(expected)                         # right after the step: not yet
    seg["latAccelLocalizer"] = predict(cfg, seg, offset_deg=0.7)["steady"]
    assert calibrate_offset(cfg, seg) == pytest.approx(0.7, abs=1e-6)
