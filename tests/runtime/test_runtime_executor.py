"""Executor: multi-rate timing, two-phase execution, feedback ports, determinism, debugging, profiler."""

import numpy as np
import pytest

from vdsim.framework.component import Component, Port
from vdsim.framework.plugins import component
from vdsim.runtime import BreakHit, ExecutionError, Executor, Graph, NodeStep, Recorder, RuntimeTypeError


@component
class _Counter(Component):
    # records the times it was called
    KIND, NAME, VERSION = "rt_test", "counter", "1.0.0"
    INPUTS = {"u": Port("Any", optional=True)}
    OUTPUTS = {"n": Port("float"), "seen": Port("Any")}

    def reset(self, context):
        super().reset(context)
        self.times = []

    def step(self, t, inputs):
        self.times.append(t)
        return {"n": float(len(self.times)), "seen": inputs["u"]}


@component
class _Noise(Component):
    KIND, NAME, VERSION = "rt_test", "noise", "1.0.0"
    OUTPUTS = {"y": Port("float")}

    def reset(self, context):
        super().reset(context)
        self.rng = context.rng(self.instance_name)

    def step(self, t, inputs):
        return {"y": float(self.rng.normal())}


@component
class _BadType(Component):
    KIND, NAME, VERSION = "rt_test", "bad_type", "1.0.0"
    OUTPUTS = {"y": Port("float")}

    def step(self, t, inputs):
        return {"y": "kein Skalar"}


@component
class _Raises(Component):
    KIND, NAME, VERSION = "rt_test", "raises", "1.0.0"
    OUTPUTS = {"y": Port("float")}

    def step(self, t, inputs):
        if t >= 0.05:
            raise ValueError("kaputt")
        return {"y": 0.0}


@component
class _FbReader(Component):
    KIND, NAME, VERSION = "rt_test", "fb_reader", "1.0.0"
    INPUTS = {"fb": Port("float", optional=True, feedback=True)}
    OUTPUTS = {"seen": Port("Any")}

    def step(self, t, inputs):
        return {"seen": inputs["fb"]}


def _integrator_loop(k=2.0, dt=0.01):
    # r = 1 -> e = r - y -> k e -> integrator (no direct feedthrough) -> y
    g = Graph("loop", base_dt=dt)
    g.add_node("r", "node/constant", params={"value": 1.0})
    g.add_node("e", "node/sum", params={"signs": "+-"})
    g.add_node("k", "node/gain", params={"k": k})
    g.add_node("i", "node/integrator")
    g.connect("r.y", "e.u1")
    g.connect("i.y", "e.u2")
    g.connect("e.y", "k.u")
    g.connect("k.y", "i.u")
    return g


def test_two_phase_integrator_loop_exact():
    g = _integrator_loop(k=2.0, dt=0.01)
    ex = Executor(g)
    res = ex.run(1.0)
    assert res.stop_reason == "t_end" and res.steps == 101
    t, y = ex.recorder.series("i.y")
    n = np.arange(len(t))
    # output(t_k) = y_k = 1 - (1 - k dt)^k  (explicit Euler, state before the update of step k)
    np.testing.assert_allclose(y, 1.0 - (1.0 - 0.02) ** n, rtol=0, atol=1e-14)
    assert ex.value("i.y") == pytest.approx(1 - 0.98 ** 100)
    np.testing.assert_allclose(ex.recorder["e.y"], 1.0 - y, atol=1e-15)


def test_multirate_timing_exact_and_zoh():
    g = Graph("mr", base_dt=0.01)
    g.add_node("fast", "rt_test/counter")
    g.add_node("slow", "rt_test/counter", period=0.1)
    g.add_node("mid", "rt_test/counter", period=0.03)
    g.add_node("clk", "node/clock")
    g.connect("clk.t", "slow.u")
    ex = Executor(g)
    ex.run(10.0)
    fast, slow, mid = (g.instance(n) for n in ("fast", "slow", "mid"))
    assert len(fast.times) == 1001 and len(slow.times) == 101 and len(mid.times) == 334
    assert slow.times[:4] == [0.0, 0.1, 0.2, 0.3] and slow.times[-1] == 10.0
    assert mid.times[:4] == [0.0, 0.03, 0.06, 0.09]
    assert fast.times == [round(k * 0.01, 12) for k in range(1001)]        # no float accumulation
    t, n_slow = ex.recorder.series("slow.n")
    assert list(n_slow[:12]) == [1.0] * 10 + [2.0] * 2                       # zero-order hold
    assert ex.recorder.t[-1] == 10.0


