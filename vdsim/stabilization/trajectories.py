"""Reference trajectories for tests and examples (no planner needed).

    Path                      fine arc-length samples (x, y, theta, kappa, dkappa) with interpolation
    path_from_curvature       clothoid-like path by integration of kappa(s)
    path_from_lateral_offset  path y = d(x) (lane change / evasive maneuver) with exact curvature
    SpeedProfile              smooth v(t) (quintic smootherstep transitions, stops), s(t), a(t)
    build_trajectory          Path + SpeedProfile -> PlannedTrajectory
    transform_rear_to_point   rear-axle trajectory -> trajectory of a point lambda ahead (Satz 5),
                              e.g. lambda = l_h for the CoG trajectory of the same kinematic motion
    replan_from_prediction    re-initialized trajectory starting at a predicted vehicle state and
                              merging back into the previous trajectory (stands in for the planner)
"""

from __future__ import annotations

import math

import numpy as np

from ..framework.types import PlannedTrajectory
from .errors import flat_reference_transform


class Path:
    def __init__(self, s, x, y, theta, kappa, dkappa):
        self.s, self.x, self.y = np.asarray(s, float), np.asarray(x, float), np.asarray(y, float)
        self.theta, self.kappa, self.dkappa = (np.asarray(theta, float), np.asarray(kappa, float),
                                               np.asarray(dkappa, float))

    @property
    def length(self):
        return float(self.s[-1] - self.s[0])

    def evaluate(self, s):
        s = np.clip(s, self.s[0], self.s[-1])
        return tuple(np.interp(s, self.s, arr) for arr in (self.x, self.y, self.theta, self.kappa, self.dkappa))


def path_from_curvature(kappa_fn, length, ds=0.02, x0=0.0, y0=0.0, theta0=0.0):
    # integrates theta' = kappa, x' = cos theta, y' = sin theta (trapezoidal, fine grid)
    s = np.arange(0.0, length + ds, ds)
    kappa = np.array([kappa_fn(si) for si in s], dtype=float)
    dkappa = np.gradient(kappa, s)
    theta = theta0 + np.concatenate([[0.0], np.cumsum(0.5 * (kappa[1:] + kappa[:-1]) * ds)])
    c, sn = np.cos(theta), np.sin(theta)
    x = x0 + np.concatenate([[0.0], np.cumsum(0.5 * (c[1:] + c[:-1]) * ds)])
    y = y0 + np.concatenate([[0.0], np.cumsum(0.5 * (sn[1:] + sn[:-1]) * ds)])
    return Path(s, x, y, theta, kappa, dkappa)


def quintic_step(u):
    u = np.clip(u, 0.0, 1.0)
    return u**3 * (10 - 15 * u + 6 * u * u)


def smooth_bump(s, s0, s1, ramp, height):
    # plateau `height` on [s0, s1] with quintic ramps of length `ramp` (C2 curvature profiles)
    return height * float(quintic_step((s - s0 + ramp) / ramp) * quintic_step((s1 + ramp - s) / ramp))


def quintic_step_derivatives(u):
    u = np.clip(u, 0.0, 1.0)
    return (u**3 * (10 - 15 * u + 6 * u * u), 30 * u * u * (1 - u) ** 2, 60 * u * (1 - u) * (1 - 2 * u),
            60 * (1 - 6 * u + 6 * u * u))


