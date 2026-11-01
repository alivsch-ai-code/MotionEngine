"""Research metrics of an automated-driving run (ADResult -> KPI dict).

Groups:
    safety      collisions, minimum distance, TTC, time headway, DRAC, post-encroachment time
    comfort     accelerations, jerk, steering activity
    tracking    invariant tracking errors of the low-level stabilization, re-initializations
    planner     cycle time, fallback share, Bellman consistency between successive plans
    cost        average contribution of every cost term of the selected trajectories
    mission     progress, mean speed, goal reached
"""

from __future__ import annotations

import numpy as np

from ..framework.knowledge import trace

KPI_INFO = {
    # key: (label, unit, group, better)  better: "low" / "high" / ""
    "collision": ("Kollision", "-", "Sicherheit", "low"),
    "off_road": ("Fahrbahn verlassen", "-", "Sicherheit", "low"),
    "min_distance": ("Min. Abstand zu Objekten", "m", "Sicherheit", "high"),
    "min_ttc": ("Min. Time-to-Collision", "s", "Sicherheit", "high"),
    "min_thw": ("Min. Zeitlücke", "s", "Sicherheit", "high"),
    "max_drac": ("Max. DRAC", "m/s²", "Sicherheit", "low"),
    "min_pet": ("Min. Post-Encroachment-Time", "s", "Sicherheit", "high"),
    "max_ay": ("Max. Querbeschleunigung", "m/s²", "Komfort", "low"),
    "max_ax": ("Max. Längsbeschleunigung", "m/s²", "Komfort", "low"),
    "min_ax": ("Max. Verzögerung", "m/s²", "Komfort", "high"),
    "rms_jerk_long": ("RMS Längsruck", "m/s³", "Komfort", "low"),
    "rms_jerk_lat": ("RMS Querruck", "m/s³", "Komfort", "low"),
    "max_jerk": ("Max. Ruck", "m/s³", "Komfort", "low"),
    "rms_steer_rate": ("RMS Lenkrate", "rad/s", "Komfort", "low"),
    "rms_e_n": ("RMS Querfehler", "m", "Tracking", "low"),
    "max_e_n": ("Max. Querfehler", "m", "Tracking", "low"),
    "rms_e_t": ("RMS Längsfehler", "m", "Tracking", "low"),
    "max_e_t": ("Max. Längsfehler", "m", "Tracking", "low"),
    "max_e_theta": ("Max. Kurswinkelfehler", "rad", "Tracking", "low"),
    "reinit_count": ("Reinitialisierungen", "-", "Tracking", "low"),
    "plan_time_mean": ("Planungszeit Mittel", "ms", "Planer", "low"),
    "plan_time_p95": ("Planungszeit p95", "ms", "Planer", "low"),
    "plan_time_max": ("Planungszeit Max", "ms", "Planer", "low"),
    "fallback_share": ("Anteil Fallback-Trajektorien", "-", "Planer", "low"),
    "consistency_mean": ("Konsistenzabweichung Mittel", "m", "Planer", "low"),
    "consistency_max": ("Konsistenzabweichung Max", "m", "Planer", "low"),
    "candidates_mean": ("Kandidaten je Zyklus", "-", "Planer", ""),
    "cost_mean": ("Mittlere Trajektorienkosten", "-", "Kosten", "low"),
    "distance": ("Zurückgelegte Strecke", "m", "Mission", "high"),
    "mean_speed": ("Mittlere Geschwindigkeit", "m/s", "Mission", "high"),
    "final_speed": ("Endgeschwindigkeit", "m/s", "Mission", ""),
    "goal_reached": ("Ziel erreicht", "-", "Mission", "high"),
    "duration": ("Simulierte Dauer", "s", "Mission", ""),
    "real_time_factor": ("Echtzeitfaktor", "-", "Laufzeit", "high"),
}


def _sig(result, key, default=None):
    s = result.signals
    if key in s:
        return np.asarray(s[key], dtype=float)
    return default


def _rect_corners(x, y, psi, length, width):
    c, s = np.cos(psi), np.sin(psi)
    hl, hw = length / 2, width / 2
    dx = np.array([hl, hl, -hl, -hl])
    dy = np.array([hw, -hw, -hw, hw])
    return np.stack([x[..., None] + c[..., None] * dx - s[..., None] * dy,
                     y[..., None] + s[..., None] * dx + c[..., None] * dy], axis=-1)   # (..., 4, 2)


