"""tracking_controller/composite: combination of a lateral and a longitudinal tracking controller.

    params lateral="pure_pursuit" | "stanley" | "lqr" | "mpc" | any tracking_controller spec,
           longitudinal="ff_fb" | "pid" | "pi" | "acc" | "speed_pi" | ...

Steering from the lateral, acceleration from the longitudinal controller; the status takes the lateral
errors from the lateral and e_t / e_v from the longitudinal controller.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.parameters import param
from ..framework.component import Port
from ..framework.knowledge import ComponentDoc
from ..framework.layers import TrackingControllerBase
from ..framework.plugins import component, create_component


def _spec(name):
    return name if "/" in name or ":" in name else f"tracking_controller/{name}"


@dataclass
class CompositeParams:
    lateral: str = param("stanley", "", "Querregler")
    longitudinal: str = param("ff_fb", "", "Längsregler")
    lateral_params: dict = field(default_factory=dict, metadata={"label": "Parameter Querregler", "unit": ""})
    longitudinal_params: dict = field(default_factory=dict, metadata={"label": "Parameter Längsregler", "unit": ""})


@component
class CompositeController(TrackingControllerBase):
    NAME, VERSION = "composite", "1.0.0"
    LABEL = "Kombination Quer- + Längsregler"
    PARAMS = CompositeParams
    INPUTS = {"ego": Port("EgoState"), "trajectory": Port("PlannedTrajectory"),
              "objects": Port("ObjectList", "Objekte (für ACC)", optional=True)}
    DOC = ComponentDoc(summary="Kombiniert einen beliebigen Quer- und Längsregler zu einem Trackingregler.",
                       purpose="Klassische entkoppelte Quer-/Längsregelung als Vergleich zur gekoppelten Werling-"
                               "Regelung.", assumptions=["Quer- und Längsdynamik entkoppelt"],
                       limitations=["Kopplung (Kammscher Kreis) unberücksichtigt"], references=["rajamani2012"],
                       validation=["tests/stabilization/test_stabilization_classic.py"], concepts=["composite"],
                       expert="Stabilität folgt aus den Teilreglern nur bei schwacher Kopplung.")

    def __init__(self, params=None, **overrides):
        super().__init__(params, **overrides)
        p = self.params
        self.lat = create_component(_spec(p.lateral), {"with_speed_control": False, **p.lateral_params}
                                    if p.lateral in ("pure_pursuit", "stanley", "lqr", "mpc") else p.lateral_params)
        self.lon = create_component(_spec(p.longitudinal), p.longitudinal_params)

    def reset(self, context):
        super().reset(context)
        self.lat.reset(context)
        self.lon.reset(context)

    def step(self, t, inputs):
        lat = self.lat.step(t, inputs)
        lon = self.lon.step(t, inputs)
        cmd, st = lat["command"], lat["status"]
        if cmd is None:
            return lat
        lcmd, lst = lon["command"], lon["status"]
        if lcmd is not None:
            cmd.accel = lcmd.accel
            cmd.force = lcmd.force
            cmd.info = {**lcmd.info, **cmd.info}
        if lst is not None:
            st.e_t, st.e_v, st.e_t_dot = lst.e_t, lst.e_v, lst.e_t_dot
        st.active_controller = f"{self.lat.NAME}+{self.lon.NAME}"
        cmd.controller = st.active_controller
        self.signals = {**self.lat.signals, **self.lon.signals}
        return {"command": cmd, "status": st}
