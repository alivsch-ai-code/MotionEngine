"""MatlabPanel: MATLAB import, analysis, code generation and component integration.

    editor          QPlainTextEdit with MATLAB syntax highlighting, load / save
    analysis        signature, variables, equations (LaTeX), control structure, complexity, call graph
    code generation Python / C++ / Rust with diagnostics panel
    interpreter     run functions with editable inputs, output display
    component       load as vdsim Component, wire into the active stack (stack_changed signal)
"""

from __future__ import annotations

import re
import traceback
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from ..theme import FAIL, MUTED, OK, WARN

TAB_TITLE = "MATLAB"


def _mono():
    f = QtGui.QFont("Consolas", 10)
    f.setStyleHint(QtGui.QFont.Monospace)
    return f


# ---------------------------------------------------------------------------- syntax highlighter
class MatlabHighlighter(QtGui.QSyntaxHighlighter):
    KEYWORDS = {"function", "end", "if", "else", "elseif", "for", "while", "switch", "case",
                "otherwise", "try", "catch", "return", "break", "continue", "persistent", "global"}
    BUILTINS = {"sin", "cos", "tan", "exp", "log", "sqrt", "abs", "sign", "max", "min", "mod",
                "zeros", "ones", "eye", "length", "size", "reshape", "diag", "norm", "cross", "dot",
                "atan2", "asin", "acos", "atan", "ceil", "floor", "round", "pi", "inf", "nan",
                "true", "false"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        kw = QtGui.QTextCharFormat()
        kw.setForeground(QtGui.QColor("#c586c0"))
        kw.setFontWeight(QtGui.QFont.Bold)
        self._rules.append((re.compile(r"\b(" + "|".join(self.KEYWORDS) + r")\b"), kw))
        bi = QtGui.QTextCharFormat()
        bi.setForeground(QtGui.QColor("#dcdcaa"))
        self._rules.append((re.compile(r"\b(" + "|".join(self.BUILTINS) + r")\b"), bi))
        num = QtGui.QTextCharFormat()
        num.setForeground(QtGui.QColor("#b5cea8"))
        self._rules.append((re.compile(r"\b\d+\.?\d*([eE][+-]?\d+)?\b"), num))
        st = QtGui.QTextCharFormat()
        st.setForeground(QtGui.QColor("#ce9178"))
        self._rules.append((re.compile(r"'[^']*'"), st))
        op = QtGui.QTextCharFormat()
        op.setForeground(QtGui.QColor("#d4d4d4"))
        self._rules.append((re.compile(r"[+\-*/\\^~<>=&|!@:;,\[\](){}.]"), op))
        self._comment = QtGui.QTextCharFormat()
        self._comment.setForeground(QtGui.QColor("#6a9955"))

    def highlightBlock(self, text):
        for rx, fmt in self._rules:
            for m in rx.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)
        cm = text.find("%")
        if cm >= 0:
            self.setFormat(cm, len(text) - cm, self._comment)


# ---------------------------------------------------------------------------- editor widget
class MatlabEditor(QtWidgets.QWidget):
    file_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.path = None
        bar = QtWidgets.QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        self.path_label = QtWidgets.QLabel("Keine Datei geladen")
        self.path_label.setStyleSheet(f"color: {MUTED};")
        self.btn_open = QtWidgets.QPushButton("Öffnen …")
        self.btn_open.clicked.connect(self.open_file)
        self.btn_save = QtWidgets.QPushButton("Speichern")
        self.btn_save.clicked.connect(self.save_file)
        self.btn_new = QtWidgets.QPushButton("Neu")
        self.btn_new.clicked.connect(self.new_file)
        bar.addWidget(self.path_label, 1)
        bar.addWidget(self.btn_new)
        bar.addWidget(self.btn_open)
        bar.addWidget(self.btn_save)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setFont(_mono())
        self.editor.setTabStopDistance(QtGui.QFontMetricsF(self.editor.font()).horizontalAdvance("    "))
        self.editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self._hl = MatlabHighlighter(self.editor.document())

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(bar)
        layout.addWidget(self.editor, 1)

        self.editor.setPlainText(_TEMPLATE)

    def open_file(self, path=None):
        if path is None:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "MATLAB-Datei öffnen", "",
                                                             "MATLAB (*.m);;Alle Dateien (*)")
            if not path:
                return
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        self.editor.setPlainText(text)
        self.path = path
        self.path_label.setText(str(path))
        self.file_changed.emit(path)

    def save_file(self, path=None):
        if path is None:
            path = self.path
        if path is None:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "MATLAB-Datei speichern", "controller.m",
                                                             "MATLAB (*.m)")
            if not path:
                return
        Path(path).write_text(self.editor.toPlainText(), encoding="utf-8")
        self.path = path
        self.path_label.setText(str(path))

    def new_file(self):
        self.editor.setPlainText(_TEMPLATE)
        self.path = None
        self.path_label.setText("Neue Datei (nicht gespeichert)")

    def source(self):
        return self.editor.toPlainText()