def _point_segment_dist(p, a, b):
    ab = b - a
    t = np.clip(np.sum((p - a) * ab, axis=-1) / np.maximum(np.sum(ab * ab, axis=-1), 1e-12), 0, 1)
    proj = a + t[..., None] * ab
    return np.linalg.norm(p - proj, axis=-1)


def _overlap(ca, cb):
    # separating axis test for two convex quadrilaterals per time step, arrays (n, 4, 2)
    sep = np.zeros(ca.shape[0], dtype=bool)
    for poly in (ca, cb):
        for i in range(4):
            edge = poly[:, (i + 1) % 4] - poly[:, i]
            axis = np.stack([-edge[:, 1], edge[:, 0]], axis=-1)
            pa = np.einsum("nkd,nd->nk", ca, axis)
            pb = np.einsum("nkd,nd->nk", cb, axis)
            sep |= (pa.max(1) < pb.min(1)) | (pb.max(1) < pa.min(1))
    return ~sep


@trace("ericson2004", section="4.4", concept="rectangle_distance", note="Abstand orientierter Rechtecke (SAT + Kantenabstände)")
def rectangle_distance(ca, cb):
    # minimum distance between rectangles (0 if they overlap), arrays (n, 4, 2)
    d = np.full(ca.shape[0], np.inf)
    for i in range(4):
        a1, b1 = ca[:, i], ca[:, (i + 1) % 4]
        a2, b2 = cb[:, i], cb[:, (i + 1) % 4]
        for k in range(4):
            d = np.minimum(d, _point_segment_dist(cb[:, k], a1, b1))
            d = np.minimum(d, _point_segment_dist(ca[:, k], a2, b2))
    d[_overlap(ca, cb)] = 0.0
    return d


def _ego_geometry(result):
    dims = result.metadata.get("ego_dims", {})
    return dims.get("length", 4.8), dims.get("width", 1.85), dims.get("center_offset", 0.15)


def _object_on_ego_time(result, rec, t):
    # interpolate an object's history on the ego time base; NaN where the object did not exist
    ot = np.asarray(rec["t"], dtype=float)
    out = {}
    valid = (t >= ot[0] - 1e-9) & (t <= ot[-1] + 1e-9) if len(ot) else np.zeros_like(t, dtype=bool)
    for k in ("x", "y", "psi", "v"):
        arr = np.asarray(rec[k], dtype=float)
        if k == "psi":
            arr = np.unwrap(arr)
        out[k] = np.where(valid, np.interp(t, ot, arr) if len(ot) else np.nan, np.nan)
    return out, valid


@trace("vogel2003", concept="surrogate_safety_measures",
       note="TTC, Zeitlücke, DRAC und PET als Surrogate Safety Measures")
def safety_metrics(result):
    t = result.t
    out = {"collision": float(np.nanmax(_sig(result, "collision", np.zeros(1)))) if len(t) else 0.0,
           "off_road": float(np.nanmax(_sig(result, "off_road", np.zeros(1)))) if len(t) else 0.0}
    if len(t) < 2 or not result.objects:
        out.update(min_distance=np.nan, min_ttc=np.nan, min_thw=np.nan, max_drac=0.0, min_pet=np.nan)
        return out
    L, W, off = _ego_geometry(result)
    ex, ey, epsi = _sig(result, "ego_x"), _sig(result, "ego_y"), _sig(result, "ego_psi")
    ev = _sig(result, "ego_vx")
    cx, cy = ex + off * np.cos(epsi), ey + off * np.sin(epsi)
    ego_c = _rect_corners(cx, cy, epsi, L, W)
    min_d, ttc_min, thw_min, drac_max = np.inf, np.inf, np.inf, 0.0
    for rec in result.objects.values():
        o, valid = _object_on_ego_time(result, rec, t)
        if not np.any(valid):
            continue
        idx = np.where(valid)[0]
        oc = _rect_corners(o["x"][idx], o["y"][idx], o["psi"][idx], rec["length"], rec["width"])
        d = rectangle_distance(ego_c[idx], oc)
        min_d = min(min_d, float(d.min()))
        # longitudinal conflict: object ahead inside the ego's swept corridor
        c, s = np.cos(epsi[idx]), np.sin(epsi[idx])
        rx, ry = o["x"][idx] - cx[idx], o["y"][idx] - cy[idx]
        x_rel, y_rel = c * rx + s * ry, -s * rx + c * ry
        ahead = (x_rel > 0) & (np.abs(y_rel) < (W + rec["width"]) / 2 + 0.3)
        if np.any(ahead):
            gap = x_rel - L / 2 - rec["length"] / 2
            v_obj_long = o["v"][idx] * np.cos(o["psi"][idx] - epsi[idx])
            closing = ev[idx] - v_obj_long
            m = ahead & (gap > 0)
            if np.any(m & (closing > 0.1)):
                mm = m & (closing > 0.1)
                ttc_min = min(ttc_min, float(np.min(gap[mm] / closing[mm])))
                drac_max = max(drac_max, float(np.max(closing[mm] ** 2 / (2 * gap[mm]))))
            if np.any(m & (ev[idx] > 1.0)):
                mm = m & (ev[idx] > 1.0)
                thw_min = min(thw_min, float(np.min(gap[mm] / ev[idx][mm])))
    out.update(min_distance=min_d if np.isfinite(min_d) else np.nan,
               min_ttc=ttc_min if np.isfinite(ttc_min) else np.nan,
               min_thw=thw_min if np.isfinite(thw_min) else np.nan, max_drac=drac_max,
               min_pet=post_encroachment_time(result))
    return out


