import numpy as np

from vdsim.framework import RunContext, create_component
from vdsim.framework.types import EgoState, ObjectState, WorldState


def _world():
    objs = [ObjectState(id=1, x=50.0, y=0.0), ObjectState(id=2, x=-30.0, y=0.0), ObjectState(id=3, x=200.0, y=0.0),
            ObjectState(id=4, x=80.0, y=0.3, length=4.5, width=1.8), ObjectState(id=5, x=20.0, y=40.0)]
    return WorldState(t=0.0, objects=objs)


def _run(params, seed=1, steps=5):
    comp = create_component("perception/object_sensor", params)
    comp.reset(RunContext(seed=seed))
    out = []
    for k in range(steps):
        r = comp.step(0.1 * k, {"world": _world(), "ego": EgoState()})
        out.append([(o.id, o.x, o.y, o.v) for o in r["objects"].objects])
    return out


def test_reproducible_with_seed():
    p = {"pos_sigma": 0.3, "vel_sigma": 0.2, "azimuth_sigma_deg": 0.5, "detection_probability": 0.8}
    assert _run(p, seed=4) == _run(p, seed=4)
    assert _run(p, seed=4) != _run(p, seed=5)


def test_range_and_field_of_view():
    ids = {o[0] for o in _run({"range": 120.0, "fov_deg": 60.0}, steps=1)[0]}
    assert ids == {1, 4}                       # 2 behind, 3 too far, 5 outside the 60° cone
    ids = {o[0] for o in _run({"range": 250.0, "fov_deg": 360.0}, steps=1)[0]}
    assert ids == {1, 2, 3, 4, 5}


def test_occlusion_and_latency():
    ids = {o[0] for o in _run({"occlusion": True}, steps=1)[0]}
    assert 4 not in ids and 3 not in ids and 1 in ids          # hidden behind object 1
    comp = create_component("perception/object_sensor", {"latency": 0.3, "cycle_time": 0.1})
    comp.reset(RunContext())
    ts = [comp.step(0.1 * k, {"world": WorldState(t=0.1 * k, objects=[]), "ego": EgoState()})["objects"].t
          for k in range(8)]
    assert np.isclose(ts[-1], 0.4)


def test_ground_truth_passthrough():
    comp = create_component("perception/ground_truth")
    comp.reset(RunContext())
    r = comp.step(0.0, {"world": _world(), "ego": EgoState(x=1.0)})
    assert [o.id for o in r["objects"].objects] == [1, 2, 3, 4, 5] and r["ego_estimate"].x == 1.0
