"""Planner configurations (configs/planning/*.json).

File format:
    {"name": "...", "description": "...", "component": "trajectory_planner/werling@^1",
     "params": {"cost": {"terminal_deviation": {"k_delta": 400}}, ...}}
"""

from __future__ import annotations

import json
from pathlib import Path

from ..core.parameters import default_config_dir
from ..framework.plugins import create_component


def config_path(name_or_path):
    path = Path(name_or_path)
    if not path.suffix:
        path = default_config_dir() / "planning" / f"{name_or_path}.json"
    return path


def load_planner_config(name_or_path):
    # dict with "component" and "params"
    data = json.loads(config_path(name_or_path).read_text(encoding="utf-8"))
    data.setdefault("component", "trajectory_planner/werling")
    data.setdefault("params", {})
    return data


def create_planner(name_or_path="default", **overrides):
    # planner instance from a configuration file (overrides: dotted parameter names, e.g. cost.k_lat=2)
    cfg = load_planner_config(name_or_path)
    return create_component(cfg["component"], cfg["params"], **overrides)


def available_configs():
    folder = default_config_dir() / "planning"
    return sorted(p.stem for p in folder.glob("*.json"))
