"""Classical longitudinal trajectory tracking controllers (output: acceleration request).

    tracking_controller/pid        PID on the speed error v_d(t) - v (derivative from a_d - a)
    tracking_controller/pi         PI on the speed error (integrator clamped)
    tracking_controller/ff_fb      feedforward a_d(t) + feedback on speed and longitudinal position error e_t
    tracking_controller/acc        distance based adaptive cruise control (constant time gap) for comparisons
                                   without a planner; lead from the optional ObjectList input or a virtual lead
    tracking_controller/speed_pi   vehicle speed controller: PI with back-calculation anti-windup and a_d feedforward

The longitudinal position error e_t (time based, Frenet frame of the trajectory point at time t) is taken at
the trajectory's reference point. Forward driving only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..core.parameters import param
from ..framework.component import Port
from ..framework.knowledge import ComponentDoc, trace
from ..framework.plugins import component
from .classic_lateral import ClassicBase
from .errors import frenet_errors


@dataclass
class _LongParams:
    a_max: float = param(3.0, "m/s²", "max. Beschleunigung", min=0.0)
    a_min: float = param(-8.0, "m/s²", "max. Verzögerung (negativ)", max=0.0)


class LongitudinalBase(ClassicBase):
    PARAMS = _LongParams

    def reset(self, context):
        super().reset(context)
        self.integral = 0.0
        self.t_prev = None
        self.extra = {}

    def control(self, t, ego, traj):
        pt, e, _, (px, py, course, speed) = self.errors(t, ego, traj)
        dt = 0.0 if self.t_prev is None else t - self.t_prev
        self.t_prev = t
        a = self.accel(t, ego, traj, pt, e, speed, dt)
        a = float(np.clip(a, self.params.a_min, self.params.a_max))
        out = self.finish(t, ego.delta, a, pt, e, speed, {"a_request": a})
        out["command"].steer_angle = None
        self.signals = {"a_request": a, "e_t": e["e_t"], **self.extra}
        return out


@dataclass
class PIDParams(_LongParams):
    kp: float = param(1.5, "1/s", "K_P", min=0.0)
    ki: float = param(0.5, "1/s²", "K_I", min=0.0)
    kd: float = param(0.05, "-", "K_D", min=0.0)


@component
class PID(LongitudinalBase):
    NAME, LABEL, PARAMS = "pid", "PID-Geschwindigkeitsregler", PIDParams
    DOC = ComponentDoc(summary="PID-Regler auf den Geschwindigkeitsfehler der Solltrajektorie.",
                       purpose="Klassischer Längsregler zum Vergleich.", theory="$a=K_Pe_v+K_I\\int e_v+K_D\\dot e_v$",
                       assumptions=["Vorwärtsfahrt"], limitations=["Keine Vorsteuerung, Schleppfehler in e_t"],
                       references=["astrom2006"], validation=["tests/stabilization/test_stabilization_classic.py"],
                       concepts=["pid"], expert="Stabil für positive Verstärkungen am Integrator $\\dot v=a$.")

    @trace("astrom2006", concept="pid")
    def accel(self, t, ego, traj, pt, e, speed, dt):
        p = self.params
        ev = pt.v - speed
        self.integral = float(np.clip(self.integral + ev * dt, -20.0, 20.0))
        return p.kp * ev + p.ki * self.integral + p.kd * (pt.a - ego.ax)


@dataclass
class PIParams(_LongParams):
    kp: float = param(1.5, "1/s", "K_P", min=0.0)
    ki: float = param(0.5, "1/s²", "K_I", min=0.0)


@component
class PI(LongitudinalBase):
    NAME, LABEL, PARAMS = "pi", "PI-Geschwindigkeitsregler", PIParams
    DOC = ComponentDoc(summary="PI-Regler auf den Geschwindigkeitsfehler.", purpose="Klassischer Längsregler.",
                       theory="$a=K_Pe_v+K_I\\int e_v$", assumptions=["Vorwärtsfahrt"],
                       limitations=["Keine Vorsteuerung"], references=["astrom2006"],
                       validation=["tests/stabilization/test_stabilization_classic.py"], concepts=["pid"],
                       expert="PT2-ähnlicher geschlossener Kreis, stabil für $K_P,K_I>0$.")

    def accel(self, t, ego, traj, pt, e, speed, dt):
        p = self.params
        ev = pt.v - speed
        self.integral = float(np.clip(self.integral + ev * dt, -20.0, 20.0))
        return p.kp * ev + p.ki * self.integral


@dataclass
class FFFBParams(_LongParams):
    k_v: float = param(1.0, "1/s", "Verstärkung Geschwindigkeitsfehler", min=0.0)
    k_s: float = param(0.3, "1/s²", "Verstärkung Längsfehler", min=0.0)


@component
class FeedForwardFeedback(LongitudinalBase):
    NAME, LABEL, PARAMS = "ff_fb", "Vorsteuerung + Rückführung (längs)", FFFBParams
    DOC = ComponentDoc(summary="Beschleunigungsvorsteuerung aus der Trajektorie mit Rückführung von Geschwindigkeits- "
                               "und Längsfehler.", purpose="Zeitbasiertes Längstracking (Trajektorie statt Bahn).",
                       theory="$a=a_d+k_v(v_d-v)-k_se_t$", assumptions=["Vorwärtsfahrt"],
                       limitations=["Stellbeschränkungen nur geklemmt"], references=["astrom2006", "werling2011"],
                       validation=["tests/stabilization/test_stabilization_classic.py"], concepts=["feedforward"],
                       expert="Fehlerdynamik $\\ddot e_t+k_v\\dot e_t+k_se_t=0$, stabil für $k_v,k_s>0$.")

    def accel(self, t, ego, traj, pt, e, speed, dt):
        p = self.params
        return pt.a + p.k_v * (pt.v - speed) - p.k_s * e["e_t"]


@dataclass
class ACCParams(_LongParams):
    time_gap: float = param(1.8, "s", "Zeitlücke", min=0.0)
    standstill_gap: float = param(5.0, "m", "Abstand im Stand", min=0.0)
    k_gap: float = param(0.25, "1/s²", "Verstärkung Abstandsfehler", min=0.0)
    k_speed: float = param(0.7, "1/s", "Verstärkung Relativgeschwindigkeit", min=0.0)
    k_v: float = param(1.0, "1/s", "Verstärkung Wunschgeschwindigkeit", min=0.0)
    lead_gap0: float = param(-1.0, "m", "virtuelles Vorderfahrzeug: Startabstand (<0: keins)")
    lead_speed: float = param(15.0, "m/s", "virtuelles Vorderfahrzeug: Geschwindigkeit", min=0.0)
    lane_width: float = param(2.0, "m", "Halbbreite des Fahrschlauchs für Objekte", min=0.1)


@component
class ACC(LongitudinalBase):
    NAME, LABEL, PARAMS = "acc", "Abstandsregeltempomat (ACC)", ACCParams
    INPUTS = {"ego": Port("EgoState"), "trajectory": Port("PlannedTrajectory"),
              "objects": Port("ObjectList", "Objekte für das Vorderfahrzeug", optional=True)}
    DOC = ComponentDoc(summary="Abstandsbasierte Längsregelung mit konstanter Zeitlücke.",
                       purpose="Vergleich der trajektorienbasierten Längsführung mit klassischem ACC ohne Planer "
                               "(Werling 4.1.3: bei Trajektorienfolge implizit enthalten).",
                       theory="$a=\\min(a_{cruise},k_g(d-d_0-\\tau v)+k_v(v_l-v))$",
                       assumptions=["Vorderfahrzeug im Fahrschlauch der Trajektorie"],
                       limitations=["Keine Kollisionsfreiheit garantiert"], references=["rajamani2012"],
                       validation=["tests/stabilization/test_stabilization_classic.py"], concepts=["acc"],
                       expert="String-Stabilität für $\\tau>0$ und geeignete Verstärkungen (Rajamani Kap. 5).")

    def reset(self, context):
        super().reset(context)
        self.lead_s = None
        self.objects = None

    def step(self, t, inputs):
        self.objects = inputs.get("objects")
        return super().step(t, inputs)

    def lead(self, t, ego, dt):
        p = self.params
        if self.objects is not None and getattr(self.objects, "objects", None):
            best = None
            c, s = math.cos(ego.psi), math.sin(ego.psi)
            for o in self.objects.objects:
                dx, dy = o.x - ego.x, o.y - ego.y
                ahead, lat = c * dx + s * dy, -s * dx + c * dy
                if ahead > 0 and abs(lat) < p.lane_width:
                    gap = ahead - 0.5 * (o.length + self.cfg.vehicle.length)
                    if best is None or gap < best[0]:
                        best = (gap, o.v)
            return best
        if p.lead_gap0 < 0:
            return None
        if self.lead_s is None:
            self.lead_s = p.lead_gap0
            self.own_s = 0.0
        self.lead_s += p.lead_speed * dt
        self.own_s += ego.vx * dt
        return self.lead_s - self.own_s, p.lead_speed

    @trace("rajamani2012", section="5", concept="acc")
    def accel(self, t, ego, traj, pt, e, speed, dt):
        p = self.params
        a_cruise = pt.a + p.k_v * (pt.v - speed)
        lead = self.lead(t, ego, dt)
        if lead is None:
            return a_cruise
        gap, v_lead = lead
        a_follow = p.k_gap * (gap - p.standstill_gap - p.time_gap * speed) + p.k_speed * (v_lead - speed)
        self.extra = {"gap": gap, "v_lead": v_lead}
        return min(a_cruise, a_follow)


@dataclass
class SpeedPIParams(_LongParams):
    kp: float = param(1.2, "1/s", "K_P", min=0.0)
    ki: float = param(0.4, "1/s²", "K_I", min=0.0)
    k_aw: float = param(2.0, "1/s", "Anti-Windup Rückrechnung", min=0.0)
    feedforward: bool = param(True, "", "Beschleunigungsvorsteuerung a_d")


@component
class VehicleSpeedController(LongitudinalBase):
    NAME, LABEL, PARAMS = "speed_pi", "Fahrzeug-Geschwindigkeitsregler (PI mit Anti-Windup)", SpeedPIParams
    DOC = ComponentDoc(summary="PI-Geschwindigkeitsregler mit Back-Calculation-Anti-Windup und Vorsteuerung.",
                       purpose="Robuster Geschwindigkeitsregler bei Stellgrößensättigung.",
                       theory="$a=a_d+K_Pe_v+K_II$, $\\dot I=e_v+k_{aw}(a_{sat}-a)/K_I$",
                       assumptions=["Vorwärtsfahrt"], limitations=["Kein Positionsfehler"],
                       references=["astrom2006"], validation=["tests/stabilization/test_stabilization_classic.py"],
                       concepts=["anti_windup"],
                       expert="Die Rückrechnung begrenzt den Integrator in der Sättigung (Åström/Hägglund).")

    @trace("astrom2006", concept="anti_windup")
    def accel(self, t, ego, traj, pt, e, speed, dt):
        p = self.params
        ev = pt.v - speed
        a = (pt.a if p.feedforward else 0.0) + p.kp * ev + p.ki * self.integral
        a_sat = float(np.clip(a, p.a_min, p.a_max))
        if p.ki > 0:
            self.integral += (ev + p.k_aw * (a_sat - a) / p.ki) * dt
        return a_sat


__all__ = ["ACC", "PI", "PID", "FeedForwardFeedback", "VehicleSpeedController", "frenet_errors"]
