"""Analysis of the optimal control problem (Werling 2011, 3.4.1, remarks 1 and 2).

    continuous_solution        (3.12): optimal polynomial for a continuous target manifold and a
                               given end time (end position follows from the transversality condition (3.11))
    transversality_residual    (3.13): necessary condition for the optimal end time
    optimal_end_time           numerical solution of the continuous problem (scan + refinement)
    estimate_sampling_horizon  remark 1: necessary length of the sampling horizon
    lock_in_distance           (3.14): remaining distance d0 / (1 + k tau^5 / 720)
    lock_in_check              remark 2: configuration warning if weights and the offset grid would
                               let the vehicle drive parallel to the reference instead of "locking in"
"""

from __future__ import annotations

import numpy as np

from ..framework.knowledge import trace
from .polynomials import coefficient_matrices, jerk_integral


@trace("werling2011", section="3.4.1", equation="(3.12)", concept="continuous_manifold",
       note="c345 = M3(tau)^-1 [xi_ref(tau) - M1(tau) c012], M3 = M2 + 120/k_xi in der c5-Spalte der ersten Zeile")
def continuous_solution(xi0, tau, k_xi, ref_state, k_jerk=1.0):
    # xi0 = (xi1, xi2, xi3)(0); ref_state = (xi_ref, xi_ref_dot, xi_ref_ddot)(tau)
    # cost: k_jerk int 1/2 u^2 + 1/2 k_xi (xi1(tau) - xi_ref(tau))^2 (the k_tau tau part is added by the caller)
    k = k_xi / k_jerk
    m1, m2 = coefficient_matrices(tau)
    c012 = np.array([xi0[0], xi0[1], 0.5 * xi0[2]])
    m3 = m2.copy()
    m3[0, 2] += 120.0 / k
    c345 = np.linalg.solve(m3, np.asarray(ref_state, dtype=float) - m1 @ c012)
    coeffs = np.concatenate([c012, c345])
    end_dev = -120.0 / k * c345[2]                                                   # (3.11)
    jerk = k_jerk * 0.5 * float(jerk_integral(coeffs, tau))
    return {"coeffs": coeffs, "end_deviation": float(end_dev), "jerk_cost": jerk,
            "deviation_cost": 0.5 * k_xi * end_dev ** 2}


@trace("werling2011", section="3.4.1", equation="(3.13)", concept="continuous_manifold",
       note="-1/2 psi3^2 - psi1 xi_ref_dot - psi2 xi_ref_ddot + k_tau = 0")
def transversality_residual(coeffs, tau, ref_state, k_tau, k_jerk=1.0):
    # Hamiltonian condition for a free end time; psi from (3.6) (scaled with the jerk weight)
    c = np.asarray(coeffs, dtype=float)
    t = float(tau)
    psi3 = 6 * c[3] + 24 * c[4] * t + 60 * c[5] * t * t
    psi2 = -(24 * c[4] + 120 * c[5] * t)
    psi1 = 120 * c[5]
    return float(k_jerk * (-0.5 * psi3 ** 2 - psi1 * ref_state[1] - psi2 * ref_state[2]) + k_tau)


def optimal_end_time(xi0, k_tau, k_xi, ref_fn, tau_max=15.0, n=600, k_jerk=1.0):
    # continuous optimum over tau of k_jerk int 1/2 u^2 + k_tau tau + 1/2 k_xi e^2 (remark 1)
    taus = np.linspace(tau_max / n, tau_max, n)
    costs, res = [], []
    for tau in taus:
        sol = continuous_solution(xi0, tau, k_xi, ref_fn(tau), k_jerk)
        costs.append(sol["jerk_cost"] + sol["deviation_cost"] + k_tau * tau)
        res.append(transversality_residual(sol["coeffs"], tau, ref_fn(tau), k_tau, k_jerk))
    costs = np.array(costs)
    i = int(np.argmin(costs))
    lo, hi = taus[max(i - 1, 0)], taus[min(i + 1, n - 1)]
    g = (np.sqrt(5) - 1) / 2

    def f(tau):
        sol = continuous_solution(xi0, tau, k_xi, ref_fn(tau), k_jerk)
        return sol["jerk_cost"] + sol["deviation_cost"] + k_tau * tau

    for _ in range(60):
        a, b = hi - g * (hi - lo), lo + g * (hi - lo)
        if f(a) < f(b):
            hi = b
        else:
            lo = a
    tau_opt = 0.5 * (lo + hi)
    sol = continuous_solution(xi0, tau_opt, k_xi, ref_fn(tau_opt), k_jerk)
    return {"tau": float(tau_opt), "cost": float(f(tau_opt)), "solution": sol, "taus": taus, "costs": costs,
            "residual": np.array(res),
            "residual_at_opt": transversality_residual(sol["coeffs"], tau_opt, ref_fn(tau_opt), k_tau, k_jerk)}


@trace("werling2011", section="3.4.2", equation="(3.14)", concept="lock_in",
       note="Bemerkung 2: Endabstand d0 / (1 + k_xi tau^5 / 720)")
def lock_in_distance(d0, k_xi, tau, k_jerk=1.0):
    # remaining distance to the reference of the continuous optimum (xi2(0) = xi3(0) = 0, constant reference)
    return d0 / (1.0 + (k_xi / k_jerk) * np.asarray(tau, dtype=float) ** 5 / 720.0)