def path_from_lateral_offset(segments, length, dx=0.02, x0=0.0, y0=0.0):
    """Path y(x) = sum of quintic offset transitions; segments = [(x_start, x_length, dy), ...].

    Exact heading, curvature and curvature derivative from y', y'', y'''.
    """
    xs = np.arange(0.0, length + dx, dx)
    y, yp, ypp, yppp = (np.zeros_like(xs) for _ in range(4))
    for xa, lx, dy in segments:
        u = (xs - xa) / lx
        d0, d1, d2, d3 = quintic_step_derivatives(u)
        inside = (u > 0) & (u < 1)
        y += dy * d0
        yp += np.where(inside, dy * d1 / lx, 0.0)
        ypp += np.where(inside, dy * d2 / lx**2, 0.0)
        yppp += np.where(inside, dy * d3 / lx**3, 0.0)
    q = 1.0 + yp**2
    theta = np.arctan(yp)
    kappa = ypp / q**1.5
    dkappa_dx = yppp / q**1.5 - 3 * yp * ypp**2 / q**2.5
    dkappa = dkappa_dx / np.sqrt(q)
    s = np.concatenate([[0.0], np.cumsum(0.5 * (np.sqrt(q[1:]) + np.sqrt(q[:-1])) * dx)])
    return Path(s, x0 + xs, y0 + y, theta, kappa, dkappa)


class SpeedProfile:
    """Piecewise smooth speed v(t): knots [(t_i, v_i)], quintic smootherstep between the knots."""

    def __init__(self, knots, dt=0.001):
        self.knots = [(float(t), float(v)) for t, v in knots]
        t0, t1 = self.knots[0][0], self.knots[-1][0]
        self.t = np.arange(t0, t1 + 30.0, dt)
        self.v = np.array([self._v(ti) for ti in self.t])
        self.a = np.array([self._a(ti) for ti in self.t])
        self.s = np.concatenate([[0.0], np.cumsum(0.5 * (self.v[1:] + self.v[:-1]) * dt)])

    def _segment(self, t):
        k = self.knots
        if t <= k[0][0]:
            return k[0], k[0]
        for a, b in zip(k[:-1], k[1:]):
            if a[0] <= t < b[0]:
                return a, b
        return k[-1], k[-1]

    def _v(self, t):
        a, b = self._segment(t)
        if b[0] == a[0]:
            return a[1]
        return a[1] + (b[1] - a[1]) * float(quintic_step((t - a[0]) / (b[0] - a[0])))

    def _a(self, t):
        a, b = self._segment(t)
        if b[0] == a[0]:
            return 0.0
        T = b[0] - a[0]
        return (b[1] - a[1]) * float(quintic_step_derivatives((t - a[0]) / T)[1]) / T

    def at(self, t):
        return (float(np.interp(t, self.t, self.s)), float(np.interp(t, self.t, self.v)),
                float(np.interp(t, self.t, self.a)))


def build_trajectory(path, profile, t0=0.0, duration=None, dt=0.01, reference_point="rear_axle", direction=1,
                     s0=0.0, lateral_mode=None):
    # PlannedTrajectory over absolute time t0 + profile time
    if duration is None:
        duration = float(profile.knots[-1][0] - profile.knots[0][0])
    tt = np.arange(0.0, duration + 0.5 * dt, dt)
    s, v, a = (np.array(z) for z in zip(*[profile.at(profile.knots[0][0] + ti) for ti in tt]))
    x, y, th, k, dk = path.evaluate(s0 + s)
    return PlannedTrajectory(t=t0 + tt, x=x, y=y, theta=th, kappa=k, dkappa=dk, v=v, a=a, s=s0 + s, d=np.zeros_like(s),
                             direction=direction, reference_point=reference_point,
                             lateral_mode=lateral_mode or ("arc" if reference_point == "rear_axle" else "time"))


