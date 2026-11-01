"""Quasi-static analysis: wheel loads and load transfer, roll (roll axis, roll gradient), steering kinematics."""

import numpy as np

from ..core.conventions import G


class QuasiStaticAnalysis:
    def __init__(self, config):
        self.config = config
        p, ch = config.vehicle, config.chassis
        self.p, self.ch = p, ch
        self.m_s = p.mass - 2 * (p.unsprung_mass_front + p.unsprung_mass_rear)
        self.k_front, self.k_rear = ch.roll_stiffness(p.track_front, p.track_rear)

    # roll
    @property
    def roll_axis_height(self):
        ch, p = self.ch, self.p
        return ch.roll_center_height_front + (ch.roll_center_height_rear - ch.roll_center_height_front) \
            * p.cg_to_front / p.wheelbase

    @property
    def roll_arm(self):
        return self.p.cg_height - self.roll_axis_height

    @property
    def roll_gradient(self):
        # rad per m/s^2 of lateral acceleration
        return self.m_s * self.roll_arm / (self.k_front + self.k_rear - self.m_s * G * self.roll_arm)

    @property
    def roll_stiffness_distribution(self):
        return self.k_front / (self.k_front + self.k_rear)

    # loads
    def static_wheel_loads(self):
        fz_f, fz_r = self.p.static_axle_loads
        return np.array([fz_f, fz_f, fz_r, fz_r]) / 2

    def wheel_loads(self, ax=0.0, ay=0.0):
        # steady-state wheel loads (FL, FR, RL, RR) under constant ax, ay (left turn: ay > 0)
        p, ch = self.p, self.ch
        dfz_long = p.mass * ax * p.cg_height / p.wheelbase / 2
        phi = self.roll_gradient * ay
        dfz_f = (self.k_front * phi + self.m_s * ay * p.cg_to_rear / p.wheelbase * ch.roll_center_height_front
                 + 2 * p.unsprung_mass_front * ay * p.wheel_radius) / p.track_front
        dfz_r = (self.k_rear * phi + self.m_s * ay * p.cg_to_front / p.wheelbase * ch.roll_center_height_rear
                 + 2 * p.unsprung_mass_rear * ay * p.wheel_radius) / p.track_rear
        fz = self.static_wheel_loads() + np.array([-dfz_long - dfz_f, -dfz_long + dfz_f,
                                                    dfz_long - dfz_r, dfz_long + dfz_r])
        return fz, {"roll": phi, "transfer_front": dfz_f, "transfer_rear": dfz_r}

    def lateral_load_transfer_distribution(self, ay=4.0):
        _, info = self.wheel_loads(0.0, ay)
        f, r = info["transfer_front"] * self.p.track_front, info["transfer_rear"] * self.p.track_rear
        return f / (f + r)

    def wheel_lift_acceleration(self):
        # lateral acceleration at which the first inner wheel lifts off (steady state)
        ay = np.linspace(0.1, 30, 600)
        loads = np.array([self.wheel_loads(0.0, a)[0] for a in ay])
        lifted = np.where(loads.min(axis=1) <= 0)[0]
        return float(ay[lifted[0]]) if len(lifted) else float("inf")

    def camber_at(self, ay):
        # camber of the outer wheels relative to the road (deg) at steady lateral acceleration
        phi = self.roll_gradient * ay
        front = np.degrees(self.ch.camber_gain_front * self.p.track_front / 2 * phi - phi)
        rear = np.degrees(self.ch.camber_gain_rear * self.p.track_rear / 2 * phi - phi)
        return front, rear

    # steering kinematics
    def ackermann_angles(self, radius):
        # inner and outer front road-wheel angles (rad) for a turn radius at the rear axle
        L, t = self.p.wheelbase, self.p.track_front
        return np.arctan(L / (radius - t / 2)), np.arctan(L / (radius + t / 2))

    def turning_circle(self):
        # wall-to-wall turning circle diameter (m) at maximum steering angle
        p = self.p
        r_rear = p.wheelbase / np.tan(p.max_steer_angle)
        front_outer = np.hypot(r_rear + p.width / 2, p.wheelbase + (p.length - p.wheelbase) / 2)
        return 2 * front_outer

    def summary(self):
        f_front, f_rear = self.camber_at(5.0)
        fz0 = self.static_wheel_loads()
        return {"axle_load_front_share": (fz0[0] + fz0[1]) / fz0.sum(),
                "roll_axis_height": self.roll_axis_height, "roll_arm": self.roll_arm,
                "roll_gradient_deg_per_g": np.degrees(self.roll_gradient) * G,
                "roll_stiffness_front": self.k_front, "roll_stiffness_rear": self.k_rear,
                "roll_stiffness_distribution": self.roll_stiffness_distribution,
                "lltd_front": self.lateral_load_transfer_distribution(),
                "wheel_lift_ay": self.wheel_lift_acceleration(),
                "camber_outer_front_at_5": f_front, "camber_outer_rear_at_5": f_rear,
                "turning_circle": self.turning_circle()}
