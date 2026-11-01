"""Interactive knowledge-graph view (QGraphicsView): force layout, movable nodes, zoom, click signals."""

from __future__ import annotations

import math

from PySide6 import QtCore, QtGui, QtWidgets

from ...knowledge.graph import NODE_COLORS, force_layout


class EdgeItem(QtWidgets.QGraphicsLineItem):
    def __init__(self, a, b, edge_type):
        super().__init__()
        self.a, self.b, self.edge_type = a, b, edge_type
        self.setPen(QtGui.QPen(QtGui.QColor(150, 150, 160, 90), 1.0))
        self.setZValue(-1)
        self.setToolTip(edge_type)
        self.update_position()

    def update_position(self):
        self.setLine(QtCore.QLineF(self.a.pos(), self.b.pos()))

    def highlight(self, on):
        self.setPen(QtGui.QPen(QtGui.QColor(57, 135, 229, 230) if on else QtGui.QColor(150, 150, 160, 90),
                               2.0 if on else 1.0))


class NodeItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, view, node, radius=7.0):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.view, self.node_id, self.edges = view, node.id, []
        self.setBrush(QtGui.QColor(NODE_COLORS.get(node.type, "#888888")))
        self.setPen(QtGui.QPen(QtGui.QColor("#1e1f22"), 1.0))
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | QtWidgets.QGraphicsItem.ItemIsSelectable
                      | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setToolTip(f"{node.label}\n{node.id}\n{node.data.get('summary', '')}"[:400])
        self.label = QtWidgets.QGraphicsSimpleTextItem(node.label, self)
        self.label.setBrush(QtGui.QColor("#e6e6e6"))
        font = self.label.font()
        font.setPointSizeF(7.5)
        self.label.setFont(font)
        self.label.setPos(radius + 2, -radius)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.view.node_clicked.emit(self.node_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.view.node_activated.emit(self.node_id)
        super().mouseDoubleClickEvent(event)


class GraphView(QtWidgets.QGraphicsView):
    node_clicked = QtCore.Signal(str)
    node_activated = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setBackgroundBrush(QtGui.QColor("#1e1f22"))
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.items_by_id = {}

    def show_graph(self, graph, center=None, iterations=150):
        # graph: KnowledgeGraph (typically a neighborhood); deterministic layout
        scene = self.scene()
        scene.clear()
        self.items_by_id = {}
        ids = list(graph.nodes)
        index = {nid: i for i, nid in enumerate(ids)}
        edges = [(index[e.source], index[e.target]) for e in graph.edges]
        pos = force_layout(len(ids), edges, iterations=iterations, seed=0) if ids else []
        size = 120.0 * math.sqrt(max(len(ids), 1))
        for i, nid in enumerate(ids):
            item = NodeItem(self, graph.nodes[nid], 10.0 if nid == center else 7.0)
            item.setPos(float(pos[i][0]) * size, float(pos[i][1]) * size)
            if nid == center:
                item.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 2.0))
            scene.addItem(item)
            self.items_by_id[nid] = item
        for e in graph.edges:
            a, b = self.items_by_id[e.source], self.items_by_id[e.target]
            edge = EdgeItem(a, b, e.type)
            a.edges.append(edge)
            b.edges.append(edge)
            scene.addItem(edge)
            if center in (e.source, e.target):
                edge.highlight(True)
        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-80, -80, 80, 80))
        self.fitInView(scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
