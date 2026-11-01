"""Dark engineering theme for the Qt application and pyqtgraph."""

import pyqtgraph as pg
from PySide6 import QtGui, QtWidgets

BACKGROUND = "#1e1f22"
PANEL = "#26282c"
BORDER = "#3a3d43"
TEXT = "#e6e6e6"
MUTED = "#9a9ca3"
ACCENT = "#3987e5"
OK, WARN, FAIL = "#3fb950", "#d29922", "#f85149"

QSS = f"""
QWidget {{ background: {BACKGROUND}; color: {TEXT}; font-size: 12px; }}
QMainWindow::separator {{ background: {BORDER}; width: 3px; height: 3px; }}
QDockWidget::title {{ background: #2b2d31; padding: 5px; font-weight: bold; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; }}
QTabBar::tab {{ background: #2b2d31; padding: 7px 14px; border: none; color: {MUTED}; }}
QTabBar::tab:selected {{ background: {PANEL}; color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QPushButton {{ background: #2f3237; border: 1px solid #44474e; padding: 5px 12px; border-radius: 4px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: #5c5f66; }}
QPushButton#primary {{ background: #2a78d6; border-color: #2a78d6; color: white; font-weight: bold; }}
QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox, QPlainTextEdit, QTextEdit {{
    background: {PANEL}; border: 1px solid #44474e; padding: 3px; border-radius: 3px; }}
QComboBox QAbstractItemView {{ background: {PANEL}; selection-background-color: #2a78d6; }}
QTableWidget, QTreeWidget, QListWidget {{ background: #232528; gridline-color: {BORDER}; alternate-background-color: #26282c; }}
QHeaderView::section {{ background: #2b2d31; padding: 4px; border: none; border-right: 1px solid {BORDER}; }}
QGroupBox {{ border: 1px solid {BORDER}; border-radius: 4px; margin-top: 14px; padding-top: 6px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; color: {MUTED}; }}
QToolBar {{ background: #2b2d31; border-bottom: 1px solid {BORDER}; spacing: 6px; padding: 3px; }}
QStatusBar {{ background: #2b2d31; color: {MUTED}; }}
QProgressBar {{ border: 1px solid {BORDER}; border-radius: 3px; text-align: center; background: {PANEL}; }}
QProgressBar::chunk {{ background: #2a78d6; }}
QFrame#kpiTile {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 6px; }}
QLabel#kpiValue {{ font-size: 20px; font-weight: bold; color: #ffffff; background: transparent; }}
QLabel#kpiCaption {{ color: {MUTED}; font-size: 11px; background: transparent; }}
QScrollArea {{ border: none; }}
"""


def apply_theme(app):
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    palette = QtGui.QPalette()
    for role, color in ((QtGui.QPalette.Window, BACKGROUND), (QtGui.QPalette.WindowText, TEXT),
                        (QtGui.QPalette.Base, PANEL), (QtGui.QPalette.AlternateBase, "#2b2d31"),
                        (QtGui.QPalette.Text, TEXT), (QtGui.QPalette.Button, "#2f3237"),
                        (QtGui.QPalette.ButtonText, TEXT), (QtGui.QPalette.Highlight, "#2a78d6"),
                        (QtGui.QPalette.HighlightedText, "#ffffff"), (QtGui.QPalette.ToolTipBase, PANEL),
                        (QtGui.QPalette.ToolTipText, TEXT)):
        palette.setColor(role, QtGui.QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(QSS)
    pg.setConfigOptions(antialias=True, background=BACKGROUND, foreground="#c8c8c8")
