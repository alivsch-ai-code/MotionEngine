"""Step-by-step derivation of one Werling planning cycle (Werling 2011, ch. 3 and appendix A).

The planner is run once; the selected trajectory is then re-derived from its boundary conditions so
that every number shown to the engineer is checked against the planner's own result:

    1. start state in Frenet coordinates               (reinitialization / stitching, 3.5.5)
    2. lateral quintic   d(t) or d(s)                  Satz 1, (3.6)-(3.8)
    3. longitudinal quartic / quintic s(t)             Satz 2 / Satz 1, Tab. 3.1
    4. cost terms  1/2 k_j J + k_tau tau + 1/2 k_x x^2 (3.4), (3.10)
    5. combination and lazy selection                  3.2, 3.5.5
    6. Frenet -> world transformation                  (A.1)-(A.6)
    7. restrictions over the horizon                   3.5.3
    8. vehicle physics: steady-state single track      Rajamani 3.2 (linear tires)

Formulas are LaTeX strings; descriptive text is translated by the client (step ids are stable keys).
"""

from __future__ import annotations

import math

import numpy as np

from ..core.conventions import G
from ..planning.polynomials import jerk_integral, polyval, quartic_coefficients, quintic_coefficients


def _f(x, digits=4):
    x = float(x)
    if not math.isfinite(x):
        return "\\infty" if x > 0 else "-\\infty"
    if x == 0.0:
        return "0"
    if abs(x) >= 1e4 or abs(x) < 1e-3:
        mant, exp = f"{x:.{digits - 1}e}".split("e")
        return f"{mant} \\cdot 10^{{{int(exp)}}}"
    return f"{x:.{digits}g}"


def _poly_latex(var, c, arg):
    terms = []
    for i, ci in enumerate(c):
        if abs(ci) < 1e-15:
            continue
        mono = "" if i == 0 else (arg if i == 1 else f"{arg}^{i}")
        terms.append(f"{_f(ci)}\\,{mono}" if mono else _f(ci))
    body = " + ".join(terms).replace("+ -", "- ") or "0"
    return f"{var}({arg}) = {body}"


def _num(x):
    x = float(x)
    return x if math.isfinite(x) else None


