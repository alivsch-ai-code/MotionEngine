import json
from pathlib import Path

from vdsim.matlab import analyze

ROOT = Path(__file__).resolve().parents[2]
A5 = ROOT / "examples" / "matlab" / "kin_tracking_with_orientation_stab.m"
FIX = ROOT / "tests" / "matlab" / "fixtures"


def test_a5_analysis():
    res = analyze(A5)
    f = res.main
    assert f.outputs == ["delta_dot", "F_l"] and f.calls == ["normalize_angle"]
    assert {"cos", "sin", "tan"} <= set(f.builtins)
    eqs = {e["equation"] for e in f.equations}
    assert {"4.7", "4.9", "4.10a", "4.11", "4.12", "4.15", "4.16", "4.17", "4.18", "A.10", "A.13"} <= eqs
    assert next(e for e in f.equations if e["equation"] == "4.12")["target"] == "w2"
    dd = set(f.output_dependencies["delta_dot"])
    assert {"k1", "k2", "k4", "kappa_d_dot"} <= dd and not dd & {"k3", "m", "J", "gam", "v_d_dot"}
    assert set(f.output_dependencies["F_l"]) == set(f.inputs)
    c = f.control
    assert c["gains"] == ["k1", "k2", "k3", "k4"]
    assert {t["term"] for t in c["feedforward_terms"]} == {"kappa_d", "v_d_dot", "kappa_d_dot"}
    assert len(c["feedback_terms"]) == 8 and c["has_feedforward"]
    assert {"e_t", "e_n", "e_psi", "e_v", "e_delta"} <= set(c["errors"])
    assert f.unused_variables == [] and f.complexity["cyclomatic"] == 1
    assert r"\dot{\xi}_{1}" in next(a["latex"] for a in f.assignments if a["target"] == "xi1_dot")
    assert json.loads(res.to_json())["functions"][0]["name"] == "kin_tracking_with_orientation_stab"
    dot = res.to_dot()
    assert dot.startswith("digraph") and '"e_psi" -> "xi1"' in dot
    assert "digraph calls" in res.to_dot("calls")


def test_pid_and_pure_feedback_structures():
    pid = analyze(FIX / "pid_controller.m").main.control
    assert pid["structure"].startswith("PID") and not pid["has_feedforward"]
    assert pid["integrators"][0]["state"] == "integ" and pid["differentiators"]
    pf = analyze(FIX / "pure_feedback.m").main.control
    assert pf["has_feedback"] and not pf["has_feedforward"] and pf["references"] == ["r"]


def test_unused_and_complexity():
    f = analyze("function y = f(a, b)\nz = 3;\ny = 0;\nfor k = 1:a\n if k > 2 && a < 9\n y = y + k;\n end\nend\n").main
    assert f.unused_variables == ["z"] and f.unused_inputs == ["b"]
    assert f.complexity["cyclomatic"] == 4 and f.complexity["max_nesting"] == 2
