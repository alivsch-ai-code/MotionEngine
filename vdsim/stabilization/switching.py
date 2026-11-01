"""Speed dependent, bumpless switching of the Werling controllers and the re-initialization monitor
(Werling 4.4, Fig. 4.13, and 4.5): tracking_controller/werling_bilevel.

    reference_point "rear_axle", varsigma = -1   -> Lyapunov with orientation stabilization (Satz 4)
    reference_point "rear_axle", varsigma = +1   -> Lyapunov without orientation stabilization (Satz 6)
    reference_point "cog"                        -> exact I/O linearization (Satz 8)

At v_d = 0 the planned direction varsigma decides. The trajectory's reference point (set by the planner
with the threshold v_s = 3 m/s and hysteresis, contracts.md section 7) is decisive, so trajectory and
controller are always consistent. A "cog" trajectory slower than v_min_dynamic falls back to the
kinematic center controller (quasi-static conversion to the rear axle).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..core.parameters import param
from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import TrackingControllerBase
from ..framework.plugins import component
from .common import V_SWITCH, StepTimer, design_parameters, empty_status, hold_command
from .reinit import ReinitMonitor, predict_reference_point
from .werling_dynamic import WerlingDynamic
from .werling_kinematic import WerlingKinematicCenter, WerlingKinematicOrientation


@dataclass
class BilevelParams:
    v_switch: float = param(V_SWITCH, "m/s", "Umschaltgeschwindigkeit v_s", min=0.5, max=15.0)
    v_min_dynamic: float = param(1.0, "m/s", "Mindestgeschwindigkeit des dynamischen Reglers", min=0.1)
    forward_slow: str = param("center", "", "Regler langsam vorwärts: center / orientation",
                              choices=["center", "orientation"])
    c_t: float = param(1.0, "m/s", "Schwellwert c_t (Längsfehleränderung)", min=0.01)
    c_n: float = param(0.5, "m/s", "Schwellwert c_n (Querfehleränderung)", min=0.01)
    e_t_max: float = param(0.0, "m", "absoluter Längsfehler e_max (0 = aus)", min=0.0)
    e_n_max: float = param(0.0, "m", "absoluter Querfehler e_max (0 = aus)", min=0.0)
    e_theta_max: float = param(0.0, "rad", "absoluter Orientierungsfehler (0 = aus)", min=0.0)
    reinit_enabled: bool = param(True, "", "Reinitialisierungsauslösung aktiv")
    cooldown: float = param(0.3, "s", "Sperrzeit nach einer Reinitialisierung", min=0.0)
    max_hold: float = param(0.5, "s", "max. Haltedauer der Anforderung", min=0.0)
    prediction_dt: float = param(0.1, "s", "Prädiktionszeit Delta t (Planungslatenz)", min=0.0, max=1.0)
    mu: float = param(-1.0, "-", "Reibwert (<0: aus Fahrzeug/Umgebung)")
    orientation: dict = field(default_factory=dict, metadata={"label": "Parameter Satz 4", "unit": ""})
    center: dict = field(default_factory=dict, metadata={"label": "Parameter Satz 6", "unit": ""})
    dynamic: dict = field(default_factory=dict, metadata={"label": "Parameter Satz 8", "unit": ""})


@trace("werling2011", section="4.4", concept="controller_switching", note="Abb. 4.13")
def select_controller(reference_point, direction, v_d, v_min_dynamic=1.0, forward_slow="center"):
    if reference_point == "cog" and direction > 0 and v_d >= v_min_dynamic:
        return "dynamic"
    if direction < 0:
        return "orientation"
    return forward_slow


@component
class WerlingBilevel(TrackingControllerBase):
    NAME = "werling_bilevel"
    VERSION = "1.0.0"
    LABEL = "Werling: Bi-level-Stabilisierung (Umschaltung + Reinitialisierung)"
    PARAMS = BilevelParams
    DOC = ComponentDoc(
        summary="Standard-Trackingregler: stoßfreie Umschaltung der drei Werling-Regler nach Referenzpunkt und "
                "Fahrtrichtung, dazu Reinitialisierungsauslösung und Bewegungsprädiktion für die Planung.",
        purpose="Vereint Low-level-Stabilisierung (permanente Störungen, Modellfehler) mit der High-level-"
                "Stabilisierung durch Reinitialisierung bei Impulsstörungen (Werling 2.3, 4.4, 4.5).",
        theory="Umschaltung nach Abb. 4.13; elliptisches Maß $(\\dot e_t/c_t)^2+(\\dot e_n/c_n)^2\\geq1$ (4.5.1) im "
               "Schwerpunkt bzw. geometrischen Mittelpunkt; Taylor-Prädiktion des Referenzpunkts über die "
               "Planungslatenz (4.5.2).",
        assumptions=["Planer setzt reference_point mit Hysterese um v_s (contracts.md Abschnitt 7)",
                     "Planer beantwortet reinit_request mit einer Trajektorie mit reinitialized=True"],
        limitations=["Harte Umschaltung: kleine Stellgrößensprünge möglich, Verstärkungen abgestimmt",
                     "Schwellwerte c_t, c_n experimentell (Standardwerte für die Mittelklasselimousine)"],
        design_decisions=["Reinitialisierungsanforderung gehalten bis zur Antwort (max_hold), danach Sperrzeit",
                          "cog-Trajektorie unter v_min_dynamic: kinematischer Regler mit quasistatischer "
                          "Umrechnung auf die Hinterachse"],
        references=["werling2011", "werling2010tro"],
        equations=["werling2011:Abb. 4.13", "werling2011:(4.58)", "werling2011:(4.59)", "werling2011:4.5.1",
                   "werling2011:4.5.2"],
        validation=["tests/stabilization/test_stabilization_switching.py"],
        concepts=["bilevel_stabilization", "controller_switching", "reinitialization_trigger", "motion_prediction"],
        expert="Jeder Teilregler ist für sich asymptotisch stabil (Sätze 4, 6, 8). Da beim Umschalten beide "
               "Modelle gültig sind und die Vorsteueranteile dominieren, bleiben die Sprünge klein; die "
               "Reinitialisierung setzt die Low-level-Fehler auf null (Werling 2.3).")

    def __init__(self, params=None, **overrides):
        super().__init__(params, **overrides)
        p = self.params
        self.controllers = {"orientation": WerlingKinematicOrientation({**p.orientation, **_mu(p)}),
                            "center": WerlingKinematicCenter({**p.center, **_mu(p)}),
                            "dynamic": WerlingDynamic({**p.dynamic, **_mu(p)})}

    def reset(self, context):
        super().reset(context)
        p = self.params
        for c in self.controllers.values():
            c.reset(context)
        self.P = design_parameters(context, p.mu)
        self.monitor = ReinitMonitor(p.c_t, p.c_n, p.e_t_max, p.e_n_max, p.e_theta_max, p.cooldown, p.max_hold)
        self.active = None
        self.switch_events = []
        self.timer = StepTimer()

    def step(self, t, inputs):
        ego, traj = inputs.get("ego"), inputs.get("trajectory")
        if ego is None:
            return {"command": None, "status": empty_status(t, self.NAME)}
        if traj is None or traj.empty:
            return {"command": hold_command(t, ego, self.NAME), "status": empty_status(t, self.NAME)}
        start = time.perf_counter()
        p = self.params
        pt = traj.sample(t)
        name = select_controller(traj.reference_point, traj.direction, pt.v, p.v_min_dynamic, p.forward_slow)
        if name != self.active:
            if name == "dynamic":
                self.controllers["dynamic"].activate(t, ego)
            self.switch_events.append((t, self.active, name))
            self.active = name
        ctl = self.controllers[name]
        out = ctl.step(t, {"ego": ego, "trajectory": traj})
        status = out["status"]
        if p.reinit_enabled:
            status.reinit_request = self.monitor.update(t, status, traj)
        ref_point = traj.reference_point
        status.prediction = predict_reference_point(ego, self.P, ref_point, p.prediction_dt, p.v_switch, traj.direction)
        status.info.update(active=name, reinit_measure=self.monitor.measure, reinit_reason=self.monitor.reason)
        out["command"].info["active"] = name
        self.signals = {**ctl.signals, "reinit_request": float(status.reinit_request),
                        "reinit_measure": self.monitor.measure}
        self.timer.add(time.perf_counter() - start)
        return {"command": out["command"], "status": status}


def _mu(p):
    return {"mu": p.mu} if p.mu >= 0 else {}
