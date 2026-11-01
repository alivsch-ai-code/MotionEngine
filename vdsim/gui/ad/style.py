"""Plot conventions of the AD workbench (data-viz rules) and small pyqtgraph helpers.

    categorical   fixed slot order (dark-mode steps of the reference palette), never cycled anew
    sequential    cost: one warm family, light yellow (low) -> dark red (high)
    status        OK / WARN / FAIL from the theme, only for states (fallback, reinit, collision)
    one y-axis per plot, recessive grid, legend from two series on
"""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from ..theme import BACKGROUND, BORDER, FAIL, MUTED, OK, PANEL, TEXT, WARN

CAT = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
COST_RAMP = ["#fde68a", "#fcd34d", "#fbbf24", "#f59e0b", "#f97316", "#ea580c", "#dc2626", "#b91c1c", "#8f1414"]
BLUE_RAMP = ["#0d366b", "#104281", "#184f95", "#1c5cab", "#256abf", "#2a78d6", "#3987e5", "#5598e7",
             "#6da7ec", "#86b6ef", "#9ec5f4", "#b7d3f6"]
BEST = "#4ade80"          # selected trajectory (distinct from the status OK green)
INVALID = "#6b6e75"
GRID_ALPHA = 0.12
EGO = "#e8e8e8"
DESIRED = "#9085e9"
ACCENT_REF = "#86b6ef"     # reference path
OBJECT = "#c98500"
LANE = "#7d8088"
LIGHT_COLORS = {"red": "#e5484d", "yellow": "#e5b400", "amber": "#e5b400", "green": "#30a46c", "off": "#55585e"}
EVENT_STYLE = {   # type -> (label, color)
    "collision": ("Kollision", FAIL),
    "reinit": ("Reinitialisierung", WARN),
    "goal_reached": ("Ziel erreicht", OK),
    "maneuver": ("Manöver", CAT[0]),
    "mode_switch": ("Moduswechsel", CAT[2]),
    "controller_switch": ("Reglerwechsel", CAT[4]),
    "scenario_event": ("Szenario", MUTED),
}

__all__ = ["CAT", "COST_RAMP", "BLUE_RAMP", "BEST", "INVALID", "OK", "WARN", "FAIL", "MUTED", "TEXT", "PANEL",
           "BORDER", "BACKGROUND", "pen", "make_plot", "cursor", "cat_color", "cost_colors", "sig", "fmt",
           "set_bars", "Placeholder"]


def pen(color, width=1.6, style=QtCore.Qt.SolidLine, alpha=None):
    c = QtGui.QColor(color)
    if alpha is not None:
        c.setAlphaF(float(alpha))
    p = pg.mkPen(c, width=width, style=style)
    p.setCosmetic(True)
    return p


def brush(color, alpha=None):
    c = QtGui.QColor(color)
    if alpha is not None:
        c.setAlphaF(float(alpha))
    return pg.mkBrush(c)


def cat_color(i):
    # fixed categorical order; beyond eight entities fall back to a neutral gray (no generated hues)
    return CAT[i] if 0 <= i < len(CAT) else MUTED


def cost_colors(n_bins=len(COST_RAMP)):
    return [COST_RAMP[int(round(i * (len(COST_RAMP) - 1) / max(n_bins - 1, 1)))] for i in range(n_bins)]


