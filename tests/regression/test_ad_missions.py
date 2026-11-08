"""System tests: the AD stack (perception -> prediction -> behavior -> Werling planner -> controller -> plant)
must fulfil the success criteria of every library scenario (configs/ad_scenarios, scenario seeds).

The criteria (no_collision, stay_on_road, reach_goal, final_lane, parked, ...) are evaluated by
vdsim.ad.runner._evaluate_mission into result.metadata["mission"]; before this review they were
defined but never checked.
"""

import pytest

from vdsim.ad import run_scenario
from vdsim.planning.collision import circle_cover, circles_needed
from vdsim.world import list_ad_scenarios

KNOWN_FAILURES = {
    # Werling velocity mode at v_ref = 1 m/s: the sampled standstill candidate (k_nu nu^2 / 2 = 10) is cheaper
    # than accelerating to v_ref (k_tau tau ~ 11) in every cycle, so the vehicle stays beside the gap.
    # Root cause and options: docs/review/2026-11-08-full-review.md, finding F2.
    "laengsparken_rueckwaerts": "standstill local optimum in the reverse phase (review finding F2)",
}
SCENARIOS = [s["name"] for s in list_ad_scenarios()]


def _mission(name, **kw):
    res = run_scenario(name, record_snapshots=False, **kw)
    return res, res.metadata.get("mission") or {}


@pytest.mark.integration
def test_merge_between_trucks_is_collision_free():
    # regression: trucks (16.5 m x 2.5 m) were covered by 5 circles of radius 2.07 m, so a truck in the
    # adjacent lane collided with every candidate of the acceleration lane; the planner fell back and the
    # fallback steered in front of the faster rear truck (collision at t = 2.5 s for every seed)
    res, mission = _mission("einfaedeln_lkw", duration=12.0)
    assert res.metadata["stop_reason"] != "Kollision", res.metadata.get("collision_with")
    assert mission["criteria"]["no_collision"]["ok"] and mission["criteria"]["stay_on_road"]["ok"]


def test_circle_cover_bounds_lateral_inflation():
    for length, width in ((16.5, 2.5), (12.0, 2.55), (4.5, 1.8), (4.8, 1.85), (0.6, 0.6)):
        n = circles_needed(length, width, 0.3)
        _, r = circle_cover(length, width, n)
        assert r - 0.5 * width <= 0.3 + 1e-9
        # truck in the adjacent 3.75 m lane, sedan ego with 3 circles and the 0.7 m truck margin: no overlap
    _, r_truck = circle_cover(16.5, 2.5, circles_needed(16.5, 2.5, 0.3))
    _, r_ego = circle_cover(4.8, 1.85, 3)
    assert r_truck + r_ego + 0.7 < 3.75


@pytest.mark.slow
@pytest.mark.parametrize("name", SCENARIOS)
def test_library_scenario_mission(name):
    if name in KNOWN_FAILURES:
        pytest.xfail(KNOWN_FAILURES[name])
    res, mission = _mission(name)
    failed = {k: v["detail"] for k, v in mission.get("criteria", {}).items() if not v["ok"]}
    assert mission.get("passed"), failed
