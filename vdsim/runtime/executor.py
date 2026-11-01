"""Deterministic multi-rate executor for component graphs.

Time base: integer ticks k with t_k = round(k * base_dt, 12) (no floating point
accumulation). A node with period T runs at the ticks k with k mod (T / base_dt) = 0;
between its samples its outputs are held (zero-order hold).

One base step (tick k) consists of
    1. output(t)           of all due nodes WITHOUT direct feedthrough (state -> outputs)
    2. step(t, inputs)     of all due nodes WITH direct feedthrough, in topological order
    3. update(t, inputs, dt) of all due nodes without direct feedthrough (dt = node period)
    4. latch of the values read by feedback ports, recording, step listeners
Feedback ports (Port.feedback=True) read the value at the end of the previous step.

Debugging: breakpoints (per node, conditional), single step per node (step_node) or per
base step (step), pause/resume, probes (live port values), listeners before/after every
node, per-node profiler. Real-time mode for the GUI: advance(wall_dt) runs as many base
steps as fit into wall_dt * realtime_factor.
"""

from __future__ import annotations

import math
import time
import weakref
from dataclasses import dataclass, field

from ..framework.context import RunContext
from ..framework.types import check_value
from .debug import BreakHit, Breakpoint, NodeStep, Probe, Profiler
from .graph import GraphValidationError
from .recorder import Recorder

OUTPUT, STEP, UPDATE = "output", "step", "update"


class ExecutionError(RuntimeError):
    """Exception inside a node (German message, original exception as __cause__)."""

    def __init__(self, message, node=None, phase=None, t=None):
        super().__init__(message)
        self.node, self.phase, self.t = node, phase, t


class RuntimeTypeError(ExecutionError):
    pass


@dataclass
class RunResult:
    t: float                    # time of the last completed step
    steps: int                  # base steps executed by this call
    stop_reason: str            # "t_end", "stop", "breakpoint", "pause", "request", "max_steps"
    message: str = ""
    wall_time: float = 0.0
    break_hit: BreakHit | None = None
    recorder: Recorder | None = None
    profile: dict = field(default_factory=dict)
    base_dt: float = 0.0

    @property
    def realtime_factor(self):
        # simulated time / wall time of this call
        return self.steps * self.base_dt / self.wall_time if self.wall_time > 0 else float("nan")


class _RT:
    # compiled runtime record of one node
    __slots__ = ("id", "comp", "ticks", "dt", "ft", "inputs", "out_keys", "out_types", "in_types", "prof",
                 "tick_ns", "ran")

    def __init__(self, nid, comp, ticks, base_dt, ft):
        self.id, self.comp, self.ticks, self.ft = nid, comp, ticks, ft
        self.dt = round(ticks * base_dt, 12)
        self.inputs = []          # [(port, source key or None, feedback)]
        self.out_keys = {}        # port -> "node.port"
        self.out_types = {}
        self.in_types = {}
        self.prof = None
        self.tick_ns = 0
        self.ran = False