def make_plot(title="", ylabel="", unit="", xlabel="t", xunit="s", legend=False, parent=None):
    plot = pg.PlotWidget(parent=parent)
    plot.setBackground(BACKGROUND)
    item = plot.getPlotItem()
    if title:
        item.setTitle(f"<span style='color:{TEXT};font-size:10pt'>{title}</span>")
    plot.showGrid(x=True, y=True, alpha=GRID_ALPHA)
    for name in ("left", "bottom"):
        axis = plot.getAxis(name)
        axis.setPen(pen(BORDER, 1))
        axis.setTextPen(pen(MUTED, 1))
        axis.enableAutoSIPrefix(False)      # keep the SI unit of the data (no "mm", "x0.001")
    unit = "" if unit == "-" else unit
    xunit = "" if xunit == "-" else xunit
    if ylabel or unit:
        plot.setLabel("left", ylabel, units=None if not unit else unit, color=MUTED)
    plot.getAxis("left").setWidth(48)
    if xlabel:
        plot.setLabel("bottom", xlabel, units=None if not xunit else xunit, color=MUTED)
    item.setMenuEnabled(True)
    if legend:
        leg = plot.addLegend(offset=(-8, 8), labelTextColor=TEXT, brush=brush(PANEL, 0.85), pen=pen(BORDER, 1),
                             labelTextSize="8pt")
        leg.setZValue(100)
    plot.setMinimumHeight(120)
    return plot


def cursor(plot, color=TEXT):
    line = pg.InfiniteLine(pos=0.0, angle=90, movable=False, pen=pen(color, 1, QtCore.Qt.DashLine, 0.7))
    line.setZValue(50)
    plot.addItem(line, ignoreBounds=True)
    return line


def sig(result, key):
    # signal array or None (missing / not numeric / all NaN)
    signals = getattr(result, "signals", None) or {}
    if key not in signals:
        return None
    try:
        arr = np.asarray(signals[key], dtype=float)
    except (TypeError, ValueError):
        return None
    if arr.ndim != 1 or not len(arr) or not np.any(np.isfinite(arr)):
        return None
    return arr


def fmt(value, digits=3):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value) if value is not None else "-"
    if not np.isfinite(v):
        return "-"
    if v != 0 and (abs(v) >= 1e5 or abs(v) < 1e-3):
        return f"{v:.{digits - 1}e}"
    return f"{v:.{digits}g}"


def set_bars(plot, labels, values, colors=None, horizontal=False, highlight=None, width=0.7):
    # replace the bars of a categorical bar chart; one color per bar (entity) or a single series color
    for it in [i for i in plot.getPlotItem().items if isinstance(i, (pg.BarGraphItem, pg.TextItem))]:
        plot.removeItem(it)
    values = np.nan_to_num(np.asarray(values, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    pos = np.arange(len(values))
    if colors is None:
        colors = [CAT[0]] * len(values)
    elif isinstance(colors, str):
        colors = [colors] * len(values)
    colors = list(colors)
    if highlight is not None:
        colors = [CAT[0] if i == highlight else INVALID for i in range(len(values))]
    brushes = [brush(c) for c in colors]
    gap = pen(BACKGROUND, 2)
    labels = [str(lbl) for lbl in labels]
    if horizontal:
        bar = pg.BarGraphItem(x0=0, y=pos, height=width, width=values, brushes=brushes, pen=gap)
        plot.getAxis("left").setTicks([list(zip(pos, labels))])
        longest = max((len(lbl) for lbl in labels), default=4)
        plot.getAxis("left").setWidth(int(min(240, max(48, 6.5 * longest + 14))))
        plot.getAxis("bottom").setTicks(None)
    else:
        bar = pg.BarGraphItem(x=pos, height=values, width=width, brushes=brushes, pen=gap)
        plot.getAxis("bottom").setTicks([list(zip(pos, labels))])
        plot.getAxis("left").setTicks(None)
        plot.getAxis("left").setWidth(48)
    plot.addItem(bar)
    if len(values):
        plot.getPlotItem().enableAutoRange()
        if not np.any(values):      # all zero: show a meaningful 0..1 range instead of an arbitrary one
            (plot.setXRange if horizontal else plot.setYRange)(0, 1)
    return bar


class Placeholder(QtWidgets.QLabel):
    # stands in for a tab whose module is not (yet) available
    def __init__(self, title, reason="", parent=None):
        text = f"<h3>{title}</h3><p style='color:{MUTED}'>Modul noch nicht verfügbar.</p>"
        if reason:
            text += f"<p style='color:{MUTED};font-size:10px'>{reason}</p>"
        super().__init__(text, parent)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setWordWrap(True)
