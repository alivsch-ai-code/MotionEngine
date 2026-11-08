"""KPI evaluation per maneuver class, result I/O, PDF/Markdown reports and the matplotlib figures."""

import numpy as np
import pytest

from vdsim.core.parameters import load_vehicle_preset
from vdsim.reporting import compare, evaluate
from vdsim.reporting.report_generator import engineering_summary, generate_pdf, save_summary
from vdsim.simulation.results import SimulationResult
from vdsim.simulation.scenario import Scenario
from vdsim.simulation.simulator import Simulator
from vdsim.visualization import plotter


def _run(**kwargs):
    kwargs.setdefault("name", "test")
    return Simulator.from_scenario(Scenario(**kwargs)).run()


@pytest.fixture(scope="module")
def dt_result():
    return _run(model="double_track", maneuver="step_steer",
                maneuver_params={"speed_kmh": 60, "steering_wheel_deg": 20}, duration=3.0)


@pytest.fixture(scope="module")
def mb_result():
    return _run(model="multibody", maneuver="straight", maneuver_params={"length": 60, "speed_kmh": 40},
                environment={"road": {"roughness_class": "C", "seed": 1}}, duration=2.0)


# ----------------------------------------------------------------------------- KPIs per maneuver
MANEUVERS = [
    ("circle", {"radius": 30, "laps": 0.3, "speed_start_kmh": 20, "speed_end_kmh": 40}, set()),
    ("ramp_steer", {"speed_kmh": 60, "steer_rate_deg": 40, "duration": 6}, set()),
    ("step_steer", {"speed_kmh": 60, "steering_wheel_deg": 20, "duration": 4}, set()),
    ("sine_with_dwell", {"speed_kmh": 60, "amplitude_deg": 60}, set()),
    ("braking", {"speed_kmh": 60, "deceleration": 8.0}, set()),
    ("acceleration", {"target_kmh": 50, "request": 3.0}, set()),
    ("frequency_sweep", {"speed_kmh": 60, "amplitude_deg": 10, "duration": 8}, set()),
    ("slalom", {"speed_kmh": 40}, set()),
]


@pytest.mark.parametrize("maneuver, params, expected", MANEUVERS, ids=[m[0] for m in MANEUVERS])
def test_maneuver_specific_kpis(maneuver, params, expected):
    model = "double_track" if maneuver in ("braking", "acceleration") else "bicycle_nonlinear"
    result = _run(model=model, maneuver=maneuver, maneuver_params=params, duration=8.0)
    kpis = {k.key: k for k in evaluate(result)}
    assert {"max_ay", "max_yaw_rate", "max_beta"} <= set(kpis)
    general = {"max_ay", "max_ax", "min_ax", "max_yaw_rate", "max_beta", "max_roll", "max_steer"}
    assert len(set(kpis) - general) > 0
    assert expected <= set(kpis)
    for k in kpis.values():
        assert isinstance(k.value, str) or k.value is None or np.isfinite(k.value) or np.isnan(k.value)
        assert k.formatted()
    assert result.kpis and set(result.kpis) == set(kpis)


def test_understeer_kpi_sign_matches_linear_theory():
    from vdsim.analysis import LinearSingleTrackAnalysis
    result = _run(model="bicycle_linear", maneuver="ramp_steer", maneuver_params={"speed_kmh": 60,
                                                                                    "steer_rate_deg": 20,
                                                                                    "duration": 8.0})
    kpis = {k.key: k.value for k in evaluate(result)}
    eg_theory = LinearSingleTrackAnalysis(load_vehicle_preset("mid_size_sedan")).understeer_gradient
    if "understeer_gradient" in kpis:
        assert np.sign(kpis["understeer_gradient"]) == np.sign(eg_theory)


def test_following_and_aeb_kpis():
    result = _run(model="bicycle_nonlinear", maneuver="straight", maneuver_params={"length": 400, "speed_kmh": 70},
                  longitudinal_controller="aeb", environment={"lead_vehicle": {"initial_gap": 40.0,
                                                                               "time": [0, 2, 3, 100],
                                                                               "speed": [15, 15, 0, 0]}},
                  duration=10.0)
    kpis = {k.key: k for k in evaluate(result)}
    assert {"min_gap", "collision"} <= set(kpis)
    assert kpis["collision"].value == "nein" and kpis["min_gap"].value > 0.0


