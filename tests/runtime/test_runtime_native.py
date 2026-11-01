"""Native custom nodes (C ABI): codegen, Rust/C++ build, load, run, codec round trip, hot reload, scaffolding.

Rust tests are skipped if no working cargo toolchain exists, C++ tests if no working
compiler (MSVC with Windows SDK, g++ or clang++) is found. All build artifacts go to tmp.
"""

import shutil
from pathlib import Path

import numpy as np
import pytest

from vdsim.framework import types as T
from vdsim.framework.context import RunContext
from vdsim.framework.plugins import create_component
from vdsim.geometry import ReferenceLine
from vdsim.runtime import Executor, Graph, codecs, codegen, create_custom_node
from vdsim.runtime import build as B

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "custom_nodes"


@pytest.fixture(scope="module", autouse=True)
def build_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("native_build")
    B.set_build_root(root)
    yield root
    B.set_build_root(None)


def require(language):
    ok, msg = B.toolchain_status(language)
    if not ok:
        pytest.skip(f"{language}-Toolchain nicht verfügbar: {msg[:300]}")


# ---------------------------------------------------------------------------- sample values of every codec type
def sample_values():
    ego = T.EgoState(t=1.5, x=10.0, y=-2.0, psi=0.3, vx=12.0, vy=0.2, r=0.05, ax=0.5, ay=0.6, delta=0.02,
                     delta_rate=-0.01, gear=-1)
    cmd = T.ControlCommand(t=1.5, steer_rate=0.1, steer_angle=None, force=1500.0, accel=None, direction=-1)
    status = T.ControllerStatus(t=1.5, e_t=0.1, e_n=-0.2, e_theta=0.03, e_v=0.4, e_t_dot=0.01, e_n_dot=-0.02,
                                reinit_request=True, lookahead=6.0)
    ci = T.ControlInput(steer_front=0.05, steer_rear=-0.01, drive_torque=np.array([1, 2, 3, 4.0]),
                        brake_torque=np.array([5, 6, 7, 8.0]), roll_moment=9.0, damper_force=np.array([1, 1, 2, 2.0]))
    ac = T.ActuatorCommand(t=1.5, steer_angle=0.1, steer_rate=0.2, steer_rear=0.0, drive_torque=np.arange(4.0),
                           brake_torque=np.arange(4.0) + 4)
    n = 7
    tt = np.linspace(0.0, 0.6, n)
    traj = T.PlannedTrajectory(t=tt, x=tt * 10, y=tt ** 2, theta=tt * 0.1, kappa=tt * 0.01, dkappa=tt * 0.001,
                               v=10 + tt, a=tt * 0.5, s=tt * 10, d=-tt, direction=-1, reference_point="rear_axle",
                               cost=3.5, valid=False)
    objs = T.ObjectList(objects=[T.ObjectState(id=3, type="truck", x=1.0, y=2.0, psi=0.1, v=5.0, a=0.2, length=12.0,
                                               width=2.5),
                                 T.ObjectState(id=9, type="pedestrian", x=-1.0, y=0.5, v=1.2, length=0.5, width=0.5)])
    world = T.WorldState(objects=list(objs.objects))
    pred = T.Prediction(objects=[T.PredictedObject(id=3, type="truck", length=12.0, width=2.5, t=tt, x=tt * 5,
                                                   y=tt * 0 + 2, psi=tt * 0, v=tt * 0 + 5)])
    ref = ReferenceLine.straight(20.0, 1.0, 2.0, 0.2, ds=5.0)
    return {"float": 2.5, "bool": True, "Vector": np.array([1.0, -2.0, 3.5]), "EgoState": ego, "ControlCommand": cmd,
            "ControllerStatus": status, "ControlInput": ci, "ActuatorCommand": ac, "PlannedTrajectory": traj,
            "ObjectList": objs, "WorldState": world, "Prediction": pred, "ReferenceLine": ref}


ECHO_TYPES = list(sample_values())
RUST_TYPE = {"float": "f64", "bool": "bool", "Vector": "Vec<f64>"}
CPP_TYPE = {"float": "double", "bool": "bool", "Vector": "vdsim::Vector"}


