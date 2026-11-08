"""Experiment design (sweep, Monte Carlo, comparisons) and batch result statistics."""

import json

import numpy as np
import pytest

from vdsim.research.experiments import (
    _sample,
    compare_controllers,
    compare_planners,
    get_path,
    monte_carlo,
    parameter_sweep,
    run_batch,
    set_path,
)

BASE = {"scenario": "einscherer", "duration": 0.4}


def test_paths():
    job = set_path({}, "stack.planner.params.k", 2.0)
    assert get_path(job, "stack.planner.params.k") == 2.0 and get_path(job, "stack.x.y", "d") == "d"


def test_distributions_are_reproducible_and_bounded():
    rng = np.random.default_rng(0)
    assert 1.0 <= _sample({"dist": "uniform", "low": 1.0, "high": 2.0}, rng) <= 2.0
    assert -1.0 <= _sample({"dist": "normal", "mean": 0.0, "std": 5.0, "low": -1.0, "high": 1.0}, rng) <= 1.0
    assert _sample({"dist": "lognormal", "mean": 0.0, "sigma": 0.1}, rng) > 0.0
    assert _sample({"dist": "choice", "values": ["a", "b"]}, rng) in ("a", "b")
    assert _sample({"dist": "integer", "low": 3, "high": 3}, rng) == 3
    with pytest.raises(ValueError):
        _sample({"dist": "cauchy"}, rng)
    dist = {"stack.planner.params.timing.t_comp": {"dist": "uniform", "low": 0.02, "high": 0.08}}
    a, b = monte_carlo(BASE, dist, 5, seed=3), monte_carlo(BASE, dist, 5, seed=3)
    assert [j["sample"] for j in a] == [j["sample"] for j in b] and len({j["seed"] for j in a}) > 1


def test_sweep_and_comparisons_build_jobs():
    jobs = parameter_sweep(BASE, {"seed": [1, 2], "duration": [0.2, 0.3]})
    assert len(jobs) == 4 and {(j["seed"], j["duration"]) for j in jobs} == {(1, 0.2), (1, 0.3), (2, 0.2), (2, 0.3)}
    assert all(j["label"] for j in jobs)
    ctrl = compare_controllers(BASE, {"Stanley": "tracking_controller/stanley",
                                      "PP": {"component": "tracking_controller/pure_pursuit"}})
    assert [j["label"] for j in ctrl] == ["Stanley", "PP"]
    assert ctrl[0]["stack"]["controller"] == {"component": "tracking_controller/stanley"}
    assert compare_planners(BASE, {"W": "trajectory_planner/werling"})[0]["stack"]["planner"]["component"]


def test_batch_statistics_and_exports(tmp_path):
    jobs = parameter_sweep(BASE, {"seed": [1, 2]}) + [{"scenario": "does_not_exist", "label": "bad"}]
    batch = run_batch(jobs, workers=0, progress=lambda i, n: None)
    assert len(batch) == 3 and len(batch.ok) == 2 and len(batch.failed) == 1
    keys = batch.kpi_keys
    assert keys
    stats = batch.statistics()
    key = next(iter(stats))
    assert {"mean", "std", "min", "max"} <= set(stats[key])
    table = batch.table()
    assert table[key]["labels"] == ["seed=1", "seed=2", "bad"] and len(batch.column(key)) == 3
    assert batch.best(key) is not None
    batch.to_json(tmp_path / "b.json")
    batch.to_csv(tmp_path / "b.csv")
    assert json.loads((tmp_path / "b.json").read_text())
    assert (tmp_path / "b.csv").read_text().count("\n") >= 3
    sens = batch.sensitivity(key)
    assert isinstance(sens, dict)


def test_batch_in_process_pool():
    batch = run_batch(parameter_sweep(BASE, {"seed": [1, 2]}), workers=2)
    assert [r["ok"] for r in batch.records] == [True, True]
