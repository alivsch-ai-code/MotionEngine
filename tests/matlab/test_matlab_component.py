import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from vdsim.framework.component import Component
from vdsim.framework.plugins import create_component
from vdsim.matlab import convert_file, load_matlab_component
from vdsim.matlab.interpreter import Interpreter

ROOT = Path(__file__).resolve().parents[2]
A5 = ROOT / "examples" / "matlab" / "kin_tracking_with_orientation_stab.m"
FIX = ROOT / "tests" / "matlab" / "fixtures"
PID = {"kp": 2.0, "ki": 1.0, "kd": 0.1, "dt": 0.01, "u_min": -1.0, "u_max": 1.0}


@pytest.mark.parametrize("backend", ["interpreter", "python"])
def test_a5_component(backend):
    comp = load_matlab_component(A5, backend=backend, params={"l_v": 1.2, "l_h": 1.5, "m": 1500.0, "J": 2500.0,
                                                               "gam": 0.1, "k1": 1.0, "k2": 2.0, "k3": 3.0, "k4": 4.0})
    assert isinstance(comp, Component) and comp.KIND == "matlab" and comp.LANGUAGE == "matlab"
    assert list(comp.OUTPUTS) == ["delta_dot", "F_l"] and "k1" not in comp.INPUTS and len(comp.INPUTS) == 13
    assert all(p.type == "float" for p in comp.input_ports().values())
    assert "Appendix A.5" in comp.DOC.theory and "4.11" in comp.DOC.equations
    vals = [0.1, 0.2, 0.3, 0.05, 0.01, 2.0, 0.1, 1.0, 0.0, 0.0, 0.25, 2.1, 0.02]
    out = comp.step(0.0, dict(zip(comp.INPUTS, vals)))
    ref = Interpreter.from_file(A5).call(None, *vals, 1.2, 1.5, 1500.0, 2500.0, 0.1, 1.0, 2.0, 3.0, 4.0)
    assert (out["delta_dot"], out["F_l"]) == ref


@pytest.mark.parametrize("backend", ["interpreter", "python"])
def test_loader_spec_vector_ports_and_state(backend):
    comp = create_component(f"matlab:{FIX / 'pid_controller.m'}", dict(PID, backend=backend))
    first = comp.step(0.0, {"r": 1.0, "y": 0.2})
    comp.step(0.01, {"r": 1.0, "y": 0.3})
    state = comp.get_state()
    comp.reset(None)
    assert comp.step(0.0, {"r": 1.0, "y": 0.2}) == first
    comp.set_state(state)
    assert comp.step(0.02, {"r": 1.0, "y": 0.3})["integ_out"] == pytest.approx(0.007)   # restored, not reset
    mat = create_component(f"matlab:{FIX / 'matrices.m'}:matrices", {"backend": backend})
    assert mat.INPUTS["x"].type == "Vector" and mat.OUTPUTS["y"].type == "Vector"
    out = mat.step(0.0, {"x": [1.0, 2.0], "theta": 0.3})
    assert out["y"].shape == (2,) and isinstance(out["tr"], float)


def test_unconnected_input_and_bad_params():
    comp = load_matlab_component(FIX / "pure_feedback.m")
    with pytest.raises(ValueError, match="nicht verbunden"):
        comp.step(0.0, {"r": 1.0})
    with pytest.raises(ValueError):
        load_matlab_component(FIX / "pure_feedback.m", params={"nope": 1.0})


def test_convert_file_and_cli(tmp_path):
    res = convert_file(A5, "all", tmp_path)
    assert all(c.ok for c in res.values())
    assert (tmp_path / "python" / "kin_tracking_with_orientation_stab.py").exists()
    assert (tmp_path / "cpp" / "matlab_runtime.hpp").exists() and (tmp_path / "rust" /
                                                                  "kin_tracking_with_orientation_stab.rs").exists()
    bad = convert_file(FIX / "strings_cells.m", "rust", tmp_path / "bad")
    assert not bad["rust"].ok and not (tmp_path / "bad").exists()
    run = lambda *a: subprocess.run([sys.executable, "-m", "vdsim.matlab", *a], cwd=ROOT, capture_output=True,
                                    text=True, encoding="utf-8")
    r = run("convert", str(FIX / "pid_controller.m"), "--to", "python", "--out", str(tmp_path / "cli"))
    assert r.returncode == 0 and (tmp_path / "cli" / "pid_controller.py").exists()
    r = run("convert", str(FIX / "nested_functions.m"), "--to", "cpp", "--out", str(tmp_path / "x"))
    assert r.returncode == 1 and "Fehler" in r.stdout
    r = run("analyze", str(A5))
    assert r.returncode == 0 and "Vorsteuerung" in r.stdout
    r = run("analyze", str(A5), "--json")
    assert json.loads(r.stdout)["functions"][0]["outputs"] == ["delta_dot", "F_l"]


def test_reference_implementation():
    ref = pytest.importorskip("vdsim.stabilization.werling_kinematic")
    if not hasattr(ref, "kin_tracking_with_orientation_stab"):
        pytest.skip("Referenz kin_tracking_with_orientation_stab noch nicht vorhanden")
    rng = np.random.default_rng(7)
    it = Interpreter.from_file(A5)
    worst = 0.0
    for _ in range(300):
        a = [*rng.uniform(-3, 3, 7), float(rng.choice([-1.0, 1.0])), *rng.uniform(-3, 3, 5), 1.2, 1.5, 1500.0,
             2500.0, 0.1, *rng.uniform(0.1, 5, 4)]
        x, y = it.call(None, *a), ref.kin_tracking_with_orientation_stab(*a)
        worst = max(worst, max(abs(p - q) / max(1.0, abs(p)) for p, q in zip(x, y)))
    assert worst < 1e-9
