"""Longitudinal control: speed tracking (PI + feedforward), ACC and emergency brake assist (AEB)."""

import numpy as np

from ..core.interfaces import LongitudinalController
from ..core.registry import create, register


@register("longitudinal_controller", "speed_pi")
class SpeedController(LongitudinalController):
    label = "Geschwindigkeitsregler (PI)"

    def __init__(self, config, kp=1.2, ki=0.3, a_max=4.0, a_min=-9.0, preview=0.6):
        self.config = config
        self.kp, self.ki, self.a_max, self.a_min, self.preview = kp, ki, a_max, a_min, preview
        self.reset()

    def reset(self):
        self._hint = 0
        self.integral = 0.0
        self._t_last = None
        self.signals = {}

    def acceleration(self, t, state, ref, env):
        dt = 0.0 if self._t_last is None else t - self._t_last
        self._t_last = t
        if ref.accel_table is not None:
            a_table = ref.accel_at(t)
            target = ref.metadata.get("target")
            if a_table != 0.0 and (target is None or state.vx < target):
                self.signals = {"v_ref": state.vx, "a_request": a_table, "mode": 1.0}
                return a_table
        proj = ref.project(state.x, state.y, hint=self._hint)
        self._hint = proj.index
        v = state.vx
        v_ref = proj.speed
        v_ahead = float(np.interp(proj.s + max(v, 1.0) * self.preview, ref.s, ref.v))
        a_ff = (v_ahead**2 - v_ref**2) / (2 * max(v, 1.0) * self.preview)
        error = v_ref - v
        a = a_ff + self.kp * error + self.ki * self.integral
        if self.a_min < a < self.a_max:
            self.integral += error * dt  # anti-windup: integrate only when not saturated
        a = float(np.clip(a, self.a_min, self.a_max))
        self.signals = {"v_ref": v_ref, "a_request": a, "mode": 0.0}
        return a


def _own_path_position(state, ref, controller):
    proj = ref.project(state.x, state.y, hint=getattr(controller, "_hint", 0))
    controller._hint = proj.index
    return proj.s


@register("longitudinal_controller", "acc")
class AdaptiveCruiseControl(LongitudinalController):
    label = "Abstandsregeltempomat (ACC)"

    def __init__(self, config, time_gap=1.8, standstill_gap=5.0, k_gap=0.23, k_speed=0.7, a_max=2.0, a_min=-3.5):
        self.config = config
        self.time_gap, self.standstill_gap = time_gap, standstill_gap
        self.k_gap, self.k_speed, self.a_max, self.a_min = k_gap, k_speed, a_max, a_min
        self.cruise = SpeedController(config, a_max=a_max, a_min=a_min)
        self.signals = {}

    def reset(self):
        self.cruise.reset()
        self._hint = 0

    def acceleration(self, t, state, ref, env):
        a_cruise = self.cruise.acceleration(t, state, ref, env)
        lead = env.lead_vehicle
        if lead is None:
            self.signals = {"a_request": a_cruise}
            return a_cruise
        gap = lead.s - _own_path_position(state, ref, self) - self.config.vehicle.length / 2
        v_lead = lead.speed_at(t)
        desired = self.standstill_gap + self.time_gap * max(state.vx, 0.0)
        a_follow = self.k_gap * (gap - desired) + self.k_speed * (v_lead - state.vx)
        a = float(np.clip(min(a_cruise, a_follow), self.a_min, self.a_max))
        self.signals = {"gap": gap, "gap_desired": desired, "v_lead": v_lead, "a_request": a,
                        "acc_following": float(a_follow < a_cruise)}
        return a


@register("longitudinal_controller", "aeb")
class EmergencyBrakeAssist(LongitudinalController):
    # Time-to-collision based staged braking on top of a base longitudinal controller
    label = "Notbremsassistent (AEB)"

    def __init__(self, config, base="acc", ttc_warning=2.6, ttc_partial=2.0, ttc_full=1.3,
                 partial_decel=5.0, full_decel=9.5):
        self.config = config
        self.base = create("longitudinal_controller", base, config) if isinstance(base, str) else base
        self.ttc = (ttc_warning, ttc_partial, ttc_full)
        self.partial_decel, self.full_decel = partial_decel, full_decel
        self.reset()

    def reset(self):
        self.base.reset()
        self._hint = 0
        self.stage = 0
        self.signals = {}

    def acceleration(self, t, state, ref, env):
        a_base = self.base.acceleration(t, state, ref, env)
        lead = env.lead_vehicle
        if lead is None:
            return a_base
        gap = lead.s - _own_path_position(state, ref, self) - self.config.vehicle.length / 2
        closing = state.vx - lead.speed_at(t)
        ttc = gap / closing if closing > 0.1 else np.inf
        warn, partial, full = self.ttc
        if state.vx < 0.3 and self.stage >= 2 and lead.speed_at(t) < 1.0:
            # standstill hold after an emergency stop until the obstacle moves away
            self.signals = {"ttc": 99.0, "aeb_stage": float(self.stage), "gap": gap, "a_request": -3.0}
            return -3.0
        if state.vx < 0.3:
            self.stage = 0
        elif ttc < full:
            self.stage = 3
        elif ttc < partial:
            self.stage = max(self.stage, 2)
        elif ttc < warn:
            self.stage = max(self.stage, 1)
        a = a_base
        if self.stage == 2:
            a = min(a_base, -self.partial_decel)
        elif self.stage == 3:
            a = -self.full_decel
        self.signals = {"ttc": min(ttc, 99.0), "aeb_stage": float(self.stage), "gap": gap, "a_request": a}
        return a
