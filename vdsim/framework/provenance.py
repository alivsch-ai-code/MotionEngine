"""Reproducibility manifest stored with every result (versions, configuration hash, seeds)."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def config_hash(obj):
    text = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _git_commit(root):
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def manifest(config=None, components=None, seed=None):
    import numpy
    import scipy
    from .. import __version__
    root = Path(__file__).resolve().parents[2]
    return {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "vdsim_version": __version__,
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "platform": platform.platform(),
        "git_commit": _git_commit(root),
        "seed": seed,
        "config_hash": config_hash(config) if config is not None else None,
        "components": components or {},
    }