_TEMPLATE = """\
function [u] = my_controller(y_d, y, e_prev, dt, Kp, Ki, Kd)
% Einfacher PID-Regler als Vorlage.
% y_d: Sollwert, y: Istwert
% e_prev: vorheriger Fehler (persistent)
% dt: Abtastzeit, Kp/Ki/Kd: Reglerparameter

persistent e_int;
if isempty(e_int)
    e_int = 0;
end

e = y_d - y;
e_int = e_int + e * dt;
e_dot = (e - e_prev) / dt;

u = Kp * e + Ki * e_int + Kd * e_dot;
"""


# ---------------------------------------------------------------------------- analysis view
class AnalysisView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.sig_table = _table(["Eingang", "Typ", "Signal-Rolle"])
        self.out_table = _table(["Ausgang", "Typ", "Abhängigkeiten"])
        self.var_table = _table(["Variable", "Rolle", "Typ", "Signal", "Def-Zeilen", "Use-Zeilen"])
        self.eq_list = QtWidgets.QTextEdit()
        self.eq_list.setReadOnly(True)
        self.eq_list.setFont(_mono())
        self.ctrl_text = QtWidgets.QTextEdit()
        self.ctrl_text.setReadOnly(True)
        self.ctrl_text.setFont(_mono())
        self.diag_text = QtWidgets.QTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setFont(_mono())
        self.tabs.addTab(self._sig_page(), "Signatur")
        self.tabs.addTab(self.var_table, "Variablen")
        self.tabs.addTab(self.eq_list, "Gleichungen")
        self.tabs.addTab(self.ctrl_text, "Reglerstruktur")
        self.tabs.addTab(self.diag_text, "Diagnostik")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

    def _sig_page(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.addWidget(QtWidgets.QLabel("Eingänge:"))
        lay.addWidget(self.sig_table)
        lay.addWidget(QtWidgets.QLabel("Ausgänge:"))
        lay.addWidget(self.out_table)
        return w

    def set_analysis(self, fa):
        if fa is None:
            for t in (self.sig_table, self.out_table, self.var_table):
                t.setRowCount(0)
            self.eq_list.clear()
            self.ctrl_text.clear()
            self.diag_text.clear()
            return

        _fill(self.sig_table, [(v.name, v.type, v.signal or "-") for v in fa.variables.values()
                                if v.role == "input"])
        deps = fa.output_dependencies or {}
        _fill(self.out_table, [(v.name, v.type, ", ".join(deps.get(v.name, [])) or "-")
                                for v in fa.variables.values() if v.role in ("output", "inout")])
        _fill(self.var_table, [(v.name, v.role, v.type, v.signal or "-",
                                 ", ".join(str(d) for d in v.defs[:5]),
                                 ", ".join(str(u) for u in v.uses[:5]))
                                for v in fa.variables.values()])

        lines = []
        for a in fa.assignments:
            eq_refs = ", ".join(a.get("equations", []))
            matlab = a.get("matlab", "")
            latex = a.get("latex", "")
            ref = f"  % ({eq_refs})" if eq_refs else ""
            lines.append(f"Zeile {a.get('line', '?'):>3}: {matlab}{ref}")
            if latex:
                lines.append(f"         LaTeX: ${latex}$")
        self.eq_list.setPlainText("\n".join(lines) or "Keine Zuweisungen erkannt.")

        ctrl = fa.control or {}
        cl = []
        cl.append(f"Struktur:     {ctrl.get('structure', '-')}")
        cl.append(f"Verstärkungen: {', '.join(ctrl.get('gains', [])) or '-'}")
        cl.append(f"Referenz:     {', '.join(ctrl.get('references', [])) or '-'}")
        cl.append(f"Messung:      {', '.join(ctrl.get('measurements', [])) or '-'}")
        cl.append(f"Fehler:       {', '.join(ctrl.get('errors', [])) or '-'}")
        cl.append(f"Feedback:     {', '.join(ctrl.get('feedback', [])) or '-'}")
        cl.append(f"Feedforward:  {', '.join(ctrl.get('feedforward', [])) or '-'}")
        cl.append(f"Integrator:   {', '.join(ctrl.get('integrators', [])) or '-'}")
        cl.append(f"Differenzierer: {', '.join(ctrl.get('differentiators', [])) or '-'}")
        cpx = fa.complexity or {}
        cl.append("\nKomplexität:")
        cl.append(f"  Zyklomatisch: {cpx.get('cyclomatic', '-')}")
        cl.append(f"  Max. Tiefe:   {cpx.get('max_nesting', '-')}")
        cl.append(f"  Zeilen:       {cpx.get('lines', '-')}")
        cl.append(f"  Zuweisungen:  {cpx.get('assignments', '-')}")
        self.ctrl_text.setPlainText("\n".join(cl))

        dl = []
        for v in fa.unused_variables:
            dl.append(f"⚠ Unbenutzte Variable: {v}")
        for v in fa.unused_inputs:
            dl.append(f"⚠ Unbenutzter Eingang: {v}")
        for c in fa.unknown_calls:
            dl.append(f"? Unbekannter Aufruf: {c}")
        self.diag_text.setPlainText("\n".join(dl) or "Keine Auffälligkeiten.")


# ---------------------------------------------------------------------------- code generation view
class CodeGenView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        self.lang = QtWidgets.QComboBox()
        self.lang.addItems(["Python (NumPy)", "C++17", "Rust"])
        self.lang.setCurrentIndex(0)
        self.btn_gen = QtWidgets.QPushButton("Generieren")
        self.btn_export = QtWidgets.QPushButton("Exportieren …")
        self.btn_export.setEnabled(False)
        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet(f"color: {MUTED};")
        row.addWidget(QtWidgets.QLabel("Zielsprache:"))
        row.addWidget(self.lang)
        row.addWidget(self.btn_gen)
        row.addWidget(self.btn_export)
        row.addWidget(self.status, 1)

        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(_mono())
        self.diag_list = QtWidgets.QTextEdit()
        self.diag_list.setReadOnly(True)
        self.diag_list.setFont(_mono())
        self.diag_list.setMaximumHeight(120)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(row)
        layout.addWidget(self.output, 1)
        layout.addWidget(QtWidgets.QLabel("Diagnose:"))
        layout.addWidget(self.diag_list)

        self._code = None
        self.btn_gen.clicked.connect(self._placeholder_gen)
        self.btn_export.clicked.connect(self._export)

    def _placeholder_gen(self):
        pass

    def set_generated(self, code):
        self._code = code
        if code is None:
            self.output.clear()
            self.diag_list.clear()
            self.status.setText("")
            self.btn_export.setEnabled(False)
            return
        source = "\n".join(code.files.values()) if code.files else ""
        self.output.setPlainText(source)
        dl = []
        for d in code.diagnostics:
            sev = getattr(d, "severity", "info")
            icon = {"error": "X", "warning": "!"}.get(sev, "i")
            dl.append(f"{icon} [{sev}] Zeile {getattr(d, 'line', '?')}: {getattr(d, 'message', d)}")
        self.diag_list.setPlainText("\n".join(dl) or "Keine Diagnosen.")
        ok = code.ok
        n_files = len(code.files)
        self.status.setText(f"<span style='color:{OK if ok else FAIL}'>"
                            f"{'OK' if ok else 'Fehler'} ({n_files} Datei(en), "
                            f"{len(code.diagnostics)} Diagnosen)</span>")
        self.btn_export.setEnabled(ok)

    def _export(self):
        if self._code is None or not self._code.files:
            return
        ext = {0: "py", 1: "cpp", 2: "rs"}.get(self.lang.currentIndex(), "txt")
        if len(self._code.files) == 1:
            content = next(iter(self._code.files.values()))
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Code exportieren", f"generated.{ext}",
                                                             f"Quellcode (*.{ext});;Alle Dateien (*)")
            if path:
                Path(path).write_text(content, encoding="utf-8")
                self.status.setText(f"Exportiert: {path}")
        else:
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Zielordner")
            if folder:
                for name, content in self._code.files.items():
                    (Path(folder) / name).write_text(content, encoding="utf-8")
                self.status.setText(f"Exportiert: {len(self._code.files)} Dateien nach {folder}")


