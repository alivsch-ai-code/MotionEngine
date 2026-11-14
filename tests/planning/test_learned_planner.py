"""Learned trajectory planner: the network proposes, the Werling planner verifies (vdsim.learning.trajectory)."""

import numpy as np
import pytest

from vdsim.learning.trajectory import (
    PLAN_FEATURES,
    PLAN_TARGETS,
    Situation,
    plan_label,
    planner_for,
    rollout,
    sample_plan_dataset,
    sample_situation,
)
from vdsim.planning.lateral import build_lateral_set
from vdsim.planning.sampling import SamplingParams, nearest, open_edges

OVERTAKE = {"road": [{"kind": "straight", "length": 500.0}], "ego": {"s": 10.0, "d": 0.0, "vx": 20.0},
            "target_speed": 20.0, "d_min": -1.75, "d_max": 5.25, "obstacles": [{"id": 1, "s": 70.0, "d": 0.0, "v": 4.0}]}


class Oracle:
    """Backend that returns the teacher's own choice for the current cycle."""

    def __init__(self, labels):
        self.labels, self.k = labels, 0

    def predict(self, x):
        self.k += 1
        return np.array([self.labels[self.k - 1]])


class Constant:
    def __init__(self, y):
        self.y = np.array([y], dtype=float)

    def predict(self, x):
        return self.y


def teacher_run(data, cycles):
    teacher, labels = planner_for(None), []
    log = rollout(teacher, Situation(data), cycles, on_cycle=lambda p, *_: labels.append(plan_label(p.plan)))
    return log, labels


def test_focus_keeps_a_subset_of_the_grid():
    grid = np.arange(-3.5, 3.6, 0.5)
    kept = nearest(grid, 1.1, 3, include=(0.0, -3.5, 0.123))
    assert sorted(kept) == [-3.5, 0.0, 0.5, 1.0, 1.5]                  # 3 nearest + included grid values only
    assert open_edges(grid, [0.5, 1.0, 1.5]) == (0.5, 1.5)
    assert open_edges(grid, [2.5, 3.0, 3.5]) == (2.5,)                 # 3.5 is the end of the grid

    class Start:
        s, d, d_d, d_dd, d_p, d_pp = 0.0, 0.3, 0.0, 0.0, 0.0, 0.0

    t_grid = np.arange(0.0, 5.01, 0.1)
    full = build_lateral_set(Start, "time", 0.05, 0.0, -5.25, 5.25, 0.9, SamplingParams(), t_grid)
    local = build_lateral_set(Start, "time", 0.05, 0.0, -5.25, 5.25, 0.9, SamplingParams(), t_grid, focus=(1.0, 2.0, 3, 2, (0.0,)))
    assert len(local) == 4 * 2 and len(full) > 100
    pairs = {(round(d, 6), round(t, 6)) for d, t in zip(full.delta, full.tau)}
    assert all((round(d, 6), round(t, 6)) in pairs for d, t in zip(local.delta, local.tau))
    assert local.open_edges["offset"] == (0.0, 1.5) and full.open_edges == {}


def test_without_a_model_it_is_the_werling_planner():
    from vdsim.framework import RunContext
    from vdsim.planning import create_planner

    plain = create_planner("default")
    plain.reset(RunContext(vehicle=planner_for(None).vehicle))
    a, b = rollout(planner_for(None), Situation(OVERTAKE), 6), rollout(plain, Situation(OVERTAKE), 6)
    assert a["cost"] == b["cost"] and a["x"] == b["x"] and set(a["source"]) == {"teacher"}


def test_a_perfect_proposal_reproduces_the_teacher():
    ref, labels = teacher_run(OVERTAKE, 12)
    assert all(y is not None for y in labels)
    learned = planner_for(Oracle(labels))
    log = rollout(learned, Situation(OVERTAKE), 12)
    assert learned.stats["network"] == 12 and learned.stats["teacher"] == 0
    assert log["cost"] == pytest.approx(ref["cost"], rel=1e-9) and log["x"] == pytest.approx(ref["x"], abs=1e-9)


@pytest.mark.parametrize("proposal", [(3.5, 0.5, -20.0, 0.5), (-3.5, 5.0, 4.0, 8.0), (np.nan, 1.0, 0.0, 1.0)])
def test_a_wrong_proposal_never_gives_a_worse_than_valid_result(proposal):
    # the proposal points at an invalid or poor region: the cycle must fall back to the complete search or use a
    # verified candidate - never an unchecked trajectory
    ref, _ = teacher_run(OVERTAKE, 10)
    learned = planner_for(Constant(proposal))
    log = rollout(learned, Situation(OVERTAKE), 10)
    assert all(log["valid"]) and not log["collision"]
    assert learned.stats["teacher"] + learned.stats["out_of_scope"] > 0
    if learned.stats["network"] == 0:                # every cycle solved by the teacher: identical drive
        assert log["x"] == pytest.approx(ref["x"], abs=1e-9)


def test_dataset_and_scope():
    x, y = sample_plan_dataset(40, seed=3, max_cycles=4)
    assert x.shape == (40, len(PLAN_FEATURES)) and y.shape == (40, len(PLAN_TARGETS))
    assert np.all(np.isfinite(x)) and np.all(y[:, 1] > 0) and np.all(y[:, 3] > 0)
    prev = PLAN_FEATURES.index("prev_present")
    assert 0 < x[:, prev].mean() < 1                # first cycles (no previous plan) and later ones
    # stop lines are outside the model's scope: such cycles use the teacher
    data = sample_situation(np.random.default_rng(1))
    sit = Situation(data)
    from vdsim.framework.types import LongitudinalMode

    learned = planner_for(Constant((0.0, 2.0, 0.0, 3.0)))
    beh = sit.behavior(0.0)
    beh.modes.append(LongitudinalMode("stopping", {"s_stop": 200.0}))
    learned.plan_cycle(0.0, sit.ego, beh, sit.prediction(0.0))
    assert learned.source == "out_of_scope"


def test_collision_check_of_the_evaluation_uses_the_outlines():
    from vdsim.learning.trajectory import _box, _overlap

    ego = _box(0.0, 0.0, 0.0, 4.8, 1.9)
    assert _overlap(ego, _box(4.0, 0.0, 0.0, 4.5, 1.8))                 # 0.65 m overlap in length
    assert not _overlap(ego, _box(4.8, 0.0, 0.0, 4.5, 1.8))             # 0.15 m gap
    assert not _overlap(ego, _box(0.0, 2.0, 0.0, 4.5, 1.8))             # side by side, 0.15 m gap
    assert _overlap(ego, _box(3.0, 1.5, 0.8, 4.5, 1.8))                 # turned into the ego's corner
