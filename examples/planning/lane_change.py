"""Spurwechsel mit dem Werling-Planer auf gerader und gekrümmter Straße (Werling 2011, 3.5.1).

Die Verhaltensebene legt die Referenzkurve auf die Mitte der Zielspur; der Planer führt den
Spurwechsel als Rückkehr auf d = 0 aus. Ausgabe: Draufsicht mit Kandidatensatz, d(t), Quer-
beschleunigung und Geschwindigkeit; Bild in examples/planning/output/lane_change.png.
"""

import common  # noqa: F401  (path setup, Agg backend)
import matplotlib.pyplot as plt
import numpy as np

from common import draw_candidates, save, status_legend
from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode
from vdsim.geometry import ReferenceLine
from vdsim.planning import WerlingPlanner
from vdsim.planning.simulation import run_closed_loop


def run(road, v=20.0, t_end=10.0):
    target = road.offset(3.5, name="Zielspur")

    def behavior(t, ego):
        return BehaviorCommand(t=t, reference_line=target, target_speed=v, d_min=-5.25, d_max=1.75,
                               modes=[LongitudinalMode("velocity", {"v_ref": v})], maneuver="lane_change_left")

    planner = WerlingPlanner()
    return run_closed_loop(planner, behavior, EgoState(x=road.x[0], y=road.y[0], psi=road.theta[0], vx=v), t_end), \
        target


def main():
    straight = ReferenceLine.straight(400.0, ds=0.5, name="gerade")
    curved = ReferenceLine.from_segments([("straight", 40.0), ("arc", 250.0, 1 / 150.0), ("straight", 100.0)],
                                         name="Kurve")
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for row, road in enumerate((straight, curved)):
        log, target = run(road)
        ax = axes[row, 0]
        dbg = log.debug[5]
        draw_candidates(ax, dbg, frenet=True)
        tr = log.trajectories[5]
        ax.plot(tr.s, tr.d, color="k", lw=0.8, ls=":", label="Ausgabe (6 s)")
        status_legend(ax)
        ax.set_xlim(tr.s[0] - 5, tr.s[0] + 100)
        ax.set_title(f"{road.name}: Kandidaten (Frenet, Zielspur) bei t = {log.t[5]:.1f} s")
        ax.set_xlabel("s / m")
        ax.set_ylabel("d / m")
        d = np.array([tr.d[0] for tr in log.trajectories])
        ay = np.array([tr.v[0] ** 2 * tr.kappa[0] for tr in log.trajectories])
        axes[row, 1].plot(log.t, d, label="d (Zielspur)")
        axes[row, 1].set_title("Querablage zur Zielspur")
        axes[row, 1].set_xlabel("t / s")
        axes[row, 1].set_ylabel("d / m")
        axes[row, 2].plot(log.t, ay, label="a_quer = v²κ")
        axes[row, 2].plot(log.t, [tr.a[0] for tr in log.trajectories], label="a_längs")
        axes[row, 2].legend()
        axes[row, 2].set_xlabel("t / s")
        axes[row, 2].set_ylabel("a / m/s²")
        times = np.array([dbg.compute_time for dbg in log.debug]) * 1e3
        print(f"{road.name}: Endablage {d[-1]:.2e} m, max |a_quer| {np.max(np.abs(ay)):.2f} m/s², "
              f"Rechenzeit median {np.median(times):.1f} ms, max {times.max():.1f} ms")
    fig.tight_layout()
    save(fig, "lane_change.png")


if __name__ == "__main__":
    main()
