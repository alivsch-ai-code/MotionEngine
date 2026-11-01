import time

import pytest


def test_lane_change_study_regression():
    # results of the original latency study (run_lane_change.py) must not change
    import run_lane_change as r
    from lane_change.latency import LATENCY_CASES
    from lane_change.simulation import simulate

    ideal = simulate(r.V, r.k_des, r.ideal_steering, LATENCY_CASES["none"], r.T_END, r.DT)
    uncorrected = simulate(r.V, r.k_des, r.distorted_steering, LATENCY_CASES["system"], r.T_END, r.DT, False, r.YAW_RATE_NOISE)
    corrected = simulate(r.V, r.k_des, r.distorted_steering, LATENCY_CASES["system"], r.T_END, r.DT, True, r.YAW_RATE_NOISE)
    assert ideal["y"][-1] == pytest.approx(3.500, abs=5e-4)
    assert uncorrected["y"][-1] == pytest.approx(3.849, abs=5e-4)
    assert corrected["y"][-1] == pytest.approx(3.627, abs=5e-4)
    assert corrected["error_factor_est"][-1] == pytest.approx(1.088, abs=5e-4)


def test_gui_smoke():
    pytest.importorskip("PySide6")
    pytest.importorskip("pyqtgraph")
    from PySide6 import QtWidgets
    from vdsim.gui.main_window import MainWindow
    from vdsim.gui.theme import apply_theme

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    apply_theme(app)
    window = MainWindow()
    window.show()
    library = window.scenario_panel.library
    library.setCurrentIndex(library.findData("spurwechsel_latenzkette"))
    window.scenario_panel._load_selected()
    window.start_simulation()
    start = time.time()
    while window.timer.isActive() and time.time() - start < 60:
        app.processEvents()
    assert window.sim.finished
    assert window.kpi.table.rowCount() > 10
    assert len(window.compare.results) == 1
    for i in range(window.analysis.kind.count()):
        window.analysis.kind.setCurrentIndex(i)
        app.processEvents()
    window.close()
