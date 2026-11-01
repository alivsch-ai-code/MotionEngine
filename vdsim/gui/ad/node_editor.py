"""NodeEditor: Simulink-like architecture editor for vdsim.runtime graphs (AD workbench tab).

    palette       all registered components (framework.plugins.available_components), grouped by CATEGORY,
                  searchable, drag & drop onto the canvas
    canvas        nodes (title, version, language), ports colored by type (types.TYPE_COLORS), Bezier wires
                  drawn from output to input (Graph.check_connection rejects type errors), Del deletes,
                  wheel zooms, middle mouse pans
    side panels   block parameters (ParameterTree -> Graph.set_param, period), validation, inspector,
                  probes (scope plots), profiler, version history (VersionStore: snapshot, diff, restore), log
    simulation    QTimer -> Executor.advance(wall_dt) with real-time factor; AD stacks get a scenario context
                  (vehicle, road, scenario like vdsim.ad.runner.run_scenario), basic-block graphs run without
    debugging     breakpoints (context menu), step / node step, live wire values (types.summarize)
    custom nodes  create (runtime.create_custom_node), load (python:/rust:/cpp:/matlab:), hot reload

Public API (also used by the tests): new_graph, load_default_stack, open_file, save_file, add_node, connect,
remove_node, delete_selected, validate, set_param, start, pause, stop, single_step, step_node, advance,
toggle_breakpoint, add_probe, snapshot, history, diff, restore, load_custom_node, reload_custom_nodes.
"""

from __future__ import annotations

import dataclasses
import math
import time
import traceback
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from ..theme import ACCENT, BACKGROUND, BORDER, FAIL, MUTED, OK, PANEL, TEXT, WARN

MIME = "application/x-vdsim-spec"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
NODE_W, HEADER_H, ROW_H = 200, 38, 18
PROBE_HISTORY = 3000


def _rt():
    import vdsim.runtime as rt  # registers blocks and loaders
    return rt


def _type_color(type_name):
    from ...framework.types import TYPE_COLORS
    return QtGui.QColor(TYPE_COLORS.get(type_name, "#c8c8c8"))


def _summarize(value):
    from ...framework.types import summarize
    try:
        return summarize(value)
    except Exception:
        return str(value)[:60]


def _numeric(value):
    if isinstance(value, (bool, int, float, np.integer, np.floating)):
        return float(value)
    if isinstance(value, np.ndarray) and value.size:
        return float(value.flat[0])
    for attr in ("v", "value"):
        if isinstance(getattr(value, attr, None), (int, float)):
            return float(getattr(value, attr))
    return None


def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    return value


# ---------------------------------------------------------------------------- graphics items
class PortItem(QtWidgets.QGraphicsEllipseItem):
    R = 5.5

    def __init__(self, node_item, name, port, is_output, index):
        super().__init__(-self.R, -self.R, 2 * self.R, 2 * self.R, node_item)
        self.node_item, self.name, self.port, self.is_output = node_item, name, port, is_output
        self.type = getattr(port, "type", "Any")
        self.setBrush(_type_color(self.type))
        self.setPen(QtGui.QPen(QtGui.QColor(BACKGROUND), 1.2))
        self.setPos(NODE_W if is_output else 0, HEADER_H + ROW_H * index + ROW_H / 2)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.CrossCursor)
        fb = " (Rückführung)" if getattr(port, "feedback", False) else ""
        opt = " (optional)" if getattr(port, "optional", False) else ""
        self.setToolTip(f"{'Ausgang' if is_output else 'Eingang'} {name}: {self.type}{fb}{opt}")
        self.edges = []

    @property
    def endpoint(self):
        return f"{self.node_item.node_id}.{self.name}"


class NodeItem(QtWidgets.QGraphicsObject):
    def __init__(self, editor, node_id):
        super().__init__()
        self.editor, self.node_id = editor, node_id
        node = editor.graph.node(node_id)
        inst = node.instance
        self.title = node.label or (getattr(inst, "LABEL", "") or node.component)
        self.subtitle = (f"{node_id} · v{getattr(inst, 'VERSION', '?')} · {getattr(inst, 'LANGUAGE', '?')}"
                         if inst is not None else f"{node_id} · Fehler")
        self.error = node.error
        ins, outs = editor.graph.ports(node_id)
        self.inputs = {n: PortItem(self, n, p, False, i) for i, (n, p) in enumerate(ins.items())}
        self.outputs = {n: PortItem(self, n, p, True, i) for i, (n, p) in enumerate(outs.items())}
        self.height = HEADER_H + ROW_H * max(len(ins), len(outs), 1) + 6
        self.breakpoint = False
        self.highlight = None          # None | color
        self._moved = False
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | QtWidgets.QGraphicsItem.ItemIsSelectable |
                      QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.setPos(*node.position)
        tip = [f"<b>{self.title}</b>", node.component]
        if node.error:
            tip.append(f"<span style='color:{FAIL}'>{node.error}</span>")
        self.setToolTip("<br>".join(tip))

    def boundingRect(self):
        return QtCore.QRectF(-8, -8, NODE_W + 16, self.height + 16)

    def paint(self, p, option, widget=None):
        rect = QtCore.QRectF(0, 0, NODE_W, self.height)
        border = QtGui.QColor(FAIL if self.error else (ACCENT if self.isSelected() else BORDER))
        width = 2.0 if (self.error or self.isSelected()) else 1.2
        if self.highlight:
            border, width = QtGui.QColor(self.highlight), 3.0
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtGui.QPen(border, width))
        p.setBrush(QtGui.QColor(PANEL))
        p.drawRoundedRect(rect, 6, 6)
        p.setPen(QtGui.QPen(QtGui.QColor(BORDER), 1))
        p.drawLine(QtCore.QPointF(0, HEADER_H - 2), QtCore.QPointF(NODE_W, HEADER_H - 2))
        f = QtGui.QFont(p.font())
        f.setBold(True)
        p.setFont(f)
        p.setPen(QtGui.QColor(TEXT))
        fm = QtGui.QFontMetrics(f)
        p.drawText(QtCore.QPointF(8, 15), fm.elidedText(self.title, QtCore.Qt.ElideRight, NODE_W - 28))
        f.setBold(False)
        f.setPointSizeF(max(6.5, f.pointSizeF() - 1.5))
        p.setFont(f)
        p.setPen(QtGui.QColor(MUTED))
        p.drawText(QtCore.QPointF(8, 30), QtGui.QFontMetrics(f).elidedText(self.subtitle, QtCore.Qt.ElideRight,
                                                                            NODE_W - 12))
        p.setPen(QtGui.QColor(TEXT))
        fm = QtGui.QFontMetrics(f)
        for port in self.inputs.values():
            p.drawText(QtCore.QPointF(10, port.y() + 4), port.name)
        for port in self.outputs.values():
            p.drawText(QtCore.QPointF(NODE_W - 10 - fm.horizontalAdvance(port.name), port.y() + 4), port.name)
        if self.breakpoint:
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(FAIL))
            p.drawEllipse(QtCore.QPointF(NODE_W - 11, 11), 5, 5)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            self._moved = True
            for port in (*self.inputs.values(), *self.outputs.values()):
                for e in port.edges:
                    e.update_path()
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        if self._moved:
            self._moved = False
            for item in self.scene().selectedItems() if self.scene() else [self]:
                if isinstance(item, NodeItem):
                    self.editor.graph.move_node(item.node_id, (item.pos().x(), item.pos().y()))

    def contextMenuEvent(self, ev):
        self.editor.node_context_menu(self.node_id, ev.screenPos())


class EdgeItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, conn, src, dst):
        super().__init__()
        self.conn, self.src, self.dst = conn, src, dst
        self.color = _type_color(src.type)
        self.active = False
        self.setZValue(-1)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.label = QtWidgets.QGraphicsSimpleTextItem("", self)
        self.label.setBrush(QtGui.QColor(TEXT))
        f = self.label.font()
        f.setPointSizeF(7.5)
        self.label.setFont(f)
        src.edges.append(self)
        dst.edges.append(self)
        self.setToolTip(f"{conn.src} → {conn.dst}  [{src.type}]")
        self.update_path()

    def update_path(self):
        a, b = self.src.scenePos(), self.dst.scenePos()
        dx = max(40.0, abs(b.x() - a.x()) * 0.5)
        path = QtGui.QPainterPath(a)
        path.cubicTo(a + QtCore.QPointF(dx, 0), b - QtCore.QPointF(dx, 0), b)
        self.setPath(path)
        mid = path.pointAtPercent(0.5)
        self.label.setPos(mid + QtCore.QPointF(4, -14))
        self._restyle()

    def set_active(self, active):
        if active != self.active:
            self.active = active
            self._restyle()

    def _restyle(self):
        c = QtGui.QColor(self.color)
        if not self.active:
            c.setAlphaF(0.65)
        pen = QtGui.QPen(QtGui.QColor(ACCENT) if self.isSelected() else c, 3.2 if self.active else 1.8)
        if self.isSelected():
            pen.setStyle(QtCore.Qt.DashLine)
        self.setPen(pen)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemSelectedHasChanged:
            self._restyle()
        return super().itemChange(change, value)

    def shape(self):
        s = QtGui.QPainterPathStroker()
        s.setWidth(10)
        return s.createStroke(self.path())

    def detach(self):
        for port in (self.src, self.dst):
            if self in port.edges:
                port.edges.remove(self)


class GraphScene(QtWidgets.QGraphicsScene):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setSceneRect(-2000, -2000, 6000, 4000)
        self.setBackgroundBrush(QtGui.QColor(BACKGROUND))
        self._drag_port, self._temp = None, None

    def drawBackground(self, p, rect):
        super().drawBackground(p, rect)
        p.setPen(QtGui.QPen(QtGui.QColor(PANEL), 1))
        step = 40
        x0, y0 = int(math.floor(rect.left() / step)) * step, int(math.floor(rect.top() / step)) * step
        lines = [QtCore.QLineF(x, rect.top(), x, rect.bottom()) for x in range(x0, int(rect.right()) + 1, step)]
        lines += [QtCore.QLineF(rect.left(), y, rect.right(), y) for y in range(y0, int(rect.bottom()) + 1, step)]
        p.drawLines(lines)

    def _port_at(self, pos):
        for item in self.items(pos):
            if isinstance(item, PortItem):
                return item
        return None

    def mousePressEvent(self, ev):
        port = self._port_at(ev.scenePos()) if ev.button() == QtCore.Qt.LeftButton else None
        if port is not None:
            self._drag_port = port
            self._temp = self.addPath(QtGui.QPainterPath(), QtGui.QPen(QtGui.QColor(ACCENT), 1.6,
                                                                        QtCore.Qt.DashLine))
            ev.accept()
            return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._drag_port is not None:
            a, b = self._drag_port.scenePos(), ev.scenePos()
            if not self._drag_port.is_output:
                a, b = b, a
            dx = max(40.0, abs(b.x() - a.x()) * 0.5)
            path = QtGui.QPainterPath(a)
            path.cubicTo(a + QtCore.QPointF(dx, 0), b - QtCore.QPointF(dx, 0), b)
            self._temp.setPath(path)
            return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self._drag_port is not None:
            start, self._drag_port = self._drag_port, None
            self.removeItem(self._temp)
            self._temp = None
            end = self._port_at(ev.scenePos())
            if end is not None and end is not start and end.is_output != start.is_output:
                src, dst = (start, end) if start.is_output else (end, start)
                self.editor.connect(src.endpoint, dst.endpoint)
            return
        super().mouseReleaseEvent(ev)

    def dragEnterEvent(self, ev):
        ev.setAccepted(ev.mimeData().hasFormat(MIME))

    def dragMoveEvent(self, ev):
        ev.setAccepted(ev.mimeData().hasFormat(MIME))

    def dropEvent(self, ev):
        spec = bytes(ev.mimeData().data(MIME)).decode("utf-8")
        if spec:
            pos = ev.scenePos()
            self.editor.add_node(spec, position=(pos.x() - NODE_W / 2, pos.y() - 15))
            ev.acceptProposedAction()


class GraphView(QtWidgets.QGraphicsView):
    def __init__(self, scene, editor):
        super().__init__(scene)
        self.editor = editor
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setAcceptDrops(True)
        self._pan = None

    def wheelEvent(self, ev):
        f = 1.15 ** (ev.angleDelta().y() / 120.0)
        z = self.transform().m11() * f
        if 0.15 < z < 4.0:
            self.scale(f, f)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.MiddleButton:
            self._pan = ev.position()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._pan is not None:
            d = ev.position() - self._pan
            self._pan = ev.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(d.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(d.y()))
            return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.MiddleButton:
            self._pan = None
            self.unsetCursor()
            return
        super().mouseReleaseEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self.editor.delete_selected()
            return
        if ev.key() == QtCore.Qt.Key_F:
            self.editor.fit_view()
            return
        super().keyPressEvent(ev)


class PaletteTree(QtWidgets.QTreeWidget):
    def mimeTypes(self):
        return [MIME]

    def mimeData(self, items):
        md = QtCore.QMimeData()
        spec = items[0].data(0, QtCore.Qt.UserRole) if items else None
        if spec:
            md.setData(MIME, QtCore.QByteArray(spec.encode("utf-8")))
        return md


class Palette(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.search = QtWidgets.QLineEdit(placeholderText="Komponenten suchen…")
        self.search.setClearButtonEnabled(True)
        self.tree = PaletteTree()
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.tree.itemDoubleClicked.connect(self._double)
        self.search.textChanged.connect(self.filter)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QtWidgets.QLabel("Bibliothek"))
        lay.addWidget(self.search)
        lay.addWidget(self.tree, 1)
        self.specs = []

    def populate(self):
        from ...framework.plugins import available_components
        _rt()
        self.tree.clear()
        groups, seen = {}, set()
        for d in available_components():
            spec = f"{d['kind']}/{d['name']}"
            if spec in seen:
                continue
            seen.add(spec)
            cat = d.get("category") or d["kind"]
            key = f"Grundblöcke: {cat}" if d["kind"] == "node" else cat
            if key not in groups:
                groups[key] = QtWidgets.QTreeWidgetItem([key])
                groups[key].setFlags(QtCore.Qt.ItemIsEnabled)
            it = QtWidgets.QTreeWidgetItem([f"{d.get('label') or d['name']}"])
            it.setData(0, QtCore.Qt.UserRole, spec)
            summary = (d.get("doc") or {}).get("summary", "")
            it.setToolTip(0, f"{spec}  v{d.get('version')}  [{d.get('language')}]\n{summary}".strip())
            it.setData(0, QtCore.Qt.UserRole + 1, f"{spec} {d.get('label', '')} {cat} {d['kind']}".lower())
            groups[key].addChild(it)
            self.specs.append(spec)
        for key in sorted(groups, key=lambda k: (not k.startswith("Grund"), k)):
            self.tree.addTopLevelItem(groups[key])
        self.tree.expandAll()

    def filter(self, text):
        text = text.lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            g = self.tree.topLevelItem(i)
            visible = 0
            for j in range(g.childCount()):
                c = g.child(j)
                hit = not text or text in c.data(0, QtCore.Qt.UserRole + 1)
                c.setHidden(not hit)
                visible += hit
            g.setHidden(visible == 0)

    def _double(self, item):
        spec = item.data(0, QtCore.Qt.UserRole)
        if spec:
            self.editor.add_node(spec, position=self.editor.view_center())


