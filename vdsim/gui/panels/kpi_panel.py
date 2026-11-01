"""KPI dashboard: headline tiles, full KPI table with ratings, vehicle characteristics from the analyses."""

import numpy as np
from PySide6 import QtGui, QtWidgets

from ...analysis import LinearSingleTrackAnalysis, QuasiStaticAnalysis
from ...core.conventions import G
from ...visualization.dashboard import KPITile
from ..theme import FAIL, OK, WARN

RATING = {"ok": ("OK", OK), "warn": ("Hinweis", WARN), "fail": ("nicht erfüllt", FAIL)}
HEADLINE = [("max_ay", "Max. Querbeschl.", "m/s²"), ("max_beta", "Max. Schwimmwinkel", "°"),
            ("max_lateral_error", "Max. Bahnabw.", "m"), ("max_friction_utilization", "Reibwertausn.", "-"),
            ("max_roll", "Max. Wankwinkel", "°"), ("duration", "Sim.-Zeit", "s")]


class KPIPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        tiles = QtWidgets.QHBoxLayout()
        self.tiles = {}
        for key, caption, unit in HEADLINE:
            tile = KPITile(caption, unit)
            self.tiles[key] = tile
            tiles.addWidget(tile)
        layout.addLayout(tiles)
        self.verdict = QtWidgets.QLabel("Noch keine Simulation")
        self.verdict.setStyleSheet("font-size: 14px; padding: 4px;")
        layout.addWidget(self.verdict)
        split = QtWidgets.QSplitter()
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Gruppe", "Kennwert", "Wert", "Einheit", "Bewertung"])
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        split.addWidget(self.table)
        self.vehicle_table = QtWidgets.QTableWidget(0, 3)
        self.vehicle_table.setHorizontalHeaderLabels(["Fahrzeugkennwert", "Wert", "Einheit"])
        self.vehicle_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.vehicle_table.verticalHeader().setVisible(False)
        self.vehicle_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        split.addWidget(self.vehicle_table)
        split.setSizes([700, 400])
        layout.addWidget(split, 1)

    def show_kpis(self, kpis, stop_reason=""):
        self.table.setRowCount(len(kpis))
        fails = [k.label for k in kpis if k.rating == "fail"]
        warns = [k.label for k in kpis if k.rating == "warn"]
        for row, kpi in enumerate(kpis):
            values = [kpi.group, kpi.label, kpi.formatted(), kpi.unit, RATING.get(kpi.rating, ("", None))[0]]
            for col, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(text))
                if col == 4 and kpi.rating in RATING:
                    item.setForeground(QtGui.QColor(RATING[kpi.rating][1]))
                self.table.setItem(row, col, item)
        by_key = {k.key: k for k in kpis}
        for key, tile in self.tiles.items():
            tile.set_value(by_key[key].formatted() if key in by_key else "-")
        if fails:
            text, color = f"Nicht erfüllt: {', '.join(fails)}", FAIL
        elif warns:
            text, color = f"Hinweise: {', '.join(warns)}", WARN
        else:
            text, color = "Alle bewerteten Kennwerte in Ordnung", OK
        self.verdict.setText(f"{text}   ({stop_reason})" if stop_reason else text)
        self.verdict.setStyleSheet(f"font-size: 14px; padding: 4px; color: {color};")

    def show_vehicle(self, config):
        try:
            lin, qs = LinearSingleTrackAnalysis(config), QuasiStaticAnalysis(config)
            eig = lin.eigen(100 / 3.6)
            rows = [("Eigenlenkgradient", np.degrees(lin.understeer_gradient) * G, "°/g"),
                    ("Charakteristische Geschwindigkeit", lin.characteristic_speed * 3.6, "km/h"),
                    ("Gierverstärkung bei 100 km/h", lin.steady_state_gains(100 / 3.6)["yaw_rate"], "1/s"),
                    ("Gier-Eigenfrequenz bei 100 km/h", eig["natural_frequency"], "Hz"),
                    ("Gier-Dämpfungsmaß bei 100 km/h", eig["damping"], "-"),
                    ("Schräglaufsteifigkeit Achse vorne", lin.model.c_front / 1000, "kN/rad"),
                    ("Schräglaufsteifigkeit Achse hinten", lin.model.c_rear / 1000, "kN/rad")]
            q = qs.summary()
            rows += [("Achslast vorne", q["axle_load_front_share"] * 100, "%"),
                     ("Wankgradient", q["roll_gradient_deg_per_g"], "°/g"),
                     ("Wanksteifigkeitsverteilung vorne", q["roll_stiffness_distribution"] * 100, "%"),
                     ("Querlastverteilung vorne (LLTD)", q["lltd_front"] * 100, "%"),
                     ("Rollachsenhöhe am Schwerpunkt", q["roll_axis_height"] * 1000, "mm"),
                     ("Radabheben ab a_y", q["wheel_lift_ay"], "m/s²"),
                     ("Wendekreis", q["turning_circle"], "m")]
        except Exception as exc:  # invalid parameters while editing
            rows = [("Analyse nicht möglich", 0.0, str(exc))]
        self.vehicle_table.setRowCount(len(rows))
        for row, (label, value, unit) in enumerate(rows):
            for col, text in enumerate((label, "-" if not np.isfinite(value) else f"{value:.3g}", unit)):
                self.vehicle_table.setItem(row, col, QtWidgets.QTableWidgetItem(text))
