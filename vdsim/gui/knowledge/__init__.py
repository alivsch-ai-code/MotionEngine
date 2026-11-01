"""Knowledge browser (GUI of vdsim.knowledge): embeddable widget KnowledgeBrowser(QWidget).

Standalone: python -m vdsim.knowledge.gui
"""

from .browser import KnowledgeBrowser
from .graph_view import GraphView

__all__ = ["GraphView", "KnowledgeBrowser"]
