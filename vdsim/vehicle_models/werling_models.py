"""Design models of Werling (2011), chapter 4, as plant models of the vdsim simulator.

WerlingKinematicModel  "werling_kesm"  extended kinematic single-track model (model 1, eq. 4.2):
    rear-axle center [x1, x2], orientation psi, steering angle delta and speed v as states,
    inputs delta_dot and the total longitudinal tire force F_l = F_vl + F_hl with the force ratio
    gamma = F_vl / F_l; effective inertia M = (m l_h^2 + J) / l^2. Free of singularities for
    forward and reverse driving and at standstill (no division by v).
WerlingDynamicModel    "werling_desm"  dynamic single-track model (model 4, eq. 4.39) with the
    isotropic Pacejka tire (4.40) and its lateral/longitudinal coupling (4.42)-(4.45). The plant is
    integrated in vx/vy coordinates (v cos(beta), v sin(beta)), which is identical to model 4 for
    v > 0 and stays defined at v = 0; below v_kin_high the derivatives are blended with the
    kinematic model (no tire slip at standstill).

Both models take the common ControlInput: steer_front is the commanded road-wheel angle, the
real angle follows with a fast first-order steering dynamics (state delta, so that delta_dot
exists), the wheel torques give the axle forces F_vl, F_hl (and thereby gamma); negative drive
torques drive backwards. Driving resistances (aero drag with wind, rolling resistance, optional
road grade env.grade in rad) act on the plant - the design models of the controllers neglect
them, the vehicle-dynamics layer compensates them (Werling 5.1.2.2).
"""

import math
from dataclasses import dataclass

import numpy as np

from ..core.conventions import G
from ..core.interfaces import VehicleModel
from ..core.registry import register
from ..framework.knowledge import trace
from ..simulation.vehicle_state import VehicleState
from ..tire_models import create_tires
from ..tire_models.isotropic import lateral_force, peak_slip
from .common import aero_drag, axle_cornering_stiffness, rolling_resistance

WERLING_MODEL_LABELS = {
    "werling_kesm": "Erweitertes kinematisches Einspurmodell (Werling Modell 1)",
    "werling_desm": "Dynamisches Einspurmodell, isotroper Reifen (Werling Modell 4)",
}


@dataclass
class WerlingParameters:
    # vehicle and axle tire parameters of the Werling design models (SI)
    m: float
    J: float
    lv: float
    lh: float
    R: float
    max_steer: float
    Av: float          # peak axle force mu F_z,v
    Bv: float          # shape factor
    Cv: float          # stiffness factor, c_v = Av Bv Cv
    Ah: float
    Bh: float
    Ch: float
    mu: float = 1.0

    @property
    def l(self):
        return self.lv + self.lh

    @property
    def M(self):
        # effective inertia of the kinematic model (Werling 4.2.1)
        return (self.m * self.lh**2 + self.J) / self.l**2

    @property
    def cv(self):
        return self.Av * self.Bv * self.Cv

    @property
    def ch(self):
        return self.Ah * self.Bh * self.Ch

    @property
    def s_max_v(self):
        return peak_slip(self.Bv, self.Cv)

    @property
    def s_max_h(self):
        return peak_slip(self.Bh, self.Ch)

    def with_mu(self, mu):
        # same cornering stiffness c = A B C, peak force scaled with the friction coefficient
        scale = mu / self.mu
        return WerlingParameters(self.m, self.J, self.lv, self.lh, self.R, self.max_steer,
                                 self.Av * scale, self.Bv, self.Cv / scale, self.Ah * scale, self.Bh,
                                 self.Ch / scale, mu)


def werling_parameters(config, mu=None):
    # WerlingParameters from a VehicleConfig: A = mu F_z,axle, c = A B C = axle cornering stiffness
    p, tp = config.vehicle, config.tires
    mu = tp.mu if mu is None else mu
    tire_f, tire_r = create_tires(tp)
    fz_f, fz_r = p.static_axle_loads
    c_f = axle_cornering_stiffness(tire_f, fz_f / 2)
    c_r = axle_cornering_stiffness(tire_r, fz_r / 2)
    B = tp.shape_lateral
    Av, Ah = mu * fz_f, mu * fz_r
    return WerlingParameters(m=p.mass, J=p.inertia_z, lv=p.cg_to_front, lh=p.cg_to_rear, R=p.wheel_radius,
                             max_steer=p.max_steer_angle, Av=Av, Bv=B, Cv=c_f / (Av * B), Ah=Ah, Bh=B,
                             Ch=c_r / (Ah * B), mu=mu)