def _echo_info(lang):
    import json
    ports = [{"name": f"p{i}", "type": t} for i, t in enumerate(ECHO_TYPES)]
    return json.dumps({"name": f"echo_{lang}", "kind": "node", "version": "1.0.0", "label": "Echo",
                       "inputs": [dict(p, optional=True) for p in ports], "outputs": ports, "params": []})


def _rust_echo(dest):
    (dest / "src").mkdir(parents=True)
    (dest / "Cargo.toml").write_text('[package]\nname = "echo_node"\nversion = "1.0.0"\nedition = "2021"\n'
                                     '[lib]\ncrate-type = ["cdylib"]\n', encoding="utf-8")
    codegen.write_headers(dest / "src", cpp=False)
    lines = [f"        if let Some(v) = inputs.get::<{RUST_TYPE.get(t, t)}>({i}) {{ outputs.set({i}, &v); }}"
             for i, t in enumerate(ECHO_TYPES)]
    (dest / "src" / "lib.rs").write_text(
        "#[macro_use]\nmod vdsim_node;\nuse vdsim_node::*;\n"
        f"const INFO: &str = r#\"{_echo_info('rust')}\"#;\n"
        "struct Echo;\nimpl Node for Echo {\n    fn new(_p: &[f64]) -> Self { Echo }\n"
        "    fn step(&mut self, _t: f64, inputs: &Inputs, outputs: &mut Outputs) -> Result<(), String> {\n"
        + "\n".join(lines) + "\n        Ok(())\n    }\n}\nexport_node!(Echo, INFO);\n", encoding="utf-8")
    return dest


def _cpp_echo(dest):
    dest.mkdir(parents=True)
    codegen.write_headers(dest, rust=False)
    lines = [f"    if (in.has({i})) out.set({i}, in.get<{CPP_TYPE.get(t, 'vdsim::' + t)}>({i}));"
             for i, t in enumerate(ECHO_TYPES)]
    (dest / "echo_node.cpp").write_text(
        '#include "vdsim_node.h"\n'
        f'static const char* INFO = R"json({_echo_info("cpp")})json";\n'
        "class Echo : public vdsim::Node {\n public:\n  Echo(const double*, size_t) {}\n"
        "  void step(double t, const vdsim::Inputs& in, vdsim::Outputs& out) override {\n    (void)t;\n"
        + "\n".join(lines) + "\n  }\n};\nVDSIM_EXPORT_NODE(Echo, INFO)\n", encoding="utf-8")
    return dest


def _check_echo(node):
    values = sample_values()
    node.reset(RunContext(dt=0.01))
    out = node.step(0.0, {f"p{i}": v for i, v in enumerate(values.values())})
    assert len(out) == len(values)
    for i, (tp, v) in enumerate(values.items()):
        a, b = codecs.encode(tp, v), codecs.encode(tp, out[f"p{i}"])
        np.testing.assert_array_equal(a, b, err_msg=tp)
    assert out["p3"] == values["EgoState"]
    assert out["p4"].steer_angle is None and out["p4"].force == 1500.0 and out["p4"].direction == -1
    assert out["p8"].reference_point == "rear_axle" and out["p8"].valid is False
    assert [o.type for o in out["p9"].objects] == ["truck", "pedestrian"]
    # unconnected inputs -> outputs not set (value held by the executor)
    assert node.step(0.0, {}) == {}


# ---------------------------------------------------------------------------- tests without compiler
def test_codegen_layouts_match_python_codecs():
    h, rs = codegen.cpp_header(), codegen.rust_module()
    assert f"constexpr size_t EGO_STATE_SIZE = {len(T.EGO_FIELDS)};" in h
    assert f"pub const CONTROL_COMMAND_SIZE: usize = {len(T.COMMAND_FIELDS)};" in rs
    assert f"constexpr size_t TRAJECTORY_POINT_SIZE = {len(T.TRAJECTORY_FIELDS)};" in h
    assert "constexpr size_t EGO_STATE_GEAR = 11;" in h and "OBJECT_PEDESTRIAN = 2" in h
    for name in ("EgoState", "ControlCommand", "PlannedTrajectory", "ObjectList", "Prediction", "ReferenceLine",
                 "ControllerStatus", "ControlInput", "ActuatorCommand"):
        assert f"struct {name}" in h and f"pub struct {name}" in rs
    # python codec extensions round trip
    for tp, v in sample_values().items():
        np.testing.assert_array_equal(codecs.encode(tp, codecs.decode(tp, codecs.encode(tp, v))),
                                      codecs.encode(tp, v), err_msg=tp)
    np.testing.assert_array_equal(codecs.encode("PlannedTrajectory", sample_values()["PlannedTrajectory"]),
                                  T.encode("PlannedTrajectory", sample_values()["PlannedTrajectory"]))