# ---------------------------------------------------------------------------- parameter panel
def _param_child(entry, value):
    name, default = entry["name"], entry.get("default")
    unit = entry.get("unit", "")
    label = entry.get("label") or name
    spec = {"name": name, "title": f"{label} [{unit}]" if unit and unit != "-" else label,
            "tip": entry.get("description", "")}
    value = _plain(value)
    if isinstance(default, dict):
        cur = value if isinstance(value, dict) else {}
        spec.update(type="group", children=[_param_child({"name": k, "default": v}, cur.get(k, v))
                                            for k, v in default.items()])
        return spec
    value = default if value is None else value
    if entry.get("choices"):
        spec.update(type="list", limits=list(entry["choices"]), value=value)
    elif isinstance(default, bool):
        spec.update(type="bool", value=bool(value))
    elif isinstance(default, int):
        spec.update(type="int", value=int(value))
    elif isinstance(default, float):
        spec.update(type="float", value=float(value), decimals=6)
    elif isinstance(default, (list, tuple)):
        spec.update(type="str", value=", ".join(str(v) for v in (value or [])), is_list=True)
    else:
        spec.update(type="str", value="" if value is None else str(value))
    return spec


class ParamPanel(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__()
        from pyqtgraph.parametertree import ParameterTree
        self.editor, self.node_id, self.root, self._busy = editor, None, None, False
        self.header = QtWidgets.QLabel("Kein Knoten ausgewählt")
        self.header.setWordWrap(True)
        self.header.setTextFormat(QtCore.Qt.RichText)
        self.label_edit = QtWidgets.QLineEdit()
        self.period = QtWidgets.QDoubleSpinBox(decimals=4, minimum=0.0, maximum=100.0, singleStep=0.01)
        self.period.setSpecialValueText("Standard")
        self.period.setSuffix(" s")
        form = QtWidgets.QFormLayout()
        form.addRow("Bezeichnung", self.label_edit)
        form.addRow("Periode", self.period)
        self.tree = ParameterTree(showHeader=False)
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addWidget(self.header)
        lay.addLayout(form)
        lay.addWidget(self.tree, 1)
        self.label_edit.editingFinished.connect(self._label)
        self.period.valueChanged.connect(self._period)
        self.setEnabled(False)

    def show_node(self, node_id):
        from pyqtgraph.parametertree import Parameter
        g = self.editor.graph
        self.node_id = node_id if node_id in g.nodes else None
        self._busy = True
        try:
            self.tree.clear()
            self.root = None
            self.setEnabled(self.node_id is not None)
            if self.node_id is None:
                self.header.setText("Kein Knoten ausgewählt")
                return
            info = g.node_info(node_id)
            node = g.node(node_id)
            summary = (info.get("doc") or {}).get("summary", "")
            err = f"<br><span style='color:{FAIL}'>{node.error}</span>" if node.error else ""
            self.header.setText(f"<b>{info.get('label', node_id)}</b> <span style='color:{MUTED}'>({node_id})</span>"
                                f"<br>{node.component} · v{info.get('version', '?')} · {info.get('language', '?')}"
                                f"<br><span style='color:{MUTED}'>{summary}</span>{err}")
            self.label_edit.setText(node.label)
            self.period.setValue(node.period or 0.0)
            kids = []
            for e in info.get("params", []):
                try:
                    cur = g.get_param(node_id, e["name"]) if node.instance is not None else None
                except Exception:
                    cur = None
                kids.append(_param_child(e, cur))
            self.root = Parameter.create(name="params", type="group", children=kids)
            self.root.sigTreeStateChanged.connect(self._changed)
            self.tree.setParameters(self.root, showTop=False)
        finally:
            self._busy = False

    def _changed(self, root, changes):
        if self._busy or self.node_id is None:
            return
        for param, what, data in changes:
            if what != "value":
                continue
            path, p = [], param
            while p is not None and p is not self.root:
                path.insert(0, p.name())
                p = p.parent()
            value = data
            if param.opts.get("is_list"):
                try:
                    value = [float(x) for x in str(data).replace(";", ",").split(",") if x.strip()]
                except ValueError:
                    self.editor.log(f"Ungültige Liste für {'.'.join(path)}: {data}", error=True)
                    continue
            self.editor.set_param(self.node_id, ".".join(path), value)

    def _label(self):
        if self.node_id and not self._busy:
            self.editor.graph.set_label(self.node_id, self.label_edit.text())
            self.editor.refresh_node(self.node_id)

    def _period(self, v):
        if self.node_id and not self._busy:
            self.editor.graph.set_period(self.node_id, v or None)


# ---------------------------------------------------------------------------- dialogs
class CustomNodeDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        from ...framework.layers import LAYER_BASES
        self.setWindowTitle("Neuer Custom Node")
        self.language = QtWidgets.QComboBox()
        for key, text in (("python", "Python"), ("rust", "Rust"), ("cpp", "C++")):
            self.language.addItem(text, key)
        self.name = QtWidgets.QLineEdit("my_node")
        self.kind = QtWidgets.QComboBox()
        self.kind.addItems(["node", *LAYER_BASES])
        self.kind.setCurrentText("tracking_controller")
        self.dest = QtWidgets.QLineEdit(str(PROJECT_ROOT / "custom_nodes"))
        form = QtWidgets.QFormLayout(self)
        form.addRow("Sprache", self.language)
        form.addRow("Name (snake_case)", self.name)
        form.addRow("Ebene / Schnittstelle", self.kind)
        form.addRow("Zielordner", self.dest)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        form.addRow(bb)

    def values(self):
        return self.language.currentData(), self.name.text().strip(), self.kind.currentText(), self.dest.text()


# ---------------------------------------------------------------------------- editor
class NodeEditor(QtWidgets.QWidget):
    TAB_TITLE = "Architektur"
    stack_changed = QtCore.Signal(dict)
    message = QtCore.Signal(str)

    AD_KINDS = {"world", "perception", "predictor", "behavior_planner", "trajectory_planner",
                "tracking_controller", "vehicle_dynamics", "actuator", "vehicle_plant"}

    def __init__(self, parent=None):
        super().__init__(parent)
        rt = _rt()
        self.graph = rt.Graph("neu")
        self.graph.on_change(self._graph_changed)
        self.items, self.edges = {}, []
        self.executor = None
        self.breakpoints = {}                # node_id -> Breakpoint
        self.probe_keys = []
        self.report = None
        self.dirty = False
        self._stack = None
        self._initial_loaded = False
        self._last_wall = None
        self._last_live = 0.0
        self._prev_values = {}
        self._structural = False
        self._build_ui()
        self.sim_timer = QtCore.QTimer(self, interval=30)
        self.sim_timer.timeout.connect(self._on_sim_timer)
        self.reload_timer = QtCore.QTimer(self, interval=1000)
        self.reload_timer.timeout.connect(lambda: self.reload_custom_nodes(force=False, quiet=True))
        self._validate_timer = QtCore.QTimer(self, singleShot=True, interval=150)
        self._validate_timer.timeout.connect(self.validate)
        self._update_sim_buttons()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.scene = GraphScene(self)
        self.scene.selectionChanged.connect(self._selection_changed)
        self.view = GraphView(self.scene, self)
        self.palette = Palette(self)
        self.params = ParamPanel(self)

        tb1, tb2 = QtWidgets.QToolBar(), QtWidgets.QToolBar()
        for tb in (tb1, tb2):
            tb.setIconSize(QtCore.QSize(14, 14))
            tb.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)

        def act(tb, text, slot, tip="", shortcut=None):
            a = tb.addAction(text)
            a.triggered.connect(lambda checked=False: slot())
            if tip:
                a.setToolTip(tip)
            if shortcut:
                a.setShortcut(shortcut)
                a.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            return a

        act(tb1, "Neu", self.new_graph, "Leeren Graphen anlegen")
        act(tb1, "Standard-Stack", self.load_default_stack,
            "Perception → Prediction → Behavior → Trajectory Planning → Vehicle Control → Dynamics → Actuators")
        act(tb1, "Öffnen…", self.open_file, shortcut=QtGui.QKeySequence.Open)
        act(tb1, "Speichern…", self.save_file, shortcut=QtGui.QKeySequence.Save)
        tb1.addSeparator()
        act(tb1, "Validieren", self.validate)
        act(tb1, "Einpassen", self.fit_view, "Ansicht auf alle Knoten einpassen (F)")
        tb1.addSeparator()
        cm = QtWidgets.QMenu(self)
        cm.addAction("Neuer Custom Node…", self.new_custom_node_dialog)
        cm.addAction("Custom Node laden (Datei)…", self.load_custom_node_file)
        cm.addAction("Custom Node laden (Spec)…", self.load_custom_node_spec)
        btn = QtWidgets.QToolButton(text="Custom Node", popupMode=QtWidgets.QToolButton.InstantPopup)
        btn.setMenu(cm)
        tb1.addWidget(btn)
        act(tb1, "Hot Reload", lambda: self.reload_custom_nodes(force=True), "Custom Nodes neu laden")
        self.auto_reload = QtWidgets.QCheckBox("Auto-Reload")
        self.auto_reload.setToolTip("Quelltexte der Custom Nodes zyklisch prüfen und bei Änderung neu laden")
        self.auto_reload.toggled.connect(lambda on: self.reload_timer.start() if on else self.reload_timer.stop())
        tb1.addWidget(self.auto_reload)
        tb1.addSeparator()
        act(tb1, "Stack übernehmen", self.emit_stack, "Ebenen-Knoten des Graphen als Stack an die Workbench geben")

        tb2.addWidget(QtWidgets.QLabel(" Szenario "))
        self.scenario = QtWidgets.QComboBox()
        self.scenario.setMinimumWidth(170)
        self.scenario.setToolTip("Nur für AD-Stacks; Graphen aus Grundblöcken laufen ohne Szenario")
        tb2.addWidget(self.scenario)
        self.a_start = act(tb2, "▶ Start", self.start)
        self.a_pause = act(tb2, "⏸ Pause", self.pause)
        self.a_stop = act(tb2, "⏹ Stopp", self.stop)
        self.a_step = act(tb2, "Schritt", self.single_step, "Einen Basisschritt rechnen")
        self.a_node = act(tb2, "Knotenschritt", self.step_node, "Genau eine Knotenaktion rechnen (Debugger)")
        tb2.addWidget(QtWidgets.QLabel("  Echtzeitfaktor "))
        self.rtf = QtWidgets.QDoubleSpinBox(decimals=2, minimum=0.01, maximum=100.0, value=1.0, singleStep=0.25)
        self.rtf.valueChanged.connect(self._rtf_changed)
        tb2.addWidget(self.rtf)
        self.show_values = QtWidgets.QCheckBox("Werte an Kanten")
        self.show_values.setChecked(True)
        self.show_values.toggled.connect(lambda _: self._update_live(force=True))
        tb2.addWidget(self.show_values)
        self.time_label = QtWidgets.QLabel("  t = –")
        tb2.addWidget(self.time_label)

        # side tabs
        self.side = QtWidgets.QTabWidget()
        self.side.setDocumentMode(True)
        self.side.addTab(self.params, "Parameter")
        self.issues = QtWidgets.QListWidget()
        self.issues.itemClicked.connect(self._issue_clicked)
        self.side.addTab(self.issues, "Validierung")
        self.side.addTab(self._build_debug(), "Debug")
        self.probe_area = QtWidgets.QWidget()
        self.probe_layout = QtWidgets.QVBoxLayout(self.probe_area)
        self.probe_layout.addStretch(1)
        sa = QtWidgets.QScrollArea(widgetResizable=True)
        sa.setWidget(self.probe_area)
        self.side.addTab(sa, "Probes")
        self.profile = QtWidgets.QTableWidget(0, 6)
        self.profile.setHorizontalHeaderLabels(["Knoten", "Aufrufe", "Mittel µs", "p95 µs", "Max µs", "Summe ms"])
        self.profile.verticalHeader().hide()
        self.profile.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.side.addTab(self.profile, "Profiler")
        self.side.addTab(self._build_versions(), "Versionen")
        self.log_view = QtWidgets.QPlainTextEdit(readOnly=True)
        self.log_view.setMaximumBlockCount(2000)
        self.side.addTab(self.log_view, "Meldungen")

        split = QtWidgets.QSplitter()
        split.addWidget(self.palette)
        split.addWidget(self.view)
        split.addWidget(self.side)
        split.setStretchFactor(1, 1)
        split.setSizes([200, 800, 340])
        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet(f"color:{MUTED}")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(tb1)
        lay.addWidget(tb2)
        lay.addWidget(split, 1)
        lay.addWidget(self.status)

    def _build_debug(self):
        w = QtWidgets.QWidget()
        self.inspect_title = QtWidgets.QLabel("Inspektor: Knoten auswählen oder Haltepunkt setzen (Rechtsklick)")
        self.inspect_title.setWordWrap(True)
        self.inspector = QtWidgets.QTreeWidget()
        self.inspector.setHeaderLabels(["Signal", "Wert"])
        self.inspector.setColumnWidth(0, 130)
        self.bp_list = QtWidgets.QListWidget()
        self.bp_list.setMaximumHeight(90)
        row = QtWidgets.QHBoxLayout()
        for text, slot in (("Fortsetzen", self.start), ("Schritt", self.single_step),
                           ("Knotenschritt", self.step_node), ("Haltepunkte löschen", self.clear_breakpoints)):
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(lambda checked=False, s=slot: s())
            row.addWidget(b)
        lay = QtWidgets.QVBoxLayout(w)
        lay.addWidget(self.inspect_title)
        lay.addLayout(row)
        lay.addWidget(self.inspector, 1)
        lay.addWidget(QtWidgets.QLabel("Haltepunkte"))
        lay.addWidget(self.bp_list)
        return w

    def _build_versions(self):
        w = QtWidgets.QWidget()
        self.version_list = QtWidgets.QListWidget()
        self.version_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.diff_view = QtWidgets.QPlainTextEdit(readOnly=True)
        self.diff_view.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        row = QtWidgets.QHBoxLayout()
        for text, slot in (("Snapshot…", self.snapshot_dialog), ("Diff", self._diff_selected),
                           ("Wiederherstellen", self._restore_selected)):
            b = QtWidgets.QPushButton(text)
            b.clicked.connect(lambda checked=False, s=slot: s())
            row.addWidget(b)
        self.version_path = QtWidgets.QLabel("Graph noch nicht gespeichert")
        self.version_path.setStyleSheet(f"color:{MUTED}")
        self.version_path.setWordWrap(True)
        lay = QtWidgets.QVBoxLayout(w)
        lay.addWidget(self.version_path)
        lay.addLayout(row)
        lay.addWidget(self.version_list, 1)
        lay.addWidget(QtWidgets.QLabel("Diff (eine Version: gegen aktuellen Stand; zwei: untereinander)"))
        lay.addWidget(self.diff_view, 1)
        return w

    def showEvent(self, ev):
        super().showEvent(ev)
        if not self._initial_loaded:
            self._initial_loaded = True
            self.palette.populate()
            self._fill_scenarios()
            if not self.graph.nodes:
                try:
                    self.load_default_stack(self._stack)
                except Exception as exc:
                    self.log(f"Standard-Stack konnte nicht geladen werden: {exc}", error=True)

    def _fill_scenarios(self):
        if self.scenario.count():
            return
        try:
            from .workbench import list_scenarios
            for sc in list_scenarios():
                name = sc.get("name") if isinstance(sc, dict) else str(sc)
                label = (sc.get("label") or name) if isinstance(sc, dict) else name
                self.scenario.addItem(label, name)
        except Exception as exc:
            self.log(f"Szenarien nicht verfügbar: {exc}", error=True)

    # ------------------------------------------------------------------ logging
    def log(self, text, error=False):
        stamp = time.strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{stamp}] {'FEHLER: ' if error else ''}{text}")
        self.status.setText(("⚠ " if error else "") + text.splitlines()[0] if text else "")
        self.status.setStyleSheet(f"color:{FAIL if error else MUTED}")
        self.message.emit(text)

    # ------------------------------------------------------------------ workbench protocol
    def set_stack(self, stack):
        self._stack = stack
        if self._initial_loaded and not self.dirty and self.graph.metadata.get("layers") is not None \
                and self.executor is None:
            self.load_default_stack(stack)

    def emit_stack(self):
        from ...ad.stack import LAYERS
        stack = {}
        for layer in LAYERS:
            if layer in self.graph.nodes:
                n = self.graph.node(layer)
                entry = {"component": n.component}
                if n.params:
                    entry["params"] = dict(n.params)
                if n.period:
                    entry["period"] = n.period
                stack[layer] = entry
        if not stack:
            self.log("Der Graph enthält keine Ebenen-Knoten (world, perception, …)", error=True)
            return {}
        self.stack_changed.emit(stack)
        self.log(f"Stack mit {len(stack)} Ebenen an die Workbench übergeben")
        return stack

    # ------------------------------------------------------------------ graph management
    def _set_graph(self, graph):
        self.stop()
        self.graph.remove_listener(self._graph_changed)
        self.graph = graph
        graph.on_change(self._graph_changed)
        self.breakpoints.clear()
        self.dirty = False
        self.rebuild_scene()
        self.validate()
        self._refresh_versions()
        self._refresh_bp_list()
        QtCore.QTimer.singleShot(0, self.fit_view)

    def new_graph(self, name="neu", base_dt=0.01):
        self._set_graph(_rt().Graph(name, base_dt=base_dt))
        self.log("Neuer leerer Graph")
        return self.graph

    def load_default_stack(self, stack=None):
        from ...ad.stack import build_graph
        doc = build_graph(stack if stack is not None else self._stack)
        self._set_graph(_rt().Graph.from_dict(doc))
        self.log(f"Standard-Stack geladen ({len(self.graph.nodes)} Knoten, "
                 f"{len(self.graph.connections)} Verbindungen)")
        return self.graph

    def open_file(self, path=None):
        if path is None:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Graph öffnen", str(PROJECT_ROOT),
                                                            "Graph (*.json)")
            if not path:
                return None
        try:
            g = _rt().Graph.load(path)
        except Exception as exc:
            self.log(f"Öffnen fehlgeschlagen: {exc}", error=True)
            return None
        self._set_graph(g)
        for w in g.load_warnings:
            self.log(w, error=True)
        self.log(f"Geöffnet: {path}")
        return g

    def save_file(self, path=None):
        if path is None:
            start = str(self.graph.path or PROJECT_ROOT / f"{self.graph.name}.json")
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Graph speichern", start, "Graph (*.json)")
            if not path:
                return None
        p = self.graph.save(path)
        self.dirty = False
        self.log(f"Gespeichert: {p}")
        self._refresh_versions()
        return p

    def _graph_changed(self, event, info):
        if event != "move":
            self.dirty = True
        if event in ("param", "period"):
            nid = info.get("node")
            if self.items.get(nid) is not None and self._ports_changed(nid):
                self.refresh_node(nid)
        self._validate_timer.start()

    def _ports_changed(self, nid):
        item = self.items[nid]
        ins, outs = self.graph.ports(nid)
        return list(ins) != list(item.inputs) or list(outs) != list(item.outputs)

    # ------------------------------------------------------------------ scene
    def rebuild_scene(self):
        self.scene.clearSelection()
        for e in self.edges:
            self.scene.removeItem(e)
        for it in self.items.values():
            self.scene.removeItem(it)
        self.items, self.edges = {}, []
        for nid in self.graph.nodes:
            self._add_item(nid)
        for c in self.graph.connections:
            self._add_edge(c)
        self.params.show_node(None)

    def _add_item(self, nid):
        item = NodeItem(self, nid)
        item.breakpoint = nid in self.breakpoints
        self.scene.addItem(item)
        self.items[nid] = item
        return item

    def _add_edge(self, conn):
        s, d = self.items.get(conn.src_node), self.items.get(conn.dst_node)
        if s is None or d is None or conn.src_port not in s.outputs or conn.dst_port not in d.inputs:
            return None
        e = EdgeItem(conn, s.outputs[conn.src_port], d.inputs[conn.dst_port])
        self.scene.addItem(e)
        self.edges.append(e)
        return e

    def _remove_edges_of(self, nid):
        for e in [e for e in self.edges if nid in (e.conn.src_node, e.conn.dst_node)]:
            e.detach()
            self.scene.removeItem(e)
            self.edges.remove(e)

    def refresh_node(self, nid):
        # rebuild one node item (ports / label changed) and its edges
        old = self.items.pop(nid, None)
        selected = old.isSelected() if old else False
        self._remove_edges_of(nid)
        if old is not None:
            self.scene.removeItem(old)
        if nid not in self.graph.nodes:
            return
        item = self._add_item(nid)
        item.setSelected(selected)
        for c in self.graph.connections_of(nid):
            self._add_edge(c)

    def view_center(self):
        c = self.view.mapToScene(self.view.viewport().rect().center())
        return c.x() - NODE_W / 2, c.y() - 30

    def fit_view(self):
        if self.items:
            r = self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
            self.view.fitInView(r, QtCore.Qt.KeepAspectRatio)
            if self.view.transform().m11() > 1.0:
                self.view.resetTransform()
                self.view.centerOn(r.center())

    def _selection_changed(self):
        nodes = [i for i in self.scene.selectedItems() if isinstance(i, NodeItem)]
        nid = nodes[0].node_id if len(nodes) == 1 else None
        if nid != self.params.node_id:
            self.params.show_node(nid)
        if nid and self.executor is not None and self.executor.break_hit is None:
            self._show_inspector(nid)

    def select_node(self, nid, center=True):
        item = self.items.get(nid)
        if item is None:
            return
        self.scene.clearSelection()
        item.setSelected(True)
        if center:
            self.view.centerOn(item)

    # ------------------------------------------------------------------ editing API
    def add_node(self, component, position=None, node_id=None, params=None, strict=False):
        """Add a node (registry spec "kind/name" or custom spec). Returns the node id or None."""
        if position is None:
            position = self.view_center()
        try:
            node = self.graph.add_node(node_id, component, params=params, position=list(position),
                                       strict=strict)
        except Exception as exc:
            self.log(f"Knoten '{component}' kann nicht angelegt werden: {exc}", error=True)
            return None
        self._add_item(node.id)
        if node.error:
            self.log(f"Knoten {node.id}: {node.error}", error=True)
        else:
            self.log(f"Knoten {node.id} ({component}) hinzugefügt")
        self.select_node(node.id, center=False)
        return node.id

    def connect(self, src, dst):
        """Connect "node.out" -> "node.in". Returns (ok, message); type errors are rejected."""
        msg = self.graph.check_connection(src, dst)
        if msg is None and self.graph.source_of(dst) is not None:
            msg = f"Eingang {dst} ist bereits mit {self.graph.source_of(dst)} verbunden (zuerst trennen)"
        if msg:
            self.log(f"Verbindung abgelehnt: {msg}", error=True)
            return False, msg
        try:
            conn = self.graph.connect(src, dst)
        except Exception as exc:
            self.log(f"Verbindung abgelehnt: {exc}", error=True)
            return False, str(exc)
        self._add_edge(conn)
        self.log(f"Verbunden: {src} → {dst}")
        return True, ""

    def disconnect(self, src, dst):
        n = self.graph.disconnect(src, dst)
        for e in [e for e in self.edges if e.conn.src == src and e.conn.dst == dst]:
            e.detach()
            self.scene.removeItem(e)
            self.edges.remove(e)
        return n

    def remove_node(self, nid):
        bp = self.breakpoints.pop(nid, None)
        if bp is not None and self.executor is not None:
            self.executor.remove_breakpoint(bp)
        for key in [k for k in self.probe_keys if k.split(".")[0] == nid]:
            self.remove_probe(key)
        self._remove_edges_of(nid)
        item = self.items.pop(nid, None)
        if item is not None:
            self.scene.removeItem(item)
        self.graph.remove_node(nid)
        self.params.show_node(None)
        self._refresh_bp_list()
        self.log(f"Knoten {nid} gelöscht")

    def delete_selected(self):
        sel = self.scene.selectedItems()
        for e in [i for i in sel if isinstance(i, EdgeItem)]:
            if e in self.edges:
                self.disconnect(e.conn.src, e.conn.dst)
        for n in [i for i in sel if isinstance(i, NodeItem)]:
            self.remove_node(n.node_id)

    def set_param(self, nid, name, value):
        try:
            v = self.graph.set_param(nid, name, value)
            self.log(f"{nid}.{name} = {v}")
            return True
        except Exception as exc:
            self.log(str(exc), error=True)
            return False

    def validate(self):
        self.report = self.graph.validate()
        self.issues.clear()
        bad = set()
        for issue in self.report:
            it = QtWidgets.QListWidgetItem(("✖ " if issue.severity == "error" else "⚠ ") + issue.message)
            it.setForeground(QtGui.QColor(FAIL if issue.severity == "error" else WARN))
            it.setData(QtCore.Qt.UserRole, issue.node or (issue.nodes[0] if issue.nodes else None)
                       or (issue.connection[0].split(".")[0] if issue.connection else None))
            it.setToolTip(issue.message)
            self.issues.addItem(it)
            if issue.severity == "error":
                bad.update([issue.node] if issue.node else issue.nodes)
        if not len(self.report):
            it = QtWidgets.QListWidgetItem("✔ Graph ist gültig")
            it.setForeground(QtGui.QColor(OK))
            self.issues.addItem(it)
        n_err, n_warn = len(self.report.errors), len(self.report.warnings)
        self.side.setTabText(1, f"Validierung ({n_err}/{n_warn})" if len(self.report) else "Validierung")
        for nid, item in self.items.items():
            item.error = self.graph.node(nid).error or (nid in bad)
            item.update()
        return self.report

    def _issue_clicked(self, item):
        nid = item.data(QtCore.Qt.UserRole)
        if nid in self.items:
            self.select_node(nid)

    def node_context_menu(self, nid, screen_pos):
        m = QtWidgets.QMenu(self)
        m.addAction("Haltepunkt entfernen" if nid in self.breakpoints else "Haltepunkt setzen",
                    lambda: self.toggle_breakpoint(nid))
        pm = m.addMenu("Probe auf Ausgang")
        for port in self.graph.ports(nid)[1]:
            key = f"{nid}.{port}"
            pm.addAction(("✓ " if key in self.probe_keys else "") + port,
                         lambda k=key: self.remove_probe(k) if k in self.probe_keys else self.add_probe(k))
        m.addAction("Inspizieren", lambda: (self._show_inspector(nid), self.side.setCurrentIndex(2)))
        node = self.graph.node(nid)
        if ":" in node.component.split("/")[0]:
            m.addAction("Neu laden", lambda: self._reinstantiate(nid))
        m.addSeparator()
        m.addAction("Löschen", lambda: self.remove_node(nid))
        m.exec(screen_pos)

    def _reinstantiate(self, nid):
        try:
            self.graph.reinstantiate(nid)
            self.refresh_node(nid)
            self.log(f"Knoten {nid} neu instanziiert")
        except Exception as exc:
            self.log(f"Neu laden von {nid} fehlgeschlagen: {exc}", error=True)

    # ------------------------------------------------------------------ simulation
    def needs_scenario(self):
        return any(getattr(n.instance, "KIND", "node") in self.AD_KINDS for n in self.graph.nodes.values())

    def _make_context(self):
        from ...framework.context import RunContext
        if not self.needs_scenario():
            return RunContext(dt=self.graph.base_dt)
        self._fill_scenarios()
        name = self.scenario.currentData()
        try:
            from ...ad.runner import _spec_dict
            from ...core.parameters import load_vehicle_preset
            from ...world import build_scenario
            from .workbench import scenario_spec
            spec = _spec_dict(scenario_spec(name) if name else "einscherer")
            seed = int(spec.get("seed", 0)) if isinstance(spec, dict) else 0
            inst = build_scenario(spec, seed=seed)
            veh = (spec.get("vehicle") if isinstance(spec, dict) else None) \
                or getattr(inst, "metadata", {}).get("vehicle") or "mid_size_sedan"
            vehicle = load_vehicle_preset(veh) if isinstance(veh, str) else veh
            self.log(f"Szenario '{name}' geladen (Fahrzeug {veh if isinstance(veh, str) else 'eigen'})")
            return RunContext(dt=self.graph.base_dt, seed=seed, vehicle=vehicle, road=inst.road, scenario=inst)
        except Exception as exc:
            self.log(f"Szenario '{name}' nicht ladbar, Lauf ohne Szenario: {exc}", error=True)
            return RunContext(dt=self.graph.base_dt)

    def ensure_executor(self):
        if self.executor is not None:
            return self.executor
        rep = self.validate()
        if rep.errors:
            self.side.setCurrentIndex(1)
            self.log(f"Simulation nicht möglich: {len(rep.errors)} Fehler im Graphen", error=True)
            return None
        rt = _rt()
        try:
            ex = rt.Executor(self.graph, self._make_context(), recorder=False, profile=True,
                             realtime_factor=self.rtf.value())
            for nid in list(self.breakpoints):
                self.breakpoints[nid] = ex.add_breakpoint(nid, label=f"Haltepunkt {nid}")
            for key in self.probe_keys:
                ex.add_probe(key, history=PROBE_HISTORY)
            ex.reset()
        except Exception as exc:
            self.log(f"Executor-Start fehlgeschlagen: {exc}", error=True)
            self.log(traceback.format_exc())
            return None
        self.executor = ex
        self._prev_values = {}
        self._reset_probe_plots()
        self.log(f"Executor bereit ({len(self.graph.nodes)} Knoten, base_dt={self.graph.base_dt:g} s)")
        self._update_sim_buttons()
        return ex

    def start(self):
        ex = self.ensure_executor()
        if ex is None:
            return False
        if ex.break_hit is not None:
            self._clear_break_highlight()
        ex.resume()
        self._last_wall = time.perf_counter()
        self.sim_timer.start()
        self._update_sim_buttons()
        return True

    def pause(self):
        self.sim_timer.stop()
        if self.executor is not None:
            self.executor.pause()
        self._update_live(force=True)
        self._update_sim_buttons()

    def stop(self):
        self.sim_timer.stop()
        if self.executor is not None:
            try:
                self.executor.close()
            except Exception:
                pass
            self.executor = None
            self.log("Simulation gestoppt")
        self._clear_break_highlight()
        for e in self.edges:
            e.label.setText("")
            e.set_active(False)
        self.time_label.setText("  t = –")
        self._update_sim_buttons()

    def _rtf_changed(self, v):
        if self.executor is not None:
            self.executor.realtime_factor = float(v)

    def _update_sim_buttons(self):
        running = self.sim_timer.isActive()
        self.a_start.setEnabled(not running)
        self.a_pause.setEnabled(running)
        self.a_stop.setEnabled(self.executor is not None)

    def _guard(self, fn):
        try:
            return fn()
        except Exception as exc:
            self.sim_timer.stop()
            self.log(f"Laufzeitfehler bei t={getattr(self.executor, 't', 0):g} s: {exc}", error=True)
            self._update_sim_buttons()
            return None

    def advance(self, wall_dt):
        """Real-time step as done by the timer (used by the tests). Returns the number of base steps."""
        ex = self.ensure_executor()
        if ex is None:
            return 0
        n = self._guard(lambda: ex.advance(wall_dt)) or 0
        self._after_steps()
        return n

    def _on_sim_timer(self):
        now = time.perf_counter()
        dt, self._last_wall = now - (self._last_wall or now), now
        if self.executor is None:
            self.sim_timer.stop()
            return
        self._guard(lambda: self.executor.advance(dt))
        self._after_steps()

    def _after_steps(self):
        ex = self.executor
        if ex is None:
            return
        if ex.break_hit is not None:
            self.sim_timer.stop()
            self._on_break(ex.break_hit)
            self._update_sim_buttons()
        self._update_live(force=not self.sim_timer.isActive())

    def single_step(self):
        ex = self.ensure_executor()
        if ex is None:
            return None
        self.sim_timer.stop()
        self._clear_break_highlight()
        res = self._guard(ex.step)
        self._after_steps()
        self._update_sim_buttons()
        return res

    def step_node(self):
        ex = self.ensure_executor()
        if ex is None:
            return None
        self.sim_timer.stop()
        self._clear_break_highlight()
        res = self._guard(ex.step_node)
        rt = _rt()
        if isinstance(res, rt.NodeStep):
            self._highlight(res.node, ACCENT)
            self._show_inspector(res.node, title=f"Knotenschritt: {res.node} ({res.phase}) bei t={res.t:g} s")
            self.log(f"Knotenschritt {res.node} ({res.phase}), t={res.t:g} s")
        self._after_steps()
        self._update_sim_buttons()
        return res

    # ------------------------------------------------------------------ debugging
    def toggle_breakpoint(self, nid, on=None):
        on = (nid not in self.breakpoints) if on is None else on
        if on and nid not in self.breakpoints:
            bp = self.executor.add_breakpoint(nid, label=f"Haltepunkt {nid}") if self.executor else None
            self.breakpoints[nid] = bp
        elif not on and nid in self.breakpoints:
            bp = self.breakpoints.pop(nid)
            if bp is not None and self.executor is not None:
                self.executor.remove_breakpoint(bp)
        if nid in self.items:
            self.items[nid].breakpoint = nid in self.breakpoints
            self.items[nid].update()
        self._refresh_bp_list()
        return nid in self.breakpoints

    def clear_breakpoints(self):
        for nid in list(self.breakpoints):
            self.toggle_breakpoint(nid, False)

    def _refresh_bp_list(self):
        self.bp_list.clear()
        for nid in self.breakpoints:
            self.bp_list.addItem(f"● {nid}")

    def _on_break(self, hit):
        self.log(str(hit))
        if hit.node:
            self._highlight(hit.node, WARN)
            self.select_node(hit.node)
        self._show_inspector(hit.node, inputs=hit.inputs, title=str(hit))
        self.side.setCurrentIndex(2)

    def _highlight(self, nid, color):
        self._clear_break_highlight()
        if nid in self.items:
            self.items[nid].highlight = color
            self.items[nid].update()

    def _clear_break_highlight(self):
        for it in self.items.values():
            if it.highlight:
                it.highlight = None
                it.update()

    def _show_inspector(self, nid, inputs=None, title=None):
        self.inspector.clear()
        ex = self.executor
        if nid is None or nid not in self.graph.nodes:
            self.inspect_title.setText(title or "Inspektor")
            return
        if ex is None:
            self.inspect_title.setText(f"Inspektor {nid}: Simulation nicht aktiv")
            return
        if inputs is None:
            try:
                inputs = ex.inputs_of(nid)
            except Exception:
                inputs = {}
        self.inspect_title.setText(title or f"Inspektor {nid} bei t={ex.t:g} s")
        for head, values in (("Eingänge", inputs), ("Ausgänge", ex.outputs(nid))):
            top = QtWidgets.QTreeWidgetItem([head, ""])
            for k, v in values.items():
                child = QtWidgets.QTreeWidgetItem([k, _summarize(v)])
                child.setToolTip(1, repr(v)[:2000])
                top.addChild(child)
            self.inspector.addTopLevelItem(top)
            top.setExpanded(True)

    # probes
    def add_probe(self, key):
        if key not in self.probe_keys:
            self.probe_keys.append(key)
            if self.executor is not None:
                self.executor.add_probe(key, history=PROBE_HISTORY)
            self._make_probe_plot(key)
            self.log(f"Probe {key} hinzugefügt")
        return key

    def remove_probe(self, key):
        if key in self.probe_keys:
            self.probe_keys.remove(key)
            if self.executor is not None:
                self.executor.remove_probe(key)
            w = self._probe_plots.pop(key, None)
            if w is not None:
                w[0].setParent(None)
                w[0].deleteLater()

    _probe_plots = None

    def _make_probe_plot(self, key):
        if self._probe_plots is None:
            self._probe_plots = {}
        box = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 4)
        label = QtWidgets.QLabel(key)
        plot = pg.PlotWidget(background=PANEL)
        plot.setFixedHeight(120)
        plot.showGrid(x=True, y=True, alpha=0.12)
        plot.getPlotItem().hideButtons()
        curve = plot.plot(pen=pg.mkPen(_type_color(self._port_type(key)).name(), width=1.6))
        lay.addWidget(label)
        lay.addWidget(plot)
        self.probe_layout.insertWidget(self.probe_layout.count() - 1, box)
        self._probe_plots[key] = (box, label, curve)

    def _reset_probe_plots(self):
        for key, (_, label, curve) in (self._probe_plots or {}).items():
            curve.setData([], [])
            label.setText(key)

    def _port_type(self, key):
        nid, _, port = key.partition(".")
        try:
            return self.graph.ports(nid)[1][port].type
        except Exception:
            return "Any"

    # ------------------------------------------------------------------ live view
    def _update_live(self, force=False):
        ex = self.executor
        now = time.perf_counter()
        if ex is None or (not force and now - self._last_live < 0.1):
            return
        self._last_live = now
        self.time_label.setText(f"  t = {ex.t:.2f} s   Takt {ex.tick}"
                                + (f"   Überläufe {ex.realtime_overruns}" if ex.realtime_overruns else ""))
        show = self.show_values.isChecked()
        for e in self.edges:
            v = ex.values.get(e.conn.src)
            text = _summarize(v)
            e.set_active(v is not None and self._prev_values.get(e.conn.src) != text)
            e.setToolTip(f"{e.conn.src} → {e.conn.dst}  [{e.src.type}]\n{text}")
            e.label.setText(text if show and v is not None else "")
        self._prev_values = {e.conn.src: _summarize(ex.values.get(e.conn.src)) for e in self.edges}
        for key, (_, label, curve) in (self._probe_plots or {}).items():
            probe = ex.probes.get(key)
            if probe is None:
                continue
            label.setText(f"{key} = {probe.text}")
            if probe.history:
                pts = [(t, _numeric(v)) for t, v in probe.history]
                pts = [(t, y) for t, y in pts if y is not None]
                if pts:
                    a = np.asarray(pts)
                    curve.setData(a[:, 0], a[:, 1])
        self._update_profiler()

    def _update_profiler(self):
        if self.executor is None:
            return
        rows = sorted(self.executor.profiler.report().items(), key=lambda kv: -kv[1]["total_ms"])
        self.profile.setRowCount(len(rows))
        for r, (nid, s) in enumerate(rows):
            vals = [nid, f"{s['calls']}", f"{s['mean_us']:.1f}", f"{s['p95_us']:.1f}", f"{s['max_us']:.1f}",
                    f"{s['total_ms']:.2f}"]
            for c, v in enumerate(vals):
                it = QtWidgets.QTableWidgetItem(v)
                if c:
                    it.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.profile.setItem(r, c, it)

    # ------------------------------------------------------------------ versioning
    def store(self, ask=True):
        if self.graph.path is None:
            if not ask or self.save_file() is None:
                return None
        return _rt().VersionStore(self.graph.path, git=False)

    def snapshot(self, message="", ask=False):
        store = self.store(ask=ask)
        if store is None:
            self.log("Snapshot: Graph zuerst speichern", error=True)
            return None
        v = store.snapshot(self.graph, message)
        self.dirty = False
        self.log(f"Snapshot {v.id}: {message}")
        self._refresh_versions()
        return v

    def snapshot_dialog(self):
        msg, ok = QtWidgets.QInputDialog.getText(self, "Snapshot", "Nachricht:")
        if ok:
            self.snapshot(msg, ask=True)

    def history(self):
        store = self.store(ask=False)
        return store.list() if store else []

    def diff(self, a, b=None):
        """Diff between versions a and b; b=None compares against the graph in the editor."""
        from ...runtime.versioning import diff_documents
        store = self.store(ask=False)
        if store is None:
            return None
        d = diff_documents(store.get(a), store.get(b) if b else self.graph.to_dict())
        self.diff_view.setPlainText(f"{a} → {b or 'aktueller Stand'}\n" + (d.text() or "keine Unterschiede"))
        return d

    def restore(self, vid):
        store = self.store(ask=False)
        if store is None:
            return None
        doc, v = store.restore(vid)
        g = _rt().Graph.from_dict(doc, base_dir=self.graph.path.parent)
        g.path = self.graph.path
        self._set_graph(g)
        self.log(f"Version {vid} wiederhergestellt (neuer Snapshot {v.id})")
        return v

    def _refresh_versions(self):
        self.version_list.clear()
        if self.graph.path is None:
            self.version_path.setText("Graph noch nicht gespeichert (Snapshot fragt nach einem Pfad)")
            return
        self.version_path.setText(str(self.graph.path))
        for v in reversed(self.history()):
            it = QtWidgets.QListWidgetItem(f"{v.id}  {v.timestamp.replace('T', ' ')[:19]}  {v.message}")
            it.setData(QtCore.Qt.UserRole, v.id)
            self.version_list.addItem(it)

    def _selected_versions(self):
        return [i.data(QtCore.Qt.UserRole) for i in self.version_list.selectedItems()]

    def _diff_selected(self):
        sel = sorted(self._selected_versions())
        if sel:
            self.diff(sel[0], sel[1] if len(sel) > 1 else None)

    def _restore_selected(self):
        sel = self._selected_versions()
        if sel:
            self.restore(sel[0])

    # ------------------------------------------------------------------ custom nodes
    def new_custom_node_dialog(self):
        dlg = CustomNodeDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.create_custom_node(*dlg.values())

    def create_custom_node(self, language, name, kind="tracking_controller", dest=None):
        try:
            res = _rt().create_custom_node(language, name, kind, dest or PROJECT_ROOT / "custom_nodes")
        except Exception as exc:
            self.log(f"Custom Node konnte nicht angelegt werden: {exc}", error=True)
            return None
        self.log(f"Custom Node angelegt: {res.path} (Spec {res.spec})")
        return self.load_custom_node(res.spec)

    def load_custom_node(self, spec, position=None):
        if not spec or spec.split(":")[0] not in ("python", "rust", "cpp", "matlab"):
            self.log(f"Ungültige Spec '{spec}' (python:datei.py[:Klasse], rust:ordner, cpp:ordner, "
                     f"matlab:datei.m)", error=True)
            return None
        return self.add_node(spec, position=position)

    def load_custom_node_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Custom Node laden", str(PROJECT_ROOT),
            "Custom Nodes (*.py *.m Cargo.toml CMakeLists.txt *.cpp);;Alle Dateien (*)")
        if not path:
            return None
        p = Path(path)
        if p.suffix == ".py":
            spec = f"python:{p.as_posix()}"
        elif p.suffix == ".m":
            spec = f"matlab:{p.as_posix()}"
        elif p.name == "Cargo.toml":
            spec = f"rust:{p.parent.as_posix()}"
        else:
            spec = f"cpp:{p.parent.as_posix()}"
        return self.load_custom_node(spec)

    def load_custom_node_spec(self):
        spec, ok = QtWidgets.QInputDialog.getText(self, "Custom Node laden",
                                                  "Spec (python:datei.py[:Klasse], rust:ordner, cpp:ordner, "
                                                  "matlab:datei.m):", text="python:")
        if ok and spec.strip():
            return self.load_custom_node(spec.strip())
        return None

    def reload_custom_nodes(self, force=True, quiet=False):
        """Hot reload of changed custom nodes (Executor.check_reload / HotReloader)."""
        try:
            if self.executor is not None:
                events = self.executor.check_reload(force=force)
            else:
                if getattr(self, "_reloader", None) is None or self._reloader.graph is not self.graph:
                    self._reloader = _rt().HotReloader(self.graph)
                events = self._reloader.check(force=force)
        except Exception as exc:
            self.log(f"Hot Reload fehlgeschlagen: {exc}", error=True)
            return []
        for ev in events:
            self.log(f"Reload {ev.node}: {ev.message}", error=not ev.ok)
            if ev.node in self.items:
                self.refresh_node(ev.node)
        if not events and not quiet:
            self.log("Hot Reload: keine Änderungen")
        if events:
            self.validate()
        return events

    def closeEvent(self, ev):
        self.stop()
        super().closeEvent(ev)