def post_encroachment_time(result, dt=0.2):
    # smallest time difference between ego and an object occupying the same location (crossing paths)
    t = result.t
    if len(t) < 2:
        return np.nan
    L, W, off = _ego_geometry(result)
    step = max(int(round(dt / max(t[1] - t[0], 1e-6))), 1)
    ti = t[::step]
    ex, ey, epsi = _sig(result, "ego_x")[::step], _sig(result, "ego_y")[::step], _sig(result, "ego_psi")[::step]
    pet = np.inf
    for rec in result.objects.values():
        ot = np.asarray(rec["t"], dtype=float)
        if len(ot) < 2 or rec["type"] == "static":
            continue
        ostep = max(int(round(dt / max(ot[1] - ot[0], 1e-6))), 1)
        ox, oy, otm = np.asarray(rec["x"])[::ostep], np.asarray(rec["y"])[::ostep], ot[::ostep]
        dist = np.hypot(ex[:, None] - ox[None, :], ey[:, None] - oy[None, :])
        thr = 0.5 * (W + rec["width"])
        close = dist < thr
        if not np.any(close):
            continue
        dtm = np.abs(ti[:, None] - otm[None, :])
        pet = min(pet, float(dtm[close].min()))
    return pet if np.isfinite(pet) else np.nan


def _jerk(sig, t, smooth=0.1):
    if sig is None or len(sig) < 5:
        return np.zeros(0)
    dt = max(float(np.median(np.diff(t))), 1e-6)
    n = max(int(round(smooth / dt)), 1)
    kernel = np.ones(n) / n
    sm = np.convolve(sig, kernel, mode="same")
    return np.gradient(sm, dt)


def comfort_metrics(result):
    t = result.t
    ax, ay = _sig(result, "ego_ax"), _sig(result, "ego_ay")
    out = {}
    if ax is None or len(t) < 3:
        return out
    jx, jy = _jerk(ax, t), _jerk(ay, t)
    out.update(max_ay=float(np.max(np.abs(ay))), max_ax=float(np.max(ax)), min_ax=float(np.min(ax)),
               rms_jerk_long=float(np.sqrt(np.mean(jx ** 2))), rms_jerk_lat=float(np.sqrt(np.mean(jy ** 2))),
               max_jerk=float(np.max(np.hypot(jx, jy))))
    rate = _sig(result, "delta_rate")
    if rate is not None:
        out["rms_steer_rate"] = float(np.sqrt(np.mean(rate ** 2)))
    return out


def tracking_metrics(result):
    out = {}
    for key, name in (("e_n", "e_n"), ("e_t", "e_t")):
        e = _sig(result, key)
        if e is not None and len(e):
            e = e[np.isfinite(e)]
            if len(e):
                out[f"rms_{name}"] = float(np.sqrt(np.mean(e ** 2)))
                out[f"max_{name}"] = float(np.max(np.abs(e)))
    e = _sig(result, "e_theta")
    if e is not None and len(e):
        out["max_e_theta"] = float(np.nanmax(np.abs(e)))
    out["reinit_count"] = float(len(result.events_of("reinit")))
    return out


