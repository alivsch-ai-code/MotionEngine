"""Flat float64 codecs used by native nodes.

The layouts of docs/specs/contracts.md (section 5) are implemented in
vdsim.framework.types.encode/decode and used unchanged. This module adds layouts for
types that the framework has no codec for yet but that native nodes of the standard
layers need (marked RUNTIME_EXTENSIONS; candidates for vdsim.framework.types):

    ControllerStatus  [t, e_t, e_n, e_theta, e_v, e_t_dot, e_n_dot, reinit_request, lookahead]
    ControlInput      [steer_front, steer_rear, drive_torque x4, brake_torque x4, roll_moment, damper_force x4]
    ActuatorCommand   [t, steer_angle, steer_rate, steer_rear, drive_torque x4, brake_torque x4]
    WorldState        decode of the ObjectList layout (framework encodes it, but does not decode)
"""

from __future__ import annotations

import numpy as np

from ..framework import types as T

STATUS_FIELDS = ("t", "e_t", "e_n", "e_theta", "e_v", "e_t_dot", "e_n_dot", "reinit_request", "lookahead")
CONTROL_INPUT_LAYOUT = (("steer_front", 1), ("steer_rear", 1), ("drive_torque", 4), ("brake_torque", 4),
                        ("roll_moment", 1), ("damper_force", 4))
ACTUATOR_LAYOUT = (("t", 1), ("steer_angle", 1), ("steer_rate", 1), ("steer_rear", 1), ("drive_torque", 4),
                   ("brake_torque", 4))
TRAJECTORY_HEADER = ("n", "direction", "reference_point", "cost", "valid")
PREDICTED_OBJECT_HEADER = ("id", "type", "length", "width", "k")
RUNTIME_EXTENSIONS = ("ControllerStatus", "ControlInput", "ActuatorCommand", "WorldState")
FRAMEWORK_CODECS = ("float", "bool", "Vector", "EgoState", "ControlCommand", "PlannedTrajectory", "ObjectList",
                    "Prediction", "ReferenceLine")
CODEC_TYPES = FRAMEWORK_CODECS + RUNTIME_EXTENSIONS

# initial output buffer capacity per type (grown on demand)
DEFAULT_CAPACITY = {"float": 1, "bool": 1, "Vector": 64, "EgoState": len(T.EGO_FIELDS),
                    "ControlCommand": len(T.COMMAND_FIELDS), "ControllerStatus": len(STATUS_FIELDS),
                    "ControlInput": 15, "ActuatorCommand": 12,
                    "PlannedTrajectory": 5 + 200 * len(T.TRAJECTORY_FIELDS),
                    "ObjectList": 1 + 64 * len(T.OBJECT_FIELDS), "WorldState": 1 + 64 * len(T.OBJECT_FIELDS),
                    "Prediction": 1 + 32 * (5 + 50 * 5), "ReferenceLine": 1 + 1000 * 6}


def has_codec(type_name):
    return type_name in CODEC_TYPES


def _pack(value, layout):
    out = []
    for name, n in layout:
        v = getattr(value, name)
        if n == 1:
            out.append(float(v))
        else:
            arr = np.asarray(v, dtype=float).ravel()
            out.extend(list(arr[:n]) + [0.0] * (n - min(n, arr.size)))
    return np.asarray(out, dtype=float)


def _unpack(arr, layout):
    vals, i = {}, 0
    for name, n in layout:
        if n == 1:
            vals[name] = float(arr[i]) if i < arr.size else 0.0
        else:
            chunk = arr[i:i + n]
            vals[name] = np.concatenate([chunk, np.zeros(n - chunk.size)]) if chunk.size < n else chunk.copy()
        i += n
    return vals


def encode(type_name, value):
    if value is None:
        return np.zeros(0)
    if type_name == "ControllerStatus":
        return np.array([float(getattr(value, f)) for f in STATUS_FIELDS])
    if type_name == "ControlInput":
        return _pack(value, CONTROL_INPUT_LAYOUT)
    if type_name == "ActuatorCommand":
        return _pack(value, ACTUATOR_LAYOUT)
    if type_name == "PlannedTrajectory":
        # same layout as framework.types.encode, without rebuilding arrays() per field
        n = len(value.t)
        out = np.empty(5 + n * len(T.TRAJECTORY_FIELDS))
        out[:5] = (n, value.direction, 0.0 if value.reference_point == "cog" else 1.0, value.cost, float(value.valid))
        if n:
            body = out[5:].reshape(n, len(T.TRAJECTORY_FIELDS))
            for i, f in enumerate(T.TRAJECTORY_FIELDS):
                body[:, i] = getattr(value, f)
        return out
    return np.ascontiguousarray(T.encode(type_name, value), dtype=float)


def decode(type_name, arr):
    arr = np.asarray(arr, dtype=float)
    if type_name == "ControllerStatus":
        vals = {f: float(v) for f, v in zip(STATUS_FIELDS, arr)}
        vals["reinit_request"] = bool(vals.get("reinit_request", 0.0))
        return T.ControllerStatus(**vals)
    if type_name == "ControlInput":
        return T.ControlInput(**_unpack(arr, CONTROL_INPUT_LAYOUT))
    if type_name == "ActuatorCommand":
        return T.ActuatorCommand(**_unpack(arr, ACTUATOR_LAYOUT))
    if type_name == "WorldState":
        return T.WorldState(objects=T.decode("ObjectList", arr).objects)
    return T.decode(type_name, arr)