def transform_rear_to_point(traj, lam, reference_point="cog"):
    # trajectory of the point lambda ahead of the rear axle for the same kinematic motion (4.20)-(4.24)
    n = len(traj)
    out = {k: np.zeros(n) for k in ("x", "y", "theta", "kappa", "v", "a")}
    sg = traj.direction
    for i in range(n):
        psi = traj.theta[i] if sg > 0 else traj.theta[i] + math.pi
        kd, vd = sg * traj.kappa[i], sg * traj.v[i]
        r = flat_reference_transform(traj.x[i], traj.y[i], psi, kd, sg * traj.dkappa[i] * traj.v[i],
                                     sg * traj.dkappa[i], vd, sg * traj.a[i], lam)
        th = r["theta"] if sg > 0 else r["theta"] - math.pi
        out["x"][i], out["y"][i], out["theta"][i] = r["y1"], r["y2"], th
        out["kappa"][i], out["v"][i], out["a"][i] = sg * r["kappa"], abs(r["v"]), sg * r["v_dot"]
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(out["x"]), np.diff(out["y"])))])
    dk = np.gradient(out["kappa"], s) if n > 2 and s[-1] > 0 else np.zeros(n)
    dk = np.where(np.isfinite(dk), dk, 0.0)
    return PlannedTrajectory(t=np.array(traj.t), x=out["x"], y=out["y"], theta=np.unwrap(out["theta"]),
                             kappa=out["kappa"], dkappa=dk, v=out["v"], a=out["a"], s=s, d=np.zeros(n),
                             direction=traj.direction, reference_point=reference_point,
                             lateral_mode="time" if reference_point == "cog" else "arc")


def replan_from_prediction(old, prediction, blend_time=3.0, dt=0.01, horizon=None):
    """New trajectory starting at the predicted state that merges back into `old` (stand-in planner).

    The Frenet offset (along/normal to the old trajectory) and its rate at the start decay with a
    quintic polynomial to zero within blend_time (Werling 4.5.2: speed and course continuous,
    curvature/acceleration from the current trajectory).
    """
    t0 = float(prediction["t"])
    horizon = horizon or max(old.t_end - t0, blend_time + 1.0)
    tt = t0 + np.arange(0.0, horizon + 0.5 * dt, dt)
    p0 = old.sample(t0)
    c, s = math.cos(p0.theta), math.sin(p0.theta)
    dx, dy = prediction["x"] - p0.x, prediction["y"] - p0.y
    off_t, off_n = c * dx + s * dy, -s * dx + c * dy
    dth = (prediction["theta"] - p0.theta + math.pi) % (2 * math.pi) - math.pi
    rate_t = prediction["v"] * math.cos(dth) - p0.v
    rate_n = prediction["v"] * math.sin(dth)
    T = blend_time

    def decay(z0, z1, tau):
        # quintic with z(0)=z0, z'(0)=z1, z''(0)=0 and z(T)=z'(T)=z''(T)=0
        u = np.clip(tau / T, 0.0, 1.0)
        a0, a1 = z0, z1 * T
        h0 = 1 - 10 * u**3 + 15 * u**4 - 6 * u**5
        h1 = u - 6 * u**3 + 8 * u**4 - 3 * u**5
        return a0 * h0 + a1 * h1

    pts = [old.sample(ti) for ti in tt]
    bx = np.array([p.x for p in pts])
    by = np.array([p.y for p in pts])
    bth = np.unwrap(np.array([p.theta for p in pts]))
    zt, zn = decay(off_t, rate_t, tt - t0), decay(off_n, rate_n, tt - t0)
    x = bx + np.cos(bth) * zt - np.sin(bth) * zn
    y = by + np.sin(bth) * zt + np.cos(bth) * zn
    vx, vy = np.gradient(x, tt), np.gradient(y, tt)
    ax, ay = np.gradient(vx, tt), np.gradient(vy, tt)
    v = np.hypot(vx, vy)
    theta = np.unwrap(np.arctan2(vy, vx))
    if old.direction < 0:
        theta = np.unwrap(np.arctan2(vy, vx))
    kappa = (vx * ay - vy * ax) / np.maximum(v, 1e-3) ** 3
    a = (vx * ax + vy * ay) / np.maximum(v, 1e-3)
    sarc = np.concatenate([[0.0], np.cumsum(v[1:] * dt)])
    dk = np.gradient(kappa, tt) / np.maximum(v, 1e-3)
    new = PlannedTrajectory(t=tt, x=x, y=y, theta=theta, kappa=kappa, dkappa=dk, v=v, a=a, s=sarc, d=zn,
                            direction=old.direction, reference_point=old.reference_point,
                            lateral_mode=old.lateral_mode, reinitialized=True)
    new.metadata["replanned_at"] = t0
    return new
