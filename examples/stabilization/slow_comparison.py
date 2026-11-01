"""Werling 5.2: comparison of the low-level controllers on a stored slow stop-and-go trajectory.

(a) forward with orientation stabilization (Satz 4), (b) reverse with orientation stabilization,
(c) forward without orientation stabilization (Satz 6, geometric center). The trajectory starts with
v_d = 0 directly at the rear axle of the waiting vehicle (no initial tracking error), stops for one
second every few meters and changes its curvature permanently. Plant: werling_desm (forward) /
werling_kesm (reverse), full chain split range -> actuator -> plant.

Output: examples/stabilization/output/slow_comparison_signals.png, slow_comparison_path.png
"""

import math

import numpy as np
from plotting import SERIES, plt, save, stop_motion, style

from vdsim.core.parameters import load_vehicle_preset
from vdsim.stabilization.simulate import run_closed_loop
from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_curvature


def stored_trajectory(direction):
    path = path_from_curvature(lambda s: 0.14 * math.sin(s / 7.0) + 0.04 * math.sin(s / 2.9), 260)
    knots = [(0, 0)]
    t = 0.0
    for _ in range(3):                    # stop and go: 1 s standstill every ~20 s
        knots += [(t + 4, 3.0), (t + 15, 3.0), (t + 19, 0.0), (t + 20, 0.0)]
        t += 20
    return build_trajectory(path, SpeedProfile(knots), direction=direction)


def main():
    cfg = load_vehicle_preset("mid_size_sedan")
    lh, l = cfg.vehicle.cg_to_rear, cfg.vehicle.wheelbase
    cases = [("(a) vorwärts, mit Orientierungsstabilisierung", 1, "orientation", "werling_desm"),
             ("(b) rückwärts, mit Orientierungsstabilisierung", -1, "orientation", "werling_kesm"),
             ("(c) vorwärts, ohne Orientierungsstabilisierung", 1, "center", "werling_desm")]
    logs = []
    for label, direction, slow, plant in cases:
        traj = stored_trajectory(direction)
        p0 = traj.sample(0)
        ego0 = dict(x=p0.x + lh * math.cos(p0.psi), y=p0.y + lh * math.sin(p0.psi), psi=p0.psi, v=0.0,
                    delta=math.atan(l * direction * p0.kappa))
        log, comps = run_closed_loop("werling_bilevel", traj, cfg, duration=60.0, plant=plant, ego_initial=ego0,
                                     controller_params={"forward_slow": slow, "reinit_enabled": False})
        logs.append((label, log, traj))
        print(f"{label}: max |e_n| = {np.max(np.abs(log['e_n'])) * 100:.1f} cm, max |e_t| = "
              f"{np.max(np.abs(log['e_t'])) * 100:.1f} cm, max |e_theta| = {np.degrees(np.max(np.abs(log['e_theta']))):.2f}°, "
              f"Rechenzeit {np.mean(log['compute_time']) * 1e3:.2f} ms/Schritt")

    fig, axes = plt.subplots(6, 1, figsize=(9, 11), sharex=True)
    rows = [("delta", "δ / rad"), ("force_cmd", "F_l / kN"), ("vx", "v / m/s"), ("e_theta", "e_θ / rad"),
            ("e_n", "e_n / m"), ("e_t", "e_t / m")]
    for (key, ylabel), ax in zip(rows, axes):
        for color, (label, log, _) in zip(SERIES, logs):
            y = log[key] / 1000.0 if key == "force_cmd" else log[key]
            ax.plot(log["t"], y, color=color, lw=1.2, label=label)
        style(ax, ylabel)
    axes[0].legend(fontsize=8, frameon=False, loc="upper right")
    style(axes[-1], "e_t / m", "t / s")
    fig.suptitle("Lyapunov-basierte Low-level-Stabilisierungen im Vergleich (vgl. Werling Abb. 5.6)", fontsize=11)
    save(fig, "slow_comparison_signals.png")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, color, (label, log, traj) in zip(axes, SERIES, logs):
        ax.plot(traj.x, traj.y, color="#0b0b0b", lw=0.8, label="Solltrajektorie Hinterachse")
        ax.plot(log["x"], log["y"], color=color, lw=1.2, label="Schwerpunkt (Ist)")
        stop_motion(ax, log, every=5.0)
        ax.set_aspect("equal")
        ax.set_title(label, fontsize=9)
        style(ax, "y / m", "x / m")
    axes[0].legend(fontsize=8, frameon=False)
    save(fig, "slow_comparison_path.png")


if __name__ == "__main__":
    main()
