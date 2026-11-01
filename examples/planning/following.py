"""Folgefahrt hinter einem bremsenden Vorderfahrzeug (Werling 2011, 3.5.2) mit Ablösestrategie.

Aktiv sind Geschwindigkeithalten (v_ref = 25 m/s) und Folgen (s_ref = s_v - [k0 + kv ṡ_v]).
Der Modus mit dem kleinsten Anfangsruck setzt sich durch (Schritt 6). Das Vorderfahrzeug fährt
mit 15 m/s, bremst ab t = 12 s mit -2 m/s² bis 5 m/s und beschleunigt ab t = 25 s wieder.
Bild: examples/planning/output/following.png
"""

import common  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from common import save

from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
from vdsim.geometry import ReferenceLine
from vdsim.planning import WerlingPlanner
from vdsim.planning.simulation import constant_velocity_object, run_closed_loop

K0, KV = 5.0, 1.5


def lead_state(t):
    # (x, v, a) of the leader: piecewise constant acceleration, integrated exactly
    phases = [(0.0, 0.0), (12.0, -2.0), (17.0, 0.0), (25.0, 1.0), (35.0, 0.0)]
    x, v, t_prev, a_prev = 60.0, 15.0, 0.0, 0.0
    for t_ph, a_ph in phases[1:] + [(np.inf, 0.0)]:
        dt = min(t, t_ph) - t_prev
        if dt <= 0:
            break
        x, v = x + v * dt + 0.5 * a_prev * dt * dt, v + a_prev * dt
        t_prev, a_prev = t_ph, a_ph
    a_now = 0.0
    for t_ph, a_ph in phases:
        if t >= t_ph:
            a_now = a_ph
    return x, v, a_now


def prediction(t):
    x, v, a = lead_state(t)
    return Prediction(t0=t, objects=[constant_velocity_object(1, x, 0.0, 0.0, v, t0=t, a=a)])


def main():
    road = ReferenceLine.straight(2000.0, ds=0.5)
    modes = [LongitudinalMode("velocity", {"v_ref": 25.0}), LongitudinalMode("following", {"lead_id": 1, "k0": K0,
                                                                                          "kv": KV})]

    def behavior(t, ego):
        return BehaviorCommand(t=t, reference_line=road, target_speed=25.0, modes=modes, d_min=-1.75, d_max=1.75)

    planner = WerlingPlanner()
    log = run_closed_loop(planner, behavior, EgoState(vx=22.0), 45.0, prediction)
    t = np.array(log.t)
    lead = np.array([lead_state(ti) for ti in t])
    front = planner.geometry.extent("cog")[0]
    gap = (lead[:, 0] - 2.25) - (log.array("x") + front)
    desired = K0 + KV * lead[:, 1]
    mode = np.array([d.mode == "following" for d in log.debug], dtype=float)
    fig, ax = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    ax[0].plot(t, log.array("vx"), label="Ego v")
    ax[0].plot(t, lead[:, 1], "--", label="Vorderfahrzeug v")
    ax[0].set_ylabel("v / m/s")
    ax[0].legend()
    ax[1].plot(t, gap, label="Abstand (Stoßstange)")
    ax[1].plot(t, desired, "--", label="Sollabstand k0 + kv v_v")
    ax[1].set_ylabel("Abstand / m")
    ax[1].legend()
    ax[2].plot(t, [tr.a[0] for tr in log.trajectories], label="a Soll")
    ax[2].fill_between(t, -3, 3 * mode - 3 * (1 - mode), color="#a371f7", alpha=0.15, step="mid",
                       label="Folgemodus aktiv")
    ax[2].set_ylim(-3, 3)
    ax[2].set_ylabel("a / m/s²")
    ax[2].set_xlabel("t / s")
    ax[2].legend()
    fig.suptitle("Folgefahrt mit Ablösestrategie (Werling 3.5.2, Schritt 6)")
    save(fig, "following.png")
    times = np.array([d.compute_time for d in log.debug]) * 1e3
    print(f"Abstandsfehler am Ende {gap[-1] - desired[-1]:.3f} m, Rechenzeit median {np.median(times):.1f} ms, "
          f"max {times.max():.1f} ms, Fallbacks {sum(d.fallback for d in log.debug)}")


if __name__ == "__main__":
    main()