# ---------------------------------------------------------------------------- interpreter view
class InterpreterView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.func_combo = QtWidgets.QComboBox()
        self.func_combo.setMinimumWidth(200)
        self.btn_run = QtWidgets.QPushButton("Ausführen")
        self.btn_run.setObjectName("primary")
        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet(f"color: {MUTED};")

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QtWidgets.QLabel("Funktion:"))
        row.addWidget(self.func_combo)
        row.addWidget(self.btn_run)
        row.addWidget(self.status, 1)

        self.input_table = _table(["Parameter", "Wert"])
        self.input_table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        self.output_text = QtWidgets.QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(_mono())
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(_mono())
        self.log_text.setMaximumHeight(100)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(row)
        layout.addWidget(QtWidgets.QLabel("Eingabewerte:"))
        layout.addWidget(self.input_table)
        layout.addWidget(QtWidgets.QLabel("Ergebnis:"))
        layout.addWidget(self.output_text, 1)
        layout.addWidget(QtWidgets.QLabel("Interpreter-Ausgabe:"))
        layout.addWidget(self.log_text)

    def set_functions(self, names, default_params=None):
        self.func_combo.clear()
        for n in names:
            self.func_combo.addItem(n)
        self._default_params = default_params or {}

    def set_params(self, params):
        self.input_table.setRowCount(len(params))
        for i, (name, default) in enumerate(params):
            n_item = QtWidgets.QTableWidgetItem(name)
            n_item.setFlags(n_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.input_table.setItem(i, 0, n_item)
            self.input_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(default)))
        self.input_table.resizeColumnsToContents()

    def get_args(self):
        args = []
        for i in range(self.input_table.rowCount()):
            item = self.input_table.item(i, 1)
            text = item.text().strip() if item else "0"
            try:
                if "," in text or text.startswith("["):
                    import numpy as np
                    args.append(np.array([float(x) for x in text.strip("[] ").split(",")]).reshape(-1, 1))
                else:
                    args.append(float(text))
            except ValueError:
                args.append(0.0)
        return args


