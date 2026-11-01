"""Synthetic ADResult / BatchResult data so the workbench can be developed and tested without the runner.

make_demo_result(): lane change around a slow truck on a two-lane road, then braking for a red light;
fan-shaped Werling candidates (lateral end offsets x end times x speed variants), cost terms, restrictions,
predictions, MPC horizon, re-initialization, fallback cycle, mode/maneuver/controller switches.
"""

from __future__ import annotations

import numpy as np

LANE_W = 3.5
EGO_DIMS = {"length": 4.8, "width": 1.85, "center_offset": 0.15, "wheelbase": 2.8, "cg_to_rear": 1.5}
CONTROLLERS = ["Hohe Geschwindigkeit", "Niedrige Geschwindigkeit", "Rückwärts"]
MODES = ["velocity", "following", "stopping"]
MANEUVERS = ["lane_keeping", "lane_change_left", "lane_change_right"]


def _smooth(u):
    u = np.clip(u, 0.0, 1.0)
    return u ** 3 * (10 - 15 * u + 6 * u ** 2)


def _quintic(d0, dd0, d1, T, tau):
    # quintic d(tau) from (d0, dd0, 0) to (d1, 0, 0) in time T, constant afterwards
    a0, a1 = d0, dd0
    h = d1 - d0
    a3 = (10 * h - 6 * dd0 * T) / T ** 3
    a4 = (-15 * h + 8 * dd0 * T) / T ** 4
    a5 = (6 * h - 3 * dd0 * T) / T ** 5
    tt = np.minimum(tau, T)
    d = a0 + a1 * tt + a3 * tt ** 3 + a4 * tt ** 4 + a5 * tt ** 5
    ddd = 6 * a3 + 24 * a4 * tt + 60 * a5 * tt ** 2
    acc = 6 * a3 * tt + 12 * a4 * tt ** 2 + 20 * a5 * tt ** 3
    return d, acc, ddd


def _road():
    xs = np.linspace(-50, 320, 75)
    def line(y):
        return [xs.tolist(), np.full_like(xs, y).tolist()]
    lanes = [
        {"id": "r", "center": line(0.0), "left": line(LANE_W / 2), "right": line(-LANE_W / 2), "type": "driving",
         "marking_left": "dashed", "marking_right": "solid"},
        {"id": "l", "center": line(LANE_W), "left": line(1.5 * LANE_W), "right": line(LANE_W / 2), "type": "driving",
         "marking_left": "solid", "marking_right": "dashed"},
    ]
    return {"lanes": lanes,
            "stop_lines": [{"x": 200.0, "y": LANE_W / 2, "theta": 0.0, "width": 2 * LANE_W}],
            "traffic_lights": [{"id": "TL1", "x": 201.0, "y": 1.5 * LANE_W + 1.0,
                                "states": [[0.0, "green"], [7.0, "yellow"], [8.0, "red"]]}],
            "parking": [{"x": 225.0, "y": -LANE_W / 2 - 1.5, "theta": 0.0, "length": 5.5, "width": 2.5},
                        {"x": 231.0, "y": -LANE_W / 2 - 1.5, "theta": 0.0, "length": 5.5, "width": 2.5}]}


