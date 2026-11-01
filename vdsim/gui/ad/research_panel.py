"""ResearchPanel: research mode of the workbench.

    experiments   controller / planner comparison, parameter sweep (<= 2 parameters), Monte Carlo, batch
    execution     vdsim.research.run_batch in a QThread (worker processes configurable)
    dashboard     KPI table (labels/units from kpi_label), KPI bars over variants, sweep heatmap, Monte Carlo
                  histogram + statistics + sensitivities, safety / tracking small multiples, cost-term shares,
                  runtime benchmarking per node
    export        CSV / JSON; a click on a saved run loads it into the planner view (result_loaded)
"""

from __future__ import annotations

import re
import tempfile
import time
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from .run_overview import fill, kpi_meta, table
from .style import BLUE_RAMP, CAT, FAIL, MUTED, OK, TEXT, WARN, brush, cat_color, fmt, make_plot, pen, set_bars
from .workbench import components, list_scenarios

EXPERIMENTS = [("Controller-Vergleich", "compare_controller"), ("Planner-Vergleich", "compare_planner"),
               ("Parameter-Sweep", "sweep"), ("Monte Carlo", "monte_carlo"), ("Batch (Szenarioliste)", "batch")]
DISTRIBUTIONS = {"uniform": ("Gleichverteilung", "low", "high"), "normal": ("Normalverteilung", "mean", "std"),
                 "lognormal": ("Log-Normal", "mean", "sigma"), "integer": ("Ganzzahlig", "low", "high"),
                 "choice": ("Auswahl", "values", "")}
GROUP_TABS = [("Sicherheit", "Safety Metrics"), ("Tracking", "Tracking Error Evaluation")]
MAX_CAT = len(CAT)


def safe_label(text):
    # labels double as file names of saved runs (ADResult.save uses with_suffix -> no '.')
    text = re.sub(r'[<>:"/\\|?*]', "_", str(text))
    return text.replace(".", ",").strip() or "run"


def unique_labels(jobs):
    seen = {}
    for job in jobs:
        base = safe_label(job.get("label", "run"))
        k = seen.get(base, 0)
        seen[base] = k + 1
        job["label"] = base if k == 0 else f"{base} ({k + 1})"
    return jobs


def parse_values(text):
    # "0.5, 1, 2" | "0.1:2:5" (linspace start:stop:n) | words (strings)
    text = text.strip()
    if re.fullmatch(r"\s*[-+0-9.eE]+\s*:\s*[-+0-9.eE]+\s*:\s*\d+\s*", text):
        a, b, n = text.split(":")
        return [float(v) for v in np.linspace(float(a), float(b), int(n))]
    out = []
    for part in re.split(r"[;,\s]+", text):
        if not part:
            continue
        try:
            v = float(part)
            out.append(int(v) if v.is_integer() and "." not in part else v)
        except ValueError:
            out.append(part)
    return out


def infer_kind(batch):
    recs = getattr(batch, "records", []) or []
    if any("sweep" in (r.get("job") or {}) for r in recs):
        return "sweep"
    if any("sample" in (r.get("job") or {}) for r in recs):
        return "monte_carlo"
    scen = {str((r.get("job") or {}).get("scenario")) for r in recs}
    return "batch" if len(scen) > 1 else "compare"


