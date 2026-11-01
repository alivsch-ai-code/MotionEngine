"""Analysis views of the planner view: Frenet view, cost evaluation, restriction violations,
controller states and command scopes. All follow the timeline via set_time(t, snap)."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

from .data import rect
from .style import (BEST, CAT, FAIL, INVALID, MUTED, OBJECT, TEXT, WARN, brush, cat_color, cursor, fmt, make_plot,
                    pen, set_bars, sig)
from .topview import CandidateLayer

DEG = 180.0 / np.pi


def _grid(widgets, columns=2):
    w = QtWidgets.QWidget()
    g = QtWidgets.QGridLayout(w)
    g.setContentsMargins(2, 2, 2, 2)
    g.setSpacing(4)
    for i, item in enumerate(widgets):
        span = 2 if (len(widgets) % columns and i == len(widgets) - 1) else 1
        g.addWidget(item, i // columns, i % columns, 1, span)
    return w


def title_legend(entries):
    # compact legend in the title row: colored mark + label in secondary text color (never covers the data)
    return "&nbsp;&nbsp;".join(f"<span style='color:{c}'>{mark}</span>&nbsp;"
                               f"<span style='color:{MUTED};font-size:8pt'>{lbl}</span>" for c, mark, lbl in entries)


# ---------------------------------------------------------------------------- time scopes
class TimeScope:
    """One plot with one y-axis (one unit), several series, time cursor and optional event marks.
    series: [(signal key, label, scale)] -- colors follow the slot order of the series list."""

    def __init__(self, title, unit, series, colors=None):
        self.series = series
        colors = colors or [cat_color(i) for i in range(len(series))]
        if len(series) > 1:
            title = f"{title}&nbsp;&nbsp;" + title_legend([(c, "━", lbl) for c, (_, lbl, _) in zip(colors, series)])
        self.plot = make_plot(title, "", unit, xlabel="")
        self.curves = [self.plot.plot([], [], pen=pen(colors[i], 1.6), connect="finite")
                       for i in range(len(series))]
        self.cursor = cursor(self.plot)
        self.marks = []

    def set_result(self, result, events=()):
        t = sig(result, "t")
        for (key, _, scale), curve in zip(self.series, self.curves):
            y = sig(result, key)
            if t is None or y is None or len(y) != len(t):
                curve.setData([], [])
            else:
                curve.setData(t, y * scale)
        for m in self.marks:
            self.plot.removeItem(m)
        self.marks = []
        for e in events:
            line = pg.InfiniteLine(pos=e["t"], angle=90, pen=pen(WARN if e["type"] == "reinit" else FAIL, 1,
                                                                  QtCore.Qt.DotLine, 0.8))
            self.plot.addItem(line, ignoreBounds=True)
            self.marks.append(line)
        self.plot.getPlotItem().enableAutoRange()

    def set_time(self, t):
        self.cursor.setValue(t)


class ScopeGroup(QtWidgets.QWidget):
    def __init__(self, scopes, columns=2, parent=None):
        super().__init__(parent)
        self.scopes = scopes
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_grid([s.plot for s in scopes], columns))
        for s in scopes[1:]:
            s.plot.setXLink(scopes[0].plot)

    def set_result(self, result, events=()):
        for s in self.scopes:
            s.set_result(result, events)

    def set_time(self, t, snap=None):
        for s in self.scopes:
            s.set_time(t)


# ---------------------------------------------------------------------------- Frenet view
class FrenetView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.plot = make_plot("Frenet-Ansicht: Kandidaten d(s)", "d", "m", xlabel="s", xunit="m", legend=True)
        self.cands = CandidateLayer(self.plot)
        self.corridor = self.plot.plot([], [], pen=pen(TEXT, 1.0, QtCore.Qt.DashLine, 0.6), connect="finite",
                                       name="Korridor d_min / d_max")
        # obstacles do not take part in the auto range (the candidates define the view)
        self.obstacles = pg.PlotDataItem([], [], pen=pen(OBJECT, 1.4), connect="finite", name="Objekte")
        self.obstacle_pred = pg.PlotDataItem([], [], pen=pen(OBJECT, 0.9, alpha=0.35), connect="finite",
                                             name="Prädiktion")
        for it in (self.obstacles, self.obstacle_pred):
            self.plot.addItem(it, ignoreBounds=True)
        self.plot.getPlotItem().legend.setColumnCount(2)
        self.start = pg.ScatterPlotItem(size=9, symbol="o", brush=brush(BEST), pen=pen("#111111", 1))
        self.start.setZValue(20)
        self.plot.addItem(self.start)
        self.note = pg.TextItem("", color=MUTED, anchor=(0, 0))
        self.plot.addItem(self.note, ignoreBounds=True)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)

    def set_data(self, data):
        self.data = data

    def set_time(self, t, snap=None):
        self.cands.update(snap, "candidates_s", "candidates_d", ("s", "d"))
        traj = (snap or {}).get("trajectory") or {}
        s, d = traj.get("s"), traj.get("d")
        self.start.setData([float(s[0])], [float(d[0])]) if s is not None and d is not None and len(s) else \
            self.start.setData([], [])
        cs = (snap or {}).get("candidates_s")
        s_lo, s_hi = (float(np.nanmin(cs)), float(np.nanmax(cs))) if cs is not None and np.size(cs) else \
            ((float(np.min(s)), float(np.max(s))) if s is not None and len(s) else (0.0, 1.0))
        beh = (snap or {}).get("behavior") or {}
        lines = []
        for key in ("d_min", "d_max"):
            v = beh.get(key)
            if v is not None and np.isfinite(v) and abs(v) < 1e6:
                lines += [(s_lo, float(v)), (s_hi, float(v)), (np.nan, np.nan)]
        if lines:
            a = np.asarray(lines)
            self.corridor.setData(a[:, 0], a[:, 1])
        else:
            self.corridor.setData([], [])
        self._obstacles(t, snap)

    def _obstacles(self, t, snap):
        d = self.data
        ref = d.reference(snap) if d else None
        if ref is None:
            self.obstacles.setData([], [])
            self.obstacle_pred.setData([], [])
            self.note.setText("Keine Referenzlinie: Objekte nicht projiziert")
            return
        self.note.setText("")
        boxes, preds = [], []
        def box(s, dd, length, width):
            return [s - length / 2, s + length / 2, s + length / 2, s - length / 2, s - length / 2, np.nan], \
                   [dd - width / 2, dd - width / 2, dd + width / 2, dd + width / 2, dd - width / 2, np.nan]
        for oid in d.objects:
            o = d.object_state(oid, t)
            if o is None:
                continue
            (s,), (dd,) = ref.project([o["x"]], [o["y"]])
            boxes.append(box(s, dd, o["length"], o["width"]))
        for p in (snap or {}).get("prediction") or []:
            x, y = np.asarray(p.get("x", []), float), np.asarray(p.get("y", []), float)
            if len(x) and len(x) == len(y):
                ss, dd = ref.project(x, y)
                stride = max(int(np.ceil(len(x) / 10)), 1)
                for k in range(stride, len(x), stride):
                    preds.append(box(ss[k], dd[k], float(p.get("length", 4.5)), float(p.get("width", 1.8))))
        for item, group in ((self.obstacles, boxes), (self.obstacle_pred, preds)):
            if group:
                item.setData(np.concatenate([g[0] for g in group]), np.concatenate([g[1] for g in group]))
            else:
                item.setData([], [])


# ---------------------------------------------------------------------------- cost evaluation
class CostView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.terms = make_plot("Kostenterme der gewählten Trajektorie", "", "", xlabel="Kosten", xunit="")
        self.hist = make_plot("Kostenverteilung gültiger Kandidaten", "Anzahl", "", xlabel="Kosten", xunit="",
                              legend=True)
        self.hist_curve = self.hist.plot([], [], stepMode="center", fillLevel=0, brush=brush(CAT[0], 0.55),
                                         pen=pen(CAT[0], 1.2), name="Kandidaten")
        self.best_line = pg.InfiniteLine(angle=90, pen=pen(BEST, 2.0))
        self.hist.addItem(self.best_line, ignoreBounds=True)
        self.hist.plot([], [], pen=pen(BEST, 2.0), name="gewählt")
        self.mode_cost = make_plot("Modi-Vergleich: Kosten je Längsmodus", "Kosten", "", xlabel="")
        self.mode_jerk = make_plot("Modi-Vergleich: Anfangsruck je Längsmodus", "Ruck", "m/s³", xlabel="")
        self.mode_note = QtWidgets.QLabel("")
        self.mode_note.setStyleSheet(f"color: {MUTED}; padding: 2px;")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_grid([self.terms, self.hist, self.mode_cost, self.mode_jerk]), 1)
        layout.addWidget(self.mode_note)
        self._last = None

    def set_time(self, t, snap=None):
        if snap is self._last:
            return
        self._last = snap
        terms = {k: float(v) for k, v in ((snap or {}).get("cost_terms") or {}).items()
                 if isinstance(v, (int, float, np.floating, np.integer))}
        items = sorted(terms.items(), key=lambda kv: kv[1])
        set_bars(self.terms, [k for k, _ in items], [v for _, v in items], CAT[0], horizontal=True)
        cost = np.asarray((snap or {}).get("candidates_cost", []), float).ravel()
        status = np.asarray((snap or {}).get("candidates_status", []), int).ravel()
        if len(status) == len(cost):
            cost = cost[status == 0]
        cost = cost[np.isfinite(cost)]
        if len(cost) > 1:
            hi = np.percentile(cost, 98)
            y, x = np.histogram(np.clip(cost, None, hi), bins=min(30, max(len(cost) // 3, 5)))
            self.hist_curve.setData(x, y)
        else:
            self.hist_curve.setData([], [])
        best = ((snap or {}).get("trajectory_info") or {}).get("cost")
        bi = (snap or {}).get("best_index")
        if best is None and bi is not None and 0 <= int(bi) < np.size((snap or {}).get("candidates_cost", [])):
            best = float(np.asarray(snap["candidates_cost"]).ravel()[int(bi)])
        self.best_line.setVisible(bool(best is not None and np.isfinite(best)))
        if best is not None and np.isfinite(best):
            self.best_line.setValue(float(best))
        modes = (snap or {}).get("modes") or {}
        names = list(modes)
        selected = (snap or {}).get("mode") or ((snap or {}).get("trajectory_info") or {}).get("mode")
        hl = names.index(selected) if selected in names else None
        def col(key):
            return [float(modes[m].get(key, np.nan)) if isinstance(modes[m], dict) else np.nan for m in names]
        set_bars(self.mode_cost, names, col("cost"), highlight=hl)
        set_bars(self.mode_jerk, names, col("jerk0"), highlight=hl)
        if names:
            self.mode_note.setText(f"Gewählter Modus (Ablösestrategie): <b>{selected or '-'}</b>  "
                                   f"(blau hervorgehoben, übrige grau)")
        else:
            self.mode_note.setText("Keine Modusinformationen in diesem Zyklus")


# ---------------------------------------------------------------------------- restrictions
class ConstraintView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = make_plot("Verworfen je Restriktion (Zyklus)", "", "", xlabel="Anzahl", xunit="")
        self.share = make_plot("Anteil gültiger Kandidaten&nbsp;&nbsp;" + title_legend(
            [(CAT[0], "━", "gültig / geprüft"), (FAIL, "✖", "Fallback"), (WARN, "▲", "Reinitialisierung")]),
            "Anteil", "", xlabel="")
        self.share.setYRange(0, 1.05)
        self.share_curve = self.share.plot([], [], pen=pen(CAT[0], 1.6), connect="finite")
        self.fallback = pg.ScatterPlotItem(size=9, symbol="x", pen=pen(FAIL, 2), brush=brush(FAIL))
        self.reinit = pg.ScatterPlotItem(size=9, symbol="t", pen=None, brush=brush(WARN))
        for it in (self.fallback, self.reinit):
            self.share.addItem(it)
        self.cursor = cursor(self.share)
        self.count = make_plot("Kandidaten je Zyklus&nbsp;&nbsp;" + title_legend(
            [(CAT[0], "━", "erzeugt"), (CAT[1], "━", "geprüft"), (CAT[2], "━", "gültig")]), "Anzahl", "", xlabel="")
        self.count_total = self.count.plot([], [], pen=pen(CAT[0], 1.4), connect="finite")
        self.count_checked = self.count.plot([], [], pen=pen(CAT[1], 1.4), connect="finite")
        self.count_valid = self.count.plot([], [], pen=pen(CAT[2], 1.4), connect="finite")
        self.count.setXLink(self.share)
        self.count_cursor = cursor(self.count)
        self.reasons = QtWidgets.QLabel("")
        self.reasons.setWordWrap(True)
        self.reasons.setStyleSheet(f"color: {MUTED}; padding: 2px;")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        top = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        for w in (self.bars, self.share, self.count):
            top.addWidget(w)
        top.setSizes([200, 150, 150])
        layout.addWidget(top, 1)
        layout.addWidget(self.reasons)
        self._last = None

    def set_data(self, data):
        snaps = data.snapshots if data else []
        t = data.snap_t if data else np.zeros(0)
        n_valid = np.array([np.sum(np.asarray(s.get("candidates_status", []), int) == 0)
                            if np.size(s.get("candidates_status", [])) else np.nan for s in snaps], float)
        n_cand = np.array([s.get("n_candidates", np.size(s.get("candidates_status", []))) or np.nan for s in snaps],
                          float)
        n_check = np.array([s.get("n_checked", np.nan) for s in snaps], float)
        denom = np.where(np.isfinite(n_check) & (n_check > 0), n_check, n_cand)
        share = n_valid / np.where(denom > 0, denom, np.nan)
        self.share_curve.setData(t, share) if len(t) else self.share_curve.setData([], [])
        fb = np.array([bool(s.get("fallback")) for s in snaps], bool)
        ri = np.array([bool(s.get("reinitialized") or (s.get("trajectory_info") or {}).get("reinitialized"))
                       for s in snaps], bool)
        self.fallback.setData(t[fb], np.zeros(fb.sum()) + 0.02) if len(t) else self.fallback.setData([], [])
        self.reinit.setData(t[ri], np.zeros(ri.sum()) + 1.02) if len(t) else self.reinit.setData([], [])
        for item, y in ((self.count_total, n_cand), (self.count_checked, n_check), (self.count_valid, n_valid)):
            item.setData(t, y) if len(t) and np.any(np.isfinite(y)) else item.setData([], [])
        self._last = None

    def set_time(self, t, snap=None):
        self.cursor.setValue(t)
        self.count_cursor.setValue(t)
        if snap is self._last:
            return
        self._last = snap
        viol = {k: float(v) for k, v in ((snap or {}).get("constraint_violations") or {}).items()
                if isinstance(v, (int, float, np.integer, np.floating))}
        items = sorted(viol.items(), key=lambda kv: kv[1])
        set_bars(self.bars, [k for k, _ in items], [v for _, v in items], CAT[1], horizontal=True)
        status = np.asarray((snap or {}).get("candidates_status", []), int).ravel()
        if len(status):
            counts = {lbl: int(np.sum(status == k)) for k, lbl in ((0, "gültig"), (1, "Restriktion verletzt"),
                                                                   (2, "Kollision"), (3, "nicht geprüft"))}
            text = ", ".join(f"{k}: {v}" for k, v in counts.items())
            if (snap or {}).get("fallback"):
                text = f"<span style='color:{FAIL}'>✖ Fallback-Trajektorie</span>   " + text
            self.reasons.setText(f"Kandidatenstatus im Zyklus t = {snap.get('t', 0):.2f} s: {text}")
        else:
            self.reasons.setText("Keine Kandidaten in diesem Zyklus")


# ---------------------------------------------------------------------------- controller states
class ControllerView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.e_n = TimeScope("Querfehler e_n", "m", [("e_n", "e_n", 1.0)])
        self.e_t = TimeScope("Längsfehler e_t", "m", [("e_t", "e_t", 1.0)])
        self.e_theta = TimeScope("Kurswinkelfehler e_θ", "°", [("e_theta", "e_θ", DEG)])
        self.e_dot = TimeScope("Fehlerraten ė_n, ė_t", "m/s", [("e_n_dot", "ė_n", 1.0), ("e_t_dot", "ė_t", 1.0)])
        self.lam = TimeScope("Vorausschau λ", "m", [("lookahead", "λ", 1.0)])
        self.scopes = [self.e_n, self.e_t, self.e_theta, self.e_dot, self.lam]
        for s in self.scopes[1:]:
            s.plot.setXLink(self.e_n.plot)
        # active controller as a state band
        self.band = make_plot("Aktiver Regler", "", "", xlabel="")
        self.band.setXLink(self.e_n.plot)
        self.band.getPlotItem().hideAxis("left")
        self.band.setYRange(0, 1, padding=0.05)
        self.band.setMouseEnabled(y=False)
        self.band_cursor = cursor(self.band)
        self.band_items = []
        # phase plot e_t / e_n with the re-initialization threshold ellipse
        self.phase = make_plot("Fehlerebene e_t / e_n mit Reinit-Schwelle", "e_n", "m", xlabel="e_t", xunit="m",
                               legend=True)
        self.phase.setAspectLocked(False)
        self.phase_trail = self.phase.plot([], [], pen=pen(CAT[0], 1.2, alpha=0.7), name="Verlauf (2 s)")
        self.phase_now = pg.ScatterPlotItem(size=10, brush=brush(CAT[0]), pen=pen("#111111", 1))
        self.phase.addItem(self.phase_now)
        self.ellipse = self.phase.plot([], [], pen=pen(WARN, 1.4, QtCore.Qt.DashLine), name="Reinit-Schwelle")
        self.ell_box = QtWidgets.QCheckBox("Schwellwert-Ellipse")
        self.ell_box.setChecked(True)
        self.ell_et = QtWidgets.QDoubleSpinBox(decimals=2, minimum=0.01, maximum=50, value=0.5, suffix=" m")
        self.ell_en = QtWidgets.QDoubleSpinBox(decimals=2, minimum=0.01, maximum=50, value=0.3, suffix=" m")
        for w in (self.ell_box, self.ell_et, self.ell_en):
            (w.toggled if isinstance(w, QtWidgets.QCheckBox) else w.valueChanged).connect(self._update_ellipse)
        ctl = QtWidgets.QHBoxLayout()
        for w in (self.ell_box, QtWidgets.QLabel("e_t,max"), self.ell_et, QtWidgets.QLabel("e_n,max"), self.ell_en):
            ctl.addWidget(w)
        ctl.addStretch(1)
        phase_box = QtWidgets.QWidget()
        pl = QtWidgets.QVBoxLayout(phase_box)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(self.phase, 1)
        pl.addLayout(ctl)
        self.band.setMaximumHeight(110)
        left = _grid([s.plot for s in self.scopes] + [self.band], 2)
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(phase_box)
        split.setSizes([900, 380])
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(split)
        self.data = None

    def set_result(self, result, data=None, events=()):
        self.data = data
        reinits = [e for e in events if e.get("type") in ("reinit", "collision")]
        for s in self.scopes:
            s.set_result(result, reinits)
        for it in self.band_items:
            self.band.removeItem(it)
        self.band_items = []
        t, cid = sig(result, "t"), sig(result, "controller_id")
        if t is not None and cid is not None and len(cid) == len(t):
            names = (data.metadata.get("controllers") if data else None) or []
            ids = [int(v) for v in np.unique(cid[np.isfinite(cid)])]
            for k in sorted(set(ids) | set(range(len(names)))):
                mask = np.isfinite(cid) & (cid == k)
                if not mask.any() and k >= len(names):
                    continue
                label = names[k] if 0 <= k < len(names) else f"Regler {k}"
                edges = np.diff(np.r_[0, mask.astype(int), 0])
                starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0] - 1
                if not len(starts):
                    continue
                x0 = t[starts]
                w = t[np.minimum(ends + 1, len(t) - 1)] - x0
                bar = pg.BarGraphItem(x0=x0, y0=0.1, width=np.maximum(w, 1e-3), height=0.8,
                                      brush=brush(cat_color(k), 0.8), pen=pen(cat_color(k), 0.5))
                self.band.addItem(bar)
                self.band_items.append(bar)
                for a, b in zip(x0, w):   # direct labels inside the segments
                    txt = pg.TextItem(label, color=TEXT, anchor=(0, 0.5))
                    txt.setPos(a + 0.05, 0.5)
                    self.band.addItem(txt, ignoreBounds=True)
                    self.band_items.append(txt)
        thr = (data.metadata.get("reinit_thresholds") if data else None) or {}
        if "e_t" in thr:
            self.ell_et.setValue(float(thr["e_t"]))
        if "e_n" in thr:
            self.ell_en.setValue(float(thr["e_n"]))
        self._phase_src = (sig(result, "t"), sig(result, "e_t"), sig(result, "e_n"))
        self._update_ellipse()

    def _update_ellipse(self, *_):
        if self.ell_box.isChecked():
            a = np.linspace(0, 2 * np.pi, 80)
            self.ellipse.setData(self.ell_et.value() * np.cos(a), self.ell_en.value() * np.sin(a))
        else:
            self.ellipse.setData([], [])

    def set_time(self, t, snap=None):
        for s in self.scopes:
            s.set_time(t)
        self.band_cursor.setValue(t)
        tt, et, en = getattr(self, "_phase_src", (None, None, None))
        if tt is None or et is None or en is None:
            self.phase_trail.setData([], [])
            self.phase_now.setData([], [])
            return
        i1 = int(np.clip(np.searchsorted(tt, t + 1e-9, side="right") - 1, 0, len(tt) - 1))
        i0 = int(np.searchsorted(tt, t - 2.0))
        self.phase_trail.setData(et[i0:i1 + 1], en[i0:i1 + 1])
        self.phase_now.setData([et[i1]], [en[i1]])


# ---------------------------------------------------------------------------- commands
class CommandView(ScopeGroup):
    def __init__(self, parent=None):
        scopes = [
            TimeScope("Lenkwinkel", "°", [("cmd_steer_angle", "Soll (cmd_steer_angle)", DEG),
                                         ("act_steer", "Aktor (act_steer)", DEG), ("delta", "Ist δ", DEG)]),
            TimeScope("Lenkrate", "°/s", [("cmd_steer_rate", "Soll (cmd_steer_rate)", DEG),
                                         ("delta_rate", "Ist δ̇", DEG)]),
            TimeScope("Längsbeschleunigung", "m/s²", [("cmd_accel", "Soll (cmd_accel)", 1.0),
                                                    ("des_a", "Trajektorie a_soll", 1.0), ("ego_ax", "Ist a_x", 1.0)]),
            TimeScope("Längskraft", "N", [("cmd_force", "Soll (cmd_force)", 1.0)]),
            TimeScope("Geschwindigkeit", "km/h", [("ego_v", "Ist v", 3.6), ("des_v", "v_soll", 3.6),
                                                ("target_speed", "Zielgeschw. Verhalten", 3.6)]),
            TimeScope("Aktorik Antrieb / Bremse", "", [("act_drive", "Antrieb", 1.0), ("act_brake", "Bremse", 1.0)]),
        ]
        super().__init__(scopes, 2, parent)
