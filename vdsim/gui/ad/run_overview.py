"""RunOverview: KPIs, events, runtime profile and provenance of a single ADResult.
A click on an event emits time_requested(t) (the workbench moves the timeline there)."""

from __future__ import annotations

import json

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from .style import CAT, MUTED, EVENT_STYLE, fmt, make_plot, set_bars


def kpi_meta(key):
    # (label, unit, group, better) with fallbacks when vdsim.research is not importable
    try:
        from ...research.metrics import KPI_INFO, kpi_label
    except Exception:
        return key, "", "", ""
    if key in KPI_INFO:
        return KPI_INFO[key]
    label, unit = kpi_label(key)
    return label, unit, "Kosten" if key.startswith("cost_") else "Sonstige", ""


def table(headers, stretch=0):
    t = QtWidgets.QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    t.horizontalHeader().setSectionResizeMode(stretch, QtWidgets.QHeaderView.Stretch)
    return t


def fill(t, rows):
    t.setSortingEnabled(False)
    t.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QtWidgets.QTableWidgetItem()
            if isinstance(value, (int, float, np.floating, np.integer)) and not isinstance(value, bool):
                item.setData(QtCore.Qt.DisplayRole, fmt(value, 4))
                item.setData(QtCore.Qt.UserRole, float(value))
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            else:
                item.setText(str(value))
            t.setItem(r, c, item)


class RunOverview(QtWidgets.QWidget):
    TAB_TITLE = "Lauf-Kennwerte"
    time_requested = QtCore.Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self.header = QtWidgets.QLabel("Kein Ergebnis")
        self.header.setStyleSheet("font-size: 14px; padding: 4px;")
        self.kpi_table = table(["Gruppe", "Kennwert", "Wert", "Einheit", "besser"], 1)
        self.event_table = table(["Zeit [s]", "Typ", "Details"], 2)
        self.event_table.cellDoubleClicked.connect(self._event_clicked)
        self.event_table.cellClicked.connect(self._event_clicked)
        self.profile_table = table(["Knoten", "Aufrufe", "Mittel [ms]", "p95 [ms]", "Max [ms]", "Gesamt [s]"], 0)
        self.profile_plot = make_plot("Mittlere Rechenzeit je Knoten", "", "", xlabel="ms", xunit="")
        self.provenance = QtWidgets.QPlainTextEdit()
        self.provenance.setReadOnly(True)
        tabs = QtWidgets.QTabWidget()
        prof = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        prof.addWidget(self.profile_table)
        prof.addWidget(self.profile_plot)
        tabs.addTab(self.event_table, "Ereignisse")
        tabs.addTab(prof, "Laufzeitprofil")
        tabs.addTab(self.provenance, "Metadaten / Provenienz")
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.addWidget(self.kpi_table)
        split.addWidget(tabs)
        split.setSizes([650, 650])
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.header)
        layout.addWidget(split, 1)

    def set_result(self, result):
        self.result = result
        if result is None:
            self.header.setText("Kein Ergebnis")
            for t in (self.kpi_table, self.event_table, self.profile_table):
                t.setRowCount(0)
            return
        md = getattr(result, "metadata", {}) or {}
        self.header.setText(f"<b>{getattr(result, 'name', '') or 'Lauf'}</b>   "
                            f"<span style='color:{MUTED}'>Dauer {getattr(result, 'duration', 0.0):.2f} s, "
                            f"Seed {getattr(result, 'seed', '-')}, Abbruchgrund: {md.get('stop_reason', '-')}</span>")
        rows = []
        for key, value in (getattr(result, "kpis", {}) or {}).items():
            if not isinstance(value, (int, float, np.floating, np.integer)):
                continue
            label, unit, group, better = kpi_meta(key)
            rows.append((group, label, float(value), unit, {"low": "↓ niedriger", "high": "↑ höher"}.get(better, "")))
        fill(self.kpi_table, rows)
        events = sorted(getattr(result, "events", []) or [], key=lambda e: e.get("t", 0))
        self._events = events
        fill(self.event_table, [(float(e.get("t", 0)), EVENT_STYLE.get(e.get("type"), (e.get("type"), ""))[0],
                                 ", ".join(f"{k}={v}" for k, v in e.items() if k not in ("t", "type")))
                                for e in events])
        for r, e in enumerate(events):
            color = EVENT_STYLE.get(e.get("type"), ("", MUTED))[1]
            self.event_table.item(r, 1).setIcon(self._swatch(color))
        prof = getattr(result, "profile", {}) or {}
        prows = sorted(((n, int(s.get("calls", 0)), 1e3 * float(s.get("mean", np.nan)), 1e3 * float(s.get("p95", np.nan)),
                         1e3 * float(s.get("max", np.nan)), float(s.get("total", np.nan))) for n, s in prof.items()),
                       key=lambda r: -r[5] if np.isfinite(r[5]) else 0)
        fill(self.profile_table, prows)
        order = sorted(prows, key=lambda r: r[2] if np.isfinite(r[2]) else 0)
        set_bars(self.profile_plot, [r[0] for r in order], [r[2] for r in order], CAT[0], horizontal=True)
        meta = {"metadata": md, "provenance": getattr(result, "provenance", {}),
                "stack": getattr(result, "stack", {}), "scenario": getattr(result, "scenario", {})}
        self.provenance.setPlainText(json.dumps(meta, indent=2, ensure_ascii=False, default=str))

    @staticmethod
    def _swatch(color):
        pm = QtGui.QPixmap(10, 10)
        pm.fill(QtGui.QColor(color))
        return QtGui.QIcon(pm)

    def _event_clicked(self, row, _col=0):
        if 0 <= row < len(getattr(self, "_events", [])):
            self.time_requested.emit(float(self._events[row].get("t", 0.0)))
