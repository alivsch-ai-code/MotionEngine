"""Closed loop world -> perception -> prediction -> behavior with the kinematic ego stand-in.

For tests and examples of the behavior layer without trajectory planner and controller
(vdsim.world.ego_stub.KinematicEgoStub moves the ego along the commanded reference line).
"""

from __future__ import annotations

from ..core.parameters import load_vehicle_preset
from ..framework.context import RunContext
from ..framework.plugins import create_component
from ..world.ego_stub import KinematicEgoStub
from ..world.scenario import build_scenario


def run_closed_loop(scenario, duration=None, dt=0.1, seed=None, behavior_params=None,
                    perception="perception/ground_truth", perception_params=None,
                    predictor="predictor/constant_acceleration", stop_on_collision=False):
    # returns a list of dicts {t, ego, behavior, world, objects}
    inst = build_scenario(scenario, seed=seed) if not hasattr(scenario, "road") else scenario
    vehicle = load_vehicle_preset(inst.vehicle)
    ctx = RunContext(dt=dt, seed=inst.seed, vehicle=vehicle, road=inst.road, scenario=inst)
    world = create_component("world/scenario_engine")
    per = create_component(perception, perception_params)
    pred = create_component(predictor)
    beh = create_component("behavior_planner/rule_based", behavior_params)
    for c in (world, per, pred, beh):
        c.reset(ctx)
    v = vehicle.vehicle
    oh = max(v.length - v.wheelbase, 0.0) / 2
    ego = KinematicEgoStub.from_initial(inst.ego_initial, length=v.length, width=v.width,
                                        front_extent=v.cg_to_front + oh)
    hist = []
    n = int(round((duration or inst.duration) / dt))
    cmd = None
    for k in range(n):
        t = k * dt
        es = ego.state()
        es.t = t
        w = world.step(t, {"ego": es})["world"]
        o = per.step(t, {"world": w, "ego": es})
        pr = pred.step(t, {"objects": o["objects"], "world": w})["prediction"]
        cmd = beh.step(t, {"ego": o["ego_estimate"], "objects": o["objects"], "prediction": pr, "world": w,
                           "trajectory": None})["behavior"]
        hist.append({"t": t, "ego": es, "behavior": cmd, "world": w, "objects": o["objects"]})
        if stop_on_collision and w.collision:
            break
        ego.step(t, dt, cmd, o["objects"])
    return hist
