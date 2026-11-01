"""Generate docs/generated (documentation, traceability matrix, knowledge graph).

    python tools/build_docs.py            generate (idempotent, deterministic)
    python tools/build_docs.py --check    exit code 1 if the generated documentation is outdated
    python tools/build_docs.py --help     all options (report, explain, path, search, bibtex, init)
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

from vdsim.knowledge.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
