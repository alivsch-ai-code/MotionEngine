"""Interactive timeline: slider over the simulation time with event marks, play/pause, speed, single step,
jump to the previous/next event. Emits time_changed(t); every view of the planner view follows it."""

from __future__ import annotations

import time

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from .style import EVENT_STYLE, MUTED

SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0]
EVENT_FILTERS = [("Alle Ereignisse", None), ("Reinitialisierung", "reinit"), ("Kollision", "collision"),
                 ("Manöver", "maneuver"), ("Moduswechsel", "mode_switch"), ("Reglerwechsel", "controller_switch"),
                 ("Szenario", "scenario_event"), ("Ziel erreicht", "goal_reached")]
RES = 1000          # slider ticks per second


class EventSlider(QtWidgets.QSlider):
    # horizontal slider that paints colored event marks below the groove
    def __init__(self, parent=None):
        super().__init__(QtCore.Qt.Horizontal, parent)
        self.marks = []           # [(value, color)]
        self.setMinimumHeight(30)
        self.setStyleSheet("QSlider::groove:horizontal { height: 4px; background: #3a3d43; border-radius: 2px; }"
                           "QSlider::sub-page:horizontal { background: #2a78d6; border-radius: 2px; }"
                           "QSlider::handle:horizontal { background: #e6e6e6; width: 10px; margin: -6px 0;"
                           " border-radius: 5px; }")

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.marks or self.maximum() <= self.minimum():
            return
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        groove = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self)
        handle = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)
        span = groove.width() - handle.width()
        painter = QtGui.QPainter(self)
        for value, color in self.marks:
            px = groove.x() + handle.width() / 2 + QtWidgets.QStyle.sliderPositionFromValue(
                self.minimum(), self.maximum(), int(value), span)
            painter.setPen(QtGui.QPen(QtGui.QColor(color), 2))
            painter.drawLine(QtCore.QPointF(px, self.height() - 9), QtCore.QPointF(px, self.height() - 1))
        painter.end()


