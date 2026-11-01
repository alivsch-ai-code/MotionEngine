"""Main window: dockable setup panels, live/analysis tabs, toolbar and menus; runs the simulation
step by step in the GUI loop so all views update in real time."""

import time
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.logging_setup import get_logger
from ..core.parameters import VehicleConfig, load_vehicle_preset
from ..reporting import evaluate
from ..simulation.scenario import Scenario
from ..simulation.simulator import Simulator
from ..visualization.dashboard import GaugeRow, SignalScope, VehicleTopView, make_3d_view
from .panels.analysis_panel import AnalysisPanel
from .panels.compare_panel import ComparePanel
from .panels.kpi_panel import KPIPanel
from .panels.log_panel import LogPanel
from .panels.scenario_panel import ScenarioPanel
from .panels.trajectory_editor import TrajectoryEditorPanel
from .panels.vehicle_panel import VehiclePanel

log = get_logger("gui")
TICK_MS = 30


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("vdsim - Fahrdynamik- und ADAS-Simulationsumgebung")
        self.resize(1680, 980)
        self.setDockNestingEnabled(True)
        self.sim = None
        self.paused = False
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)

        # central tabs
        self.top_view = VehicleTopView()
        self.gauges = GaugeRow()
        live = QtWidgets.QWidget()
        live_layout = QtWidgets.QVBoxLayout(live)
        live_layout.addWidget(self.gauges)
        live_layout.addWidget(self.top_view, 1)
        self.scope = SignalScope()
        self.view3d = make_3d_view()
        self.analysis = AnalysisPanel()
        self.kpi = KPIPanel()
        self.compare = ComparePanel()
        self.editor = TrajectoryEditorPanel()
        self.tabs = QtWidgets.QTabWidget()
        for widget, title in ((live, "Live"), (self.scope, "Signale"), (self.view3d, "3D"), (self.analysis, "Analyse"),
                              (self.kpi, "Kennwerte"), (self.compare, "Vergleich"), (self.editor, "Trajektorien-Editor")):
            self.tabs.addTab(widget, title)
        self.setCentralWidget(self.tabs)

        # docks
        self.scenario_panel = ScenarioPanel()
        self.vehicle_panel = VehiclePanel()
        self.log_panel = LogPanel()
        self.scenario_dock = self._dock("Szenario", self.scenario_panel, QtCore.Qt.LeftDockWidgetArea)
        self.vehicle_dock = self._dock("Fahrzeug", self.vehicle_panel, QtCore.Qt.LeftDockWidgetArea)
        self.tabifyDockWidget(self.scenario_dock, self.vehicle_dock)
        self.scenario_dock.raise_()
        self.log_dock = self._dock("Protokoll", self.log_panel, QtCore.Qt.BottomDockWidgetArea)
        self.log_dock.setMaximumHeight(160)

        self._build_toolbar()
        self._build_menu()
        self.statusBar().showMessage("Bereit")

        # wiring
        self.analysis.config_provider = self.vehicle_panel.get_config
        self.editor.scenario_trajectory_provider = self._current_trajectory
        self.scenario_panel.trajectory_changed.connect(self._preview_trajectory)
        self.scenario_panel.scenario_loaded.connect(self._apply_scenario_vehicle)
        self.scenario_panel.save_requested.connect(self.save_scenario_to_library)
        self.vehicle_panel.config_changed.connect(lambda: self._vehicle_timer.start(400))
        self.editor.use_trajectory.connect(self._use_editor_trajectory)
        self.editor.friction_changed.connect(self._use_friction)
        self._vehicle_timer = QtCore.QTimer(self, singleShot=True)
        self._vehicle_timer.timeout.connect(self._vehicle_changed)
        self._vehicle_changed()
        self._preview_trajectory()

        self.settings = QtCore.QSettings("vdsim", "vdsim")
        self._default_state = self.saveState()
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
            self.restoreState(self.settings.value("state"))

    # construction helpers
    def _dock(self, title, widget, area):
        dock = QtWidgets.QDockWidget(title, self)
        dock.setObjectName(f"dock_{title}")
        dock.setWidget(widget)
        dock.setMinimumWidth(380)
        self.addDockWidget(area, dock)
        return dock

    def _build_toolbar(self):
        bar = self.addToolBar("Simulation")
        bar.setObjectName("toolbar_simulation")
        bar.setMovable(False)
        style = self.style()
        self.start_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaPlay), "Start", self,
                                          shortcut="F5", triggered=self.start_simulation)
        self.pause_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaPause), "Pause", self,
                                          shortcut="F6", triggered=self.pause_simulation)
        self.stop_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaStop), "Stop", self,
                                         shortcut="F7", triggered=self.stop_simulation)
        bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        for action in (self.start_action, self.pause_action, self.stop_action):
            bar.addAction(action)
        bar.addSeparator()
        bar.addWidget(QtWidgets.QLabel(" Wiedergabe "))
        self.speed = QtWidgets.QComboBox()
        for label, factor in (("Echtzeit", 1.0), ("2-fach", 2.0), ("5-fach", 5.0), ("Maximal", 0.0)):
            self.speed.addItem(label, factor)
        self.speed.setCurrentIndex(3)
        bar.addWidget(self.speed)
        self.follow = QtWidgets.QCheckBox("Kamera folgt")
        self.follow.setChecked(True)
        self.follow.toggled.connect(lambda on: setattr(self.top_view, "follow", on))
        bar.addWidget(self.follow)
        bar.addSeparator()
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumWidth(260)
        bar.addWidget(self.progress)
        self.sim_label = QtWidgets.QLabel("")
        bar.addWidget(self.sim_label)
        self._set_running(False)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&Datei")
        for text, slot, shortcut in (("Szenario öffnen ...", self.open_scenario, "Ctrl+O"),
                                     ("Szenario speichern unter ...", self.save_scenario_as, "Ctrl+S"),
                                     (None, None, None),
                                     ("Trajektorie importieren ...", self.scenario_panel.import_trajectory, "Ctrl+I"),
                                     ("Fahrzeug importieren ...", self.vehicle_panel.import_config, None),
                                     ("Fahrzeug exportieren ...", self.vehicle_panel.export_config, None),
                                     (None, None, None),
                                     ("Ergebnis exportieren (CSV/JSON/NPZ) ...", self.export_result, "Ctrl+E"),
                                     ("PDF-Bericht erstellen ...", self.export_pdf, "Ctrl+P"),
                                     ("Engineering Summary (Markdown) ...", self.export_summary, None),
                                     ("Animation exportieren (GIF) ...", self.export_animation, None),
                                     (None, None, None),
                                     ("Beenden", self.close, "Ctrl+Q")):
            if text is None:
                file_menu.addSeparator()
                continue
            action = file_menu.addAction(text, slot)
            if shortcut:
                action.setShortcut(shortcut)
        sim_menu = menu.addMenu("&Simulation")
        for action in (self.start_action, self.pause_action, self.stop_action):
            sim_menu.addAction(action)
        view_menu = menu.addMenu("&Ansicht")
        for dock in (self.scenario_dock, self.vehicle_dock, self.log_dock):
            view_menu.addAction(dock.toggleViewAction())
        view_menu.addSeparator()
        view_menu.addAction("Layout zurücksetzen", lambda: self.restoreState(self._default_state))
        ad_menu = menu.addMenu("&Automatisiertes Fahren")
        ad_action = ad_menu.addAction("AD-Workbench öffnen (Editor, Planer, MATLAB, Forschung) ...",
                                      self._open_ad_workbench)
        ad_action.setShortcut("Ctrl+Shift+A")
        ad_menu.addAction("Wissensbrowser (Doku, Quellen, Wissensgraph) ...", self._open_knowledge)
        help_menu = menu.addMenu("&Hilfe")
        help_menu.addAction("Architektur-Dokumentation", self._open_docs)
        help_menu.addAction("Über vdsim", self._about)

    # scenario / vehicle wiring
    def _current_trajectory(self):
        # trajectory of the current scenario settings (maneuver or imported file)
        try:
            config = self.vehicle_panel.get_config()
            return self.scenario_panel.to_scenario(config).build_trajectory(config)
        except Exception as exc:
            log.warning("Trajektorie kann nicht erzeugt werden: %s", exc)
            return None

    def _preview_trajectory(self):
        if self.timer.isActive():
            return
        traj = self._current_trajectory()
        self.top_view.set_trajectory(traj)
        self.view3d.set_trajectory(traj)

    def _apply_scenario_vehicle(self, scenario):
        if isinstance(scenario.vehicle, dict):
            config = VehicleConfig.from_dict(scenario.vehicle)
        else:
            config = load_vehicle_preset(scenario.vehicle)
        for dotted, value in scenario.vehicle_overrides.items():
            group, name = dotted.split(".", 1)
            setattr(getattr(config, group), name, value)
        self.vehicle_panel.set_config(config)
        self.editor.set_patches(self.scenario_panel.extra_friction_patches)
        self._preview_trajectory()
        self.statusBar().showMessage(f"Szenario geladen: {scenario.name}")

    def _vehicle_changed(self):
        config = self.vehicle_panel.get_config()
        self.kpi.show_vehicle(config)
        self.top_view.set_vehicle(config)
        self.view3d.set_vehicle(config)

    def _use_editor_trajectory(self, path):
        self.scenario_panel.set_trajectory_file(path)
        self.statusBar().showMessage(f"Editor-Trajektorie übernommen: {Path(path).name}")

    def _use_friction(self, patches):
        self.scenario_panel.extra_friction_patches = patches
        self.statusBar().showMessage(f"Reibwertkarte übernommen ({len(patches)} Flächen)")

    def save_scenario_to_library(self, name):
        scenario = self.scenario_panel.to_scenario(self.vehicle_panel.get_config())
        self.scenario_panel.manager.save(scenario, name)
        self.scenario_panel.refresh_library()
        self.statusBar().showMessage(f"Szenario gespeichert: {name}.json")

    def open_scenario(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Szenario öffnen", str(self.scenario_panel.manager.directory),
                                                        "Szenario (*.json)")
        if path:
            scenario = Scenario.load(path)
            self.scenario_panel.set_scenario(scenario)
            self._apply_scenario_vehicle(scenario)

    def save_scenario_as(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Szenario speichern", str(self.scenario_panel.manager.directory),
                                                        "Szenario (*.json)")
        if path:
            self.scenario_panel.to_scenario(self.vehicle_panel.get_config()).save(path)
            self.scenario_panel.refresh_library()

    # simulation control
    def _set_running(self, running):
        self.start_action.setEnabled(not running or self.paused)
        self.pause_action.setEnabled(running and not self.paused)
        self.stop_action.setEnabled(running)

    def start_simulation(self):
        if self.sim is not None and self.paused and not self.sim.finished:
            self.paused = False
            self.timer.start(TICK_MS)
            self._set_running(True)
            return
        config = self.vehicle_panel.get_config()
        scenario = self.scenario_panel.to_scenario(config)
        try:
            self.sim = Simulator.from_scenario(scenario)
        except Exception as exc:
            log.exception("Szenario kann nicht gestartet werden")
            QtWidgets.QMessageBox.critical(self, "Szenario fehlerhaft", str(exc))
            return
        self.top_view.set_vehicle(config)
        self.top_view.set_trajectory(self.sim.trajectory)
        self.view3d.set_vehicle(config)
        self.view3d.set_trajectory(self.sim.trajectory)
        self.scope.clear()
        self.progress.setValue(0)
        self.paused = False
        self._wall_start = time.perf_counter()
        log.info("Start: %s (%s, %s)", scenario.name, scenario.model, scenario.maneuver)
        self.timer.start(TICK_MS)
        self._set_running(True)

    def pause_simulation(self):
        if self.sim is not None and not self.sim.finished:
            self.paused = True
            self.timer.stop()
            self._set_running(True)
            self.statusBar().showMessage(f"Pausiert bei t = {self.sim.t:.2f} s")

    def stop_simulation(self):
        if self.sim is not None and not self.sim.finished:
            self.sim.finished, self.sim.stop_reason = True, "vom Benutzer gestoppt"
            self._finish()

    def _tick(self):
        sim = self.sim
        factor = self.speed.currentData()
        deadline = time.perf_counter() + 0.8 * TICK_MS / 1000
        target = sim.t + factor * TICK_MS / 1000 if factor else float("inf")
        try:
            while not sim.finished and sim.t < target - 1e-9 and time.perf_counter() < deadline:
                sim.step()
        except Exception as exc:
            self.timer.stop()
            log.exception("Simulationsfehler")
            QtWidgets.QMessageBox.critical(self, "Simulationsfehler", str(exc))
            sim.finished, sim.stop_reason = True, f"Fehler: {exc}"
        state = sim.state
        lead = None
        if sim.env.lead_vehicle is not None:
            point = sim.trajectory.at(sim.env.lead_vehicle.s)
            lead = (point["x"], point["y"])
        self.gauges.update_state(state)
        self.top_view.update_state(state, sim.u.steer_front, lead)
        current = self.tabs.currentWidget()
        if current is self.view3d:
            self.view3d.update_state(state, sim.u.steer_front)
        elif current is self.scope:
            self.scope.update_result(sim.result)
        self.progress.setValue(int(100 * min(sim.t / sim.duration, 1.0)))
        self.sim_label.setText(f"  t = {sim.t:6.2f} s")
        if sim.finished:
            self._finish()

    def _finish(self):
        self.timer.stop()
        sim = self.sim
        result = sim.result
        result.metadata.update(stop_reason=sim.stop_reason, wall_time=time.perf_counter() - self._wall_start,
                               energy_drive=sim.actuation.powertrain.energy_drive,
                               energy_regen=sim.actuation.powertrain.energy_regen)
        kpis = evaluate(result)
        self.kpi.show_kpis(kpis, sim.stop_reason)
        self.scope.update_result(result)
        self.analysis.set_result(result)
        self.compare.add_result(result)
        self.progress.setValue(100)
        self._set_running(False)
        self.paused = False
        self.statusBar().showMessage(f"Fertig: {result.name} - {sim.stop_reason} (t = {sim.t:.2f} s)")
        log.info("Fertig: %s (%s)", result.name, sim.stop_reason)

    # export
    def _last_result(self):
        if not self.compare.results:
            QtWidgets.QMessageBox.information(self, "Kein Ergebnis", "Bitte zuerst eine Simulation ausführen.")
            return None
        return self.compare.results[-1]

    def export_result(self):
        result = self._last_result()
        if result is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Ergebnis exportieren", f"{result.name}.csv",
                                                        "CSV (*.csv);;JSON (*.json);;NumPy (*.npz)")
        if path:
            result.save(path)
            self.statusBar().showMessage(f"Ergebnis exportiert: {path}")

    def export_pdf(self):
        results = self.compare.selected() or ([self._last_result()] if self._last_result() else [])
        if not results:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "PDF-Bericht", "bericht.pdf", "PDF (*.pdf)")
        if path:
            from ..reporting.report_generator import generate_pdf
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                generate_pdf(results, path)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
            self.statusBar().showMessage(f"PDF-Bericht erstellt: {path}")
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))

    def export_summary(self):
        results = self.compare.selected() or ([self._last_result()] if self._last_result() else [])
        if not results:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Engineering Summary", "summary.md", "Markdown (*.md)")
        if path:
            from ..reporting.report_generator import save_summary
            save_summary(results, path)
            self.statusBar().showMessage(f"Engineering Summary erstellt: {path}")

    def export_animation(self):
        result = self._last_result()
        if result is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Animation exportieren", f"{result.name}.gif", "GIF (*.gif)")
        if path:
            from ..visualization.animation import save_animation
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                save_animation(result, path, fps=15)
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
            self.statusBar().showMessage(f"Animation gespeichert: {path}")

    # misc
    def _open_docs(self):
        path = Path(__file__).resolve().parents[2] / "docs" / "ARCHITECTURE.md"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))

    def _open_ad_workbench(self):
        # separate main window of the automated-driving platform (kept alive as an attribute)
        try:
            from .ad.workbench import ADWorkbench
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "AD-Workbench", f"AD-Workbench nicht verfügbar:\n{exc}")
            return
        if getattr(self, "_ad_window", None) is None:
            self._ad_window = ADWorkbench()
        self._ad_window.show()
        self._ad_window.raise_()

    def _open_knowledge(self):
        try:
            from .knowledge import KnowledgeBrowser
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Wissensbrowser", f"Wissensbrowser nicht verfügbar:\n{exc}")
            return
        if getattr(self, "_knowledge_window", None) is None:
            self._knowledge_window = KnowledgeBrowser()
            self._knowledge_window.setWindowTitle("vdsim – Wissensbrowser")
            self._knowledge_window.resize(1400, 900)
        self._knowledge_window.show()
        self._knowledge_window.raise_()

    def _about(self):
        from .. import __version__
        QtWidgets.QMessageBox.about(self, "Über vdsim",
                                    f"vdsim {__version__}\nFahrdynamik- und ADAS-Simulationsumgebung\n\n"
                                    "Einspur-, Zweispur- und Mehrkörpermodelle, Pacejka-/Bürstenreifen,\n"
                                    "Bahnregler (Stanley, Pure Pursuit, MPC), ACC/AEB/LKA, ABS/ASR/ESP,\n"
                                    "Hinterachslenkung, Torque Vectoring, aktives Fahrwerk.")

    def closeEvent(self, event):
        self.timer.stop()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        super().closeEvent(event)
