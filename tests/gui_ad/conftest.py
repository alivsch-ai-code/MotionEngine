import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")


@pytest.fixture(scope="session")
def qapp():
    from PySide6 import QtGui, QtWidgets

    from vdsim.gui.theme import apply_theme
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    apply_theme(app)
    app.setFont(QtGui.QFont("Segoe UI", 9))
    return app


@pytest.fixture(scope="session")
def demo_result():
    from vdsim.gui.ad.demo import make_demo_result
    return make_demo_result()


@pytest.fixture(scope="session")
def shot_dir(tmp_path_factory):
    # screenshots for visual self-checks (path printed by the tests with -s)
    return tmp_path_factory.mktemp("gui_ad_shots")
