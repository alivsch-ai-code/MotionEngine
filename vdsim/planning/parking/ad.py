"""Parking in the automated-driving stack.

`trajectory_planner/werling_parking` is the Werling planner plus a parking mode. As long as the behavior
layer plans normal driving it delegates every cycle to the Werling planner. When the behavior command
carries a parking task (maneuver "park_maneuver", info["parking"]) it plans the whole parking path once
with the Hybrid A* / Reeds-Shepp planner (planner.py) from the vehicle's current pose and then hands the
controller one move at a time:

    * every cycle the current move is cut at the point nearest to the vehicle (re-anchored, like the
      Werling replanning) and time-parametrized with a speed profile that starts at the measured speed,
      respects the steering rate and stops at the end of the move;
    * at the end of a move (standstill) the next move starts with the other gear;
    * after the last move the planner holds the vehicle at the goal.

Reference point "rear_axle" and the direction flag select the Lyapunov controllers of the bi-level
stabilization for slow driving (Werling 2011, 4.3). This replaces the reverse phase on the reversed lane
center line, where the Werling velocity mode had a standstill local optimum (review finding F2).
"""

from __future__ import annotations

import math

import numpy as np

from ...framework.plugins import component
from ...framework.types import PlannedTrajectory, PlannerDebug
from ..planner import WerlingPlanner
from .planner import Footprint, ParkingPlanner, PlannerSettings
from .steering import steering_geometry
from .tracking import DriveSettings, _speed_profile