class Timeline(QtWidgets.QWidget):
    time_changed = QtCore.Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.t0, self.t1 = 0.0, 0.0
        self.step_dt = 0.1
        self.events = []
        self._t = 0.0
        self._last_tick = None
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)

        style = self.style()
        def button(icon, tip, slot):
            b = QtWidgets.QToolButton()
            b.setIcon(style.standardIcon(icon))
            b.setToolTip(tip)
            b.setAutoRaise(True)
            b.clicked.connect(slot)
            return b
        self.prev_event_btn = button(QtWidgets.QStyle.SP_MediaSkipBackward, "Vorheriges Ereignis",
                                     lambda: self.jump_event(-1))
        self.step_back_btn = button(QtWidgets.QStyle.SP_MediaSeekBackward, "Einzelschritt zurück",
                                    lambda: self.step(-1))
        self.play_btn = button(QtWidgets.QStyle.SP_MediaPlay, "Wiedergabe / Pause (Leertaste)", self.toggle_play)
        self.step_fwd_btn = button(QtWidgets.QStyle.SP_MediaSeekForward, "Einzelschritt vor", lambda: self.step(1))
        self.next_event_btn = button(QtWidgets.QStyle.SP_MediaSkipForward, "Nächstes Ereignis",
                                     lambda: self.jump_event(1))
        self.slider = EventSlider()
        self.slider.valueChanged.connect(self._slider_moved)
        self.speed = QtWidgets.QComboBox()
        for s in SPEEDS:
            self.speed.addItem(f"{s:g}×", s)
        self.speed.setCurrentIndex(SPEEDS.index(1.0))
        self.speed.setToolTip("Wiedergabegeschwindigkeit")
        self.event_filter = QtWidgets.QComboBox()
        for label, kind in EVENT_FILTERS:
            self.event_filter.addItem(label, kind)
        self.event_filter.setToolTip("Ereignistyp für den Sprung")
        self.event_filter.currentIndexChanged.connect(self._update_marks)
        self.time_label = QtWidgets.QLabel("t = 0.00 s")
        self.time_label.setMinimumWidth(130)
        self.time_label.setStyleSheet("font-family: Consolas, monospace;")
        self.legend = QtWidgets.QLabel("")
        self.legend.setStyleSheet(f"color: {MUTED}; font-size: 10px;")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        for w in (self.prev_event_btn, self.step_back_btn, self.play_btn, self.step_fwd_btn, self.next_event_btn):
            layout.addWidget(w)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.speed)
        layout.addWidget(self.event_filter)
        layout.addWidget(self.legend)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space), self, self.toggle_play,
                        context=QtCore.Qt.WidgetWithChildrenShortcut)

    # ------------------------------------------------------------------ setup
    def set_range(self, t0, t1, step_dt=None):
        self.pause()
        self.t0, self.t1 = float(t0), float(max(t1, t0))
        if step_dt:
            self.step_dt = float(step_dt)
        self.slider.blockSignals(True)
        self.slider.setRange(0, int(round((self.t1 - self.t0) * RES)))
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self._t = self.t0
        self._update_label()

    def set_events(self, events):
        self.events = sorted((e for e in (events or []) if "t" in e), key=lambda e: e["t"])
        present = []
        for e in self.events:
            if e.get("type") not in present:
                present.append(e.get("type"))
        self.legend.setText("  ".join(f"<span style='color:{EVENT_STYLE.get(k, ('', MUTED))[1]}'>▮</span> "
                                      f"{EVENT_STYLE.get(k, (k, ''))[0]}" for k in present))
        self._update_marks()

    def _filtered(self):
        kind = self.event_filter.currentData()
        return [e for e in self.events if kind is None or e.get("type") == kind]

    def _update_marks(self):
        self.slider.marks = [((e["t"] - self.t0) * RES, EVENT_STYLE.get(e.get("type"), ("", MUTED))[1])
                             for e in self._filtered()]
        self.slider.update()

    # ------------------------------------------------------------------ time
    @property
    def current_time(self):
        return self._t

    def set_time(self, t, emit=True):
        t = float(np.clip(t, self.t0, self.t1))
        self._t = t
        self.slider.blockSignals(True)
        self.slider.setValue(int(round((t - self.t0) * RES)))
        self.slider.blockSignals(False)
        self._update_label()
        if emit:
            self.time_changed.emit(t)

    def _slider_moved(self, value):
        self._t = self.t0 + value / RES
        self._update_label()
        self.time_changed.emit(self._t)

    def _update_label(self):
        self.time_label.setText(f"t = {self._t:6.2f} / {self.t1:.2f} s")

    def step(self, n=1):
        self.pause()
        # snap to the step grid (planning cycles) so repeated steps land on snapshot times
        k = np.round((self._t - self.t0) / self.step_dt) + n
        self.set_time(self.t0 + k * self.step_dt)

    def jump_event(self, direction=1):
        self.pause()
        times = [e["t"] for e in self._filtered()]
        if direction > 0:
            nxt = [t for t in times if t > self._t + 1e-6]
            if nxt:
                self.set_time(nxt[0])
        else:
            prv = [t for t in times if t < self._t - 1e-6]
            if prv:
                self.set_time(prv[-1])

    # ------------------------------------------------------------------ playback
    @property
    def playing(self):
        return self.timer.isActive()

    def play(self):
        if self.t1 <= self.t0:
            return
        if self._t >= self.t1 - 1e-9:
            self.set_time(self.t0)
        self._last_tick = time.perf_counter()
        self.timer.start()
        self.play_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))

    def pause(self):
        self.timer.stop()
        self.play_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

    def toggle_play(self):
        self.pause() if self.playing else self.play()

    def _tick(self):
        now = time.perf_counter()
        dt = (now - (self._last_tick or now)) * float(self.speed.currentData() or 1.0)
        self._last_tick = now
        t = self._t + dt
        if t >= self.t1:
            self.set_time(self.t1)
            self.pause()
        else:
            self.set_time(t)
