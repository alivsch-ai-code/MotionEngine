"""Double-track model with roll dynamics and wheel rotation (12 states).

States: x, y, psi, vx, vy, r, roll, roll_rate, omega_FL, omega_FR, omega_RL, omega_RR

- Wheel loads: static + quasi-static longitudinal transfer + lateral transfer through the
  suspension (roll stiffness of springs/anti-roll bars, nonlinear damper curves, active
  roll moment) and the roll centers (geometric part).
- Roll steer and camber from suspension travel and body roll.
- Combined-slip tire forces per wheel with the road friction at each contact patch.
- Wheel spin dynamics with drive, brake and rolling-resistance torques (basis for ABS/TCS/ESP).
"""

import numpy as np

from ..core.conventions import AIR_DENSITY, G
from ..core.interfaces import VehicleModel
from ..core.registry import register
from ..simulation.vehicle_state import VehicleState
from ..tire_models import create_tire_set


@register("vehicle_model", "double_track")
class DoubleTrackModel(VehicleModel):
    state_names = ("x", "y", "psi", "vx", "vy", "r", "roll", "roll_rate",
                   "omega_fl", "omega_fr", "omega_rl", "omega_rr")
    has_wheel_dynamics = True
    has_roll_dynamics = True
    recommended_dt = 0.002
    slip_speed_floor = 3.0     # m/s, avoids the slip singularity at low speed
    brake_smoothing = 2.0      # rad/s, brake torque fades in below this wheel speed

    def __init__(self, config):
        super().__init__(config)
        p, ch = config.vehicle, config.chassis
        self.p, self.ch = p, ch
        self.tires = create_tire_set(config.tires)
        self.mu_tire = config.tires.mu
        lf, lr, tf, tr = p.cg_to_front, p.cg_to_rear, p.track_front, p.track_rear
        self.x_w = np.array([lf, lf, -lr, -lr])
        self.y_w = np.array([tf / 2, -tf / 2, tr / 2, -tr / 2])
        self.side = np.sign(self.y_w)
        self.m_s = p.mass - 2 * (p.unsprung_mass_front + p.unsprung_mass_rear)
        h_rf, h_rr = ch.roll_center_height_front, ch.roll_center_height_rear
        self.h_arm = p.cg_height - (h_rf + (h_rr - h_rf) * lf / p.wheelbase)
        self.k_roll_f, self.k_roll_r = ch.roll_stiffness(tf, tr)
        self.active_roll_share_front = self.k_roll_f / (self.k_roll_f + self.k_roll_r)
        self.camber_gain = np.array([ch.camber_gain_front] * 2 + [ch.camber_gain_rear] * 2)
        self.roll_steer = np.array([ch.roll_steer_front] * 2 + [ch.roll_steer_rear] * 2)
        fz_f, fz_r = p.static_axle_loads
        self.fz_static = np.array([fz_f, fz_f, fz_r, fz_r]) / 2
        # geometric lateral load transfer per unit lateral acceleration, per axle (N per m/s^2)
        self.geo_f = (self.m_s * p.cg_to_rear / p.wheelbase * h_rf + 2 * p.unsprung_mass_front * p.wheel_radius) / tf
        self.geo_r = (self.m_s * p.cg_to_front / p.wheelbase * h_rr + 2 * p.unsprung_mass_rear * p.wheel_radius) / tr
        self.drag_factor = 0.5 * AIR_DENSITY * p.drag_coefficient * p.frontal_area
        self.damper_v = np.asarray(ch.damper_velocity, dtype=float)
        self.damper_f = np.asarray(ch.damper_force_front, dtype=float)
        self.damper_r = np.asarray(ch.damper_force_rear, dtype=float)
        self.long_stiffness_max = config.tires.longitudinal_stiffness * 2.0 * self.fz_static.max() / config.tires.nominal_load
        self.brake_max = max(config.brakes.max_torque_front, config.brakes.max_torque_rear)

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0):
        omega = speed / self.p.wheel_radius
        return np.array([x, y, psi, speed, 0.0, 0.0, 0.0, 0.0, omega, omega, omega, omega], dtype=float)

    def stable_dt(self, state):
        # explicit-RK4 stability of the wheel spin dynamics (slip stiffness and brake smoothing)
        p = self.p
        v = max(abs(state[3]), self.slip_speed_floor)
        lam_slip = self.long_stiffness_max * p.wheel_radius**2 / (p.wheel_inertia * v)
        lam_brake = self.brake_max / (self.brake_smoothing * p.wheel_inertia)
        return 2.0 / max(lam_slip, lam_brake)

    def wheel_positions(self, x, y, psi):
        c, s = np.cos(psi), np.sin(psi)
        return x + self.x_w * c - self.y_w * s, y + self.x_w * s + self.y_w * c

    def derivatives(self, t, s, u, env, with_outputs=False):
        p = self.p
        x, y, psi, vx, vy, r, phi, phi_dot = s[:8]
        omega = s[8:12]
        R, m, tf, tr = p.wheel_radius, p.mass, p.track_front, p.track_rear

        # wheel steering angles and contact-patch velocities
        delta = self.roll_steer * phi
        delta[:2] += u.steer_front
        delta[2:] += u.steer_rear
        cd, sd = np.cos(delta), np.sin(delta)
        vwx, vwy = vx - r * self.y_w, vy + r * self.x_w
        v_long = vwx * cd + vwy * sd
        v_lat = vwy * cd - vwx * sd
        abs_long = np.abs(v_long)
        alpha = -np.arctan2(v_lat, np.maximum(abs_long, 1.0))
        kappa = (omega * R - v_long) / np.maximum(abs_long, self.slip_speed_floor)

        # wheel loads: longitudinal transfer (from the torque request) and lateral transfer
        drag = self.drag_factor * (vx - env.wind_speed) * abs(vx - env.wind_speed)
        fx_req = (u.drive_torque.sum() - u.brake_torque.sum() * np.tanh(vx / 0.2)) / R
        ax_est = min(max((fx_req - drag) / m, -1.5 * G), 1.5 * G)
        ay_est = vx * r
        dfz_long = m * ax_est * p.cg_height / p.wheelbase / 2

        comp_vel = phi_dot * tf / 2, phi_dot * tr / 2  # right side compresses for positive roll rate
        fd = (np.interp(-comp_vel[0], self.damper_v, self.damper_f), np.interp(comp_vel[0], self.damper_v, self.damper_f),
              np.interp(-comp_vel[1], self.damper_v, self.damper_r), np.interp(comp_vel[1], self.damper_v, self.damper_r))
        fb = u.damper_force
        m_act_f = self.active_roll_share_front * u.roll_moment
        m_susp_f = -self.k_roll_f * phi + tf / 2 * (fd[0] + fb[0] - fd[1] - fb[1]) + m_act_f
        m_susp_r = -self.k_roll_r * phi + tr / 2 * (fd[2] + fb[2] - fd[3] - fb[3]) + (u.roll_moment - m_act_f)
        dfz_f = (-m_susp_f + self.geo_f * ay_est) / tf
        dfz_r = (-m_susp_r + self.geo_r * ay_est) / tr
        fz = self.fz_static + np.array([-dfz_long - dfz_f, -dfz_long + dfz_f, dfz_long - dfz_r, dfz_long + dfz_r])
        np.maximum(fz, 0.0, out=fz)

        # camber relative to the road (positive = top leaning left)
        camber = -self.side * self.camber_gain * self.y_w * phi - phi

        xw, yw = self.wheel_positions(x, y, psi)
        mu = self.mu_tire * env.mu_at(xw, yw)
        fx_w, fy_w, mz = self.tires.forces(alpha, kappa, fz, mu, camber)

        fx_v = fx_w * cd - fy_w * sd
        fy_v = fx_w * sd + fy_w * cd
        fx_sum = fx_v.sum() - drag
        fy_sum = fy_v.sum()
        mz_sum = (self.x_w * fy_v - self.y_w * fx_v).sum() + mz.sum()

        ay = fy_sum / m
        t_roll = p.rolling_resistance * fz * R * np.tanh(omega)
        t_brake = u.brake_torque * np.tanh(omega / self.brake_smoothing)

        ds = np.empty(12)
        cos_psi, sin_psi = np.cos(psi), np.sin(psi)
        ds[0] = vx * cos_psi - vy * sin_psi
        ds[1] = vx * sin_psi + vy * cos_psi
        ds[2] = r
        ds[3] = fx_sum / m + vy * r
        ds[4] = ay - vx * r
        ds[5] = mz_sum / p.inertia_z
        ds[6] = phi_dot
        ds[7] = (self.m_s * self.h_arm * (ay + G * np.sin(phi)) + m_susp_f + m_susp_r) / p.inertia_x
        ds[8:12] = (u.drive_torque - t_brake - fx_w * R - t_roll) / p.wheel_inertia
        if not with_outputs:
            return ds
        out = {"ax": fx_sum / m, "ay": ay, "r": r, "beta": np.arctan2(vy, max(abs(vx), 1.0)),
               "slip_angle": alpha, "slip_ratio": kappa, "fx": fx_w, "fy": fy_w, "fz": fz, "mu": mu * np.ones(4),
               "camber": camber, "delta": delta, "roll": phi, "roll_rate": phi_dot, "wheel_speed": omega.copy()}
        return ds, out

    def vehicle_state(self, t, s, out):
        x, y, psi, vx, vy, r, phi, phi_dot = s[:8]
        return VehicleState(t=t, x=x, y=y, psi=psi, vx=vx, vy=vy, r=r, ax=out["ax"], ay=out["ay"],
                            delta_f=out["delta"][0], delta_r=out["delta"][2], roll=phi, roll_rate=phi_dot,
                            wheel_speed=s[8:12].copy(), slip_ratio=out["slip_ratio"], slip_angle=out["slip_angle"],
                            fx=out["fx"], fy=out["fy"], fz=out["fz"], mu=out["mu"])