@trace("werling2011", section="3.4.2", equation="Bemerkung 1, (3.13)", concept="sampling_horizon")
def estimate_sampling_horizon(sampling, cost, lane_width=3.5, speed_change=10.0, position_change=8.0, factor=1.2):
    # optimal end times of representative maneuvers -> recommended tau_max (remark 1)
    j, tt, dv = cost.jerk, cost.terminal_time, cost.terminal_deviation
    const = lambda value: (lambda tau: (value, 0.0, 0.0))  # noqa: E731
    lat = optimal_end_time((lane_width, 0.0, 0.0), tt.k_tau_lat, dv.k_delta, const(0.0), 20.0, 400, j.k_lat)
    pos = optimal_end_time((position_change, 0.0, 0.0), tt.k_tau_lon, dv.k_sigma, const(0.0), 20.0, 400, j.k_lon)
    # velocity change (quartic, free end position): rest-to-rest jerk 12 dv^2 / tau^3
    taus = np.linspace(0.05, 30.0, 3000)
    vel = j.k_lon * 6.0 * speed_change ** 2 / taus ** 3 + tt.k_tau_lon * taus
    tau_vel = float(taus[int(np.argmin(vel))])
    need = {"lateral": lat["tau"], "position": pos["tau"], "velocity": tau_vel}
    warnings = []
    if factor * lat["tau"] > sampling.lat_tau_max:
        warnings.append(f"Querhorizont τ_max = {sampling.lat_tau_max:.1f} s kürzer als {factor:.1f}·τ* = "
                        f"{factor * lat['tau']:.1f} s (Spurwechsel {lane_width:.1f} m)")
    if factor * max(pos["tau"], tau_vel) > sampling.lon_tau_max:
        warnings.append(f"Längshorizont τ_max = {sampling.lon_tau_max:.1f} s kürzer als {factor:.1f}·τ* = "
                        f"{factor * max(pos['tau'], tau_vel):.1f} s")
    return {"tau_opt": need, "recommended_lat_tau_max": factor * lat["tau"],
            "recommended_lon_tau_max": factor * max(pos["tau"], tau_vel), "warnings": warnings}


def _lock_offsets(grid, taus, k_jerk, k_tau, k_dev, rest_jerk, tau_stay):
    # offsets of the grid from which staying on the manifold is cheaper than moving closer to the reference
    locked = []
    for di in grid:
        if abs(di) < 1e-9:
            continue
        stay = 0.5 * k_dev * di ** 2 + k_tau * tau_stay
        closer = grid[np.abs(grid) < abs(di) - 1e-9]
        if len(closer) == 0:
            continue
        move = np.min(k_jerk * rest_jerk(di - closer[:, None], taus[None, :]) + k_tau * taus[None, :]
                      + 0.5 * k_dev * closer[:, None] ** 2)
        if move >= stay:
            locked.append(float(di))
    return locked


def lock_in_check(sampling, cost):
    # remark 2 as a configuration check of the discrete sets (d(t), d(s), s(t) and s_dot(t))
    j, tt, dv = cost.jerk, cost.terminal_time, cost.terminal_deviation
    quintic = lambda dx, tau: 360.0 * dx ** 2 / tau ** 5   # 1/2 int u^2 of a rest-to-rest quintic  # noqa: E731
    quartic = lambda dx, tau: 6.0 * dx ** 2 / tau ** 3     # 1/2 int u^2, velocity change dx       # noqa: E731

    def grid(step, rng):
        n = int(np.floor(rng / step + 1e-9)) if step > 0 else 0
        return np.arange(-n, n + 1) * step

    def taus(step, lo, hi):
        t = np.arange(max(step, lo), hi + 1e-9, step)
        return t if len(t) else np.array([hi])

    cases = {
        "quer d(t)": (grid(sampling.lat_d_step, sampling.lat_d_range), taus(sampling.lat_tau_step, sampling.lat_tau_min,
                      sampling.lat_tau_max), j.k_lat, tt.k_tau_lat, dv.k_delta, quintic, sampling.lat_tau_min),
        "quer d(s)": (grid(sampling.lat_d_step, sampling.lat_d_range), taus(sampling.arc_s_step, sampling.arc_s_min,
                      sampling.arc_s_max), j.k_arc, tt.k_s_arc, dv.k_delta_arc, quintic, sampling.arc_s_min),
        "längs s(t)": (grid(sampling.lon_sigma_step, sampling.lon_sigma_range), taus(sampling.lon_tau_step,
                       sampling.lon_tau_min, sampling.lon_tau_max), j.k_lon, tt.k_tau_lon, dv.k_sigma, quintic,
                       sampling.lon_tau_min),
        "längs ṡ(t)": (grid(sampling.lon_nu_step, sampling.lon_nu_range), taus(sampling.lon_tau_step,
                       sampling.lon_tau_min, sampling.lon_tau_max), j.k_lon, tt.k_tau_lon, dv.k_nu, quartic,
                       sampling.lon_tau_min),
    }
    out, warnings = {}, []
    for name, (g, tau, kj, kt, kd, rest, stay) in cases.items():
        locked = _lock_offsets(g, tau, kj, kt, kd, rest, stay)
        step = g[1] - g[0] if len(g) > 1 else 0.0
        entry = {"locked_offsets": locked, "step": float(step)}
        if name.startswith("quer d(t)") and step > 0:
            # continuous end distance (3.14) of the smallest grid offset at its optimal end time
            opt = optimal_end_time((step, 0.0, 0.0), kt, kd, lambda tau: (0.0, 0.0, 0.0), 10.0, 200, kj)
            entry["continuous_end_distance"] = float(lock_in_distance(step, kd, opt["tau"], kj))
            entry["continuous_tau"] = opt["tau"]
        out[name] = entry
        if locked:
            warnings.append(f"{name}: kein Einrasten auf der Referenz von den Versätzen {locked} aus "
                            f"(Gewichte/Raster nach Werling Bemerkung 2 prüfen) – Fahrzeug fährt ggf. parallel")
    out["warnings"] = warnings
    return out