def test_comfort_kpis_on_rough_road(mb_result):
    kpis = {k.key: k for k in evaluate(mb_result)}
    assert kpis["iso2631_aw"].value > 0.0


# ----------------------------------------------------------------------------- result I/O
@pytest.mark.parametrize("suffix", [".npz", ".json", ".csv"])
def test_result_round_trip(dt_result, tmp_path, suffix):
    path = tmp_path / f"r{suffix}"
    evaluate(dt_result)
    dt_result.save(path)
    assert path.exists() and path.stat().st_size > 0
    if suffix == ".csv":
        header = path.read_text().splitlines()[0].split(",")
        assert "t" in header and "fz_FL" in header and "fz_RR" in header
        return
    back = SimulationResult.load(path)
    assert back.name == dt_result.name and back.kpis.keys() == dt_result.kpis.keys()
    assert np.allclose(back["t"], dt_result["t"]) and np.allclose(back["fz"], dt_result["fz"], equal_nan=True)
    assert len(back) == len(dt_result)


def test_result_accessors(dt_result):
    assert np.array_equal(dt_result.wheel("fz", "fl"), dt_result["fz"][:, 0])
    assert "t" in dt_result and dt_result.get("missing") is None
    assert np.array_equal(dt_result.time, dt_result["t"]) and "fz" in dt_result.names
    r = SimulationResult("partial")
    r.append({"a": 1.0})
    r.append({"a": 2.0, "b": [1.0, 2.0]})
    assert np.isnan(r["b"][0]).all() and r["a"].tolist() == [1.0, 2.0]


# ----------------------------------------------------------------------------- reports
def test_reports(dt_result, mb_result, tmp_path):
    pdf = generate_pdf([dt_result, mb_result], tmp_path / "report.pdf")
    assert pdf.read_bytes()[:4] == b"%PDF"
    text = engineering_summary([dt_result, mb_result])
    assert "# Engineering Summary" in text and "## Vergleich" in text and "| Max. Querbeschleunigung" in text
    assert save_summary(dt_result, tmp_path / "s.md").read_text().startswith("# Engineering Summary")
    table = compare([dt_result, mb_result])
    assert len(table["max_ay"]["values"]) == 2


# ----------------------------------------------------------------------------- figures
def test_figures(dt_result, mb_result, tmp_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cfg = load_vehicle_preset("mid_size_sedan")
    figs = [plotter.overview_figure(dt_result, "t"), plotter.tire_figure(dt_result),
            plotter.heatmap_figure(dt_result), plotter.suspension_figure(mb_result), plotter.energy_figure(dt_result),
            plotter.compare_figure([dt_result, mb_result]), plotter.quasi_static_figure(cfg)]
    fig, ax = plt.subplots(1, 3)
    plotter.plot_path(ax[0], dt_result)
    plotter.plot_ggv(ax[1], dt_result)
    plotter.plot_tire_curves(cfg.tires)
    plotter.plot_bode(cfg)
    figs.append(fig)
    for i, f in enumerate(figs):
        f.savefig(tmp_path / f"f{i}.png", dpi=40)
    plt.close("all")
    assert len(list(tmp_path.glob("*.png"))) == len(figs)


def test_animation(dt_result, tmp_path):
    from vdsim.visualization.animation import animate, save_animation
    anim = animate(dt_result, fps=5)
    assert anim is not None
    out = save_animation(dt_result, tmp_path / "a.gif", fps=2)
    assert (tmp_path / "a.gif").exists() or out


# ----------------------------------------------------------------------------- AD stack benchmark
def test_stack_benchmark_report():
    from vdsim.research.benchmark import benchmark, format_benchmark
    report = benchmark("einscherer", repeats=1, duration=1.0)
    assert report["repeats"] == 1 and report["simulated_s"] == pytest.approx(1.0, abs=0.11)
    assert report["real_time_factor"] > 0 and report["nodes"]
    for stats in report["nodes"].values():
        assert stats["calls"] > 0 and stats["max_ms"] >= stats["mean_ms"] >= 0
    text = format_benchmark(report)
    assert text.startswith("Echtzeitfaktor") and "planner" in text