def test_long_run_has_no_drift():
    g = Graph("drift", base_dt=0.001)
    g.add_node("slow", "rt_test/counter", period=0.1)
    ex = Executor(g, recorder=False, profile=False)
    ex.run(100.0)
    times = g.instance("slow").times
    assert times[-1] == 100.0 and times[777] == 77.7 and len(times) == 1001


def test_feedback_port_reads_previous_step():
    g = Graph()
    g.add_node("clk", "node/clock")
    g.add_node("r", "rt_test/fb_reader")
    g.connect("clk.t", "r.fb")
    ex = Executor(g)
    ex.run(0.05)
    t, seen = ex.recorder.series("clk.t")
    vals = [ex.recorder.columns.get("r.seen")]
    assert vals[0] is None                                       # Any ports are not recorded by default
    ex2 = Executor(g, recorder=Recorder(ports=["r.seen", "clk.t"]))
    ex2.run(0.05)
    seen = ex2.recorder["r.seen"]
    assert np.isnan(seen[0]) and list(seen[1:]) == pytest.approx([0.0, 0.01, 0.02, 0.03, 0.04])


def test_determinism_bit_identical(tmp_path):
    def run():
        g = _integrator_loop()
        g.add_node("noise", "rt_test/noise")
        g.add_node("lp", "node/lowpass", params={"T": 0.05}, period=0.02)
        g.add_node("sine", "node/sine", params={"frequency": 3.0})
        g.add_node("sum", "node/sum")
        g.connect("noise.y", "sum.u1")
        g.connect("sine.y", "sum.u2")
        g.connect("sum.y", "lp.u")
        ex = Executor(g)
        ex.run(2.0)
        return ex.recorder.to_arrays()
    a, b = run(), run()
    assert a.keys() == b.keys()
    for key in a:
        assert a[key].tobytes() == b[key].tobytes(), key
    # reset() of the same executor reproduces the run as well
    g = _integrator_loop()
    g.add_node("noise", "rt_test/noise")
    ex = Executor(g)
    ex.run(1.0)
    first = ex.recorder.to_arrays()["noise.y"].copy()
    ex.reset()
    ex.run(1.0)
    assert ex.recorder.to_arrays()["noise.y"].tobytes() == first.tobytes()


def test_breakpoint_single_step_pause_resume():
    g = _integrator_loop()
    ex = Executor(g)
    bp = ex.add_breakpoint("k", condition=lambda inp: inp["u"] < 0.5)
    res = ex.run(1.0)
    assert res.stop_reason == "breakpoint" and isinstance(res.break_hit, BreakHit)
    hit = res.break_hit
    assert hit.node == "k" and hit.inputs["u"] < 0.5 and ex.paused
    # first time e < 0.5: 0.98^n < 0.5 -> n = 35
    assert hit.tick == 35 and hit.t == pytest.approx(0.35)
    assert ex.mid_step and ex.value("e.y") == hit.inputs["u"]
    k_before = ex.value("k.y")
    s = ex.step_node()                               # executes k only
    assert isinstance(s, NodeStep) and s.node == "k" and s.phase == "step"
    assert ex.value("k.y") == pytest.approx(2 * hit.inputs["u"]) and ex.value("k.y") != k_before
    s = ex.step_node()                               # update of the integrator, completes the step
    assert s.node == "i" and s.phase == "update" and s.step_complete and ex.tick == 36
    ex.remove_breakpoint(bp)
    once = ex.add_breakpoint(None, condition=lambda inp, t: t >= 0.5, once=True)
    res = ex.run(1.0)
    assert res.stop_reason == "breakpoint" and res.break_hit.t == pytest.approx(0.5) and once.hits == 1
    res = ex.run(1.0)                                 # continue after the breakpoint
    assert res.stop_reason == "t_end" and ex.t == 1.0
    # a run interrupted by a breakpoint gives the same result as an uninterrupted run
    ref = Executor(_integrator_loop())
    ref.run(1.0)
    assert ref.value("i.y") == ex.value("i.y")


def test_step_and_pause_in_realtime_mode():
    g = _integrator_loop()
    ex = Executor(g, realtime_factor=2.0)
    assert ex.advance(0.05) == 10                       # 0.05 s wall * 2 = 0.1 s = 10 steps
    ex.pause()
    assert ex.advance(1.0) == 0
    assert ex.step() is None and ex.tick == 11          # single step while paused
    ex.resume()
    assert ex.advance(0.0151) == 3
    ex.max_steps_per_advance = 5
    assert ex.advance(10.0) == 5 and ex.realtime_overruns == 1


