"""Repository layout used by the knowledge system (all paths relative to the repository root).

    vdsim/<package>/            source (src)
    vdsim/<package>/docs/       module.yaml, theory.md, further chapters (hand-written)
    tests/<package>/, tests/    tests
    examples/<package>/         runnable examples
    docs/references/*.yaml      literature database (+ user.yaml, links.yaml)
    docs/generated/             generated documentation (never edited by hand)
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# top-level packages outside vdsim/ that are documented like vdsim packages
EXTRA_PACKAGES = ("lane_change",)


def root_dir(root=None):
    return Path(root).resolve() if root is not None else ROOT


def references_dir(root=None):
    return root_dir(root) / "docs" / "references"


def generated_dir(root=None):
    return root_dir(root) / "docs" / "generated"


def rel(path, root=None):
    # repository-relative POSIX path (stable across machines -> deterministic output)
    path = Path(path)
    try:
        return path.resolve().relative_to(root_dir(root)).as_posix()
    except ValueError:
        return path.as_posix()


def cache_dir(name="knowledge"):
    # per-user cache folder (VDSIM_CACHE_DIR overrides, e.g. in tests)
    override = os.environ.get("VDSIM_CACHE_DIR")
    if override:
        base = Path(override)
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "vdsim" / "cache"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "vdsim"
    path = base / name
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        import tempfile
        path = Path(tempfile.gettempdir()) / "vdsim_cache" / name
        path.mkdir(parents=True, exist_ok=True)
    return path
