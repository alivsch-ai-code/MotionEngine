"""Ausweichen um ein liegengebliebenes Fahrzeug bei Gegenverkehr (Werling 2011, 3.5.4, 5.3).

Ein stehendes Fahrzeug blockiert die eigene Spur, auf der Gegenspur kommt ein Fahrzeug
entgegen. Der Werling-Planer optimiert Quer- und Längsbewegung kombiniert: er verzögert leicht,
lässt den Gegenverkehr passieren und weicht dann aus. Zum Vergleich der sequentielle Planer
(erst längs, dann quer, Werling 3.1).
Bild: examples/planning/output/evasion.png
"""

import common  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from common import draw_box, draw_candidates, draw_road, save, status_legend

from vdsim.framework.plugins import create_component
from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
from vdsim.geometry import ReferenceLine
from vdsim.planning.simulation import constant_velocity_object, run_closed_loop

V = 14.0


def prediction(t):
    parked = constant_velocity_object(1, 70.0, 0.2, 0.0, 0.0, t0=t, obj_type="static", length=4.5, width=1.9)
    oncoming = constant_velocity_object(2, 100.0 - 12.0 * t, 3.5, np.pi, 12.0, t0=t)
    return Prediction(t0=t, objects=[parked, oncoming])


def behavior(road):
    return lambda t, ego: BehaviorCommand(t=t, reference_line=road, target_speed=V, d_min=-1.75, d_max=5.25,
                                          modes=[LongitudinalMode("velocity", {"v_ref": V})], maneuver="lane_keeping")


def main():
    road = ReferenceLine.straight(400.0, ds=0.5)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    for name, spec, color in (("Werling (kombiniert)", "trajectory_planner/werling", "#1f6feb"),
                              ("sequentiell (erst längs)", "trajectory_planner/sequential", "#d29922")):
        planner = create_component(spec)
        log = run_closed_loop(planner, behavior(road), EgoState(vx=V), 12.0, prediction)
        t = np.array(log.t)
        axes[1].plot(t, log.array("vx"), color=color, label=name)
        axes[2].plot(t, log.array("y"), color=color, label=name)
        times = np.array([d.compute_time for d in log.debug]) * 1e3
        print(f"{name}: min v {log.array('vx').min():.2f} m/s, max y {log.array('y').max():.2f} m, "
              f"Fallbacks {sum(d.fallback for d in log.debug)}, Rechenzeit median {np.median(times):.1f} ms, "
              f"max {times.max():.1f} ms")
        if spec.endswith("werling"):
            k = int(np.argmax([d.n_checked for d in log.debug]))
            ax = axes[0]
            draw_road(ax, road, offsets=(-1.75, 1.75, 5.25))
            draw_candidates(ax, log.debug[k])
            for obj in prediction(t[k]).objects:
                x, y, psi, _ = obj.state_at(t[k])
                draw_box(ax, x, y, psi, obj.length, obj.width, "#e3a33b")
            ego = log.ego[k]
            draw_box(ax, ego.x + planner.geometry.center_offset("cog"), ego.y, ego.psi, planner.geometry.length,
                     planner.geometry.width, "#3987e5")
            ax.plot(log.array("x"), log.array("y"), color="k", lw=1.0, label="gefahren")
            status_legend(ax)
            ax.set_xlim(ego.x - 10, ego.x + 80)
            ax.set_ylim(-4, 8)
            ax.set_title(f"Werling: Kandidaten bei t = {t[k]:.1f} s ({log.debug[k].n_checked} geprüft)")
    axes[1].set_ylabel("v / m/s")
    axes[1].legend()
    axes[2].set_ylabel("y / m")
    axes[2].set_xlabel("t / s")
    axes[2].legend()
    fig.tight_layout()
    save(fig, "evasion.png")


if __name__ == "__main__":
    main()