# ---------------------------------------------------------------------------- worker
class BatchWorker(QtCore.QObject):
    progress = QtCore.Signal(int, int)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs

    @QtCore.Slot()
    def run(self):
        try:
            self.finished.emit(self.fn(*self.args, progress=lambda i, n: self.progress.emit(int(i), int(n)),
                                       **self.kwargs))
        except Exception as exc:
            import traceback
            self.failed.emit(f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")


def _run_batch(jobs, workers=0, progress=None):
    from ...research import run_batch
    return run_batch(jobs, workers=workers, progress=progress)


def _run_benchmark(scenario, stack=None, repeats=3, duration=None, progress=None):
    from ...research import benchmark
    if progress:
        progress(0, 1)
    rep = benchmark(scenario, stack=stack, repeats=repeats, duration=duration)
    if progress:
        progress(1, 1)
    return rep


# ---------------------------------------------------------------------------- configuration form
class ExperimentForm(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        form = QtWidgets.QFormLayout()
        self.kind = QtWidgets.QComboBox()
        for label, key in EXPERIMENTS:
            self.kind.addItem(label, key)
        self.scenario = QtWidgets.QComboBox()
        self.scenario.setEditable(True)
        self.scenarios = [sc.get("name", str(sc)) if isinstance(sc, dict) else str(sc) for sc in list_scenarios()]
        self.scenario.addItems(self.scenarios)
        self.use_stack = QtWidgets.QCheckBox("Stack der Workbench als Basis")
        self.use_stack.setChecked(True)
        self.seed = QtWidgets.QSpinBox()
        self.seed.setRange(0, 2 ** 31 - 1)
        self.duration = QtWidgets.QDoubleSpinBox()
        self.duration.setRange(0, 3600)
        self.duration.setSuffix(" s")
        self.duration.setSpecialValueText("Szenario")
        form.addRow("Experiment", self.kind)
        form.addRow("Szenario", self.scenario)
        form.addRow("", self.use_stack)
        form.addRow("Seed", self.seed)
        form.addRow("Dauer", self.duration)

        self.pages = QtWidgets.QStackedWidget()
        self.ctrl_list = self._component_page("tracking_controller")
        self.plan_list = self._component_page("trajectory_planner")
        self.pages.addWidget(self.ctrl_list["page"])
        self.pages.addWidget(self.plan_list["page"])
        self.pages.addWidget(self._sweep_page())
        self.pages.addWidget(self._mc_page())
        self.pages.addWidget(self._batch_page())
        self.kind.currentIndexChanged.connect(self.pages.setCurrentIndex)

        run_box = QtWidgets.QFormLayout()
        self.workers = QtWidgets.QSpinBox()
        self.workers.setRange(0, 64)
        self.workers.setSpecialValueText("0 (sequentiell)")
        self.save_runs = QtWidgets.QCheckBox("Läufe speichern (Klick lädt Lauf)")
        self.save_runs.setChecked(True)
        self.save_dir = QtWidgets.QLineEdit(str(Path(tempfile.gettempdir()) / "vdsim_research"))
        run_box.addRow("Worker-Prozesse", self.workers)
        run_box.addRow("", self.save_runs)
        run_box.addRow("Ablage", self.save_dir)

        layout = QtWidgets.QVBoxLayout(self)
        g1 = QtWidgets.QGroupBox("Experiment")
        g1.setLayout(form)
        g2 = QtWidgets.QGroupBox("Varianten / Parameter")
        l2 = QtWidgets.QVBoxLayout(g2)
        l2.addWidget(self.pages)
        g3 = QtWidgets.QGroupBox("Ausführung")
        g3.setLayout(run_box)
        for g in (g1, g2, g3):
            layout.addWidget(g)

    def _component_page(self, kind):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lst = QtWidgets.QListWidget()
        for d in components(kind):
            spec = f"{d.get('kind', kind)}/{d.get('name')}@{d.get('version')}"
            item = QtWidgets.QListWidgetItem(f"{d.get('label') or d.get('name')} ({d.get('version')})")
            item.setData(QtCore.Qt.UserRole, spec)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            lst.addItem(item)
        extra = QtWidgets.QLineEdit()
        extra.setPlaceholderText(f"weitere Komponente, z. B. {kind}/name oder python:pfad.py:Klasse")
        add = QtWidgets.QPushButton("Hinzufügen")
        def add_spec():
            spec = extra.text().strip()
            if spec:
                item = QtWidgets.QListWidgetItem(spec)
                item.setData(QtCore.Qt.UserRole, spec)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Checked)
                lst.addItem(item)
                extra.clear()
        add.clicked.connect(add_spec)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(extra, 1)
        row.addWidget(add)
        hint = QtWidgets.QLabel("Angehakte Komponenten werden auf demselben Szenario verglichen.")
        hint.setStyleSheet(f"color: {MUTED};")
        hint.setWordWrap(True)
        lay.addWidget(lst, 1)
        lay.addLayout(row)
        lay.addWidget(hint)
        return {"page": page, "list": lst, "extra": extra, "add": add_spec}

    def _sweep_page(self):
        page = QtWidgets.QWidget()
        f = QtWidgets.QFormLayout(page)
        self.sweep_path = [QtWidgets.QLineEdit("stack.planner.params.cost.k_jerk"),
                           QtWidgets.QLineEdit("stack.planner.params.cost.k_d")]
        self.sweep_values = [QtWidgets.QLineEdit("0.5, 1, 2"), QtWidgets.QLineEdit("0.5, 1, 2")]
        self.sweep_second = QtWidgets.QCheckBox("Zweiter Parameter")
        self.sweep_second.setChecked(False)
        f.addRow("Parameter 1", self.sweep_path[0])
        f.addRow("Werte 1", self.sweep_values[0])
        f.addRow("", self.sweep_second)
        f.addRow("Parameter 2", self.sweep_path[1])
        f.addRow("Werte 2", self.sweep_values[1])
        hint = QtWidgets.QLabel("Werte als Liste „0.5, 1, 2“ oder „start:stop:n“. Pfade in den Job, z. B. "
                                "stack.controller.params.k_n oder scenario_params.lead_speed.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {MUTED};")
        f.addRow(hint)
        return page

    def _mc_page(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        self.mc_table = QtWidgets.QTableWidget(0, 4)
        self.mc_table.setHorizontalHeaderLabels(["Pfad", "Verteilung", "Parameter 1", "Parameter 2"])
        self.mc_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.mc_table.verticalHeader().setVisible(False)
        self.add_mc_row("scenario_params.cut_in_gap", "uniform", "8", "30")
        self.add_mc_row("scenario_params.lead_speed", "normal", "14", "1.5")
        row = QtWidgets.QHBoxLayout()
        add, rem = QtWidgets.QPushButton("+ Parameter"), QtWidgets.QPushButton("− entfernen")
        add.clicked.connect(lambda: self.add_mc_row("", "uniform", "0", "1"))
        rem.clicked.connect(lambda: self.mc_table.removeRow(max(self.mc_table.currentRow(), 0))
                            if self.mc_table.rowCount() else None)
        row.addWidget(add)
        row.addWidget(rem)
        row.addStretch(1)
        f = QtWidgets.QFormLayout()
        self.mc_n = QtWidgets.QSpinBox()
        self.mc_n.setRange(2, 100000)
        self.mc_n.setValue(50)
        self.mc_seed = QtWidgets.QSpinBox()
        self.mc_seed.setRange(0, 2 ** 31 - 1)
        f.addRow("Stichprobenumfang n", self.mc_n)
        f.addRow("Seed der Stichprobe", self.mc_seed)
        lay.addWidget(self.mc_table, 1)
        lay.addLayout(row)
        lay.addLayout(f)
        return page

    def add_mc_row(self, path, dist, p1, p2):
        r = self.mc_table.rowCount()
        self.mc_table.insertRow(r)
        self.mc_table.setItem(r, 0, QtWidgets.QTableWidgetItem(path))
        combo = QtWidgets.QComboBox()
        for key, (label, _, _) in DISTRIBUTIONS.items():
            combo.addItem(label, key)
        combo.setCurrentIndex(list(DISTRIBUTIONS).index(dist))
        self.mc_table.setCellWidget(r, 1, combo)
        self.mc_table.setItem(r, 2, QtWidgets.QTableWidgetItem(str(p1)))
        self.mc_table.setItem(r, 3, QtWidgets.QTableWidgetItem(str(p2)))

    def _batch_page(self):
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        self.batch_list = QtWidgets.QListWidget()
        for name in self.scenarios:
            item = QtWidgets.QListWidgetItem(name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            self.batch_list.addItem(item)
        self.batch_extra = QtWidgets.QLineEdit()
        self.batch_extra.setPlaceholderText("weitere Szenarien, durch Komma getrennt")
        f = QtWidgets.QFormLayout()
        self.batch_seeds = QtWidgets.QSpinBox()
        self.batch_seeds.setRange(1, 1000)
        f.addRow("Seeds je Szenario", self.batch_seeds)
        lay.addWidget(self.batch_list, 1)
        lay.addWidget(self.batch_extra)
        lay.addLayout(f)
        return page

    # ------------------------------------------------------------------ jobs
    def distributions(self):
        out = {}
        for r in range(self.mc_table.rowCount()):
            path = (self.mc_table.item(r, 0).text() if self.mc_table.item(r, 0) else "").strip()
            if not path:
                continue
            kind = self.mc_table.cellWidget(r, 1).currentData()
            p1 = self.mc_table.item(r, 2).text() if self.mc_table.item(r, 2) else ""
            p2 = self.mc_table.item(r, 3).text() if self.mc_table.item(r, 3) else ""
            _, k1, k2 = DISTRIBUTIONS[kind]
            if kind == "choice":
                out[path] = {"dist": "choice", "values": parse_values(p1)}
            elif kind == "integer":
                out[path] = {"dist": kind, k1: int(float(p1)), k2: int(float(p2))}
            else:
                out[path] = {"dist": kind, k1: float(p1), k2: float(p2)}
        return out

    def build_jobs(self, base_stack=None):
        from ...research import compare_components, monte_carlo, parameter_sweep
        kind = self.kind.currentData()
        base = {"scenario": self.scenario.currentText().strip(), "stack": dict(base_stack or {}),
                "seed": int(self.seed.value()), "duration": float(self.duration.value()) or None, "snapshots": True}
        if kind in ("compare_controller", "compare_planner"):
            page = self.ctrl_list if kind == "compare_controller" else self.plan_list
            layer = "controller" if kind == "compare_controller" else "planner"
            lst = page["list"]
            variants = {}
            for i in range(lst.count()):
                it = lst.item(i)
                if it.checkState() == QtCore.Qt.Checked:
                    label = re.sub(r"\s*\([^)]*\)$", "", it.text()) or it.data(QtCore.Qt.UserRole)
                    spec = {"component": it.data(QtCore.Qt.UserRole)}
                    prev = (base["stack"].get(layer) or {})
                    if prev.get("component", "").split("@")[0] == spec["component"].split("@")[0] and prev.get("params"):
                        spec["params"] = prev["params"]
                    variants[label] = spec
            jobs = compare_components(base, layer, variants)
        elif kind == "sweep":
            grid = {self.sweep_path[0].text().strip(): parse_values(self.sweep_values[0].text())}
            if self.sweep_second.isChecked() and self.sweep_path[1].text().strip():
                grid[self.sweep_path[1].text().strip()] = parse_values(self.sweep_values[1].text())
            jobs = parameter_sweep(base, grid)
            for job in jobs:
                job["label"] = "; ".join(f"{k.split('.')[-1]}={v:g}" if isinstance(v, (int, float)) else
                                         f"{k.split('.')[-1]}={v}" for k, v in job["sweep"].items())
        elif kind == "monte_carlo":
            jobs = monte_carlo(base, self.distributions(), int(self.mc_n.value()), seed=int(self.mc_seed.value()))
        else:
            names = [self.batch_list.item(i).text() for i in range(self.batch_list.count())
                     if self.batch_list.item(i).checkState() == QtCore.Qt.Checked]
            names += [s.strip() for s in self.batch_extra.text().split(",") if s.strip()]
            jobs = []
            for name in names:
                for k in range(int(self.batch_seeds.value())):
                    seed = base["seed"] + k
                    jobs.append(dict(base, scenario=name, seed=seed,
                                     label=name if self.batch_seeds.value() == 1 else f"{name} s{seed}"))
        if self.save_runs.isChecked():
            folder = Path(self.save_dir.text().strip() or tempfile.gettempdir()) / time.strftime("%Y%m%d_%H%M%S")
            for job in jobs:
                job["save_dir"] = str(folder)
        else:
            for job in jobs:
                job["snapshots"] = False
        return unique_labels(jobs)


# ---------------------------------------------------------------------------- dashboard parts
def _kpi_combo():
    c = QtWidgets.QComboBox()
    c.setMinimumWidth(260)
    return c


def _labels_colors(labels):
    # fixed categorical order by variant; beyond eight variants one neutral series color
    return [cat_color(i) for i in range(len(labels))] if len(labels) <= MAX_CAT else CAT[0]


class SmallMultiples(QtWidgets.QWidget):
    # one bar chart (or histogram for many runs) per KPI of a group
    def __init__(self, group, parent=None):
        super().__init__(parent)
        self.group = group
        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setContentsMargins(2, 2, 2, 2)
        self.plots = []
        self.note = QtWidgets.QLabel("")
        self.note.setStyleSheet(f"color: {MUTED};")

    def set_batch(self, batch):
        for p in self.plots:
            p.setParent(None)
            p.deleteLater()
        self.plots = []
        keys = [k for k in batch.kpi_keys() if kpi_meta(k)[2] == self.group] if batch else []
        labels = [r.get("label", "") for r in batch.records] if batch else []
        many = len(labels) > 12
        for i, key in enumerate(keys):
            label, unit, _, better = kpi_meta(key)
            arrow = {"low": " ↓", "high": " ↑"}.get(better, "")
            col = batch.column(key)
            if many:
                p = make_plot(f"{label}{arrow}", "Anzahl", "", xlabel=unit if unit != "-" else "", xunit="")
                v = col[np.isfinite(col)]
                if len(v) > 1 and np.ptp(v) > 0:
                    y, x = np.histogram(v, bins=min(20, max(len(v) // 3, 5)))
                    p.plot(x, y, stepMode="center", fillLevel=0, brush=brush(CAT[0], 0.6), pen=pen(CAT[0], 1))
            else:
                p = make_plot(f"{label}{arrow}", "", unit, xlabel="")
                set_bars(p, labels, col, _labels_colors(labels))
            p.setMinimumHeight(170)
            self.grid.addWidget(p, i // 3, i % 3)
            self.plots.append(p)
        self.grid.addWidget(self.note, (len(keys) + 2) // 3 + 1, 0, 1, 3)
        self.note.setText("" if keys else f"Keine Kennwerte der Gruppe {self.group} vorhanden.")
        if keys:
            self.note.setText("↓ / ↑: niedriger bzw. höher ist besser. " +
                              ("Histogramme über alle Läufe." if many else "Balkenfarbe = Variante (feste Reihenfolge)."))


class ResearchPanel(QtWidgets.QWidget):
    TAB_TITLE = "Forschung"
    result_loaded = QtCore.Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.job_provider = None
        self.batch = None
        self.kind = None
        self._thread = None
        self._worker = None
        self.benchmark_report = None

        self.form = ExperimentForm()
        self.run_btn = QtWidgets.QPushButton("Experiment starten")
        self.run_btn.setObjectName("primary")
        self.run_btn.clicked.connect(self.start)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setFormat("%v / %m Läufe")
        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet(f"color: {MUTED};")
        left = QtWidgets.QWidget()
        ll = QtWidgets.QVBoxLayout(left)
        ll.addWidget(self.form, 1)
        ll.addWidget(self.run_btn)
        ll.addWidget(self.progress)
        ll.addWidget(self.status)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(left)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)

        self.tabs = QtWidgets.QTabWidget()
        self._build_table_tab()
        self._build_compare_tab()
        self._build_sweep_tab()
        self._build_mc_tab()
        self.groups = {}
        for group, title in GROUP_TABS:
            sm = SmallMultiples(group)
            sc = QtWidgets.QScrollArea()
            sc.setWidget(sm)
            sc.setWidgetResizable(True)
            self.tabs.addTab(sc, title)
            self.groups[group] = sm
        self._build_cost_tab()
        self._build_runtime_tab()

        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.addWidget(scroll)
        split.addWidget(self.tabs)
        split.setSizes([400, 1200])
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(split)

    # ------------------------------------------------------------------ tabs
    def _build_table_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        self.summary = QtWidgets.QLabel("Noch kein Experiment")
        csv, js = QtWidgets.QPushButton("Export CSV ..."), QtWidgets.QPushButton("Export JSON ...")
        csv.clicked.connect(lambda: self.export_csv())
        js.clicked.connect(lambda: self.export_json())
        row.addWidget(self.summary, 1)
        row.addWidget(csv)
        row.addWidget(js)
        self.table = QtWidgets.QTableWidget(0, 0)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.cellDoubleClicked.connect(lambda r, c: self.load_run(r))
        self.table.cellClicked.connect(lambda r, c: self.load_run(r) if c == 0 else None)
        hint = QtWidgets.QLabel("Klick auf den Laufnamen bzw. Doppelklick auf eine Zeile lädt einen gespeicherten "
                                "Lauf in die Planer-Ansicht. Fett = bester Wert je Kennwert.")
        hint.setStyleSheet(f"color: {MUTED};")
        lay.addLayout(row)
        lay.addWidget(self.table, 1)
        lay.addWidget(hint)
        self.tabs.addTab(w, "KPI-Tabelle")

    def _build_compare_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        self.cmp_kpi = _kpi_combo()
        self.cmp_kpi.currentIndexChanged.connect(self._update_compare)
        row.addWidget(QtWidgets.QLabel("Kennwert"))
        row.addWidget(self.cmp_kpi)
        row.addStretch(1)
        self.cmp_plot = make_plot("", "", "", xlabel="")
        lay.addLayout(row)
        lay.addWidget(self.cmp_plot, 1)
        self.tabs.addTab(w, "KPI-Vergleich")

    def _build_sweep_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        self.sweep_kpi = _kpi_combo()
        self.sweep_kpi.currentIndexChanged.connect(self._update_sweep)
        row.addWidget(QtWidgets.QLabel("Kennwert"))
        row.addWidget(self.sweep_kpi)
        row.addStretch(1)
        self.sweep_plot = make_plot("", "", "", xlabel="")
        self.sweep_img = pg.ImageItem()
        self.sweep_plot.addItem(self.sweep_img)
        cmap = pg.ColorMap(np.linspace(0, 1, len(BLUE_RAMP)), [pg.mkColor(c) for c in BLUE_RAMP])
        self.sweep_img.setColorMap(cmap)
        self.sweep_bar = pg.ColorBarItem(colorMap=cmap, interactive=False, width=14)
        self.sweep_bar.setImageItem(self.sweep_img, insert_in=self.sweep_plot.getPlotItem())
        self.sweep_line = self.sweep_plot.plot([], [], pen=pen(CAT[0], 2), symbol="o", symbolSize=8,
                                               symbolBrush=brush(CAT[0]), symbolPen=None)
        self.sweep_texts = []
        self.sweep_note = QtWidgets.QLabel("")
        self.sweep_note.setStyleSheet(f"color: {MUTED};")
        lay.addLayout(row)
        lay.addWidget(self.sweep_plot, 1)
        lay.addWidget(self.sweep_note)
        self.tabs.addTab(w, "Sweep")

    def _build_mc_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        self.mc_kpi = _kpi_combo()
        self.mc_kpi.currentIndexChanged.connect(self._update_mc)
        self.mc_rate = QtWidgets.QLabel("")
        self.mc_rate.setStyleSheet("font-weight: bold;")
        row.addWidget(QtWidgets.QLabel("Kennwert"))
        row.addWidget(self.mc_kpi)
        row.addStretch(1)
        row.addWidget(self.mc_rate)
        self.mc_hist = make_plot("Verteilung", "Anzahl", "", xlabel="")
        self.mc_curve = self.mc_hist.plot([], [], stepMode="center", fillLevel=0, brush=brush(CAT[0], 0.6),
                                          pen=pen(CAT[0], 1))
        self.mc_lines = []
        self.mc_stats = table(["Statistik", "Wert"], 0)
        self.mc_sens = make_plot("Sensitivität (standardisierter Regressionskoeffizient)", "", "", xlabel="SRC",
                                 xunit="")
        grid = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        grid.addWidget(self.mc_hist)
        right = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        right.addWidget(self.mc_stats)
        right.addWidget(self.mc_sens)
        grid.addWidget(right)
        grid.setSizes([700, 450])
        lay.addLayout(row)
        lay.addWidget(grid, 1)
        self.tabs.addTab(w, "Monte Carlo")

    def _build_cost_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        self.cost_plot = make_plot("Anteile der Kostenterme je Variante (gestapelt, normiert)", "Anteil", "",
                                   xlabel="", legend=True)
        self.cost_items = []
        self.cost_table = table(["Kostenterm", "Mittel über Läufe", "Anteil"], 0)
        self.cost_table.setMaximumHeight(200)
        lay.addWidget(self.cost_plot, 1)
        lay.addWidget(self.cost_table)
        self.tabs.addTab(w, "Cost Function Analysis")

    def _build_runtime_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        self.bench_repeats = QtWidgets.QSpinBox()
        self.bench_repeats.setRange(1, 50)
        self.bench_repeats.setValue(3)
        self.bench_btn = QtWidgets.QPushButton("Benchmark ausführen")
        self.bench_btn.clicked.connect(self.start_benchmark)
        self.bench_info = QtWidgets.QLabel("Profil gemittelt über die Läufe des Experiments")
        self.bench_info.setStyleSheet(f"color: {MUTED};")
        row.addWidget(QtWidgets.QLabel("Wiederholungen"))
        row.addWidget(self.bench_repeats)
        row.addWidget(self.bench_btn)
        row.addWidget(self.bench_info, 1)
        self.bench_table = table(["Knoten", "Aufrufe", "Mittel [ms]", "p95 [ms]", "Max [ms]", "Gesamt [s]"], 0)
        self.bench_plot = make_plot("Mittlere Rechenzeit je Knoten", "", "", xlabel="ms", xunit="")
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.addWidget(self.bench_table)
        split.addWidget(self.bench_plot)
        lay.addLayout(row)
        lay.addWidget(split, 1)
        self.tabs.addTab(w, "Runtime Benchmarking")

    # ------------------------------------------------------------------ execution
    def build_jobs(self):
        stack = None
        if self.form.use_stack.isChecked() and callable(self.job_provider):
            try:
                stack = (self.job_provider() or {}).get("stack")
            except Exception:
                stack = None
        return self.form.build_jobs(stack)

    def start(self):
        if self._thread is not None:
            return
        try:
            jobs = self.build_jobs()
        except Exception as exc:
            self.status.setText(f"<span style='color:{FAIL}'>Konfiguration fehlerhaft: {exc}</span>")
            return
        if not jobs:
            self.status.setText("Keine Läufe konfiguriert")
            return
        if not jobs[0].get("scenario"):
            self.status.setText("Bitte ein Szenario angeben")
            return
        self.progress.setRange(0, len(jobs))
        self.progress.setValue(0)
        self.status.setText(f"{len(jobs)} Läufe gestartet ...")
        self._pending_kind = {"compare_controller": "compare", "compare_planner": "compare"}.get(
            self.form.kind.currentData(), self.form.kind.currentData())
        self._run_thread(_run_batch, jobs, workers=int(self.form.workers.value()), on_done=self._batch_done)

    def start_benchmark(self):
        if self._thread is not None:
            return
        stack = (self.job_provider() or {}).get("stack") if callable(self.job_provider) else None
        scenario = self.form.scenario.currentText().strip()
        if not scenario:
            self.bench_info.setText("Bitte ein Szenario angeben")
            return
        self.bench_info.setText("Benchmark läuft ...")
        self._run_thread(_run_benchmark, scenario, stack=stack, repeats=int(self.bench_repeats.value()),
                         duration=float(self.form.duration.value()) or None, on_done=self.set_benchmark)

    def _run_thread(self, fn, *args, on_done=None, **kwargs):
        self._worker = BatchWorker(fn, *args, **kwargs)
        self._thread = QtCore.QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(lambda i, n: (self.progress.setRange(0, n), self.progress.setValue(i)))
        self._worker.finished.connect(on_done)
        self._worker.failed.connect(lambda msg: self.status.setText(
            f"<span style='color:{FAIL}'>Fehler: {msg.splitlines()[0]}</span>"))
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread_done)
        self.run_btn.setEnabled(False)
        self.bench_btn.setEnabled(False)
        self._thread.start()

    def _thread_done(self):
        self._thread.deleteLater()
        self._thread = None
        self._worker = None
        self.run_btn.setEnabled(True)
        self.bench_btn.setEnabled(True)

    def wait(self, timeout_ms=120000):
        timer = QtCore.QElapsedTimer()
        timer.start()
        while self._thread is not None and timer.elapsed() < timeout_ms:
            QtWidgets.QApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)
            QtCore.QThread.msleep(5)
        return self._thread is None

    def _batch_done(self, batch):
        self.set_batch(batch, getattr(self, "_pending_kind", None))

    # ------------------------------------------------------------------ results
    def set_batch(self, batch, kind=None):
        self.batch = batch
        self.kind = kind or (infer_kind(batch) if batch is not None else None)
        n_ok = len(batch.ok) if batch else 0
        n = len(batch) if batch else 0
        failed = n - n_ok
        self.summary.setText(f"<b>{n}</b> Läufe, <span style='color:{OK}'>✔ {n_ok} erfolgreich</span>"
                             + (f", <span style='color:{FAIL}'>✖ {failed} fehlgeschlagen</span>" if failed else "")
                             + f"   <span style='color:{MUTED}'>Experiment: {self.kind}</span>")
        self.status.setText(f"Fertig: {n_ok}/{n} Läufe erfolgreich")
        keys = batch.kpi_keys() if batch else []
        for combo in (self.cmp_kpi, self.sweep_kpi, self.mc_kpi):
            prev = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for k in keys:
                label, unit, _, _ = kpi_meta(k)
                combo.addItem(f"{label} [{unit}]" if unit and unit != "-" else label, k)
            idx = combo.findData(prev) if prev else -1
            if idx < 0:
                for pref in ("rms_e_n", "min_ttc", "cost_mean", "collision"):
                    idx = combo.findData(pref)
                    if idx >= 0:
                        break
            combo.setCurrentIndex(max(idx, 0))
            combo.blockSignals(False)
        self._update_table()
        self._update_compare()
        self._update_sweep()
        self._update_mc()
        for sm in self.groups.values():
            sm.set_batch(batch)
        self._update_costs()
        self._update_profile()
        # bring the most telling view to the front
        target = {"sweep": "Sweep", "monte_carlo": "Monte Carlo"}.get(self.kind, "KPI-Vergleich")
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == target:
                self.tabs.setCurrentIndex(i)

    def _params(self):
        names = []
        for r in self.batch.records:
            job = r.get("job") or {}
            for k in (job.get("sweep") or job.get("sample") or {}):
                if k not in names:
                    names.append(k)
        return names

    def _update_table(self):
        b = self.batch
        if b is None:
            self.table.setRowCount(0)
            return
        keys = b.kpi_keys()
        params = self._params()
        headers = ["Lauf", "Status"] + [p.split(".")[-1] for p in params]
        for k in keys:
            label, unit, _, better = kpi_meta(k)
            arrow = {"low": " ↓", "high": " ↑"}.get(better, "")
            headers.append(f"{label}{arrow}" + (f" [{unit}]" if unit and unit != "-" else ""))
        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(b.records))
        best = {}
        for k in keys:
            better = kpi_meta(k)[3]
            col = b.column(k)
            if better and np.any(np.isfinite(col)):
                best[k] = np.nanmin(col) if better == "low" else np.nanmax(col)
        for r, rec in enumerate(b.records):
            job = rec.get("job") or {}
            name = QtWidgets.QTableWidgetItem(str(rec.get("label", "")))
            name.setData(QtCore.Qt.UserRole, r)
            if rec.get("path"):
                name.setToolTip(f"Gespeichert: {rec['path']}")
                f = name.font()
                f.setUnderline(True)
                name.setFont(f)
            self.table.setItem(r, 0, name)
            ok = rec.get("ok")
            st = QtWidgets.QTableWidgetItem("✔ ok" if ok else "✖ Fehler")
            st.setForeground(QtGui.QColor(OK if ok else FAIL))
            if not ok:
                st.setToolTip(rec.get("error", ""))
            self.table.setItem(r, 1, st)
            pv = job.get("sweep") or job.get("sample") or {}
            for c, p in enumerate(params):
                self.table.setItem(r, 2 + c, self._num(pv.get(p)))
            for c, k in enumerate(keys):
                v = (rec.get("kpis") or {}).get(k)
                item = self._num(v)
                if k in best and v is not None and np.isfinite(v) and np.isclose(v, best[k]):
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                self.table.setItem(r, 2 + len(params) + c, item)
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

    @staticmethod
    def _num(v):
        item = QtWidgets.QTableWidgetItem()
        if isinstance(v, (int, float, np.floating, np.integer)) and not isinstance(v, bool):
            item.setData(QtCore.Qt.DisplayRole, float(v) if np.isfinite(v) else float("nan"))
            item.setText(fmt(v, 4))
            item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        else:
            item.setText("" if v is None else str(v))
        return item

    def _update_compare(self):
        key = self.cmp_kpi.currentData()
        if self.batch is None or key is None:
            set_bars(self.cmp_plot, [], [])
            return
        labels = [r.get("label", "") for r in self.batch.records]
        label, unit, _, better = kpi_meta(key)
        arrow = {"low": " (niedriger ist besser)", "high": " (höher ist besser)"}.get(better, "")
        self.cmp_plot.getPlotItem().setTitle(f"<span style='color:{TEXT}'>{label}{arrow}</span>")
        self.cmp_plot.setLabel("left", "", units=unit if unit and unit != "-" else None)
        horizontal = len(labels) > 8
        set_bars(self.cmp_plot, labels, self.batch.column(key), _labels_colors(labels), horizontal=horizontal)

    def _update_sweep(self):
        for t in self.sweep_texts:
            self.sweep_plot.removeItem(t)
        self.sweep_texts = []
        key = self.sweep_kpi.currentData()
        params = self._params() if self.batch is not None and self.kind == "sweep" else []
        self.sweep_img.clear()
        self.sweep_line.setData([], [])
        self.sweep_bar.setVisible(False)
        if not params or key is None:
            self.sweep_note.setText("Kein Parameter-Sweep im aktuellen Experiment.")
            return
        recs = self.batch.records
        vals = [[(r.get("job") or {}).get("sweep", {}).get(p) for r in recs] for p in params]
        z = self.batch.column(key)
        label, unit, _, better = kpi_meta(key)
        if len(params) == 1:
            x = np.asarray(vals[0], float)
            order = np.argsort(x)
            self.sweep_line.setData(x[order], z[order])
            self.sweep_plot.setLabel("bottom", params[0].split(".")[-1])
            self.sweep_plot.setLabel("left", label, units=unit if unit != "-" else None)
            self.sweep_plot.getPlotItem().getAxis("bottom").setTicks(None)
            self.sweep_plot.getPlotItem().getAxis("left").setTicks(None)
            self.sweep_note.setText("1 Parameter: Kennwert über dem Parameterwert")
            self.sweep_plot.getPlotItem().enableAutoRange()
            return
        ux = sorted(set(vals[0]), key=lambda v: (isinstance(v, str), v))
        uy = sorted(set(vals[1]), key=lambda v: (isinstance(v, str), v))
        grid = np.full((len(ux), len(uy)), np.nan)
        for a, b, v in zip(vals[0], vals[1], z):
            grid[ux.index(a), uy.index(b)] = v
        finite = grid[np.isfinite(grid)]
        lo, hi = (float(finite.min()), float(finite.max())) if len(finite) else (0.0, 1.0)
        if hi <= lo:
            hi = lo + 1e-9
        self.sweep_img.setImage(np.nan_to_num(grid, nan=lo), levels=(lo, hi))
        self.sweep_img.setRect(QtCore.QRectF(-0.5, -0.5, len(ux), len(uy)))
        self.sweep_bar.setLevels((lo, hi))
        self.sweep_bar.setVisible(True)
        for i in range(len(ux)):
            for j in range(len(uy)):
                v = grid[i, j]
                frac = (v - lo) / (hi - lo) if np.isfinite(v) else 0
                txt = pg.TextItem(fmt(v), color="#0b0b0b" if frac > 0.6 else "#f0f0f0", anchor=(0.5, 0.5))
                txt.setPos(i, j)
                self.sweep_plot.addItem(txt)
                self.sweep_texts.append(txt)
        self.sweep_plot.getAxis("bottom").setTicks([[(i, f"{v:g}" if not isinstance(v, str) else v)
                                                     for i, v in enumerate(ux)]])
        self.sweep_plot.getAxis("left").setTicks([[(j, f"{v:g}" if not isinstance(v, str) else v)
                                                   for j, v in enumerate(uy)]])
        self.sweep_plot.setLabel("bottom", params[0].split(".")[-1], units=None)
        self.sweep_plot.setLabel("left", params[1].split(".")[-1], units=None)
        self.sweep_plot.getPlotItem().setTitle(f"<span style='color:{TEXT}'>{label}"
                                               f"{' [' + unit + ']' if unit and unit != '-' else ''}</span>")
        self.sweep_plot.getPlotItem().getViewBox().autoRange(items=[self.sweep_img])
        hint = {"low": "niedriger ist besser", "high": "höher ist besser"}.get(better, "")
        self.sweep_note.setText(f"Heatmap über {params[0]} × {params[1]}; hell = hoher Wert. {hint}")

    def _update_mc(self):
        for ln in self.mc_lines:
            self.mc_hist.removeItem(ln)
        self.mc_lines = []
        key = self.mc_kpi.currentData()
        if self.batch is None or key is None:
            self.mc_curve.setData([], [])
            self.mc_stats.setRowCount(0)
            return
        col = self.batch.column(key)
        v = col[np.isfinite(col)]
        label, unit, _, _ = kpi_meta(key)
        self.mc_hist.getPlotItem().setTitle(f"<span style='color:{TEXT}'>Verteilung: {label}</span>")
        self.mc_hist.setLabel("bottom", label, units=unit if unit and unit != "-" else None)
        if len(v) > 1 and np.ptp(v) > 0:
            y, x = np.histogram(v, bins=min(30, max(len(v) // 3, 5)))
            self.mc_curve.setData(x, y)
        else:
            self.mc_curve.setData([], [])
        stats = self.batch.statistics([key])
        s = stats.get(key, {})
        for name, val, style in (("Mittelwert", s.get("mean"), QtCore.Qt.SolidLine),
                                 ("p05", s.get("p05"), QtCore.Qt.DashLine), ("p95", s.get("p95"), QtCore.Qt.DashLine)):
            if val is not None and np.isfinite(val):
                ln = pg.InfiniteLine(pos=val, angle=90, pen=pen(TEXT, 1.2, style, 0.8),
                                     label=name, labelOpts={"color": TEXT, "position": 0.93})
                self.mc_hist.addItem(ln)
                self.mc_lines.append(ln)
        runs = stats.get("_runs", {})
        rows = [(n, s.get(k)) for n, k in (("Mittelwert", "mean"), ("Standardabweichung", "std"), ("Minimum", "min"),
                                          ("p05", "p05"), ("Median", "p50"), ("p95", "p95"), ("Maximum", "max"),
                                          ("n gültig", "n"))]
        rows += [("Läufe gesamt", runs.get("n")), ("fehlgeschlagen", runs.get("failed")),
                 ("Kollisionsrate", runs.get("collision_rate"))]
        fill(self.mc_stats, [(n, v if v is not None else "-") for n, v in rows])
        rate = runs.get("collision_rate")
        if rate is not None and np.isfinite(rate):
            color = OK if rate == 0 else (WARN if rate < 0.05 else FAIL)
            icon = "✔" if rate == 0 else ("▲" if rate < 0.05 else "✖")
            self.mc_rate.setText(f"<span style='color:{color}'>{icon} Kollisionsrate {100 * rate:.1f} %</span>")
        else:
            self.mc_rate.setText("")
        sens = self.batch.sensitivity(key)
        names = list(sens)
        vals = [sens[n] for n in names]
        colors = [CAT[1] if x >= 0 else CAT[0] for x in vals]    # diverging: sign -> two hues
        set_bars(self.mc_sens, [n.split(".")[-1] for n in names], vals, colors, horizontal=True)

    def _update_costs(self):
        for it in self.cost_items:
            self.cost_plot.removeItem(it)
        self.cost_items = []
        leg = self.cost_plot.getPlotItem().legend
        if leg is not None:
            leg.clear()
        b = self.batch
        terms = [k for k in (b.kpi_keys() if b else []) if k.startswith("cost_") and k != "cost_mean"]
        if not terms:
            self.cost_table.setRowCount(0)
            return
        labels = [r.get("label", "") for r in b.records]
        mat = np.abs(np.nan_to_num(np.array([b.column(k) for k in terms]), nan=0.0))   # (terms, runs)
        tot = mat.sum(0)
        share = mat / np.where(tot > 0, tot, 1)
        x = np.arange(len(labels))
        bottom = np.zeros(len(labels))
        for i, k in enumerate(terms):
            color = cat_color(i)
            bar = pg.BarGraphItem(x=x, height=share[i], width=0.7, y0=bottom, brush=brush(color),
                                  pen=pen("#1e1f22", 1.5), name=k[5:])
            self.cost_plot.addItem(bar)
            self.cost_items.append(bar)
            bottom = bottom + share[i]
        self.cost_plot.getAxis("bottom").setTicks([list(zip(x, labels))] if len(labels) <= 30 else None)
        self.cost_plot.setYRange(0, 1.0)
        means = mat.mean(1)
        msum = means.sum() or 1.0
        fill(self.cost_table, [(k[5:], float(m), float(m / msum)) for k, m in zip(terms, means)])

    def _update_profile(self, report=None):
        rows = []
        if report:
            for node, s in report.get("nodes", {}).items():
                rows.append((node, s.get("calls", 0), s.get("mean_ms", np.nan), s.get("p95_ms", np.nan),
                             s.get("max_ms", np.nan), s.get("total_s", np.nan)))
        elif self.batch is not None:
            acc = {}
            for r in self.batch.records:
                for node, s in (r.get("profile") or {}).items():
                    acc.setdefault(node, []).append(s)
            for node, runs in acc.items():
                def m(key, f=np.nanmean):
                    vals = [x.get(key, np.nan) for x in runs]
                    return float(f(vals)) if vals else np.nan
                rows.append((node, int(m("calls")), 1e3 * m("mean"), 1e3 * m("p95"), 1e3 * m("max", np.nanmax),
                             m("total")))
        rows.sort(key=lambda r: -(r[5] if np.isfinite(r[5]) else 0))
        fill(self.bench_table, rows)
        order = sorted(rows, key=lambda r: r[2] if np.isfinite(r[2]) else 0)
        set_bars(self.bench_plot, [r[0] for r in order], [r[2] for r in order], CAT[0], horizontal=True)

    def set_benchmark(self, report):
        self.benchmark_report = report
        self._update_profile(report)
        pc = report.get("planner_cycle_ms") or {}
        self.bench_info.setText(f"Echtzeitfaktor {report.get('real_time_factor', np.nan):.2f} "
                                f"({report.get('simulated_s', 0):.1f} s simuliert in {report.get('wall_time_s', 0):.2f} s)"
                                + (f", Planungszyklus Mittel {pc['mean']:.1f} ms / p95 {pc['p95']:.1f} ms" if pc else ""))

    # ------------------------------------------------------------------ export / load
    def export_csv(self, path=None):
        if self.batch is None:
            return None
        if path is None:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export CSV", "experiment.csv", "CSV (*.csv)")
            if not path:
                return None
        return self.batch.to_csv(path)

    def export_json(self, path=None):
        if self.batch is None:
            return None
        if path is None:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export JSON", "experiment.json", "JSON (*.json)")
            if not path:
                return None
        return self.batch.to_json(path)

    def load_run(self, row):
        if self.batch is None:
            return None
        item = self.table.item(row, 0)
        idx = item.data(QtCore.Qt.UserRole) if item is not None else row
        if idx is None or not 0 <= int(idx) < len(self.batch.records):
            return None
        rec = self.batch.records[int(idx)]
        path = rec.get("path")
        if not path:
            self.status.setText(f"Lauf „{rec.get('label')}“ wurde nicht gespeichert (Option „Läufe speichern“).")
            return None
        try:
            from ...ad.results import ADResult
            result = ADResult.load(path)
        except Exception as exc:
            self.status.setText(f"<span style='color:{FAIL}'>Laden fehlgeschlagen: {exc}</span>")
            return None
        self.status.setText(f"Lauf „{rec.get('label')}“ geladen")
        self.result_loaded.emit(result)
        return result
