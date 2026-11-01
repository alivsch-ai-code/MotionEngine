"""Automatic KPI evaluation of simulation results.

General: driving dynamics (accelerations, yaw rate, side slip, roll, path deviation, friction
utilization), comfort (lateral jerk) and energy. Maneuver specific (taken from the trajectory
metadata): ISO 3888 cone hits, ISO 4138 understeer gradient, ISO 7401 step-steer response,
FMVSS 126 sine-with-dwell criteria, braking distance / MFDD, 0-100 km/h time, lap time,
frequency response, ACC/AEB gaps and LKA lane departure.
"""

from dataclasses import asdict, dataclass

import numpy as np

from ..core.conventions import G


@dataclass
class KPI:
    key: str
    label: str
    value: float
    unit: str = ""
    group: str = "Fahrdynamik"
    rating: str = ""  # "ok", "warn", "fail" or ""

    def formatted(self):
        if isinstance(self.value, str):
            return self.value
        if self.value is None or not np.isfinite(self.value):
            return "-"
        digits = 3 if abs(self.value) < 10 else 1
        return f"{self.value:.{digits}f}"

    def to_dict(self):
        return asdict(self)


def _first_crossing(t, signal, level):
    idx = np.where(signal >= level)[0]
    return float(t[idx[0]]) if len(idx) else float("nan")


def iso2631_weighted_rms(acc, fs):
    # Frequency-weighted RMS of vertical acceleration (ISO 2631-1, weighting Wk, band limit 0.4 Hz)
    from scipy.signal import bilinear, lfilter
    w = lambda f: 2 * np.pi * f
    w1, w3, w4, w5, w6 = w(0.4), w(12.5), w(12.5), w(2.37), w(3.35)
    q1, q4, q5, q6 = 1 / np.sqrt(2), 0.63, 0.91, 0.91
    num = np.polymul([1, 0, 0], np.polymul([1 / w3, 1], [w4**2]))
    num = np.polymul(num, [1, w5 / q5, w5**2])
    den = np.polymul([1, w1 / q1, w1**2], np.polymul([1, w4 / q4, w4**2], [1, w6 / q6, w6**2]))
    b, a = bilinear(num, den, fs)
    weighted = lfilter(b, a, acc - np.mean(acc))
    return float(np.sqrt(np.mean(weighted**2)))


def iso2631_rating(a_w):
    for limit, text in ((0.315, "nicht unkomfortabel"), (0.63, "etwas unkomfortabel"), (1.0, "ziemlich unkomfortabel"),
                        (1.6, "unkomfortabel"), (2.5, "sehr unkomfortabel")):
        if a_w < limit:
            return text
    return "extrem unkomfortabel"


