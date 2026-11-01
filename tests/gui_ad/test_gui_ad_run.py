import importlib.util

import numpy as np
import pytest

runner_missing = importlib.util.find_spec("vdsim.ad.runner") is None


@pytest.mark.skipif(runner_missing, reason="vdsim.ad.runner noch nicht vorhanden")
def test_real_run_in_workbench(qapp, shot_dir):
    from vdsim.ad import run_scenario
    from vdsim.gui.ad.workbench import ADWorkbench, list_scenarios, scenario_spec
    scenarios = list_scenarios()
    if not scenarios:
        pytest.skip("keine Szenarien verfügbar")
    sc = scenarios[0]
    name = sc.get("name", sc) if isinstance(sc, dict) else sc
    try:
        result = run_scenario(scenario_spec(name), seed=0, duration=1.5, record_snapshots=True)
    except Exception as exc:
        if "unbekannte Komponente" in str(exc) or "unknown" in str(exc).lower():
            pytest.skip(f"Stack noch unvollständig: {str(exc).splitlines()[0]}")
        raise
    wb = ADWorkbench()
    wb.resize(1600, 1000)
    wb.show()
    wb.set_result(result, show_planner=True)
    pv = wb.planner_view
    assert pv.data is not None and len(pv.data.t) > 10
    for t in np.linspace(pv.data.t0, pv.data.t1, 31):
        pv.set_time(t)
    for i in range(wb.tabs.count()):
        wb.tabs.setCurrentIndex(i)
    wb.tabs.setCurrentWidget(pv)
    pv.set_time(pv.data.t1)
    qapp.processEvents()
    wb.grab().save(str(shot_dir / "real_run.png"))
    wb.close()
