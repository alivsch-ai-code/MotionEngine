"""Shared helpers of the stabilization examples (plots are saved to examples/stabilization/output/)."""

import math
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

# categorical slots 1-3 of the validated reference palette (fixed order), ink colors for text / reference
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def style(ax, ylabel="", xlabel=""):
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.set_ylabel(ylabel, color=INK, fontsize=9)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK, fontsize=9)


def save(fig, name):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"gespeichert: {path}")
    return path


def draw_vehicle(ax, x, y, psi, length=4.8, width=1.85, cg_to_rear_end=2.45, color=MUTED, lw=0.7):
    # rectangle outline of the vehicle body around the CoG
    c, s = math.cos(psi), math.sin(psi)
    pts = [(-cg_to_rear_end, -width / 2), (length - cg_to_rear_end, -width / 2),
           (length - cg_to_rear_end, width / 2), (-cg_to_rear_end, width / 2), (-cg_to_rear_end, -width / 2)]
    ax.plot([x + c * a - s * b for a, b in pts], [y + s * a + c * b for a, b in pts], color=color, lw=lw)


def stop_motion(ax, log, every=4.0, color=MUTED, lw=0.6):
    t = np.asarray(log["t"])
    for tk in np.arange(0.0, t[-1], every):
        k = int(np.argmin(np.abs(t - tk)))
        draw_vehicle(ax, log["x"][k], log["y"][k], log["psi"][k], color=color, lw=lw)
