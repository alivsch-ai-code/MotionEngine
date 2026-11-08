"""Vehicle model with learned dynamics: exact planar kinematics, accelerations from a neural network.

State [x, y, psi, v_x, v_y, r] as the single-track models; the network returns
[dv_x/dt, dv_y/dt, dr/dt] for the features [v_x, v_y, r, delta, F_x] (vdsim.learning.dataset).
Outside the training envelope the network extrapolates: below v_min the model falls back to the
kinematic single-track relation (no slip), as the physics models do at low speed.
"""

from __future__ import annotations

import numpy as np

from ..core.interfaces import VehicleModel
from ..core.registry import _REGISTRY, register
from ..simulation.vehicle_state import VehicleState
from ..vehicle_models.common import wheel_force_request


class NeuralVehicleModel(VehicleModel):
    state_names = ("x", "y", "psi", "vx", "vy", "r")
    recommended_dt = 0.002
    backend = None          # set by register_neural_model
    model_info = {}
    v_min = 2.0

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0):
        return np.array([x, y, psi, speed, 0.0, 0.0], dtype=float)

    def derivatives(self, t, s, u, env, with_outputs=False):
        p = self.config.vehicle
        x, y, psi, vx, vy, r = s
        fx = float(np.sum(wheel_force_request(u, p, vx)))
        if vx >= self.v_min:
            vx_dot, vy_dot, r_dot = self.backend.predict([[vx, vy, r, u.steer_front, fx]])[0]
        else:
            # kinematic fallback (no tire slip) at very low speed
            vx_dot = fx / p.mass
            r_target = vx * np.tan(u.steer_front) / p.wheelbase
            vy_dot, r_dot = -vy / 0.1, (r_target - r) / 0.1
        c, sn = np.cos(psi), np.sin(psi)
        ds = np.array([vx * c - vy * sn, vx * sn + vy * c, r, vx_dot, vy_dot, r_dot])
        if not with_outputs:
            return ds
        out = {"ax": vx_dot - vy * r, "ay": vy_dot + vx * r, "r": r, "beta": np.arctan2(vy, max(abs(vx), 1.0))}
        return ds, out

    def vehicle_state(self, t, s, out):
        x, y, psi, vx, vy, r = s
        return VehicleState(t=t, x=x, y=y, psi=psi, vx=vx, vy=vy, r=r, ax=out["ax"], ay=out["ay"])


def register_neural_model(model_id, backend, info=None):
    # registry name "neural_<id>": selectable in scenarios, the REST service and the GUI like any vehicle model
    name = f"neural_{model_id}"
    cls = type(f"NeuralVehicleModel_{model_id}", (NeuralVehicleModel,),
               {"backend": backend, "model_info": dict(info or {})})
    _REGISTRY["vehicle_model"].pop(name, None)
    register("vehicle_model", name)(cls)
    return name