# ---------------------------------------------------------------------------- component view
class ComponentView(QtWidgets.QWidget):
    stack_changed = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        form = QtWidgets.QFormLayout()
        self.backend = QtWidgets.QComboBox()
        self.backend.addItems(["interpreter", "python"])
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("(automatisch aus Funktionsname)")
        self.layer = QtWidgets.QComboBox()
        self.layer.addItems(["controller", "planner", "behavior", "dynamics", "perception"])
        self.params_text = QtWidgets.QPlainTextEdit()
        self.params_text.setFont(_mono())
        self.params_text.setMaximumHeight(100)
        self.params_text.setPlaceholderText('{"Kp": 1.0, "Ki": 0.1, "Kd": 0.01}')
        form.addRow("Backend:", self.backend)
        form.addRow("Komponentenname:", self.name_edit)
        form.addRow("Stack-Ebene:", self.layer)
        form.addRow("Feste Parameter (JSON):", self.params_text)

        self.btn_load = QtWidgets.QPushButton("Als Komponente laden")
        self.btn_load.setObjectName("primary")
        self.btn_wire = QtWidgets.QPushButton("In Stack einsetzen")
        self.btn_wire.setEnabled(False)
        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        self.info = QtWidgets.QTextEdit()
        self.info.setReadOnly(True)
        self.info.setFont(_mono())

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(form)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.btn_load)
        row.addWidget(self.btn_wire)
        layout.addLayout(row)
        layout.addWidget(self.status)
        layout.addWidget(self.info, 1)

        self._component = None