@trace("werling2011", section="4.3.2", equation="(4.44), (4.45)", concept="desm")
def slip_angles(vx, vy, r, delta, lv, lh, v_floor=0.0):
    # front/rear slip angles; equals (4.45) for vx > 0, physically signed for reverse driving
    vfy = vy + lv * r
    cd, sd = math.cos(delta), math.sin(delta)
    wx = vx * cd + vfy * sd                 # front wheel velocity in wheel coordinates
    wy = -vx * sd + vfy * cd
    alpha_v = -math.atan(wy / max(abs(wx), v_floor, 1e-9))
    alpha_h = -math.atan((vy - lh * r) / max(abs(vx), v_floor, 1e-9))
    return alpha_v, alpha_h


@trace("werling2011", section="4.3.1", equation="(4.39)", concept="desm")
def desm_forces(vx, vy, r, delta, F_vl, F_hl, P, mode="plateau", n=16, v_floor=0.0, mu_v=1.0, mu_h=1.0,
                mode_h=None):
    """Body forces of model 4: returns (Fx, Fy, Mz, info) in vehicle coordinates at the CoG.

    Tire lateral forces from the isotropic tire with the prescribed longitudinal axle forces
    (4.40)-(4.45). mu_v/mu_h scale the peak force (road friction), c = A B C stays constant;
    mode / mode_h select the saturation treatment of the front / rear axle (see tire_models.isotropic).
    """
    a_v, a_h = slip_angles(vx, vy, r, delta, P.lv, P.lh, v_floor)
    Av, Ah = P.Av * mu_v, P.Ah * mu_h
    F_vq, S_v, sat_v = lateral_force(math.sin(a_v), F_vl, Av, P.Bv, P.cv / (Av * P.Bv), mode, n)
    F_hq, S_h, sat_h = lateral_force(math.sin(a_h), F_hl, Ah, P.Bh, P.ch / (Ah * P.Bh), mode_h or mode, n)
    cd, sd = math.cos(delta), math.sin(delta)
    Fx = F_vl * cd - F_vq * sd + F_hl
    Fy = F_vl * sd + F_vq * cd + F_hq
    Mz = P.lv * (F_vq * cd + F_vl * sd) - P.lh * F_hq
    return Fx, Fy, Mz, {"alpha_v": a_v, "alpha_h": a_h, "F_vq": F_vq, "F_hq": F_hq, "S_v": S_v, "S_h": S_h,
                        "sat_v": sat_v, "sat_h": sat_h}


@trace("werling2011", section="4.3.1", equation="(4.39)", concept="desm")
def werling_model4(x, delta, F_l, gamma, P, mode="plateau", n=16):
    # Model 4 in the original coordinates x = [x1, x2, psi, r, beta, v] (v > 0), input u = [delta, F_l]
    x1, x2, psi, r, beta, v = x
    F_vl, F_hl = gamma * F_l, (1.0 - gamma) * F_l
    vx, vy = v * math.cos(beta), v * math.sin(beta)
    _, _, Mz, info = desm_forces(vx, vy, r, delta, F_vl, F_hl, P, mode, n)
    F_vq, F_hq = info["F_vq"], info["F_hq"]
    db, dhb = delta - beta, beta
    beta_dot = -r + (F_vq * math.cos(db) + F_vl * math.sin(db) + F_hq * math.cos(dhb) - F_hl * math.sin(dhb)) \
        / (P.m * v)
    v_dot = (-F_vq * math.sin(db) + F_vl * math.cos(db) + F_hq * math.sin(dhb) + F_hl * math.cos(dhb)) / P.m
    return np.array([v * math.cos(psi + beta), v * math.sin(psi + beta), r, Mz / P.J, beta_dot, v_dot])


@trace("werling2011", section="4.2.1", equation="(4.2)", concept="kesm")
def werling_model1(x, u1, u2, gamma, P):
    # Model 1 (extended KESM), x = [x1, x2, psi, delta, v] of the rear-axle center, u1 = delta_dot, u2 = F_l
    _, _, psi, delta, v = x
    t, c = math.tan(delta), math.cos(delta)
    M = P.M
    v_dot = ((1.0 + gamma * (1.0 / c - 1.0)) * u2 - 2.0 * M * v * t / c**2 * u1) / (P.m + M * t * t)
    return np.array([v * math.cos(psi), v * math.sin(psi), v * t / P.l, u1, v_dot])


