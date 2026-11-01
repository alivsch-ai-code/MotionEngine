"""AD workbench GUI: planner/controller visualization with interactive timeline, research dashboard.

    python -m vdsim.gui.ad [result.npz | --demo]
"""


def main(argv=None):
    from .workbench import main as _main
    return _main(argv)


def __getattr__(name):
    # lazy access to the public widgets (keeps `import vdsim.gui.ad` free of Qt imports)
    targets = {"ADWorkbench": "workbench", "TABS": "workbench", "PlannerView": "planner_view",
               "ResearchPanel": "research_panel", "RunOverview": "run_overview", "Timeline": "timeline",
               "make_demo_result": "demo", "make_demo_batch": "demo"}
    if name in targets:
        import importlib
        return getattr(importlib.import_module(f".{targets[name]}", __name__), name)
    raise AttributeError(name)


__all__ = ["main", "ADWorkbench", "TABS", "PlannerView", "ResearchPanel", "RunOverview", "Timeline",
           "make_demo_result", "make_demo_batch"]