def explain_cycle(planner, start, debug, trajectory, behavior, vehicle_cfg, horizon=None):
    """Derivation dict of the selected trajectory of one planning cycle (all SI units)."""
    plan = trajectory.plan
    summ = plan.summary()
    p = planner.params
    cost = p.cost
    st = debug.start_state
    arc = plan.lateral_mode == "arc"
    lat_c = np.asarray(summ["lat_coeffs"], dtype=float)
    lon_c = np.asarray(summ["lon_coeffs"], dtype=float)
    tau_lat, tau_lon = float(summ["lat_tau"]), float(summ["lon_tau"])
    steps = []

    # ------------------------------------------------------------------ 1 start state
    steps.append(
        {
            "id": "start_state",
            "quantities": {
                k: _num(st[k])
                for k in ("t", "s", "s_d", "s_dd", "d", "d_d", "d_dd", "d_p", "d_pp", "v", "kappa", "a")
                if k in st
            }
            | {
                "reference_point": st.get("reference_point"),
                "lateral_mode": st.get("lateral_mode"),
                "source": st.get("source"),
                "reinitialized": bool(st.get("reinitialized", False)),
            },
            "formulas": [
                "\\xi_s(0) = [s_0,\\ \\dot s_0,\\ \\ddot s_0] = "
                f"[{_f(st['s'])},\\ {_f(st['s_d'])},\\ {_f(st['s_dd'])}]",
                (f"\\xi_d(0) = [d_0,\\ d'_0,\\ d''_0] = [{_f(st['d'])},\\ {_f(st['d_p'])},\\ {_f(st['d_pp'])}]")
                if arc
                else (
                    "\\xi_d(0) = [d_0,\\ \\dot d_0,\\ \\ddot d_0] = "
                    f"[{_f(st['d'])},\\ {_f(st['d_d'])},\\ {_f(st['d_dd'])}]"
                ),
            ],
        }
    )

    # ------------------------------------------------------------------ 2 lateral quintic
    d_ref = float(getattr(behavior, "d_ref", 0.0))
    delta = float(summ["lat_delta"])
    d0, d1_0, d2_0 = (st["d"], st["d_p"], st["d_pp"]) if arc else (st["d"], st["d_d"], st["d_dd"])
    lat_check = quintic_coefficients(d0, d1_0, d2_0, d_ref + delta, 0.0, 0.0, tau_lat)
    var, arg = ("d", "s") if arc else ("d", "t")
    j_lat = float(jerk_integral(lat_c[None], tau_lat)[0])
    k_j_lat = cost.jerk.k_arc if arc else cost.jerk.k_lat
    k_t_lat = cost.terminal_time.k_s_arc if arc else cost.terminal_time.k_tau_lat
    k_d_lat = cost.terminal_deviation.k_delta_arc if arc else cost.terminal_deviation.k_delta
    c_lat = 0.5 * k_j_lat * j_lat + k_t_lat * tau_lat + 0.5 * k_d_lat * delta**2
    tsym = "S" if arc else "\\tau"
    steps.append(
        {
            "id": "lateral",
            "quantities": {
                "mode": plan.lateral_mode,
                "tau": tau_lat,
                "delta": delta,
                "d_ref": d_ref,
                "d_end": d_ref + delta,
                "coefficients": lat_c.tolist(),
                "jerk_integral": j_lat,
                "cost": c_lat,
                "verification_max_abs_error": float(np.max(np.abs(lat_check - lat_c))),
            },
            "formulas": [
                f"\\min \\int_0^{{{tsym}}} \\tfrac12 \\dddot d^2\\,d{arg} \\;\\Rightarrow\\; d({arg}) = \\sum_{{i=0}}^{{5}} c_i {arg}^i",
                f"\\xi_d({tsym}) = [d_{{ref}} + \\delta,\\ 0,\\ 0] = [{_f(d_ref + delta)},\\ 0,\\ 0],\\quad "
                f"{tsym} = {_f(tau_lat)}",
                "\\Delta p = d_1 - (d_0 + \\dot d_0 \\tau + \\tfrac12 \\ddot d_0 \\tau^2),\\ "
                "\\Delta v = \\dot d_1 - (\\dot d_0 + \\ddot d_0\\tau),\\ \\Delta a = \\ddot d_1 - \\ddot d_0",
                "c_3 = \\frac{10\\Delta p - 4\\Delta v\\,\\tau + \\tfrac12\\Delta a\\,\\tau^2}{\\tau^3},\\ "
                "c_4 = \\frac{-15\\Delta p + 7\\Delta v\\,\\tau - \\Delta a\\,\\tau^2}{\\tau^4},\\ "
                "c_5 = \\frac{6\\Delta p - 3\\Delta v\\,\\tau + \\tfrac12\\Delta a\\,\\tau^2}{\\tau^5}",
                _poly_latex(var, lat_c, arg),
                f"J_d = \\int_0^{{{tsym}}} (6c_3 + 24c_4{arg} + 60c_5{arg}^2)^2 d{arg} = {_f(j_lat)}",
                f"C_d = \\tfrac12 k_j J_d + k_{{\\tau}} {tsym} + \\tfrac12 k_\\delta \\delta^2 = "
                f"\\tfrac12 \\cdot {_f(k_j_lat)} \\cdot {_f(j_lat)} + {_f(k_t_lat)} \\cdot {_f(tau_lat)} + "
                f"\\tfrac12 \\cdot {_f(k_d_lat)} \\cdot {_f(delta)}^2 = {_f(c_lat)}",
            ],
        }
    )

    # ------------------------------------------------------------------ 3 longitudinal
    kind = str(summ["lon_kind"])
    off = float(summ["lon_offset"])
    j_lon = float(jerk_integral(lon_c[None], tau_lon)[0])
    _, sd_end, sdd_end, _ = (a[0, 0] for a in polyval(lon_c[None], np.array([[tau_lon]])))
    if kind == "velocity":
        v_ref = float(sd_end - off)
        lon_check = quartic_coefficients(st["s"], st["s_d"], st["s_dd"], v_ref + off, 0.0, tau_lon)
        k_off = cost.terminal_deviation.k_nu
        off_sym, end_formula = (
            "\\nu",
            (
                f"\\dot s(\\tau) = \\dot s_{{ref}} + \\nu = {_f(v_ref)} + {_f(off)},\\ "
                "\\ddot s(\\tau) = 0,\\ s(\\tau)\\ \\mathrm{free} \\Rightarrow c_5 = 0"
            ),
        )
        verification = float(np.max(np.abs(lon_check - lon_c)))
    else:
        k_off = cost.terminal_deviation.k_sigma
        s_end = float(polyval(lon_c[None], np.array([[tau_lon]]))[0][0, 0])
        off_sym, end_formula = (
            "\\sigma",
            (
                f"s(\\tau) = s_{{ref}}(\\tau) + \\sigma = {_f(s_end)},\\ "
                f"\\dot s(\\tau) = {_f(sd_end)},\\ \\ddot s(\\tau) = {_f(sdd_end)}"
            ),
        )
        lon_check = quintic_coefficients(st["s"], st["s_d"], st["s_dd"], s_end, sd_end, sdd_end, tau_lon)
        verification = float(np.max(np.abs(lon_check - lon_c)))
    k_j_lon, k_t_lon = cost.jerk.k_lon, cost.terminal_time.k_tau_lon
    c_lon = 0.5 * k_j_lon * j_lon + k_t_lon * tau_lon + 0.5 * k_off * off**2
    steps.append(
        {
            "id": "longitudinal",
            "quantities": {
                "mode": kind,
                "tau": tau_lon,
                "offset": off,
                "coefficients": lon_c.tolist(),
                "jerk_integral": j_lon,
                "cost": c_lon,
                "verification_max_abs_error": verification,
            },
            "formulas": [
                (
                    "\\min \\int_0^\\tau \\tfrac12 \\dddot s^2\\,dt \\;\\Rightarrow\\; s(t) = \\sum_{i=0}^{"
                    + ("4" if kind == "velocity" else "5")
                    + "} c_i t^i"
                ),
                end_formula + f",\\quad \\tau = {_f(tau_lon)}",
                _poly_latex("s", lon_c, "t"),
                f"J_s = {_f(j_lon)}",
                f"C_s = \\tfrac12 k_j J_s + k_\\tau \\tau + \\tfrac12 k_{{{off_sym}}} {off_sym}^2 = "
                f"\\tfrac12 \\cdot {_f(k_j_lon)} \\cdot {_f(j_lon)} + {_f(k_t_lon)} \\cdot {_f(tau_lon)} + "
                f"\\tfrac12 \\cdot {_f(k_off)} \\cdot {_f(off)}^2 = {_f(c_lon)}",
            ],
        }
    )

    # ------------------------------------------------------------------ 4 combination and selection
    total = cost.k_lat * c_lat + cost.k_lon * c_lon
    status = np.asarray(debug.candidates_status, dtype=int)
    steps.append(
        {
            "id": "selection",
            "quantities": {
                "n_candidates": int(debug.n_candidates),
                "n_checked": int(debug.n_checked),
                "cost_total": total,
                "cost_planner": _num(plan.cost),
                "cost_terms_planner": {k: _num(v) for k, v in debug.cost_terms.items()},
                "constraint_violations": {k: int(v) for k, v in debug.constraint_violations.items()},
                "fallback": bool(debug.fallback),
                "sample_status_counts": {
                    "valid": int(np.sum(status == 0)),
                    "constraint": int(np.sum(status == 1)),
                    "collision": int(np.sum(status == 2)),
                    "unchecked": int(np.sum(status == 3)),
                },
                "modes": {
                    k: {
                        "best_cost": _num(v.get("best_cost") or float("nan")),
                        "initial_jerk": _num(v.get("initial_jerk") or float("nan")),
                        "selected": bool(v.get("selected")),
                    }
                    for k, v in debug.modes.items()
                },
            },
            "formulas": [
                "C = k_{lat} C_d + k_{lon} C_s = "
                f"{_f(cost.k_lat)} \\cdot {_f(c_lat)} + {_f(cost.k_lon)} \\cdot {_f(c_lon)} = {_f(total)}",
                f"N = N_d \\times N_s = {int(debug.n_candidates)},\\quad N_{{\\mathrm{{checked}}}} = {int(debug.n_checked)}",
            ],
        }
    )

    # ------------------------------------------------------------------ series of the selected trajectory
    t0 = float(plan.t0)
    t_end = t0 + float(horizon if horizon is not None else max(tau_lon, 0.0 if arc else tau_lat, 3.0))
    tt = np.linspace(t0, t_end, 61)
    fr = plan.frenet(tt)
    w = plan.world(tt, dkappa=False)
    series = {"t": (tt - t0).tolist()}
    for k in ("s", "s_d", "s_dd", "s_ddd", "d", "d_d", "d_dd", "d_p", "d_pp"):
        series[k] = [_num(v) for v in fr[k]]
    for k in ("x", "y", "theta", "kappa", "v", "a"):
        series[k] = [_num(v) for v in w[k]]
    a_lat = np.asarray(w["v"]) ** 2 * np.asarray(w["kappa"])
    series["a_lat"] = [_num(v) for v in a_lat]

    # ------------------------------------------------------------------ 5 Frenet -> world
    ref = plan.reference_line
    samples = []
    for i in (0, 20, 40, 60):
        s_i, d_i, dp_i = float(fr["s"][i]), float(fr["d"][i]), float(fr["d_p"][i])
        x_r, y_r, th_r, k_r, _ = (float(np.asarray(v).ravel()[0]) for v in ref.evaluate(np.array([s_i])))
        samples.append(
            {
                "t": float(tt[i] - t0),
                "s": s_i,
                "d": d_i,
                "d_p": dp_i,
                "x_r": x_r,
                "y_r": y_r,
                "theta_r": th_r,
                "kappa_r": k_r,
                "x": float(w["x"][i]),
                "y": float(w["y"][i]),
                "theta": float(w["theta"][i]),
                "kappa": float(w["kappa"][i]),
                "v": float(w["v"][i]),
            }
        )
    m = samples[1]
    steps.append(
        {
            "id": "transformation",
            "quantities": {"samples": samples},
            "formulas": [
                "x = x_r(s) - d\\,\\sin\\theta_r(s),\\quad y = y_r(s) + d\\,\\cos\\theta_r(s)",
                "\\Delta\\theta = \\arctan\\frac{d'}{1 - \\kappa_r d},\\quad \\theta = \\theta_r + \\Delta\\theta,\\quad "
                "v = \\dot s\\,\\frac{1 - \\kappa_r d}{\\cos\\Delta\\theta}",
                "\\kappa = \\Big(\\big(d'' + (\\kappa_r' d + \\kappa_r d')\\tan\\Delta\\theta\\big)"
                "\\frac{\\cos^2\\Delta\\theta}{1 - \\kappa_r d} + \\kappa_r\\Big)\\frac{\\cos\\Delta\\theta}{1 - \\kappa_r d}",
                f"t = {_f(m['t'])}:\\ x = {_f(m['x_r'])} - {_f(m['d'])}\\sin({_f(m['theta_r'])}) = {_f(m['x'])},\\ "
                f"y = {_f(m['y_r'])} + {_f(m['d'])}\\cos({_f(m['theta_r'])}) = {_f(m['y'])}",
            ],
        }
    )

    # ------------------------------------------------------------------ 6 restrictions
    c = p.constraints
    veh = vehicle_cfg.vehicle
    kappa_max = (
        c.max_curvature.kappa_max
        if c.max_curvature.kappa_max > 0
        else c.max_curvature.auto_factor * math.tan(veh.max_steer_angle) / veh.wheelbase
    )
    checks = [
        (
            "lateral_acceleration",
            float(np.max(np.abs(a_lat))),
            c.max_lateral_acceleration.a_max,
            "m/s^2",
            "|v^2\\kappa|",
        ),
        ("longitudinal_acceleration", float(np.max(w["a"])), c.max_longitudinal_acceleration.a_accel_max, "m/s^2", "a"),
        (
            "longitudinal_deceleration",
            float(-np.min(w["a"])),
            c.max_longitudinal_acceleration.a_decel_max,
            "m/s^2",
            "-a",
        ),
        ("curvature", float(np.max(np.abs(w["kappa"]))), kappa_max, "1/m", "|\\kappa|"),
        ("speed", float(np.max(w["v"])), c.speed_range.v_max, "m/s", "v"),
        (
            "yaw_rate",
            float(np.max(np.abs(np.asarray(w["v"]) * np.asarray(w["kappa"])))),
            c.max_yaw_rate.r_max,
            "rad/s",
            "|v\\kappa|",
        ),
    ]
    steps.append(
        {
            "id": "constraints",
            "quantities": {
                "checks": [
                    {
                        "name": n,
                        "max": v,
                        "limit": lim,
                        "unit": u,
                        "ok": bool(v <= lim + 1e-9),
                        "utilization": v / lim if lim > 0 else None,
                    }
                    for n, v, lim, u, _ in checks
                ]
            },
            "formulas": [f"\\max_t {sym} = {_f(v)} \\le {_f(lim)}\\ \\mathrm{{{u}}}" for _, v, lim, u, sym in checks],
        }
    )

    # ------------------------------------------------------------------ 7 vehicle physics (steady state)
    from ..tire_models import create_tires
    from ..vehicle_models.common import axle_cornering_stiffness

    tires = vehicle_cfg.tires
    fz_f, fz_r = veh.static_axle_loads
    tf, tr = create_tires(tires)
    c_f = axle_cornering_stiffness(tf, fz_f / 2)
    c_r = axle_cornering_stiffness(tr, fz_r / 2)
    lf, lr, L, mass = veh.cg_to_front, veh.cg_to_rear, veh.wheelbase, veh.mass
    eg = (fz_f / c_f - fz_r / c_r) / G
    i = int(np.argmax(np.abs(a_lat)))
    ay, kap, v = float(a_lat[i]), float(w["kappa"][i]), float(w["v"][i])
    fyf, fyr = mass * ay * lr / L, mass * ay * lf / L
    alpha_f, alpha_r = fyf / c_f, fyr / c_r
    delta_ss = L * kap + eg * ay
    beta = lr * kap - mass * lf * v**2 * kap / (c_r * L) if v > 0 else 0.0
    mu = tires.mu
    util = math.hypot(ay, float(w["a"][i])) / (mu * G)
    steps.append(
        {
            "id": "vehicle_physics",
            "quantities": {
                "t": float(tt[i] - t0),
                "v": v,
                "kappa": kap,
                "a_y": ay,
                "F_yf": fyf,
                "F_yr": fyr,
                "alpha_f": alpha_f,
                "alpha_r": alpha_r,
                "delta": delta_ss,
                "beta": beta,
                "understeer_gradient": eg,
                "C_f": c_f,
                "C_r": c_r,
                "friction_utilization": util,
            },
            "formulas": [
                f"a_y = v^2 \\kappa = {_f(v)}^2 \\cdot {_f(kap)} = {_f(ay)}\\ \\mathrm{{m/s^2}}",
                f"F_{{y,v}} = m a_y \\frac{{l_h}}{{l}} = {_f(fyf)}\\ \\mathrm{{N}},\\quad "
                f"F_{{y,h}} = m a_y \\frac{{l_v}}{{l}} = {_f(fyr)}\\ \\mathrm{{N}}",
                f"\\alpha_v = \\frac{{F_{{y,v}}}}{{C_v}} = {_f(alpha_f)}\\ \\mathrm{{rad}},\\quad "
                f"\\alpha_h = \\frac{{F_{{y,h}}}}{{C_h}} = {_f(alpha_r)}\\ \\mathrm{{rad}}",
                f"\\delta = l\\kappa + EG\\,a_y = {_f(L)} \\cdot {_f(kap)} + {_f(eg)} \\cdot {_f(ay)} = "
                f"{_f(delta_ss)}\\ \\mathrm{{rad}}",
                f"\\beta = l_h\\kappa - \\frac{{m l_v v^2 \\kappa}}{{C_h l}} = {_f(beta)}\\ \\mathrm{{rad}}",
                f"\\frac{{\\sqrt{{a_x^2 + a_y^2}}}}{{\\mu g}} = {_f(util)}",
            ],
        }
    )

    # ------------------------------------------------------------------ candidates (for the plot)
    cand = []
    best = int(debug.best_index)
    show = list(range(min(len(status), 119)))
    if 0 <= best < len(status) and best not in show:
        show.append(best)  # the selected candidate is stored last in the debug snapshot
    for k in show:
        cand.append(
            {
                "x": [_num(v) for v in np.asarray(debug.candidates_x[k])[::3]],
                "y": [_num(v) for v in np.asarray(debug.candidates_y[k])[::3]],
                "s": [_num(v) for v in np.asarray(debug.candidates_s[k])[::3]],
                "d": [_num(v) for v in np.asarray(debug.candidates_d[k])[::3]],
                "status": int(status[k]),
                "cost": _num(debug.candidates_cost[k]),
                "selected": k == best,
            }
        )
    return {
        "steps": steps,
        "series": series,
        "candidates": cand,
        "weights": {
            "k_lat": cost.k_lat,
            "k_lon": cost.k_lon,
            "jerk": vars(cost.jerk),
            "terminal_time": vars(cost.terminal_time),
            "terminal_deviation": vars(cost.terminal_deviation),
        },
    }