def make_demo_result(duration=12.0, dt=0.01, plan_dt=0.1, seed=0):
    from ...ad.results import ADResult
    rng = np.random.default_rng(seed)
    t = np.round(np.arange(0.0, duration + 1e-9, dt), 6)
    n = len(t)

    # ego motion: lane change 1.5-5.5 s, braking for the red light from 8 s
    v = np.where(t < 8.0, 15.0, np.maximum(15.0 - 1.6 * (t - 8.0), 0.0))
    x = np.concatenate([[0.0], np.cumsum(0.5 * (v[1:] + v[:-1]) * dt)])
    y = LANE_W * _smooth((t - 1.5) / 4.0)
    dx, dy = np.gradient(x, dt), np.gradient(y, dt)
    psi = np.arctan2(dy, dx)
    r = np.gradient(psi, dt)
    ax = np.gradient(v, dt)
    ay = v * r
    kappa = np.where(v > 0.5, r / np.maximum(v, 0.5), 0.0)
    delta = np.arctan(EGO_DIMS["wheelbase"] * kappa)
    delta_rate = np.gradient(delta, dt)

    # tracking errors with a disturbance (-> re-initialization at 4 s)
    e_n = 0.04 * np.sin(1.3 * t) + 0.01 * rng.standard_normal(n) + 0.55 * np.exp(-((t - 3.95) / 0.12) ** 2)
    e_t = 0.08 * np.sin(0.7 * t + 0.4) + 0.02 * rng.standard_normal(n)
    e_theta = 0.01 * np.cos(1.1 * t) + 0.002 * rng.standard_normal(n)
    reinit_mask = (t >= 3.98) & (t < 4.0 + dt / 2)
    e_n[(t >= 4.0) & (t < 4.3)] *= 0.2
    nx, ny = -np.sin(psi), np.cos(psi)
    des_x = x + e_t * np.cos(psi) - e_n * nx
    des_y = y + e_t * np.sin(psi) - e_n * ny
    controller_id = np.where(v > 10.0, 0, 1).astype(float)
    mode_id = np.where(t < 8.0, 0, 2).astype(float)
    maneuver_id = np.where((t >= 1.5) & (t < 5.5), 1, 0).astype(float)
    target_speed = np.where(t < 8.0, 15.0, 0.0)
    m = 1600.0
    cmd_accel = ax + 0.4 * (-e_t) + 0.05 * rng.standard_normal(n)
    cmd_force = m * cmd_accel + 250.0
    cmd_steer_rate = delta_rate - 0.6 * e_n * 0.1
    cmd_steer_angle = np.full(n, np.nan)
    cmd_steer_angle[controller_id == 1] = (delta + 0.02 * e_n)[controller_id == 1]
    cmd_steer_rate[controller_id == 1] = np.nan
    act_drive = np.maximum(cmd_force, 0.0) * 0.32
    act_brake = np.maximum(-cmd_force, 0.0) * 0.32
    lookahead = np.clip(0.3 * v, 1.0, None)

    signals = {"t": t, "ego_x": x, "ego_y": y, "ego_psi": psi, "ego_vx": v, "ego_vy": 0.02 * ay,
               "ego_v": v, "ego_r": r, "ego_ax": ax, "ego_ay": ay, "delta": delta, "delta_rate": delta_rate,
               "des_x": des_x, "des_y": des_y, "des_theta": psi + e_theta, "des_kappa": kappa, "des_v": v - 0.05 * e_t,
               "des_a": ax, "cmd_steer_rate": cmd_steer_rate, "cmd_steer_angle": cmd_steer_angle,
               "cmd_force": cmd_force, "cmd_accel": cmd_accel, "act_steer": delta * 0.98, "act_drive": act_drive,
               "act_brake": act_brake, "e_t": e_t, "e_n": e_n, "e_theta": e_theta, "e_v": 0.05 * e_t,
               "e_t_dot": np.gradient(e_t, dt), "e_n_dot": np.gradient(e_n, dt), "lookahead": lookahead,
               "reinit_request": reinit_mask.astype(float), "controller_id": controller_id,
               "target_speed": target_speed, "maneuver_id": maneuver_id, "collision": np.zeros(n),
               "off_road": np.zeros(n)}

    # objects: slow truck in the ego lane, car in the left lane far ahead
    objs = {1: {"type": "truck", "length": 10.0, "width": 2.5, "x0": 55.0, "y": 0.0, "v": 6.0},
            2: {"type": "car", "length": 4.6, "width": 1.9, "x0": 120.0, "y": LANE_W, "v": 14.0}}
    objects = {}
    for oid, o in objs.items():
        ov = np.where(t < 8.0, o["v"], np.maximum(o["v"] - 1.5 * (t - 8.0), 0.0))
        ox = o["x0"] + np.concatenate([[0.0], np.cumsum(0.5 * (ov[1:] + ov[:-1]) * dt)])
        objects[oid] = {"type": o["type"], "length": o["length"], "width": o["width"], "t": t.tolist(),
                        "x": ox.tolist(), "y": np.full(n, o["y"]).tolist(), "psi": np.zeros(n).tolist(),
                        "v": ov.tolist(), "a": np.gradient(ov, dt).tolist()}

    # planner snapshots
    snaps, plan_cost, plan_valid, plan_reinit, plan_time, plan_t = [], [], [], [], [], []
    d_ends = np.linspace(-1.0, 1.25 * LANE_W, 9)
    T_ends = np.array([2.0, 3.0, 4.0, 5.0])
    horizon = 5.0
    tau = np.linspace(0.0, horizon, 26)
    for tp in np.arange(0.0, duration - horizon * 0 + 1e-9, plan_dt):
        i = min(int(round(tp / dt)), n - 1)
        s0, d0, dd0, v0 = x[i], y[i], dy[i], v[i]
        stopping = tp >= 8.0
        d_target = LANE_W if tp >= 1.5 else 0.0
        cx, cy, cs, cd, cost, status, reason, terms_all = [], [], [], [], [], [], [], []
        for vi, dv in enumerate((-1.0, 0.0, 1.0) if not stopping else (-1.6, -1.0, -0.5)):
            for T in T_ends:
                for de in d_ends:
                    d, acc_lat, jerk_lat = _quintic(d0, dd0, de, T, tau)
                    a_long = dv if stopping else dv * np.exp(-tau / 2)
                    vv = np.maximum(v0 + np.cumsum(np.r_[0, np.diff(tau)] * a_long), 0.0)
                    s = s0 + np.concatenate([[0.0], np.cumsum(0.5 * (vv[1:] + vv[:-1]) * np.diff(tau))])
                    terms = {"jerk_lat": 0.1 * float(np.sum(jerk_lat ** 2) * (tau[1] - tau[0])), "time": 0.6 * T,
                             "offset": 0.9 * (de - d_target) ** 2,
                             "velocity": 0.25 * float((vv[-1] - (0.0 if stopping else 15.0)) ** 2) / 10,
                             "jerk_long": 0.05 * dv ** 2 * 4}
                    st, rs = 0, ""
                    if de < -0.4 or de > LANE_W + 1.2:
                        st, rs = 1, "Korridor d_min/d_max"
                    elif np.max(np.abs(acc_lat)) > 3.0:
                        st, rs = 1, "Querbeschleunigung"
                    elif np.max(vv) > 16.5:
                        st, rs = 1, "Geschwindigkeit"
                    else:
                        tx = objects[1]
                        ox = np.interp(tp + tau, t, tx["x"])
                        if np.any((np.abs(s - ox) < 8.0) & (np.abs(d - 0.0) < 2.4)):
                            st, rs = 2, "Kollision Objekt 1"
                    cx.append(s); cy.append(d); cs.append(s); cd.append(d)
                    cost.append(sum(terms.values())); status.append(st); reason.append(rs); terms_all.append(terms)
        cost, status = np.asarray(cost), np.asarray(status, dtype=np.int8)
        fallback = abs(tp - 3.1) < 1e-6
        if fallback:
            status[status == 0] = 1
            for k in range(len(reason)):
                reason[k] = reason[k] or "Krümmung"
        n_checked = int(np.sum(status != 3))
        unchecked = rng.random(len(status)) < 0.15
        status[(status == 1) & unchecked] = 3
        valid = status == 0
        best = int(np.argmin(np.where(valid, cost, np.inf))) if valid.any() else int(np.argmin(cost))
        viol = {}
        for st, rs in zip(status, reason):
            if st in (1, 2) and rs:
                viol[rs] = viol.get(rs, 0) + 1
        bx, by = cx[best], cy[best]
        th = np.arctan2(np.gradient(by), np.gradient(bx))
        bv = np.gradient(bx, tau)
        traj = {"t": (tp + tau).astype(np.float32), "x": bx.astype(np.float32), "y": by.astype(np.float32),
                "theta": th.astype(np.float32), "kappa": np.gradient(th, tau).astype(np.float32) / np.maximum(bv, 0.5),
                "v": bv.astype(np.float32), "a": np.gradient(bv, tau).astype(np.float32),
                "s": cs[best].astype(np.float32), "d": cd[best].astype(np.float32)}
        modes = {mm: {"cost": float(np.min(cost) * (1.0 + 0.35 * k)) if mm != MODES[int(mode_id[i])] else float(cost[best]),
                      "jerk0": float(abs(1.2 - 0.5 * k + 0.2 * np.sin(tp))), "valid": bool(k != 1 or tp < 8)}
                 for k, mm in enumerate(MODES)}
        compute = 0.007 + 0.002 * rng.random() + (0.006 if fallback else 0.0)
        reinit = abs(tp - 4.0) < 1e-6
        pred = []
        for oid, rec in objects.items():
            px = np.interp(tp, t, rec["x"]) + np.interp(tp, t, rec["v"]) * np.arange(0.0, horizon + 1e-9, 0.5)
            pred.append({"id": oid, "t": (tp + np.arange(0.0, horizon + 1e-9, 0.5)).tolist(), "x": px.tolist(),
                         "y": np.full(len(px), rec["y"][0]).tolist(), "psi": np.zeros(len(px)).tolist(),
                         "length": rec["length"], "width": rec["width"]})
        hz = 20
        hor_x = (bx[:hz] + 0.05 * np.arange(hz) * np.sin(tp)).tolist()
        hor_y = (by[:hz] + 0.01 * np.arange(hz)).tolist()
        snaps.append({
            "t": float(tp), "start_state": {"x": float(s0), "y": float(d0), "v": float(v0)},
            "candidates_x": np.asarray(cx, dtype=np.float32), "candidates_y": np.asarray(cy, dtype=np.float32),
            "candidates_s": np.asarray(cs, dtype=np.float32), "candidates_d": np.asarray(cd, dtype=np.float32),
            "candidates_cost": cost.astype(np.float32), "candidates_status": status, "candidates_reason": reason,
            "best_index": best, "cost_terms": terms_all[best], "constraint_violations": viol,
            "n_candidates": len(cost), "n_checked": n_checked, "mode": MODES[int(mode_id[i])], "modes": modes,
            "reinitialized": reinit, "fallback": fallback, "compute_time": compute,
            "collision_circles": {"ego_radius": 1.25, "ego_offsets": [-1.35, 0.0, 1.35], "margin": 0.3,
                                  "ramp_time": 1.0},
            "info": {},
            "trajectory": traj,
            "trajectory_info": {"mode": MODES[int(mode_id[i])], "lateral_mode": "time", "reference_point": "cog",
                                "direction": 1, "cost": float(cost[best]), "valid": not fallback,
                                "reinitialized": reinit},
            "behavior": {"maneuver": MANEUVERS[int(maneuver_id[i])], "target_speed": float(target_speed[i]),
                         "modes": MODES, "lane_id": "r", "d_min": -0.4, "d_max": LANE_W + 1.2, "direction": 1,
                         "info": {}},
            "prediction": pred,
            "controller": {"horizon_x": hor_x if controller_id[i] == 0 else None,
                           "horizon_y": hor_y if controller_id[i] == 0 else None,
                           "active": CONTROLLERS[int(controller_id[i])], "lookahead": float(lookahead[i])},
        })
        plan_t.append(tp); plan_cost.append(float(cost[best])); plan_valid.append(0.0 if fallback else 1.0)
        plan_reinit.append(1.0 if reinit else 0.0); plan_time.append(compute)

    # planner signals held between cycles (zero-order hold at the executor rate)
    idx = np.clip(np.searchsorted(np.asarray(plan_t), t + 1e-9, side="right") - 1, 0, len(plan_t) - 1)
    signals.update(plan_cost=np.asarray(plan_cost)[idx], plan_valid=np.asarray(plan_valid)[idx],
                   plan_reinit=np.asarray(plan_reinit)[idx], plan_time=np.asarray(plan_time)[idx],
                   plan_mode_id=mode_id)

    res = ADResult(name="Demo: Spurwechsel mit Hindernis", scenario={"name": "demo_lane_change"},
                   stack={}, seed=seed)
    res._signals = signals
    res.objects = objects
    res.snapshots = snaps
    res.road = _road()
    res.events = [
        {"t": 1.5, "type": "maneuver", "maneuver": "lane_change_left"},
        {"t": 3.1, "type": "scenario_event", "name": "Fallback-Zyklus (Demo)"},
        {"t": 4.0, "type": "reinit", "reason": "e_n > Schwelle"},
        {"t": 5.5, "type": "maneuver", "maneuver": "lane_keeping"},
        {"t": 7.0, "type": "scenario_event", "name": "Ampel TL1 gelb"},
        {"t": 8.0, "type": "mode_switch", "mode": "stopping"},
        {"t": float(t[np.argmax(controller_id > 0)]), "type": "controller_switch", "controller": CONTROLLERS[1]},
    ]
    res.metadata = {"ego_dims": dict(EGO_DIMS), "controllers": CONTROLLERS, "modes": MODES, "maneuvers": MANEUVERS,
                    "stop_reason": "duration", "wall_time": 1.6, "reinit_thresholds": {"e_t": 0.5, "e_n": 0.3},
                    "demo": True}
    res.profile = {name: {"calls": int(c), "mean": m_, "p95": m_ * 1.6, "max": m_ * 3.0, "total": c * m_}
                   for name, c, m_ in (("world", 1200, 4e-5), ("perception", 1200, 3e-5), ("prediction", 1200, 6e-5),
                                       ("behavior", 120, 2e-4), ("planner", 120, 8.2e-3),
                                       ("controller", 1200, 1.4e-4), ("dynamics", 1200, 2e-5),
                                       ("actuators", 1200, 2e-5), ("plant", 1200, 9e-5))}
    res.provenance = {"generator": "vdsim.gui.ad.demo", "seed": seed}
    try:
        from ...research import evaluate
        evaluate(res)
    except Exception:  # metrics are optional for the demo
        res.kpis = {"collision": 0.0, "rms_e_n": float(np.sqrt(np.mean(e_n ** 2)))}
    return res


