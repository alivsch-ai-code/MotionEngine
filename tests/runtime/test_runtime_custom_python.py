"""Python custom nodes: loader, hot reload with state transfer, error handling, examples, scaffolding."""

import os
import time
from pathlib import Path

import numpy as np
import pytest

from vdsim.framework.layers import LAYER_BASES
from vdsim.framework.plugins import create_component
from vdsim.runtime import Executor, Graph, create_custom_node

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "examples" / "custom_nodes" / "python"

NODE_V1 = '''
from dataclasses import dataclass
from vdsim.core.parameters import param
from vdsim.framework.component import Component, Port


@dataclass
class P:
    k: float = param(1.0, "", "k")


class Acc(Component):
    KIND, NAME, VERSION = "node", "acc", "1.0.0"
    INPUTS = {"u": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = P

    def reset(self, context):
        super().reset(context)
        self.total = 0.0

    def step(self, t, inputs):
        self.total += self.params.k * inputs["u"]
        return {"y": self.total}
'''


def _write(path, text):
    # make sure the mtime changes even on coarse file systems
    old = path.stat().st_mtime_ns if path.exists() else 0
    path.write_text(text, encoding="utf-8")
    if path.stat().st_mtime_ns == old:
        os.utime(path, ns=(old + 1_000_000, old + 1_000_000))


def _graph(path):
    g = Graph("hot", base_dt=0.1)
    g.add_node("c", "node/constant", params={"value": 1.0})
    g.add_node("acc", f"python:{path.as_posix()}:Acc", params={"k": 2.0})
    g.connect("c.y", "acc.u")
    return g


def test_python_loader_and_hot_reload_with_state_transfer(tmp_path):
    src = tmp_path / "acc.py"
    _write(src, NODE_V1)
    g = _graph(src)
    ex = Executor(g)
    ex.run(0.4)                                            # 5 steps: total = 10
    assert ex.value("acc.y") == 10.0
    assert ex.check_reload() == []                         # unchanged
    _write(src, NODE_V1.replace("self.total += self.params.k * inputs[\"u\"]",
                                "self.total += 100 * self.params.k * inputs[\"u\"]"))
    events = ex.check_reload()
    assert len(events) == 1 and events[0].ok and not events[0].ports_changed, events
    new = g.instance("acc")
    assert new.total == 10.0 and new.params.k == 2.0       # state and parameters transferred
    ex.run(0.5)
    assert ex.value("acc.y") == 210.0
    assert ex.recorder.events_of("reload")[0].node == "acc"


def test_hot_reload_error_keeps_old_instance(tmp_path):
    src = tmp_path / "acc.py"
    _write(src, NODE_V1)
    g = _graph(src)
    ex = Executor(g)
    ex.run(0.1)
    old = g.instance("acc")
    _write(src, NODE_V1 + "\n    def broken(:\n")
    ev = ex.check_reload()
    assert len(ev) == 1 and not ev[0].ok and "SyntaxError" in ev[0].message and "bisherige Version" in ev[0].message
    assert g.instance("acc") is old
    assert ex.check_reload() == []                         # the broken state is not retried
    ex.run(0.3)
    assert ex.value("acc.y") == 8.0
    _write(src, NODE_V1)                                    # fixed again
    assert ex.check_reload()[0].ok


def test_hot_reload_port_change_revalidates(tmp_path):
    src = tmp_path / "acc.py"
    _write(src, NODE_V1)
    g = _graph(src)
    ex = Executor(g)
    ex.run(0.1)
    # new required input -> graph invalid -> old version stays
    _write(src, NODE_V1.replace('INPUTS = {"u": Port("float")}', 'INPUTS = {"u": Port("float"), "v": Port("float")}'))
    ev = ex.check_reload()[0]
    assert not ev.ok and ev.ports_changed and "Pflichteingang acc.v" in ev.message
    # additional output -> still valid -> accepted, executor recompiles
    _write(src, NODE_V1.replace('OUTPUTS = {"y": Port("float")}', 'OUTPUTS = {"y": Port("float"), "z": Port("float")}')
           .replace('return {"y": self.total}', 'return {"y": self.total, "z": -self.total}'))
    ev = ex.check_reload()[0]
    assert ev.ok and ev.ports_changed
    ex.run(0.2)
    assert ex.value("acc.z") == -ex.value("acc.y") == -6.0


