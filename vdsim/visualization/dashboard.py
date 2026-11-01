"""Real-time dashboard widgets (PySide6 + pyqtgraph): top view, signal scope, KPI tiles, 3D view."""

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

ACCENT = "#3987e5"
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"]
MUTED = "#8b8d93"


def _pen(color, width=1.5, style=QtCore.Qt.SolidLine):
    return pg.mkPen(color=color, width=width, style=style)


class VehicleTopView(pg.PlotWidget):
    # Bird's-eye view: reference path, cones, lane lines, driven trace and the vehicle with its wheels
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAspectLocked(True)
        self.showGrid(x=True, y=True, alpha=0.15)
        self.setLabel("bottom", "x", "m")
        self.setLabel("left", "y", "m")
        self.follow = True
        self.zoom = 40.0
        self.ref_item = self.plot([], [], pen=_pen(MUTED, 1.2, QtCore.Qt.DashLine))
        self.trace_item = self.plot([], [], pen=_pen(ACCENT, 2.0))
        self.cone_item = pg.ScatterPlotItem(size=8, symbol="t1", brush=pg.mkBrush("#d95926"), pen=None)
        self.addItem(self.cone_item)
        self.lead_item = pg.ScatterPlotItem(size=14, symbol="s", brush=pg.mkBrush("#c98500"), pen=None)
        self.addItem(self.lead_item)
        self.boundary_items = []
        self.body_item = self.plot([], [], pen=_pen("#e8e8e8", 2.0), fillLevel=None)
        self.wheel_items = [self.plot([], [], pen=_pen("#ffffff", 3.0)) for _ in range(4)]
        self.length, self.width, self.lf, self.lr, self.track = 4.8, 1.85, 1.25, 1.55, 1.6
        self._trace_x, self._trace_y = [], []

    def set_vehicle(self, config):
        p = config.vehicle
        self.length, self.width = p.length, p.width
        self.lf, self.lr, self.track = p.cg_to_front, p.cg_to_rear, p.track_front

    def set_trajectory(self, traj):
        for item in self.boundary_items:
            self.removeItem(item)
        self.boundary_items = []
        if traj is None:
            self.ref_item.setData([], [])
            self.cone_item.setData([], [])
            return
        self.ref_item.setData(traj.x, traj.y)
        for bx, by in traj.boundaries:
            item = self.plot(np.asarray(bx), np.asarray(by), pen=_pen("#5a5d63", 1.0))
            self.boundary_items.append(item)
        cones = np.array(traj.cones) if traj.cones else np.zeros((0, 2))
        self.cone_item.setData(cones[:, 0] if len(cones) else [], cones[:, 1] if len(cones) else [])
        self.clear_trace()
        self.autoRange()

    def clear_trace(self):
        self._trace_x, self._trace_y = [], []
        self.trace_item.setData([], [])

    def update_state(self, state, steer=0.0, lead_xy=None):
        self._trace_x.append(state.x)
        self._trace_y.append(state.y)
        self.trace_item.setData(self._trace_x, self._trace_y)
        c, s = np.cos(state.psi), np.sin(state.psi)
        rot = lambda px, py: (state.x + px * c - py * s, state.y + px * s + py * c)
        hl, hw = self.length / 2, self.width / 2
        bx, by = rot(np.array([hl, hl, -hl, -hl, hl]), np.array([hw, -hw, -hw, hw, hw]))
        self.body_item.setData(bx, by)
        wheel_len = 0.65
        positions = [(self.lf, self.track / 2, steer), (self.lf, -self.track / 2, steer),
                     (-self.lr, self.track / 2, state.delta_r), (-self.lr, -self.track / 2, state.delta_r)]
        for item, (wx, wy, d) in zip(self.wheel_items, positions):
            ex, ey = wheel_len / 2 * np.cos(d), wheel_len / 2 * np.sin(d)
            px, py = rot(np.array([wx - ex, wx + ex]), np.array([wy - ey, wy + ey]))
            item.setData(px, py)
        if lead_xy is not None:
            self.lead_item.setData([lead_xy[0]], [lead_xy[1]])
        else:
            self.lead_item.setData([], [])
        if self.follow:
            self.setXRange(state.x - self.zoom, state.x + self.zoom, padding=0)
            self.setYRange(state.y - self.zoom * 0.6, state.y + self.zoom * 0.6, padding=0)