class Executor:
    """Runs a Graph.

    Executor(graph, context=None, recorder=None, check_types=False, profile=True)
        context      RunContext (dt is set to graph.base_dt); default RunContext(dt=base_dt)
        recorder     Recorder (default: all float/bool ports + component signals); False = none
        check_types  check every output value against its port type (framework.types.check_value)
        profile      measure the computation time per node
    """

    def __init__(self, graph, context=None, recorder=None, check_types=False, profile=True, realtime_factor=1.0):
        self.graph = graph
        self.context = context
        self.recorder = Recorder() if recorder is None else (None if recorder is False else recorder)
        self.check_types = check_types
        self.profiler = Profiler(enabled=profile)
        self.realtime_factor = float(realtime_factor)
        self.max_steps_per_advance = 1000
        self.values = {}            # "node.port" -> current value (zero-order hold)
        self.breakpoints = []
        self.probes = {}
        self.break_hit = None
        self.paused = False
        self.tick = 0               # index of the next base step
        self.t = 0.0                # time of the current / last executed step
        self.initialized = False
        self.realtime_overruns = 0
        self._before, self._after, self._step_listeners = [], [], []
        self._prev = {}
        self._fb_keys = []
        self._actions = []
        self._plan_rev = None
        self._rts = {}
        self._pc = 0
        self._in_tick = False
        self._bp_skip = None
        self._stop_request = None
        self._rt_accum = 0.0
        self._initialized_instances = weakref.WeakSet()
        self.reloader = None

    # ------------------------------------------------------------------ properties
    @property
    def base_dt(self):
        return self.graph.base_dt

    def time_of(self, tick):
        return round(tick * self.graph.base_dt, 12)

    @property
    def mid_step(self):
        # True while a base step is partially executed (breakpoint / step_node)
        return self._in_tick

    # ------------------------------------------------------------------ compile
    def compile(self):
        graph = self.graph
        rep = graph.validate()
        if rep.errors:
            raise GraphValidationError(rep)
        plan = graph.execution_plan()
        rts = {}
        for nid in plan["output"] + plan["step"]:
            node = graph.nodes[nid]
            rt = _RT(nid, node.instance, graph.period_ticks(nid), graph.base_dt, node.direct_feedthrough)
            ins, outs = node.instance.ports()
            for pname, port in ins.items():
                src = graph.source_of(f"{nid}.{pname}")
                rt.inputs.append((pname, src, bool(port.feedback) and src is not None))
                rt.in_types[pname] = port.type
            for pname, port in outs.items():
                rt.out_keys[pname] = f"{nid}.{pname}"
                rt.out_types[pname] = port.type
            rt.prof = self.profiler.node(nid)
            rts[nid] = rt
        actions = ([(OUTPUT, rts[n]) for n in plan["output"]] + [(STEP, rts[n]) for n in plan["step"]]
                   + [(UPDATE, rts[n]) for n in plan["update"]])
        fb = []
        for rt in rts.values():
            for _, src, is_fb in rt.inputs:
                if is_fb and src not in fb:
                    fb.append(src)
        valid = {k for rt in rts.values() for k in rt.out_keys.values()}
        self.values = {k: v for k, v in self.values.items() if k in valid}
        self._prev = {k: v for k, v in self._prev.items() if k in valid}
        self._rts, self._actions, self._fb_keys = rts, actions, fb
        self._plan_rev = graph.revision
        if self.initialized:
            for rt in rts.values():
                if rt.comp not in self._initialized_instances:
                    self._reset_component(rt)
        if self.recorder is not None:
            self.recorder.bind(self)
        return plan

    def _reset_component(self, rt):
        comp = rt.comp
        comp.sample_time = rt.dt
        comp.instance_name = rt.id
        try:
            comp.reset(self.context)
        except Exception as exc:
            raise ExecutionError(f"Fehler in Knoten '{rt.id}' (reset): {type(exc).__name__}: {exc}", rt.id,
                                 "reset", 0.0) from exc
        self._initialized_instances.add(comp)

    def mark_initialized(self, component):
        # hot reload: the new instance was reset and received the old state already
        self._initialized_instances.add(component)

    # ------------------------------------------------------------------ lifecycle
    def reset(self, context=None):
        # (re)start at t = 0: validate + compile the graph, reset all components
        if context is not None:
            self.context = context
        if self.context is None:
            self.context = RunContext(dt=self.graph.base_dt)
        self.context.dt = self.graph.base_dt
        self.context.t = 0.0
        self.context.services["executor"] = self
        if self.recorder is not None:
            self.recorder.clear()
            self.context.recorder = self.recorder
        self.values, self._prev = {}, {}
        self.tick, self.t, self._pc, self._in_tick = 0, 0.0, 0, False
        self.break_hit, self._bp_skip, self._stop_request = None, None, None
        self.paused = False
        self._rt_accum = 0.0
        self.profiler.clear()
        self.initialized = False
        self._initialized_instances = weakref.WeakSet()
        self.compile()
        for rt in self._rts.values():
            self._reset_component(rt)
        self.initialized = True
        for probe in self.probes.values():
            probe.value, probe.t = None, None
        return self

    def request_stop(self, reason="Stopp angefordert"):
        # may be called by components (context.services["executor"]) or listeners
        self._stop_request = reason

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.break_hit = None

    # ------------------------------------------------------------------ hooks
    def add_listener(self, before=None, after=None, step=None):
        # before(node_id, phase, t, inputs); after(node_id, phase, t, inputs, outputs, duration_ns);
        # step(executor) after every complete base step. Returns a handle for remove_listener().
        handle = (before, after, step)
        if before:
            self._before.append(before)
        if after:
            self._after.append(after)
        if step:
            self._step_listeners.append(step)
        return handle

    def remove_listener(self, handle):
        before, after, step = handle
        for lst, cb in ((self._before, before), (self._after, after), (self._step_listeners, step)):
            if cb in lst:
                lst.remove(cb)

    def add_breakpoint(self, node=None, condition=None, once=False, phase=None, label=""):
        if node is not None and node not in self.graph.nodes:
            raise KeyError(f"Knoten '{node}' existiert nicht")
        bp = Breakpoint(node, condition, once, phase, label=label)
        self.breakpoints.append(bp)
        return bp

    def remove_breakpoint(self, bp):
        if bp in self.breakpoints:
            self.breakpoints.remove(bp)

    def clear_breakpoints(self):
        self.breakpoints.clear()

    def add_probe(self, key, history=0):
        probe = self.probes.get(key)
        if probe is None:
            probe = self.probes[key] = Probe(key, history)
            if key in self.values:
                probe.push(self.t, self.values[key])
        return probe

    def remove_probe(self, key):
        self.probes.pop(key, None)

    # ------------------------------------------------------------------ values
    def value(self, key, default=None):
        # current (held) value of an output "node.port"
        return self.values.get(key, default)

    def output(self, node_id, port, default=None):
        return self.values.get(f"{node_id}.{port}", default)

    def outputs(self, node_id):
        prefix = node_id + "."
        return {k[len(prefix):]: v for k, v in self.values.items() if k.startswith(prefix)}

    def inputs_of(self, node_id):
        # inputs a node would currently see
        rt = self._rts.get(node_id)
        return self._gather(rt) if rt is not None else {}

    def probe_values(self):
        from ..framework.types import summarize
        return {k: summarize(v) for k, v in self.values.items()}

    # ------------------------------------------------------------------ execution core
    def _gather(self, rt):
        vals, prev = self.values, self._prev
        return {name: ((prev.get(src) if fb else vals.get(src)) if src is not None else None)
                for name, src, fb in rt.inputs}

    def _begin_tick(self):
        if self._plan_rev != self.graph.revision:
            self.compile()
        self.t = self.time_of(self.tick)
        self.context.t = self.t
        self._in_tick = True
        self._step_t0 = time.perf_counter_ns()
        for rt in self._rts.values():
            rt.tick_ns = 0
            rt.ran = False

    def _end_tick(self):
        prof = self.profiler
        if prof.enabled:
            for rt in self._rts.values():
                if rt.ran:
                    rt.prof.add(rt.tick_ns)
        vals, prev = self.values, self._prev
        for key in self._fb_keys:
            prev[key] = vals.get(key)
        if self.recorder is not None:
            self.recorder.sample(self)
        self._in_tick = False
        self._pc = 0
        if prof.enabled:
            prof.steps.add(time.perf_counter_ns() - self._step_t0)
        self.tick += 1
        for cb in self._step_listeners:
            cb(self)

    def _write(self, rt, out, t):
        vals = self.values
        keys = rt.out_keys
        probes = self.probes
        for name, value in out.items():
            key = keys.get(name)
            if key is None:
                if self.check_types:
                    raise RuntimeTypeError(f"Knoten '{rt.id}' liefert unbekannten Ausgang '{name}' "
                                           f"(deklariert: {', '.join(keys)})", rt.id, "output", t)
                continue
            if self.check_types and not check_value(rt.out_types[name], value):
                raise RuntimeTypeError(f"Laufzeit-Typfehler bei t={t:g} s: {key} soll '{rt.out_types[name]}' "
                                       f"liefern, geliefert wurde {type(value).__name__}", rt.id, "output", t)
            vals[key] = value
            if probes:
                p = probes.get(key)
                if p is not None:
                    p.push(t, value)

    def _run_action(self, kind, rt):
        t = self.t
        comp = rt.comp
        inputs = self._gather(rt) if kind != OUTPUT else None
        if self.check_types and inputs:
            for name, v in inputs.items():
                if not check_value(rt.in_types[name], v):
                    raise RuntimeTypeError(f"Laufzeit-Typfehler bei t={t:g} s: Eingang {rt.id}.{name} erwartet "
                                           f"'{rt.in_types[name]}', erhalten {type(v).__name__}", rt.id, kind, t)
        for cb in self._before:
            cb(rt.id, kind, t, inputs)
        t0 = time.perf_counter_ns()
        try:
            if kind == STEP:
                out = comp.step(t, inputs)
            elif kind == OUTPUT:
                out = comp.output(t)
            else:
                comp.update(t, inputs, rt.dt)
                out = None
        except ExecutionError:
            raise
        except Exception as exc:
            if self.recorder is not None:
                self.recorder.event(t, "error", f"{type(exc).__name__}: {exc}", rt.id, phase=kind)
            raise ExecutionError(f"Fehler in Knoten '{rt.id}' ({kind}) bei t={t:g} s: {type(exc).__name__}: {exc}",
                                 rt.id, kind, t) from exc
        dur = time.perf_counter_ns() - t0
        rt.tick_ns += dur
        rt.ran = True
        if out:
            self._write(rt, out, t)
        for cb in self._after:
            cb(rt.id, kind, t, inputs, out, dur)
        return out

    def _check_breakpoints(self, kind, rt):
        for bp in self.breakpoints:
            if bp.node != rt.id or not bp.enabled:
                continue
            phase = bp.phase or (STEP if rt.ft else UPDATE)
            if phase != kind:
                continue
            inputs = self._gather(rt) if kind != OUTPUT else {}
            if bp.matches(inputs, self.t):
                return self._hit(bp, rt.id, kind, inputs)
        return None

    def _hit(self, bp, node, kind, inputs):
        bp.hits += 1
        if bp.once:
            bp.enabled = False
        hit = BreakHit(bp, node, kind, self.t, self.tick, inputs)
        self.break_hit = hit
        self.paused = True
        if self.recorder is not None:
            self.recorder.event(self.t, "breakpoint", str(hit), node, breakpoint=bp.id)
        return hit

    def _advance(self, single=False):
        # execute from the cursor until the end of the step (or one action if single)
        if not self.initialized:
            self.reset()
        if not self._in_tick:
            self._begin_tick()
            if self.breakpoints and self._bp_skip != (self.tick, -1):
                for bp in self.breakpoints:
                    if bp.node is None and bp.enabled and bp.matches({}, self.t):
                        self._bp_skip = (self.tick, -1)
                        return self._hit(bp, None, "tick", {})
        actions = self._actions
        k = self.tick
        executed = None
        while self._pc < len(actions):
            kind, rt = actions[self._pc]
            if k % rt.ticks:
                self._pc += 1
                continue
            if executed is not None:
                return executed          # single step: stop before the next due action
            if self.breakpoints and self._bp_skip != (k, self._pc):
                hit = self._check_breakpoints(kind, rt)
                if hit is not None:
                    self._bp_skip = (k, self._pc)
                    return hit
            out = self._run_action(kind, rt)
            self._pc += 1
            if single:
                executed = NodeStep(rt.id, kind, self.t, k, out)
        self._end_tick()
        if executed is not None:
            executed.step_complete = True
        return executed

    # ------------------------------------------------------------------ public stepping
    def step(self):
        """Run one base step (or its remainder after a breakpoint / step_node).

        Returns None, or a BreakHit if a breakpoint stopped the step (executor is paused then;
        the next step()/run()/resume() continues with the node at the breakpoint)."""
        if self.break_hit is not None:
            self.break_hit = None
        return self._advance()

    def step_node(self):
        """Debugger single step: execute exactly one node action. Returns NodeStep or BreakHit."""
        if self.break_hit is not None:
            self.break_hit = None
        return self._advance(single=True)

    def run(self, t_end=None, stop=None, max_steps=None):
        """Run until t_end (inclusive), a stop condition, a breakpoint or pause().

        stop: callable(executor) -> falsy | True | str (reason); checked after every base step.
        Continues from the current state (call reset() for a fresh start)."""
        if not self.initialized:
            self.reset()
        self.paused = False
        self.break_hit = None
        self._stop_request = None
        k_end = None if t_end is None else int(math.floor(t_end / self.graph.base_dt + 1e-9))
        if k_end is None and max_steps is None and stop is None:
            raise ValueError("run() braucht t_end, max_steps oder eine Stoppbedingung")
        wall0 = time.perf_counter()
        start_tick = self.tick
        reason, message, hit = "t_end", "", None
        while True:
            if k_end is not None and self.tick > k_end and not self._in_tick:
                break
            if max_steps is not None and self.tick - start_tick >= max_steps and not self._in_tick:
                reason, message = "max_steps", f"{max_steps} Schritte ausgeführt"
                break
            if self.paused:
                reason, message = "pause", "angehalten"
                break
            res = self._advance()
            if isinstance(res, BreakHit):
                reason, message, hit = "breakpoint", str(res), res
                break
            if self._stop_request:
                reason, message = "request", str(self._stop_request)
                self._event("stop", message)
                break
            if stop is not None:
                r = stop(self)
                if r:
                    reason, message = "stop", r if isinstance(r, str) else "Stoppbedingung erfüllt"
                    self._event("stop", message)
                    break
        res = RunResult(self.t, self.tick - start_tick, reason, message, time.perf_counter() - wall0, hit,
                        self.recorder, self.profiler.report() if self.profiler.enabled else {}, self.graph.base_dt)
        return res

    def advance(self, wall_dt):
        """Real-time mode: run as many base steps as fit into wall_dt * realtime_factor.

        Returns the number of steps executed. Backlog beyond max_steps_per_advance is dropped
        (counted in realtime_overruns) so that a slow model does not spiral."""
        if not self.initialized:
            self.reset()
        if self.paused:
            return 0
        self._rt_accum += max(0.0, float(wall_dt)) * self.realtime_factor
        dt = self.graph.base_dt
        n = int(self._rt_accum / dt + 1e-9)
        if n > self.max_steps_per_advance:
            self.realtime_overruns += 1
            n = self.max_steps_per_advance
            self._rt_accum = n * dt
        done = 0
        for _ in range(n):
            res = self._advance()
            done += 1
            if isinstance(res, BreakHit) or self.paused or self._stop_request:
                self._rt_accum = 0.0
                return done
        self._rt_accum -= done * dt
        return done

    def _event(self, kind, message, node=None, **data):
        if self.recorder is not None:
            self.recorder.event(self.t, kind, message, node, **data)

    # ------------------------------------------------------------------ hot reload
    def check_reload(self, force=False):
        """Poll custom-node sources (mtime) and hot-reload changed nodes. Returns ReloadEvents."""
        if self.reloader is None:
            from .hot_reload import HotReloader
            self.reloader = HotReloader(self.graph, executor=self)
        events = self.reloader.check(force=force)
        for ev in events:
            self._event("reload", ev.message, ev.node, ok=ev.ok, ports_changed=ev.ports_changed)
        return events

    def close(self):
        for node in self.graph.nodes.values():
            fn = getattr(node.instance, "close", None)
            if callable(fn):
                fn()
