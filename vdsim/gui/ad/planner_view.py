"""PlannerView: central visualization of planner and controller with an interactive timeline.

    info bar         time, mode, maneuver, active controller, candidates n_checked / n_candidates, planning time
    top view         lanes, candidates by cost, collision circles, predictions, envelope, ego, MPC horizon
    analysis tabs    Frenet view, cost evaluation, restriction violations
    scope tabs       controller states, steering / acceleration commands, speed
    timeline         slider with event marks, play/pause, speed, single step, jump to events
"""

from __future__ import annotations

import numpy as np
from PySide6 import QtCore, QtWidgets

from .data import ResultData
from .style import FAIL, MUTED, OK, PANEL, BORDER, WARN, fmt
from .timeline import Timeline
from .topview import TopView
from .views import CommandView, ConstraintView, ControllerView, CostView, FrenetView


class InfoBar(QtWidgets.QFrame):
    FIELDS = [("t", "Zeit"), ("mode", "Modus"), ("maneuver", "Manöver"), ("controller", "Regler"),
              ("candidates", "Kandidaten geprüft/erzeugt"), ("plan_time", "Planungszeit"), ("v", "v"),
              ("cost", "Kosten")]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"QFrame {{ background: {PANEL}; border-bottom: 1px solid {BORDER}; }}"
                           "QLabel { background: transparent; }")
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(8, 3, 8, 3)
        row.setSpacing(18)
        self.labels = {}
        for key, caption in self.FIELDS:
            box = QtWidgets.QVBoxLayout()
            box.setSpacing(0)
            cap = QtWidgets.QLabel(caption)
            cap.setStyleSheet(f"color: {MUTED}; font-size: 10px;")
            val = QtWidgets.QLabel("-")
            val.setStyleSheet("font-size: 13px; font-weight: bold;")
            box.addWidget(cap)
            box.addWidget(val)
            row.addLayout(box)
            self.labels[key] = val
        row.addStretch(1)
        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet("font-size: 12px; font-weight: bold;")
        row.addWidget(self.status)

    def set_values(self, values, flags):
        for key, val in values.items():
            if key in self.labels:
                self.labels[key].setText(str(val))
        # status chips: icon + label + status color (never color alone)
        chips = []
        if flags.get("collision"):
            chips.append(f"<span style='color:{FAIL}'>✖ Kollision</span>")
        if flags.get("off_road"):
            chips.append(f"<span style='color:{FAIL}'>✖ Fahrbahn verlassen</span>")
        if flags.get("fallback"):
            chips.append(f"<span style='color:{FAIL}'>✖ Fallback</span>")
        if flags.get("reinit"):
            chips.append(f"<span style='color:{WARN}'>▲ Reinitialisierung</span>")
        if not chips and flags.get("valid"):
            chips.append(f"<span style='color:{OK}'>✔ Plan gültig</span>")
        self.status.setText("   ".join(chips))


