"""Component base class.

A component is the unit of the open vehicle architecture: native algorithms, custom
nodes (Python/C++/Rust), MATLAB function blocks and simple signal blocks all share this
interface, so they are exchangeable in the graph editor and the executor.

    class MyController(Component):
        KIND, NAME, VERSION = "tracking_controller", "my_controller", "1.0.0"
        INPUTS = {"ego": "EgoState", "trajectory": "PlannedTrajectory"}
        OUTPUTS = {"command": "ControlCommand"}
        PARAMS = MyParams                     # dataclass, fields created with vdsim.core.parameters.param()
        PERIOD = 0.01                         # s, None = every executor step

        def reset(self, context): ...
        def step(self, t, inputs):            # inputs: dict port -> value (None if not yet available)
            return {"command": ControlCommand(...)}

Components without direct feedthrough (vehicle plants, unit delays) implement
output(t) and update(t, inputs, dt) instead of step(); the executor calls output() of
all such components first, which breaks feedback loops like in Simulink.

Feedback ports (Port(..., feedback=True)) read the value of the previous executor step
and are ignored for the execution order (used for planner <- controller status).
"""

from __future__ import annotations

import copy
from dataclasses import MISSING, asdict, dataclass, fields, is_dataclass

from .knowledge import ComponentDoc


@dataclass
class Port:
    type: str = "Any"
    description: str = ""
    unit: str = ""
    optional: bool = False       # input may stay unconnected
    feedback: bool = False       # input reads the previous step's value (breaks loops)

    def to_dict(self):
        return asdict(self)


def _ports(spec):
    # {"name": "Type"} or {"name": Port(...)} -> {"name": Port}
    out = {}
    for name, value in (spec or {}).items():
        out[name] = value if isinstance(value, Port) else Port(type=value)
    return out


@dataclass
class NoParams:
    pass


class Component:
    KIND = "node"
    NAME = "component"
    VERSION = "1.0.0"
    API_VERSION = 1
    LABEL = ""                 # display name (German)
    CATEGORY = ""              # palette group in the graph editor
    INPUTS = {}
    OUTPUTS = {}
    PARAMS = NoParams
    PERIOD = None
    DIRECT_FEEDTHROUGH = True
    LANGUAGE = "python"        # python / cpp / rust / matlab
    DOC = ComponentDoc()

    def __init__(self, params=None, **overrides):
        self.params = self.make_params(params, **overrides)
        self.context = None
        self.signals = {}          # named scalar signals for logging / scopes
        self.instance_name = self.NAME

    # ------------------------------------------------------------------ parameters
    @classmethod
    def make_params(cls, params=None, **overrides):
        p_cls = cls.PARAMS or NoParams
        if params is None:
            p = p_cls()
        elif is_dataclass(params) and not isinstance(params, type):
            p = copy.deepcopy(params)
        elif isinstance(params, dict):
            p = params_from_dict(p_cls, params)
        else:
            raise TypeError(f"parameters of {cls.NAME} must be a dict or {p_cls.__name__}")
        for key, value in overrides.items():
            set_param(p, key, value)
        return p

    # ------------------------------------------------------------------ ports
    @classmethod
    def input_ports(cls):
        return _ports(cls.INPUTS)

    @classmethod
    def output_ports(cls):
        return _ports(cls.OUTPUTS)

    def ports(self):
        # instance level (custom nodes may define ports dynamically)
        return self.input_ports(), self.output_ports()

    # ------------------------------------------------------------------ lifecycle
    def reset(self, context):
        self.context = context

    def step(self, t, inputs):
        raise NotImplementedError

    def output(self, t):
        # non-feedthrough components: outputs from the internal state only
        raise NotImplementedError

    def update(self, t, inputs, dt):
        # non-feedthrough components: advance the internal state by dt
        raise NotImplementedError

    # ------------------------------------------------------------------ hot reload / versioning
    def get_state(self):
        # state transferred to the new instance on hot reload
        return {k: v for k, v in self.__dict__.items() if k not in ("params", "context")}

    def set_state(self, state):
        for key, value in state.items():
            if key in self.__dict__:
                self.__dict__[key] = value

    # ------------------------------------------------------------------ description
    @classmethod
    def spec(cls):
        return f"{cls.KIND}/{cls.NAME}@{cls.VERSION}"

    @classmethod
    def describe(cls):
        return {
            "kind": cls.KIND, "name": cls.NAME, "version": cls.VERSION, "api_version": cls.API_VERSION,
            "label": cls.LABEL or cls.NAME, "category": cls.CATEGORY or cls.KIND, "language": cls.LANGUAGE,
            "period": cls.PERIOD, "direct_feedthrough": cls.DIRECT_FEEDTHROUGH,
            "inputs": {k: p.to_dict() for k, p in cls.input_ports().items()},
            "outputs": {k: p.to_dict() for k, p in cls.output_ports().items()},
            "params": params_schema(cls.PARAMS or NoParams),
            "doc": (cls.DOC or ComponentDoc()).to_dict(),
            "module": cls.__module__, "class": cls.__qualname__,
        }


# ---------------------------------------------------------------------------- parameter helpers
def params_schema(p_cls):
    # GUI/API description of a parameter dataclass (label, unit, limits from field metadata)
    out = []
    for f in fields(p_cls):
        default = f.default if f.default is not MISSING else (f.default_factory() if f.default_factory is not MISSING else None)
        meta = dict(f.metadata)
        entry = {"name": f.name, "default": default if not is_dataclass(default) else asdict(default),
                 "type": type(default).__name__, "label": meta.get("label", f.name), "unit": meta.get("unit", "")}
        for key in ("min", "max", "step", "choices", "description"):
            if key in meta:
                entry[key] = meta[key]
        out.append(entry)
    return out


def params_from_dict(p_cls, data):
    p = p_cls()
    for key, value in (data or {}).items():
        set_param(p, key, value)
    return p


def set_param(p, dotted, value):
    # "cost.k_jerk" style access into nested parameter dataclasses
    parts = dotted.split(".")
    obj = p
    for part in parts[:-1]:
        obj = getattr(obj, part)
    name = parts[-1]
    if not hasattr(obj, name):
        raise AttributeError(f"unknown parameter '{dotted}' for {type(p).__name__}")
    current = getattr(obj, name)
    if is_dataclass(current) and isinstance(value, dict):
        for k, v in value.items():
            set_param(current, k, v)
        return
    if isinstance(current, bool):
        value = bool(value)
    elif isinstance(current, int) and not isinstance(value, bool):
        value = int(value) if float(value).is_integer() else float(value)
    elif isinstance(current, float):
        value = float(value)
    setattr(obj, name, value)


def params_to_dict(p):
    return asdict(p) if is_dataclass(p) else dict(p or {})
