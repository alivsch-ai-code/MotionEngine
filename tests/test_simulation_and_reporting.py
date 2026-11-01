import numpy as np
import pytest

from vdsim.analysis import LinearSingleTrackAnalysis
from vdsim.core.parameters import VehicleConfig, load_vehicle_preset
from vdsim.reporting import compare, evaluate
from vdsim.reporting.kpi_evaluator import iso2631_weighted_rms
from vdsim.reporting.report_generator import engineering_summary, generate_pdf
from vdsim.simulation.results import SimulationResult
from vdsim.simulation.scenario import Scenario, ScenarioManager
from vdsim.simulation.solver import create_solver


def test_vehicle_config_json_roundtrip(tmp_path, sedan):
    sedan.save(tmp_path / "v.json")
    assert VehicleConfig.load(tmp_path / "v.json").to_dict() == sedan.to_dict()


def test_scenario_library_builds(sedan):
    manager = ScenarioManager()
    assert len(manager.names()) >= 20
    for name in manager.names():
        scenario = manager.load(name)
        config = scenario.build_config()
        assert len(scenario.build_trajectory(config).x) > 10, name


def test_scenario_roundtrip(tmp_path):
    sc = Scenario(name="x", maneuver="slalom", maneuver_params={"speed_kmh": 40}, vehicle_overrides={"tires.mu": 0.8})
    sc.save(tmp_path / "s.json")
    loaded = Scenario.load(tmp_path / "s.json")
    assert loaded.to_dict() == sc.to_dict()
    assert loaded.build_config().tires.mu == 0.8


def test_solvers_agree():
    f = lambda t, x: np.array([x[1], -4.0 * x[0]])  # harmonic oscillator, omega = 2
    exact = np.cos(2.0)
    for name in ("rk4", "heun", "adaptive"):
        solver = create_solver(name, substeps=10)
        x = np.array([1.0, 0.0])
        for k in range(100):
            x = solver.step(f, k * 0.01, x, 0.01)
        assert x[0] == pytest.approx(exact, abs=1e-4 if name != "heun" else 1e-3), name


def test_results_save_load(tmp_path, run):
    result, _ = run(model="bicycle_nonlinear", maneuver="straight", maneuver_params={"length": 60}, duration=2)
    evaluate(result)
    for suffix in (".npz", ".json"):
        result.save(tmp_path / f"r{suffix}")
        loaded = SimulationResult.load(tmp_path / f"r{suffix}")
        assert np.allclose(loaded["x"], result["x"])
        assert loaded.kpis.keys() == result.kpis.keys()
    result.save(tmp_path / "r.csv")
    assert "fz_FL" in (tmp_path / "r.csv").read_text().splitlines()[0]


def test_maneuver_kpis(run):
    step, _ = run(model="double_track", maneuver="step_steer")
    k = {x.key: x.value for x in evaluate(step)}
    assert 0.05 < k["response_time"] < 0.4 and k["yaw_overshoot"] >= 0
    brake, _ = run(model="double_track", maneuver="braking")
    k = {x.key: x.value for x in evaluate(brake)}
    assert 8.0 < k["mfdd"] < 10.5
    circle, _ = run(model="bicycle_linear", maneuver="circle", maneuver_params={"laps": 1})
    k = {x.key: x.value for x in evaluate(circle)}
    eg = np.degrees(LinearSingleTrackAnalysis(load_vehicle_preset("mid_size_sedan")).understeer_gradient)
    assert k["understeer_gradient"] == pytest.approx(eg, rel=0.1)


def test_iso2631_weighting():
    fs = 200.0
    t = np.arange(0, 60, 1 / fs)
    for f, wk in ((1.0, 0.482), (2.0, 0.531), (6.3, 1.054)):
        assert iso2631_weighted_rms(np.sin(2 * np.pi * f * t), fs) == pytest.approx(wk / np.sqrt(2), rel=0.03)


def test_report_and_comparison(tmp_path, run):
    a, _ = run(model="bicycle_nonlinear", maneuver="iso_double_lane_change")
    b, _ = run(model="bicycle_nonlinear", maneuver="iso_double_lane_change", lateral_controller="mpc")
    table = compare([a, b])
    assert table["max_lateral_error"]["values"][1] < table["max_lateral_error"]["values"][0]
    pdf = generate_pdf([a, b], tmp_path / "r.pdf")
    assert pdf.stat().st_size > 50_000
    assert "| Max. Querbeschleunigung |" in engineering_summary([a, b])