# ---------------------------------------------------------------------------- main panel
class MatlabPanel(QtWidgets.QWidget):
    TAB_TITLE = "MATLAB"
    stack_changed = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mfile = None
        self._analysis = None

        self.editor = MatlabEditor()
        self.analysis_view = AnalysisView()
        self.codegen_view = CodeGenView()
        self.interp_view = InterpreterView()
        self.comp_view = ComponentView()

        right = QtWidgets.QTabWidget()
        right.setDocumentMode(True)
        right.addTab(self.analysis_view, "Analyse")
        right.addTab(self.codegen_view, "Codegenerierung")
        right.addTab(self.interp_view, "Interpreter")
        right.addTab(self.comp_view, "Komponente")
        self._right_tabs = right

        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.addWidget(self.editor)
        split.addWidget(right)
        split.setSizes([600, 700])

        btn_bar = QtWidgets.QHBoxLayout()
        self.btn_analyze = QtWidgets.QPushButton("Analysieren (F6)")
        self.btn_analyze.setObjectName("primary")
        self.btn_analyze.setShortcut("F6")
        self.btn_analyze.clicked.connect(self._analyze)
        self.main_status = QtWidgets.QLabel("")
        self.main_status.setStyleSheet(f"color: {MUTED};")
        btn_bar.addWidget(self.btn_analyze)
        btn_bar.addWidget(self.main_status, 1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(btn_bar)
        layout.addWidget(split, 1)

        self.editor.file_changed.connect(lambda _: self._analyze())
        self.codegen_view.btn_gen.clicked.disconnect()
        self.codegen_view.btn_gen.clicked.connect(self._generate)
        self.interp_view.btn_run.clicked.connect(self._run_interpreter)
        self.interp_view.func_combo.currentIndexChanged.connect(self._func_selected)
        self.comp_view.btn_load.clicked.connect(self._load_component)
        self.comp_view.btn_wire.clicked.connect(self._wire_component)
        self.comp_view.stack_changed.connect(self.stack_changed)

    # ------------------------------------------------------------------ parse & analyze
    def _analyze(self):
        source = self.editor.source()
        if not source.strip():
            self.main_status.setText("Kein Quelltext vorhanden.")
            return
        try:
            from ...matlab.parser import parse
            self._mfile = parse(source)
        except Exception as exc:
            self._mfile = None
            self._analysis = None
            self.main_status.setText(f"<span style='color:{FAIL}'>Parse-Fehler: {exc}</span>")
            self.analysis_view.set_analysis(None)
            return
        try:
            from ...matlab.analysis import analyze as matlab_analyze
            self._analysis = matlab_analyze(self._mfile)
        except Exception as exc:
            self._analysis = None
            self.main_status.setText(f"<span style='color:{WARN}'>Analyse-Fehler: {exc}</span>")
            return
        funcs = [f.name for f in self._analysis.functions]
        if funcs:
            self.interp_view.set_functions(funcs)
            self._func_selected(0)
            main = self._analysis.function(funcs[0])
            self.analysis_view.set_analysis(main)
            n_eq = sum(len(a.get("equations", [])) for a in main.assignments)
            self.main_status.setText(
                f"<span style='color:{OK}'>✔ {len(funcs)} Funktion(en), "
                f"{len(main.variables)} Variablen, {n_eq} Gleichungsverweise</span>")
        else:
            self.main_status.setText(f"<span style='color:{WARN}'>Keine Funktionen gefunden (Skript?)</span>")
            self.analysis_view.set_analysis(None)

    def _func_selected(self, idx):
        if self._analysis is None or idx < 0:
            return
        funcs = self._analysis.functions
        if idx >= len(funcs):
            return
        fa = funcs[idx]
        self.analysis_view.set_analysis(fa)
        params = [(p, 0.0) for p in fa.inputs]
        self.interp_view.set_params(params)

    # ------------------------------------------------------------------ code generation
    def _generate(self):
        if self._mfile is None:
            self.codegen_view.set_generated(None)
            self.codegen_view.status.setText("Bitte zuerst analysieren (F6).")
            return
        lang_map = {0: "python", 1: "cpp", 2: "rust"}
        lang = lang_map.get(self.codegen_view.lang.currentIndex(), "python")
        try:
            from ...matlab.codegen import generate
            funcs = [f.name for f in (self._analysis.functions if self._analysis else [])]
            code = generate(self._mfile, lang, function=funcs[0] if funcs else None)
            self.codegen_view.set_generated(code)
        except Exception as exc:
            self.codegen_view.set_generated(None)
            self.codegen_view.status.setText(f"<span style='color:{FAIL}'>Fehler: {exc}</span>")

    # ------------------------------------------------------------------ interpreter
    def _run_interpreter(self):
        if self._mfile is None:
            self.interp_view.status.setText("Bitte zuerst analysieren (F6).")
            return
        func_name = self.interp_view.func_combo.currentText()
        if not func_name:
            return
        args = self.interp_view.get_args()
        log_lines = []
        try:
            from ...matlab.interpreter import Interpreter
            interp = Interpreter(self._mfile, output=log_lines.append)
            func = self._mfile.function(func_name)
            nout = len(func.outputs)
            result = interp.call(func_name, *args, nargout=nout)
            if not isinstance(result, tuple):
                result = (result,)
            out_lines = []
            for name, val in zip(func.outputs, result):
                out_lines.append(f"{name} = {_format_value(val)}")
            self.interp_view.output_text.setPlainText("\n".join(out_lines))
            self.interp_view.status.setText(f"<span style='color:{OK}'>✔ Ausgeführt</span>")
        except Exception as exc:
            self.interp_view.output_text.setPlainText(f"Fehler:\n{traceback.format_exc()}")
            self.interp_view.status.setText(f"<span style='color:{FAIL}'>✖ {exc}</span>")
        self.interp_view.log_text.setPlainText("\n".join(str(l) for l in log_lines) or "(keine Ausgabe)")

    # ------------------------------------------------------------------ component
    def _load_component(self):
        if self._mfile is None:
            self.comp_view.status.setText("Bitte zuerst analysieren (F6).")
            return
        import json
        import tempfile
        params_text = self.comp_view.params_text.toPlainText().strip()
        params = {}
        if params_text:
            try:
                params = json.loads(params_text)
            except json.JSONDecodeError as exc:
                self.comp_view.status.setText(f"<span style='color:{FAIL}'>JSON-Fehler: {exc}</span>")
                return

        source = self.editor.source()
        path = self.editor.path
        if path is None:
            tmp = Path(tempfile.gettempdir()) / "vdsim_matlab_panel.m"
            tmp.write_text(source, encoding="utf-8")
            path = str(tmp)

        backend = self.comp_view.backend.currentText()
        name = self.comp_view.name_edit.text().strip() or None
        try:
            from ...matlab.component import load_matlab_component
            comp = load_matlab_component(path, backend=backend, params=params, name=name)
            self.comp_view._component = comp
            self.comp_view.btn_wire.setEnabled(True)
            info_lines = [f"Komponente: {comp.NAME} (v{comp.VERSION})",
                          f"Backend:    {comp.BACKEND}",
                          f"Eingänge:   {', '.join(comp.INPUTS)}",
                          f"Ausgänge:   {', '.join(comp.OUTPUTS)}"]
            doc = getattr(comp, "DOC", None)
            if doc:
                info_lines.append(f"\n{getattr(doc, 'summary', '')}")
                info_lines.append(f"Zweck: {getattr(doc, 'purpose', '')}")
                eqs = getattr(doc, "equations", [])
                if eqs:
                    info_lines.append(f"Gleichungen: {', '.join(eqs[:5])}")
            self.comp_view.info.setPlainText("\n".join(info_lines))
            self.comp_view.status.setText(f"<span style='color:{OK}'>✔ Komponente geladen</span>")
        except Exception as exc:
            self.comp_view._component = None
            self.comp_view.btn_wire.setEnabled(False)
            self.comp_view.info.setPlainText(traceback.format_exc())
            self.comp_view.status.setText(f"<span style='color:{FAIL}'>✖ {exc}</span>")

    def _wire_component(self):
        comp = self.comp_view._component
        if comp is None:
            return
        layer = self.comp_view.layer.currentText()
        spec = f"matlab:{self.editor.path or 'panel.m'}"
        import json
        params_text = self.comp_view.params_text.toPlainText().strip()
        params = json.loads(params_text) if params_text else {}
        stack_update = {layer: {"component": spec, "params": params}}
        self.stack_changed.emit(stack_update)
        self.comp_view.status.setText(
            f"<span style='color:{OK}'>✔ In Stack-Ebene «{layer}» eingesetzt</span>")

    # ------------------------------------------------------------------ workbench protocol
    def set_result(self, result):
        pass

    def set_stack(self, stack):
        pass


# ---------------------------------------------------------------------------- helpers
def _table(headers):
    t = QtWidgets.QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    t.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
    return t


def _fill(table, rows):
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            table.setItem(r, c, QtWidgets.QTableWidgetItem(str(val)))
    table.resizeColumnsToContents()


def _format_value(val):
    import numpy as np
    if isinstance(val, np.ndarray):
        if val.size <= 10:
            return str(val.ravel())
        return f"[{val.shape} array, min={val.min():.4g}, max={val.max():.4g}]"
    if isinstance(val, float):
        return f"{val:.6g}"
    return str(val)
