"""Basic signal blocks (Simulink-like) as regular components (KIND "node").

Sources: Constant, Step, Sine, Ramp, Clock, TypedDefault    Math: Gain, Sum, Product, Saturation,
Switch, Mux, Demux    Discrete/continuous: UnitDelay, Integrator, LowPass (PT1), RateLimiter
Sinks: Scope, Probe

Discrete blocks use the sample time of the node (executor sets `sample_time` = node period,
default base_dt). UnitDelay and Integrator have no direct feedthrough (they break loops).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..core.parameters import param
from ..framework.component import Component, Port
from ..framework.knowledge import ComponentDoc, trace
from ..framework.plugins import component
from ..framework.types import TYPES

SOURCES, MATH, DISCRETE, SINKS, ROUTING = "Quellen", "Mathematik", "Diskret", "Senken", "Signalführung"


class Block(Component):
    KIND = "node"

    def dt(self):
        st = getattr(self, "sample_time", None)
        if st:
            return st
        return getattr(self.context, "dt", None) or 0.01


def _num_ports(prefix, n, type_name="float", optional=False):
    return {f"{prefix}{i + 1}": Port(type_name, optional=optional) for i in range(max(1, int(n)))}


# ---------------------------------------------------------------------------- sources
@dataclass
class ConstantParams:
    value: float = param(1.0, "", "Wert")


@component
class Constant(Block):
    NAME, LABEL, CATEGORY = "constant", "Konstante", SOURCES
    OUTPUTS = {"y": Port("float")}
    PARAMS = ConstantParams
    DOC = ComponentDoc(summary="Konstanter Wert y = c.")

    def step(self, t, inputs):
        return {"y": self.params.value}


@dataclass
class StepParams:
    t_step: float = param(1.0, "s", "Sprungzeit", min=0.0)
    initial: float = param(0.0, "", "Anfangswert")
    final: float = param(1.0, "", "Endwert")


@component
class Step(Block):
    NAME, LABEL, CATEGORY = "step", "Sprung", SOURCES
    OUTPUTS = {"y": Port("float")}
    PARAMS = StepParams
    DOC = ComponentDoc(summary="Sprungfunktion: Anfangswert für t < t_step, sonst Endwert.")

    def step(self, t, inputs):
        p = self.params
        return {"y": p.final if t >= p.t_step - 1e-12 else p.initial}


@dataclass
class SineParams:
    amplitude: float = param(1.0, "", "Amplitude")
    frequency: float = param(1.0, "Hz", "Frequenz", min=0.0)
    phase: float = param(0.0, "rad", "Phase")
    offset: float = param(0.0, "", "Offset")


@component
class Sine(Block):
    NAME, LABEL, CATEGORY = "sine", "Sinus", SOURCES
    OUTPUTS = {"y": Port("float")}
    PARAMS = SineParams
    DOC = ComponentDoc(summary="y = A sin(2π f t + φ) + Offset.")

    def step(self, t, inputs):
        p = self.params
        return {"y": p.amplitude * math.sin(2.0 * math.pi * p.frequency * t + p.phase) + p.offset}


@dataclass
class RampParams:
    slope: float = param(1.0, "1/s", "Steigung")
    t_start: float = param(0.0, "s", "Startzeit", min=0.0)
    initial: float = param(0.0, "", "Anfangswert")


@component
class Ramp(Block):
    NAME, LABEL, CATEGORY = "ramp", "Rampe", SOURCES
    OUTPUTS = {"y": Port("float")}
    PARAMS = RampParams
    DOC = ComponentDoc(summary="Rampe: y = y0 + m (t - t_start) ab t_start.")

    def step(self, t, inputs):
        p = self.params
        return {"y": p.initial + p.slope * max(0.0, t - p.t_start)}


@component
class Clock(Block):
    NAME, LABEL, CATEGORY = "clock", "Uhr", SOURCES
    OUTPUTS = {"t": Port("float", "Simulationszeit", "s")}
    DOC = ComponentDoc(summary="Gibt die Simulationszeit aus.")

    def step(self, t, inputs):
        return {"t": t}


@dataclass
class TypedDefaultParams:
    type_name: str = param("ObjectList", "", "Datentyp")


@component
class TypedDefault(Block):
    NAME, LABEL, CATEGORY = "typed_default", "Standardwert", SOURCES
    OUTPUTS = {"y": Port("Any")}
    PARAMS = TypedDefaultParams
    DOC = ComponentDoc(summary="Liefert den Standardwert eines Datentyps (z. B. leere ObjectList).",
                       purpose="Platzhalter für noch nicht vorhandene Ebenen beim Aufbau eines Graphen.")

    def ports(self):
        return {}, {"y": Port(self.params.type_name, "Standardwert")}

    def reset(self, context):
        super().reset(context)
        py = TYPES.get(self.params.type_name, object)
        self._value = 0.0 if py is float else (False if py is bool else (np.zeros(0) if py is np.ndarray else
                                                                          (None if py is object else py())))

    def step(self, t, inputs):
        if isinstance(getattr(self._value, "t", None), float):
            self._value.t = t
        return {"y": self._value}


# ---------------------------------------------------------------------------- math
@dataclass
class GainParams:
    k: float = param(1.0, "", "Verstärkung")


@component
class Gain(Block):
    NAME, LABEL, CATEGORY = "gain", "Verstärkung", MATH
    INPUTS = {"u": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = GainParams
    DOC = ComponentDoc(summary="y = k · u (Skalar oder Vektor).")

    def step(self, t, inputs):
        u = inputs["u"]
        return {"y": None if u is None else self.params.k * (np.asarray(u) if isinstance(u, list) else u)}


@dataclass
class SumParams:
    signs: str = param("++", "", "Vorzeichen (z. B. '+-')")


@component
class Sum(Block):
    NAME, LABEL, CATEGORY = "sum", "Summe", MATH
    INPUTS = {"u1": Port("float"), "u2": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = SumParams
    DOC = ComponentDoc(summary="Summe der Eingänge mit Vorzeichen aus dem Parameter 'signs'.")

    def _signs(self):
        s = [c for c in self.params.signs if c in "+-"]
        return s or ["+"]

    def ports(self):
        return _num_ports("u", len(self._signs())), {"y": Port("float")}

    def step(self, t, inputs):
        acc = 0.0
        for i, sgn in enumerate(self._signs()):
            u = inputs.get(f"u{i + 1}")
            if u is None:
                continue
            acc = acc + u if sgn == "+" else acc - u
        return {"y": acc}


@dataclass
class ProductParams:
    ops: str = param("**", "", "Operationen (z. B. '*/')")


@component
class Product(Block):
    NAME, LABEL, CATEGORY = "product", "Produkt", MATH
    INPUTS = {"u1": Port("float"), "u2": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = ProductParams
    DOC = ComponentDoc(summary="Produkt bzw. Quotient der Eingänge ('*' multipliziert, '/' dividiert).")

    def _ops(self):
        s = [c for c in self.params.ops if c in "*/"]
        return s or ["*"]

    def ports(self):
        return _num_ports("u", len(self._ops())), {"y": Port("float")}

    def step(self, t, inputs):
        acc = 1.0
        for i, op in enumerate(self._ops()):
            u = inputs.get(f"u{i + 1}")
            if u is None:
                continue
            acc = acc * u if op == "*" else acc / u
        return {"y": acc}


@dataclass
class SaturationParams:
    lower: float = param(-1.0, "", "Untere Grenze")
    upper: float = param(1.0, "", "Obere Grenze")


@component
class Saturation(Block):
    NAME, LABEL, CATEGORY = "saturation", "Begrenzung", MATH
    INPUTS = {"u": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = SaturationParams
    DOC = ComponentDoc(summary="Begrenzt u auf [lower, upper].")

    def step(self, t, inputs):
        u = inputs["u"]
        if u is None:
            return {}
        return {"y": np.clip(u, self.params.lower, self.params.upper) if isinstance(u, np.ndarray)
                else min(max(u, self.params.lower), self.params.upper)}


@dataclass
class SwitchParams:
    threshold: float = param(0.0, "", "Schwelle")


@component
class Switch(Block):
    NAME, LABEL, CATEGORY = "switch", "Schalter", ROUTING
    INPUTS = {"u1": Port("Any"), "control": Port("float"), "u2": Port("Any")}
    OUTPUTS = {"y": Port("Any")}
    PARAMS = SwitchParams
    DOC = ComponentDoc(summary="y = u1, falls control ≥ Schwelle, sonst u2.")

    def step(self, t, inputs):
        c = inputs["control"]
        return {"y": inputs["u1"] if c is not None and c >= self.params.threshold else inputs["u2"]}


@dataclass
class MuxParams:
    n: int = param(2, "", "Anzahl Eingänge", min=1, max=64)


@component
class Mux(Block):
    NAME, LABEL, CATEGORY = "mux", "Mux", ROUTING
    INPUTS = {"u1": Port("float"), "u2": Port("float")}
    OUTPUTS = {"y": Port("Vector")}
    PARAMS = MuxParams
    DOC = ComponentDoc(summary="Fasst n Skalare zu einem Vektor zusammen.")

    def ports(self):
        return _num_ports("u", self.params.n, optional=True), {"y": Port("Vector")}

    def step(self, t, inputs):
        n = max(1, int(self.params.n))
        return {"y": np.array([np.nan if inputs.get(f"u{i + 1}") is None else float(inputs[f"u{i + 1}"])
                               for i in range(n)])}


@component
class Demux(Block):
    NAME, LABEL, CATEGORY = "demux", "Demux", ROUTING
    INPUTS = {"u": Port("Vector")}
    OUTPUTS = {"y1": Port("float"), "y2": Port("float")}
    PARAMS = MuxParams
    DOC = ComponentDoc(summary="Zerlegt einen Vektor in n Skalare (fehlende Elemente: NaN).")

    def ports(self):
        return {"u": Port("Vector")}, _num_ports("y", self.params.n)

    def step(self, t, inputs):
        u = inputs["u"]
        n = max(1, int(self.params.n))
        arr = np.atleast_1d(np.asarray(u, dtype=float)) if u is not None else np.zeros(0)
        return {f"y{i + 1}": float(arr[i]) if i < arr.size else np.nan for i in range(n)}


# ---------------------------------------------------------------------------- discrete / dynamic
@dataclass
class DelayParams:
    initial: float = param(0.0, "", "Anfangswert")


@component
class UnitDelay(Block):
    NAME, LABEL, CATEGORY = "unit_delay", "Verzögerung (z⁻¹)", DISCRETE
    INPUTS = {"u": Port("Any")}
    OUTPUTS = {"y": Port("Any")}
    PARAMS = DelayParams
    DIRECT_FEEDTHROUGH = False
    DOC = ComponentDoc(summary="Verzögert das Eingangssignal um einen Abtastschritt: y_k = u_{k-1}.",
                       purpose="Bricht algebraische Schleifen auf (kein Durchgriff).")

    def reset(self, context):
        super().reset(context)
        self.state = self.params.initial

    def output(self, t):
        return {"y": self.state}

    def update(self, t, inputs, dt):
        if inputs["u"] is not None:
            self.state = inputs["u"]


@dataclass
class IntegratorParams:
    k: float = param(1.0, "", "Verstärkung")
    initial: float = param(0.0, "", "Anfangswert")
    lower: float = param(-math.inf, "", "Untere Grenze")
    upper: float = param(math.inf, "", "Obere Grenze")


@component
class Integrator(Block):
    NAME, LABEL, CATEGORY = "integrator", "Integrator", DISCRETE
    INPUTS = {"u": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = IntegratorParams
    DIRECT_FEEDTHROUGH = False
    DOC = ComponentDoc(summary="Zeitdiskreter Integrator (explizites Euler-Verfahren) mit Begrenzung.",
                       theory="$y_{k+1} = \\mathrm{sat}(y_k + K\\,T_s\\,u_k)$", concepts=["discrete_blocks"])

    def reset(self, context):
        super().reset(context)
        self.state = float(self.params.initial)

    def output(self, t):
        return {"y": self.state}

    @trace("lee_seshia2017", section="2", concept="discrete_blocks", note="explizites Euler-Verfahren")
    def update(self, t, inputs, dt):
        u = inputs["u"]
        if u is None:
            return
        p = self.params
        self.state = min(max(self.state + p.k * dt * u, p.lower), p.upper)


@dataclass
class LowPassParams:
    T: float = param(0.1, "s", "Zeitkonstante", min=0.0)
    K: float = param(1.0, "", "Verstärkung")
    initial: float = param(0.0, "", "Anfangswert")


@component
class LowPass(Block):
    NAME, LABEL, CATEGORY = "lowpass", "Tiefpass (PT1)", DISCRETE
    INPUTS = {"u": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = LowPassParams
    DOC = ComponentDoc(summary="PT1-Glied, exakt diskretisiert (Sprunginvarianz).",
                       theory="$y_k = a\\,y_{k-1} + (1-a)\\,K\\,u_k$, $a = e^{-T_s/T}$", concepts=["discrete_blocks"])

    def reset(self, context):
        super().reset(context)
        self.state = float(self.params.initial)

    @trace("lee_seshia2017", concept="discrete_blocks", note="sprunginvariante Diskretisierung des PT1")
    def step(self, t, inputs):
        u = inputs["u"]
        if u is None:
            return {"y": self.state}
        p = self.params
        a = math.exp(-self.dt() / p.T) if p.T > 0 else 0.0
        self.state = a * self.state + (1.0 - a) * p.K * u
        return {"y": self.state}


@dataclass
class RateLimiterParams:
    rising: float = param(1.0, "1/s", "Max. Anstiegsrate", min=0.0)
    falling: float = param(1.0, "1/s", "Max. Abfallrate", min=0.0)
    initial: float = param(0.0, "", "Anfangswert")


@component
class RateLimiter(Block):
    NAME, LABEL, CATEGORY = "rate_limiter", "Ratenbegrenzer", DISCRETE
    INPUTS = {"u": Port("float")}
    OUTPUTS = {"y": Port("float")}
    PARAMS = RateLimiterParams
    DOC = ComponentDoc(summary="Begrenzt die Änderungsrate des Signals.")

    def reset(self, context):
        super().reset(context)
        self.state = None

    def step(self, t, inputs):
        u = inputs["u"]
        if u is None:
            return {}
        if self.state is None:
            self.state = float(self.params.initial) if self.params.initial is not None else u
        dt = self.dt()
        du = min(max(u - self.state, -self.params.falling * dt), self.params.rising * dt)
        self.state = self.state + du
        return {"y": self.state}


# ---------------------------------------------------------------------------- sinks
@dataclass
class ScopeParams:
    n: int = param(1, "", "Anzahl Eingänge", min=1, max=16)
    max_samples: int = param(100000, "", "Max. Abtastwerte", min=1)


@component
class Scope(Block):
    NAME, LABEL, CATEGORY = "scope", "Scope", SINKS
    INPUTS = {"u1": Port("Any", optional=True)}
    PARAMS = ScopeParams
    DOC = ComponentDoc(summary="Zeichnet seine Eingänge als Zeitreihen auf (data()).")

    def ports(self):
        return _num_ports("u", self.params.n, "Any", optional=True), {}

    def reset(self, context):
        super().reset(context)
        self.t_log = []
        self.logs = {f"u{i + 1}": [] for i in range(max(1, int(self.params.n)))}

    def step(self, t, inputs):
        if len(self.t_log) < self.params.max_samples:
            self.t_log.append(t)
            for k, v in inputs.items():
                self.logs.setdefault(k, []).append(v)
                if isinstance(v, (int, float, np.floating, np.integer)):
                    self.signals[k] = float(v)
        return {}

    def data(self, port="u1"):
        t = np.asarray(self.t_log)
        try:
            return t, np.asarray(self.logs[port], dtype=float)
        except (TypeError, ValueError):
            return t, list(self.logs[port])


@component
class ProbeBlock(Block):
    NAME, LABEL, CATEGORY = "probe", "Messpunkt", SINKS
    INPUTS = {"u": Port("Any")}
    OUTPUTS = {"y": Port("Any")}
    DOC = ComponentDoc(summary="Durchschleifender Messpunkt: y = u, Skalare erscheinen als Signal 'value'.")

    def step(self, t, inputs):
        u = inputs["u"]
        if isinstance(u, (int, float, np.floating, np.integer)):
            self.signals["value"] = float(u)
        return {"y": u}


BLOCKS = [Constant, Step, Sine, Ramp, Clock, TypedDefault, Gain, Sum, Product, Saturation, Switch, Mux, Demux,
          UnitDelay, Integrator, LowPass, RateLimiter, Scope, ProbeBlock]
