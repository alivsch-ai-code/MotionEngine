"""Analysis tab: matplotlib engineering plots (overview, tires, Pacejka curves, GGV, Bode, quasi-static,
heatmaps, energy) for the last run and the current vehicle configuration."""

import matplotlib
from PySide6 import QtWidgets

matplotlib.use("QtAgg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT  # noqa: E402

from ...visualization import plotter  # noqa: E402

PLOTS = [("overview", "Übersicht Zustandsgrößen", True), ("tires", "Reifen: Radlasten, Schlupf, Ausnutzung", True),
         ("heatmaps", "Heatmaps: Reifenbelastung, Reibwertnutzung, Stabilität", True), ("ggv", "GGV-Diagramm", True),
         ("energy", "Energie und Leistung", True), ("suspension", "Federwege und Aufbaubewegung", True), ("pacejka", "Reifenkennlinien (Modell)", False),
         ("bode", "Bode-Diagramm (lineares Einspurmodell)", False),
         ("quasi_static", "Quasi-statisch: Radlasten, Wanken, Sturz", False)]


class AnalysisPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        bar = QtWidgets.QHBoxLayout()
        self.kind = QtWidgets.QComboBox()
        for key, label, _ in PLOTS:
            self.kind.addItem(label, key)
        self.kind.currentIndexChanged.connect(self.refresh)
        refresh = QtWidgets.QPushButton("Aktualisieren")
        refresh.clicked.connect(self.refresh)
        save = QtWidgets.QPushButton("Als Bild speichern ...")
        save.clicked.connect(self.save_figure)
        bar.addWidget(QtWidgets.QLabel("Darstellung"))
        bar.addWidget(self.kind, 1)
        bar.addWidget(refresh)
        bar.addWidget(save)
        layout.addLayout(bar)
        self.canvas_holder = QtWidgets.QVBoxLayout()
        layout.addLayout(self.canvas_holder, 1)
        self.canvas = self.toolbar = None
        self.result = None
        self.config_provider = None

    def set_result(self, result):
        self.result = result
        self.refresh()

    def refresh(self):
        key = self.kind.currentData()
        needs_result = dict((k, r) for k, _, r in PLOTS)[key]
        if needs_result and self.result is None:
            fig = plt.figure()
            fig.text(0.5, 0.5, "Noch kein Simulationsergebnis", ha="center")
        else:
            try:
                fig = self._figure(key)
            except Exception as exc:
                fig = plt.figure()
                fig.text(0.5, 0.5, f"Darstellung nicht möglich: {exc}", ha="center", wrap=True)
        self._show(fig)

    def _figure(self, key):
        r = self.result
        config = self.config_provider() if self.config_provider else None
        if key == "overview":
            return plotter.overview_figure(r)
        if key == "tires":
            return plotter.tire_figure(r)
        if key == "heatmaps":
            return plotter.heatmap_figure(r)
        if key == "energy":
            return plotter.energy_figure(r)
        if key == "suspension":
            return plotter.suspension_figure(r)
        if key == "ggv":
            fig, ax = plt.subplots(figsize=(8, 7), layout="constrained")
            plotter.plot_ggv(ax, r, config.tires.mu if config else 1.0)
            return fig
        if key == "pacejka":
            return plotter.plot_tire_curves(config.tires)
        if key == "bode":
            return plotter.plot_bode(config, (10.0, 20.0, 30.0, 40.0))
        if key == "quasi_static":
            return plotter.quasi_static_figure(config)
        raise ValueError(key)

    def _show(self, fig):
        for widget in (self.canvas, self.toolbar):
            if widget is not None:
                self.canvas_holder.removeWidget(widget)
                widget.deleteLater()
        if self.canvas is not None:
            plt.close(self.canvas.figure)
        self.canvas = FigureCanvasQTAgg(fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.canvas_holder.addWidget(self.toolbar)
        self.canvas_holder.addWidget(self.canvas, 1)
        self.canvas.draw_idle()

    def save_figure(self):
        if self.canvas is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Bild speichern", "", "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if path:
            self.canvas.figure.savefig(path, dpi=150)
