"""Entry point of the desktop application."""

import sys

from PySide6 import QtWidgets

from ..core.logging_setup import setup_logging
from .theme import apply_theme


def main():
    setup_logging()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName("vdsim")
    apply_theme(app)
    from .ad.workbench import ADWorkbench
    window = ADWorkbench()
    window.show()
    return app.exec()


def main_legacy():
    """Start the old main window (vehicle dynamics only, no AD)."""
    setup_logging()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName("vdsim")
    apply_theme(app)
    from .main_window import MainWindow
    window = MainWindow()
    window.show()
    return app.exec()
