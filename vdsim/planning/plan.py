"""Exact representation of a planned trajectory (PlannedTrajectory.plan).

The selected trajectory is stored as its two polynomials (coefficients, end time, continuation
on the target manifold) instead of samples. The next planning cycle evaluates the start state
exactly at t0 + t_comp, so that the Bellman principle holds to machine precision (Werling 2011,
3.5.5 step 1); interpolating the sampled output would destroy the consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .combination import frenet_to_world, time_to_arc

V_EPS = 0.2        # m/s, below: dkappa from the geometry instead of kappa_dot / v


@dataclass
class TrajectoryPlan:
    t0: float                         # absolute start time of the polynomials
    reference_line: object
    reference_point: str              # "cog" / "rear_axle"
    lateral_mode: str                 # "time" / "arc"
    direction: int
    lat: object                       # PolynomialSet with one row
    lon: object                       # PolynomialSet with one row
    lat_s0: float = 0.0               # start arc length of d(s)
    lat_k: int = -1                   # absolute grid index of the lateral end time / end position
    lon_k: int = -1
    lat_delta: float = 0.0
    lat_tau: float = 0.0
    lon_offset: float = 0.0
    lon_tau: float = 0.0
    lon_kind: str = "velocity"
    lon_label: str = "velocity"
    d_ref: float = 0.0
    cost: float = 0.0
    valid: bool = True
    info: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ Frenet
    def frenet(self, t_abs):
        t = np.atleast_1d(np.asarray(t_abs, dtype=float)) - self.t0
        s, sd, sdd, sddd = (a[0] for a in self.lon.evaluate(t))
        if self.lateral_mode == "arc":
            d, d_p, d_pp, d_ppp = (a[0] for a in self.lat.evaluate(np.maximum(s - self.lat_s0, 0.0)[None, :]))
            d_d, d_dd = sd * d_p, sdd * d_p + sd * sd * d_pp
        else:
            d, d_d, d_dd, _ = (a[0] for a in self.lat.evaluate(t))
            d_p, d_pp = time_to_arc(sd, sdd, d_d, d_dd)
        return {"s": s, "s_d": sd, "s_dd": sdd, "s_ddd": sddd, "d": d, "d_d": d_d, "d_dd": d_dd, "d_p": d_p,
                "d_pp": d_pp}

    def world(self, t_abs, dkappa=True):
        fr = self.frenet(t_abs)
        w = frenet_to_world(self.reference_line, fr["s"], fr["s_d"], fr["s_dd"], fr["d"], fr["d_p"], fr["d_pp"])
        w["s"], w["d"] = fr["s"], fr["d"]
        if dkappa:
            w["dkappa"] = self.dkappa(np.atleast_1d(t_abs), w)
        return w

    def dkappa(self, t_abs, w=None, h=1e-3):
        # d kappa / d (arc length of the trajectory), robust at v ~ 0
        t = np.atleast_1d(np.asarray(t_abs, dtype=float))
        w = w if w is not None else self.world(t, dkappa=False)
        if self.lateral_mode == "arc":
            # purely geometric derivative: kappa(s) of the path d(s) (independent of the speed)
            fr = self.frenet(t)
            s = fr["s"]
            ks = []
            for sh in (s - h, s + h):
                d, d_p, d_pp, _ = (a[0] for a in self.lat.evaluate(np.maximum(sh - self.lat_s0, 0.0)[None, :]))
                ks.append(frenet_to_world(self.reference_line, sh, np.ones_like(sh), np.zeros_like(sh), d, d_p,
                                          d_pp))
            dk_ds = (ks[1]["kappa"] - ks[0]["kappa"]) / (2 * h)
            dl_ds = np.maximum(np.abs(0.5 * (ks[0]["v"] + ks[1]["v"])), 1e-6)    # v for s_dot = 1
            return dk_ds / dl_ds
        kp = self.world(t + h, dkappa=False)["kappa"]
        km = self.world(t - h, dkappa=False)["kappa"]
        kdot = (kp - km) / (2 * h)
        v = np.abs(w["v"])
        out = np.where(v > V_EPS, kdot / np.maximum(v, V_EPS), np.nan)
        ok = np.isfinite(out)
        if not np.any(ok):
            return np.zeros_like(t)
        if not np.all(ok):
            out = np.interp(t, t[ok], out[ok])
        return out

    def state_at(self, t_abs):
        w = self.world(np.array([float(t_abs)]), dkappa=False)
        fr = self.frenet(np.array([float(t_abs)]))
        out = {k: float(v[0]) for k, v in w.items()}
        out.update({f"f_{k}": float(v[0]) for k, v in fr.items()})
        return out

    def summary(self):
        return {"t0": self.t0, "reference_point": self.reference_point, "lateral_mode": self.lateral_mode,
                "direction": self.direction, "lat_coeffs": self.lat.coeffs[0].tolist(), "lat_tau": self.lat_tau,
                "lat_delta": self.lat_delta, "lat_k": int(self.lat_k), "lon_coeffs": self.lon.coeffs[0].tolist(),
                "lon_tau": self.lon_tau, "lon_offset": self.lon_offset, "lon_k": int(self.lon_k),
                "lon_kind": self.lon_kind, "cost": self.cost, "valid": self.valid}
