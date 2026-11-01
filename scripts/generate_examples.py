#!/usr/bin/env python
"""Generate example output images for the README and documentation.

Run from the repository root:
    python scripts/generate_examples.py

Generates plots in examples/planning/output/ and examples/stabilization/output/.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXAMPLE_SCRIPTS = [
    "examples/planning/lane_change.py",
    "examples/planning/following.py",
    "examples/planning/evasion.py",
    "examples/planning/stopping.py",
    "examples/planning/consistency.py",
    "examples/stabilization/controller_comparison.py",
    "examples/stabilization/highway_gust.py",
    "examples/stabilization/slow_comparison.py",
    "examples/stabilization/reverse_maneuver.py",
]


def main():
    failed = []
    for script in EXAMPLE_SCRIPTS:
        path = REPO_ROOT / script
        if not path.exists():
            print(f"  SKIP  {script} (not found)")
            continue
        print(f"  RUN   {script}")
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"  FAIL  {script}")
            failed.append(script)
        else:
            print(f"  OK    {script}")

    if failed:
        print(f"\n{len(failed)} example(s) failed:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"\nAll {len(EXAMPLE_SCRIPTS)} examples completed successfully.")


if __name__ == "__main__":
    main()
