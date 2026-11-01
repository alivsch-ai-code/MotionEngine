"""Fast driving (30 m/s) with an evasive maneuver and a strong side-wind gust: bi-level stabilization.

Low-level: exact I/O linearization (Satz 8) with speed dependent look-ahead lambda(zeta, v) (4.70) and the
dynamic reference transformation (4.71)-(4.74). High-level: the elliptic error-rate measure (4.5.1)
triggers a re-initialization, the planner (stand-in: replan_from_prediction) restarts the trajectory at the
predicted vehicle state (4.5.2) and merges back into the lane. Compared: with and without re-initialization.

Output: examples/stabilization/output/highway_gust.png
"""

import numpy as np
from plotting import SERIES, plt, save, style

from vdsim.core.parameters import load_vehicle_preset
from vdsim.stabilization.simulate import run_closed_loop
from vdsim.stabilization.trajectories import (
    SpeedProfile,
    build_trajectory,
    path_from_lateral_offset,
    replan_from_prediction,
)

GUST = [{"t": 7.0, "duration": 0.4, "fy": 7000.0, "mz": 2500.0}]   # side wind gust at the CoG


def main():
    cfg = load_vehicle_preset("mid_size_sedan")
    path = path_from_lateral_offset([(60, 50, 3.5), (140, 50, -3.5)], 450)
    traj = build_trajectory(path, SpeedProfile([(0, 30.0), (13, 30.0)]), reference_point="cog")

    def planner(t, ego, status, tr):
        if status is not None and status.reinit_request and \
                not (tr.reinitialized and tr.metadata.get("replanned_at", -1) >= status.prediction["t"] - 0.2):
            return replan_from_prediction(tr, status.prediction, blend_time=3.0)
        return tr
    runs = {}
    for label, provider in (("Bi-level (mit Reinitialisierung)", planner), ("nur Low-level", None)):
        log, comps = run_closed_loop("werling_bilevel", traj, cfg, duration=12.0, provider=provider,
                                     ego_initial=dict(x=0.0, y=0.0, psi=0.0, v=30.0),
                                     plant_params={"disturbances": GUST})
        runs[label] = log
        events = comps["controller"].monitor.events
        print(f"{label}: Reinitialisierungen {[round(e[0], 2) for e in events] if provider else '-'}, "
              f"max |e_n| (vor Böe) = {np.max(np.abs(log['e_n'][log['t'] < 7.0])) * 100:.1f} cm, "
              f"max |e_n| (nach Böe) = {np.max(np.abs(log['e_n'][log['t'] >= 7.0])) * 100:.1f} cm, "
              f"max |d delta/dt| = {np.nanmax(np.abs(log['steer_rate_cmd'])):.3f} rad/s, "
              f"lambda bei 30 m/s = {log['lookahead'][100]:.1f} m, "
              f"Rechenzeit {np.mean(log['compute_time']) * 1e3:.2f} ms/Schritt")

    fig, axes = plt.subplots(5, 1, figsize=(10, 11), sharex=True)
    ax = axes[0]
    ax.plot(traj.t, traj.y, color="#0b0b0b", lw=0.8, label="ursprüngliche Solltrajektorie")
    for color, (label, log) in zip(SERIES, runs.items()):
        ax.plot(log["t"], log["y"], color=color, lw=1.2, label=label)
    style(ax, "y / m")
    ax.legend(fontsize=8, frameon=False)
    rows = [("e_n", "e_n / m"), ("e_n_dot", "ė_n / m/s"), ("delta", "δ / rad"), ("lookahead", "λ / m")]
    for ax, (key, ylabel) in zip(axes[1:], rows):
        for color, (label, log) in zip(SERIES, runs.items()):
            ax.plot(log["t"], log[key], color=color, lw=1.2, label=label)
        style(ax, ylabel)
    for ax in axes:
        ax.axvspan(GUST[0]["t"], GUST[0]["t"] + GUST[0]["duration"], color="#e4e3df", lw=0)
    log = runs["Bi-level (mit Reinitialisierung)"]
    for t in log["t"][np.flatnonzero(np.diff(log["reinit"]) > 0) + 1]:
        axes[1].axvline(t, color="#52514e", lw=0.8, ls=":")
    style(axes[-1], "λ / m", "t / s")
    fig.suptitle("Ausweichen bei 30 m/s und Seitenwindböe (grau): Low-level vs. Bi-level-Stabilisierung", fontsize=11)
    save(fig, "highway_gust.png")


if __name__ == "__main__":
    main()
