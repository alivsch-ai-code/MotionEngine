"""Scenario dashboard: maneuver, model, controllers, actuator latency, environment, simulation settings."""

import inspect
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from ...core.registry import available, get
from ...simulation.scenario import Scenario, ScenarioManager
from ...trajectory import FILE_FILTER, MANEUVER_INFO
from ...vehicle_models import MODEL_LABELS


def _labelled_combo(items):
    # items: [(key, label)]
    combo = QtWidgets.QComboBox()
    for key, label in items:
        combo.addItem(label, key)
    return combo


def _select(combo, key):
    index = combo.findData(key)
    if index >= 0:
        combo.setCurrentIndex(index)


def _spin(value, minimum, maximum, decimals=2, step=0.1, suffix=""):
    spin = QtWidgets.QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setDecimals(decimals)
    spin.setSingleStep(step)
    spin.setValue(value)
    if suffix:
        spin.setSuffix(f" {suffix}")
    return spin


class ScenarioPanel(QtWidgets.QScrollArea):
    trajectory_changed = QtCore.Signal()
    scenario_loaded = QtCore.Signal(object)
    save_requested = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.manager = ScenarioManager()
        self.trajectory_file = ""
        self.extra_friction_patches = []
        body = QtWidgets.QWidget()
        self.setWidget(body)
        layout = QtWidgets.QVBoxLayout(body)

        # library
        lib = QtWidgets.QGroupBox("Szenario-Bibliothek")
        lib_layout = QtWidgets.QGridLayout(lib)
        self.library = QtWidgets.QComboBox()
        self.refresh_library()
        load_btn = QtWidgets.QPushButton("Laden")
        load_btn.clicked.connect(self._load_selected)
        save_btn = QtWidgets.QPushButton("Speichern")
        save_btn.clicked.connect(self.save_to_library)
        lib_layout.addWidget(self.library, 0, 0, 1, 2)
        lib_layout.addWidget(load_btn, 1, 0)
        lib_layout.addWidget(save_btn, 1, 1)
        layout.addWidget(lib)

        # general
        general = QtWidgets.QGroupBox("Allgemein")
        form = QtWidgets.QFormLayout(general)
        self.name = QtWidgets.QLineEdit("Neues Szenario")
        self.description = QtWidgets.QLineEdit()
        self.model = _labelled_combo([(k, MODEL_LABELS.get(k, k)) for k in available("vehicle_model")])
        _select(self.model, "double_track")
        form.addRow("Name", self.name)
        form.addRow("Beschreibung", self.description)
        form.addRow("Fahrzeugmodell", self.model)
        layout.addWidget(general)

        # maneuver
        man = QtWidgets.QGroupBox("Manöver / Trajektorie")
        man_layout = QtWidgets.QVBoxLayout(man)
        items = sorted(MANEUVER_INFO.items(), key=lambda kv: (kv[1]["category"], kv[1]["label"]))
        self.maneuver = _labelled_combo([(k, f"{v['category']}: {v['label']}") for k, v in items])
        self.maneuver.currentIndexChanged.connect(self._build_maneuver_params)
        self.maneuver_info = QtWidgets.QLabel()
        self.maneuver_info.setWordWrap(True)
        self.maneuver_info.setStyleSheet("color: #9a9ca3;")
        self.param_form = QtWidgets.QFormLayout()
        self.param_widgets = {}
        file_row = QtWidgets.QHBoxLayout()
        self.file_label = QtWidgets.QLabel("Keine Datei (Manöver-Generator)")
        import_btn = QtWidgets.QPushButton("Importieren ...")
        import_btn.clicked.connect(self.import_trajectory)
        clear_btn = QtWidgets.QPushButton("Entfernen")
        clear_btn.clicked.connect(lambda: self.set_trajectory_file(""))
        file_row.addWidget(import_btn)
        file_row.addWidget(clear_btn)
        man_layout.addWidget(self.maneuver)
        man_layout.addWidget(self.maneuver_info)
        man_layout.addLayout(self.param_form)
        man_layout.addWidget(QtWidgets.QLabel("Importierte Trajektorie (CSV, JSON, GPS, MATLAB, ROS, OpenDRIVE):"))
        man_layout.addWidget(self.file_label)
        man_layout.addLayout(file_row)
        layout.addWidget(man)

        # controllers
        ctrl = QtWidgets.QGroupBox("Regler / Fahrerassistenz")
        form = QtWidgets.QFormLayout(ctrl)
        self.lateral = _labelled_combo([(k, getattr(get("lateral_controller", k), "label", k))
                                        for k in available("lateral_controller")])
        _select(self.lateral, "stanley")
        self.longitudinal = _labelled_combo([(k, getattr(get("longitudinal_controller", k), "label", k))
                                             for k in available("longitudinal_controller")])
        _select(self.longitudinal, "speed_pi")
        form.addRow("Querführung", self.lateral)
        form.addRow("Längsführung", self.longitudinal)
        layout.addWidget(ctrl)

        # steering actuator / latency chain
        act = QtWidgets.QGroupBox("Lenkaktor und Wirkkette")
        form = QtWidgets.QFormLayout(act)
        self.dead_time = _spin(0.0, 0, 1000, 0, 5, "ms")
        self.tau = _spin(0.0, 0, 1000, 0, 5, "ms")
        self.sensor_delay = _spin(0.0, 0, 1000, 0, 5, "ms")
        self.rate_limit = _spin(0.0, 0, 100, 2, 0.1, "rad/s")
        self.char_error = QtWidgets.QCheckBox("Kennlinienfehler im Aktuator")
        self.k_full_lock = _spin(0.3, 0.01, 1, 3, 0.01, "1/m")
        self.k_full_lock_assumed = _spin(0.2, 0.01, 1, 3, 0.01, "1/m")
        self.error_at_zero = _spin(0.10, 0, 1, 3, 0.01)
        self.feedback = QtWidgets.QCheckBox("Rückkanal-Korrektur (Offset-Schätzer)")
        form.addRow("Stellpfad (Gateway + Aktuator)", self.dead_time)
        form.addRow("Aktordynamik PT1", self.tau)
        form.addRow("Rückkanal (Odometrie + Gateway)", self.sensor_delay)
        form.addRow("Lenkraten-Begrenzung (0 = aus)", self.rate_limit)
        form.addRow(self.char_error)
        form.addRow("Volleinschlag real", self.k_full_lock)
        form.addRow("Volleinschlag Kennlinie", self.k_full_lock_assumed)
        form.addRow("Fehler bei kleiner Krümmung", self.error_at_zero)
        form.addRow(self.feedback)
        layout.addWidget(act)

        # environment
        env = QtWidgets.QGroupBox("Umgebung")
        form = QtWidgets.QFormLayout(env)
        self.mu = _spin(1.0, 0.05, 1.5, 2, 0.05)
        self.split_mu = QtWidgets.QCheckBox("Split-µ (linke Seite)")
        self.mu_left = _spin(0.2, 0.05, 1.5, 2, 0.05)
        self.wind = _spin(0.0, -40, 40, 1, 1, "m/s")
        self.road_class = QtWidgets.QComboBox()
        self.road_class.addItems(["glatt", "A", "B", "C", "D", "E"])
        self.lead = QtWidgets.QCheckBox("Vorausfahrendes Fahrzeug")
        self.lead_gap = _spin(60.0, 1, 500, 1, 5, "m")
        self.lead_v0 = _spin(100.0, 0, 250, 0, 5, "km/h")
        self.lead_v1 = _spin(60.0, 0, 250, 0, 5, "km/h")
        self.lead_t = _spin(8.0, 0, 300, 1, 1, "s")
        form.addRow("Reibwert (Basis)", self.mu)
        form.addRow(self.split_mu, self.mu_left)
        form.addRow("Gegenwind", self.wind)
        form.addRow("Straßenklasse ISO 8608", self.road_class)
        form.addRow(self.lead)
        form.addRow("Abstand", self.lead_gap)
        form.addRow("Geschwindigkeit Start", self.lead_v0)
        form.addRow("Geschwindigkeit Ende", self.lead_v1)
        form.addRow("Bremsbeginn", self.lead_t)
        layout.addWidget(env)

        # simulation
        sim = QtWidgets.QGroupBox("Simulation")
        form = QtWidgets.QFormLayout(sim)
        self.duration = _spin(0.0, 0, 3600, 1, 1, "s (0 = auto)")
        self.dt = _spin(10.0, 0.5, 100, 1, 1, "ms")
        self.solver = QtWidgets.QComboBox()
        self.solver.addItems(["rk4", "heun", "euler", "adaptive"])
        form.addRow("Dauer", self.duration)
        form.addRow("Regler-Takt", self.dt)
        form.addRow("Integrator", self.solver)
        layout.addWidget(sim)
        layout.addStretch()
        self._build_maneuver_params()

    # library
    def refresh_library(self):
        self.library.clear()
        for name in self.manager.names():
            try:
                self.library.addItem(self.manager.load(name).name, name)
            except Exception:
                self.library.addItem(name, name)

    def _load_selected(self):
        name = self.library.currentData()
        if name:
            scenario = self.manager.load(name)
            self.set_scenario(scenario)
            self.scenario_loaded.emit(scenario)

    def save_to_library(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Szenario speichern", "Dateiname (ohne .json):",
                                                  text=self._slug())
        if ok and name:
            self.save_requested.emit(name)

    def _slug(self):
        from ...simulation.scenario import _slug
        return _slug(self.name.text())

    # maneuver parameters
    def _build_maneuver_params(self):
        while self.param_form.rowCount():
            self.param_form.removeRow(0)
        self.param_widgets = {}
        key = self.maneuver.currentData()
        info = MANEUVER_INFO.get(key, {})
        self.maneuver_info.setText(info.get("description", ""))
        fn = get("maneuver", key)
        for name, par in inspect.signature(fn).parameters.items():
            if name in ("steering_ratio", "vehicle_width"):
                continue  # taken from the vehicle
            label, unit = info.get("params", {}).get(name, (name, ""))
            default = par.default
            if isinstance(default, (int, float)) and not isinstance(default, bool):
                widget = _spin(float(default), -1e6, 1e6, 3 if abs(default) < 10 else 1, 1.0, unit)
            else:
                widget = QtWidgets.QLineEdit(str(default))
            self.param_widgets[name] = widget
            self.param_form.addRow(label, widget)
        self.trajectory_changed.emit()

    def maneuver_params(self):
        params = {}
        for name, widget in self.param_widgets.items():
            params[name] = widget.value() if isinstance(widget, QtWidgets.QDoubleSpinBox) else widget.text()
        return params

    # trajectory import
    def import_trajectory(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Trajektorie importieren", str(Path.cwd()), FILE_FILTER)
        if path:
            self.set_trajectory_file(path)

    def set_trajectory_file(self, path):
        self.trajectory_file = path or ""
        self.file_label.setText(Path(path).name if path else "Keine Datei (Manöver-Generator)")
        self.maneuver.setEnabled(not path)
        self.trajectory_changed.emit()

    # scenario <-> widgets
    def environment(self):
        friction = {"base": self.mu.value(), "patches": list(self.extra_friction_patches)}
        if self.split_mu.isChecked():
            friction["patches"].append({"x_min": -1e6, "x_max": 1e6, "y_min": 0.0, "y_max": 1e6,
                                        "mu": self.mu_left.value(), "name": "split-mu"})
        env = {"friction": friction, "wind_speed": self.wind.value()}
        if self.road_class.currentIndex() > 0:
            env["road"] = {"roughness_class": self.road_class.currentText(), "length": 5000}
        if self.lead.isChecked():
            t1 = self.lead_t.value()
            env["lead_vehicle"] = {"initial_gap": self.lead_gap.value(), "time": [0.0, t1, t1 + 5.0, 1e5],
                                   "speed": [self.lead_v0.value() / 3.6, self.lead_v0.value() / 3.6,
                                             self.lead_v1.value() / 3.6, self.lead_v1.value() / 3.6]}
        return env

    def steering_actuator(self):
        return {"dead_time": self.dead_time.value() / 1000, "tau": self.tau.value() / 1000,
                "sensor_delay": self.sensor_delay.value() / 1000, "rate_limit": self.rate_limit.value(),
                "characteristic_error": self.char_error.isChecked(), "k_full_lock": self.k_full_lock.value(),
                "k_full_lock_assumed": self.k_full_lock_assumed.value(), "error_at_zero": self.error_at_zero.value(),
                "feedback_correction": self.feedback.isChecked()}

    def to_scenario(self, vehicle_config):
        return Scenario(name=self.name.text(), description=self.description.text(), vehicle=vehicle_config.to_dict(),
                        model=self.model.currentData(), maneuver=self.maneuver.currentData(),
                        maneuver_params=self.maneuver_params(), trajectory_file=self.trajectory_file,
                        lateral_controller=self.lateral.currentData(),
                        longitudinal_controller=self.longitudinal.currentData(),
                        steering_actuator=self.steering_actuator(), environment=self.environment(),
                        duration=self.duration.value(), dt_control=self.dt.value() / 1000,
                        solver=self.solver.currentText())

    def set_scenario(self, sc):
        self.name.setText(sc.name)
        self.description.setText(sc.description)
        _select(self.model, sc.model)
        _select(self.maneuver, sc.maneuver)
        self._build_maneuver_params()
        for name, value in sc.maneuver_params.items():
            widget = self.param_widgets.get(name)
            if isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.setValue(float(value))
            elif widget is not None:
                widget.setText(str(value))
        self.set_trajectory_file(sc.trajectory_file)
        _select(self.lateral, sc.lateral_controller)
        _select(self.longitudinal, sc.longitudinal_controller)
        act = sc.steering_actuator or {}
        self.dead_time.setValue(act.get("dead_time", 0.0) * 1000)
        self.tau.setValue(act.get("tau", 0.0) * 1000)
        self.sensor_delay.setValue(act.get("sensor_delay", 0.0) * 1000)
        self.rate_limit.setValue(act.get("rate_limit", 0.0))
        self.char_error.setChecked(act.get("characteristic_error", False))
        self.k_full_lock.setValue(act.get("k_full_lock", 0.3))
        self.k_full_lock_assumed.setValue(act.get("k_full_lock_assumed", 0.2))
        self.error_at_zero.setValue(act.get("error_at_zero", 0.1))
        self.feedback.setChecked(act.get("feedback_correction", False))
        env = sc.environment or {}
        friction = env.get("friction", {})
        self.mu.setValue(friction.get("base", 1.0))
        patches = friction.get("patches", [])
        split = [p for p in patches if p.get("name") == "split-mu" or (p.get("y_min") == 0.0 and p.get("y_max", 0) >= 1e5)]
        self.split_mu.setChecked(bool(split))
        if split:
            self.mu_left.setValue(split[0]["mu"])
        self.extra_friction_patches = [p for p in patches if p not in split]
        self.wind.setValue(env.get("wind_speed", 0.0))
        road = env.get("road") or {}
        self.road_class.setCurrentText(road.get("roughness_class") or "glatt")
        lead = env.get("lead_vehicle")
        self.lead.setChecked(bool(lead))
        if lead:
            self.lead_gap.setValue(lead.get("initial_gap", 60.0))
            self.lead_v0.setValue(lead["speed"][0] * 3.6)
            self.lead_v1.setValue(lead["speed"][-1] * 3.6)
            self.lead_t.setValue(lead["time"][1] if len(lead["time"]) > 2 else 8.0)
        self.duration.setValue(sc.duration or 0.0)
        self.dt.setValue((sc.dt_control or 0.01) * 1000)
        self.solver.setCurrentText(sc.solver)
