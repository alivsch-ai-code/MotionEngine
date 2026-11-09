"""Closed-loop parking: the planned path driven by a controller on a low-speed vehicle model.

Vehicle model (parking speed, |v| < ~3 m/s):
    * lateral: the reference point P moves without side slip (kinematic single track, see steering.py);
      the curvature follows from the actual road-wheel angles, which follow the commands with a rate limit
      (electric power steering, steering at standstill allowed);
    * longitudinal: m dv/dt = F_x - F_roll - m g sin(slope), where the drive force acts at the driven
      axle(s) and is limited by mu times their normal load (static load plus load transfer and slope),
      brakes act on all wheels. The drive layout (fwd / rwd / awd) therefore decides whether the vehicle
      can start on a slope or on low friction: on a slope uphill the load moves to the rear axle, so a
      front-driven car loses traction first (Mitschke and Wallentowitz 2014, ch. 4).

Controller: rear-axle feedback law of Samson (1995) / De Luca, Oriolo and Samson (1998) for the reference
point P, written for signed speed so that it holds forward and in reverse:

    kappa_cmd = kappa_ref cos(e_theta) / (1 - kappa_ref e) - k_theta sign(v) e_theta - k_e sinc(e_theta) e

(e lateral offset of P from the path, left > 0; e_theta heading error). Speed: per move a profile that
accelerates with a_max and stops at the end of the move (the cusp); the steering is turned at standstill
to the curvature the next move starts with.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ...core.conventions import G
from .planner import CollisionChecker, ParkingPath
from .steering import SteeringGeometry

LAYOUTS = ("fwd", "rwd", "awd")


@dataclass
class DriveSettings:
    v_forward: float = 1.5          # m/s
    v_reverse: float = 1.0          # m/s
    accel: float = 0.8              # m/s^2, comfortable start
    decel: float = 1.0              # m/s^2
    steer_rate: float = 0.6         # rad/s road-wheel angle (~520 deg/s at the steering wheel for i = 15)
    layout: str = "fwd"             # driven axle(s)
    front_share_awd: float = 0.5    # torque share of the front axle for awd
    mu: float = 0.9                 # tire-road friction (0.9 dry, 0.5 wet, 0.2 snow)
    slope: float = 0.0              # road gradient along the street (+x), rise per meter (0.1 = 10 %)
    max_drive_force: float = 6000.0 # N, powertrain limit at crawl speed
    rolling_resistance: float = 0.015
    k_theta: float = 2.0            # 1/m
    k_e: float = 1.2                # 1/m^2
    k_v: float = 4.0                # 1/s, speed controller gain
    dt: float = 0.02                # s
    preview: float = 0.5            # s, curvature preview (steering lag)
    v_min: float = 0.03             # m/s, crawl speed where the steering must catch up with a curvature jump
    stop_tolerance: float = 0.05    # m, end of a move
    max_time: float = 240.0         # s


@dataclass
class DriveResult:
    t: np.ndarray
    x: np.ndarray
    y: np.ndarray
    theta: np.ndarray
    v: np.ndarray
    delta_f: np.ndarray
    delta_r: np.ndarray
    e_lat: np.ndarray
    e_head: np.ndarray
    traction_limited: np.ndarray
    segment: np.ndarray
    kpis: dict = field(default_factory=dict)
    success: bool = True
    message: str = "ok"


def _actual_curvature(geo: SteeringGeometry, df, dr):
    return (math.tan(df) - math.tan(dr)) / geo.wheelbase


def _traction_limit(vehicle, geo, s: DriveSettings, theta, accel_dir, ax):
    # max drive force from the friction of the driven axle(s); slope along the heading and load transfer
    v = getattr(vehicle, "vehicle", vehicle)
    m, L, h = v.mass, v.wheelbase, v.cg_height
    lf, lr = v.cg_to_front, v.wheelbase - v.cg_to_front
    slope_heading = s.slope * math.cos(theta)                  # rise per meter along the vehicle heading
    angle = math.atan(slope_heading)
    w = m * G * math.cos(angle)
    # longitudinal load transfer from the slope (gravity component) and the acceleration
    dfz = m * (G * math.sin(angle) + ax) * h / L
    fz_f = max(w * lr / L - dfz, 0.0)
    fz_r = max(w * lf / L + dfz, 0.0)
    if s.layout == "fwd":
        return s.mu * fz_f
    if s.layout == "rwd":
        return s.mu * fz_r
    # awd with a fixed torque split: the first axle to slip limits the total
    share = min(max(s.front_share_awd, 1e-3), 1 - 1e-3)
    return min(s.mu * fz_f / share, s.mu * fz_r / (1 - share))


def _speed_profile(geo: SteeringGeometry, ss, pk, vmax, s: DriveSettings):
    """Speed limit along a move: the steering angle must be reachable with the steering rate,
    v <= steer_rate / |d delta / ds|; then acceleration and deceleration limits (forward/backward pass)."""
    if len(ss) < 2:
        return np.full(len(ss), vmax)
    ang = np.array([max(abs(a) for a in geo.angles(float(k))) * (1 if k >= 0 else -1) for k in pk])
    win = 3
    grad = np.zeros_like(ang)
    for i in range(len(ang)):
        a, b = max(i - win, 0), min(i + win, len(ang) - 1)
        ds = max(ss[b] - ss[a], 1e-3)
        grad[i] = abs(ang[b] - ang[a]) / ds
    v = np.minimum(vmax, s.steer_rate / np.maximum(grad, 1e-6))
    v = np.maximum(v, s.v_min)
    for i in range(1, len(v)):
        v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * s.accel * (ss[i] - ss[i - 1])))
    for i in range(len(v) - 2, -1, -1):
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * s.decel * (ss[i + 1] - ss[i])))
    return v


def drive(path: ParkingPath, vehicle, geo: SteeringGeometry, settings: DriveSettings | None = None,
          checker: CollisionChecker | None = None) -> DriveResult:
    """Drive the planned path move by move; returns traces and KPIs."""
    s = settings or DriveSettings()
    if s.layout not in LAYOUTS:
        raise ValueError(f"unknown drive layout '{s.layout}', available: {LAYOUTS}")
    v_cfg = getattr(vehicle, "vehicle", vehicle)
    m = v_cfg.mass
    kmax = geo.max_curvature
    max_f = geo.max_front if geo.mode != "rear" else 0.0
    max_r = geo.max_rear
    x, y, th = float(path.x[0]), float(path.y[0]), float(path.theta[0])
    v = 0.0
    df, dr = geo.angles(float(path.kappa[0]))
    rec: dict[str, list] = {k: [] for k in ("t", "x", "y", "theta", "v", "df", "dr", "e", "eth", "tl", "seg")}
    t = 0.0
    stand_steer_time = 0.0
    traction_time = 0.0
    ok = True
    message = "ok"

    def record(e, eth, limited, k):
        rec["t"].append(t)
        rec["x"].append(x)
        rec["y"].append(y)
        rec["theta"].append(th)
        rec["v"].append(v)
        rec["df"].append(df)
        rec["dr"].append(dr)
        rec["e"].append(e)
        rec["eth"].append(eth)
        rec["tl"].append(limited)
        rec["seg"].append(k)

    for k, seg in enumerate(path.segments):
        a, b, direction = seg["start"], seg["end"], int(seg["direction"])
        px, py, pth, pk = path.x[a:b + 1], path.y[a:b + 1], path.theta[a:b + 1], path.kappa[a:b + 1]
        # signed arc length along the move (direction of travel > 0)
        ss = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(px), np.diff(py)))])
        total = float(ss[-1])
        vmax = s.v_forward if direction > 0 else s.v_reverse
        v_prof = _speed_profile(geo, ss, pk, vmax, s)
        # 1) steer at standstill to the curvature the move starts with
        tf, tr = geo.angles(float(pk[min(1, len(pk) - 1)]))
        while abs(tf - df) > 1e-3 or abs(tr - dr) > 1e-3:
            step = s.steer_rate * s.dt
            df += float(np.clip(tf - df, -step, step))
            dr += float(np.clip(tr - dr, -step, step))
            t += s.dt
            stand_steer_time += s.dt
            record(0.0, 0.0, False, k)
        # 2) drive the move
        i_near = 0
        stuck = 0.0
        while True:
            # nearest path point (monotone search ahead of the last one)
            lo, hi = i_near, min(i_near + 40, len(px))
            d2 = (px[lo:hi] - x) ** 2 + (py[lo:hi] - y) ** 2
            i_near = lo + int(np.argmin(d2))
            th_p = float(pth[i_near])
            # curvature preview: the steering needs time to follow, so look ahead by |v| * tau
            s_prev = float(ss[i_near]) + abs(v) * s.preview
            k_p = float(np.interp(s_prev, ss, pk))
            dx, dy = x - float(px[i_near]), y - float(py[i_near])
            e = -math.sin(th_p) * dx + math.cos(th_p) * dy                  # lateral offset, left > 0
            along = math.cos(th_p) * dx + math.sin(th_p) * dy               # ahead of the nearest point
            eth = (th - th_p + math.pi) % (2 * math.pi) - math.pi
            remaining = total - float(ss[i_near]) - direction * along
            if remaining < s.stop_tolerance and abs(v) < 0.05:
                break
            if t > s.max_time:
                ok, message = False, "time limit reached"
                break
            # lateral control (signed speed form)
            sgn = 1.0 if direction > 0 else -1.0
            sinc = math.sin(eth) / eth if abs(eth) > 1e-6 else 1.0
            k_cmd = k_p * math.cos(eth) / max(1.0 - k_p * e, 0.2) - s.k_theta * sgn * eth - s.k_e * sinc * e
            k_cmd = float(np.clip(k_cmd, -kmax, kmax))
            tf, tr = geo.angles(k_cmd)
            step = s.steer_rate * s.dt
            df += float(np.clip(tf - df, -step, step))
            dr += float(np.clip(tr - dr, -step, step))
            df = float(np.clip(df, -max_f, max_f)) if geo.mode != "rear" else 0.0
            dr = float(np.clip(dr, -max_r, max_r))
            # longitudinal control: profile to stop at the end of the move
            # stop exactly at the end of the move: braking curve with 30 % reserve, crawl only before the end
            rem = max(remaining - 0.01, 0.0)
            v_stop = math.sqrt(2 * 0.7 * s.decel * rem) + (0.05 if remaining > 0.1 else 0.0)
            v_target = sgn * min(float(np.interp(float(ss[i_near]), ss, v_prof)), v_stop)
            a_brake = 1.5 * s.decel
            a_cmd = float(np.clip(s.k_v * (v_target - v), -a_brake, s.accel)) if sgn > 0 else \
                float(np.clip(s.k_v * (v_target - v), -s.accel, a_brake))
            slope_heading = s.slope * math.cos(th)
            f_grade = -m * G * math.sin(math.atan(slope_heading))
            f_roll = -np.sign(v) * s.rolling_resistance * m * G if abs(v) > 1e-3 else 0.0
            f_need = m * a_cmd - f_grade - f_roll
            limited = False
            # traction: a force that speeds the vehicle up in the direction of travel comes from the drive
            if f_need * sgn > 0:
                cap = min(_traction_limit(vehicle, geo, s, th, sgn, a_cmd), s.max_drive_force)
                if abs(f_need) > cap:
                    f_need = sgn * cap
                    limited = True
            else:
                f_need = float(np.clip(f_need, -s.mu * m * G, s.mu * m * G))
            acc = (f_need + f_grade + f_roll) / m
            v_new = v + acc * s.dt
            # at standstill the brakes hold the vehicle unless the drive overcomes the slope
            if abs(v) < 1e-3 and limited and (v_new * sgn) <= 0:
                v_new = 0.0
            v = v_new
            kap = _actual_curvature(geo, df, dr)
            th_new = th + v * kap * s.dt
            if abs(kap) > 1e-9:
                x += (math.sin(th_new) - math.sin(th)) / kap
                y -= (math.cos(th_new) - math.cos(th)) / kap
            else:
                x += v * s.dt * math.cos(th)
                y += v * s.dt * math.sin(th)
            th = th_new
            t += s.dt
            if limited:
                traction_time += s.dt
                stuck = stuck + s.dt if abs(v) < 0.02 else 0.0
                if stuck > 3.0:
                    ok, message = False, "no traction: the driven wheels cannot move the vehicle"
                    record(e, eth, limited, k)
                    break
            else:
                stuck = 0.0
            record(e, eth, limited, k)
        if not ok:
            break
        v = 0.0
    arr = {k: np.array(vv, dtype=float) for k, vv in rec.items()}
    goal = (float(path.x[-1]), float(path.y[-1]), float(path.theta[-1]))
    kpis = {
        "final_position_error": math.hypot(x - goal[0], y - goal[1]),
        "final_heading_error_deg": math.degrees(abs((th - goal[2] + math.pi) % (2 * math.pi) - math.pi)),
        "max_lateral_error": float(np.max(np.abs(arr["e"]))) if len(arr["e"]) else 0.0,
        "max_heading_error_deg": math.degrees(float(np.max(np.abs(arr["eth"])))) if len(arr["eth"]) else 0.0,
        "maneuver_time": t,
        "standstill_steering_time": stand_steer_time,
        "traction_limited_time": traction_time,
        "moves": len(path.segments),
        "gear_changes": max(len(path.segments) - 1, 0),
        "path_length": path.length,
        "max_front_angle_deg": math.degrees(float(np.max(np.abs(arr["df"])))) if len(arr["df"]) else 0.0,
        "max_rear_angle_deg": math.degrees(float(np.max(np.abs(arr["dr"])))) if len(arr["dr"]) else 0.0,
    }
    if checker is not None and len(arr["x"]):
        kpis["min_clearance"] = float(np.min(checker.min_clearance(arr["x"][::5], arr["y"][::5], arr["theta"][::5])))
    if ok and kpis["final_position_error"] > 0.3:
        ok, message = False, "did not reach the goal"
    return DriveResult(arr["t"], arr["x"], arr["y"], arr["theta"], arr["v"], arr["df"], arr["dr"], arr["e"],
                       arr["eth"], arr["tl"].astype(bool), arr["seg"].astype(int), kpis, ok, message)
