"""Anhalten an einer Haltelinie aus 50 km/h (Werling 2011, 3.5.2) mit Regimewechsel.

Unterhalb von v_s - Hysterese wechselt der Planer von d(t) mit Schwerpunkt auf d(s) mit
Hinterachsmitte (3.5.1, 3.5.4). Die Fahrzeugfront steht exakt auf der Haltelinie.
Bild: examples/planning/output/stopping.png
"""

import common  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from common import save

from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode
from vdsim.geometry import ReferenceLine
from vdsim.planning import WerlingPlanner
from vdsim.planning.simulation import run_closed_loop

S_STOP = 120.0


def main():
    road = ReferenceLine.straight(400.0, ds=0.5)

    def behavior(t, ego):
        return BehaviorCommand(t=t, reference_line=road, target_speed=14.0, d_min=-1.75, d_max=1.75,
                               modes=[LongitudinalMode("stopping", {"s_stop": S_STOP})], maneuver="stop")

    planner = WerlingPlanner()
    log = run_closed_loop(planner, behavior, EgoState(y=0.6, vx=14.0), 25.0)
    t = np.array(log.t)
    front = log.array("x") + planner.geometry.extent("cog")[0]
    regime = np.array([tr.reference_point == "rear_axle" for tr in log.trajectories])
    fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    ax[0].plot(t, front, label="Fahrzeugfront")
    ax[0].axhline(S_STOP, color="r", ls="--", label="Haltelinie")
    ax[0].set_ylabel("x / m")
    ax[0].legend()
    ax[1].plot(t, log.array("vx"), label="v")
    ax[1].axhline(3.0, color="k", ls=":", lw=0.8, label="v_s")
    ax[1].fill_between(t, 0, 15 * regime, color="#d29922", alpha=0.15, step="mid", label="d(s), Hinterachse")
    ax[1].set_ylabel("v / m/s")
    ax[1].legend()
    ax[2].plot(t, [tr.a[0] for tr in log.trajectories], label="a")
    ax[2].plot(t, log.array("y"), label="y (Querablage)")
    ax[2].set_xlabel("t / s")
    ax[2].legend()
    fig.suptitle("Anhalten an der Haltelinie (Werling 3.5.2)")
    save(fig, "stopping.png")
    print(f"Front {front[-1]:.4f} m (Haltelinie {S_STOP} m), v_end {log.ego[-1].vx:.2e} m/s, "
          f"Regimewechsel bei v = {log.trajectories[int(np.argmax(regime))].v[0]:.2f} m/s")


if __name__ == "__main__":
    main()
