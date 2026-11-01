"""ADWorkbench: main window of the automated-driving development and simulation platform.

    toolbar        scenario, seed, duration, start (QThread + progress), cancel, load / save result, demo
    stack toolbar  component per layer (from available_components(kind)) + parameter dialog (describe()["params"])
    central tabs   registry TABS of "module:Class" strings, imported lazily; missing modules -> placeholder tab

Tab protocol (all optional, duck typing):
    set_result(result)          receives every new ADResult
    set_stack(stack)            receives the stack dict when it changes
    result_loaded  Signal(obj)  the tab provides an ADResult (e.g. research run) -> shown in all tabs
    time_requested Signal(t)    jump the planner view timeline to t
    stack_changed  Signal(dict) the tab edited the stack (e.g. node editor) -> workbench adopts it
    job_provider                attribute set to ADWorkbench.current_job (base job for experiments)
"""

from __future__ import annotations

import copy
import importlib
import math
import sys
import time
import traceback
from pathlib import Path

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from .style import MUTED, Placeholder

TABS = [
    "vdsim.gui.ad.planner_view:PlannerView",
    "vdsim.gui.ad.run_overview:RunOverview",
    "vdsim.gui.ad.research_panel:ResearchPanel",
    "vdsim.gui.ad.node_editor:NodeEditor",
    "vdsim.gui.ad.matlab_panel:MatlabPanel",
    "vdsim.gui.knowledge:KnowledgeBrowser",
]
TAB_TITLES = {
    "vdsim.gui.ad.planner_view:PlannerView": "Planer && Regler",
    "vdsim.gui.ad.run_overview:RunOverview": "Lauf-Kennwerte",
    "vdsim.gui.ad.research_panel:ResearchPanel": "Forschung",
    "vdsim.gui.ad.node_editor:NodeEditor": "Architektur",
    "vdsim.gui.ad.matlab_panel:MatlabPanel": "MATLAB",
    "vdsim.gui.knowledge:KnowledgeBrowser": "Wissen",
}
# stack layer -> component KIND of the plugin registry
LAYER_KINDS = {"world": "world", "perception": "perception", "prediction": "predictor",
               "behavior": "behavior_planner", "planner": "trajectory_planner", "controller": "tracking_controller",
               "dynamics": "vehicle_dynamics", "actuators": "actuator", "plant": "vehicle_plant"}
DEMO_SCENARIO = "__demo__"


def load_tab(spec):
    # "module:Class" -> (widget, title, error message or "")
    title = TAB_TITLES.get(spec, spec.rsplit(":", 1)[-1])
    module_name, _, cls_name = spec.partition(":")
    try:
        cls = getattr(importlib.import_module(module_name), cls_name)
        widget = cls()
        return widget, getattr(cls, "TAB_TITLE", None) or title, ""
    except Exception as exc:  # missing or broken module must not break the workbench
        reason = f"{type(exc).__name__}: {exc}"
        return Placeholder(title, reason), title, reason


def default_stack():
    try:
        from ...ad.stack import DEFAULT_STACK
        return copy.deepcopy(DEFAULT_STACK)
    except Exception:
        return {}


def components(kind):
    try:
        from ...framework.plugins import available_components
        return available_components(kind)
    except Exception:
        return []


def list_scenarios():
    # library scenarios (api.list_scenarios) followed by the scenario types (also valid scenario names)
    out = []
    try:
        from ...api import list_scenarios as _list
        out = list(_list() or [])
    except Exception:
        pass
    try:
        from ...world import list_scenario_types
        names = {sc.get("name") if isinstance(sc, dict) else str(sc) for sc in out}
        out += [dict(t, label=f"{t.get('label') or t['name']} [Typ]") for t in list_scenario_types()
                if t.get("name") not in names]
    except Exception:
        pass
    return out


def scenario_spec(name):
    # library scenarios by name; scenario types as spec dict (the runner only loads library files by name)
    if not isinstance(name, str) or name == DEMO_SCENARIO:
        return name
    for sc in list_scenarios():
        if isinstance(sc, dict) and sc.get("name") == name and "path" not in sc and "defaults" in sc:
            return {"name": name, "type": name}
    return name


def component_schema(spec):
    try:
        from ...framework.plugins import get_component
        return get_component(spec).describe().get("params", [])
    except Exception:
        return None


