"""2D top-view animation of a simulation result (matplotlib), exportable as GIF or MP4."""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from .plotter import COLORS, REFERENCE


def animate(result, fps=25, follow=True, window=40.0):
    vehicle = result.metadata.get("vehicle", {}).get("vehicle", {})
    length, width = vehicle.get("length", 4.8), vehicle.get("width", 1.85)
    traj = result.metadata.get("trajectory", {})
    t = result["t"]
    frames = np.searchsorted(t, np.arange(t[0], t[-1], 1.0 / fps))

    fig, ax = plt.subplots(figsize=(10, 5))
    if traj:
        ax.plot(traj["x"], traj["y"], color=REFERENCE, ls="--", lw=1)
        cones = np.array(traj.get("cones", []))
        if len(cones):
            ax.plot(cones[:, 0], cones[:, 1], "^", color=COLORS[1], ms=5)
        for bx, by in traj.get("boundaries", []):
            ax.plot(bx, by, color="#aaaaaa", lw=0.8)
    trace, = ax.plot([], [], color=COLORS[0], lw=1.5)
    body, = ax.plot([], [], color="black", lw=1.5)
    label = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top")
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    if not follow:
        ax.set_xlim(result["x"].min() - 10, result["x"].max() + 10)
        ax.set_ylim(result["y"].min() - 10, result["y"].max() + 10)
    corners = np.array([[1, 1], [1, -1], [-1, -1], [-1, 1], [1, 1]]) * [length / 2, width / 2]

    def update(i):
        x, y, psi = result["x"][i], result["y"][i], result["psi"][i]
        c, s = np.cos(psi), np.sin(psi)
        body.set_data(x + corners[:, 0] * c - corners[:, 1] * s, y + corners[:, 0] * s + corners[:, 1] * c)
        trace.set_data(result["x"][:i + 1], result["y"][:i + 1])
        label.set_text(f"t = {t[i]:.2f} s   v = {result['speed'][i] * 3.6:.0f} km/h   a_y = {result['ay'][i]:.1f} m/s²")
        if follow:
            ax.set_xlim(x - window, x + window)
            ax.set_ylim(y - window * 0.5, y + window * 0.5)
        return trace, body, label

    return fig, FuncAnimation(fig, update, frames=frames, interval=1000 / fps, blit=False)


def save_animation(result, path, fps=25, **kwargs):
    fig, anim = animate(result, fps, **kwargs)
    if str(path).lower().endswith(".gif"):
        anim.save(path, writer=PillowWriter(fps=fps))
    else:
        anim.save(path, fps=fps)  # MP4 needs ffmpeg on the PATH
    plt.close(fig)
    return path