@component
class ParkingAwarePlanner(WerlingPlanner):
    NAME, VERSION = "werling_parking", "1.0.0"
    LABEL = "Trajektorienplaner (Werling + Parkplaner)"

    def reset(self, context=None):
        super().reset(context)
        self._park = None

    def step(self, t, inputs):
        beh = inputs.get("behavior")
        if beh is not None and beh.maneuver in ("park_maneuver", "parked") and beh.info.get("parking"):
            return self._park_step(float(t), inputs.get("ego"), beh)
        self._park = None
        return super().step(t, inputs)

    # ------------------------------------------------------------------ parking mode
    def _rear_axle(self, x, y, psi):
        lr = self.vehicle.vehicle.cg_to_rear if hasattr(self.vehicle, "vehicle") else self.vehicle.cg_to_rear
        return x - lr * math.cos(psi), y - lr * math.sin(psi), psi

    def _start(self, t, ego, task):
        geo = steering_geometry(self.vehicle, "front")
        fp = Footprint.from_vehicle(self.vehicle, geo)
        planner = ParkingPlanner(geo, fp, task["obstacles"], task["bounds"],
                                 PlannerSettings(time_limit=float(task.get("time_limit", 10.0))))
        start = self._rear_axle(ego.x, ego.y, ego.psi)
        goal = self._rear_axle(*task["goal"])
        path = planner.plan(start, goal, int(task.get("final_direction", -1)))
        self._park = {"id": task.get("id"), "path": path, "geo": geo, "move": 0, "near": 0, "done": False,
                      "t_plan": t, "compute_time": path.compute_time}

    def _park_step(self, t, ego, beh):
        task = beh.info["parking"]
        if ego is None:
            return {"trajectory": self.last_trajectory, "debug": PlannerDebug(t=t, info={"error": "keine Eingänge"})}
        if self._park is None or self._park["id"] != task.get("id"):
            self._start(t, ego, task)
        st = self._park
        path = st["path"]
        info = {"parking": True, "planned": path.success, "message": path.message, "moves": len(path.segments),
                "move": st["move"], "path_length": path.length, "compute_time": st["compute_time"]}
        if not path.success or beh.maneuver == "parked" or st["done"]:
            traj = self._hold(t, ego, beh)
            self.last_trajectory = traj
            return {"trajectory": traj, "debug": PlannerDebug(t=t, mode="parking", info=info,
                                                              fallback=not path.success)}
        px, py, pth = self._rear_axle(ego.x, ego.y, ego.psi)
        while True:
            seg = path.segments[st["move"]]
            a, b, d = seg["start"], seg["end"], int(seg["direction"])
            lo = max(st["near"], a)
            hi = min(lo + 60, b + 1)
            i = lo + int(np.argmin((path.x[lo:hi] - px) ** 2 + (path.y[lo:hi] - py) ** 2))
            st["near"] = i
            th = path.theta[i]
            along = math.cos(th) * (px - path.x[i]) + math.sin(th) * (py - path.y[i])
            remaining = float(path.s[b] - path.s[i]) - d * along
            standstill = abs(ego.vx) < 0.1
            if remaining < 0.15 and standstill:
                if st["move"] + 1 < len(path.segments):
                    st["move"] += 1
                    st["near"] = path.segments[st["move"]]["start"]
                    continue
                st["done"] = True
                traj = self._hold(t, ego, beh)
                self.last_trajectory = traj
                info["move"] = st["move"]
                return {"trajectory": traj, "debug": PlannerDebug(t=t, mode="parking", info={**info, "done": True})}
            break
        traj = self._move_trajectory(t, ego, beh, i, b, d)
        self.last_trajectory = traj
        info.update(move=st["move"], remaining=remaining, direction=d)
        return {"trajectory": traj, "debug": PlannerDebug(t=t, mode="parking", info=info)}

    def _move_trajectory(self, t, ego, beh, i, b, d):
        path = self._park["path"]
        geo = self._park["geo"]
        x, y, th, k = path.x[i:b + 1], path.y[i:b + 1], path.theta[i:b + 1], path.kappa[i:b + 1]
        if len(x) < 2:
            return self._hold(t, ego, beh)
        s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
        task = beh.info["parking"]
        vmax = float(task.get("v_forward", 1.5) if d > 0 else task.get("v_reverse", 1.0))
        ds = DriveSettings()
        v = _speed_profile(geo, s, k, vmax, ds)
        v0 = min(abs(float(ego.vx)), vmax)
        # start at the measured speed and accelerate from there; stop at the end of the move
        v = np.minimum(v, np.sqrt(v0 ** 2 + 2 * ds.accel * s))
        v = np.minimum(v, np.sqrt(np.maximum(2 * ds.decel * (s[-1] - s), 0.0)))
        v[0] = max(v[0], v0)
        vm = np.maximum(0.5 * (v[1:] + v[:-1]), 0.05)
        tt = t + np.concatenate([[0.0], np.cumsum(np.diff(s) / vm)])
        a = np.gradient(v, tt) if len(tt) > 2 else np.zeros_like(v)
        # hold the end pose for 2 s so that sampling after the end stays at the goal of the move
        tt = np.concatenate([tt, [tt[-1] + 2.0]])
        x, y, th, k, v, a, s = (np.concatenate([arr, arr[-1:]]) for arr in (x, y, th, k, v, a, s))
        v[-1] = a[-1] = 0.0
        theta = th if d > 0 else th + np.pi                     # direction of motion
        kappa = d * k                                           # curvature w.r.t. the direction of motion
        dk = np.gradient(kappa, np.maximum(s, 0) + 1e-9 * np.arange(len(s))) if len(s) > 2 else np.zeros_like(kappa)
        return PlannedTrajectory(t=tt, x=x, y=y, theta=theta, kappa=kappa, dkappa=dk, v=v, a=a, s=s,
                                 d=np.zeros_like(s), direction=d, reference_point="rear_axle", lateral_mode="arc",
                                 longitudinal_mode="parking", cost=0.0, valid=True, reference_line=beh.reference_line,
                                 metadata={"parking": True, "move": self._park["move"]})

    def _hold(self, t, ego, beh):
        px, py, pth = self._rear_axle(ego.x, ego.y, ego.psi)
        d = -1 if ego.vx < 0 else 1
        theta = pth if d > 0 else pth + np.pi
        tt = np.array([t, t + 2.0])
        z = np.zeros(2)
        return PlannedTrajectory(t=tt, x=np.full(2, px), y=np.full(2, py), theta=np.full(2, theta), kappa=z.copy(),
                                 dkappa=z.copy(), v=z.copy(), a=z.copy(), s=z.copy(), d=z.copy(), direction=d,
                                 reference_point="rear_axle", lateral_mode="arc", longitudinal_mode="parking",
                                 valid=True, reference_line=beh.reference_line, metadata={"parking": True, "hold": True})