class _WerlingBase(VehicleModel):
    steer_time_constant = 0.02     # s, fast steering dynamics (delta follows steer_front)
    brake_smoothing_speed = 0.2    # m/s, brakes fade in like vdsim.vehicle_models.common

    def __init__(self, config):
        super().__init__(config)
        self.vp = config.vehicle
        self.P = werling_parameters(config)
        self.resistances = True

    def _axle_forces(self, u, vx):
        # wheel torques -> longitudinal axle forces (brakes act against the motion, hold at standstill)
        fw = (np.asarray(u.drive_torque, dtype=float)
              - np.asarray(u.brake_torque, dtype=float) * math.tanh(vx / self.brake_smoothing_speed)) / self.P.R
        return float(fw[0] + fw[1]), float(fw[2] + fw[3])

    def _resistance(self, vx, env):
        if not self.resistances:
            return 0.0
        grade = float(getattr(env, "grade", 0.0) or 0.0)
        return aero_drag(self.vp, vx, env.wind_speed) + rolling_resistance(self.vp, vx) + self.P.m * G * math.sin(grade)

    def _steer_rate(self, delta, u):
        target = min(max(u.steer_front, -self.P.max_steer), self.P.max_steer)
        return (target - delta) / self.steer_time_constant

    def _fz(self):
        fz_f, fz_r = self.vp.static_axle_loads
        return np.array([fz_f, fz_f, fz_r, fz_r]) / 2


@register("vehicle_model", "werling_kesm")
class WerlingKinematicModel(_WerlingBase):
    state_names = ("x1", "x2", "psi", "delta", "v")   # rear-axle center
    recommended_dt = 0.005

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0, delta=0.0):
        # (x, y) = CoG position, speed signed (negative = reverse)
        lh = self.P.lh
        return np.array([x - lh * math.cos(psi), y - lh * math.sin(psi), psi, delta, speed], dtype=float)

    def design_rhs(self, state, delta_dot, F_l, gamma):
        # pure design model (4.2) without resistances / steering lag
        return werling_model1(state, delta_dot, F_l, gamma, self.P)

    def stable_dt(self, state):
        return 1.0 * self.steer_time_constant

    def derivatives(self, t, s, u, env, with_outputs=False):
        P = self.P
        x1, x2, psi, delta, v = s
        delta_dot = self._steer_rate(delta, u)
        F_vl, F_hl = self._axle_forces(u, v)
        mu = float(env.mu_at(x1, x2))          # road friction relative to the tire reference mu
        F_vl = min(max(F_vl, -mu * P.Av), mu * P.Av)
        F_hl = min(max(F_hl, -mu * P.Ah), mu * P.Ah)
        tan_d, cos_d = math.tan(delta), math.cos(delta)
        # generalized force along the rear-axle path (4.4) plus resistances
        Q = F_hl + F_vl / cos_d - self._resistance(v, env)
        M = P.M
        v_dot = (Q - 2.0 * M * v * tan_d / cos_d**2 * delta_dot) / (P.m + M * tan_d**2)
        r = v * tan_d / P.l
        ds = np.array([v * math.cos(psi), v * math.sin(psi), r, delta_dot, v_dot])
        if not with_outputs:
            return ds
        r_dot = (v_dot * tan_d + v * delta_dot / cos_d**2) / P.l
        vy = P.lh * r
        out = {"r": r, "ax": v_dot - r * vy, "ay": v * r + P.lh * r_dot, "beta": math.atan2(vy, max(abs(v), 1e-3)),
               "delta": delta, "delta_rate": delta_dot, "vx": v, "vy": vy, "F_vl": F_vl, "F_hl": F_hl,
               "gamma": F_vl / (F_vl + F_hl) if abs(F_vl + F_hl) > 1e-6 else 0.0, "fz": self._fz()}
        return ds, out

    def vehicle_state(self, t, s, out):
        x1, x2, psi, delta, v = s
        lh = self.P.lh
        fx = np.array([out["F_vl"], out["F_vl"], out["F_hl"], out["F_hl"]]) / 2
        return VehicleState(t=t, x=x1 + lh * math.cos(psi), y=x2 + lh * math.sin(psi), psi=psi, vx=v,
                            vy=out["vy"], r=out["r"], ax=out["ax"], ay=out["ay"], delta_f=delta, fz=out["fz"], fx=fx)