def test_example_headers_are_current():
    assert codegen.header_is_current(EXAMPLES / "rust" / "my_controller_node" / "src" / "vdsim_node.rs")
    assert codegen.header_is_current(EXAMPLES / "cpp" / "my_controller_node" / "vdsim_node.h")


def test_scaffold_rejects_layers_without_codec(tmp_path):
    with pytest.raises(ValueError, match="BehaviorCommand"):
        create_custom_node("rust", "planner", "trajectory_planner", tmp_path)


# ---------------------------------------------------------------------------- Rust
def _copy_example(lang, tmp_path):
    dst = tmp_path / f"{lang}_my_controller_node"
    shutil.copytree(EXAMPLES / lang / "my_controller_node", dst,
                    ignore=shutil.ignore_patterns("target", "Cargo.lock", "build"))
    return dst


def _random_inputs(rng, k):
    tt = np.linspace(0.0, 5.0, 51) + k * 0.01
    x = np.linspace(0.0, 60.0, 51)
    y = rng.normal(0.0, 0.5) * np.sin(x / 20.0)
    th = np.arctan(np.gradient(y, x))
    traj = T.PlannedTrajectory(t=tt, x=x, y=y, theta=th, kappa=0 * x, dkappa=0 * x, v=np.full(51, 10.0),
                               a=np.full(51, 0.1), s=x, d=y)
    ego = T.EgoState(t=k * 0.01, x=rng.uniform(0, 10), y=rng.normal(0, 1), psi=rng.normal(0, 0.1),
                     vx=rng.uniform(0, 15))
    return {"ego": ego, "trajectory": traj}


def _compare_with_python(native, steps=100):
    py = create_component(f"python:{(EXAMPLES / 'python' / 'my_controller_node.py').as_posix()}:PurePursuitController")
    ctx = RunContext(dt=0.01)
    native.reset(ctx)
    py.reset(ctx)
    rng = np.random.default_rng(3)
    for k in range(steps):
        inp = _random_inputs(rng, k)
        a, b = py.step(k * 0.01, inp), native.step(k * 0.01, inp)
        for f in ("t", "steer_angle", "accel", "direction"):
            assert getattr(a["command"], f) == pytest.approx(getattr(b["command"], f), abs=1e-12), f
        for f in ("e_t", "e_n", "e_theta", "e_v", "lookahead"):
            assert getattr(a["status"], f) == pytest.approx(getattr(b["status"], f), abs=1e-12), f
    assert native.get_state()["__native_state__"][0] == py.calls == steps


def test_rust_example_build_load_run_matches_python(tmp_path):
    # codec round trip through the native interface: EgoState + PlannedTrajectory in, ControlCommand out
    require("rust")
    crate = _copy_example("rust", tmp_path)
    node = create_component(f"rust:{crate.as_posix()}")
    assert node.LANGUAGE == "rust" and node.KIND == "tracking_controller" and node.VERSION == "1.0.0"
    assert list(node.input_ports()) == ["ego", "trajectory"] and list(node.output_ports()) == ["command", "status"]
    assert [p["name"] for p in type(node).describe()["params"]][:2] == ["lookahead_min", "lookahead_gain"]
    _compare_with_python(node)
    node.close()
    assert not (crate / "Cargo.lock").exists() and not (crate / "target").exists()


def test_rust_codec_roundtrip_all_types(tmp_path):
    require("rust")
    node = create_component(f"rust:{_rust_echo(tmp_path / 'echo').as_posix()}")
    _check_echo(node)
    node.close()


