import json
from pathlib import Path

import numpy as np
import pytest

from PySide6 import QtCore


@pytest.mark.parametrize("kind", ["compare", "sweep", "monte_carlo", "batch"])
def test_research_panel_synthetic_batch(qapp, kind, tmp_path, shot_dir):
    from vdsim.gui.ad.demo import make_demo_batch
    from vdsim.gui.ad.research_panel import ResearchPanel
    batch = make_demo_batch(kind, save_dir=tmp_path)
    rp = ResearchPanel()
    rp.resize(1500, 900)
    rp.show()
    rp.set_batch(batch)
    assert rp.kind == kind
    assert rp.table.rowCount() == len(batch)
    n_params = {"sweep": 2, "monte_carlo": 2}.get(kind, 0)
    assert rp.table.columnCount() == 2 + n_params + len(batch.kpi_keys())
    assert rp.cmp_kpi.count() == len(batch.kpi_keys())
    if kind == "sweep":
        img = rp.sweep_img.image
        assert img is not None and img.shape == (5, 4)
        assert len(rp.sweep_texts) == 20
    if kind == "monte_carlo":
        assert rp.mc_stats.rowCount() >= 8
        assert "Kollisionsrate" in rp.mc_rate.text()
    assert rp.cost_items, "stacked cost bars expected"
    assert rp.bench_table.rowCount() > 0
    for group in rp.groups.values():
        assert group.plots
    for i in range(rp.tabs.count()):
        rp.tabs.setCurrentIndex(i)
        qapp.processEvents()
        rp.grab().save(str(shot_dir / f"research_{kind}_{i}.png"))
    # every KPI selectable in all dashboards
    for k in range(rp.cmp_kpi.count()):
        rp.cmp_kpi.setCurrentIndex(k)
        rp.mc_kpi.setCurrentIndex(k)
        rp.sweep_kpi.setCurrentIndex(k)
    # export
    csv = rp.export_csv(str(tmp_path / "exp.csv"))
    js = rp.export_json(str(tmp_path / "exp.json"))
    assert Path(csv).read_text(encoding="utf-8").startswith("label;")
    assert len(json.loads(Path(js).read_text(encoding="utf-8"))) == len(batch)
    # click on a saved run loads it
    loaded = []
    rp.result_loaded.connect(loaded.append)
    row = next(r for r in range(rp.table.rowCount())
               if batch.records[rp.table.item(r, 0).data(QtCore.Qt.UserRole)].get("path"))
    res = rp.load_run(row)
    assert res is not None and loaded and len(loaded[0].snapshots) > 0
    other = next(r for r in range(rp.table.rowCount()) if r != row)
    assert rp.load_run(other) is None and "nicht gespeichert" in rp.status.text()


def test_research_panel_benchmark_report(qapp):
    from vdsim.gui.ad.research_panel import ResearchPanel
    rp = ResearchPanel()
    rp.set_benchmark({"repeats": 2, "wall_time_s": 1.0, "simulated_s": 10.0, "real_time_factor": 10.0,
                      "nodes": {"planner": {"mean_ms": 8.0, "p95_ms": 12.0, "max_ms": 20.0, "calls": 100,
                                            "total_s": 0.8},
                                "controller": {"mean_ms": 0.2, "p95_ms": 0.3, "max_ms": 1.0, "calls": 1000,
                                               "total_s": 0.2}},
                      "planner_cycle_ms": {"mean": 8.0, "p95": 12.0, "max": 20.0, "n": 100}})
    assert rp.bench_table.rowCount() == 2
    assert "Echtzeitfaktor 10.00" in rp.bench_info.text()