class PlannerView(QtWidgets.QWidget):
    TAB_TITLE = "Planer && Regler"
    time_changed = QtCore.Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self.data = None
        self._snap_index = None
        self.info = InfoBar()
        self.top = TopView()
        self.frenet = FrenetView()
        self.cost = CostView()
        self.constraints = ConstraintView()
        self.controller = ControllerView()
        self.commands = CommandView()
        self.timeline = Timeline()
        self.timeline.time_changed.connect(self.set_time)

        self.analysis_tabs = QtWidgets.QTabWidget()
        for w, title in ((self.frenet, "Frenet"), (self.cost, "Kosten"), (self.constraints, "Restriktionen")):
            self.analysis_tabs.addTab(w, title)
        self.scope_tabs = QtWidgets.QTabWidget()
        for w, title in ((self.controller, "Reglerzustände"), (self.commands, "Stellgrößen && Geschwindigkeit")):
            self.scope_tabs.addTab(w, title)
        upper = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        upper.addWidget(self.top)
        upper.addWidget(self.analysis_tabs)
        upper.setSizes([900, 640])
        main = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        main.addWidget(upper)
        main.addWidget(self.scope_tabs)
        main.setSizes([520, 440])
        self.empty = QtWidgets.QLabel("Noch kein Ergebnis. Simulation starten oder Ergebnis laden.")
        self.empty.setAlignment(QtCore.Qt.AlignCenter)
        self.empty.setStyleSheet(f"color: {MUTED}; font-size: 14px;")
        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self.empty)
        self.stack.addWidget(main)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.info)
        layout.addWidget(self.stack, 1)
        layout.addWidget(self.timeline)

    # ------------------------------------------------------------------ public API
    def set_result(self, result):
        self.result = result
        if result is None:
            self.data = None
            self.stack.setCurrentIndex(0)
            return
        self.data = ResultData(result)
        self.stack.setCurrentIndex(1)
        self.top.set_data(self.data)
        self.frenet.set_data(self.data)
        self.constraints.set_data(self.data)
        self.controller.set_result(result, self.data, self.data.events)
        self.commands.set_result(result, [e for e in self.data.events if e.get("type") in ("reinit", "collision")])
        self.timeline.set_range(self.data.t0, self.data.t1, self.data.plan_period)
        self.timeline.set_events(self.data.events)
        self._snap_index = None
        self.set_time(self.data.t0, force=True)
        self.top._apply_follow(force=True)

    def set_time(self, t, force=False):
        if self.data is None:
            return
        t = float(np.clip(t, self.data.t0, self.data.t1))
        if abs(self.timeline.current_time - t) > 1e-9:
            self.timeline.set_time(t, emit=False)
        i = self.data.snapshot_index(t)
        snap = self.data.snapshots[i] if i is not None else None
        self.top.set_time(t, snap)
        if force or i != self._snap_index:
            self.frenet.set_time(t, snap)
            self.cost.set_time(t, snap)
        self.constraints.set_time(t, snap)
        self.controller.set_time(t, snap)
        self.commands.set_time(t, snap)
        self._snap_index = i
        self._update_info(t, snap)
        self.time_changed.emit(t)

    @property
    def current_time(self):
        return self.timeline.current_time

    def current_snapshot(self):
        return self.data.snapshot(self.current_time) if self.data else None

    # ------------------------------------------------------------------ info bar
    def _update_info(self, t, snap):
        d = self.data
        snap = snap or {}
        info = snap.get("trajectory_info") or {}
        beh = snap.get("behavior") or {}
        mode = snap.get("mode") or info.get("mode")
        if not mode:
            mid = d.value("plan_mode_id", t)
            mode = d.name("modes", mid) if np.isfinite(mid) else "-"
        maneuver = beh.get("maneuver")
        if not maneuver:
            mid = d.value("maneuver_id", t)
            maneuver = d.name("maneuvers", mid) if np.isfinite(mid) else "-"
        cid = d.value("controller_id", t)
        ctrl = d.name("controllers", cid) if np.isfinite(cid) else ((snap.get("controller") or {}).get("active") or "-")
        n_c, n_k = snap.get("n_candidates"), snap.get("n_checked")
        pt = snap.get("compute_time")
        if pt is None:
            pt = d.value("plan_time", t)
        v = d.value("ego_v", t)
        cost = info.get("cost", d.value("plan_cost", t))
        values = {"t": f"{t:.2f} s", "mode": mode, "maneuver": maneuver, "controller": ctrl,
                  "candidates": f"{n_k if n_k is not None else '-'} / {n_c if n_c is not None else '-'}",
                  "plan_time": f"{1e3 * pt:.1f} ms" if pt is not None and np.isfinite(pt) else "-",
                  "v": f"{3.6 * v:.1f} km/h" if np.isfinite(v) else "-", "cost": fmt(cost)}
        flags = {"collision": d.value("collision", t, 0.0) > 0.5, "off_road": d.value("off_road", t, 0.0) > 0.5,
                 "fallback": bool(snap.get("fallback")) or (info.get("valid") is False),
                 "reinit": bool(snap.get("reinitialized") or info.get("reinitialized")),
                 "valid": bool(snap) and info.get("valid", True)}
        self.info.set_values(values, flags)
