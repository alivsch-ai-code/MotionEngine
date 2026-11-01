import numpy as np
import pytest
from PySide6 import QtCore, QtWidgets


def _process(app, ms=0):
    timer = QtCore.QElapsedTimer()
    timer.start()
    app.processEvents()
    while timer.elapsed() < ms:
        app.processEvents(QtCore.QEventLoop.AllEvents, 20)
        QtCore.QThread.msleep(5)


def test_workbench_demo_timeline_and_tabs(qapp, demo_result, shot_dir):
    from vdsim.gui.ad.workbench import TABS, ADWorkbench
    wb = ADWorkbench()
    wb.resize(1600, 1000)
    wb.show()
    assert wb.tabs.count() == len(TABS)
    # missing modules of other agents appear as placeholder tabs, never as an exception
    assert set(wb.tab_errors) <= set(TABS)
    wb.set_result(demo_result, show_planner=True)
    pv = wb.planner_view
    assert pv.data is not None and pv.stack.currentIndex() == 1
    tl = pv.timeline
    assert tl.t0 == pytest.approx(0.0) and tl.t1 == pytest.approx(12.0)
    for t in np.linspace(0, 12, 61):
        tl.set_time(t)
    assert pv.info.labels["t"].text() == "12.00 s"
    tl.set_time(0.0)
    tl.step(1)
    assert tl.current_time == pytest.approx(0.1)
    tl.jump_event(1)
    assert tl.current_time == pytest.approx(1.5)
    tl.event_filter.setCurrentIndex(tl.event_filter.findData("reinit"))
    tl.jump_event(1)
    assert tl.current_time == pytest.approx(4.0)
    assert "Reinitialisierung" in pv.info.status.text()
    tl.jump_event(-1)          # no earlier reinit -> stays
    assert tl.current_time == pytest.approx(4.0)
    tl.speed.setCurrentIndex(tl.speed.count() - 1)
    tl.play()
    _process(qapp, 300)
    tl.pause()
    assert tl.current_time > 4.5
    pv.top.set_follow(False)
    pv.top.set_layer_visible("candidates", False)
    pv.top.set_layer_visible("candidates", True)
    pv.set_time(3.1)
    assert "Fallback" in pv.info.status.text()
    # all tabs and sub tabs
    for i in range(wb.tabs.count()):
        wb.tabs.setCurrentIndex(i)
        _process(qapp)
        wb.grab().save(str(shot_dir / f"workbench_tab{i}.png"))
    wb.tabs.setCurrentWidget(pv)
    for tabs in (pv.analysis_tabs, pv.scope_tabs):
        for i in range(tabs.count()):
            tabs.setCurrentIndex(i)
            pv.set_time(4.0 + i)
            _process(qapp)
            wb.grab().save(str(shot_dir / f"planner_{tabs.tabText(i).replace('&', '')}.png"))
    print("screenshots:", shot_dir)
    wb.close()


def test_run_overview_event_jump(qapp, demo_result):
    from vdsim.gui.ad.workbench import ADWorkbench
    wb = ADWorkbench()
    wb.set_result(demo_result)
    ov = wb.tab_widgets["vdsim.gui.ad.run_overview:RunOverview"]
    assert ov.kpi_table.rowCount() > 10
    assert ov.event_table.rowCount() == len(demo_result.events)
    ov._event_clicked(2)
    assert wb.planner_view.current_time == pytest.approx(demo_result.events[2]["t"])
    wb.close()


def test_planner_view_tolerates_missing_fields(qapp):
    from vdsim.ad.results import ADResult
    from vdsim.gui.ad.planner_view import PlannerView
    pv = PlannerView()
    pv.resize(1200, 800)
    pv.set_result(None)
    # only a few signals, sparse snapshots, no road / objects / metadata
    res = ADResult("minimal")
    t = np.arange(0, 2.0, 0.01)
    res._signals = {"t": t, "ego_x": 10 * t, "ego_y": np.zeros_like(t), "cmd_steer_angle": np.full(len(t), np.nan)}
    res.snapshots = [{"t": 0.0}, {"t": 0.5, "candidates_x": np.zeros((0, 0), np.float32), "best_index": 3},
                     {"t": 1.0, "candidates_x": np.ones((3, 5), np.float32), "candidates_y": np.ones((3, 5), np.float32),
                      "candidates_cost": np.array([1.0, 2.0, np.nan]), "trajectory": {"x": np.arange(5.0)},
                      "prediction": [{"id": 1, "x": [1.0], "y": [2.0]}], "controller": {"horizon_x": None},
                      "modes": {"velocity": {"cost": 1.0}}, "collision_circles": {"margin": 0.2}}]
    res.events = [{"t": 1.0, "type": "unknown_kind"}, {"type": "no_time"}]
    pv.set_result(res)
    for tt in np.linspace(0, 2, 21):
        pv.set_time(tt)
    # snapshots only (no signals)
    res2 = ADResult("snaps_only")
    res2.snapshots = [{"t": 0.0}, {"t": 0.1, "mode": "velocity"}]
    pv.set_result(res2)
    pv.set_time(0.1)
    assert pv.info.labels["mode"].text() == "velocity"
    # completely empty result
    pv.set_result(ADResult("empty"))
    pv.set_time(0.0)