# ---------------------------------------------------------------------------- parameter dialog
class ParamDialog(QtWidgets.QDialog):
    """pyqtgraph ParameterTree built from describe()["params"]; values() returns the changed values (nested)."""

    def __init__(self, title, schema, current=None, parent=None):
        super().__init__(parent)
        from pyqtgraph.parametertree import Parameter, ParameterTree
        self.setWindowTitle(f"Parameter: {title}")
        self.resize(520, 600)
        self.schema = schema or []
        self.defaults = {}
        children = [self._child(e, (current or {}).get(e["name"]), self.defaults) for e in self.schema]
        self.root = Parameter.create(name="params", type="group", children=children)
        tree = ParameterTree(showHeader=True)
        tree.setParameters(self.root, showTop=False)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel |
                                             QtWidgets.QDialogButtonBox.RestoreDefaults)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QtWidgets.QDialogButtonBox.RestoreDefaults).setText("Standardwerte")
        buttons.button(QtWidgets.QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout = QtWidgets.QVBoxLayout(self)
        if not self.schema:
            layout.addWidget(QtWidgets.QLabel("Diese Komponente hat keine Parameter (oder ist nicht registriert)."))
        layout.addWidget(tree, 1)
        layout.addWidget(buttons)

    def _child(self, entry, value, defaults):
        name = entry["name"]
        default = entry.get("default")
        unit = entry.get("unit", "")
        label = entry.get("label") or name
        title = f"{label} [{unit}]" if unit and unit != "-" else label
        tip = entry.get("description", "")
        if isinstance(default, dict):
            sub = {}
            defaults[name] = sub
            cur = value if isinstance(value, dict) else {}
            kids = [self._child({"name": k, "default": v, "label": k}, cur.get(k), sub) for k, v in default.items()]
            return {"name": name, "title": title, "type": "group", "children": kids, "tip": tip}
        defaults[name] = default
        value = default if value is None else value
        spec = {"name": name, "title": title, "tip": tip}
        if entry.get("choices"):
            spec.update(type="list", limits=list(entry["choices"]), value=value)
        elif isinstance(default, bool):
            spec.update(type="bool", value=bool(value))
        elif isinstance(default, int):
            spec.update(type="int", value=int(value))
        elif isinstance(default, float):
            spec.update(type="float", value=float(value), decimals=6)
            if "step" in entry:
                spec["step"] = entry["step"]
        elif isinstance(default, (list, tuple)):
            spec.update(type="str", value=", ".join(str(v) for v in value))
        else:
            spec.update(type="str", value="" if value is None else str(value))
        if isinstance(default, (int, float)) and not isinstance(default, bool) and ("min" in entry or "max" in entry):
            spec["limits"] = (entry.get("min", -1e12), entry.get("max", 1e12))
        return spec

    def restore_defaults(self):
        def walk(group, defaults):
            for child in group.children():
                d = defaults.get(child.name())
                if isinstance(d, dict):
                    walk(child, d)
                elif d is not None:
                    child.setValue(", ".join(str(v) for v in d) if isinstance(d, (list, tuple)) else d)
        walk(self.root, self.defaults)

    def values(self, only_changed=True):
        def walk(group, defaults):
            out = {}
            for child in group.children():
                d = defaults.get(child.name())
                if isinstance(d, dict):
                    sub = walk(child, d)
                    if sub or not only_changed:
                        out[child.name()] = sub
                    continue
                v = child.value()
                if isinstance(d, (list, tuple)):
                    try:
                        v = [float(x) for x in str(v).replace(";", ",").split(",") if x.strip()]
                    except ValueError:
                        v = d
                if not only_changed or v != d:
                    out[child.name()] = v
            return out
        return walk(self.root, self.defaults)


# ---------------------------------------------------------------------------- simulation thread
class _Cancelled(Exception):
    pass


class SimWorker(QtCore.QObject):
    progress = QtCore.Signal(float, float)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, run_function, kwargs):
        super().__init__()
        self.run_function = run_function
        self.kwargs = kwargs
        self.cancelled = False

    def _progress(self, t, t_end):
        if self.cancelled:
            raise _Cancelled()
        self.progress.emit(float(t), float(t_end or 0.0))

    @QtCore.Slot()
    def run(self):
        try:
            result = self.run_function(progress=self._progress, **self.kwargs)
            self.finished.emit(result)
        except _Cancelled:
            self.failed.emit("Simulation abgebrochen")
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")


def _default_run(**kwargs):
    if kwargs.get("scenario") == DEMO_SCENARIO:
        from .demo import make_demo_result
        prog = kwargs.get("progress")
        dur = float(kwargs.get("duration") or 12.0)
        if prog:
            prog(0.0, dur)
        res = make_demo_result(duration=dur, seed=int(kwargs.get("seed") or 0))
        if prog:
            prog(dur, dur)
        return res
    from ...ad import run_scenario
    return run_scenario(**kwargs)


# ---------------------------------------------------------------------------- telemetry panel
import pyqtgraph as pg