def test_build_jobs_for_all_experiments(qapp, tmp_path):
    from vdsim.gui.ad.research_panel import ResearchPanel, parse_values, safe_label
    assert parse_values("0.5, 1, 2") == [0.5, 1, 2]
    assert parse_values("0:1:3") == [0.0, 0.5, 1.0]
    assert "." not in safe_label("k=0.5") and "/" not in safe_label("a/b")
    rp = ResearchPanel()
    rp.job_provider = lambda: {"stack": {"controller": {"component": "tracking_controller/x"}}}
    f = rp.form
    f.scenario.setEditText("highway_cut_in")
    f.save_dir.setText(str(tmp_path))
    kinds = {f.kind.itemData(i): i for i in range(f.kind.count())}
    # controller comparison: checked components (+ a manual spec)
    f.kind.setCurrentIndex(kinds["compare_controller"])
    f.ctrl_list["extra"].setText("tracking_controller/custom")
    f.ctrl_list["add"]()
    jobs = rp.build_jobs()
    assert jobs and all(j["scenario"] == "highway_cut_in" and "save_dir" in j for j in jobs)
    assert jobs[-1]["stack"]["controller"]["component"] == "tracking_controller/custom"
    assert len({j["label"] for j in jobs}) == len(jobs)
    # sweep with two parameters
    f.kind.setCurrentIndex(kinds["sweep"])
    f.sweep_values[0].setText("0.5, 1")
    f.sweep_second.setChecked(True)
    f.sweep_values[1].setText("1:3:3")
    jobs = rp.build_jobs()
    assert len(jobs) == 6
    assert jobs[0]["stack"]["planner"]["params"]["cost"]["k_jerk"] == 0.5
    assert all("." not in j["label"] for j in jobs)
    # Monte Carlo
    f.kind.setCurrentIndex(kinds["monte_carlo"])
    f.mc_n.setValue(7)
    jobs = rp.build_jobs()
    assert len(jobs) == 7 and "cut_in_gap" in jobs[0]["scenario_params"]
    assert 8 <= jobs[0]["scenario_params"]["cut_in_gap"] <= 30
    # batch over scenarios with two seeds
    f.kind.setCurrentIndex(kinds["batch"])
    f.batch_extra.setText("a, b")
    f.batch_seeds.setValue(2)
    f.save_runs.setChecked(False)
    jobs = rp.build_jobs()
    assert [j["scenario"] for j in jobs][-4:] == ["a", "a", "b", "b"]
    assert all(j["snapshots"] is False for j in jobs)


def test_research_result_opens_in_planner_view(qapp, tmp_path):
    from vdsim.gui.ad.demo import make_demo_batch
    from vdsim.gui.ad.workbench import ADWorkbench
    wb = ADWorkbench()
    rp = wb.tab_widgets["vdsim.gui.ad.research_panel:ResearchPanel"]
    assert rp.job_provider is not None
    rp.set_batch(make_demo_batch("compare", save_dir=tmp_path))
    row = next(r for r in range(rp.table.rowCount()) if rp.batch.records[r].get("path"))
    rp.load_run(row)
    assert wb.result is not None and wb.tabs.currentWidget() is wb.planner_view
    assert wb.planner_view.data is not None
    wb.close()


def test_research_runs_batch_in_thread(qapp, monkeypatch):
    # run_batch replaced by a synthetic batch: checks the thread wiring and the progress bar
    import vdsim.gui.ad.research_panel as mod
    from vdsim.gui.ad.demo import make_demo_batch

    def fake(jobs, workers=0, progress=None):
        for i in range(len(jobs)):
            progress(i + 1, len(jobs))
        return make_demo_batch("sweep")
    monkeypatch.setattr(mod, "_run_batch", fake)
    rp = mod.ResearchPanel()
    rp.form.scenario.setEditText("x")
    rp.form.kind.setCurrentIndex(2)
    rp.form.save_runs.setChecked(False)
    rp.start()
    assert rp.wait(20000)
    assert rp.batch is not None and rp.kind == "sweep"
    assert rp.progress.value() == rp.progress.maximum()
    assert np.isfinite(rp.batch.column("rms_e_n")).all()