# ---------------------------------------------------------------------------- synthetic batch results
def make_demo_batch(kind="sweep", n=None, seed=0, save_dir=None):
    """kind: compare | sweep | monte_carlo | batch. With save_dir the first run is stored as ADResult."""
    from ...research import BatchResult
    rng = np.random.default_rng(seed)
    records = []

    def kpis(scale=1.0, bad=0.0):
        k = {"collision": float(rng.random() < 0.05 + bad), "off_road": 0.0,
             "min_distance": float(rng.uniform(1.5, 6) / scale), "min_ttc": float(rng.uniform(1.5, 5) / scale),
             "min_thw": float(rng.uniform(0.8, 2.5)), "max_drac": float(rng.uniform(0.5, 3) * scale),
             "max_ay": float(rng.uniform(1.5, 3.5) * scale), "max_ax": float(rng.uniform(0.5, 2)),
             "min_ax": float(-rng.uniform(1, 4) * scale), "rms_jerk_long": float(rng.uniform(0.2, 1.0) * scale),
             "rms_jerk_lat": float(rng.uniform(0.2, 1.2) * scale), "rms_e_n": float(rng.uniform(0.02, 0.12) * scale),
             "max_e_n": float(rng.uniform(0.1, 0.5) * scale), "rms_e_t": float(rng.uniform(0.03, 0.2) * scale),
             "max_e_t": float(rng.uniform(0.1, 0.6) * scale), "max_e_theta": float(rng.uniform(0.01, 0.06)),
             "reinit_count": float(rng.integers(0, 3)), "plan_time_mean": float(rng.uniform(5, 12)),
             "plan_time_p95": float(rng.uniform(10, 20)), "fallback_share": float(rng.uniform(0, 0.05)),
             "consistency_mean": float(rng.uniform(0.0, 0.05)), "mean_speed": float(rng.uniform(11, 15)),
             "distance": float(rng.uniform(140, 175)), "goal_reached": 1.0, "duration": 12.0}
        for term, w in (("jerk_lat", 1.2), ("time", 2.0), ("offset", 0.8), ("velocity", 1.5), ("jerk_long", 0.4)):
            k[f"cost_{term}"] = float(w * rng.uniform(0.6, 1.4) * scale)
        k["cost_mean"] = sum(v for kk, v in k.items() if kk.startswith("cost_"))
        return k

    def profile():
        return {node: {"calls": c, "mean": m_ * rng.uniform(0.8, 1.2), "p95": m_ * 1.7, "max": m_ * 3, "total": c * m_}
                for node, c, m_ in (("perception", 1200, 3e-5), ("prediction", 1200, 6e-5), ("behavior", 120, 2e-4),
                                    ("planner", 120, 8e-3), ("controller", 1200, 1.4e-4), ("plant", 1200, 9e-5))}

    base = {"scenario": "demo_lane_change", "stack": {}, "seed": seed, "duration": 12.0}
    if kind == "compare":
        for i, (label, sc) in enumerate((("Werling bi-level", 1.0), ("Stanley", 1.3), ("Pure Pursuit", 1.5),
                                          ("MPC", 0.9))):
            job = dict(base, label=label, stack={"controller": {"component": f"tracking_controller/demo{i}"}})
            records.append({"label": label, "job": job, "kpis": kpis(sc), "ok": True, "profile": profile(),
                            "wall_time": 1.5 * sc})
    elif kind == "sweep":
        ks, kd = [0.25, 0.5, 1.0, 2.0, 4.0], [0.5, 1.0, 2.0, 4.0]
        for a in ks:
            for b in kd:
                k = kpis(0.6 + 0.15 * np.log2(a / 0.25) + 0.05 * b)
                k["rms_jerk_lat"] = 1.4 / (1 + a) + 0.05 * b
                k["rms_e_n"] = 0.02 + 0.01 * a + 0.02 / b
                label = f"k_jerk={a:g}; k_d={b:g}".replace(".", ",")
                sweep = {"stack.planner.params.cost.k_jerk": a, "stack.planner.params.cost.k_d": b}
                records.append({"label": label, "job": dict(base, label=label, sweep=sweep), "kpis": k, "ok": True,
                                "profile": profile(), "wall_time": 1.4})
    elif kind == "monte_carlo":
        for i in range(n or 60):
            gap = float(rng.uniform(8, 30))
            spd = float(rng.normal(14, 1.5))
            k = kpis(1.0, bad=0.15 if gap < 11 else 0.0)
            k["min_ttc"] = max(0.3, 0.12 * gap + 0.2 * rng.standard_normal())
            k["min_distance"] = max(0.0, 0.25 * gap - 0.15 * spd + 0.3 * rng.standard_normal())
            label = f"MC {i + 1:03d}"
            sample = {"scenario_params.cut_in_gap": gap, "scenario_params.lead_speed": spd}
            records.append({"label": label, "job": dict(base, label=label, sample=sample), "kpis": k, "ok": True,
                            "profile": profile(), "wall_time": 1.3})
        records[-1] = {"label": "MC fehlerhaft", "job": dict(base, label="MC fehlerhaft"), "kpis": {}, "ok": False,
                       "error": "RuntimeError('Demo-Fehler')"}
    else:
        for i, sc in enumerate(("highway_cut_in", "urban_intersection", "parking", "lane_change")):
            label = sc
            records.append({"label": label, "job": dict(base, scenario=sc, label=label), "kpis": kpis(1 + 0.2 * i),
                            "ok": True, "profile": profile(), "wall_time": 1.1 + i})
    if save_dir is not None and records:
        from pathlib import Path
        res = make_demo_result()
        records[0]["path"] = str(res.save(Path(save_dir) / "demo_run"))
    return BatchResult(records)