def test_python_example_nodes_have_layer_ports():
    expected = {"my_controller_node.py:PurePursuitController": "tracking_controller",
                "my_planner_node.py:LaneKeepingPlanner": "trajectory_planner",
                "my_vehicle_model.py:KinematicBicyclePlant": "vehicle_plant",
                "my_behavior_planner.py:SimpleBehaviorPlanner": "behavior_planner",
                "my_sensor_fusion_module.py:TwoSensorFusion": "perception"}
    for spec, kind in expected.items():
        inst = create_component(f"python:{(EX / spec.split(':')[0]).as_posix()}:{spec.split(':')[1]}")
        base = LAYER_BASES[kind]
        assert inst.KIND == kind
        assert {k: (p.type, p.feedback) for k, p in inst.input_ports().items()} == \
               {k: (p.type, p.feedback) for k, p in base.input_ports().items()}
        assert {k: p.type for k, p in inst.output_ports().items()} == {k: p.type for k, p in base.output_ports().items()}
        assert inst.DIRECT_FEEDTHROUGH == base.DIRECT_FEEDTHROUGH


def test_example_chain_closed_loop_and_deterministic():
    def run():
        g = Graph.load(ROOT / "configs" / "graphs" / "examples" / "custom_nodes_kette.json")
        assert g.validate().ok
        ex = Executor(g)
        ex.run(8.0)
        return ex
    ex = run()
    ego = ex.value("plant.ego")
    assert abs(ego.y) < 0.3 and ego.vx == pytest.approx(15.0, abs=0.6) and ego.x > 90
    assert abs(ex.value("controller.status").e_n) < 0.3
    ex2 = run()
    a, b = ex.recorder.to_arrays(), ex2.recorder.to_arrays()
    assert "controller:delta" in a and a["controller:delta"].tobytes() == b["controller:delta"].tobytes()
    assert ex2.value("plant.ego") == ego


def test_sensor_fusion_reduces_noise_and_is_reproducible():
    from vdsim.framework.context import RunContext
    from vdsim.framework.types import EgoState, ObjectState, WorldState
    spec = f"python:{(EX / 'my_sensor_fusion_module.py').as_posix()}:TwoSensorFusion"
    errs = []
    for seed in (1, 1):
        f = create_component(spec)
        f.instance_name = "fusion"
        f.reset(RunContext(seed=seed))
        e = []
        for k in range(200):
            w = WorldState(objects=[ObjectState(id=7, x=20.0 + k * 0.1, y=3.5, v=10.0)])
            out = f.step(k * 0.01, {"world": w, "ego": EgoState()})["objects"].objects[0]
            e.append((out.x - w.objects[0].x, out.y - 3.5))
        errs.append(np.asarray(e))
    assert errs[0].tobytes() == errs[1].tobytes()
    assert np.std(errs[0][50:, 1]) < 0.2 and np.std(errs[0][50:, 0]) < 0.2


@pytest.mark.parametrize("kind", ["node", *LAYER_BASES])
def test_create_custom_node_python_runs(tmp_path, kind):
    res = create_custom_node("python", f"my_{kind}", kind, tmp_path)
    assert res.path.exists() and res.spec.startswith("python:")
    inst = create_component(res.spec)
    assert inst.KIND == kind
    ins, outs = inst.ports()
    from vdsim.framework.context import RunContext
    inst.reset(RunContext())
    inputs = {k: (1.0 if p.type == "float" else None) for k, p in ins.items()}
    if inst.DIRECT_FEEDTHROUGH:
        out = inst.step(0.0, inputs)
    else:
        out = inst.output(0.0)
        inst.update(0.0, inputs, 0.01)
    assert set(out) == set(outs)
    with pytest.raises(FileExistsError):
        create_custom_node("python", f"my_{kind}", kind, tmp_path)
