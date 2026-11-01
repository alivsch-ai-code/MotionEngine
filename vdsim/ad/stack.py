"""The automated-driving stack: which component runs in which layer, and how they are wired.

A stack is a dict  layer -> {"component": spec, "params": {...}, "period": s}. The default
stack realizes the complete concept of Werling (2011): rule-based behavior, the
Werling trajectory planner (10 Hz) and the bi-level stabilization with the three
complementary tracking controllers (100 Hz).

    Perception -> Prediction -> Behavior Planning -> Trajectory Planning -> Vehicle Control
        -> Vehicle Dynamics -> Actuators -> Vehicle Plant

`build_graph(stack)` turns it into the graph format of docs/specs/contracts.md, which the
executor runs and the graph editor displays. Every layer can be replaced by another native
component or a custom node (python:/rust:/cpp:/matlab: spec) with the same ports.
"""

from __future__ import annotations

import copy

LAYERS = ("world", "perception", "prediction", "behavior", "planner", "controller", "dynamics", "actuators", "plant")

LAYER_TITLES = {
    "world": "Szenario / Welt",
    "perception": "Perception",
    "prediction": "Prediction",
    "behavior": "Behavior Planning",
    "planner": "Trajectory Planning",
    "controller": "Vehicle Control",
    "dynamics": "Vehicle Dynamics",
    "actuators": "Actuators",
    "plant": "Fahrzeug (Strecke)",
}

DEFAULT_STACK = {
    "world": {"component": "world/scenario_engine"},
    "perception": {"component": "perception/object_sensor"},
    "prediction": {"component": "predictor/constant_acceleration"},
    "behavior": {"component": "behavior_planner/rule_based", "period": 0.1},
    "planner": {"component": "trajectory_planner/werling", "period": 0.1},
    "controller": {"component": "tracking_controller/werling_bilevel", "period": 0.01},
    "dynamics": {"component": "vehicle_dynamics/split_range"},
    "actuators": {"component": "actuator/steering_powertrain"},
    "plant": {"component": "vehicle_plant/vehicle_model", "params": {"model": "werling_desm"}},
}

# signal flow; the ego state for the algorithms comes from the perception's ego estimate
CONNECTIONS = [
    ("plant.ego", "world.ego"),
    ("plant.ego", "perception.ego"),
    ("world.world", "perception.world"),
    ("world.world", "prediction.world"),
    ("world.world", "behavior.world"),
    ("perception.objects", "prediction.objects"),
    ("perception.objects", "behavior.objects"),
    ("perception.ego_estimate", "behavior.ego"),
    ("perception.ego_estimate", "planner.ego"),
    ("perception.ego_estimate", "controller.ego"),
    ("perception.ego_estimate", "dynamics.ego"),
    ("plant.ego", "actuators.ego"),
    ("prediction.prediction", "behavior.prediction"),
    ("prediction.prediction", "planner.prediction"),
    ("behavior.behavior", "planner.behavior"),
    ("planner.trajectory", "controller.trajectory"),
    ("planner.trajectory", "behavior.trajectory"),     # feedback: danger indicator (Werling 3.6)
    ("controller.status", "planner.status"),           # feedback: re-initialization (bi-level stabilization)
    ("controller.command", "dynamics.command"),
    ("dynamics.demand", "actuators.demand"),
    ("actuators.control", "plant.control"),
]

# editor layout following the chain of the specification
POSITIONS = {
    "world": (40, 60), "perception": (300, 60), "prediction": (560, 60), "behavior": (820, 60),
    "planner": (1080, 60), "controller": (1080, 300), "dynamics": (820, 300), "actuators": (560, 300),
    "plant": (300, 300),
}


def merge_stack(*stacks):
    # later stacks override earlier ones; params are merged recursively
    out = copy.deepcopy(DEFAULT_STACK)
    for stack in stacks:
        for layer, spec in (stack or {}).items():
            if layer not in out:
                out[layer] = {}
            if isinstance(spec, str):
                spec = {"component": spec}
            spec = copy.deepcopy(spec)
            if "component" in spec and spec["component"] != out[layer].get("component"):
                out[layer] = {"component": spec["component"], "params": {}, **({"period": out[layer]["period"]}
                                                                                if "period" in out[layer] else {})}
            params = spec.pop("params", None)
            out[layer].update(spec)
            if params:
                out[layer]["params"] = _merge_dict(out[layer].get("params", {}), params)
    return out


def _merge_dict(base, extra):
    base = copy.deepcopy(base or {})
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _merge_dict(base[k], v)
        else:
            base[k] = v
    return base


def build_graph(stack=None, name="ad_stack", base_dt=0.01, extra_nodes=None, extra_connections=None):
    # stack dict -> graph dict (contracts.md section 4)
    stack = merge_stack(stack)
    nodes = []
    for layer in LAYERS:
        spec = stack.get(layer)
        if not spec:
            continue
        node = {"id": layer, "component": spec["component"], "params": copy.deepcopy(spec.get("params", {})),
                "label": LAYER_TITLES.get(layer, layer), "position": list(POSITIONS.get(layer, (0, 0)))}
        if spec.get("period"):
            node["period"] = spec["period"]
        nodes.append(node)
    present = {n["id"] for n in nodes}
    conns = [{"from": a, "to": b} for a, b in CONNECTIONS
             if a.split(".")[0] in present and b.split(".")[0] in present]
    nodes += list(extra_nodes or [])
    conns += list(extra_connections or [])
    return {"format_version": 1, "name": name, "base_dt": base_dt, "nodes": nodes, "connections": conns,
            "metadata": {"layers": {layer: stack[layer]["component"] for layer in LAYERS if layer in stack}}}
