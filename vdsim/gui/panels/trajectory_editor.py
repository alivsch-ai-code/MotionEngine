"""Interactive track editor: draggable waypoints (double-click a segment to insert one), waypoint table
with speed and corner radius, generated path preview with speed profile, friction map (mu patches)."""

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

from ...core.parameters import default_config_dir
from ...trajectory import Waypoint, WaypointEditor
from ...visualization.dashboard import ACCENT, MUTED


class TrajectoryEditorPanel(QtWidgets.QWidget):
    use_trajectory = QtCore.Signal(str)        # path of the saved trajectory JSON
    friction_changed = QtCore.Signal(list)     # list of friction patch dicts

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = WaypointEditor([Waypoint(0, 0, 50), Waypoint(80, 0, 50, 20), Waypoint(120, 40, 40, 15),
                                      Waypoint(80, 90, 40, 15), Waypoint(0, 90, 50)])
        self.preview = None
        layout = QtWidgets.QHBoxLayout(self)

        left = QtWidgets.QVBoxLayout()
        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.setLabel("bottom", "x", "m")
        self.plot.setLabel("left", "y", "m")
        self.path_item = self.plot.plot([], [], pen=pg.mkPen(ACCENT, width=2))
        self.speed_item = pg.ScatterPlotItem(size=4, pen=None)
        self.plot.addItem(self.speed_item)
        self.patch_items = []
        self.roi = None
        left.addWidget(self.plot, 1)
        hint = QtWidgets.QLabel("Punkte ziehen; Doppelklick auf ein Segment fügt einen Punkt ein; "
                                "Rechtsklick auf einen Punkt entfernt ihn.")
        hint.setStyleSheet(f"color: {MUTED};")
        left.addWidget(hint)
        layout.addLayout(left, 3)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("Wegpunkte"))
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["x [m]", "y [m]", "v [km/h]", "Radius [m]"])
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._table_edited)
        right.addWidget(self.table, 2)
        form = QtWidgets.QFormLayout()
        self.radius = QtWidgets.QDoubleSpinBox()
        self.radius.setRange(0, 500)
        self.radius.setValue(15)
        self.radius.setSuffix(" m")
        apply_radius = QtWidgets.QPushButton("Radius auf alle Ecken")
        apply_radius.clicked.connect(lambda: (self.editor.set_all_radii(self.radius.value()), self._sync_from_editor()))
        self.ay_max = QtWidgets.QDoubleSpinBox()
        self.ay_max.setRange(0, 15)
        self.ay_max.setValue(4.0)
        self.ay_max.setSuffix(" m/s²")
        form.addRow("Eckradius", self.radius)
        form.addRow(apply_radius)
        form.addRow("Max. Querbeschl. (0 = aus)", self.ay_max)
        right.addLayout(form)
        buttons = QtWidgets.QGridLayout()
        actions = [("Vorschau", self.update_preview), ("Rückgängig", self._undo),
                   ("Laden ...", self.load), ("Speichern ...", self.save),
                   ("Aus Szenario übernehmen", self._request_from_scenario),
                   ("Als Szenario-Trajektorie verwenden", self.apply_to_scenario)]
        for i, (text, slot) in enumerate(actions):
            btn = QtWidgets.QPushButton(text)
            if text.startswith("Als Szenario"):
                btn.setObjectName("primary")
            btn.clicked.connect(slot)
            buttons.addWidget(btn, i // 2, i % 2)
        right.addLayout(buttons)

        right.addWidget(QtWidgets.QLabel("Reibwertkarte (Rechtecke mit eigenem µ)"))
        self.friction = QtWidgets.QTableWidget(0, 5)
        self.friction.setHorizontalHeaderLabels(["x min", "x max", "y min", "y max", "µ"])
        self.friction.verticalHeader().setVisible(False)
        right.addWidget(self.friction, 1)
        frow = QtWidgets.QHBoxLayout()
        for text, slot in (("+ Fläche", self._add_patch), ("- Fläche", self._remove_patch),
                           ("Reibwertkarte übernehmen", self._emit_friction)):
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(slot)
            frow.addWidget(btn)
        right.addLayout(frow)
        layout.addLayout(right, 2)
        self.scenario_trajectory_provider = None
        self._sync_from_editor()

    # waypoint model <-> ROI / table
    def _sync_from_editor(self, rebuild_roi=True):
        if rebuild_roi:
            if self.roi is not None:
                self.plot.removeItem(self.roi)
            points = [[w.x, w.y] for w in self.editor.waypoints]
            self.roi = pg.PolyLineROI(points, closed=False, pen=pg.mkPen("#e8e8e8", width=1.5))
            self.roi.sigRegionChangeFinished.connect(self._roi_changed)
            self.plot.addItem(self.roi)
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.editor.waypoints))
        for row, w in enumerate(self.editor.waypoints):
            for col, value in enumerate((w.x, w.y, w.v_kmh, w.radius)):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(f"{value:.2f}"))
        self.table.blockSignals(False)
        self.update_preview()

    def _roi_changed(self):
        handles = self.roi.getSceneHandlePositions()
        points = [self.roi.mapSceneToParent(pos) for _, pos in handles]
        old = self.editor.waypoints
        new = []
        for i, p in enumerate(points):
            ref = old[min(i, len(old) - 1)] if old else Waypoint(0, 0)
            new.append(Waypoint(float(p.x()), float(p.y()), ref.v_kmh, ref.radius if 0 < i < len(points) - 1 else 0.0))
        self.editor._snapshot()
        self.editor.waypoints = new
        self._sync_from_editor(rebuild_roi=False)  # the ROI already shows the new points

    def _table_edited(self, item):
        row, col = item.row(), item.column()
        try:
            value = float(item.text())
        except ValueError:
            return
        w = self.editor.waypoints[row]
        self.editor._snapshot()
        setattr(w, ("x", "y", "v_kmh", "radius")[col], value)
        self._sync_from_editor()

    def _undo(self):
        self.editor.undo()
        self._sync_from_editor()

    # preview and export
    def update_preview(self):
        try:
            self.preview = self.editor.to_trajectory(ay_max=self.ay_max.value() or None)
        except Exception:
            self.preview = None
            self.path_item.setData([], [])
            return
        self.path_item.setData(self.preview.x, self.preview.y)
        v = self.preview.v * 3.6
        norm = (v - v.min()) / max(np.ptp(v), 1e-6)
        brushes = [pg.mkBrush(int(60 + 180 * n), int(140 - 60 * n), int(230 - 180 * n)) for n in norm[::4]]
        self.speed_item.setData(self.preview.x[::4], self.preview.y[::4], brush=brushes)

    def apply_to_scenario(self):
        self.update_preview()
        if self.preview is None:
            return
        directory = default_config_dir() / "trajectories"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "editor_trajektorie.json"
        self.preview.save(path)
        self.use_trajectory.emit(str(path))

    def save(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Wegpunkte speichern", "", "JSON (*.json)")
        if path:
            self.editor.save(path)

    def load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Wegpunkte laden", "", "JSON (*.json)")
        if path:
            self.editor = WaypointEditor.load(path)
            self._sync_from_editor()

    def _request_from_scenario(self):
        traj = self.scenario_trajectory_provider() if self.scenario_trajectory_provider else None
        if traj is not None:
            self.editor = WaypointEditor.from_trajectory(traj, n_points=25)
            self._sync_from_editor()

    # friction map
    def _add_patch(self):
        row = self.friction.rowCount()
        self.friction.insertRow(row)
        for col, value in enumerate((50.0, 100.0, -10.0, 10.0, 0.3)):
            self.friction.setItem(row, col, QtWidgets.QTableWidgetItem(f"{value:g}"))

    def _remove_patch(self):
        row = self.friction.currentRow()
        if row >= 0:
            self.friction.removeRow(row)

    def patches(self):
        patches = []
        for row in range(self.friction.rowCount()):
            try:
                values = [float(self.friction.item(row, c).text()) for c in range(5)]
            except (AttributeError, ValueError):
                continue
            patches.append(dict(zip(("x_min", "x_max", "y_min", "y_max", "mu"), values), name=f"patch {row + 1}"))
        return patches

    def set_patches(self, patches):
        self.friction.setRowCount(0)
        for p in patches:
            row = self.friction.rowCount()
            self.friction.insertRow(row)
            for col, key in enumerate(("x_min", "x_max", "y_min", "y_max", "mu")):
                self.friction.setItem(row, col, QtWidgets.QTableWidgetItem(f"{p[key]:g}"))
        self._draw_patches()

    def _draw_patches(self):
        for item in self.patch_items:
            self.plot.removeItem(item)
        self.patch_items = []
        for p in self.patches():
            rect = QtWidgets.QGraphicsRectItem(p["x_min"], p["y_min"], p["x_max"] - p["x_min"], p["y_max"] - p["y_min"])
            alpha = int(40 + 120 * (1 - min(p["mu"], 1.0)))
            rect.setBrush(pg.mkBrush(90, 160, 255, alpha))
            rect.setPen(pg.mkPen(None))
            self.plot.addItem(rect)
            self.patch_items.append(rect)

    def _emit_friction(self):
        self._draw_patches()
        self.friction_changed.emit(self.patches())