def test_rust_hot_reload_in_graph(tmp_path):
    require("rust")
    crate = _copy_example("rust", tmp_path)
    g = Graph("native", base_dt=0.01)
    g.add_node("ego", "node/typed_default", params={"type_name": "EgoState"})
    g.add_node("traj", "node/typed_default", params={"type_name": "PlannedTrajectory"})
    g.add_node("ctl", f"rust:{crate.as_posix()}", params={"speed_gain": 2.0})
    g.connect("ego.y", "ctl.ego")
    g.connect("traj.y", "ctl.trajectory")
    ex = Executor(g, check_types=True)
    ex.run(0.04)
    old = g.instance("ctl")
    assert ex.value("ctl.command").accel == 0.0 and old.native_state()[0] == 5
    lib = crate / "src" / "lib.rs"
    lib.write_text(lib.read_text(encoding="utf-8").replace("accel: Some(-self.speed_gain * ego.vx)",
                                                           "accel: Some(21.0 * self.speed_gain)"), encoding="utf-8")
    events = ex.check_reload()
    assert len(events) == 1 and events[0].ok, events[0].message
    new = g.instance("ctl")
    assert new is not old and old._lib.closed                     # old library released (FreeLibrary)
    assert new.native_state()[0] == 5 and new.params.speed_gain == 2.0
    ex.run(0.09)
    assert ex.value("ctl.command").accel == 42.0 and new.native_state()[0] == 10
    # a build error keeps the running version
    lib.write_text(lib.read_text(encoding="utf-8").replace("fn wrap(", "fn wrap(("), encoding="utf-8")
    events = ex.check_reload()
    assert not events[0].ok and "bisherige Version" in events[0].message and g.instance("ctl") is new
    ex.run(0.1)
    # parameter change at runtime recreates the native object and keeps its state
    g.set_param("ctl", "speed_gain", 1.0)
    ex.run(0.11)
    assert ex.value("ctl.command").accel == 21.0 and g.instance("ctl").native_state()[0] == 12
    ex.close()


@pytest.mark.parametrize("kind", ["tracking_controller", "vehicle_plant", "node"])
def test_rust_scaffold_compiles_and_runs(tmp_path, kind):
    require("rust")
    res = create_custom_node("rust", f"rs_{kind}", kind, tmp_path)
    node = create_component(res.spec)
    assert node.KIND == kind and node.DIRECT_FEEDTHROUGH == (kind != "vehicle_plant")
    assert "warning" not in node.build_log.lower(), node.build_log
    node.reset(RunContext(dt=0.01))
    if kind == "vehicle_plant":
        out = node.output(0.5)
        assert out["ego"].t == 0.5
        node.update(0.5, {"control": T.ControlInput()}, 0.01)
    elif kind == "node":
        assert node.step(0.0, {"u": 2.0}) == {"y": 2.0}
    else:
        out = node.step(0.3, {"ego": T.EgoState(), "trajectory": T.PlannedTrajectory()})
        assert out["command"].t == 0.3 and isinstance(out["status"], T.ControllerStatus)
    assert node.native_state()[0] == 1
    node.close()


# ---------------------------------------------------------------------------- C++
def test_cpp_example_build_load_run_matches_python(tmp_path):
    require("cpp")
    src = _copy_example("cpp", tmp_path)
    node = create_component(f"cpp:{src.as_posix()}")
    assert node.LANGUAGE == "cpp" and node.NAME == "my_pure_pursuit_cpp"
    _compare_with_python(node)
    node.close()


def test_cpp_codec_roundtrip_all_types(tmp_path):
    require("cpp")
    node = create_component(f"cpp:{_cpp_echo(tmp_path / 'echo').as_posix()}")
    _check_echo(node)
    node.close()


@pytest.mark.parametrize("kind", ["tracking_controller", "vehicle_plant"])
def test_cpp_scaffold_compiles_and_runs(tmp_path, kind):
    require("cpp")
    res = create_custom_node("cpp", f"cpp_{kind}", kind, tmp_path)
    node = create_component(res.spec)
    node.reset(RunContext(dt=0.01))
    if kind == "vehicle_plant":
        assert node.output(0.5)["ego"].t == 0.5
    else:
        assert node.step(0.3, {"ego": T.EgoState(), "trajectory": T.PlannedTrajectory()})["command"].t == 0.3
    node.close()
