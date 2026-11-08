"""Multibody full-vehicle model (24 states): sprung body with heave, roll and pitch, four unsprung
masses with vertical motion, four wheel spins and the planar motion.

States: x, y, psi, vx, vy, r, z, z_dot, roll, roll_rate, pitch, pitch_rate,
        zw_FL..zw_RR, zw_dot_FL..zw_dot_RR, omega_FL..omega_RR
(z, zw: deviations from the static equilibrium; roll > 0 lifts the left side; pitch > 0 nose down)

Per corner: wheel-rate spring, nonlinear damper curve, anti-roll bar, active damper/roll forces;
link load transfer from the roll centers (lateral) and anti-dive/anti-squat (longitudinal); radial tire
spring and damping over the road profile. Wheel loads therefore follow from the vertical dynamics,
including road excitation. Camber and toe follow from suspension travel (camber gain, bump steer)
and body roll.
"""

import numpy as np

from ..core.conventions import AIR_DENSITY, G
from ..core.interfaces import VehicleModel
from ..core.registry import register
from ..simulation.vehicle_state import VehicleState
from ..tire_models import create_tire_set


@register("vehicle_model", "multibody")
class MultibodyModel(VehicleModel):
    state_names = ("x", "y", "psi", "vx", "vy", "r", "z", "z_dot", "roll", "roll_rate", "pitch", "pitch_rate",
                   "zw_fl", "zw_fr", "zw_rl", "zw_rr", "zw_dot_fl", "zw_dot_fr", "zw_dot_rl", "zw_dot_rr",
                   "omega_fl", "omega_fr", "omega_rl", "omega_rr")
    has_wheel_dynamics = True
    has_roll_dynamics = True
    recommended_dt = 0.002
    slip_speed_floor = 3.0
    brake_smoothing = 2.0
    tire_damping = 150.0  # N s/m

    def __init__(self, config):
        super().__init__(config)
        p, ch = config.vehicle, config.chassis
        self.p, self.ch = p, ch
        self.tires = create_tire_set(config.tires)
        self.mu_tire = config.tires.mu
        lf, lr, tf, tr = p.cg_to_front, p.cg_to_rear, p.track_front, p.track_rear
        self.x_w = np.array([lf, lf, -lr, -lr])
        self.y_w = np.array([tf / 2, -tf / 2, tr / 2, -tr / 2])
        self.track = np.array([tf, tf, tr, tr])
        self.side = np.sign(self.y_w)
        self.front = np.array([True, True, False, False])
        self.m_u = np.array([p.unsprung_mass_front] * 2 + [p.unsprung_mass_rear] * 2)
        self.m_s = p.mass - self.m_u.sum()
        self.k_s = np.array([ch.spring_rate_front] * 2 + [ch.spring_rate_rear] * 2)
        self.k_arb = np.array([ch.anti_roll_bar_front, ch.anti_roll_bar_rear])
        self.k_t = config.tires.vertical_stiffness
        h_rf, h_rr = ch.roll_center_height_front, ch.roll_center_height_rear
        self.h_rc = np.array([h_rf, h_rf, h_rr, h_rr])
        self.h_arm = p.cg_height - (h_rf + (h_rr - h_rf) * lf / p.wheelbase)
        self.axle_mass_share = np.array([lr, lr, lf, lf]) / p.wheelbase
        self.camber_gain = np.array([ch.camber_gain_front] * 2 + [ch.camber_gain_rear] * 2)
        self.bump_steer = np.array([ch.bump_steer_front] * 2 + [ch.bump_steer_rear] * 2)
        self.roll_steer = np.array([ch.roll_steer_front] * 2 + [ch.roll_steer_rear] * 2)
        fz_f, fz_r = p.static_axle_loads
        self.fz_static = np.array([fz_f, fz_f, fz_r, fz_r]) / 2
        self.drag_factor = 0.5 * AIR_DENSITY * p.drag_coefficient * p.frontal_area
        self.damper_v = np.asarray(ch.damper_velocity, dtype=float)
        self.damper_f = np.asarray(ch.damper_force_front, dtype=float)
        self.damper_r = np.asarray(ch.damper_force_rear, dtype=float)
        k_roll_f = self.k_s[0] * tf**2 / 2 + ch.anti_roll_bar_front
        k_roll_r = self.k_s[2] * tr**2 / 2 + ch.anti_roll_bar_rear
        self.active_roll_share_front = k_roll_f / (k_roll_f + k_roll_r)
        self.long_stiffness_max = config.tires.longitudinal_stiffness * 2.0 * self.fz_static.max() / config.tires.nominal_load
        self.brake_max = max(config.brakes.max_torque_front, config.brakes.max_torque_rear)

    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0):
        s = np.zeros(24)
        s[:6] = [x, y, psi, speed, 0.0, 0.0]
        s[20:24] = speed / self.p.wheel_radius
        return s

    def stable_dt(self, state):
        p = self.p
        v = max(abs(state[3]), self.slip_speed_floor)
        lam_slip = self.long_stiffness_max * p.wheel_radius**2 / (p.wheel_inertia * v)
        lam_brake = self.brake_max / (self.brake_smoothing * p.wheel_inertia)
        damper_slope = max(np.max(np.abs(np.diff(self.damper_f) / np.diff(self.damper_v))),
                           np.max(np.abs(np.diff(self.damper_r) / np.diff(self.damper_v))))
        lam_damper = damper_slope / self.m_u.min()
        lam_hop = np.sqrt((self.k_s.max() + self.k_t) / self.m_u.min())
        return 2.0 / max(lam_slip, lam_brake, lam_damper, lam_hop)

    def derivatives(self, t, s, u, env, with_outputs=False):
        p = self.p
        x, y, psi, vx, vy, r, z, z_dot, phi, phi_dot, theta, theta_dot = s[:12]
        zw, zw_dot, omega = s[12:16], s[16:20], s[20:24]
        R, m = p.wheel_radius, p.mass

        # suspension travel (compression > 0) and velocity at each corner
        z_body = z - self.x_w * theta + self.y_w * phi
        z_body_dot = z_dot - self.x_w * theta_dot + self.y_w * phi_dot
        travel = zw - z_body
        travel_rate = zw_dot - z_body_dot
        f_spring = self.k_s * travel
        f_damper = np.concatenate([np.interp(travel_rate[:2], self.damper_v, self.damper_f),
                                   np.interp(travel_rate[2:], self.damper_v, self.damper_r)])
        arb_front = self.k_arb[0] * (travel[1] - travel[0]) / p.track_front**2
        arb_rear = self.k_arb[1] * (travel[3] - travel[2]) / p.track_rear**2
        f_arb = np.array([-arb_front, arb_front, -arb_rear, arb_rear])
        m_act_f = self.active_roll_share_front * u.roll_moment
        m_act = np.array([m_act_f, m_act_f, u.roll_moment - m_act_f, u.roll_moment - m_act_f])
        f_active = u.damper_force + self.side * m_act / self.track

        # planar slip quantities
        delta = self.roll_steer * phi - self.side * self.bump_steer * travel  # bump_steer = toe-in per m
        delta[:2] += u.steer_front
        delta[2:] += u.steer_rear
        cd, sd = np.cos(delta), np.sin(delta)
        vwx, vwy = vx - r * self.y_w, vy + r * self.x_w
        v_long = vwx * cd + vwy * sd
        v_lat = vwy * cd - vwx * sd
        abs_long = np.abs(v_long)
        alpha = -np.arctan2(v_lat, np.maximum(abs_long, 1.0))
        kappa = (omega * R - v_long) / np.maximum(abs_long, self.slip_speed_floor)

        # road contact: radial tire spring/damper
        cos_psi, sin_psi = np.cos(psi), np.sin(psi)
        xw = x + self.x_w * cos_psi - self.y_w * sin_psi
        yw = y + self.x_w * sin_psi + self.y_w * cos_psi
        z_road = env.road_height(xw, yw)
        z_road_dot = (env.road_height(xw + 0.01 * cos_psi, yw + 0.01 * sin_psi) - z_road) / 0.01 * vx
        f_tire = self.k_t * (z_road - zw) + self.tire_damping * (z_road_dot - zw_dot)

        # link (geometric) load transfer goes straight to the tires: lateral through the roll
        # centers, longitudinal through anti-dive/anti-squat (accelerations estimated without loop)
        f_susp = f_spring + f_damper + f_arb + f_active
        ay_est = vx * r
        ax_est = min(max(((u.drive_torque.sum() - u.brake_torque.sum() * np.tanh(vx / 0.2)) / R) / m, -1.5 * G), 1.5 * G)
        anti_eff = 0.5 * (self.ch.anti_dive if ax_est < 0 else self.ch.anti_squat)
        dfz_link = -self.side * self.m_s * ay_est * self.axle_mass_share * self.h_rc / self.track             + np.where(self.front, -1.0, 1.0) * anti_eff * m * ax_est * p.cg_height / p.wheelbase / 2
        fz = np.maximum(self.fz_static + f_tire + dfz_link, 0.0)

        camber = self.side * self.camber_gain * travel - phi
        mu = self.mu_tire * env.mu_at(xw, yw)
        fx_w, fy_w, mz = self.tires.forces(alpha, kappa, fz, mu, camber)
        fx_v = fx_w * cd - fy_w * sd
        fy_v = fx_w * sd + fy_w * cd
        v_air = vx + env.wind_speed  # head wind > 0
        drag = self.drag_factor * v_air * abs(v_air)
        fx_sum = fx_v.sum() - drag
        fy_sum = fy_v.sum()
        ax, ay = fx_sum / m, fy_sum / m

        z_ddot = f_susp.sum() / self.m_s
        phi_ddot = ((self.y_w * f_susp).sum() + self.m_s * self.h_arm * (ay + G * np.sin(phi))) / p.inertia_x
        theta_ddot = (-(self.x_w * f_susp).sum() - self.m_s * ax * p.cg_height * (1 - anti_eff)) / p.inertia_y
        zw_ddot = (f_tire - f_susp) / self.m_u

        t_roll = p.rolling_resistance * fz * R * np.tanh(omega)
        t_brake = u.brake_torque * np.tanh(omega / self.brake_smoothing)
        mz_sum = (self.x_w * fy_v - self.y_w * fx_v).sum() + mz.sum()

        ds = np.empty(24)
        ds[0] = vx * cos_psi - vy * sin_psi
        ds[1] = vx * sin_psi + vy * cos_psi
        ds[2] = r
        ds[3] = ax + vy * r
        ds[4] = ay - vx * r
        ds[5] = mz_sum / p.inertia_z
        ds[6], ds[7] = z_dot, z_ddot
        ds[8], ds[9] = phi_dot, phi_ddot
        ds[10], ds[11] = theta_dot, theta_ddot
        ds[12:16] = zw_dot
        ds[16:20] = zw_ddot
        ds[20:24] = (u.drive_torque - t_brake - fx_w * R - t_roll) / p.wheel_inertia
        if not with_outputs:
            return ds
        out = {"ax": ax, "ay": ay, "r": r, "beta": np.arctan2(vy, max(abs(vx), 1.0)),
               "slip_angle": alpha, "slip_ratio": kappa, "fx": fx_w, "fy": fy_w, "fz": fz, "mu": mu * np.ones(4),
               "camber": camber, "delta": delta, "suspension_travel": travel, "body_z": z,
               "body_az": z_ddot, "pitch": theta, "pitch_rate": theta_dot}
        return ds, out

    def vehicle_state(self, t, s, out):
        return VehicleState(t=t, x=s[0], y=s[1], psi=s[2], vx=s[3], vy=s[4], r=s[5], ax=out["ax"], ay=out["ay"],
                            delta_f=out["delta"][0], delta_r=out["delta"][2], heave=s[6], heave_rate=s[7],
                            roll=s[8], roll_rate=s[9], pitch=s[10], pitch_rate=s[11],
                            wheel_speed=s[20:24].copy(), slip_ratio=out["slip_ratio"], slip_angle=out["slip_angle"],
                            fx=out["fx"], fy=out["fy"], fz=out["fz"], mu=out["mu"])