@register("vehicle_model", "werling_desm")
class WerlingDynamicModel(_WerlingBase):
    state_names = ("x", "y", "psi", "vx", "vy", "r", "delta")   # CoG
    recommended_dt = 0.005
    v_kin_low = 0.5      # m/s, below: purely kinematic derivatives (no tire slip at standstill)
    v_kin_high = 1.5     # m/s, above: purely dynamic (model 4)
    kin_relaxation = 0.05  # s, convergence of vy, r to the kinematic values

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0, delta=0.0):
        return np.array([x, y, psi, speed, 0.0, 0.0, delta], dtype=float)

    def stable_dt(self, state):
        # explicit RK4: fastest lateral eigenvalue (c_v + c_h) / (m v) and the steering lag
        P = self.P
        v = max(abs(state[3]), self.v_kin_low)
        lam = max((P.cv + P.ch) / (P.m * v), (P.cv * P.lv**2 + P.ch * P.lh**2) / (P.J * v),
                  1.0 / self.steer_time_constant)
        return 2.0 / lam

    def _dynamic(self, vx, vy, r, delta, F_vl, F_hl, env, x, y, psi, mode="plateau"):
        P = self.P
        cp, sp = math.cos(psi), math.sin(psi)
        mu_v = env.mu_at(x + P.lv * cp, y + P.lv * sp) if env is not None else 1.0
        mu_h = env.mu_at(x - P.lh * cp, y - P.lh * sp) if env is not None else 1.0
        Fx, Fy, Mz, info = desm_forces(vx, vy, r, delta, F_vl, F_hl, P, mode, v_floor=self.v_kin_low,
                                       mu_v=float(mu_v), mu_h=float(mu_h))
        return Fx, Fy, Mz, info

    def design_rhs(self, state, delta_dot, F_vl, F_hl):
        # pure model 4 (vx/vy form) without resistances, steering lag and low-speed blending
        x, y, psi, vx, vy, r, delta = state
        P = self.P
        Fx, Fy, Mz, _ = desm_forces(vx, vy, r, delta, F_vl, F_hl, P)
        return np.array([vx * math.cos(psi) - vy * math.sin(psi), vx * math.sin(psi) + vy * math.cos(psi), r,
                         Fx / P.m + r * vy, Fy / P.m - r * vx, Mz / P.J, delta_dot])

    def derivatives(self, t, s, u, env, with_outputs=False):
        P = self.P
        x, y, psi, vx, vy, r, delta = s
        delta_dot = self._steer_rate(delta, u)
        F_vl, F_hl = self._axle_forces(u, vx)
        Fx, Fy, Mz, info = self._dynamic(vx, vy, r, delta, F_vl, F_hl, env, x, y, psi)
        Fx -= self._resistance(vx, env)
        vx_dot = Fx / P.m + r * vy
        vy_dot = Fy / P.m - r * vx
        r_dot = Mz / P.J
        speed = abs(vx)
        if speed < self.v_kin_high:
            # low-speed blending with the kinematic single-track model (Werling 4.1.1: KESM at slow speed)
            w = min(max((speed - self.v_kin_low) / (self.v_kin_high - self.v_kin_low), 0.0), 1.0)
            w = w * w * (3.0 - 2.0 * w)
            tan_d, cos_d = math.tan(delta), math.cos(delta)
            vx_dot_k = Fx / P.m
            r_kin = vx * tan_d / P.l
            r_dot_k = (vx_dot_k * tan_d + vx * delta_dot / cos_d**2) / P.l + (r_kin - r) / self.kin_relaxation
            vy_dot_k = P.lh * r_dot_k + (P.lh * r_kin - vy) / self.kin_relaxation
            vx_dot = w * vx_dot + (1 - w) * vx_dot_k
            vy_dot = w * vy_dot + (1 - w) * vy_dot_k
            r_dot = w * r_dot + (1 - w) * r_dot_k
        cp, sp = math.cos(psi), math.sin(psi)
        ds = np.array([vx * cp - vy * sp, vx * sp + vy * cp, r, vx_dot, vy_dot, r_dot, delta_dot])
        if not with_outputs:
            return ds
        a_v, a_h = info["alpha_v"], info["alpha_h"]
        out = {"r": r, "ax": vx_dot - r * vy, "ay": vy_dot + r * vx, "beta": math.atan2(vy, max(abs(vx), 0.1)),
               "delta": delta, "delta_rate": delta_dot, "F_vl": F_vl, "F_hl": F_hl,
               "F_vq": info["F_vq"], "F_hq": info["F_hq"], "tire_saturated": float(info["sat_v"] or info["sat_h"]),
               "gamma": F_vl / (F_vl + F_hl) if abs(F_vl + F_hl) > 1e-6 else 0.0,
               "slip_angle": np.array([a_v, a_v, a_h, a_h]),
               "fx": np.array([F_vl, F_vl, F_hl, F_hl]) / 2,
               "fy": np.array([info["F_vq"], info["F_vq"], info["F_hq"], info["F_hq"]]) / 2, "fz": self._fz()}
        return ds, out

    def vehicle_state(self, t, s, out):
        x, y, psi, vx, vy, r, delta = s
        return VehicleState(t=t, x=x, y=y, psi=psi, vx=vx, vy=vy, r=r, ax=out["ax"], ay=out["ay"], delta_f=delta,
                            slip_angle=out["slip_angle"], fx=out["fx"], fy=out["fy"], fz=out["fz"])