class TelemetryPanel(QtWidgets.QWidget):
    """Dockable vehicle telemetry: live gauges + signal scope strips."""

    GAUGES = [
        ("v", "Geschwindigkeit", "km/h", lambda e: e.speed * 3.6 if e else 0.0, "{:.1f}"),
        ("ax", "Längsbeschl.", "m/s²", lambda e: e.ax if e else 0.0, "{:.2f}"),
        ("ay", "Querbeschl.", "m/s²", lambda e: e.ay if e else 0.0, "{:.2f}"),
        ("r", "Gierrate", "°/s", lambda e: np.degrees(e.r) if e else 0.0, "{:.1f}"),
        ("delta", "Lenkwinkel", "°", lambda e: np.degrees(e.delta) if e else 0.0, "{:.2f}"),
        ("beta", "Schwimmwinkel", "°", lambda e: np.degrees(np.arctan2(e.vy, max(e.vx, 0.1))) if e and hasattr(e, "vy") else 0.0, "{:.2f}"),
    ]
    SCOPES = [
        ("v", "v [km/h]", 3.6, "#3987e5"),
        ("ax", "a_x [m/s²]", 1.0, "#d95926"),
        ("ay", "a_y [m/s²]", 1.0, "#199e70"),
        ("r", "r [°/s]", np.degrees(1), "#c98500"),
        ("delta", "δ [°]", np.degrees(1), "#d55181"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        gauge_row = QtWidgets.QHBoxLayout()
        gauge_row.setSpacing(2)
        self._gauge_labels = {}
        for key, caption, unit, _, _ in self.GAUGES:
            frame = QtWidgets.QFrame()
            frame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
            fl = QtWidgets.QVBoxLayout(frame)
            fl.setContentsMargins(6, 2, 6, 2)
            fl.setSpacing(0)
            val = QtWidgets.QLabel("-")
            val.setStyleSheet("font-size: 18px; font-weight: bold; color: #3987e5;")
            val.setAlignment(QtCore.Qt.AlignCenter)
            cap = QtWidgets.QLabel(f"{caption} [{unit}]")
            cap.setStyleSheet(f"font-size: 10px; color: {MUTED};")
            cap.setAlignment(QtCore.Qt.AlignCenter)
            fl.addWidget(val)
            fl.addWidget(cap)
            gauge_row.addWidget(frame)
            self._gauge_labels[key] = val
        layout.addLayout(gauge_row)
        scope_widget = pg.GraphicsLayoutWidget()
        scope_widget.setBackground("k")
        self._scope_plots = {}
        self._scope_curves = {}
        self._scope_data = {}
        for i, (key, title, _scale, color) in enumerate(self.SCOPES):
            p = scope_widget.addPlot(row=i, col=0, title=title)
            p.showGrid(x=True, y=True, alpha=0.15)
            p.setLabel("bottom", "t", "s")
            if i > 0:
                p.setXLink(self._scope_plots[self.SCOPES[0][0]])
            curve = p.plot([], [], pen=pg.mkPen(color, width=1.5))
            self._scope_plots[key] = p
            self._scope_curves[key] = curve
            self._scope_data[key] = ([], [])
        layout.addWidget(scope_widget, 1)

    def reset(self):
        for key in self._scope_data:
            self._scope_data[key] = ([], [])
            self._scope_curves[key].setData([], [])
        for lbl in self._gauge_labels.values():
            lbl.setText("-")

    def update_live(self, live, t):
        ego = live.executor.values.get("plant.ego") if live else None
        for key, _caption, _unit, fn, fmt in self.GAUGES:
            try:
                val = fn(ego)
                self._gauge_labels[key].setText(fmt.format(val) if np.isfinite(val) else "-")
            except Exception:
                self._gauge_labels[key].setText("-")
        if ego is None:
            return
        for key, _title, scale, _color in self.SCOPES:
            ts, vs = self._scope_data[key]
            val = getattr(ego, key, None)
            if val is None:
                if key == "v":
                    val = ego.speed if hasattr(ego, "speed") else ego.vx
                else:
                    continue
            ts.append(float(t))
            vs.append(float(val) * scale)
            self._scope_curves[key].setData(ts, vs)

    def update_result(self, result):
        self.reset()
        if result is None:
            return
        try:
            from .data import sig
            t = sig(result, "t")
            if t is None or len(t) < 2:
                return
            for key, _title, scale, _color in self.SCOPES:
                src_key = key if key != "v" else "ego_v"
                y = sig(result, src_key)
                if y is not None:
                    self._scope_data[key] = (list(t), list(y * scale))
                    self._scope_curves[key].setData(t, y * scale)
        except Exception:
            pass


# ---------------------------------------------------------------------------- live simulation
class LiveData:
    """Lightweight stand-in for ResultData during live mode.

    Holds only road geometry, ego dimensions and a mutable reference to the latest
    snapshot.  The TopView, FrenetView etc. call set_time(t, snap) with the snapshot
    we hand them — the heavy signal-array path is never touched.
    """

    def __init__(self, road, ego_dims, snapshots_ref):
        from .data import Polyline
        self.road = road or {}
        dims = ego_dims or {}
        self.ego_length = float(dims.get("length", 4.8))
        self.ego_width = float(dims.get("width", 1.85))
        self.center_offset = float(dims.get("center_offset", 0.15))
        self.cg_to_rear = float(dims.get("cg_to_rear", 1.5))
        self.objects = {}
        self._snapshots_ref = snapshots_ref
        self._lanes = {}
        for lane in self.road.get("lanes", []) or []:
            c = lane.get("center")
            if c is not None and len(c) == 2 and len(c[0]) > 1:
                self._lanes[str(lane.get("id"))] = Polyline(c[0], c[1])
        self._trace_x = []
        self._trace_y = []
        self._ego_x, self._ego_y, self._ego_psi = 0.0, 0.0, 0.0

    @property
    def snapshots(self):
        return self._snapshots_ref

    @property
    def snap_t(self):
        return np.array([s.get("t", 0.0) for s in self._snapshots_ref], dtype=float)

    @property
    def t(self):
        return np.zeros(0)

    @property
    def t0(self):
        return float(self.snap_t[0]) if len(self._snapshots_ref) else 0.0

    @property
    def t1(self):
        return float(self.snap_t[-1]) if len(self._snapshots_ref) else 0.0

    @property
    def plan_period(self):
        st = self.snap_t
        if len(st) > 1:
            d = np.diff(st)
            d = d[np.isfinite(d) & (d > 0)]
            if len(d):
                return float(np.median(d))
        return 0.1

    @property
    def signals(self):
        return {}

    @property
    def events(self):
        return []

    @property
    def metadata(self):
        return {}

    def index(self, t):
        return max(len(self._trace_x) - 1, 0) if self._trace_x else None

    def value(self, key, t, default=np.nan):
        return default

    def snapshot_index(self, t):
        st = self.snap_t
        if not len(st):
            return None
        i = int(np.searchsorted(st, t + 1e-9, side="right") - 1)
        return i if i >= 0 else None

    def snapshot(self, t):
        i = self.snapshot_index(t)
        return self._snapshots_ref[i] if i is not None else None

    def ego_pose(self, t):
        return self._ego_x, self._ego_y, self._ego_psi

    def ego_center(self, x, y, psi):
        return x + self.center_offset * np.cos(psi), y + self.center_offset * np.sin(psi)

    def object_state(self, oid, t):
        return self.objects.get(oid)

    def lane(self, lane_id):
        return self._lanes.get(str(lane_id))

    def reference(self, snap):
        lane_id = ((snap or {}).get("behavior") or {}).get("lane_id")
        ref = self.lane(lane_id)
        if ref is None and self._lanes:
            ref = next(iter(self._lanes.values()))
        return ref

    def name(self, kind, idx):
        return "-"

    def update_ego(self, ego):
        if ego is None:
            return
        self._ego_x = float(ego.x) if math.isfinite(ego.x) else self._ego_x
        self._ego_y = float(ego.y) if math.isfinite(ego.y) else self._ego_y
        self._ego_psi = float(ego.psi) if math.isfinite(ego.psi) else self._ego_psi
        self._trace_x.append(self._ego_x)
        self._trace_y.append(self._ego_y)

    def update_objects(self, world_objects):
        self.objects = {}
        if world_objects is None:
            return
        for o in world_objects:
            self.objects[o.id] = {"x": float(o.x), "y": float(o.y), "psi": float(o.psi),
                                  "v": float(o.v), "type": o.type,
                                  "length": float(o.length), "width": float(o.width)}

    @property
    def trace_xy(self):
        if len(self._trace_x) < 2:
            return None
        return np.array(self._trace_x), np.array(self._trace_y)


class LiveRunner:
    """Drives an Executor step-by-step for live visualization."""

    def __init__(self, scenario, stack, seed, duration, vehicle=None):
        from ...ad.runner import _spec_dict, _road_geometry, _Recorder, _apply_kicks
        from ...ad.results import ADResult
        from ...ad.stack import build_graph, merge_stack
        from ...core.parameters import load_vehicle_preset
        from ...framework.context import RunContext
        from ...runtime import Executor, Graph
        from ...world import build_scenario

        spec = _spec_dict(scenario)
        self.seed = int(seed if seed is not None else (spec.get("seed", 0) if isinstance(spec, dict) else 0))
        inst = build_scenario(spec, seed=self.seed)
        vehicle_name = vehicle or (spec.get("vehicle") if isinstance(spec, dict) else None) \
            or getattr(inst, "metadata", {}).get("vehicle") or "mid_size_sedan"
        vehicle_cfg = load_vehicle_preset(vehicle_name) if isinstance(vehicle_name, str) else vehicle_name
        scen_stack = (spec.get("stack") if isinstance(spec, dict) else None) or \
            getattr(inst, "metadata", {}).get("stack")
        full_stack = merge_stack(scen_stack, stack)
        graph_dict = build_graph(full_stack)
        g = Graph.from_dict(graph_dict)
        g.validate().raise_for_errors()

        context = RunContext(dt=g.base_dt, seed=self.seed, vehicle=vehicle_cfg, road=inst.road, scenario=inst)
        self.executor = Executor(g, context, recorder=False, profile=True, realtime_factor=1.0)
        sc_name = spec.get("name") if isinstance(spec, dict) else str(spec)
        self.result = ADResult(sc_name, spec if isinstance(spec, dict) else {"name": str(spec)}, full_stack, self.seed)
        p = vehicle_cfg.vehicle
        ego_dims = {"length": p.length, "width": p.width, "wheelbase": p.wheelbase,
                     "cg_to_rear": p.cg_to_rear, "center_offset": (p.cg_to_front - p.cg_to_rear) / 2}
        self.result.metadata["ego_dims"] = ego_dims
        self.result.metadata["vehicle"] = vehicle_name if isinstance(vehicle_name, str) else "custom"
        self.recorder = _Recorder(self.result, self.executor, True, vehicle_cfg)
        self.executor.add_listener(step=self.recorder)
        self.t_end = float(duration or getattr(inst, "duration", None) or 30.0)
        road = _road_geometry(inst.road)
        self.result.road = road
        self.live_data = LiveData(road, ego_dims, self.result.snapshots)
        self._apply_kicks = _apply_kicks
        self.stopped = False
        self.stop_reason = ""
        self.executor.reset()

    @property
    def t(self):
        return self.executor.t

    def advance(self, wall_dt):
        if self.stopped:
            return 0
        n = self.executor.advance(wall_dt)
        self._apply_kicks(self.executor, self.recorder)
        self._check_stop()
        return n

    def step_one(self):
        if self.stopped:
            return
        self.executor.step()
        self._apply_kicks(self.executor, self.recorder)
        self._check_stop()

    def _check_stop(self):
        ego = self.executor.values.get("plant.ego")
        if ego is not None and not all(math.isfinite(getattr(ego, f)) for f in ("x", "y", "vx", "psi")):
            self.stopped, self.stop_reason = True, "numerisch instabil"
        if self.recorder.collision:
            self.stopped, self.stop_reason = True, "Kollision"
        if self.recorder.goal:
            self.stopped, self.stop_reason = True, "Ziel erreicht"
        if self.t >= self.t_end - 1e-9:
            self.stopped, self.stop_reason = True, "Simulationsdauer erreicht"
        if ego is not None:
            self.live_data.update_ego(ego)
        world = self.executor.values.get("world.world")
        if world is not None:
            from ...framework.types import WorldState
            if isinstance(world, WorldState):
                self.live_data.update_objects(world.objects)

    def latest_snapshot(self):
        snaps = self.result.snapshots
        return snaps[-1] if snaps else None

    def finalize(self):
        try:
            self.executor.close()
        except Exception:
            pass
        self.result.metadata.update(stop_reason=self.stop_reason,
                                    controllers=self.recorder.controllers,
                                    modes=self.recorder.modes,
                                    maneuvers=self.recorder.maneuvers)
        self.result.finalize()
        try:
            from ...research.metrics import evaluate
            evaluate(self.result)
        except Exception:
            pass


# ---------------------------------------------------------------------------- main window
class ADWorkbench(QtWidgets.QMainWindow):
    result_changed = QtCore.Signal(object)

    def __init__(self, run_function=None, tabs=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("vdsim - Fahrdynamik- und ADAS-Simulationsumgebung")
        self.resize(1680, 1000)
        self.setDockNestingEnabled(True)
        self.run_function = run_function or _default_run
        self.result = None
        self.stack = default_stack()
        self.stack_params = {layer: copy.deepcopy(spec.get("params", {})) for layer, spec in self.stack.items()}
        self._thread = None
        self._worker = None
        self._live = None
        self._live_wall = None
        self._last_view_update = 0.0
        self._last_timeline_update = 0.0
        self._live_timer = QtCore.QTimer(self, interval=30)
        self._live_timer.timeout.connect(self._live_tick)
        self._live_wall = None
        self._build_toolbar()
        self._build_stack_toolbar()
        self._build_tabs(tabs if tabs is not None else TABS)
        self._build_telemetry_dock()
        self._build_menu()
        self.statusBar().showMessage("Bereit")

    # ------------------------------------------------------------------ construction
    def _build_toolbar(self):
        bar = self.addToolBar("Simulation")
        bar.setObjectName("toolbar_ad_simulation")
        bar.setMovable(False)
        bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        style = self.style()
        bar.addWidget(QtWidgets.QLabel(" Szenario "))
        self.scenario = QtWidgets.QComboBox()
        self.scenario.setEditable(True)
        self.scenario.setMinimumWidth(220)
        self.scenario.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.refresh_scenarios()
        bar.addWidget(self.scenario)
        bar.addWidget(QtWidgets.QLabel(" Seed "))
        self.seed = QtWidgets.QSpinBox()
        self.seed.setRange(0, 2 ** 31 - 1)
        bar.addWidget(self.seed)
        bar.addWidget(QtWidgets.QLabel(" Dauer "))
        self.duration = QtWidgets.QDoubleSpinBox()
        self.duration.setRange(0.0, 3600.0)
        self.duration.setDecimals(1)
        self.duration.setSuffix(" s")
        self.duration.setSpecialValueText("Szenario")
        self.duration.setToolTip("0 = Dauer aus dem Szenario")
        bar.addWidget(self.duration)
        bar.addSeparator()
        self.start_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaPlay), "Start", self,
                                          shortcut="F5", triggered=self.start_simulation)
        self.start_action.setObjectName("start")
        self.cancel_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaStop), "Abbrechen", self,
                                           triggered=self.cancel_simulation)
        self.cancel_action.setEnabled(False)
        bar.addAction(self.start_action)
        bar.addAction(self.cancel_action)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumWidth(220)
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setFormat("")
        bar.addWidget(self.progress)
        bar.addSeparator()
        self.live_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaPlay), "Live", self,
                                         shortcut="F6", triggered=self.start_live)
        self.live_action.setToolTip("Live-Simulation: Schritt für Schritt mit Echtzeit-Visualisierung (F6)")
        self.live_pause_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaPause), "Pause", self,
                                                triggered=self.pause_live)
        self.live_pause_action.setEnabled(False)
        self.live_step_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaSeekForward), "Schritt", self,
                                               shortcut="F7", triggered=self.step_live)
        self.live_step_action.setToolTip("Ein Planungsschritt (F7)")
        self.live_step_action.setEnabled(False)
        self.live_stop_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_MediaStop), "Stop", self,
                                               shortcut="F8", triggered=self.stop_live)
        self.live_stop_action.setEnabled(False)
        self.live_speed = QtWidgets.QComboBox()
        for s in (0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 10.0):
            self.live_speed.addItem(f"{s:g}x", s)
        self.live_speed.setCurrentIndex(3)
        self.live_speed.setToolTip("Echtzeit-Faktor der Live-Simulation")
        self.live_speed.currentIndexChanged.connect(self._live_speed_changed)
        bar.addAction(self.live_action)
        bar.addAction(self.live_pause_action)
        bar.addAction(self.live_step_action)
        bar.addAction(self.live_stop_action)
        bar.addWidget(self.live_speed)
        bar.addSeparator()
        self.load_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_DialogOpenButton), "Ergebnis laden",
                                         self, shortcut="Ctrl+O", triggered=lambda: self.load_result())
        self.save_action = QtGui.QAction(style.standardIcon(QtWidgets.QStyle.SP_DialogSaveButton),
                                         "Ergebnis speichern", self, shortcut="Ctrl+S",
                                         triggered=lambda: self.save_result())
        self.demo_action = QtGui.QAction("Demo-Ergebnis", self, triggered=self.load_demo)
        self.demo_action.setToolTip("Synthetisches Ergebnis (Spurwechsel mit Hindernis) anzeigen")
        for a in (self.load_action, self.save_action, self.demo_action):
            bar.addAction(a)

    def _build_stack_toolbar(self):
        self.addToolBarBreak()
        bar = self.addToolBar("Stack")
        bar.setObjectName("toolbar_ad_stack")
        bar.setMovable(False)
        try:
            from ...ad.stack import LAYER_TITLES
        except Exception:
            LAYER_TITLES = {}
        lbl = QtWidgets.QLabel(" Stack ")
        lbl.setStyleSheet("font-weight: bold;")
        bar.addWidget(lbl)
        self.layer_combos = {}
        self.layer_buttons = {}
        for layer, kind in LAYER_KINDS.items():
            box = QtWidgets.QWidget()
            col = QtWidgets.QVBoxLayout(box)
            col.setContentsMargins(2, 0, 2, 0)
            col.setSpacing(0)
            cap = QtWidgets.QLabel(LAYER_TITLES.get(layer, layer))
            cap.setStyleSheet(f"color: {MUTED}; font-size: 10px; background: transparent;")
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(1)
            combo = QtWidgets.QComboBox()
            combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
            combo.setMinimumContentsLength(10)
            combo.setToolTip(f"Komponente der Ebene {LAYER_TITLES.get(layer, layer)} (Typ {kind})")
            self._fill_layer(layer, kind, combo)
            combo.currentIndexChanged.connect(lambda _i, ly=layer: self._layer_changed(ly))
            btn = QtWidgets.QToolButton()
            btn.setText("⚙")
            btn.setToolTip("Parameter ...")
            btn.clicked.connect(lambda _c=False, ly=layer: self.open_param_dialog(ly))
            row.addWidget(combo)
            row.addWidget(btn)
            col.addWidget(cap)
            col.addLayout(row)
            bar.addWidget(box)
            self.layer_combos[layer] = combo
            self.layer_buttons[layer] = btn

    def _fill_layer(self, layer, kind, combo):
        combo.blockSignals(True)
        combo.clear()
        seen = set()
        for d in components(kind):
            base = f"{d.get('kind', kind)}/{d.get('name')}"
            spec = base if base not in seen else f"{base}@{d.get('version')}"
            seen.add(base)
            combo.addItem(f"{d.get('label') or d.get('name')} ({d.get('version', '')})", spec)
            combo.setItemData(combo.count() - 1, (d.get("doc") or {}).get("summary", "") or spec,
                              QtCore.Qt.ToolTipRole)
        current = (self.stack.get(layer) or {}).get("component")
        if current:
            idx = combo.findData(current)
            if idx < 0:
                idx = next((i for i in range(combo.count()) if str(combo.itemData(i)).split("@")[0] == current), -1)
            if idx < 0:
                combo.addItem(current.split("/", 1)[-1], current)
                idx = combo.count() - 1
            combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _build_tabs(self, specs):
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tab_widgets = {}
        self.tab_errors = {}
        for spec in specs:
            widget, title, error = load_tab(spec)
            self.tab_widgets[spec] = widget
            if error:
                self.tab_errors[spec] = error
            self.tabs.addTab(widget, title)
            self._connect_tab(widget)
        self.setCentralWidget(self.tabs)

    def _connect_tab(self, widget):
        if hasattr(widget, "result_loaded"):
            widget.result_loaded.connect(lambda res: self.set_result(res, show_planner=True))
        if hasattr(widget, "time_requested"):
            widget.time_requested.connect(self.jump_to_time)
        if hasattr(widget, "stack_changed"):
            widget.stack_changed.connect(self.apply_stack)
        if hasattr(widget, "job_provider"):
            widget.job_provider = self.current_job
        if hasattr(widget, "set_workbench"):
            widget.set_workbench(self)
        if hasattr(widget, "set_stack"):
            try:
                widget.set_stack(self.current_stack())
            except Exception:
                pass

    def _build_telemetry_dock(self):
        self._telemetry = TelemetryPanel()
        self._telemetry_dock = QtWidgets.QDockWidget("Fahrzeug-Telemetrie", self)
        self._telemetry_dock.setObjectName("dock_telemetry")
        self._telemetry_dock.setWidget(self._telemetry)
        self._telemetry_dock.setMinimumHeight(180)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self._telemetry_dock)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("&Datei")
        for a in (self.load_action, self.save_action, self.demo_action):
            file_menu.addAction(a)
        file_menu.addSeparator()
        file_menu.addAction("Schließen", self.close)
        sim = menu.addMenu("&Simulation")
        sim.addAction(self.start_action)
        sim.addAction(self.cancel_action)
        sim.addSeparator()
        sim.addAction(self.live_action)
        sim.addAction(self.live_pause_action)
        sim.addAction(self.live_step_action)
        sim.addAction(self.live_stop_action)
        sim.addSeparator()
        sim.addAction("Szenarien neu laden", self.refresh_scenarios)
        view = menu.addMenu("&Ansicht")
        for i in range(self.tabs.count()):
            view.addAction(self.tabs.tabText(i), lambda i=i: self.tabs.setCurrentIndex(i))
        view.addSeparator()
        view.addAction(self._telemetry_dock.toggleViewAction())

    # ------------------------------------------------------------------ scenarios / stack
    def refresh_scenarios(self):
        current = self.scenario.currentData() if self.scenario.count() else None
        self.scenario.clear()
        for sc in list_scenarios():
            if isinstance(sc, dict):
                name = sc.get("name") or sc.get("id") or str(sc)
                label = sc.get("title") or sc.get("label") or name
                self.scenario.addItem(label if label == name else f"{label} ({name})", name)
                self.scenario.setItemData(self.scenario.count() - 1, sc.get("description", ""), QtCore.Qt.ToolTipRole)
            else:
                self.scenario.addItem(str(sc), str(sc))
        self.scenario.addItem("Demo (synthetisch, ohne Runner)", DEMO_SCENARIO)
        if current:
            idx = self.scenario.findData(current)
            if idx >= 0:
                self.scenario.setCurrentIndex(idx)

    def current_scenario(self):
        idx = self.scenario.currentIndex()
        text = self.scenario.currentText().strip()
        if idx >= 0 and self.scenario.itemText(idx) == text:
            return self.scenario.itemData(idx)
        return text or DEMO_SCENARIO

    def _layer_changed(self, layer):
        spec = self.layer_combos[layer].currentData()
        if spec != (self.stack.get(layer) or {}).get("component"):
            self.stack_params[layer] = {}
        self.stack.setdefault(layer, {})["component"] = spec
        self._broadcast_stack()

    def current_stack(self):
        out = {}
        for layer, spec in self.stack.items():
            if not spec.get("component"):
                continue
            entry = {"component": spec["component"]}
            if spec.get("period"):
                entry["period"] = spec["period"]
            if self.stack_params.get(layer):
                entry["params"] = copy.deepcopy(self.stack_params[layer])
            out[layer] = entry
        return out

    def apply_stack(self, stack):
        # adopt a stack edited elsewhere (node editor, loaded result)
        for layer, spec in (stack or {}).items():
            spec = {"component": spec} if isinstance(spec, str) else dict(spec)
            self.stack.setdefault(layer, {}).update({k: v for k, v in spec.items() if k != "params"})
            self.stack_params[layer] = copy.deepcopy(spec.get("params", {}))
            if layer in self.layer_combos:
                self._fill_layer(layer, LAYER_KINDS[layer], self.layer_combos[layer])
        self._broadcast_stack(skip_sender=True)

    def _broadcast_stack(self, skip_sender=False):
        stack = self.current_stack()
        for w in self.tab_widgets.values():
            if hasattr(w, "set_stack") and not (skip_sender and w is self.sender()):
                try:
                    w.set_stack(stack)
                except Exception:
                    pass

    def current_job(self):
        return {"scenario": self.current_scenario(), "stack": self.current_stack(), "seed": int(self.seed.value()),
                "duration": float(self.duration.value()) or None}

    def open_param_dialog(self, layer, exec_dialog=True):
        spec = self.layer_combos[layer].currentData() if layer in self.layer_combos else None
        schema = component_schema(spec) if spec else None
        dlg = ParamDialog(f"{layer} - {spec}", schema or [], self.stack_params.get(layer), self)
        if not exec_dialog:
            return dlg
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            merged = copy.deepcopy(self.stack_params.get(layer) or {})
            merged.update(dlg.values())
            self.stack_params[layer] = merged
            self._broadcast_stack()
            self.statusBar().showMessage(f"Parameter von {layer} übernommen")
        return dlg

    # ------------------------------------------------------------------ simulation
    def start_simulation(self):
        if self._thread is not None:
            return
        job = self.current_job()
        kwargs = {"scenario": scenario_spec(job["scenario"]), "stack": job["stack"], "seed": job["seed"],
                  "duration": job["duration"], "record_snapshots": True}
        self._worker = SimWorker(self.run_function, kwargs)
        self._thread = QtCore.QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread_done)
        self.start_action.setEnabled(False)
        self.cancel_action.setEnabled(True)
        self.progress.setValue(0)
        self.progress.setFormat("läuft ...")
        self.statusBar().showMessage(f"Simulation von {job['scenario']} läuft ...")
        self._thread.start()

    def cancel_simulation(self):
        if self._worker is not None:
            self._worker.cancelled = True
            self.statusBar().showMessage("Abbruch angefordert ...")

    @property
    def running(self):
        return self._thread is not None

    def wait_for_simulation(self, timeout_ms=60000):
        # helper for scripts and tests: process events until the simulation thread finished
        timer = QtCore.QElapsedTimer()
        timer.start()
        while self._thread is not None and timer.elapsed() < timeout_ms:
            QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)
            QtCore.QThread.msleep(5)
        return self._thread is None

    def _on_progress(self, t, t_end):
        if t_end > 0:
            self.progress.setValue(int(1000 * min(t / t_end, 1.0)))
            self.progress.setFormat(f"{t:.1f} / {t_end:.1f} s")

    def _on_finished(self, result):
        self.progress.setValue(1000)
        self.progress.setFormat("fertig")
        self.set_result(result, show_planner=True)
        wall = (getattr(result, "metadata", {}) or {}).get("wall_time")
        self.statusBar().showMessage(f"Simulation abgeschlossen: {getattr(result, 'name', '')}"
                                     + (f" ({wall:.2f} s Rechenzeit)" if wall else ""))

    def _on_failed(self, message):
        self.progress.setFormat("Fehler" if "abgebrochen" not in message else "abgebrochen")
        first = message.splitlines()[0] if message else "Fehler"
        self.statusBar().showMessage(f"Simulation fehlgeschlagen: {first}")
        self.last_error = message

    def _thread_done(self):
        self._thread.deleteLater()
        self._thread = None
        self._worker = None
        self.start_action.setEnabled(True)
        self.cancel_action.setEnabled(False)

    # ------------------------------------------------------------------ live simulation
    def _init_live_view(self):
        pv = self.planner_view
        if pv is None:
            return
        ld = self._live.live_data
        pv.data = ld
        pv.stack.setCurrentIndex(1)
        pv.top.set_data(ld)
        pv.top.fit()
        pv.top.set_follow(True)
        pv.timeline.set_range(0.0, self._live.t_end, 0.1)
        pv.timeline.set_time(0.0, emit=False)
        self._live_scrub = False
        if hasattr(pv.timeline, "time_changed"):
            try:
                pv.timeline.time_changed.disconnect(self._live_scrub_time)
            except (TypeError, RuntimeError):
                pass
            pv.timeline.time_changed.connect(self._live_scrub_time)
        if hasattr(self, "_telemetry"):
            self._telemetry.reset()

    def start_live(self):
        if self._thread is not None:
            return
        if self._live is not None and not self._live_timer.isActive():
            self._live_scrub = False
            self._live_wall = time.perf_counter()
            self._live_timer.start()
            self._update_live_buttons(running=True)
            self.statusBar().showMessage(f"Live fortgesetzt bei t = {self._live.t:.2f} s")
            return
        if self._live is not None:
            return
        job = self.current_job()
        try:
            self._live = LiveRunner(
                scenario=scenario_spec(job["scenario"]),
                stack=job["stack"], seed=job["seed"],
                duration=job["duration"],
            )
        except Exception as exc:
            self.statusBar().showMessage(f"Live-Start fehlgeschlagen: {exc}")
            self._live = None
            return
        self._live.executor.realtime_factor = float(self.live_speed.currentData() or 1.0)
        self._live_wall = time.perf_counter()
        self._last_view_update = 0.0
        self._last_timeline_update = 0.0
        self._init_live_view()
        self._live_timer.start()
        self._update_live_buttons(running=True)
        self.start_action.setEnabled(False)
        self.statusBar().showMessage(f"Live-Simulation von {job['scenario']} gestartet ...")

    def pause_live(self):
        self._live_timer.stop()
        self._update_live_buttons(running=False)
        self.statusBar().showMessage(
            f"Live pausiert bei t = {self._live.t:.2f} s" if self._live else "Pausiert")

    def step_live(self):
        if self._live is None:
            job = self.current_job()
            try:
                self._live = LiveRunner(
                    scenario=scenario_spec(job["scenario"]),
                    stack=job["stack"], seed=job["seed"],
                    duration=job["duration"],
                )
            except Exception as exc:
                self.statusBar().showMessage(f"Live-Start fehlgeschlagen: {exc}")
                return
            self._last_view_update = 0.0
            self._last_timeline_update = 0.0
            self._init_live_view()
            self._update_live_buttons(running=False)
            self.start_action.setEnabled(False)
        self._live_timer.stop()
        dt = self._live.executor.graph.base_dt
        plan_steps = max(int(round(0.1 / dt)), 1)
        for _ in range(plan_steps):
            if self._live.stopped:
                break
            self._live.step_one()
        self._live_update_view(force=True)
        self._update_live_buttons(running=False)
        if self._live.stopped:
            self._live_finished()

    def _cleanup_live_signals(self):
        self._live_scrub = False
        pv = self.planner_view
        if pv is not None and hasattr(pv.timeline, "time_changed"):
            try:
                pv.timeline.time_changed.disconnect(self._live_scrub_time)
            except (TypeError, RuntimeError):
                pass

    def stop_live(self):
        self._live_timer.stop()
        self._cleanup_live_signals()
        if self._live is not None:
            self._live.finalize()
            result = self._live.result
            self._live = None
            self.set_result(result, show_planner=True)
            self.statusBar().showMessage(
                f"Live beendet: {getattr(result, 'name', '')} ({result.duration:.1f} s)")
        self._update_live_buttons(running=False)
        self.start_action.setEnabled(True)

    def _live_tick(self):
        if self._live is None:
            self._live_timer.stop()
            return
        now = time.perf_counter()
        wall_dt = now - (self._live_wall or now)
        self._live_wall = now
        try:
            self._live.advance(wall_dt)
        except Exception as exc:
            self._live_timer.stop()
            self.statusBar().showMessage(f"Live-Fehler: {exc}")
            self._update_live_buttons(running=False)
            return
        self._live_update_view()
        if self._live.stopped:
            self._live_finished()

    def _live_scrub_time(self, t):
        if self._live is None:
            return
        self._live_scrub = True
        self._live_scrub_t = float(t)
        self._live_update_view(force=True)

    def _live_update_view(self, force=False):
        if self._live is None:
            return
        now = time.perf_counter()
        if not force and now - getattr(self, "_last_view_update", 0.0) < 0.066:
            return
        self._last_view_update = now
        t_sim = self._live.t
        t_end = self._live.t_end
        self.progress.setValue(int(1000 * min(t_sim / max(t_end, 1e-9), 1.0)))
        self.progress.setFormat(f"Live {t_sim:.1f} / {t_end:.1f} s")
        pv = self.planner_view
        if pv is None:
            return
        ld = self._live.live_data
        if getattr(self, "_live_scrub", False):
            t = self._live_scrub_t
        else:
            t = t_sim
        snap = ld.snapshot(t) if getattr(self, "_live_scrub", False) else self._live.latest_snapshot()
        trace = ld.trace_xy
        if trace is not None:
            pv.top._trace_xy = trace
        pv.top.set_time(t, snap)
        if force or now - getattr(self, "_last_timeline_update", 0.0) > 0.5:
            self._last_timeline_update = now
            pv.timeline.set_range(ld.t0, max(ld.t1, t_sim), ld.plan_period)
            if not getattr(self, "_live_scrub", False):
                pv.timeline.set_time(t_sim, emit=False)
        i = ld.snapshot_index(t)
        if force or i != pv._snap_index:
            pv.frenet.set_time(t, snap)
            pv.cost.set_time(t, snap)
        pv.constraints.set_time(t, snap)
        pv.controller.set_time(t, snap)
        pv.commands.set_time(t, snap)
        pv._snap_index = i
        pv._update_info(t, snap)
        if hasattr(self, "_telemetry"):
            self._telemetry.update_live(self._live, t)

    def _live_finished(self):
        self._live_timer.stop()
        self._cleanup_live_signals()
        if self._live is not None:
            self._live.finalize()
            result = self._live.result
            self._live = None
            self.set_result(result, show_planner=True)
            reason = (result.metadata or {}).get("stop_reason", "")
            self.statusBar().showMessage(f"Live beendet: {reason} ({result.duration:.1f} s)")
        self._update_live_buttons(running=False)
        self.start_action.setEnabled(True)
        self.progress.setFormat("fertig")
        self.progress.setValue(1000)

    def _live_speed_changed(self, _idx):
        if self._live is not None:
            self._live.executor.realtime_factor = float(self.live_speed.currentData() or 1.0)

    def _update_live_buttons(self, running=False):
        has_live = self._live is not None
        paused = has_live and not running
        self.live_action.setEnabled((not has_live and self._thread is None) or paused)
        self.live_pause_action.setEnabled(running)
        self.live_step_action.setEnabled(has_live or self._thread is None)
        self.live_stop_action.setEnabled(has_live)

    # ------------------------------------------------------------------ results
    def set_result(self, result, show_planner=False):
        self.result = result
        for spec, w in self.tab_widgets.items():
            if hasattr(w, "set_result"):
                try:
                    w.set_result(result)
                except Exception as exc:
                    self.statusBar().showMessage(f"Tab {spec}: {exc}")
        if show_planner and self.planner_view is not None:
            self.tabs.setCurrentWidget(self.planner_view)
        self.result_changed.emit(result)
        if hasattr(self, "_telemetry"):
            self._telemetry.update_result(result)
        if result is not None:
            self.setWindowTitle(f"vdsim - {getattr(result, 'name', '') or 'Ergebnis'}")

    @property
    def planner_view(self):
        return self.tab_widgets.get("vdsim.gui.ad.planner_view:PlannerView")

    def jump_to_time(self, t):
        pv = self.planner_view
        if pv is not None and hasattr(pv, "set_time"):
            pv.set_time(float(t))
            self.tabs.setCurrentWidget(pv)

    def load_demo(self):
        from .demo import make_demo_result
        self.set_result(make_demo_result(), show_planner=True)
        self.statusBar().showMessage("Synthetisches Demo-Ergebnis geladen")

    def load_result(self, path=None):
        if path is None:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Ergebnis laden", "",
                                                            "AD-Ergebnis (*.npz *.json);;Alle Dateien (*)")
            if not path:
                return None
        from ...ad.results import ADResult
        try:
            result = ADResult.load(path)
        except Exception as exc:
            self.statusBar().showMessage(f"Laden fehlgeschlagen: {exc}")
            return None
        self.set_result(result, show_planner=True)
        self.statusBar().showMessage(f"Ergebnis geladen: {path}")
        return result

    def save_result(self, path=None):
        if self.result is None:
            self.statusBar().showMessage("Kein Ergebnis zum Speichern")
            return None
        if path is None:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Ergebnis speichern", "ergebnis.npz",
                                                            "AD-Ergebnis (*.npz)")
            if not path:
                return None
        out = self.result.save(path)
        self.statusBar().showMessage(f"Ergebnis gespeichert: {out} (+ .json)")
        return out

    def closeEvent(self, event):
        self._live_timer.stop()
        if self._live is not None:
            try:
                self._live.executor.close()
            except Exception:
                pass
            self._live = None
        if self._worker is not None:
            self._worker.cancelled = True
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(3000)
        super().closeEvent(event)


def main(argv=None):
    from ...core.logging_setup import setup_logging
    from ..theme import apply_theme
    argv = list(sys.argv if argv is None else argv)
    try:
        setup_logging()
    except Exception:
        pass
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(argv)
    app.setApplicationName("vdsim AD-Workbench")
    apply_theme(app)
    win = ADWorkbench()
    paths = [a for a in argv[1:] if not a.startswith("-")]
    if paths and Path(paths[0]).with_suffix(".json").exists():
        win.load_result(paths[0])
    elif "--demo" in argv:
        win.load_demo()
    win.show()
    return app.exec()
