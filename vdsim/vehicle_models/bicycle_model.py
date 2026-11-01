"""Single-track (bicycle) models.

KinematicBicycleModel   no tire slip; valid at low lateral acceleration
LinearBicycleModel      linear tires, small angles; provides the state-space matrices
NonlinearBicycleModel   nonlinear tire model per axle, longitudinal load transfer, friction ellipse
"""

import numpy as np

from ..core.conventions import G
from ..core.interfaces import VehicleModel
from ..core.registry import register
from ..simulation.vehicle_state import VehicleState
from ..tire_models import create_tires
from .common import aero_drag, axle_cornering_stiffness, rolling_resistance, wheel_force_request


class _BicycleBase(VehicleModel):
    recommended_dt = 0.002

    def __init__(self, config):
        super().__init__(config)
        self.p = config.vehicle
        self.tire_front, self.tire_rear = create_tires(config.tires)
        self.mu_tire = config.tires.mu

    def _longitudinal_force(self, u, vx, env):
        p = self.p
        fx_wheels = wheel_force_request(u, p, vx)
        fx_total = fx_wheels.sum()
        limit = self.mu_tire * env.mu_at(0.0, 0.0) * p.mass * G
        return np.clip(fx_total, -limit, limit) - aero_drag(p, vx, env.wind_speed) - rolling_resistance(p, vx)


@register("vehicle_model", "bicycle_kinematic")
class KinematicBicycleModel(_BicycleBase):
    state_names = ("x", "y", "psi", "v")

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0):
        return np.array([x, y, psi, speed], dtype=float)

    def derivatives(self, t, s, u, env, with_outputs=False):
        p = self.p
        x, y, psi, v = s
        tan_f, tan_r = np.tan(u.steer_front), np.tan(u.steer_rear)
        beta = np.arctan((p.cg_to_front * tan_r + p.cg_to_rear * tan_f) / p.wheelbase)
        r = v * np.cos(beta) * (tan_f - tan_r) / p.wheelbase
        v_dot = self._longitudinal_force(u, v, env) / p.mass
        ds = np.array([v * np.cos(psi + beta), v * np.sin(psi + beta), r, v_dot])
        if not with_outputs:
            return ds
        fz_f, fz_r = p.static_axle_loads
        out = {"ax": v_dot, "ay": v * r, "r": r, "beta": beta,
               "fz": np.array([fz_f, fz_f, fz_r, fz_r]) / 2}
        return ds, out

    def vehicle_state(self, t, s, out):
        x, y, psi, v = s
        beta = out["beta"]
        return VehicleState(t=t, x=x, y=y, psi=psi, vx=v * np.cos(beta), vy=v * np.sin(beta), r=out["r"],
                            ax=out["ax"], ay=out["ay"], fz=out["fz"])


@register("vehicle_model", "bicycle_linear")
class LinearBicycleModel(_BicycleBase):
    state_names = ("x", "y", "psi", "vx", "vy", "r")

    def __init__(self, config):
        super().__init__(config)
        fz_f, fz_r = self.p.static_axle_loads
        self.c_front = axle_cornering_stiffness(self.tire_front, fz_f / 2)
        self.c_rear = axle_cornering_stiffness(self.tire_rear, fz_r / 2)

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0):
        return np.array([x, y, psi, speed, 0.0, 0.0], dtype=float)

    def state_space(self, vx):
        # d/dt [vy, r] = A [vy, r] + B [delta_f, delta_r]
        p, cf, cr = self.p, self.c_front, self.c_rear
        lf, lr, m, iz = p.cg_to_front, p.cg_to_rear, p.mass, p.inertia_z
        A = np.array([[-(cf + cr) / (m * vx), -vx - (cf * lf - cr * lr) / (m * vx)],
                      [-(cf * lf - cr * lr) / (iz * vx), -(cf * lf**2 + cr * lr**2) / (iz * vx)]])
        B = np.array([[cf / m, cr / m],
                      [cf * lf / iz, -cr * lr / iz]])
        return A, B

    def understeer_gradient(self):
        # rad / (m/s^2): delta = L/R + EG * a_y
        p = self.p
        fz_f, fz_r = p.static_axle_loads
        return (fz_f / self.c_front - fz_r / self.c_rear) / G

    def derivatives(self, t, s, u, env, with_outputs=False):
        p = self.p
        x, y, psi, vx, vy, r = s
        vx_safe = max(abs(vx), 1.0)
        alpha_f = u.steer_front - (vy + p.cg_to_front * r) / vx_safe
        alpha_r = u.steer_rear - (vy - p.cg_to_rear * r) / vx_safe
        fy_f, fy_r = self.c_front * alpha_f, self.c_rear * alpha_r
        vx_dot = self._longitudinal_force(u, vx, env) / p.mass + vy * r
        vy_dot = (fy_f + fy_r) / p.mass - vx * r
        r_dot = (p.cg_to_front * fy_f - p.cg_to_rear * fy_r) / p.inertia_z
        ds = np.array([vx * np.cos(psi) - vy * np.sin(psi), vx * np.sin(psi) + vy * np.cos(psi),
                       r, vx_dot, vy_dot, r_dot])
        if not with_outputs:
            return ds
        fz_f, fz_r = p.static_axle_loads
        out = {"ax": vx_dot - vy * r, "ay": vy_dot + vx * r, "r": r, "beta": np.arctan2(vy, vx_safe),
               "slip_angle": np.array([alpha_f, alpha_f, alpha_r, alpha_r]),
               "fy": np.array([fy_f, fy_f, fy_r, fy_r]) / 2,
               "fz": np.array([fz_f, fz_f, fz_r, fz_r]) / 2}
        return ds, out

    def vehicle_state(self, t, s, out):
        x, y, psi, vx, vy, r = s
        return VehicleState(t=t, x=x, y=y, psi=psi, vx=vx, vy=vy, r=r, ax=out["ax"], ay=out["ay"],
                            slip_angle=out["slip_angle"], fy=out["fy"], fz=out["fz"])


