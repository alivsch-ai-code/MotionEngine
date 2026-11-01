"""Shared helpers of the planning examples (plots are saved to examples/planning/output/)."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUTPUT = Path(__file__).resolve().parent / "output"

STATUS_COLORS = {0: "#3fb950", 1: "#9a9ca3", 2: "#f85149", 3: "#d0d7de"}
STATUS_LABELS = {0: "gültig", 1: "Restriktion verletzt", 2: "Kollision", 3: "nicht geprüft"}


def save(fig, name):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"gespeichert: {path}")
    return path


def draw_road(ax, ref, offsets=(-1.75, 1.75), style="k-", lw=0.8):
    for d in offsets:
        x, y = ref.point(ref.s, d)
        ax.plot(x, y, style, lw=lw)
    ax.plot(ref.x, ref.y, "k--", lw=0.6, alpha=0.6)


def draw_box(ax, x, y, psi, length, width, color, alpha=0.6):
    c, s = np.cos(psi), np.sin(psi)
    pts = np.array([[length / 2, width / 2], [length / 2, -width / 2], [-length / 2, -width / 2],
                    [-length / 2, width / 2], [length / 2, width / 2]])
    ax.fill(x + c * pts[:, 0] - s * pts[:, 1], y + s * pts[:, 0] + c * pts[:, 1], color=color, alpha=alpha, lw=0)


def draw_candidates(ax, debug, frenet=False, max_lines=150):
    # candidate set of one cycle colored by status (Werling Fig. 3.6-3.9), best trajectory on top
    xs, ys = (debug.candidates_s, debug.candidates_d) if frenet else (debug.candidates_x, debug.candidates_y)
    for i in range(min(len(xs), max_lines)):
        if i == debug.best_index:
            continue
        st = int(debug.candidates_status[i])
        ax.plot(xs[i], ys[i], color=STATUS_COLORS[st], lw=0.6, alpha=0.7)
    b = debug.best_index
    ax.plot(xs[b], ys[b], color="#1f6feb", lw=2.2, label="beste Trajektorie")


def status_legend(ax):
    for st, label in STATUS_LABELS.items():
        ax.plot([], [], color=STATUS_COLORS[st], label=label)
    ax.legend(loc="best", fontsize=7)
