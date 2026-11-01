"""Zeitliche Konsistenz (Werling 2011, 3.2, Satz 3, Abb. 3.2).

Rückkehr zur Spurmitte aus 2 m Querablage mit zyklischer Neuplanung bei drei Planungsperioden:
Werling-Planer (absolutes Endzeitraster, Start auf der alten Trajektorie) gegen den naiven
Frenet-Planer (relatives Raster, Neuplanung vom Messzustand). Der konsistente Planer liefert
unabhängig von der Periode dieselbe Bewegung.
Bild: examples/planning/output/consistency.png
"""

import common  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np

from common import save
from vdsim.framework.plugins import create_component
from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode
from vdsim.geometry import ReferenceLine
from vdsim.planning.simulation import run_closed_loop


def main():
    road = ReferenceLine.straight(500.0, ds=0.5)

    def behavior(t, ego):
        return BehaviorCommand(t=t, reference_line=road, target_speed=15.0, d_min=-5.25, d_max=5.25,
                               modes=[LongitudinalMode("velocity", {"v_ref": 15.0})])

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    for ax, spec in zip(axes, ("trajectory_planner/werling", "trajectory_planner/frenet_naive")):
        for period in (0.1, 0.5, 1.0):
            planner = create_component(spec)
            log = run_closed_loop(planner, behavior, EgoState(y=2.0, vx=15.0), 8.0, period=period)
            ax.plot(log.t, log.array("y"), marker="o", ms=2, label=f"Periode {period:.1f} s")
        ax.axhline(0.0, color="k", ls="--", lw=0.6)
        ax.set_title(planner.LABEL)
        ax.set_xlabel("t / s")
        ax.legend()
    axes[0].set_ylabel("d / m")
    fig.suptitle("Zeitliche Konsistenz: Ergebnis unabhängig von der Neuplanungsfrequenz (Satz 3)")
    save(fig, "consistency.png")


if __name__ == "__main__":
    main()
