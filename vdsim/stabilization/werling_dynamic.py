"""Exact input/output linearization of the dynamic single-track model for fast driving (Werling 4.3.3).

    lookahead_for_damping       (4.70)  lambda(zeta, v_d) for a constant damping ratio of the zero dynamics
    zero_dynamics_coefficients  (4.67)  linearized zero dynamics, Satz 9 (minimum phase)
    point_kinematics            (4.50)-(4.57) auxiliary quantities beta~, v~ and derivatives
    solve_linearizing_input     (4.60)  linearizing feedback by a 2D Newton search over u = [delta, F_l]
    ZeroDynamicsReference       (4.71)-(4.74) online simulation of the zero dynamics (Remark 10)
    WerlingDynamic              tracking_controller/werling_dynamic

Equivalent formulation of (4.60): instead of differentiating the Frenet errors twice symbolically,
the condition L_f^2 e~ = w~ is converted into the required acceleration of the reference point
y~ = [x1, x2] + lambda [cos psi, sin psi] in vehicle coordinates,

    R(theta~_d) y~_dd = [v~_d_dot, v~_d^2 kappa~_d] + w - omega^2 e + 2 omega P e_dot + omega_dot P e,
    omega = v~_d kappa~_d,   P = [[0, -1], [1, 0]],   w = [w~2, w~1],

and the inputs solve  F_x/m - lambda r^2 = a_x,req,  F_y/m + lambda M_z/J = a_y,req  (model 4 forces).
Both conditions are identical (exact kinematics of the moving Frenet frame).
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
from ..tire_models.isotropic import saturation_factor
from ..vehicle_models.werling_models import desm_forces
from .common import StepTimer, design_parameters, drive_share, empty_status, hold_command, vehicle_config, wrap
from .errors import flat_reference_transform, frenet_errors


# ----------------------------------------------------------------------------- zero dynamics / lambda
def minimum_phase_bound(P):
    # Satz 9: the linearized zero dynamics is stable for lambda > max(-l_h, -J/(l_v m))
    return max(-P.lh, -P.J / (P.lv * P.m))


@trace("werling2011", section="4.3.3.2", equation="(4.67)", concept="zero_dynamics_desm")
def zero_dynamics_coefficients(lam, v_d, P):
    # p0, p1 of the linearized zero dynamics [psi, r]' = [[0, 1], [-p0, -p1]] [psi, r] and its damping
    den = P.J + lam * P.lv * P.m
    p0 = P.ch * P.l / den
    p1 = P.ch * P.l * (lam + P.lh) / (v_d * den)
    zeta = p1 / (2.0 * math.sqrt(p0)) if p0 > 0 else float("nan")
    return p0, p1, zeta


@trace("werling2011", section="4.3.3.3", equation="(4.70)", concept="zero_dynamics_desm")
def lookahead_for_damping(zeta, v_d, P):
    # lambda(zeta, v_d) for a constant damping ratio of the zero dynamics; NaN if not reachable
    lv, lh, m, J, ch, L = P.lv, P.lh, P.m, P.J, P.ch, P.l
    rad = (zeta * lv * m * v_d) ** 2 + ch * L * (J - m * lh * lv)
    if rad < 0.0:
        return float("nan")
    return (2 * zeta * v_d * math.sqrt(rad) - ch * lh**2 - ch * lv * lh + 2 * zeta**2 * lv * m * v_d**2) / (ch * L)


@trace("werling2011", section="4.3.3.1", equation="(4.50)-(4.57)", concept="exact_io_linearization")
def point_kinematics(v, beta, r, lam, v_dot=0.0, beta_dot=0.0, r_dot=0.0):
    # side slip, speed and their derivatives of the point lambda ahead of the CoG
    cb = math.cos(beta)
    beta_t = math.atan(lam * r / (v * cb) + math.tan(beta))                              # (4.52)
    v_t = v * cb / math.cos(beta_t)                                                       # (4.53)
    beta_t_dot = math.cos(beta_t) ** 2 / cb**2 * (
        beta_dot + lam / v**2 * (r_dot * v * cb - r * (v_dot * cb - v * beta_dot * math.sin(beta))))  # (4.55)
    v_t_dot = (v_dot * cb - v * beta_dot * math.sin(beta) + v_t * beta_t_dot * math.sin(beta_t)) \
        / math.cos(beta_t)                                                                # (4.56)
    return beta_t, v_t, beta_t_dot, v_t_dot


# ----------------------------------------------------------------------------- linearizing feedback
def _residual(delta, F_l, vx, vy, r, lam, a_req, P, gammas, n, mode_v="modified"):
    g = gammas[0] if F_l >= 0.0 else gammas[1]
    Fx, Fy, Mz, info = desm_forces(vx, vy, r, delta, g * F_l, (1.0 - g) * F_l, P, mode_v, n, mode_h="plateau")
    info.update(Fx=Fx, Fy=Fy, Mz=Mz, gamma=g)
    return (Fx / P.m - lam * r * r - a_req[0], Fy / P.m + lam * Mz / P.J - a_req[1]), info


@trace("werling2011", section="4.3.3.1", equation="(4.60), (4.43)", concept="exact_io_linearization",
       note="2D-Newton; Reifen mit Sättigungsmodifikation (Fußnote 17), Sättigung -> Lenkwinkel zum Querkraftoptimum")
def solve_linearizing_input(vx, vy, r, lam, a_req, P, gammas=(0.0, 0.75), guess=(0.0, 0.0), n=16, tol=1e-8,
                            max_iter=25, sat_tol=0.02):
    """Inputs u = [delta, F_l] that produce the required acceleration a_req (vehicle frame) of the point lambda.

    Returns (delta, F_l, info); info["saturated"] marks front-axle saturation (modification factor above
    1 + sat_tol: delta at the lateral force optimum), info["converged"] the Newton result.
    """
    m, d_max = P.m, P.max_steer
    F_max = 0.98 * (P.Av + P.Ah)
    delta, F = float(guess[0]), float(guess[1])
    res, info = _residual(delta, F, vx, vy, r, lam, a_req, P, gammas, n)
    norm = math.hypot(*res)
    converged = norm < tol
    it = 0
    while not converged and it < max_iter:
        it += 1
        if info["sat_v"]:
            # beyond the modified characteristic: move the steering back below the peak slip
            phi = delta - info["alpha_v"]
            delta = phi + math.copysign(math.asin(0.98 * P.s_max_v), info["alpha_v"])
            res, info = _residual(delta, F, vx, vy, r, lam, a_req, P, gammas, n)
            norm = math.hypot(*res)
        hd, hf = 1e-6, 1e-4 * m
        r_d, _ = _residual(delta + hd, F, vx, vy, r, lam, a_req, P, gammas, n)
        r_f, _ = _residual(delta, F + hf, vx, vy, r, lam, a_req, P, gammas, n)
        j00, j10 = (r_d[0] - res[0]) / hd, (r_d[1] - res[1]) / hd
        j01, j11 = (r_f[0] - res[0]) / hf, (r_f[1] - res[1]) / hf
        det = j00 * j11 - j01 * j10
        if abs(det) < 1e-14:
            break
        dd = -(j11 * res[0] - j01 * res[1]) / det
        dF = -(-j10 * res[0] + j00 * res[1]) / det
        step = 1.0
        for _ in range(8):
            dn = min(max(delta + step * dd, -d_max), d_max)
            Fn = min(max(F + step * dF, -F_max), F_max)
            rn, infon = _residual(dn, Fn, vx, vy, r, lam, a_req, P, gammas, n)
            nn = math.hypot(*rn)
            if nn < norm or step < 0.02:
                break
            step *= 0.5
        delta, F, res, info, norm = dn, Fn, rn, infon, nn
        converged = norm < tol
    # saturation: the modification factor inflates the front force noticeably (or no root at all) ->
    # steering angle of the lateral force optimum of the unmodified characteristic (footnote 17)
    saturated = False
    A_v = P.Av
    F_vl = info["gamma"] * F
    s_opt = P.s_max_v * math.sqrt(max(1.0 - (F_vl / A_v) ** 2, 0.0))
    if info["sat_v"] or saturation_factor(info["S_v"], P.Bv, P.Cv, n) > 1.0 + sat_tol or             abs(math.sin(info["alpha_v"])) > s_opt:
        saturated = True
        phi = delta - info["alpha_v"]
        delta = min(max(phi + math.copysign(math.asin(s_opt), info["alpha_v"]), -d_max), d_max)
        for _ in range(6):    # longitudinal equation only, physical (plateau) characteristic
            res, info = _residual(delta, F, vx, vy, r, lam, a_req, P, gammas, n, "plateau")
            r_f, _ = _residual(delta, F + 1e-4 * m, vx, vy, r, lam, a_req, P, gammas, n, "plateau")
            jac = (r_f[0] - res[0]) / (1e-4 * m)
            if abs(jac) < 1e-12:
                break
            F = min(max(F - res[0] / jac, -F_max), F_max)
        res, info = _residual(delta, F, vx, vy, r, lam, a_req, P, gammas, n, "plateau")
    info.update(saturated=saturated, converged=converged, iterations=it, residual=math.hypot(*res))
    return delta, F, info


def _required_point_acceleration(ref, e, e_dot, w, omega, omega_dot, psi):
    # ẽ̈ = w  <=>  required acceleration of the reference point in vehicle coordinates (equivalent to (4.60))
    et, en = e
    etd, end = e_dot
    T0 = ref["v_dot"] + w[0] - omega**2 * et - 2.0 * omega * end - omega_dot * en
    T1 = ref["v"] ** 2 * ref["kappa"] + w[1] - omega**2 * en + 2.0 * omega * etd + omega_dot * et
    a = psi - ref["theta"]
    ca, sa = math.cos(a), math.sin(a)
    return ca * T0 + sa * T1, -sa * T0 + ca * T1


# ----------------------------------------------------------------------------- dynamic reference transformation
class ZeroDynamicsReference:
    """Online simulation of a reference vehicle tracking the CoG trajectory exactly (4.71)-(4.74).

    States r0, beta0 (yaw rate and side slip of the reference vehicle); x0 = y_d, psi0 = theta_d - beta0,
    v0 = v_d; u0 solves (4.73) (CoG acceleration equal to the trajectory acceleration).
    """

    def __init__(self, P, gammas, n=16, h_max=0.005, v_floor=1.0):
        self.P, self.gammas, self.n, self.h_max, self.v_floor = P, gammas, n, h_max, v_floor
        self.t = None
        self.r0 = self.beta0 = 0.0
        self.u0 = (0.0, 0.0)

    def initialize(self, t, r, beta, delta=0.0, F_l=0.0):
        # Remark 10: start with the current vehicle states
        self.t, self.r0, self.beta0, self.u0 = t, r, beta, (delta, F_l)

    @trace("werling2011", section="4.3.3.4", equation="(4.72), (4.73)", concept="dynamic_reference_transform")
    def derivatives(self, pt, r0, beta0):
        P = self.P
        vd = max(pt.v, self.v_floor)
        a_t, a_n = pt.a, vd * vd * pt.kappa
        cb, sb = math.cos(beta0), math.sin(beta0)
        # path-frame acceleration [a_t, a_n] in the frame of the reference vehicle (psi0 = theta_d - beta0)
        a_req = (a_t * cb - a_n * sb, a_t * sb + a_n * cb)
        delta0, F0, info = solve_linearizing_input(vd * cb, vd * sb, r0, 0.0, a_req, P, self.gammas, self.u0, self.n)
        self.u0 = (delta0, F0)
        r_dot = info["Mz"] / P.J
        beta_dot = -r0 + (-info["Fx"] * sb + info["Fy"] * cb) / (P.m * vd)
        return r_dot, beta_dot, delta0, F0, info

    def advance(self, t, traj):
        if self.t is None or t <= self.t:
            self.t = t if self.t is None else self.t
            return
        n_sub = max(1, int(math.ceil((t - self.t) / self.h_max - 1e-9)))
        h = (t - self.t) / n_sub
        for i in range(n_sub):
            pt = traj.sample(self.t + i * h)
            r_dot, beta_dot, *_ = self.derivatives(pt, self.r0, self.beta0)
            self.r0 += h * r_dot
            self.beta0 += h * beta_dot
        self.t = t

    @trace("werling2011", section="4.3.3.4", equation="(4.71), (4.74)", concept="dynamic_reference_transform")
    def reference(self, pt, lam):
        r0, b0 = self.r0, self.beta0
        r_dot, beta_dot, delta0, F0, info = self.derivatives(pt, r0, b0)
        v0 = max(pt.v, self.v_floor)
        psi0 = pt.theta - b0                                                              # (4.71)
        bt, vt, btd, vtd = point_kinematics(v0, b0, r0, lam, pt.a, beta_dot, r_dot)
        return {"y1": pt.x + lam * math.cos(psi0), "y2": pt.y + lam * math.sin(psi0), "theta": psi0 + bt,
                "kappa": (r0 + btd) / vt, "v": vt, "v_dot": vtd, "delta0": delta0, "F0": F0, "psi0": psi0,
                "beta0": b0, "r0": r0, "saturated": info["saturated"]}                   # (4.74)


# ----------------------------------------------------------------------------- component
@dataclass
class DynamicParams:
    zeta: float = param(1.0, "-", "Dämpfungsgrad der Nulldynamik zeta (4.70)", min=0.3, max=3.0)
    lam_fixed: float = param(-100.0, "m", "festes lambda (< -50: geschwindigkeitsabhängig nach (4.70))")
    lam_min: float = param(0.0, "m", "minimales lambda", min=-1.5, max=30.0)
    lam_max: float = param(20.0, "m", "maximales lambda", min=0.0, max=50.0)
    lam_rate: float = param(4.0, "m/s", "max. Änderungsrate von lambda", min=0.0)
    pole_n1: float = param(-1.18, "1/s", "Pol 1 Querfehler", max=0.0)
    pole_n2: float = param(-3.82, "1/s", "Pol 2 Querfehler", max=0.0)
    pole_t1: float = param(-0.29, "1/s", "Pol 1 Längsfehler", max=0.0)
    pole_t2: float = param(-1.71, "1/s", "Pol 2 Längsfehler", max=0.0)
    k_delta: float = param(10.0, "1/s", "Lenkwinkel-Rückführung k_delta (4.75)", min=0.0)
    gamma_drive: float = param(-1.0, "-", "Kräfteverhältnis Antrieb (<0: aus Antriebslayout)", min=-1, max=1)
    gamma_brake: float = param(0.75, "-", "Kräfteverhältnis Bremsen", min=0, max=1)
    saturation_exponent: int = param(16, "-", "Exponent n der Sättigungsmodifikation", min=2, max=60)
    reference_transform: str = param("dynamic", "", "Sollgrößentransformation: dynamic / static / none",
                                     choices=["dynamic", "static", "none"])
    v_floor: float = param(1.0, "m/s", "Mindestgeschwindigkeit der Nulldynamik-Simulation", min=0.1)
    mu: float = param(-1.0, "-", "Reibwert (<0: aus Fahrzeug/Umgebung)")


def gains_from_poles(p1, p2):
    # characteristic polynomial (s - p1)(s - p2) = s^2 + k2 s + k1
    return p1 * p2, -(p1 + p2)


@component
class WerlingDynamic(TrackingControllerBase):
    NAME = "werling_dynamic"
    VERSION = "1.0.0"
    LABEL = "Werling: exakte E/A-Linearisierung (Satz 8)"
    PARAMS = DynamicParams
    INPUTS = {"ego": Port("EgoState", "Fahrzeugzustand (Schwerpunkt)"),
              "trajectory": Port("PlannedTrajectory", "Solltrajektorie des Schwerpunkts")}
    DOC = ComponentDoc(
        summary="Exakt E/A-linearisierender Trackingregler auf dem dynamischen Einspurmodell mit isotropem "
                "Pacejka-Reifen für schnelle Fahrt.",
        purpose="Stabilisiert einen Referenzpunkt lambda vor dem Schwerpunkt invariant auf der Solltrajektorie; "
                "die dynamische Sollgrößentransformation beseitigt den Schleppfehler, die geschwindigkeitsabhängige "
                "Vorausschau hält die Dämpfung der Nulldynamik konstant (Werling 4.3).",
        theory="Ausgang (4.46), invariante Fehler (4.48), relativer Grad [2,2], linearisierende Rückführung als "
               "Lösung von (4.60) (2D-Newton), lineare Stabilisierung (4.68)/(4.69), Nulldynamik (4.67), "
               "lambda(zeta, v_d) (4.70), Online-Simulation der Nulldynamik (4.71)-(4.74), Lenkratenregelung (4.75).",
        assumptions=["Ebene Fahrbahn, keine dynamischen Radlasten (Einspurmodell)",
                     "Reifenparameter A, B, C je Achse bekannt (Certainty Equivalence)",
                     "Antriebs-/Bremskräfte schnell eingeregelt, Kräfteverhältnis gamma bekannt",
                     "v > 0 (Vorwärtsfahrt, singulär bei v = 0)"],
        limitations=["Nur lokal (Reifensättigung, Bedingung (4.49))",
                     "Stellgrößenbeschränkungen nicht im Regelgesetz",
                     "Nulldynamik nur für Geradeausfahrt linear analysiert (Satz 9)"],
        design_decisions=["(4.60) über die äquivalente Bedingung der Referenzpunktbeschleunigung in "
                          "Fahrzeugkoordinaten gelöst", "Sättigungsmodifikation nur an der Vorderachse "
                          "(Eingang delta), Hinterachse mit Kammschem Kreis",
                          "kappa~_d_dot der transformierten Sollgröße numerisch (Rückwärtsdifferenz)"],
        references=["werling2011", "isidori1995", "khalil2002", "pacejka2012"],
        equations=["werling2011:(4.39)-(4.45)", "werling2011:(4.46)", "werling2011:(4.48)", "werling2011:(4.50)-(4.60)",
                   "werling2011:(4.67)-(4.75)"],
        validation=["tests/stabilization/test_stabilization_dynamic.py"],
        concepts=["exact_io_linearization", "zero_dynamics_desm", "dynamic_reference_transform", "isotropic_tire"],
        expert="Nach Linearisierung gilt $\\ddot{\\tilde e}_t=\\tilde w_2$, $\\ddot{\\tilde e}_n=\\tilde w_1$; mit "
               "(4.68)/(4.69) und $k>0$ konvergieren die Fehler exponentiell. Die Nulldynamik (4.67) ist für "
               "$\\lambda>\\max(-l_h,-J/[l_vm])$ stabil (Satz 9), ihre Dämpfung $\\zeta$ wird über (4.70) "
               "konstant gehalten.")

    def reset(self, context):
        super().reset(context)
        p = self.params
        cfg = vehicle_config(context)
        self.P = design_parameters(context, p.mu)
        g_drive = drive_share(cfg) if p.gamma_drive < 0 else p.gamma_drive
        self.gammas = (g_drive, p.gamma_brake)
        self.kn1, self.kn2 = gains_from_poles(p.pole_n1, p.pole_n2)
        self.kt1, self.kt2 = gains_from_poles(p.pole_t1, p.pole_t2)
        self.zd = ZeroDynamicsReference(self.P, self.gammas, p.saturation_exponent, v_floor=p.v_floor)
        self.lam = None
        self.t_prev = None
        self.delta0_prev = None
        self.u1_prev = None
        self.omega_prev = None
        self.traj_id = None
        self.u = (0.0, 0.0)
        self.timer = StepTimer()
        self.last = {}

    def activate(self, t, ego):
        # (re)start: zero dynamics with the current vehicle states (Remark 10)
        self.zd.initialize(t, ego.r, math.atan2(ego.vy, max(ego.vx, 0.1)), ego.delta, 0.0)
        self.t_prev = None
        self.delta0_prev = self.u1_prev = self.omega_prev = None
        self.u = (ego.delta, self.u[1])

    def lookahead(self, v_d, dt):
        p = self.params
        if p.lam_fixed > -50.0:
            return p.lam_fixed
        lam = lookahead_for_damping(p.zeta, v_d, self.P)
        lam = p.lam_min if not math.isfinite(lam) else min(max(lam, p.lam_min), p.lam_max)
        lam = max(lam, minimum_phase_bound(self.P) + 0.05)
        if self.lam is not None and p.lam_rate > 0 and dt > 0:
            lam = min(max(lam, self.lam - p.lam_rate * dt), self.lam + p.lam_rate * dt)
        return lam

    def _reference(self, traj, pt, lam):
        mode = self.params.reference_transform
        if mode == "dynamic":
            return self.zd.reference(pt, lam)
        if mode == "static":
            r = flat_reference_transform(pt.x, pt.y, pt.theta, pt.kappa, pt.dkappa * pt.v, pt.dkappa, pt.v, pt.a, lam)
            return {**r, "delta0": None}
        return {"y1": pt.x, "y2": pt.y, "theta": pt.theta, "kappa": pt.kappa, "v": pt.v, "v_dot": pt.a, "delta0": None}

    def step(self, t, inputs):
        ego, traj = inputs.get("ego"), inputs.get("trajectory")
        if ego is None:
            return {"command": None, "status": empty_status(t, self.NAME)}
        if traj is None or traj.empty:
            return {"command": hold_command(t, ego, self.NAME), "status": empty_status(t, self.NAME)}
        start = time.perf_counter()
        P, p = self.P, self.params
        if self.zd.t is None or (traj.reinitialized and id(traj) != self.traj_id):
            self.activate(t, ego)
        self.traj_id = id(traj)
        dt = 0.0 if self.t_prev is None else t - self.t_prev
        self.zd.advance(t, traj)
        pt = traj.sample(t)
        lam = self.lam = self.lookahead(pt.v, dt)
        ref = self._reference(traj, pt, lam)

        # vehicle quantities of the reference point (4.46), (4.52)-(4.54)
        vx, vy, r, psi = ego.vx, ego.vy, ego.r, ego.psi
        vx_s = max(vx, 0.1)
        beta = math.atan2(vy, vx_s)
        bt = math.atan((vy + lam * r) / vx_s)
        vt = vx_s / math.cos(bt)
        px, py = ego.x + lam * math.cos(psi), ego.y + lam * math.sin(psi)
        err = frenet_errors(px, py, psi + bt, vt, ref["y1"], ref["y2"], ref["theta"], ref["v"], ref["kappa"])
        e, e_dot = (err["e_t"], err["e_n"]), (err["e_t_dot"], err["e_n_dot"])
        w1 = -self.kn1 * e[1] - self.kn2 * e_dot[1]                                        # (4.68)
        w2 = -self.kt1 * e[0] - self.kt2 * e_dot[0]                                        # (4.69)
        omega = ref["v"] * ref["kappa"]
        omega_dot = (omega - self.omega_prev) / dt if (self.omega_prev is not None and dt > 0) else 0.0
        a_req = _required_point_acceleration(ref, e, e_dot, (w2, w1), omega, omega_dot, psi)
        delta_star, F_star, info = solve_linearizing_input(vx_s, vy, r, lam, a_req, P, self.gammas, self.u,
                                                           p.saturation_exponent)
        self.u = (delta_star, F_star)
        # feedforward of the steering rate from the noise-free delta0 of the zero dynamics (4.75)
        d_ff_src = ref["delta0"] if ref.get("delta0") is not None else delta_star
        prev = self.delta0_prev if ref.get("delta0") is not None else self.u1_prev
        delta_ff = (d_ff_src - prev) / dt if (prev is not None and dt > 0) else 0.0
        u_rate = delta_ff - p.k_delta * (ego.delta - delta_star)                          # (4.75)
        self.delta0_prev = ref.get("delta0")
        self.u1_prev, self.omega_prev, self.t_prev = delta_star, omega, t

        cog = frenet_errors(ego.x, ego.y, psi + beta, math.hypot(vx, vy), pt.x, pt.y, pt.theta, pt.v, pt.kappa)
        self.timer.add(time.perf_counter() - start)
        a_exp = info["Fx"] / P.m + r * vy
        self.last = {"ref": ref, "err": err, "info": info, "lam": lam}
        self.signals = {"lambda": lam, "e_n_point": err["e_n"], "e_n": cog["e_n"], "delta_star": delta_star,
                        "F_star": F_star, "saturated": float(info["saturated"])}
        cmd = ControlCommand(t=t, steer_rate=float(u_rate), force=float(F_star), direction=1, controller=self.NAME,
                             info={"a_expected": a_exp, "gamma": info["gamma"], "delta_star": delta_star,
                                   "saturated": info["saturated"]})
        status = ControllerStatus(t=t, e_t=cog["e_t"], e_n=cog["e_n"], e_theta=cog["e_theta"],
                                  e_v=math.hypot(vx, vy) - pt.v, e_t_dot=cog["e_t_dot"], e_n_dot=cog["e_n_dot"],
                                  active_controller=self.NAME, lookahead=lam,
                                  info={"e_t_point": err["e_t"], "e_n_point": err["e_n"], "reference_point": "cog",
                                        "tire_saturated": info["saturated"], "newton_iterations": info["iterations"]})
        return {"command": cmd, "status": status}


__all__ = ["WerlingDynamic", "ZeroDynamicsReference", "lookahead_for_damping", "minimum_phase_bound",
           "point_kinematics", "solve_linearizing_input", "zero_dynamics_coefficients", "wrap"]
