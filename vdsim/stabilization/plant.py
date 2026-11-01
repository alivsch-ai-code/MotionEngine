"""vehicle_plant/vehicle_model: any registered vdsim vehicle model as plant of the AD chain.

The model is integrated with the vdsim solvers in substeps (like vdsim.simulation.Simulator, including
the model's stable_dt). Environment (friction map, wind, optional env.grade) from
context.service("environment"), initial state from context.scenario.ego_initial (dict x, y, psi, v) if
available. Reverse driving needs a model that can drive backwards (werling_kesm, bicycle_kinematic; the
werling_desm only at low speed in its kinematic range).

Disturbances (for tests / examples): params.disturbances = [{"t": 2.0, "duration": 0.3, "fy": 4000.0,
"mz": 0.0, "fx": 0.0}] apply a force / yaw moment at the CoG (models with vy and r states), kick()
changes states instantaneously (impulse).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..core.parameters import param
from ..core.registry import create
from ..framework.knowledge import ComponentDoc
from ..framework.layers import VehiclePlantBase
from ..framework.plugins import component
from ..framework.types import EgoState
from ..simulation.environment import Environment
from ..simulation.solver import create_solver
from ..simulation.vehicle_state import ControlInput
from .common import vehicle_config


@dataclass
class PlantParams:
    model: str = param("werling_desm", "", "Fahrzeugmodell (vdsim vehicle_model)")
    solver: str = param("rk4", "", "Integrator", choices=["euler", "heun", "rk4", "adaptive"])
    dt_model: float = param(0.0, "s", "Modellschrittweite (0: Empfehlung des Modells)", min=0.0)
    x0: float = param(0.0, "m", "Startposition x (falls kein Szenario)")
    y0: float = param(0.0, "m", "Startposition y")
    psi0: float = param(0.0, "rad", "Start-Gierwinkel")
    v0: float = param(0.0, "m/s", "Startgeschwindigkeit (vorzeichenbehaftet)")
    delta0: float = param(0.0, "rad", "Start-Lenkwinkel")
    disturbances: list = param([], "", "Störkräfte [{t, duration, fx, fy, mz}]")


@component
class VehicleModelPlant(VehiclePlantBase):
    NAME, VERSION = "vehicle_model", "1.0.0"
    LABEL = "Fahrzeugmodell (vdsim)"
    PARAMS = PlantParams
    DOC = ComponentDoc(
        summary="Umschließt ein registriertes vdsim-Fahrzeugmodell als Strecke der Wirkkette (ohne Durchgriff).",
        purpose="Beliebige Fahrzeugmodelle (Werling-Entwurfsmodelle, Einspur-, Zweispur-, Mehrkörpermodell) als "
                "Strecke für Reglerentwicklung und Robustheitsuntersuchungen.",
        assumptions=["Stellgrößen über einen Executor-Schritt konstant (Halteglied)"],
        limitations=["Rückwärtsfahrt nur mit werling_kesm, bicycle_kinematic (werling_desm nur langsam)",
                     "Störkräfte nur bei Modellen mit Zuständen vy und r"],
        references=["werling2011"],
        equations=["werling2011:(4.2)", "werling2011:(4.39)"],
        validation=["tests/stabilization/test_stabilization_layers.py"],
        concepts=["vehicle_plant"],
        expert=r"Explizite Integration (Euler/Heun/RK4) mit Teilschritten; die Teilschrittweite ist durch die "
               r"Empfehlung bzw. stable_dt des Modells begrenzt (z. B. DESM: $h<2/\max(\lambda_i)$ mit "
               r"$\lambda\approx(c_v+c_h)/(mv)$), damit RK4 numerisch stabil bleibt.")

    def reset(self, context):
        super().reset(context)
        p = self.params
        self.cfg = vehicle_config(context)
        self.model = create("vehicle_model", p.model, self.cfg)
        env = context.service("environment") if context is not None else None
        self.env = env if env is not None else Environment()
        dt_model = p.dt_model or getattr(self.model, "recommended_dt", 0.002)
        self.dt_model = dt_model
        self.solver = create_solver(p.solver, 1)
        init = {"x": p.x0, "y": p.y0, "psi": p.psi0, "v": p.v0, "delta": p.delta0}
        scen = getattr(context, "scenario", None) if context is not None else None
        ego0 = getattr(scen, "ego_initial", None) if scen is not None else None
        if ego0 is None and isinstance(scen, dict):
            ego0 = scen.get("ego_initial")
        if ego0:
            init.update({k: float(v) for k, v in dict(ego0).items() if k in init})
        names = getattr(self.model, "state_names", ())
        try:
            self.x = np.asarray(self.model.initial_state(init["x"], init["y"], init["psi"], init["v"],
                                                         delta=init["delta"]), dtype=float)
        except TypeError:
            self.x = np.asarray(self.model.initial_state(init["x"], init["y"], init["psi"], init["v"]), dtype=float)
        self.names = names
        self.u = ControlInput(steer_front=init["delta"])
        self.t = 0.0
        self.gear = 1 if init["v"] >= 0 else -1
        self.delta_prev = init["delta"]
        self._delta_rate = 0.0
        self._outputs()

    # ------------------------------------------------------------------ helpers
    def _disturbance(self, t):
        fx = fy = mz = 0.0
        for d in self.params.disturbances:
            if d.get("t", 0.0) <= t < d.get("t", 0.0) + d.get("duration", 0.0):
                fx += d.get("fx", 0.0)
                fy += d.get("fy", 0.0)
                mz += d.get("mz", 0.0)
        return fx, fy, mz

    def _rhs(self, t, x, u):
        dx = self.model.derivatives(t, x, u, self.env)
        if self.params.disturbances and "vy" in self.names and "r" in self.names:
            fx, fy, mz = self._disturbance(t)
            if fx or fy or mz:
                dx = np.array(dx, dtype=float)
                vp = self.cfg.vehicle
                dx[self.names.index("vx")] += fx / vp.mass
                dx[self.names.index("vy")] += fy / vp.mass
                dx[self.names.index("r")] += mz / vp.inertia_z
        return dx

    def _outputs(self):
        _, self.out = self.model.derivatives(self.t, self.x, self.u, self.env, with_outputs=True)
        self.vs = self.model.vehicle_state(self.t, self.x, self.out)
        if "delta" not in self.out:
            self.vs.delta_f = self.u.steer_front

    def kick(self, **deltas):
        # instantaneous state change, e.g. kick(vy=1.5) or kick(psi=0.05) (impulse disturbance)
        for name, value in deltas.items():
            self.x[self.names.index(name)] += value
        self._outputs()

    # ------------------------------------------------------------------ component interface
    def output(self, t):
        vs, out = self.vs, self.out
        delta = out.get("delta")
        delta = float(vs.delta_f) if delta is None or np.ndim(delta) > 0 else float(delta)
        rate = out.get("delta_rate")
        rate = self._delta_rate if rate is None or np.ndim(rate) > 0 else float(rate)
        if abs(vs.vx) > 0.05:
            self.gear = 1 if vs.vx > 0 else -1
        return {"ego": EgoState(t=self.t, x=float(vs.x), y=float(vs.y), psi=float(vs.psi), vx=float(vs.vx),
                                vy=float(vs.vy), r=float(vs.r), ax=float(vs.ax), ay=float(vs.ay), delta=delta,
                                delta_rate=rate, gear=self.gear)}

    def update(self, t, inputs, dt):
        u = inputs.get("control")
        if u is not None:
            self.u = u
        dt_model = self.dt_model
        if hasattr(self.model, "stable_dt"):
            dt_model = min(dt_model, self.model.stable_dt(self.x))
        n = max(1, int(math.ceil(dt / dt_model - 1e-9)))
        uu = self.u
        self.x = self.solver.step(lambda tt, xx: self._rhs(tt, xx, uu), t, self.x, dt, n)
        self.t = t + dt
        self._outputs()
        if "delta_rate" not in self.out:
            self._delta_rate = (self.vs.delta_f - self.delta_prev) / dt if dt > 0 else 0.0
        self.delta_prev = self.vs.delta_f
