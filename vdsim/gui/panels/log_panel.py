"""Log panel: shows the vdsim log messages inside the GUI."""

import logging

from PySide6 import QtCore, QtWidgets


class _Emitter(QtCore.QObject):
    message = QtCore.Signal(str)


class QtLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.emitter = _Emitter()
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S"))

    def emit(self, record):
        self.emitter.message.emit(self.format(record))


class LogPanel(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(2000)
        self.handler = QtLogHandler()
        self.handler.emitter.message.connect(self.appendPlainText)
        logging.getLogger("vdsim").addHandler(self.handler)

    def closeEvent(self, event):
        logging.getLogger("vdsim").removeHandler(self.handler)
        super().closeEvent(event)
