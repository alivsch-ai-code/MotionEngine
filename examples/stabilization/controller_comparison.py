"""Comparison of all tracking controllers on the same trajectory (double lane change 15 -> 20 m/s, initial
lateral offset 0.3 m) on the DESM plant and on the double-track model (model error).

Output: examples/stabilization/output/controller_comparison.csv and controller_comparison.png
"""

import numpy as np
from plotting import OUTPUT, SERIES, plt, save, style

from vdsim.core.parameters import load_vehicle_preset
from vdsim.stabilization.simulate import run_closed_loop
from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_lateral_offset

CONTROLLERS = [("werling_bilevel", {}), ("composite", {"lateral": "pure_pursuit", "longitudinal": "ff_fb"}),
               ("composite", {"lateral": "stanley", "longitudinal": "pid"}),
               ("composite", {"lateral": "lqr", "longitudinal": "speed_pi"}),
               ("composite", {"lateral": "mpc", "longitudinal": "ff_fb"})]


def main():
    cfg = load_vehicle_preset("mid_size_sedan")
    path = path_from_lateral_offset([(40, 50, 3.5), (120, 50, -3.5)], 300)
    traj = build_trajectory(path, SpeedProfile([(0, 15), (3, 15), (8, 20), (12, 20)]), reference_point="cog")
    p0 = traj.sample(0)
    rows, logs = [], {}
    for plant in ("werling_desm", "double_track"):
        for spec, params in CONTROLLERS:
            name = spec if spec != "composite" else f"{params['lateral']}+{params['longitudinal']}"
            log, comps = run_closed_loop(spec, traj, cfg, duration=11.0, plant=plant, controller_params=params,
                                         ego_initial=dict(x=p0.x, y=p0.y + 0.3, psi=p0.theta, v=15.0))
            late = log["t"] > 3.0
            rows.append((plant, name, np.max(np.abs(log["e_n"][late])), np.max(np.abs(log["e_t"][late])),
                         np.max(np.abs(log["e_v"][late])), 1e3 * np.mean(log["compute_time"])))
            if plant == "werling_desm":
                logs[name] = log
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT / "controller_comparison.csv", "w", encoding="utf-8") as f:
        f.write("strecke;regler;max_e_n_m;max_e_t_m;max_e_v_mps;rechenzeit_ms\n")
        for r in rows:
            f.write(f"{r[0]};{r[1]};{r[2]:.4f};{r[3]:.4f};{r[4]:.4f};{r[5]:.3f}\n")
    for r in rows:
        print(f"{r[0]:13s} {r[1]:22s} e_n={r[2]:.3f} m  e_t={r[3]:.3f} m  e_v={r[4]:.3f} m/s  {r[5]:.2f} ms")
    # one panel per controller group (max. three series per panel)
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    names = list(logs)
    for ax, group in zip(axes, (names[:3], [names[0]] + names[3:])):
        for color, name in zip(SERIES, group):
            ax.plot(logs[name]["t"], logs[name]["e_n"], color=color, lw=1.2, label=name)
        ax.legend(fontsize=8, frameon=False)
        style(ax, "e_n / m")
    style(axes[-1], "e_n / m", "t / s")
    fig.suptitle("Querfehler der Trackingregler (DESM, Doppelspurwechsel 15 -> 20 m/s)", fontsize=11)
    save(fig, "controller_comparison.png")


if __name__ == "__main__":
    main()