@register("vehicle_model", "bicycle_nonlinear")
class NonlinearBicycleModel(_BicycleBase):
    state_names = ("x", "y", "psi", "vx", "vy", "r")

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0):
        return np.array([x, y, psi, speed, 0.0, 0.0], dtype=float)

    def derivatives(self, t, s, u, env, with_outputs=False):
        p = self.p
        x, y, psi, vx, vy, r = s
        lf, lr, m = p.cg_to_front, p.cg_to_rear, p.mass
        vx_safe = max(abs(vx), 1.0)

        # longitudinal load transfer from the requested longitudinal force
        fx_wheels = wheel_force_request(u, p, vx)
        fx_req_f, fx_req_r = fx_wheels[0] + fx_wheels[1], fx_wheels[2] + fx_wheels[3]
        resist = aero_drag(p, vx, env.wind_speed) + rolling_resistance(p, vx)
        ax_est = np.clip((fx_req_f + fx_req_r - resist) / m, -1.5 * G, 1.5 * G)
        fz_f0, fz_r0 = p.static_axle_loads
        dfz = m * ax_est * p.cg_height / p.wheelbase
        fz_f, fz_r = max(fz_f0 - dfz, 0.0), max(fz_r0 + dfz, 0.0)

        cos_psi, sin_psi = np.cos(psi), np.sin(psi)
        mu_f = self.mu_tire * env.mu_at(x + lf * cos_psi, y + lf * sin_psi)
        mu_r = self.mu_tire * env.mu_at(x - lr * cos_psi, y - lr * sin_psi)

        alpha_f = u.steer_front - np.arctan2(vy + lf * r, vx_safe)
        alpha_r = u.steer_rear - np.arctan2(vy - lr * r, vx_safe)
        _, fy0_f, mz_f = self.tire_front.forces(alpha_f, 0.0, fz_f / 2, mu_f)
        _, fy0_r, mz_r = self.tire_rear.forces(alpha_r, 0.0, fz_r / 2, mu_r)

        # friction ellipse: longitudinal force first, lateral force uses the remaining grip
        fx_f = np.clip(fx_req_f, -mu_f * fz_f, mu_f * fz_f)
        fx_r = np.clip(fx_req_r, -mu_r * fz_r, mu_r * fz_r)
        fy_f = 2 * fy0_f * np.sqrt(max(1 - (fx_f / (mu_f * fz_f + 1e-9)) ** 2, 0.0))
        fy_r = 2 * fy0_r * np.sqrt(max(1 - (fx_r / (mu_r * fz_r + 1e-9)) ** 2, 0.0))

        cf, sf, cr, sr = np.cos(u.steer_front), np.sin(u.steer_front), np.cos(u.steer_rear), np.sin(u.steer_rear)
        fxv_f, fyv_f = fx_f * cf - fy_f * sf, fx_f * sf + fy_f * cf
        fxv_r, fyv_r = fx_r * cr - fy_r * sr, fx_r * sr + fy_r * cr

        vx_dot = (fxv_f + fxv_r - aero_drag(p, vx, env.wind_speed)) / m + vy * r
        vy_dot = (fyv_f + fyv_r) / m - vx * r
        r_dot = (lf * fyv_f - lr * fyv_r + 2 * (mz_f + mz_r)) / p.inertia_z
        if abs(vx) < 0.5 and fx_req_f + fx_req_r <= 0:
            vx_dot = max(vx_dot, -vx / 0.05)  # standstill: brakes hold, no reversing

        ds = np.array([vx * cos_psi - vy * sin_psi, vx * sin_psi + vy * cos_psi, r, vx_dot, vy_dot, r_dot])
        if not with_outputs:
            return ds
        out = {"ax": vx_dot - vy * r, "ay": vy_dot + vx * r, "r": r, "beta": np.arctan2(vy, vx_safe),
               "slip_angle": np.array([alpha_f, alpha_f, alpha_r, alpha_r]),
               "fx": np.array([fx_f, fx_f, fx_r, fx_r]) / 2,
               "fy": np.array([fy_f, fy_f, fy_r, fy_r]) / 2,
               "fz": np.array([fz_f, fz_f, fz_r, fz_r]) / 2,
               "mu": np.array([mu_f, mu_f, mu_r, mu_r])}
        return ds, out

    def vehicle_state(self, t, s, out):
        x, y, psi, vx, vy, r = s
        return VehicleState(t=t, x=x, y=y, psi=psi, vx=vx, vy=vy, r=r, ax=out["ax"], ay=out["ay"],
                            slip_angle=out["slip_angle"], fx=out["fx"], fy=out["fy"], fz=out["fz"], mu=out["mu"])
