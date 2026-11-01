"""Standalone knowledge browser: python -m vdsim.knowledge.gui"""

import sys


def main(argv=None):
    from PySide6 import QtWidgets

    from ..gui.knowledge import KnowledgeBrowser

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv if argv is None else argv)
    try:
        from ..gui.theme import apply_theme
        apply_theme(app)
    except Exception:
        pass
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("vdsim – Wissensbrowser")
    window.setCentralWidget(KnowledgeBrowser())
    window.resize(1500, 950)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