class KPIEvaluator:
    def evaluate(self, result):
        self.r = result
        self.meta = result.metadata
        self.traj = self.meta.get("trajectory", {})
        self.tmeta = self.traj.get("metadata", {})
        kpis = self._general() + self._comfort() + self._energy()
        maneuver = self.tmeta.get("maneuver", "")
        specific = {"iso_double_lane_change": self._cone_test, "iso_obstacle_avoidance": self._cone_test,
                    "slalom": self._cone_test, "circle": self._understeer, "ramp_steer": self._understeer,
                    "step_steer": self._step_steer, "sine_with_dwell": self._sine_dwell,
                    "braking": self._braking, "acceleration": self._acceleration,
                    "race_track": self._lap, "frequency_sweep": self._frequency_response}
        if maneuver in specific:
            kpis += specific[maneuver]()
        if "lead_s" in result:
            kpis += self._following()
        if "lka_active" in result:
            kpis += self._lane_keeping()
        result.kpis = {k.key: k.to_dict() for k in kpis}
        return kpis

    # general
    def _general(self):
        r = self.r
        util = np.hypot(r["fx"], r["fy"]) / np.maximum(r["mu"] * r["fz"], 1.0)
        has_forces = np.any(np.abs(r["fy"]) > 0) or np.any(np.abs(r["fx"]) > 0)
        util_max = float(np.nanmax(util)) if has_forces else float("nan")  # kinematic model: no tire forces
        e = r["lateral_error"]
        open_loop = self.traj.get("steer_table") is not None
        kpis = [
            KPI("max_ay", "Max. Querbeschleunigung", float(np.max(np.abs(r["ay"]))), "m/s²"),
            KPI("max_ax", "Max. Längsbeschleunigung", float(np.max(r["ax"])), "m/s²"),
            KPI("min_ax", "Max. Verzögerung", float(-np.min(r["ax"])), "m/s²"),
            KPI("max_yaw_rate", "Max. Gierrate", float(np.degrees(np.max(np.abs(r["r"])))), "°/s"),
            KPI("max_beta", "Max. Schwimmwinkel", float(np.degrees(np.max(np.abs(r["beta"])))), "°",
                rating="warn" if np.degrees(np.max(np.abs(r["beta"]))) > 5 else "ok"),
            KPI("max_roll", "Max. Wankwinkel", float(np.degrees(np.max(np.abs(r["roll"])))), "°"),
            KPI("max_steer", "Max. Radlenkwinkel", float(np.degrees(np.max(np.abs(r["delta_f"])))), "°"),
        ]
        if not open_loop:
            kpis += [KPI("max_lateral_error", "Max. Bahnabweichung", float(np.max(np.abs(e))), "m",
                         group="Bahnführung", rating="warn" if np.max(np.abs(e)) > 0.5 else "ok"),
                     KPI("rms_lateral_error", "RMS Bahnabweichung", float(np.sqrt(np.mean(e**2))), "m",
                         group="Bahnführung")]
        kpis += [
            KPI("max_friction_utilization", "Max. Reibwertausnutzung", util_max, "-",
                rating="warn" if util_max > 0.95 else "ok"),
            KPI("stability_reserve", "Stabilitätsreserve (1 - Ausnutzung)", 1.0 - util_max, "-"),
            KPI("mean_speed", "Mittlere Geschwindigkeit", float(np.mean(r["speed"]) * 3.6), "km/h", group="Allgemein"),
            KPI("distance", "Fahrstrecke", float(np.sum(np.hypot(np.diff(r["x"]), np.diff(r["y"])))), "m",
                group="Allgemein"),
            KPI("duration", "Simulierte Zeit", float(r["t"][-1]), "s", group="Allgemein"),
        ]
        return kpis

    def _comfort(self):
        r = self.r
        t = r["t"]
        if len(t) < 3:
            return []
        dt = float(np.mean(np.diff(t)))
        window = max(int(round(0.1 / dt)), 1)  # 0.1 s moving average (~ 4 Hz low-pass) before differentiating
        ay_smooth = np.convolve(np.pad(r["ay"], window // 2, mode="edge"), np.ones(window) / window, mode="valid")
        jerk = np.gradient(ay_smooth[:len(t)], t)
        kpis = []
        if "body_az" in r and len(t) > 50:
            a_w = iso2631_weighted_rms(r["body_az"], 1.0 / dt)
            kpis += [KPI("iso2631_aw", "Bewertete Vertikalbeschl. a_w (ISO 2631)", a_w, "m/s²", "Komfort",
                         "ok" if a_w < 0.63 else "warn"),
                     KPI("iso2631_rating", "Komfortbewertung (ISO 2631)", iso2631_rating(a_w), "", "Komfort"),
                     KPI("max_pitch", "Max. Nickwinkel", float(np.degrees(np.max(np.abs(r["pitch"])))), "°", "Komfort")]
        return kpis + [KPI("rms_ay", "RMS Querbeschleunigung", float(np.sqrt(np.mean(r["ay"] ** 2))), "m/s²", "Komfort"),
                KPI("rms_lateral_jerk", "RMS Querruck", float(np.sqrt(np.mean(jerk**2))), "m/s³", "Komfort"),
                KPI("max_lateral_jerk", "Max. Querruck", float(np.max(np.abs(jerk))), "m/s³", "Komfort",
                    rating="warn" if np.max(np.abs(jerk)) > 5 else "ok")]

    def _energy(self):
        r = self.r
        e_drive = float(r["energy_drive"][-1]) / 3.6e6
        e_regen = float(r["energy_regen"][-1]) / 3.6e6
        dist = float(np.sum(np.hypot(np.diff(r["x"]), np.diff(r["y"]))))
        kpis = [KPI("energy_drive", "Energiebedarf (Antrieb)", e_drive, "kWh", "Energie"),
                KPI("energy_regen", "Rekuperierte Energie", e_regen, "kWh", "Energie")]
        if dist > 50:
            kpis.append(KPI("consumption", "Verbrauch", (e_drive - e_regen) / dist * 1e5, "kWh/100 km", "Energie"))
        return kpis

    # maneuver specific
    def _corners(self):
        p = self.meta.get("vehicle", {}).get("vehicle", {})
        length, width = p.get("length", 4.8), p.get("width", 1.85)
        r = self.r
        dx = np.array([1, 1, -1, -1]) * length / 2
        dy = np.array([1, -1, 1, -1]) * width / 2
        c, s = np.cos(r["psi"])[:, None], np.sin(r["psi"])[:, None]
        return r["x"][:, None] + dx * c - dy * s, r["y"][:, None] + dx * s + dy * c

    def _cone_test(self):
        r = self.r
        gates = self.tmeta.get("gates")
        cones = self.traj.get("cones", [])
        hits = 0
        cx, cy = self._corners()
        if gates:
            for x0, x1, center, width in gates:
                inside = (cx >= x0) & (cx <= x1)
                outside = np.abs(cy - center) > width / 2
                hits += int(np.any(inside & outside))
        elif cones:
            # cone inside the vehicle outline (rectangle) at any time
            p = self.meta.get("vehicle", {}).get("vehicle", {})
            half_l, half_w = p.get("length", 4.8) / 2, p.get("width", 1.85) / 2
            c, s = np.cos(r["psi"]), np.sin(r["psi"])
            for x_cone, y_cone in cones:
                dx, dy = x_cone - r["x"], y_cone - r["y"]
                lon, lat = dx * c + dy * s, -dx * s + dy * c
                hits += int(np.any((np.abs(lon) <= half_l) & (np.abs(lat) <= half_w + 0.05)))
        passed = hits == 0 and abs(np.degrees(np.max(np.abs(r["beta"])))) < 15
        return [KPI("cone_hits", "Gassenverletzungen", hits, "-", "Normtest", "ok" if hits == 0 else "fail"),
                KPI("test_passed", "Test bestanden", "ja" if passed else "nein", "", "Normtest",
                    "ok" if passed else "fail"),
                KPI("entry_speed", "Einfahrgeschwindigkeit", float(r["speed"][0] * 3.6), "km/h", "Normtest")]

    def _understeer(self):
        # ISO 4138: steering angle minus kinematic (Ackermann) angle vs lateral acceleration
        r = self.r
        L = self.meta.get("vehicle", {}).get("vehicle", {}).get("wheelbase", 2.8)
        v = np.maximum(r["speed"], 1.0)
        ackermann = L * r["r"] / v
        sel = (np.abs(r["ay"]) > 1.0) & (np.abs(r["ay"]) < 4.0)
        if sel.sum() < 20:
            return []
        slope, _ = np.polyfit(np.abs(r["ay"][sel]), np.abs(r["delta_f"][sel]) - np.abs(ackermann[sel]), 1)
        eg = np.degrees(slope)
        return [KPI("understeer_gradient", "Eigenlenkgradient", eg, "°/(m/s²)", "Normtest",
                    "ok" if eg > 0 else "warn"),
                KPI("understeer_gradient_g", "Eigenlenkgradient", eg * G, "°/g", "Normtest"),
                KPI("max_ay_steady", "Max. stationäre Querbeschleunigung", float(np.max(np.abs(r["ay"]))), "m/s²",
                    "Normtest")]

    def _step_steer(self):
        # ISO 7401 step steer: response time, peak response time, overshoot, steady-state gain
        r = self.r
        t, steer, yaw = r["t"], np.abs(r["delta_f"]), np.abs(r["r"])
        steer_ss = np.mean(steer[t > t[-1] - 1.0])
        yaw_ss = np.mean(yaw[t > t[-1] - 1.0])
        if steer_ss <= 0 or yaw_ss <= 0:
            return []
        t50 = _first_crossing(t, steer, 0.5 * steer_ss)
        t90 = _first_crossing(t, yaw, 0.9 * yaw_ss)
        i_peak = int(np.argmax(yaw))
        return [KPI("yaw_gain", "Stationäre Gierverstärkung", yaw_ss / steer_ss, "1/s", "Normtest"),
                KPI("ay_gain", "Stationäre Querbeschleunigungsverstärkung",
                    float(np.mean(np.abs(r["ay"])[t > t[-1] - 1.0]) / steer_ss), "m/s² / rad", "Normtest"),
                KPI("response_time", "Ansprechzeit Gierrate (90 %)", t90 - t50, "s", "Normtest"),
                KPI("peak_response_time", "Zeit bis Gierraten-Maximum", float(t[i_peak]) - t50, "s", "Normtest"),
                KPI("yaw_overshoot", "Überschwingen Gierrate", (yaw[i_peak] / yaw_ss - 1) * 100, "%", "Normtest")]

    def _sine_dwell(self):
        # FMVSS 126: yaw rate 1.0 s / 1.75 s after completion of steer <= 35 % / 20 % of the peak,
        # lateral displacement >= 1.83 m 1.07 s after the beginning of steer
        r = self.r
        t, steer, yaw = r["t"], r["delta_f"], r["r"]
        active = np.where(np.abs(steer) > 1e-4)[0]
        if len(active) == 0:
            return []
        t_bos, t_cos = t[active[0]], t[active[-1]]
        peak = np.max(np.abs(yaw[t <= t_cos + 0.1]))
        ratio_1 = abs(np.interp(t_cos + 1.0, t, yaw)) / peak * 100
        ratio_175 = abs(np.interp(t_cos + 1.75, t, yaw)) / peak * 100
        disp = abs(np.interp(t_bos + 1.07, t, r["y"]) - np.interp(t_bos, t, r["y"]))
        return [KPI("yaw_ratio_1s", "Gierrate 1,0 s nach Lenkende", ratio_1, "% vom Max.", "Normtest",
                    "ok" if ratio_1 <= 35 else "fail"),
                KPI("yaw_ratio_175s", "Gierrate 1,75 s nach Lenkende", ratio_175, "% vom Max.", "Normtest",
                    "ok" if ratio_175 <= 20 else "fail"),
                KPI("lateral_displacement", "Querversatz 1,07 s nach Lenkbeginn", disp, "m", "Normtest",
                    "ok" if disp >= 1.83 else "fail")]

    def _braking(self):
        r = self.r
        table = self.traj.get("accel_table")
        t_brake = table[0][1] if table else 0.0
        i0 = int(np.searchsorted(r["t"], t_brake))
        v = r["speed"]
        s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(r["x"]), np.diff(r["y"])))])
        v0 = v[i0]
        kpis = [KPI("stopping_distance", "Bremsweg", float(s[-1] - s[i0]), "m", "Bremsen"),
                KPI("brake_speed", "Bremsausgangsgeschwindigkeit", float(v0 * 3.6), "km/h", "Bremsen")]
        ib = i0 + int(np.argmax(v[i0:] <= 0.8 * v0))
        ie = i0 + int(np.argmax(v[i0:] <= 0.1 * v0))
        if ie > ib:
            mfdd = (v[ib] ** 2 - v[ie] ** 2) / (2 * (s[ie] - s[ib]))
            kpis.append(KPI("mfdd", "Mittlere Vollverzögerung (MFDD)", float(mfdd), "m/s²", "Bremsen"))
        kpis.append(KPI("max_yaw_deviation", "Max. Gierwinkelabweichung",
                        float(np.degrees(np.max(np.abs(r["heading_error"][i0:])))), "°", "Bremsen"))
        return kpis

    def _acceleration(self):
        r = self.r
        target = self.tmeta.get("target", 100 / 3.6)
        t_target = _first_crossing(r["t"], r["speed"], target - 0.1)
        return [KPI("time_to_target", f"Beschleunigung 0-{target * 3.6:.0f} km/h", t_target, "s", "Beschleunigen")]

    def _lap(self):
        return [KPI("lap_time", "Rundenzeit", float(self.r["t"][-1]), "s", "Rennstrecke")]

    def _frequency_response(self):
        # transfer function yaw rate / steering angle from the sweep (Welch cross-spectral estimate)
        from scipy.signal import csd, welch
        r = self.r
        t = r["t"]
        fs = 1.0 / float(np.mean(np.diff(t)))
        nperseg = min(len(t), int(fs * 10))
        f, p_xy = csd(r["delta_f"], r["r"], fs, nperseg=nperseg)
        _, p_xx = welch(r["delta_f"], fs, nperseg=nperseg)
        band = (f >= self.tmeta.get("f_start", 0.1)) & (f <= self.tmeta.get("f_end", 3.0))
        if band.sum() < 3:
            return []
        gain = np.abs(p_xy[band] / p_xx[band])
        i_peak = int(np.argmax(gain))
        f_band = f[band]
        i_1hz = int(np.argmin(np.abs(f_band - 1.0)))
        return [KPI("yaw_gain_low", f"Gierverstärkung bei {f_band[0]:.2f} Hz", float(gain[0]), "1/s", "Frequenzgang"),
                KPI("yaw_resonance", "Frequenz max. Gierverstärkung", float(f_band[i_peak]), "Hz", "Frequenzgang"),
                KPI("yaw_gain_peak_ratio", "Überhöhung Gierverstärkung", float(gain[i_peak] / gain[0]), "-", "Frequenzgang"),
                KPI("yaw_gain_1hz_ratio", "Gierverstärkung 1 Hz / stationär", float(gain[i_1hz] / gain[0]), "-",
                    "Frequenzgang")]

    def _following(self):
        r = self.r
        gap = r["lead_s"] - r["s"] - self.meta.get("vehicle", {}).get("vehicle", {}).get("length", 4.8) / 2
        time_gap = gap / np.maximum(r["speed"], 0.5)
        collision = bool(np.min(gap) <= 0)
        kpis = [KPI("min_gap", "Min. Abstand", float(np.min(gap)), "m", "Fahrerassistenz",
                    "fail" if collision else "ok"),
                KPI("min_time_gap", "Min. Zeitlücke", float(np.min(time_gap[r["speed"] > 2])) if np.any(r["speed"] > 2)
                    else float("nan"), "s", "Fahrerassistenz"),
                KPI("collision", "Kollision", "ja" if collision else "nein", "", "Fahrerassistenz",
                    "fail" if collision else "ok")]
        if "aeb_stage" in self.r:
            stage = np.nan_to_num(self.r["aeb_stage"])
            active = np.where(stage >= 2)[0]
            if len(active):
                kpis.append(KPI("aeb_trigger_ttc", "AEB-Auslösung bei TTC", float(self.r["ttc"][active[0]]), "s",
                                "Fahrerassistenz"))
        return kpis

    def _lane_keeping(self):
        r = self.r
        dist = r["distance_to_line"]
        departure = bool(np.nanmin(dist) < 0)
        return [KPI("min_distance_to_line", "Min. Abstand zur Fahrbahnmarkierung", float(np.nanmin(dist)), "m",
                    "Fahrerassistenz", "fail" if departure else "ok"),
                KPI("lane_departure", "Spurverlassen", "ja" if departure else "nein", "", "Fahrerassistenz",
                    "fail" if departure else "ok"),
                KPI("lka_active_time", "LKA-Eingriffsdauer", float(np.nansum(r["lka_active"]) * np.mean(np.diff(r["t"]))),
                    "s", "Fahrerassistenz")]


def evaluate(result):
    return KPIEvaluator().evaluate(result)


def compare(results):
    # KPI comparison table: {key: {"label", "unit", "values": [per result]}}
    table = {}
    for i, result in enumerate(results):
        kpis = result.kpis or {k.key: k.to_dict() for k in evaluate(result)}
        for key, kpi in kpis.items():
            row = table.setdefault(key, {"label": kpi["label"], "unit": kpi["unit"], "group": kpi["group"],
                                         "values": [None] * len(results)})
            row["values"][i] = kpi["value"]
    return table