def test_save_and_load_result(qapp, demo_result, tmp_path):
    from vdsim.gui.ad.workbench import ADWorkbench
    wb = ADWorkbench()
    assert wb.save_result(str(tmp_path / "x.npz")) is None      # nothing to save yet
    wb.set_result(demo_result)
    out = wb.save_result(str(tmp_path / "run.npz"))
    assert out.exists()
    loaded = wb.load_result(str(out))
    assert loaded is not None and len(loaded.snapshots) == len(demo_result.snapshots)
    wb.planner_view.set_time(4.0)
    assert wb.planner_view.current_snapshot()["t"] == pytest.approx(4.0)
    wb.close()


def test_simulation_thread_progress_failure_cancel(qapp, demo_result):
    from vdsim.gui.ad.workbench import ADWorkbench
    calls = {}

    def fake_run(progress=None, **kwargs):
        calls.update(kwargs)
        for k in range(5):
            progress(k * 1.0, 4.0)
        return demo_result

    wb = ADWorkbench(run_function=fake_run)
    wb.seed.setValue(7)
    wb.start_simulation()
    assert wb.wait_for_simulation(20000)
    assert wb.result is demo_result
    assert calls["seed"] == 7 and calls["record_snapshots"] is True and "controller" in calls["stack"]

    def failing(progress=None, **kwargs):
        raise RuntimeError("kaputt")
    wb.run_function = failing
    wb.start_simulation()
    assert wb.wait_for_simulation(20000)
    assert "kaputt" in wb.statusBar().currentMessage()

    def slow(progress=None, **kwargs):
        for k in range(2000):
            progress(k * 0.01, 20.0)
            QtCore.QThread.msleep(1)
        return demo_result
    wb.run_function = slow
    wb.set_result(None)
    wb.start_simulation()
    wb.cancel_simulation()
    assert wb.wait_for_simulation(20000)
    assert wb.result is None and "abgebrochen" in wb.statusBar().currentMessage()
    wb.close()


def test_demo_scenario_runs_without_runner(qapp):
    from vdsim.gui.ad.workbench import DEMO_SCENARIO, ADWorkbench
    wb = ADWorkbench()
    wb.scenario.setCurrentIndex(wb.scenario.findData(DEMO_SCENARIO))
    wb.duration.setValue(6.0)
    wb.start_simulation()
    assert wb.wait_for_simulation(30000)
    assert wb.result is not None and wb.result.duration == pytest.approx(6.0)
    wb.close()


def test_stack_selection_and_param_dialog(qapp):
    from vdsim.gui.ad.workbench import LAYER_KINDS, ADWorkbench, ParamDialog
    wb = ADWorkbench()
    stack = wb.current_stack()
    assert set(stack) <= set(LAYER_KINDS)
    for layer in wb.layer_combos:
        dlg = wb.open_param_dialog(layer, exec_dialog=False)
        assert isinstance(dlg, ParamDialog)
        dlg.values()
        dlg.deleteLater()
    combo = wb.layer_combos["controller"]
    if combo.count() > 1:
        wb.stack_params["controller"] = {"k": 1.0}
        combo.setCurrentIndex((combo.currentIndex() + 1) % combo.count())
        assert wb.current_stack()["controller"]["component"] == combo.currentData()
        assert "params" not in wb.current_stack()["controller"]
    wb.apply_stack({"planner": {"component": "trajectory_planner/werling", "params": {"cost": {"k_j": 2.0}}}})
    assert wb.current_stack()["planner"]["params"] == {"cost": {"k_j": 2.0}}
    job = wb.current_job()
    assert set(job) == {"scenario", "stack", "seed", "duration"}
    # synthetic schema with nested group, choices, list and limits
    schema = [{"name": "k_n", "default": 1.5, "label": "Verstärkung", "unit": "1/m", "min": 0, "max": 10},
              {"name": "mode", "default": "a", "choices": ["a", "b"]},
              {"name": "n", "default": 3}, {"name": "flag", "default": False},
              {"name": "times", "default": [1.0, 2.0]},
              {"name": "cost", "default": {"k_j": 1.0, "k_t": 0.5}}]
    dlg = ParamDialog("test", schema, {"cost": {"k_t": 0.7}})
    assert dlg.values() == {"cost": {"k_t": 0.7}}
    dlg.root.child("k_n").setValue(2.0)
    dlg.root.child("times").setValue("1, 2, 3")
    assert dlg.values() == {"k_n": 2.0, "times": [1.0, 2.0, 3.0], "cost": {"k_t": 0.7}}
    dlg.restore_defaults()
    assert dlg.values() == {}
    wb.close()


def test_tab_registry_placeholder(qapp):
    from vdsim.gui.ad.workbench import ADWorkbench, load_tab
    widget, title, err = load_tab("vdsim.gui.ad.does_not_exist:Nothing")
    assert err and isinstance(widget, QtWidgets.QLabel)
    wb = ADWorkbench(tabs=["vdsim.gui.ad.planner_view:PlannerView", "vdsim.gui.ad.does_not_exist:Nothing"])
    assert wb.tabs.count() == 2 and len(wb.tab_errors) == 1
    wb.load_demo()
    wb.close()


def test_main_entry_point_importable():
    import vdsim.gui.ad as pkg
    assert callable(pkg.main)
    assert pkg.TABS[0].endswith(":PlannerView")
