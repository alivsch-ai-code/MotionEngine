"""Lane change at 120 km/h with distorted steering characteristic, latency chain and feedback correction."""

import matplotlib.pyplot as plt
import numpy as np

from lane_change.latency import LATENCY_CASES
from lane_change.plotting import plot_characteristic, plot_latency_comparison, plot_scenario, plot_simple
from lane_change.profiles import lane_change_curvature
from lane_change.simulation import simulate
from lane_change.steering import correction_factor, steering_characteristic

# Scenario parameters
V = 120.0 / 3.6         # m/s
LANE_WIDTH = 3.5        # m
DURATION = 6.0          # s, duration of the lane change
T_START = 1.0           # s, start of the lane change
T_END = 10.0            # s, end of simulation
DT = 0.005              # s, simulation step (latencies must be multiples of it)
YAW_RATE_NOISE = 0.1    # deg/s, yaw-rate sensor noise (std. dev.)
SCENARIO_CASE = "system"  # latency case of the system architecture (see README)
SHOW_DETAILS = False      # True: also show characteristic, signals and latency comparison

# Steering characteristic
K_FULL_LOCK = 0.3            # 1/m, true curvature at full steering lock
K_FULL_LOCK_DISTORTED = 0.2  # 1/m, distorted characteristic ends here: requesting 0.2 gives 0.3
ERROR_AT_ZERO = 0.10         # relative error at small curvature, rises to 50 % at full lock

ideal_steering = steering_characteristic(K_FULL_LOCK, K_FULL_LOCK, error_at_zero=0.0)
distorted_steering = steering_characteristic(K_FULL_LOCK_DISTORTED, K_FULL_LOCK, ERROR_AT_ZERO)


def k_des(t):
    return lane_change_curvature(t, V, LANE_WIDTH, DURATION, T_START)


def run(case, use_correction):
    return simulate(V, k_des, distorted_steering, LATENCY_CASES[case], T_END, DT, use_correction, YAW_RATE_NOISE)


def latency_label(case):
    total = sum(LATENCY_CASES[case].values())
    return f"{case} ({total * 1000:.0f} ms)"


def print_summary(name, sim, ideal, show_factor=False):
    line = (
        f"{name:<34} y_end = {sim['y'][-1]:6.3f} m   psi_end = {np.degrees(sim['psi'][-1]):6.3f} deg   "
        f"max|a_y| = {np.max(np.abs(sim['a_y'])):4.2f} m/s^2   max|dy| = {np.max(np.abs(sim['y'] - ideal['y'])) * 100:5.1f} cm"
    )
    if show_factor:
        gain = sim["error_factor_est"][-1]
        line += f"   factor est. {gain:.3f} -> correction {1.0 / gain:.3f}"
    print(line)


if __name__ == "__main__":
    ideal = simulate(V, k_des, ideal_steering, LATENCY_CASES["none"], T_END, DT)
    uncorrected = run(SCENARIO_CASE, use_correction=False)
    corrected = {case: run(case, use_correction=True) for case in ("system", "typical", "high")}
    labels = {case: latency_label(case) for case in LATENCY_CASES}

    k_lane_change = np.max(np.abs(ideal["k_des"]))
    error_full_lock = K_FULL_LOCK / K_FULL_LOCK_DISTORTED - 1.0
    print(f"Steering: requesting {K_FULL_LOCK_DISTORTED} gives {K_FULL_LOCK} at full lock (error {error_full_lock:.0%}), "
          f"error at small curvature {ERROR_AT_ZERO:.0%}")
    print(f"Lane change {LANE_WIDTH} m in {DURATION} s at {V * 3.6:.0f} km/h, |k| <= {k_lane_change:.5f} 1/m: "
          f"error factor {distorted_steering(k_lane_change) / k_lane_change:.3f}, "
          f"correction factor {correction_factor(distorted_steering, K_FULL_LOCK_DISTORTED, k_lane_change):.3f} (theory)")
    print_summary("ideal", ideal, ideal)
    print_summary(f"no correction, {labels[SCENARIO_CASE]}", uncorrected, ideal)
    for case, sim in corrected.items():
        print_summary(f"corrected, {labels[case]}", sim, ideal, show_factor=True)

    title = f"Lane change at {V * 3.6:.0f} km/h, latency {labels[SCENARIO_CASE]}"
    plot_simple(ideal, uncorrected, corrected[SCENARIO_CASE], LANE_WIDTH, title)
    if SHOW_DETAILS:
        plot_characteristic(distorted_steering, K_FULL_LOCK, K_FULL_LOCK_DISTORTED, k_lane_change)
        plot_scenario(ideal, uncorrected, corrected[SCENARIO_CASE], title)
        plot_latency_comparison(ideal, corrected, uncorrected, labels, SCENARIO_CASE)
    plt.show()
