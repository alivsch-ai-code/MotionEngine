"""Vehicle parameter editor: preset selection, parameter tree (vehicle, tires, chassis, powertrain, brakes,
control systems), JSON import/export."""

from pathlib import Path

from PySide6 import QtCore, QtWidgets
from pyqtgraph.parametertree import ParameterTree

from ...core.parameters import VehicleConfig, default_config_dir
from ..param_tree import config_to_parameter, parameter_to_config


class VehiclePanel(QtWidgets.QWidget):
    config_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QHBoxLayout()
        self.preset = QtWidgets.QComboBox()
        self.preset_dir = default_config_dir() / "vehicles"
        for path in sorted(self.preset_dir.glob("*.json")):
            try:
                self.preset.addItem(VehicleConfig.load(path).vehicle.name, str(path))
            except Exception:
                self.preset.addItem(path.stem, str(path))
        self.preset.currentIndexChanged.connect(self._load_preset)
        top.addWidget(QtWidgets.QLabel("Preset"))
        top.addWidget(self.preset, 1)
        layout.addLayout(top)
        self.tree = ParameterTree(showHeader=False)
        layout.addWidget(self.tree, 1)
        buttons = QtWidgets.QHBoxLayout()
        for text, slot in (("Importieren ...", self.import_config), ("Exportieren ...", self.export_config),
                           ("Als Preset speichern", self.save_preset)):
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(slot)
            buttons.addWidget(btn)
        layout.addLayout(buttons)
        self.config = VehicleConfig()
        self._load_preset()

    def _load_preset(self):
        path = self.preset.currentData()
        if path:
            self.set_config(VehicleConfig.load(path))

    def set_config(self, config):
        self.config = config
        self.params = config_to_parameter(config)
        self.params.sigTreeStateChanged.connect(lambda *_: self.config_changed.emit())
        self.tree.setParameters(self.params, showTop=False)
        for group in self.params.children():
            group.setOpts(expanded=group.name() in ("vehicle", "systems"))
        self.config_changed.emit()

    def get_config(self):
        return parameter_to_config(self.params, self.config)

    def import_config(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Fahrzeug importieren", str(self.preset_dir), "JSON (*.json)")
        if path:
            self.set_config(VehicleConfig.load(path))

    def export_config(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Fahrzeug exportieren", str(self.preset_dir), "JSON (*.json)")
        if path:
            self.get_config().save(path)

    def save_preset(self):
        config = self.get_config()
        name, ok = QtWidgets.QInputDialog.getText(self, "Preset speichern", "Dateiname (ohne .json):")
        if ok and name:
            path = self.preset_dir / f"{name}.json"
            config.save(path)
            self.preset.blockSignals(True)
            self.preset.addItem(config.vehicle.name, str(path))
            self.preset.setCurrentIndex(self.preset.count() - 1)
            self.preset.blockSignals(False)

    def select_preset_by_path(self, path):
        index = self.preset.findData(str(Path(path)))
        if index >= 0:
            self.preset.setCurrentIndex(index)
