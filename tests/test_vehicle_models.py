import numpy as np
import pytest

from vdsim.analysis import LinearSingleTrackAnalysis, QuasiStaticAnalysis
from vdsim.core.conventions import G
from vdsim.core.registry import create
from vdsim.simulation.environment import Environment
from vdsim.simulation.vehicle_state import ControlInput

STEP = dict(maneuver="step_steer", maneuver_params={"steering_wheel_deg": 15, "speed_kmh": 80})


def _steady(result):
    tail = result["t"] > result["t"][-1] - 1.0
    return {k: np.mean(result[k][tail], axis=0) for k in ("r", "delta_f", "ay", "roll", "fz")}


def test_linear_model_matches_linear_analysis(run, sedan):
    result, _ = run(model="bicycle_linear", **STEP)
    s = _steady(result)
    gain = LinearSingleTrackAnalysis(sedan).steady_state_gains(80 / 3.6)["yaw_rate"]
    assert s["r"] / s["delta_f"] == pytest.approx(gain, rel=1e-3)


@pytest.mark.parametrize("model", ["bicycle_nonlinear", "double_track", "multibody"])
def test_nonlinear_models_close_to_linear_in_linear_range(run, sedan, model):
    result, _ = run(model=model, **STEP)
    s = _steady(result)
    gain = LinearSingleTrackAnalysis(sedan).steady_state_gains(80 / 3.6)["yaw_rate"]
    assert s["r"] / s["delta_f"] == pytest.approx(gain, rel=0.15)


def test_double_track_roll_and_loads_match_quasi_static(run, sedan):
    result, _ = run(model="double_track", **STEP)
    s = _steady(result)
    qa = QuasiStaticAnalysis(sedan)
    assert np.degrees(s["roll"] / s["ay"]) * G == pytest.approx(np.degrees(qa.roll_gradient) * G, rel=0.02)
    fz_qs, _ = qa.wheel_loads(0.0, s["ay"])
    assert np.allclose(s["fz"], fz_qs, rtol=0.03)


def test_multibody_wheel_loads_and_static_equilibrium(run, sedan):
    result, _ = run(model="multibody", maneuver="straight", maneuver_params={"length": 100, "speed_kmh": 50}, duration=3)
    fz_static = QuasiStaticAnalysis(sedan).static_wheel_loads()
    assert np.allclose(result["fz"][-1], fz_static, rtol=0.01)
    assert abs(result["heave"][-1]) < 2e-3


def test_kinematic_model_drives_kinematic_circle(sedan):
    model = create("vehicle_model", "bicycle_kinematic", sedan)
    u = ControlInput(steer_front=np.arctan(sedan.vehicle.wheelbase / 20.0))
    _, out = model.derivatives(0.0, model.initial_state(speed=10.0), u, Environment(), with_outputs=True)
    radius = 10.0 / out["r"]
    assert radius == pytest.approx(np.hypot(20.0, sedan.vehicle.cg_to_rear), rel=1e-3)


def test_wheel_lock_without_abs_and_abs_keeps_slip(run):
    with_abs, _ = run(model="double_track", maneuver="braking")
    without, _ = run(model="double_track", maneuver="braking", vehicle_overrides={"systems.abs_enabled": False})
    assert np.min(without["slip_ratio"]) < -0.9
    assert np.min(with_abs["slip_ratio"]) > -0.3
    def distance(r):
        i = np.searchsorted(r["t"], 1.0)
        return r["x"][-1] - r["x"][i]
    assert distance(with_abs) < distance(without)
    assert 38 < distance(with_abs) < 50  # 100 km/h on dry asphalt