def planner_metrics(result):
    snaps = result.snapshots
    out = {}
    if not snaps:
        return out
    times = np.array([s.get("compute_time", np.nan) for s in snaps], dtype=float) * 1e3
    times = times[np.isfinite(times)]
    if len(times):
        out.update(plan_time_mean=float(times.mean()), plan_time_p95=float(np.percentile(times, 95)),
                   plan_time_max=float(times.max()))
    out["fallback_share"] = float(np.mean([bool(s.get("fallback", False)) for s in snaps]))
    out["candidates_mean"] = float(np.mean([s.get("n_candidates", 0) for s in snaps]))
    dev = consistency_deviation(result)
    if len(dev):
        out.update(consistency_mean=float(np.mean(dev)), consistency_max=float(np.max(dev)))
    costs = [s.get("trajectory_info", {}).get("cost") for s in snaps]
    costs = [c for c in costs if c is not None and np.isfinite(c)]
    if costs:
        out["cost_mean"] = float(np.mean(costs))
    return out


@trace("werling2011", section="3.2", concept="bellman_principle",
       note="Messung der zeitlichen Konsistenz: Abweichung neuer Plan vs. Rest des alten Plans")
def consistency_deviation(result, horizon=2.0):
    # Bellman check: max position difference between plan k and the remainder of plan k-1 on the
    # overlapping time interval (cycles with re-initialization are excluded)
    devs = []
    prev = None
    for snap in result.snapshots:
        traj = snap.get("trajectory")
        if traj is None:
            prev = None
            continue
        info = snap.get("trajectory_info", {})
        if prev is not None and not info.get("reinitialized") and not snap.get("reinitialized"):
            t0 = float(traj["t"][0])
            tt = traj["t"][(traj["t"] >= t0) & (traj["t"] <= t0 + horizon)]
            pt = prev["t"]
            tt = tt[(tt >= pt[0]) & (tt <= pt[-1])]
            if len(tt) > 1:
                dx = np.interp(tt, traj["t"], traj["x"]) - np.interp(tt, pt, prev["x"])
                dy = np.interp(tt, traj["t"], traj["y"]) - np.interp(tt, pt, prev["y"])
                devs.append(float(np.max(np.hypot(dx, dy))))
        prev = traj
    return np.asarray(devs)


def cost_analysis(result):
    # average contribution of every cost term of the selected trajectories + time series
    series = {}
    times = []
    for snap in result.snapshots:
        terms = snap.get("cost_terms") or {}
        if not terms:
            continue
        times.append(snap.get("t", np.nan))
        for k, v in terms.items():
            try:
                series.setdefault(k, []).append(float(v))
            except (TypeError, ValueError):
                continue
    n = len(times)
    series = {k: v for k, v in series.items() if len(v) == n}
    means = {k: float(np.mean(v)) for k, v in series.items()}
    total = sum(abs(v) for v in means.values()) or 1.0
    shares = {k: abs(v) / total for k, v in means.items()}
    return {"t": np.asarray(times), "series": {k: np.asarray(v) for k, v in series.items()},
            "mean": means, "share": shares}


def mission_metrics(result):
    t = result.t
    v = _sig(result, "ego_v")
    out = {"duration": result.duration}
    if v is not None and len(t) > 1:
        out["distance"] = float(np.trapezoid(np.abs(v), t)) if hasattr(np, "trapezoid") else float(np.trapz(np.abs(v), t))
        out["mean_speed"] = float(np.mean(np.abs(v)))
        out["final_speed"] = float(v[-1])
    out["goal_reached"] = float(bool(result.events_of("goal_reached")))
    wall = result.metadata.get("wall_time")
    if wall:
        out["real_time_factor"] = result.duration / wall
    return out


def evaluate(result):
    # all KPI groups -> flat dict (stored in result.kpis)
    kpis = {}
    for fn in (safety_metrics, comfort_metrics, tracking_metrics, planner_metrics, mission_metrics):
        try:
            kpis.update(fn(result))
        except Exception as exc:  # metrics must never break a run
            kpis[f"error_{fn.__name__}"] = str(exc)
    costs = cost_analysis(result)
    for k, v in costs["mean"].items():
        kpis[f"cost_{k}"] = v
    result.kpis = kpis
    return kpis


def kpi_label(key):
    if key in KPI_INFO:
        return KPI_INFO[key][0], KPI_INFO[key][1]
    if key.startswith("cost_"):
        return f"Kostenterm {key[5:]}", "-"
    return key, ""
