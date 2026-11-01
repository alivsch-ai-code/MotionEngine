"""Bird's-eye view of a planning cycle: lanes, reference path, cost-colored candidates, selected trajectory,
collision circles, objects with faded predicted outlines, vehicle envelope, ego pose, desired position,
MPC horizon, stop lines, traffic lights, parking spaces. Camera follow, layer toggles and legend."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from .data import circle, join, object_circles, rect
from .style import (
    ACCENT_REF,
    BEST,
    COST_RAMP,
    DESIRED,
    EGO,
    INVALID,
    LANE,
    LIGHT_COLORS,
    MUTED,
    OBJECT,
    TEXT,
    brush,
    cat_color,
    make_plot,
    pen,
)

LAYERS = [("lanes", "Fahrspuren"), ("reference", "Referenzpfad"), ("infra", "Haltelinien, Ampeln, Parkplätze"),
          ("candidates", "Kandidaten"), ("best", "Gewählte Trajektorie"), ("envelope", "Fahrzeug-Envelope"),
          ("circles", "Kollisionskreise"), ("objects", "Objekte"), ("prediction", "Prädiktion"), ("ego", "Ego"),
          ("trace", "Gefahrene Spur"), ("desired", "Sollposition"), ("mpc", "MPC-Horizont")]
ENVELOPE_DT = 0.5
OBJECT_RANGE = 90.0


def classify_candidates(snap, n_bins=len(COST_RAMP)):
    # candidate indices per cost bin (valid), invalid groups and the selected index
    status = np.asarray((snap or {}).get("candidates_status", []), dtype=int).ravel()
    cost = np.asarray((snap or {}).get("candidates_cost", []), dtype=float).ravel()
    n = len(status) if len(status) else len(cost)
    if len(status) != n:
        status = np.zeros(n, dtype=int)
    if len(cost) != n:
        cost = np.zeros(n)
    best = (snap or {}).get("best_index", -1)
    best = int(best) if best is not None and 0 <= int(best) < n else None
    valid = np.where(status == 0)[0]
    bins = [np.zeros(0, dtype=int)] * n_bins
    if len(valid):
        c = cost[valid]
        finite = np.isfinite(c)
        lo = float(np.min(c[finite])) if finite.any() else 0.0
        hi = float(np.percentile(c[finite], 90)) if finite.any() else 1.0
        norm = np.clip((np.where(finite, c, hi) - lo) / max(hi - lo, 1e-12), 0, 1)
        b = np.round(norm * (n_bins - 1)).astype(int)
        bins = [valid[b == k] for k in range(n_bins)]
    return {"bins": bins, "constraint": np.where(status == 1)[0], "collision": np.where(status == 2)[0],
            "unchecked": np.where(status == 3)[0], "best": best, "n": n}


def candidate_lines(xs, ys, idx):
    if xs is None or ys is None or not len(idx):
        return np.zeros(0), np.zeros(0)
    xs, ys = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
    if xs.ndim != 2 or xs.shape != ys.shape:
        return np.zeros(0), np.zeros(0)
    idx = idx[idx < len(xs)]
    sx = np.column_stack([xs[idx], np.full(len(idx), np.nan)]).ravel()
    sy = np.column_stack([ys[idx], np.full(len(idx), np.nan)]).ravel()
    return sx, sy


class CandidateLayer:
    # one PlotDataItem per cost bin + invalid groups + selected trajectory, shared by top and Frenet view
    def __init__(self, plot, legend=True):
        self.plot = plot
        self.bins = []
        for k, color in enumerate(COST_RAMP):
            name = "Kandidaten (nach Kosten)" if (legend and k == len(COST_RAMP) // 2) else None
            item = plot.plot([], [], pen=pen(color, 1.0, alpha=0.85), connect="finite", name=name)
            item.setZValue(3)
            self.bins.append(item)
        self.constraint = plot.plot([], [], pen=pen(INVALID, 1.0, alpha=0.55), connect="finite",
                                    name="ungültig (Restriktion)" if legend else None)
        self.collision = plot.plot([], [], pen=pen(INVALID, 1.0, QtCore.Qt.DashLine, 0.7), connect="finite",
                                   name="ungültig (Kollision)" if legend else None)
        self.unchecked = plot.plot([], [], pen=pen(INVALID, 0.8, QtCore.Qt.DotLine, 0.35), connect="finite")
        for it in (self.constraint, self.collision, self.unchecked):
            it.setZValue(2)
        self.best = plot.plot([], [], pen=pen(BEST, 3.2), name="Gewählte Trajektorie" if legend else None)
        self.best.setZValue(6)

    @property
    def items(self):
        return self.bins + [self.constraint, self.collision, self.unchecked]

    def update(self, snap, xkey, ykey, traj_keys=None):
        xs, ys = (snap or {}).get(xkey), (snap or {}).get(ykey)
        groups = classify_candidates(snap)
        for item, idx in zip(self.bins, groups["bins"]):
            item.setData(*candidate_lines(xs, ys, idx))
        self.constraint.setData(*candidate_lines(xs, ys, groups["constraint"]))
        self.collision.setData(*candidate_lines(xs, ys, groups["collision"]))
        self.unchecked.setData(*candidate_lines(xs, ys, groups["unchecked"]))
        traj = (snap or {}).get("trajectory") or {}
        if traj_keys and traj.get(traj_keys[0]) is not None and traj.get(traj_keys[1]) is not None:
            self.best.setData(np.asarray(traj[traj_keys[0]], dtype=float), np.asarray(traj[traj_keys[1]], dtype=float))
        elif groups["best"] is not None and xs is not None and ys is not None and np.ndim(xs) == 2:
            self.best.setData(np.asarray(xs[groups["best"]], dtype=float), np.asarray(ys[groups["best"]], dtype=float))
        else:
            self.best.setData([], [])
        return groups


def _path_item(color, alpha, z):
    item = QtWidgets.QGraphicsPathItem()
    item.setBrush(brush(color, alpha))
    item.setPen(pen(color, 1.2))
    item.setZValue(z)
    return item


def _polygon_path(polys):
    path = QtGui.QPainterPath()
    for px, py in polys:
        poly = QtGui.QPolygonF([QtCore.QPointF(float(a), float(b)) for a, b in zip(px, py)])
        path.addPolygon(poly)
        path.closeSubpath()
    return path


class TopView(QtWidgets.QWidget):
    candidate_clicked = QtCore.Signal(int, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.follow = True
        self._last_snap = None
        self.items = {k: [] for k, _ in LAYERS}
        self.layer_visible = {k: True for k, _ in LAYERS}
        self.plot = make_plot("", "y", "m", xlabel="x", xunit="m", legend=True)
        self.plot.setAspectLocked(True)
        self.legend = self.plot.getPlotItem().legend
        self.legend.setColumnCount(2)
        self._build_items()
        self._build_controls()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.controls)
        layout.addWidget(self.plot, 1)
        self._info_label = QtWidgets.QLabel()
        self._info_label.setStyleSheet("background: rgba(30,30,30,210); color: #e0e0e0; padding: 6px;"
                                       " font-family: monospace; font-size: 11px; border-radius: 4px;")
        self._info_label.setWordWrap(True)
        self._info_label.hide()
        layout.addWidget(self._info_label)
        self.plot.scene().sigMouseClicked.connect(self._on_click)

    # ------------------------------------------------------------------ construction
    def _add(self, layer, item, z=0):
        item.setZValue(z)
        if not isinstance(item, pg.PlotDataItem) or item not in self.plot.getPlotItem().items:
            self.plot.addItem(item)
        self.items[layer].append(item)
        return item

    def _build_items(self):
        p = self.plot
        self.lane_solid = self._add("lanes", p.plot([], [], pen=pen(LANE, 1.6), connect="finite",
                                                    name="Fahrbahnmarkierung"), 0)
        self.lane_dashed = self._add("lanes", p.plot([], [], pen=pen(LANE, 1.3, QtCore.Qt.DashLine),
                                                     connect="finite"), 0)
        self.lane_center = self._add("lanes", p.plot([], [], pen=pen(LANE, 0.8, QtCore.Qt.DotLine, 0.45),
                                                     connect="finite"), 0)
        self.reference = self._add("reference", p.plot([], [], pen=pen(ACCENT_REF, 1.4, QtCore.Qt.DashDotLine, 0.9),
                                                       name="Referenzpfad"), 1)
        self.stop_lines = self._add("infra", p.plot([], [], pen=pen("#f0f0f0", 3.0), connect="finite"), 1)
        self.parking = self._add("infra", p.plot([], [], pen=pen(MUTED, 1.2), connect="finite"), 1)
        self.lights = self._add("infra", pg.ScatterPlotItem(size=13, pen=pen("#111111", 1.5)), 11)
        self.trace = self._add("trace", p.plot([], [], pen=pen(EGO, 1.2, alpha=0.45), name="Gefahrene Spur"), 2)
        self.cands = CandidateLayer(p)
        for it in self.cands.items:
            self.items["candidates"].append(it)
        self.items["best"].append(self.cands.best)
        self.envelope = self._add("envelope", p.plot([], [], pen=pen(BEST, 0.9, alpha=0.55), connect="finite",
                                                     name="Fahrzeug-Envelope"), 5)
        self.ego_circles = self._add("circles", p.plot([], [], pen=pen(EGO, 1.0, alpha=0.8), connect="finite",
                                                       name="Kollisionskreise"), 8)
        self.ego_margin = self._add("circles", p.plot([], [], pen=pen(EGO, 0.8, QtCore.Qt.DashLine, 0.5),
                                                      connect="finite"), 8)
        self.obj_circles = self._add("circles", p.plot([], [], pen=pen(OBJECT, 1.0, alpha=0.8), connect="finite"), 8)
        self.obj_margin = self._add("circles", p.plot([], [], pen=pen(OBJECT, 0.8, QtCore.Qt.DashLine, 0.5),
                                                      connect="finite"), 8)
        self.obj_fill = self._add("objects", _path_item(OBJECT, 0.35, 7), 7)
        self.obj_outline = self._add("objects", p.plot([], [], pen=pen(OBJECT, 1.6), connect="finite",
                                                       name="Objekte"), 7)
        self.obj_labels = []
        self.pred_items = []
        self.ego_fill = self._add("ego", _path_item(cat_color(0), 0.55, 9), 9)
        self.ego_outline = self._add("ego", p.plot([], [], pen=pen(EGO, 1.8), name="Ego"), 9)
        self.ego_heading = self._add("ego", p.plot([], [], pen=pen(EGO, 1.8)), 9)
        self.desired = self._add("desired", pg.ScatterPlotItem(size=11, symbol="x", pen=pen(DESIRED, 2.0),
                                                               brush=brush(DESIRED)), 10)
        self.legend.addItem(self.desired, "Sollposition")
        self.mpc = self._add("mpc", p.plot([], [], pen=pen(DESIRED, 1.6, QtCore.Qt.DotLine), name="MPC-Horizont",
                                           symbol="o", symbolSize=3, symbolBrush=brush(DESIRED), symbolPen=None), 10)

    def _build_controls(self):
        self.controls = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(self.controls)
        row.setContentsMargins(4, 0, 4, 0)
        self.follow_box = QtWidgets.QCheckBox("Kamera folgt Ego")
        self.follow_box.setChecked(True)
        self.follow_box.toggled.connect(self.set_follow)
        self.legend_box = QtWidgets.QCheckBox("Legende")
        self.legend_box.setChecked(True)
        self.legend_box.toggled.connect(lambda on: self.legend.setVisible(on))
        self.layer_btn = QtWidgets.QToolButton()
        self.layer_btn.setText("Ebenen ▾")
        self.layer_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(self.layer_btn)
        self.layer_actions = {}
        for key, label in LAYERS:
            act = menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(True)
            act.toggled.connect(lambda on, k=key: self.set_layer_visible(k, on))
            self.layer_actions[key] = act
        self.layer_btn.setMenu(menu)
        fit = QtWidgets.QPushButton("Gesamtansicht")
        fit.clicked.connect(self.fit)
        self.zoom = QtWidgets.QDoubleSpinBox()
        self.zoom.setRange(10, 1000)
        self.zoom.setValue(90)
        self.zoom.setSuffix(" m")
        self.zoom.setToolTip("Sichtbreite bei Kamera-Verfolgung")
        self.zoom.valueChanged.connect(lambda _: self._apply_follow(force=True))
        for w in (self.follow_box, QtWidgets.QLabel("Sichtbreite"), self.zoom, self.layer_btn, self.legend_box, fit):
            row.addWidget(w)
        row.addStretch(1)
        # sequential cost scale of the candidates
        stops = ", ".join(f"stop:{k / (len(COST_RAMP) - 1):.3f} {c}" for k, c in enumerate(COST_RAMP))
        scale = QtWidgets.QLabel()
        scale.setFixedSize(110, 10)
        scale.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, {stops}); border-radius: 2px;")
        self.cost_scale = scale
        row.addWidget(QtWidgets.QLabel("Kandidatenkosten: niedrig"))
        row.addWidget(scale)
        row.addWidget(QtWidgets.QLabel("hoch"))

    # ------------------------------------------------------------------ controls
    def set_follow(self, on):
        self.follow = bool(on)
        if self.follow_box.isChecked() != self.follow:
            self.follow_box.setChecked(self.follow)
        self._apply_follow(force=True)

    def set_layer_visible(self, key, on):
        self.layer_visible[key] = bool(on)
        for item in self.items.get(key, []):
            item.setVisible(bool(on))
        self._sync_legend()

    def _sync_legend(self):
        # hidden layers leave the legend; restore order of the remaining entries
        named = [(it, it.name()) for key, _ in LAYERS for it in self.items[key]
                 if isinstance(it, pg.PlotDataItem) and it.name()]
        self.legend.clear()
        for it, name in named:
            if self.layer_visible.get(self._layer_of(it), True):
                self.legend.addItem(it, name)
        if self.layer_visible["desired"]:
            self.legend.addItem(self.desired, "Sollposition")

    def _layer_of(self, item):
        for key, items in self.items.items():
            if item in items:
                return key
        return None

    def fit(self):
        self.set_follow(False)
        self.plot.getPlotItem().getViewBox().autoRange(items=[self.lane_solid, self.trace, self.lane_dashed])

    # ------------------------------------------------------------------ candidate click
    def _on_click(self, event):
        if event.double():
            self._info_label.hide()
            return
        vb = self.plot.getPlotItem().getViewBox()
        pos = vb.mapSceneToView(event.scenePos())
        mx, my = pos.x(), pos.y()
        snap = self._last_snap
        if snap is None:
            self._info_label.hide()
            return
        idx, dist = self._find_nearest_candidate(snap, mx, my)
        if idx is None or dist > 5.0:
            self._info_label.hide()
            return
        info = self._candidate_info(snap, idx)
        self._info_label.setText(info["text"])
        self._info_label.show()
        self.candidate_clicked.emit(idx, info)

    def _find_nearest_candidate(self, snap, mx, my):
        xs = np.asarray((snap or {}).get("candidates_x", []), dtype=float)
        ys = np.asarray((snap or {}).get("candidates_y", []), dtype=float)
        if xs.ndim != 2 or xs.shape[0] == 0:
            return None, float("inf")
        dists = np.nanmin(np.hypot(xs - mx, ys - my), axis=1)
        idx = int(np.argmin(dists))
        return idx, float(dists[idx])

    def _candidate_info(self, snap, idx):
        cost = np.asarray((snap or {}).get("candidates_cost", []), dtype=float).ravel()
        status = np.asarray((snap or {}).get("candidates_status", []), dtype=int).ravel()
        reasons = (snap or {}).get("candidates_reason") or []
        best_idx = (snap or {}).get("best_index")
        cost_terms = (snap or {}).get("cost_terms") or {}
        n_total = len(cost)
        status_labels = {0: "gueltig", 1: "Restriktion", 2: "Kollision", 3: "nicht geprueft"}
        c = float(cost[idx]) if idx < len(cost) else float("nan")
        s = int(status[idx]) if idx < len(status) else -1
        r = str(reasons[idx]) if idx < len(reasons) else ""
        is_best = (best_idx is not None and int(best_idx) == idx)
        lines = [f"Trajektorie #{idx} / {n_total}"]
        lines.append(f"  Kosten:  {c:.4f}" + ("  ** GEWAEHLT **" if is_best else ""))
        lines.append(f"  Status:  {status_labels.get(s, str(s))}" + (f" ({r})" if r else ""))
        if is_best and cost_terms:
            lines.append("  Kostenzerlegung:")
            for k, v in sorted(cost_terms.items()):
                lines.append(f"    {k:30s} {v:8.4f}")
        return {"text": "\n".join(lines), "index": idx, "cost": c, "status": s, "reason": r,
                "is_best": is_best, "cost_terms": cost_terms if is_best else {}}

    # ------------------------------------------------------------------ data
    def set_data(self, data):
        self.data = data
        road = data.road if data else {}
        solid, dashed, centers = [], [], []
        for lane in road.get("lanes", []) or []:
            c = lane.get("center")
            if c is not None and len(c) == 2:
                centers.append(c)
            for side in ("left", "right"):
                line = lane.get(side)
                if line is None or len(line) != 2:
                    continue
                marking = str(lane.get(f"marking_{side}", "solid") or "solid").lower()
                if marking in ("none", "no", ""):
                    continue
                (dashed if "dash" in marking or "broken" in marking else solid).append(line)
        self.lane_solid.setData(*join(solid))
        self.lane_dashed.setData(*join(dashed))
        self.lane_center.setData(*join(centers))
        stops = []
        for sl in road.get("stop_lines", []) or []:
            th, w = float(sl.get("theta", 0.0)), float(sl.get("width", 3.5))
            nx, ny = -np.sin(th), np.cos(th)
            x, y = float(sl.get("x", 0)), float(sl.get("y", 0))
            stops.append(([x - nx * w / 2, x + nx * w / 2], [y - ny * w / 2, y + ny * w / 2]))
        self.stop_lines.setData(*join(stops))
        parks = [rect(float(pk.get("x", 0)), float(pk.get("y", 0)), float(pk.get("theta", 0)),
                      float(pk.get("length", 5.0)), float(pk.get("width", 2.5)))
                 for pk in road.get("parking", []) or []]
        self.parking.setData(*join(parks))
        if data is not None and data.t is not None and len(data.t):
            x, y = data.signals.get("ego_x"), data.signals.get("ego_y")
            self._trace_xy = (np.asarray(x, float), np.asarray(y, float)) if x is not None and y is not None else None
        else:
            self._trace_xy = None
        if not self.follow:
            self.fit()

    def set_time(self, t, snap=None):
        d = self.data
        if d is None:
            return
        self._last_snap = snap
        ex, ey, epsi = d.ego_pose(t)
        i = d.index(t)
        # driven trace
        if self._trace_xy is not None and i is not None:
            self.trace.setData(self._trace_xy[0][:i + 1], self._trace_xy[1][:i + 1])
        else:
            self.trace.setData([], [])
        # infrastructure state
        spots = []
        for tl in d.road.get("traffic_lights", []) or []:
            state = "off"
            for ts, st in tl.get("states", []) or []:
                if float(ts) <= t + 1e-9:
                    state = str(st).lower()
            spots.append({"pos": (float(tl.get("x", 0)), float(tl.get("y", 0))),
                          "brush": brush(LIGHT_COLORS.get(state, LIGHT_COLORS["off"]))})
        self.lights.setData(spots)
        # reference path
        ref = d.reference(snap)
        if ref is not None:
            self.reference.setData(ref.x, ref.y)
        else:
            self.reference.setData([], [])
        # candidates and the selected trajectory
        self.cands.update(snap, "candidates_x", "candidates_y", ("x", "y"))
        self._update_envelope(snap)
        # ego
        if np.isfinite(ex) and np.isfinite(ey):
            cx, cy = d.ego_center(ex, ey, epsi)
            ox, oy = rect(cx, cy, epsi, d.ego_length, d.ego_width)
            self.ego_outline.setData(ox, oy)
            self.ego_fill.setPath(_polygon_path([(ox, oy)]))
            self.ego_heading.setData([ex, ex + 0.5 * d.ego_length * np.cos(epsi)],
                                     [ey, ey + 0.5 * d.ego_length * np.sin(epsi)])
        else:
            self.ego_outline.setData([], [])
            self.ego_fill.setPath(QtGui.QPainterPath())
            self.ego_heading.setData([], [])
        dx, dy = d.value("des_x", t), d.value("des_y", t)
        self.desired.setData([dx], [dy]) if np.isfinite(dx) and np.isfinite(dy) else self.desired.setData([], [])
        ctrl = (snap or {}).get("controller") or {}
        hx, hy = ctrl.get("horizon_x"), ctrl.get("horizon_y")
        if hx is not None and hy is not None and len(hx) and len(hx) == len(hy):
            self.mpc.setData(np.asarray(hx, float), np.asarray(hy, float))
        else:
            self.mpc.setData([], [])
        self._update_objects(t, ex, ey, epsi, snap)
        self._update_prediction(snap)
        self._apply_follow()

    def _update_envelope(self, snap):
        d = self.data
        traj = (snap or {}).get("trajectory") or {}
        tt, x, y, th = (traj.get(k) for k in ("t", "x", "y", "theta"))
        if tt is None or x is None or y is None or len(x) < 2:
            self.envelope.setData([], [])
            return
        tt, x, y = np.asarray(tt, float), np.asarray(x, float), np.asarray(y, float)
        th = np.asarray(th, float) if th is not None else np.arctan2(np.gradient(y), np.gradient(x))
        ref_point = ((snap or {}).get("trajectory_info") or {}).get("reference_point", "cog")
        off = d.cg_to_rear + d.center_offset if ref_point == "rear_axle" else d.center_offset
        marks = np.arange(tt[0], tt[-1] + 1e-9, ENVELOPE_DT)
        idx = np.unique(np.clip(np.searchsorted(tt, marks), 0, len(tt) - 1))
        polys = [rect(x[k] + off * np.cos(th[k]), y[k] + off * np.sin(th[k]), th[k], d.ego_length, d.ego_width)
                 for k in idx[1:]]
        self.envelope.setData(*join(polys))

    def _update_objects(self, t, ex, ey, epsi, snap):
        d = self.data
        cc = (snap or {}).get("collision_circles") or {}
        margin = float(cc.get("margin", 0.0) or 0.0)
        outlines, circles, margins = [], [], []
        for lbl in self.obj_labels:
            self.plot.removeItem(lbl)
        self.obj_labels = []
        for oid in d.objects:
            o = d.object_state(oid, t)
            if o is None or (np.isfinite(ex) and np.hypot(o["x"] - ex, o["y"] - ey) > OBJECT_RANGE):
                continue
            outlines.append(rect(o["x"], o["y"], o["psi"], o["length"], o["width"]))
            offs, r = object_circles(o["length"], o["width"])
            for off in offs:
                cx, cy = o["x"] + off * np.cos(o["psi"]), o["y"] + off * np.sin(o["psi"])
                circles.append(circle(cx, cy, r))
                if margin > 0:
                    margins.append(circle(cx, cy, r + margin))
            lbl = pg.TextItem(f"{oid}", color=TEXT, anchor=(0.5, 0.5))
            lbl.setPos(o["x"], o["y"])
            lbl.setZValue(12)
            lbl.setVisible(self.layer_visible["objects"])
            self.plot.addItem(lbl)
            self.obj_labels.append(lbl)
        self.obj_outline.setData(*join(outlines))
        self.obj_fill.setPath(_polygon_path(outlines))
        self.obj_circles.setData(*join(circles))
        self.obj_margin.setData(*join(margins))
        # ego collision circles (offsets along the heading from the CoG)
        if np.isfinite(ex):
            r = float(cc.get("ego_radius", np.hypot(d.ego_length / 6, d.ego_width / 2)) or 1.0)
            offsets = cc.get("ego_offsets")
            if offsets is None:
                offsets = d.center_offset + object_circles(d.ego_length, d.ego_width, 3)[0]
            ec = [circle(ex + o * np.cos(epsi), ey + o * np.sin(epsi), r) for o in np.atleast_1d(offsets)]
            em = [circle(ex + o * np.cos(epsi), ey + o * np.sin(epsi), r + margin) for o in np.atleast_1d(offsets)]
            self.ego_circles.setData(*join(ec))
            self.ego_margin.setData(*join(em) if margin > 0 else ([], []))
        else:
            self.ego_circles.setData([], [])
            self.ego_margin.setData([], [])

    def _update_prediction(self, snap):
        preds = (snap or {}).get("prediction") or []
        steps = {}
        for p in preds:
            x, y = np.asarray(p.get("x", []), float), np.asarray(p.get("y", []), float)
            if not len(x) or len(x) != len(y):
                continue
            psi = np.asarray(p.get("psi", np.zeros(len(x))), float)
            if len(psi) != len(x):
                psi = np.zeros(len(x))
            stride = max(int(np.ceil(len(x) / 10)), 1)
            for j, k in enumerate(range(stride, len(x), stride)):
                steps.setdefault(j, []).append(rect(x[k], y[k], psi[k], float(p.get("length", 4.5)),
                                                    float(p.get("width", 1.8))))
        n = max(len(steps), 1)
        while len(self.pred_items) < len(steps):
            j = len(self.pred_items)
            item = self.plot.plot([], [], connect="finite", name="Prädiktion" if j == 0 else None)
            item.setZValue(5)
            item.setVisible(self.layer_visible["prediction"])
            self.items["prediction"].append(item)
            self.pred_items.append(item)
        for j, item in enumerate(self.pred_items):
            if j in steps:
                item.setPen(pen(OBJECT, 1.0, alpha=0.75 * (1 - j / n) + 0.1))
                item.setData(*join(steps[j]))
            else:
                item.setData([], [])

    def _apply_follow(self, force=False):
        if not self.follow or self.data is None:
            return
        ex, ey, epsi = self._ego_now()
        if not np.isfinite(ex):
            return
        w = float(self.zoom.value())
        vb = self.plot.getPlotItem().getViewBox()
        cx, cy = ex + 0.2 * w * np.cos(epsi), ey + 0.2 * w * np.sin(epsi)
        size = vb.size()
        ratio = size.height() / max(size.width(), 1.0) if size.width() > 10 else 0.5
        vb.setRange(xRange=(cx - w / 2, cx + w / 2), yRange=(cy - w * ratio / 2, cy + w * ratio / 2), padding=0)

    def _ego_now(self):
        x, y = self.ego_outline.getData()
        if x is None or not len(x):
            return np.nan, np.nan, 0.0
        hx, hy = self.ego_heading.getData()
        psi = np.arctan2(hy[1] - hy[0], hx[1] - hx[0]) if hx is not None and len(hx) == 2 else 0.0
        return float(hx[0]), float(hy[0]), float(psi)
