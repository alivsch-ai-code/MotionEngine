"""Classical lateral trajectory tracking controllers (for comparison with the Werling controllers).

    tracking_controller/pure_pursuit   geometric, rear-axle reference, speed dependent look-ahead (Snider 2009)
    tracking_controller/stanley        front-axle cross-track error + heading error (Hoffmann/Thrun 2007)
    tracking_controller/lqr            error model of the dynamic single-track model (Rajamani 3.2), discrete
                                       DARE, gain scheduled over the speed, steady-state feedforward
    tracking_controller/mpc            linear time-varying MPC along the trajectory horizon (kinematic model with
                                       understeer gradient, states [e_y, e_psi, delta], input delta_dot), steering
                                       angle and rate constraints, condensed QP solved by ADMM

All lateral controllers output steer_angle and (with with_speed_control) an acceleration request of a
feedforward + feedback speed loop; combine them with a longitudinal controller via
tracking_controller/composite. The path errors are taken at the trajectory's reference point (rear axle
or CoG) by projection onto the trajectory polyline; the status carries the time-based invariant errors.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
from scipy.linalg import cho_factor, cho_solve, expm, solve_discrete_are

from ..controllers.esp_controller import understeer_gradient
from ..core.parameters import param
from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import TrackingControllerBase
from ..framework.plugins import component
from ..framework.types import ControlCommand, ControllerStatus
from .common import StepTimer, design_parameters, empty_status, hold_command, vehicle_config, wrap
from .errors import frenet_errors


# ----------------------------------------------------------------------------- projection on the trajectory
def project(traj, px, py, hint=None, window=60):
    """Nearest point of the trajectory polyline: dict(index, s, e_y (left +), theta, kappa, v, a, x, y)."""
    n = len(traj)
    if n == 1:
        i0, i1 = 0, 1
    else:
        c = int(np.clip(hint if hint is not None else 0, 0, n - 2))
        i0, i1 = max(c - window, 0), min(c + window, n - 1)
    x, y = traj.x[i0:i1 + 1], traj.y[i0:i1 + 1]
    if len(x) < 2:
        return {"index": i0, "s": 0.0, "e_y": 0.0, "theta": float(traj.theta[i0]), "kappa": float(traj.kappa[i0]),
                "v": float(traj.v[i0]), "a": float(traj.a[i0]), "x": float(traj.x[i0]), "y": float(traj.y[i0]),
                "w": 0.0}
    dx, dy = np.diff(x), np.diff(y)
    L2 = np.maximum(dx * dx + dy * dy, 1e-12)
    w = np.clip(((px - x[:-1]) * dx + (py - y[:-1]) * dy) / L2, 0.0, 1.0)
    qx, qy = x[:-1] + w * dx, y[:-1] + w * dy
    d2 = (qx - px) ** 2 + (qy - py) ** 2
    # among equal distances (standstill duplicates) prefer the latest in time order near the hint
    k = int(np.argmin(d2 + 1e-9 * np.abs(np.arange(len(d2)) + i0 - (hint or 0))))
    i, wk = i0 + k, float(w[k])
    th0, th1 = traj.theta[i], traj.theta[i + 1]
    th = float(th0 + wk * wrap(th1 - th0))
    ex, ey = px - qx[k], py - qy[k]
    lerp = lambda a: float(a[i] + wk * (a[i + 1] - a[i]))  # noqa: E731
    return {"index": i, "w": wk, "s": lerp(traj.s), "e_y": float(-math.sin(th) * ex + math.cos(th) * ey), "theta": th,
            "kappa": lerp(traj.kappa), "v": lerp(traj.v), "a": lerp(traj.a), "x": float(qx[k]), "y": float(qy[k])}


def point_along(traj, index, w, distance):
    # point `distance` further along the polyline from (index, w)
    n = len(traj)
    i = index
    x, y = traj.x[i] + w * (traj.x[i + 1] - traj.x[i]), traj.y[i] + w * (traj.y[i + 1] - traj.y[i])
    remaining = distance
    while i < n - 1:
        seg = math.hypot(traj.x[i + 1] - x, traj.y[i + 1] - y)
        if seg >= remaining:
            f = remaining / max(seg, 1e-12)
            return x + f * (traj.x[i + 1] - x), y + f * (traj.y[i + 1] - y)
        remaining -= seg
        i += 1
        x, y = traj.x[i], traj.y[i]
    th = traj.theta[-1]
    return x + remaining * math.cos(th), y + remaining * math.sin(th)


def time_index(traj, t):
    return int(np.clip(np.searchsorted(traj.t, t) - 1, 0, max(len(traj) - 2, 0)))


# ----------------------------------------------------------------------------- base class
@dataclass
class _SpeedLoopParams:
    with_speed_control: bool = param(True, "", "eigene Geschwindigkeitsführung (FF + FB)")
    k_v: float = param(1.0, "1/s", "Speed loop: Verstärkung Geschwindigkeitsfehler", min=0.0)
    k_s: float = param(0.3, "1/s²", "Speed loop: Verstärkung Längsfehler", min=0.0)


class ClassicBase(TrackingControllerBase):
    VERSION = "1.0.0"
    PARAMS = _SpeedLoopParams

    def reset(self, context):
        super().reset(context)
        self.cfg = vehicle_config(context)
        self.P = design_parameters(context)
        self.limit = self.cfg.vehicle.max_steer_angle
        self.hint = None
        self.timer = StepTimer()

    def ref_point(self, ego, traj):
        # ego point and its course matching the trajectory's reference point
        if traj.reference_point == "rear_axle":
            x, y = ego.rear_axle(self.P.lh)
            course = ego.psi if ego.vx >= -0.05 else ego.psi + math.pi
            return x, y, course, abs(ego.vx)
        return ego.x, ego.y, ego.psi + math.atan2(ego.vy, max(abs(ego.vx), 0.1)), math.hypot(ego.vx, ego.vy)

    def errors(self, t, ego, traj):
        px, py, course, speed = self.ref_point(ego, traj)
        pt = traj.sample(t)
        e = frenet_errors(px, py, course, speed, pt.x, pt.y, pt.theta, pt.v, pt.kappa)
        hint = self.hint if self.hint is not None else time_index(traj, t)
        proj = project(traj, px, py, hint)
        self.hint = proj["index"]
        return pt, e, proj, (px, py, course, speed)

    def speed_loop(self, pt, e, speed):
        p = self.params
        if not getattr(p, "with_speed_control", True):
            return None
        return pt.a + p.k_v * (pt.v - speed) - p.k_s * e["e_t"]

    def finish(self, t, steer, accel, pt, e, speed, info=None, horizon=None):
        steer = float(np.clip(steer, -self.limit, self.limit))
        cmd = ControlCommand(t=t, steer_angle=steer, accel=None if accel is None else float(accel),
                             direction=1, controller=self.NAME, info=info or {})
        st = ControllerStatus(t=t, e_t=e["e_t"], e_n=e["e_n"], e_theta=e["e_theta"], e_v=speed - pt.v,
                              e_t_dot=e["e_t_dot"], e_n_dot=e["e_n_dot"], active_controller=self.NAME,
                              info=dict(info or {}))
        if horizon is not None:
            st.horizon_x, st.horizon_y = horizon
        self.signals = {"e_n": e["e_n"], "steer": steer}
        return {"command": cmd, "status": st}

    def step(self, t, inputs):
        ego, traj = inputs.get("ego"), inputs.get("trajectory")
        if ego is None:
            return {"command": None, "status": empty_status(t, self.NAME)}
        if traj is None or traj.empty:
            return {"command": hold_command(t, ego, self.NAME), "status": empty_status(t, self.NAME)}
        start = time.perf_counter()
        out = self.control(t, ego, traj)
        self.timer.add(time.perf_counter() - start)
        return out


# ----------------------------------------------------------------------------- Pure Pursuit
@dataclass
class PurePursuitParams(_SpeedLoopParams):
    lookahead_gain: float = param(0.8, "s", "Vorausschauzeit k (L_d = k v)", min=0.0)
    lookahead_min: float = param(4.0, "m", "minimale Vorausschau", min=0.5)


@component
class PurePursuit(ClassicBase):
    NAME = "pure_pursuit"
    LABEL = "Pure Pursuit"
    PARAMS = PurePursuitParams
    DOC = ComponentDoc(
        summary="Geometrischer Querregler: Kreisbogen von der Hinterachse zu einem Zielpunkt auf der Bahn.",
        purpose="Einfacher, robuster Vergleichsregler (Snider 2009).",
        theory="$\\delta=\\arctan(2l\\sin\\alpha/L_d)$, $L_d=\\max(L_{min},kv)$, $\\alpha$ Winkel zum Zielpunkt.",
        assumptions=["Kinematisches Fahrzeug, Vorwärtsfahrt"],
        limitations=["Schneidet Kurven, stationärer Querfehler bei großer Vorausschau", "Keine Rückwärtsfahrt"],
        references=["snider2009", "rajamani2012"],
        validation=["tests/stabilization/test_stabilization_classic.py"],
        concepts=["pure_pursuit"],
        expert="Für kleine Fehler entspricht Pure Pursuit einem P-Regler auf den Querfehler mit Verstärkung "
               "$2/L_d^2$; die Stabilität folgt aus der positiven Vorausschau (Snider 2009).")

    @trace("snider2009", section="2.2", concept="pure_pursuit")
    def control(self, t, ego, traj):
        p, l = self.params, self.P.l
        pt, e, proj, (px, py, course, speed) = self.errors(t, ego, traj)
        rx, ry = ego.rear_axle(self.P.lh)
        rproj = project(traj, rx, ry, proj["index"])
        Ld = max(p.lookahead_min, p.lookahead_gain * speed)
        tx, ty = point_along(traj, rproj["index"], rproj["w"], Ld)
        alpha = wrap(math.atan2(ty - ry, tx - rx) - ego.psi)
        delta = math.atan2(2.0 * l * math.sin(alpha), Ld)
        return self.finish(t, delta, self.speed_loop(pt, e, speed), pt, e, speed, {"lookahead": Ld})


# ----------------------------------------------------------------------------- Stanley
@dataclass
class StanleyParams(_SpeedLoopParams):
    gain: float = param(1.5, "1/s", "Stanley-Verstärkung k", min=0.0)
    softening: float = param(1.0, "m/s", "Weichmachung k_soft", min=0.0)
    yaw_damping: float = param(0.08, "s", "Gierratendämpfung", min=0.0)
    feedforward: bool = param(True, "", "Krümmungsvorsteuerung")


@component
class Stanley(ClassicBase):
    NAME = "stanley"
    LABEL = "Stanley"
    PARAMS = StanleyParams
    DOC = ComponentDoc(
        summary="Querregler auf Vorderachs-Querfehler und Kurswinkelfehler (Stanley, DARPA Grand Challenge).",
        purpose="Vergleichsregler mit guter Spurtreue bei mittleren Geschwindigkeiten.",
        theory="$\\delta=\\theta_e+\\arctan(-k e_{fa}/(k_{soft}+v))+\\delta_{ff}-k_r(r-v\\kappa)$.",
        assumptions=["Vorwärtsfahrt"], limitations=["Keine Rückwärtsfahrt, kinematische Herleitung"],
        references=["hoffmann2007", "snider2009"],
        validation=["tests/stabilization/test_stabilization_classic.py"], concepts=["stanley"],
        expert="Für das kinematische Modell konvergiert der Vorderachsfehler exponentiell, "
               "$\\dot e=-v\\sin(\\arctan(ke/v))$ (Hoffmann et al. 2007).")

    @trace("hoffmann2007", concept="stanley")
    def control(self, t, ego, traj):
        p, P = self.params, self.P
        pt, e, proj, (px, py, course, speed) = self.errors(t, ego, traj)
        fx, fy = ego.point_ahead(P.lv)
        if traj.reference_point == "rear_axle":
            fx, fy = ego.point_ahead(P.lv)   # path of the rear axle: front-axle error still meaningful
        fproj = project(traj, fx, fy, proj["index"])
        v = max(ego.vx, 0.0)
        heading = wrap(fproj["theta"] - ego.psi) if traj.reference_point == "rear_axle" else \
            wrap(fproj["theta"] - course)
        ff = 0.0
        if p.feedforward:
            eg = understeer_gradient(self.cfg)
            ff = math.atan(P.l * fproj["kappa"]) + eg * v * v * fproj["kappa"]
        delta = heading + math.atan2(-p.gain * fproj["e_y"], p.softening + v) + ff \
            - p.yaw_damping * (ego.r - v * fproj["kappa"])
        return self.finish(t, delta, self.speed_loop(pt, e, speed), pt, e, speed, {"e_front": fproj["e_y"]})


# ----------------------------------------------------------------------------- LQR
@dataclass
class LQRParams(_SpeedLoopParams):
    q_e: float = param(1.0, "1/m²", "Gewicht Querfehler", min=0.0)
    q_e_dot: float = param(0.0, "s²/m²", "Gewicht Querfehlerrate", min=0.0)
    q_psi: float = param(1.0, "1/rad²", "Gewicht Kursfehler", min=0.0)
    q_psi_dot: float = param(0.0, "s²/rad²", "Gewicht Kursfehlerrate", min=0.0)
    r_delta: float = param(10.0, "1/rad²", "Gewicht Lenkwinkel", min=1e-6)
    dt: float = param(0.01, "s", "Diskretisierung", min=0.001)
    v_min: float = param(2.0, "m/s", "untere Stützstelle Gain-Scheduling", min=0.5)
    v_max: float = param(50.0, "m/s", "obere Stützstelle Gain-Scheduling", min=5.0)


@trace("rajamani2012", section="3.2", concept="lqr_lateral", note="Fehlermodell des Einspurmodells")
def lateral_error_model(v, P):
    cf, cr, m, J, lf, lr = P.cv, P.ch, P.m, P.J, P.lv, P.lh
    A = np.array([[0, 1, 0, 0],
                  [0, -(cf + cr) / (m * v), (cf + cr) / m, (-cf * lf + cr * lr) / (m * v)],
                  [0, 0, 0, 1],
                  [0, -(cf * lf - cr * lr) / (J * v), (cf * lf - cr * lr) / J, -(cf * lf**2 + cr * lr**2) / (J * v)]])
    B = np.array([[0.0], [cf / m], [0.0], [cf * lf / J]])
    return A, B


@component
class LQR(ClassicBase):
    NAME = "lqr"
    LABEL = "LQR (geschwindigkeitsgeplant)"
    PARAMS = LQRParams
    DOC = ComponentDoc(
        summary="Zustandsregler auf das Querfehlermodell des Einspurmodells mit diskreter Riccati-Lösung, "
                "Gain-Scheduling über die Geschwindigkeit und stationärer Vorsteuerung.",
        purpose="Optimaler linearer Vergleichsregler (Rajamani 3.2).",
        theory="$x=[e_1,\\dot e_1,e_2,\\dot e_2]$, $u=-Kx+\\delta_{ff}$, $K$ aus der DARE des mit ZOH "
               "diskretisierten Modells, $\\delta_{ff}=l\\kappa+K_V v^2\\kappa-k_3e_{2,ss}$.",
        assumptions=["Lineare Reifen, kleine Winkel, Vorwärtsfahrt"],
        limitations=["Linearisierung, Modell singulär bei v -> 0 (v_min)"],
        references=["rajamani2012"], validation=["tests/stabilization/test_stabilization_classic.py"],
        concepts=["lqr_lateral"],
        expert="Für jedes feste $v$ ist der geschlossene diskrete Kreis $A_d-B_dK$ asymptotisch stabil "
               "(stabilisierbares Paar, $Q\\geq0$ beobachtbar); langsames Gain-Scheduling erhält die Stabilität.")

    def reset(self, context):
        super().reset(context)
        p = self.params
        self.grid = np.linspace(p.v_min, p.v_max, 25)
        Q = np.diag([p.q_e, p.q_e_dot, p.q_psi, p.q_psi_dot])
        R = np.array([[p.r_delta]])
        gains = []
        for v in self.grid:
            A, B = lateral_error_model(v, self.P)
            M = np.zeros((5, 5))
            M[:4, :4], M[:4, 4:] = A, B
            Md = expm(M * p.dt)
            Ad, Bd = Md[:4, :4], Md[:4, 4:]
            X = solve_discrete_are(Ad, Bd, Q, R)
            gains.append(np.linalg.solve(R + Bd.T @ X @ Bd, Bd.T @ X @ Ad).ravel())
        self.gains = np.array(gains)
        self.eg = understeer_gradient(self.cfg)

    def gain(self, v):
        return np.array([np.interp(v, self.grid, self.gains[:, i]) for i in range(4)])

    @trace("rajamani2012", section="3.2", concept="lqr_lateral")
    def control(self, t, ego, traj):
        P = self.P
        pt, e, proj, (px, py, course, speed) = self.errors(t, ego, traj)
        v = max(ego.vx, self.params.v_min)
        kap = proj["kappa"]
        e1 = proj["e_y"]
        e2 = wrap(ego.psi - proj["theta"])
        e1_dot = ego.vy + ego.vx * e2
        e2_dot = ego.r - ego.vx * kap
        K = self.gain(v)
        e2_ss = -P.lh * kap + P.lv * P.m * v * v * kap / (P.ch * P.l)
        ff = P.l * kap + self.eg * v * v * kap - K[2] * e2_ss
        delta = -float(K @ np.array([e1, e1_dot, e2, e2_dot])) + ff
        return self.finish(t, delta, self.speed_loop(pt, e, speed), pt, e, speed, {"K": K.tolist()})


# ----------------------------------------------------------------------------- MPC
def admm_qp(H, g, A, lo, hi, rho=1.0, sigma=1e-6, alpha=1.6, iters=400, eps=1e-6, warm=None):
    """min 1/2 x'Hx + g'x  s.t. lo <= A x <= hi  (OSQP-type ADMM, dense)."""
    n, m = H.shape[0], A.shape[0]
    x = np.zeros(n) if warm is None else warm[0].copy()
    z = np.clip(A @ x, lo, hi)
    y = np.zeros(m) if warm is None else warm[1].copy()
    K = cho_factor(H + sigma * np.eye(n) + rho * A.T @ A)
    for _ in range(iters):
        xt = cho_solve(K, sigma * x - g + A.T @ (rho * z - y))
        zt = A @ xt
        x = alpha * xt + (1 - alpha) * x
        zr = alpha * zt + (1 - alpha) * z
        z_new = np.clip(zr + y / rho, lo, hi)
        y = y + rho * (zr - z_new)
        r_prim = np.max(np.abs(A @ x - z_new)) if m else 0.0
        r_dual = np.max(np.abs(rho * A.T @ (z_new - z))) if m else 0.0
        z = z_new
        if r_prim < eps and r_dual < eps:
            break
    return x, (x, y)


@dataclass
class MPCParams(_SpeedLoopParams):
    horizon: int = param(20, "-", "Prädiktionsschritte N", min=3, max=100)
    dt: float = param(0.05, "s", "Prädiktionsschrittweite", min=0.005)
    q_e: float = param(4.0, "1/m²", "Gewicht Querfehler", min=0.0)
    q_psi: float = param(4.0, "1/rad²", "Gewicht Kursfehler", min=0.0)
    r_delta: float = param(1.0, "1/rad²", "Gewicht Lenkwinkel gegenüber Vorsteuerung", min=0.0)
    r_rate: float = param(0.5, "s²/rad²", "Gewicht Lenkrate", min=1e-6)
    max_rate: float = param(0.6, "rad/s", "max. Lenkrate", min=0.01)
    max_angle: float = param(-1.0, "rad", "max. Lenkwinkel (<0: Fahrzeug)")
    update_period: float = param(0.05, "s", "Neuberechnungsperiode", min=0.0)


@component
class MPC(ClassicBase):
    NAME = "mpc"
    LABEL = "MPC (linear zeitvariant)"
    PARAMS = MPCParams
    DOC = ComponentDoc(
        summary="Linear zeitvariante modellprädiktive Querregelung entlang des Trajektorienhorizonts mit "
                "Lenkwinkel- und Lenkratenbeschränkung.",
        purpose="Vergleichsregler, der Stellgrößenbeschränkungen explizit berücksichtigt (Werling Tab. 4.1).",
        theory="Zustände $[e_y,e_\\psi,\\delta]$, Eingang $\\dot\\delta$; $\\dot e_y=v_ke_\\psi$, "
               "$\\dot e_\\psi=v_k(\\delta/(l+EG\\,v_k^2)-\\kappa_k)$ mit $v_k,\\kappa_k$ der Solltrajektorie zu "
               "den Horizontzeitpunkten; kondensiertes QP, gelöst mit ADMM.",
        assumptions=["Kinematik mit Untersteuergradient (quasi-stationäre Gierdynamik)", "Vorwärtsfahrt"],
        limitations=["Kein Stabilitätsbeweis ohne Endkosten/Endbeschränkung", "Rechenaufwand höher"],
        references=["rajamani2012", "borrelli2017", "werling2011"],
        validation=["tests/stabilization/test_stabilization_classic.py"], concepts=["mpc_lateral"],
        expert="Rekursive Machbarkeit ist durch die Box-Beschränkungen allein nicht garantiert; in der Praxis "
               "stabil bei hinreichend langem Horizont (Rawlings/Mayne).")

    def reset(self, context):
        super().reset(context)
        self.eg = understeer_gradient(self.cfg)
        self.plan_t = None
        self.plan = None
        self.delta_cmd = None
        self.warm = None
        self.horizon_xy = None

    @trace("borrelli2017", concept="mpc_lateral", note="LTV-MPC entlang der Solltrajektorie")
    def solve(self, t, ego, traj, e_y, e_psi, delta0):
        p, P = self.params, self.P
        N, Ts = p.horizon, p.dt
        dmax = p.max_angle if p.max_angle > 0 else self.limit
        nx = 3
        pts = [traj.sample(t + k * Ts) for k in range(N + 1)]
        # affine LTV prediction x_{k+1} = A_k x_k + B u_k + c_k
        X0 = np.zeros((N, nx))
        Gam = np.zeros((N, nx, N))
        x_free = np.array([e_y, e_psi, delta0])
        Gk = np.zeros((nx, N))
        dref = np.zeros(N)
        for k in range(N):
            v, kap = max(pts[k].v, 0.5), pts[k].kappa
            Leff = P.l + self.eg * v * v
            A = np.array([[1, Ts * v, 0], [0, 1, Ts * v / Leff], [0, 0, 1]])
            B = np.array([0, 0, Ts])
            c = np.array([0, -Ts * v * kap, 0])
            x_free = A @ x_free + c
            Gk = A @ Gk
            Gk[:, k] += B
            X0[k], Gam[k] = x_free, Gk
            dref[k] = math.atan(Leff * pts[k + 1].kappa)
        Q = np.diag([p.q_e, p.q_psi, p.r_delta])
        H = p.r_rate * np.eye(N)
        g = np.zeros(N)
        for k in range(N):
            ref = np.array([0.0, 0.0, dref[k]])
            H += Gam[k].T @ Q @ Gam[k]
            g += Gam[k].T @ Q @ (X0[k] - ref)
        A_c = np.vstack([np.eye(N), Ts * np.tril(np.ones((N, N)))])
        lo = np.concatenate([-p.max_rate * np.ones(N), -dmax - delta0 * np.ones(N)])
        hi = np.concatenate([p.max_rate * np.ones(N), dmax - delta0 * np.ones(N)])
        u, self.warm = admm_qp(H, g, A_c, lo, hi, warm=self.warm)
        X = X0 + np.einsum("kij,j->ki", Gam, u)
        hx = np.array([pts[k + 1].x - X[k, 0] * math.sin(pts[k + 1].theta) for k in range(N)])
        hy = np.array([pts[k + 1].y + X[k, 0] * math.cos(pts[k + 1].theta) for k in range(N)])
        return u, X, (hx, hy)

    def control(self, t, ego, traj):
        p = self.params
        pt, e, proj, (px, py, course, speed) = self.errors(t, ego, traj)
        e_y, e_psi = e["e_n"], e["e_theta"]
        if self.plan_t is None or t - self.plan_t >= p.update_period - 1e-9:
            # plan from the commanded angle (continuous command; the measured angle lags behind the actuator)
            d0 = ego.delta if self.delta_cmd is None else self.delta_cmd
            u, X, self.horizon_xy = self.solve(t, ego, traj, e_y, e_psi, d0)
            self.plan_t, self.plan, self.delta_plan0 = t, u, d0
        tau = t - self.plan_t
        k = min(int(tau / p.dt), len(self.plan) - 1)
        delta = self.delta_plan0 + p.dt * float(np.sum(self.plan[:k])) + (tau - k * p.dt) * self.plan[k]
        self.delta_cmd = delta
        out = self.finish(t, delta, self.speed_loop(pt, e, speed), pt, e, speed,
                          {"steer_rate_plan": float(self.plan[k])}, horizon=self.horizon_xy)
        out["command"].steer_rate = float(self.plan[k])
        return out
