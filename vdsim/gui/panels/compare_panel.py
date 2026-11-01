"""Run comparison: keeps the finished runs, KPI comparison table and comparison plot."""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6 import QtCore, QtWidgets

from ...reporting import compare
from ...visualization import plotter


class ComparePanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        layout = QtWidgets.QHBoxLayout(self)
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Simulationsläufe (für Vergleich anhaken)"))
        self.list = QtWidgets.QListWidget()
        left.addWidget(self.list, 1)
        for text, slot in (("Vergleichen", self.compare_selected), ("Entfernen", self.remove_selected),
                           ("Lauf laden ...", self.load_run), ("Lauf speichern ...", self.save_run)):
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(slot)
            left.addWidget(btn)
        layout.addLayout(left, 1)
        right = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.table = QtWidgets.QTableWidget(0, 0)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        right.addWidget(self.table)
        self.canvas = FigureCanvasQTAgg(plt.figure())
        right.addWidget(self.canvas)
        right.setSizes([300, 500])
        layout.addWidget(right, 3)

    def add_result(self, result):
        self.results.append(result)
        item = QtWidgets.QListWidgetItem(f"{len(self.results)}: {result.name}")
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked)
        self.list.addItem(item)

    def selected(self):
        return [self.results[i] for i in range(self.list.count())
                if self.list.item(i).checkState() == QtCore.Qt.Checked]

    def compare_selected(self):
        results = self.selected()
        if not results:
            return
        table = compare(results)
        self.table.clear()
        self.table.setColumnCount(2 + len(results))
        self.table.setHorizontalHeaderLabels(["Kennwert", "Einheit"] + [r.name for r in results])
        self.table.setRowCount(len(table))
        for row, entry in enumerate(table.values()):
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(entry["label"]))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(entry["unit"]))
            for col, value in enumerate(entry["values"]):
                text = "-" if value is None else value if isinstance(value, str) else f"{value:.3g}"
                self.table.setItem(row, 2 + col, QtWidgets.QTableWidgetItem(text))
        self.table.resizeColumnsToContents()
        old = self.canvas.figure
        fig = plotter.compare_figure(results)
        self.canvas.figure = fig
        fig.set_canvas(self.canvas)
        plt.close(old)
        self.canvas.draw_idle()

    def remove_selected(self):
        for i in reversed(range(self.list.count())):
            if self.list.item(i).checkState() == QtCore.Qt.Checked:
                self.list.takeItem(i)
                del self.results[i]

    def load_run(self):
        from ...simulation.results import SimulationResult
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Lauf laden", "", "Ergebnisse (*.npz *.json)")
        if path:
            self.add_result(SimulationResult.load(path))

    def save_run(self):
        rows = self.list.selectedIndexes()
        if not rows and not self.results:
            return
        result = self.results[rows[0].row()] if rows else self.results[-1]
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Lauf speichern", f"{result.name}.npz",
                                                        "NumPy (*.npz);;JSON (*.json);;CSV (*.csv)")
        if path:
            result.save(path)
