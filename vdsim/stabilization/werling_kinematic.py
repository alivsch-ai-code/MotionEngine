"""Lyapunov based trajectory tracking on the extended kinematic single-track model (Werling 4.2).

    kin_tracking_with_orientation_stab   literal port of the MATLAB example program (appendix A.5)
    orientation_law                      Satz 4: rear-axle center with orientation stabilization,
                                         forward and reverse (varsigma), backstepping on delta_dot
    center_law                           Satz 6: geometric vehicle center (lambda ~ l/2) without
                                         orientation stabilization, forward only (Satz 7)
    WerlingKinematicOrientation          tracking_controller/werling_kinematic_orientation
    WerlingKinematicCenter               tracking_controller/werling_kinematic_center

Sign decision for (4.31): the printed law reads w2~ = v~d_dot - k3 e~v - k1 [e~t cos e~th - e~n sin e~th],
but the Lyapunov proof (cancellation of k1 e~v [e~t cos e~th + e~n sin e~th]) requires the plus sign.
The implementation uses the plus sign (param sign_variant="proof"); "printed" is kept for the
numerical demonstration in the tests (V_dot > 0 for some states).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

from ..core.parameters import param
from ..framework.component import Port
from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import TrackingControllerBase
from ..framework.plugins import component
from ..framework.types import ControlCommand, ControllerStatus
from .common import (
    StepTimer,
    cog_point_as_rear_axle,
    design_parameters,
    desired_from_point,
    drive_share,
    empty_status,
    force_ratio,
    hold_command,
    vehicle_config,
)
from .errors import center_errors, flat_reference_transform, rear_axle_error_rates, rear_axle_errors, series_terms


# ----------------------------------------------------------------------------- appendix A.5
def normalize_angle(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


@trace("werling2011", section="A.5", equation="(4.7), (4.9)-(4.18), (A.10)-(A.13)", concept="lyapunov_orientation",
       note="zeilengleiche Umsetzung des MATLAB-Beispielprogramms")
def kin_tracking_with_orientation_stab(y1_d, y2_d, theta_d, kappa_d, kappa_d_dot, v_d, v_d_dot, varsigma,
                                       y1, y2, psi, v, delta, l_v, l_h, m, J, gam, k1, k2, k3, k4):
    # y1_d, ..., varsigma: desired values in rear axle coordinates
    # y1, ..., delta: measured states
    # l_v, ..., gam: vehicular parameters
    # k1, ..., k4: control design parameters
    l = l_v + l_h  # wheel base
    # State transformations
    e_t = (y1 - y1_d) * math.cos(theta_d) + (y2 - y2_d) * math.sin(theta_d)  # (4.9)
    e_n = (y1 - y1_d) * (-math.sin(theta_d)) + (y2 - y2_d) * math.cos(theta_d)  # (4.9)
    e_psi = normalize_angle(psi - theta_d)  # Normalize to -pi..pi (4.9)
    kappa_delta = math.tan(delta) / l  # (4.9)
    # Transformed time derivatives
    e_t_dot = v * math.cos(e_psi) - v_d * (1 - kappa_d * e_n)  # (4.10a)
    e_n_dot = v * math.sin(e_psi) - v_d * kappa_d * e_t  # (4.10b)
    e_psi_dot = v * kappa_delta - v_d * kappa_d  # (4.10c)
    # Taylor approximations for control law
    cos_approx = -1 / 2 * e_psi + 1 / 24 * e_psi**3 - 1 / 720 * e_psi**5  # (A.10)
    sin_approx = 1 - 1 / 6 * e_psi**2 + 1 / 120 * e_psi**4 - 1 / 5040 * e_psi**6  # (A.11)
    dcos_approx = -0.5 + 1 / 8 * e_psi**2 - 1 / 144 * e_psi**4 + 1 / 5760 * e_psi**6  # (A.12)
    dsin_approx = -1 / 3 * e_psi + 1 / 30 * e_psi**3 - 1 / 840 * e_psi**5  # (A.13)
    # Fictitious and virtual control laws
    xi1 = kappa_d - k1 * (e_t * cos_approx + e_n * sin_approx) - varsigma * k2 * e_psi  # (4.11)
    e_v = v - v_d
    w2 = v_d_dot - k1 * e_t - k3 * e_v + varsigma * k2 * e_psi**2 - e_psi * kappa_d  # (4.12)
    # Back-stepping
    xi1_dot = kappa_d_dot - k1 * (e_t_dot * cos_approx + e_t * e_psi_dot * dcos_approx + e_n_dot * sin_approx
                                  + e_n * e_psi_dot * dsin_approx) - varsigma * k2 * e_psi_dot  # (4.18)
    e_delta = kappa_delta - xi1  # (4.16)
    w1 = -e_psi * v + xi1_dot - k4 * e_delta  # (4.17)
    # Lateral input resubstitution
    u1 = l * w1 * math.cos(delta) ** 2  # (4.15)
    # Longitudinal input resubstitution
    M = (m * l_h**2 + J) / l**2
    u2 = 1 / (1 + gam * (1 / math.cos(delta) - 1)) * (w2 * (m + M * math.tan(delta) ** 2)
                                                       + 2 * M * v * math.tan(delta) / math.cos(delta) ** 2 * u1)  # (4.7)
    # Output results
    delta_dot = u1
    F_l = u2
    return delta_dot, F_l


# ----------------------------------------------------------------------------- input resubstitution
@trace("werling2011", section="4.2.2", equation="(4.6), (4.7)", concept="kesm")
def force_from_acceleration(w2, u1, v, delta, P, varsigma, gamma_drive, gamma_brake):
    # inverse input substitution (4.7); gamma follows from the sign of the force (drive / brake)
    t, c = math.tan(delta), math.cos(delta)
    num = w2 * (P.m + P.M * t * t) + 2.0 * P.M * v * t / (c * c) * u1
    gam = force_ratio(num, varsigma, gamma_drive, gamma_brake)
    return num / (1.0 + gam * (1.0 / c - 1.0)), gam


# ----------------------------------------------------------------------------- Satz 4
@trace("werling2011", section="4.2.3.2", equation="(4.11), (4.12), (4.15)-(4.18)", concept="lyapunov_orientation")
def orientation_law(d, x1, x2, psi, v, delta, P, k1, k2, k3, k4, gamma_drive=0.0, gamma_brake=0.75, switch=0.5):
    """Lyapunov tracking with orientation stabilization of the rear-axle center (Satz 4).

    d: Desired (rear-axle reference, Werling signs), measured rear-axle position/orientation,
    signed speed v and road-wheel angle delta. Returns a dict with delta_dot, F_l and diagnostics.
    """
    l, sg = P.l, d.varsigma
    e_t, e_n, e_psi, kd = rear_axle_errors(x1, x2, psi, delta, d.x, d.y, d.psi, l)
    et_d, en_d, ep_d = rear_axle_error_rates(e_t, e_n, e_psi, v, kd, d.v, d.kappa)
    ca, sa, dca, dsa = series_terms(e_psi, switch)
    xi1 = d.kappa - k1 * (e_t * ca + e_n * sa) - sg * k2 * e_psi                       # (4.11)
    e_v = v - d.v
    w2 = d.v_dot - k1 * e_t - k3 * e_v + sg * k2 * e_psi**2 - e_psi * d.kappa          # (4.12)
    xi1_dot = d.kappa_dot - k1 * (et_d * ca + e_t * ep_d * dca + en_d * sa + e_n * ep_d * dsa) \
        - sg * k2 * ep_d                                                               # (4.18)
    e_delta = kd - xi1                                                                 # (4.16)
    w1 = -e_psi * v + xi1_dot - k4 * e_delta                                           # (4.17)
    u1 = l * w1 * math.cos(delta) ** 2                                                 # (4.15)
    u2, gam = force_from_acceleration(w2, u1, v, delta, P, sg, gamma_drive, gamma_brake)
    V = 0.5 * (k1 * e_t**2 + k1 * e_n**2 + e_psi**2 + e_v**2 + e_delta**2)
    return {"delta_dot": u1, "F_l": u2, "w1": w1, "w2": w2, "xi1": xi1, "xi1_dot": xi1_dot, "gamma": gam,
            "e_t": e_t, "e_n": e_n, "e_psi": e_psi, "e_v": e_v, "e_delta": e_delta, "e_t_dot": et_d,
            "e_n_dot": en_d, "e_psi_dot": ep_d, "V": V,
            "V_dot": -d.speed * k2 * e_psi**2 - k3 * e_v**2 - k4 * e_delta**2}


# ----------------------------------------------------------------------------- Satz 6
@trace("werling2011", section="4.2.4.3", equation="(4.28)-(4.31)", concept="lyapunov_center",
       note="Vorzeichen in (4.31) nach dem Lyapunov-Beweis: + e~n sin e~theta")
def center_law(d, x1, x2, psi, v, delta, P, k1, k3, k4, lam, gamma_drive=0.0, gamma_brake=0.75, switch=0.5,
               sign_variant="proof"):
    """Lyapunov tracking of the point lambda ahead of the rear axle without orientation stabilization (Satz 6)."""
    l = P.l
    ref = flat_reference_transform(d.x, d.y, d.psi, d.kappa, d.kappa_dot, d.kappa_prime, d.v, d.v_dot, lam)
    err = center_errors(x1, x2, psi, v, delta, ref, lam, l)
    et, en, eth, vt, bt = err["e_t"], err["e_n"], err["e_theta"], err["v"], err["beta"]
    ca, sa, _, _ = series_terms(eth, switch)
    vd, kd = ref["v"], ref["kappa"]
    w1t = -k1 * vd * (et * ca + en * sa) - k4 * eth                                    # (4.30)
    ev = vt - vd
    s_n = 1.0 if sign_variant == "proof" else -1.0
    w2t = ref["v_dot"] - k3 * ev - k1 * (et * math.cos(eth) + s_n * en * math.sin(eth))  # (4.31)
    sb, cb = math.sin(bt), math.cos(bt)
    G = lam / l * cb * cb + l / lam * sb * sb                     # d beta~ / d delta (4.27)
    u1 = (w1t + vd * kd - vt * sb / lam) / G                                           # (4.28)
    w2 = w2t * cb - vt * sb * (w1t - vt * sb / lam + vd * kd)                          # (4.29)
    u2, gam = force_from_acceleration(w2, u1, v, delta, P, 1, gamma_drive, gamma_brake)
    et_d = vt * math.cos(eth) - vd * (1.0 - kd * en)                                   # (4.26a)
    en_d = vt * math.sin(eth) - vd * kd * et                                           # (4.26b)
    V = 0.5 * (k1 * et**2 + k1 * en**2 + eth**2 + ev**2)
    return {"delta_dot": u1, "F_l": u2, "w1": w1t, "w2_tilde": w2t, "w2": w2, "gamma": gam, "ref": ref,
            "e_t": et, "e_n": en, "e_theta": eth, "e_v": ev, "e_t_dot": et_d, "e_n_dot": en_d, "beta": bt,
            "v_tilde": vt, "V": V, "V_dot": -k4 * eth**2 - k3 * ev**2, "point": (err["x"], err["y"])}


# ----------------------------------------------------------------------------- components
@dataclass
class OrientationParams:
    k1: float = param(0.5, "1/m²", "k1 (Positionsfehler)", min=0.0)
    k2: float = param(2.0, "1/m", "k2 (Orientierungsfehler)", min=0.0)
    k3: float = param(2.0, "1/s", "k3 (Geschwindigkeitsfehler)", min=0.0)
    k4: float = param(10.0, "1/s", "k4 (Lenkfehler, Backstepping)", min=0.0)
    gamma_drive: float = param(-1.0, "-", "Kräfteverhältnis Antrieb (<0: aus Antriebslayout)", min=-1, max=1)
    gamma_brake: float = param(0.75, "-", "Kräfteverhältnis Bremsen", min=0, max=1)
    taylor_switch: float = param(0.5, "rad", "Grenze Taylor-Näherung", min=0.0, max=1.5)
    mu: float = param(-1.0, "-", "Reibwert (<0: aus Fahrzeug/Umgebung)")


@dataclass
class CenterParams:
    k1: float = param(0.5, "1/m²", "k~1 (Positionsfehler)", min=0.0)
    k3: float = param(2.0, "1/s", "k~3 (Geschwindigkeitsfehler)", min=0.0)
    k4: float = param(5.0, "1/s", "k~4 (Kurswinkelfehler)", min=0.0)
    lam: float = param(-1.0, "m", "Abstand lambda von der Hinterachse (<0: l/2)")
    gamma_drive: float = param(-1.0, "-", "Kräfteverhältnis Antrieb (<0: aus Antriebslayout)", min=-1, max=1)
    gamma_brake: float = param(0.75, "-", "Kräfteverhältnis Bremsen", min=0, max=1)
    taylor_switch: float = param(0.5, "rad", "Grenze Taylor-Näherung", min=0.0, max=1.5)
    sign_variant: str = param("proof", "", "Vorzeichen in (4.31): proof / printed", choices=["proof", "printed"])
    mu: float = param(-1.0, "-", "Reibwert (<0: aus Fahrzeug/Umgebung)")


class _KinematicBase(TrackingControllerBase):
    VERSION = "1.0.0"
    INPUTS = {"ego": Port("EgoState", "Fahrzeugzustand (Schwerpunkt)"),
              "trajectory": Port("PlannedTrajectory", "Solltrajektorie der Hinterachsmitte")}

    def reset(self, context):
        super().reset(context)
        cfg = vehicle_config(context)
        self.P = design_parameters(context, self.params.mu)
        self.gamma_drive = drive_share(cfg) if self.params.gamma_drive < 0 else self.params.gamma_drive
        self.timer = StepTimer()
        self.last = {}

    def _measured(self, ego):
        x1, x2 = ego.rear_axle(self.P.lh)
        return x1, x2, ego.psi, ego.vx, ego.delta

    def _desired(self, traj, t):
        pt = traj.sample(t)
        if traj.reference_point != "rear_axle":
            pt = cog_point_as_rear_axle(pt, self.P.lh)
        return desired_from_point(pt)

    def step(self, t, inputs):
        ego, traj = inputs.get("ego"), inputs.get("trajectory")
        if ego is None:
            return {"command": None, "status": empty_status(t, self.NAME)}
        if traj is None or traj.empty:
            return {"command": hold_command(t, ego, self.NAME), "status": empty_status(t, self.NAME)}
        start = time.perf_counter()
        d = self._desired(traj, t)
        res = self._law(d, *self._measured(ego))
        self.timer.add(time.perf_counter() - start)
        self.last = res
        self.signals = {k: float(res[k]) for k in ("e_t", "e_n", "e_v", "delta_dot", "F_l", "V") if k in res}
        cmd = ControlCommand(t=t, steer_rate=float(res["delta_dot"]), force=float(res["F_l"]), direction=d.varsigma,
                             controller=self.NAME, info={"a_expected": float(res["w2"]), "gamma": res["gamma"]})
        status = ControllerStatus(t=t, e_t=res["e_t"], e_n=res["e_n"], e_theta=res.get("e_theta", res.get("e_psi")),
                                  e_v=res["e_v"], e_t_dot=res["e_t_dot"], e_n_dot=res["e_n_dot"],
                                  active_controller=self.NAME, lookahead=self.lookahead,
                                  info={"V": res["V"], "V_dot": res["V_dot"], "reference_point": "rear_axle"})
        return {"command": cmd, "status": status}


@component
class WerlingKinematicOrientation(_KinematicBase):
    NAME = "werling_kinematic_orientation"
    LABEL = "Werling: Lyapunov mit Orientierungsstabilisierung (Satz 4)"
    PARAMS = OrientationParams
    lookahead = 0.0
    DOC = ComponentDoc(
        summary="Lyapunov-basierter Trackingregler der Hinterachsmitte mit Orientierungsstabilisierung für "
                "langsame Vorwärts- und Rückwärtsfahrt.",
        purpose="Stabilisiert Position, Orientierung, Geschwindigkeit und Lenkwinkel des erweiterten kinematischen "
                "Einspurmodells entlang der Solltrajektorie, auch im Stand und rückwärts (Werling 4.2.3).",
        theory="Invariante Fehler im Frenet-Rahmen der Solltrajektorie (4.9), fiktives Regelgesetz für "
               "$\\kappa_\\delta$ (4.11), virtueller Eingang $w_2=\\dot v$ (4.12), Backstepping auf "
               "$u_1=\\dot\\delta$ (4.16)-(4.18), Rücksubstitution (4.15), (4.7).",
        assumptions=["Keine Reifenschräglaufwinkel (langsame Fahrt, kinematisches Einspurmodell)",
                     "Alle Zustände gemessen, Lenkwinkel |delta| < pi/2",
                     "Antriebs- und Bremskräfte werden von unterlagerten Regelkreisen schnell eingestellt"],
        limitations=["Front schwenkt bei großen Korrekturen aus (Referenzpunkt Hinterachse)",
                     "Keine Stellgrößenbeschränkung im Regelgesetz (Reserve durch die Planung)",
                     "Für schnelle Fahrt ungeeignet (Schräglauf vernachlässigt)"],
        references=["werling2011", "werling2010tro", "khalil2002"],
        equations=["werling2011:(4.9)", "werling2011:(4.10)", "werling2011:(4.11)", "werling2011:(4.12)",
                   "werling2011:(4.15)", "werling2011:(4.16)", "werling2011:(4.17)", "werling2011:(4.18)",
                   "werling2011:(4.7)", "werling2011:(A.10)-(A.13)"],
        validation=["tests/stabilization/test_stabilization_kinematic.py"],
        concepts=["lyapunov_orientation", "backstepping", "invariant_tracking_error", "kesm"],
        expert="Mit $V_c=\\frac{1}{2}[k_1e_t^2+k_1e_n^2+e_\\psi^2+e_v^2+e_\\delta^2]$ gilt "
               "$\\dot V_c=-\\dot s_dk_2e_\\psi^2-k_3e_v^2-k_4e_\\delta^2\\leq0$; LaSalle liefert asymptotische "
               "Stabilität von $[e_t,e_n,e_\\psi,e_v,e_\\delta]=0$ für $\\dot s_d\\ne0$ (Satz 4). Vorwärts und "
               "rückwärts über $\\varsigma$, kein Lenkwinkelsprung im Stand, da keine Division durch $v$.")

    def _law(self, d, x1, x2, psi, v, delta):
        p = self.params
        return orientation_law(d, x1, x2, psi, v, delta, self.P, p.k1, p.k2, p.k3, p.k4, self.gamma_drive,
                               p.gamma_brake, p.taylor_switch)


@component
class WerlingKinematicCenter(_KinematicBase):
    NAME = "werling_kinematic_center"
    LABEL = "Werling: Lyapunov ohne Orientierungsstabilisierung (Satz 6)"
    PARAMS = CenterParams
    DOC = ComponentDoc(
        summary="Lyapunov-basierter Trackingregler der geometrischen Fahrzeugmitte ohne Orientierungsstabilisierung "
                "für langsame Vorwärtsfahrt.",
        purpose="Stabilisiert den Punkt lambda ~ l/2 vor der Hinterachse direkt, damit das Fahrzeug ruhiger lenkt "
                "und mit kleineren Korrekturamplituden der kollisionsfrei geplanten Konfiguration folgt (Werling 4.2.4).",
        theory="Flachheitsbasierte Sollgrößentransformation (4.20)-(4.24), invariante Fehler der Fahrzeugmitte "
               "(4.25), Fehlerdynamik Modell 3 (4.26)/(4.27), Regelgesetz (4.30)/(4.31) mit Inversen (4.28)/(4.29) "
               "und Rücksubstitution (4.7).",
        assumptions=["Kinematisches Einspurmodell, |beta~| < pi/2 (durch die Lenkwinkelgrenze erfüllt)",
                     "Nur Vorwärtsfahrt, |kappa_d| < 1/lambda (Satz 7)"],
        limitations=["Rückwärts instabile Nulldynamik (Taschenmessereffekt)",
                     "Orientierung nur über die Nulldynamik stabil (|psi - psi_d| <= pi/2 zu Beginn)"],
        design_decisions=["Vorzeichen in (4.31) nach dem Lyapunov-Beweis (+ e~n sin e~theta), der gedruckte "
                          "Ausdruck (-) verletzt V_dot <= 0"],
        references=["werling2011", "khalil2002", "isidori1995"],
        equations=["werling2011:(4.20)-(4.24)", "werling2011:(4.25)", "werling2011:(4.26)", "werling2011:(4.27)",
                   "werling2011:(4.28)", "werling2011:(4.29)", "werling2011:(4.30)", "werling2011:(4.31)",
                   "werling2011:(4.36)"],
        validation=["tests/stabilization/test_stabilization_kinematic.py"],
        concepts=["lyapunov_center", "flat_reference_transform", "zero_dynamics_kesm"],
        expert="Mit $\\tilde V=\\frac{1}{2}[\\tilde k_1\\tilde e_t^2+\\tilde k_1\\tilde e_n^2+\\tilde e_\\theta^2+"
               "\\tilde e_v^2]$ und $\\tilde w_2=\\dot{\\tilde v}_d-\\tilde k_3\\tilde e_v-\\tilde k_1[\\tilde e_t"
               "\\cos\\tilde e_\\theta+\\tilde e_n\\sin\\tilde e_\\theta]$ folgt $\\dot{\\tilde V}=-\\tilde k_4\\tilde "
               "e_\\theta^2-\\tilde k_3\\tilde e_v^2\\leq0$ (Satz 6). Nulldynamik (4.36) stabil für $v_d>0$, "
               "$|\\kappa_d|<1/\\lambda$ (Satz 7).")

    @property
    def lookahead(self):
        return self.params.lam if self.params.lam > 0 else 0.5 * self.P.l

    def _law(self, d, x1, x2, psi, v, delta):
        p = self.params
        return center_law(d, x1, x2, psi, v, delta, self.P, p.k1, p.k3, p.k4, self.lookahead, self.gamma_drive,
                          p.gamma_brake, p.taylor_switch, p.sign_variant)
