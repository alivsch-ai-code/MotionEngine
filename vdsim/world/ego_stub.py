"""Kinematic ego stand-in for tests and examples without trajectory planner and controller.

Moves the ego as a point along BehaviorCommand.reference_line: the longitudinal acceleration is
the minimum of IDM-like laws for the active modes (velocity, following, merging, stopping), the
lateral offset d follows d_ref with a first-order lag. Direction changes only at standstill.
Not a vehicle model - only meant to exercise the behavior layer in closed loop.
"""

from __future__ import annotations

import numpy as np

from ..framework.types import EgoState
from .traffic_models import idm_acceleration


class KinematicEgoStub:
    def __init__(self, x, y, psi, v=0.0, length=4.8, width=1.85, front_extent=None, a_max=2.0, b_max=6.0,
                 tau_d=1.5):
        self.x, self.y, self.psi, self.v = float(x), float(y), float(psi), float(v)
        self.length, self.width = length, width
        self.front_extent = 0.5 * length if front_extent is None else front_extent
        self.a_max, self.b_max, self.tau_d = a_max, b_max, tau_d
        self.direction = 1
        self.a = 0.0
        self.t = 0.0

    @classmethod
    def from_initial(cls, ego_initial, **kw):
        return cls(ego_initial["x"], ego_initial["y"], ego_initial["psi"], ego_initial.get("v", 0.0), **kw)

    def state(self):
        return EgoState(t=self.t, x=self.x, y=self.y, psi=self.psi, vx=self.direction * self.v, ax=self.a,
                        gear=self.direction)

    def _accel(self, cmd, ref, s, objects):
        v = self.v
        v_ref = cmd.target_speed
        acc = [self.a_max * (1 - (v / max(v_ref, 0.1)) ** 4) if v_ref > 0.05 else -self.b_max * min(v, 1.0)]
        for m in cmd.modes:
            p = m.params
            if m.kind == "velocity":
                v_ref = p.get("v_ref", v_ref)
                acc[0] = self.a_max * (1 - (v / max(v_ref, 0.1)) ** 4) if v_ref > 0.05 else -self.b_max * min(v, 1)
            elif m.kind in ("following", "merging") and objects is not None:
                oid = p.get("lead_id", p.get("front_id"))
                o = objects.by_id(oid) if oid is not None else None
                if o is not None:
                    so, _ = ref.project(o.x, o.y)
                    gap = so - s - 0.5 * o.length - self.front_extent
                    acc.append(idm_acceleration(v, max(v_ref, 0.1), gap, v - o.v, self.a_max, 2.0,
                                                p.get("kv", 1.2), p.get("k0", 4.0)))
            elif m.kind == "stopping":
                gap = p["s_stop"] - s - self.front_extent
                if gap < -1.0:
                    continue
                acc.append(idm_acceleration(v, max(v_ref, 0.1), max(gap, 0.05), v, self.a_max, 2.0, 0.5, 0.3))
        return float(np.clip(min(acc), -self.b_max, self.a_max))

    def step(self, t, dt, cmd, objects=None):
        self.t = t + dt
        if cmd is None or cmd.reference_line is None:
            return self.state()
        ref = cmd.reference_line
        s, d = ref.project(self.x, self.y)
        if cmd.direction != self.direction:
            a = -self.b_max if self.v > 0.05 else 0.0
            if self.v <= 0.05:
                self.direction, self.v = cmd.direction, 0.0
        else:
            a = self._accel(cmd, ref, s, objects)
        v_new = max(self.v + a * dt, 0.0)
        ds = 0.5 * (self.v + v_new) * dt
        self.v, self.a = v_new, a
        d_target = cmd.d_ref
        # first-order lag of d, slope limited to |dd/ds| <= 0.35 (no lateral jumps at low speed)
        step_d = (d_target - d) * min(dt / self.tau_d, 1.0)
        d_new = d + float(np.clip(step_d, -0.35 * ds, 0.35 * ds))
        s_new = s + ds
        x, y = ref.point(s_new, d_new)
        th = ref.evaluate(s_new)[2]
        dd_ds = (d_new - d) / ds if ds > 1e-6 else 0.0
        heading = th + np.arctan(dd_ds)
        self.x, self.y = float(x), float(y)
        self.psi = float(heading if self.direction > 0 else heading + np.pi)
        if ds <= 1e-6:
            self.psi = float(self.psi)
        return self.state()
