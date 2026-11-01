"""Reverse driving with the bi-level controller: forward arc, stop, reverse into a parking position.

The planner is replaced by two stored rear-axle trajectories; at standstill the direction varsigma of the
active trajectory switches from +1 to -1, and the werling_bilevel controller changes from the controller
without orientation stabilization (Satz 6) to the one with orientation stabilization (Satz 4) - without a
steering angle jump. Plant: werling_kesm (drives backwards).

Output: examples/stabilization/output/reverse_maneuver.png
"""

import math

import numpy as np
from plotting import SERIES, plt, save, stop_motion, style

from vdsim.core.parameters import load_vehicle_preset
from vdsim.stabilization.simulate import run_closed_loop
from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_curvature, smooth_bump


def main():
    cfg = load_vehicle_preset("mid_size_sedan")
    lh, l = cfg.vehicle.cg_to_rear, cfg.vehicle.wheelbase
    # forward: left arc, then stop
    fwd_path = path_from_curvature(lambda s: smooth_bump(s, 4, 9, 2.0, 0.15), 20)
    fwd = build_trajectory(fwd_path, SpeedProfile([(0, 0), (3, 2.0), (6.5, 2.0), (10, 0.0), (11, 0.0)]))
    end = fwd.sample(fwd.t_end)
    # reverse: start at the stop position, rear axle path curving right (motion direction backwards)
    rev_path = path_from_curvature(lambda s: smooth_bump(s, 3, 8, 2.0, -0.17), 20, x0=end.x, y0=end.y,
                                   theta0=end.theta + math.pi)
    rev = build_trajectory(rev_path, SpeedProfile([(0, 0), (3, 1.5), (7, 1.5), (10, 0.0), (12, 0.0)]),
                           t0=fwd.t_end, direction=-1)

    def planner(t, ego, status, traj):
        return fwd if t < fwd.t_end else rev
    p0 = fwd.sample(0)
    ego0 = dict(x=p0.x + lh, y=p0.y, psi=0.0, v=0.0, delta=0.0)
    log, comps = run_closed_loop("werling_bilevel", fwd, cfg, duration=23.0, plant="werling_kesm", provider=planner,
                                 ego_initial=ego0)
    act = log["active"]
    switches = [(log["t"][i], act[i - 1], act[i]) for i in range(1, len(act)) if act[i] != act[i - 1]]
    print("Reglerwechsel:", switches)
    print(f"max |e_n| = {np.max(np.abs(log['e_n'])) * 100:.1f} cm, max |e_t| = {np.max(np.abs(log['e_t'])) * 100:.1f} cm,"
          f" max |d delta| je Schritt = {np.max(np.abs(np.diff(log['delta']))):.4f} rad")

    fig = plt.figure(figsize=(12, 7))
    ax = fig.add_subplot(1, 2, 1)
    ax.plot(fwd.x, fwd.y, color="#0b0b0b", lw=0.8, label="Soll vorwärts (Hinterachse)")
    ax.plot(rev.x, rev.y, color="#0b0b0b", lw=0.8, ls="--", label="Soll rückwärts (Hinterachse)")
    rx = log["x"] - lh * np.cos(log["psi"])
    ry = log["y"] - lh * np.sin(log["psi"])
    ax.plot(rx, ry, color=SERIES[0], lw=1.3, label="Hinterachsmitte (Ist)")
    stop_motion(ax, log, every=2.0)
    ax.set_aspect("equal")
    ax.legend(fontsize=8, frameon=False)
    style(ax, "y / m", "x / m")
    for i, (key, ylabel) in enumerate([("delta", "δ / rad"), ("vx", "v / m/s"), ("e_n", "e_n / m")]):
        a = fig.add_subplot(3, 2, 2 * (i + 1))
        a.plot(log["t"], log[key], color=SERIES[i], lw=1.2)
        a.axvline(fwd.t_end, color="#52514e", lw=0.6, ls=":")
        style(a, ylabel, "t / s" if i == 2 else "")
    fig.suptitle("Vorwärts - Stand - Rückwärts: Umschaltung Satz 6 -> Satz 4 bei v_d = 0 (ς entscheidet)", fontsize=11)
    save(fig, "reverse_maneuver.png")


if __name__ == "__main__":
    main()