def test_stop_condition_request_stop_and_events():
    g = _integrator_loop()
    ex = Executor(g)
    res = ex.run(10.0, stop=lambda e: "Sollwert erreicht" if e.value("i.y") > 0.9 else None)
    assert res.stop_reason == "stop" and res.message == "Sollwert erreicht"
    assert ex.value("i.y") > 0.9 and ex.t < 2.0
    assert ex.recorder.events_of("stop")[0].message == "Sollwert erreicht"
    ex.add_listener(step=lambda e: e.request_stop("genug") if e.tick >= 150 else None)
    res = ex.run(10.0)
    assert res.stop_reason == "request" and ex.tick == 150


def test_listeners_probes_and_profiler():
    g = _integrator_loop()
    ex = Executor(g)
    calls = []
    h = ex.add_listener(before=lambda n, ph, t, inp: calls.append(("b", n, ph)),
                        after=lambda n, ph, t, inp, out, ns: calls.append(("a", n, ph)))
    probe = ex.add_probe("k.y", history=5)
    ex.run(0.0)
    assert calls[:4] == [("b", "i", "output"), ("a", "i", "output"), ("b", "r", "step"), ("a", "r", "step")]
    assert calls[-1] == ("a", "i", "update")
    ex.remove_listener(h)
    ex.run(0.5)
    assert probe.value == ex.value("k.y") and len(probe.history) == 5 and probe.t == 0.5
    assert ex.outputs("i") == {"y": ex.value("i.y")}
    rep = ex.profiler.report()
    assert set(rep) == {"r", "e", "k", "i"}
    assert rep["k"]["calls"] == 51 and rep["k"]["max_us"] >= rep["k"]["p95_us"] >= 0 and rep["k"]["mean_us"] > 0
    assert "Executor-Overhead" in ex.profiler.table()
    assert ex.profiler.overhead()["per_node_us"] > 0


def test_runtime_type_check_and_node_errors():
    g = Graph()
    g.add_node("b", "rt_test/bad_type")
    with pytest.raises(RuntimeTypeError, match="b.y soll 'float' liefern"):
        Executor(g, check_types=True).run(0.1)
    Executor(g, check_types=False).run(0.1)            # unchecked: passes through
    g2 = Graph()
    g2.add_node("x", "rt_test/raises")
    ex = Executor(g2)
    with pytest.raises(ExecutionError, match="Fehler in Knoten 'x' \\(step\\) bei t=0.05 s: ValueError: kaputt"):
        ex.run(1.0)
    assert ex.recorder.events_of("error")[0].node == "x"


def test_runtime_graph_changes_and_parameters():
    g = _integrator_loop()
    ex = Executor(g)
    ex.run(0.5)
    y_mid = ex.value("i.y")
    g.set_param("k", "k", 0.0)                           # parameter change at runtime
    ex.run(0.6)
    y_mid = ex.value("i.y")                              # (includes the update of step 0.5 with the old k)
    ex.run(0.7)
    assert ex.value("i.y") == y_mid
    g.add_node("probe", "node/probe")                   # structural change: recompiled at the next step
    g.connect("i.y", "probe.u")
    ex.run(0.8)
    assert ex.value("probe.y") == y_mid and "probe:value" in ex.recorder.columns
    g.add_node("bad", "node/gain")                     # invalid graph is reported at the next step
    with pytest.raises(Exception, match="Pflichteingang bad.u"):
        ex.run(0.9)


def test_scope_and_vector_blocks():
    g = Graph(base_dt=0.1)
    g.add_node("a", "node/constant", params={"value": 1.0})
    g.add_node("b", "node/ramp", params={"slope": 2.0})
    g.add_node("mux", "node/mux", params={"n": 2})
    g.add_node("sat", "node/saturation", params={"lower": 0.0, "upper": 1.5})
    g.add_node("demux", "node/demux", params={"n": 2})
    g.add_node("sw", "node/switch", params={"threshold": 0.5})
    g.add_node("scope", "node/scope", params={"n": 2})
    g.connect("a.y", "mux.u1")
    g.connect("b.y", "mux.u2")
    g.connect("mux.y", "sat.u")
    g.connect("sat.y", "demux.u")
    g.connect("demux.y1", "sw.u1")
    g.connect("b.y", "sw.control")
    g.connect("demux.y2", "sw.u2")
    g.connect("sw.y", "scope.u1")
    g.connect("demux.y2", "scope.u2")
    ex = Executor(g)
    ex.run(1.0)
    t, y2 = g.instance("scope").data("u2")
    np.testing.assert_allclose(y2, np.minimum(2 * t, 1.5))
    _, sw = g.instance("scope").data("u1")
    np.testing.assert_allclose(sw, np.where(2 * t >= 0.5, 1.0, np.minimum(2 * t, 1.5)))