class SignalScope(QtWidgets.QWidget):
    # Grid of time plots that update from a SimulationResult while it is being recorded
    DEFAULT = [("speed", "Geschwindigkeit", 3.6, "km/h"), ("delta_f", "Radlenkwinkel", np.degrees(1), "°"),
               ("ay", "Querbeschleunigung", 1.0, "m/s²"), ("ax", "Längsbeschleunigung", 1.0, "m/s²"),
               ("r", "Gierrate", np.degrees(1), "°/s"), ("beta", "Schwimmwinkel", np.degrees(1), "°"),
               ("lateral_error", "Bahnabweichung", 1.0, "m"), ("roll", "Wankwinkel", np.degrees(1), "°")]

    def __init__(self, signals=None, columns=2, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self.signals = signals or self.DEFAULT
        self.plots, self.curves = [], []
        for i, (key, label, _, unit) in enumerate(self.signals):
            plot = pg.PlotWidget(title=f"{label} ({unit})")
            plot.showGrid(x=True, y=True, alpha=0.15)
            if self.plots:
                plot.setXLink(self.plots[0])
            curve = plot.plot([], [], pen=_pen(SERIES[i % len(SERIES)], 1.6))
            layout.addWidget(plot, i // columns, i % columns)
            self.plots.append(plot)
            self.curves.append(curve)

    def update_result(self, result):
        if result is None or len(result) < 2:
            return
        t = result["t"]
        for (key, _, scale, _), curve in zip(self.signals, self.curves):
            if key in result:
                data = result[key]
                curve.setData(t, (data if data.ndim == 1 else data[:, 0]) * scale)

    def clear(self):
        for curve in self.curves:
            curve.setData([], [])


class KPITile(QtWidgets.QFrame):
    def __init__(self, caption, unit="", parent=None):
        super().__init__(parent)
        self.setObjectName("kpiTile")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        self.value_label = QtWidgets.QLabel("-")
        self.value_label.setObjectName("kpiValue")
        caption_label = QtWidgets.QLabel(f"{caption} [{unit}]" if unit else caption)
        caption_label.setObjectName("kpiCaption")
        layout.addWidget(self.value_label)
        layout.addWidget(caption_label)

    def set_value(self, value, fmt="{:.1f}"):
        self.value_label.setText(value if isinstance(value, str) else fmt.format(value))


class GaugeRow(QtWidgets.QWidget):
    # live numeric readouts of the most important vehicle states
    ITEMS = [("speed", "Geschwindigkeit", "km/h"), ("ay", "Querbeschl.", "m/s²"), ("ax", "Längsbeschl.", "m/s²"),
             ("r", "Gierrate", "°/s"), ("beta", "Schwimmwinkel", "°"), ("steer", "Radlenkwinkel", "°"),
             ("t", "Zeit", "s")]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tiles = {}
        for key, caption, unit in self.ITEMS:
            tile = KPITile(caption, unit)
            self.tiles[key] = tile
            layout.addWidget(tile)

    def update_state(self, state):
        self.tiles["speed"].set_value(state.speed * 3.6)
        self.tiles["ay"].set_value(state.ay, "{:.2f}")
        self.tiles["ax"].set_value(state.ax, "{:.2f}")
        self.tiles["r"].set_value(np.degrees(state.r))
        self.tiles["beta"].set_value(np.degrees(state.beta), "{:.2f}")
        self.tiles["steer"].set_value(np.degrees(state.delta_f), "{:.2f}")
        self.tiles["t"].set_value(state.t, "{:.2f}")


def make_3d_view(parent=None):
    # 3D view if OpenGL is available, otherwise a placeholder label
    try:
        return Vehicle3DView(parent)
    except Exception as exc:  # no OpenGL context (remote desktop, headless)
        label = QtWidgets.QLabel(f"3D-Ansicht nicht verfügbar (OpenGL): {exc}")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.update_state = lambda *a, **k: None
        label.set_trajectory = lambda *a, **k: None
        label.set_vehicle = lambda *a, **k: None
        return label


class Vehicle3DView(QtWidgets.QWidget):
    # Body box, wheels and tire force arrows (vertical: Fz, horizontal: Fx/Fy), camera follows
    def __init__(self, parent=None):
        super().__init__(parent)
        import pyqtgraph.opengl as gl
        self.gl = gl
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor("#1e1f22")
        self.view.setCameraPosition(distance=14, elevation=22, azimuth=-120)
        layout.addWidget(self.view)
        grid = gl.GLGridItem()
        grid.setSize(400, 400)
        grid.setSpacing(5, 5)
        self.view.addItem(grid)
        self.path = gl.GLLinePlotItem(pos=np.zeros((2, 3)), color=(0.55, 0.55, 0.58, 1), width=2, antialias=True)
        self.view.addItem(self.path)
        self.body = gl.GLMeshItem(meshdata=self._box_mesh(), smooth=False, color=(0.22, 0.53, 0.9, 0.45),
                                  shader="shaded", glOptions="translucent")
        self.view.addItem(self.body)
        cyl = gl.MeshData.cylinder(rows=2, cols=20, radius=[0.32, 0.32], length=0.24)
        self.wheels = [gl.GLMeshItem(meshdata=cyl, color=(0.15, 0.15, 0.15, 1), shader="shaded") for _ in range(4)]
        for wheel in self.wheels:
            self.view.addItem(wheel)
        self.force_lines = [gl.GLLinePlotItem(pos=np.zeros((2, 3)), color=(0.85, 0.35, 0.15, 1), width=3) for _ in range(8)]
        for line in self.force_lines:
            self.view.addItem(line)
        self.length, self.width, self.height = 4.8, 1.85, 1.4
        self.lf, self.lr, self.track = 1.25, 1.55, 1.6
        self.cg_height, self.wheel_radius = 0.55, 0.32

    @staticmethod
    def _box_mesh():
        verts = np.array([[x, y, z] for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (0, 1)], dtype=float)
        faces = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                          [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
        from pyqtgraph.opengl import MeshData
        return MeshData(vertexes=verts, faces=faces)

    def set_vehicle(self, config):
        p = config.vehicle
        self.length, self.width = p.length, p.width
        self.lf, self.lr, self.track = p.cg_to_front, p.cg_to_rear, p.track_front
        self.cg_height, self.wheel_radius = p.cg_height, p.wheel_radius

    def set_trajectory(self, traj):
        if traj is not None and len(traj.x) > 1:
            self.path.setData(pos=np.column_stack([traj.x, traj.y, np.full(len(traj.x), 0.02)]))

    def update_state(self, state, steer=0.0, lead_xy=None):
        deg = np.degrees
        body_z = self.wheel_radius * 0.6 + state.heave
        self.body.resetTransform()
        self.body.scale(self.length, self.width, self.height * 0.75)
        self.body.translate(0, 0, 0)
        self.body.rotate(deg(state.pitch), 0, 1, 0, local=False)
        self.body.rotate(deg(state.roll), 1, 0, 0, local=False)
        self.body.rotate(deg(state.psi), 0, 0, 1, local=False)
        self.body.translate(state.x, state.y, body_z, local=False)
        c, s = np.cos(state.psi), np.sin(state.psi)
        corners = [(self.lf, self.track / 2, steer), (self.lf, -self.track / 2, steer),
                   (-self.lr, self.track / 2, state.delta_r), (-self.lr, -self.track / 2, state.delta_r)]
        fz_scale, f_scale = 1 / 4000.0, 1 / 4000.0
        for i, (wheel, (wx, wy, d)) in enumerate(zip(self.wheels, corners)):
            px, py = state.x + wx * c - wy * s, state.y + wx * s + wy * c
            wheel.resetTransform()
            wheel.translate(0, -0.12, 0)
            wheel.rotate(90, 1, 0, 0)
            wheel.rotate(deg(state.psi + d), 0, 0, 1, local=False)
            wheel.translate(px, py, self.wheel_radius, local=False)
            fz = state.fz[i] if len(state.fz) else 0.0
            self.force_lines[2 * i].setData(pos=np.array([[px, py, 0.0], [px, py, fz * fz_scale]]),
                                            color=(0.2, 0.75, 0.5, 1))
            heading = state.psi + d
            fx_w, fy_w = (state.fx[i], state.fy[i]) if len(state.fx) else (0.0, 0.0)
            gx = (fx_w * np.cos(heading) - fy_w * np.sin(heading)) * f_scale
            gy = (fx_w * np.sin(heading) + fy_w * np.cos(heading)) * f_scale
            self.force_lines[2 * i + 1].setData(pos=np.array([[px, py, 0.05], [px + gx, py + gy, 0.05]]),
                                                color=(0.85, 0.35, 0.15, 1))
        self.view.opts["center"] = pg.Vector(state.x, state.y, 0.5)
        self.view.update()
