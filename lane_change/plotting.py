"""matplotlib figures for the lane-change simulations."""

import matplotlib.pyplot as plt
import numpy as np

from .steering import correction_factor

# Fixed colors per entity, used in every figure
IDEAL = "#555555"
UNCORRECTED = "#eb6834"
CORRECTED = "#2a78d6"
LATENCY_COLORS = {"system": CORRECTED, "typical": "#1baf7a", "high": "#eda100"}


def plot_simple(ideal, uncorrected, corrected, lane_width, title):
    # Overview: trajectories and the lateral offset built up against the ideal lane change
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    ax1.axhline(lane_width, color=IDEAL, lw=0.5)
    ax1.annotate("target lane center", (0.0, lane_width), textcoords="offset points", xytext=(0, 4))
    ax1.plot(ideal["x"], ideal["y"], color=IDEAL, ls="--", label="ideal")
    ax1.plot(uncorrected["x"], uncorrected["y"], color=UNCORRECTED, label="with error")
    ax1.plot(corrected["x"], corrected["y"], color=CORRECTED, label="with error, corrected")
    ax1.set_ylabel("y (m)")
    ax1.set_title("Trajectory")
    ax1.legend(loc="lower right")

    ax2.axhline(0.0, color=IDEAL, ls="--", lw=1.0)
    for sim, color, name in ((uncorrected, UNCORRECTED, "with error"), (corrected, CORRECTED, "corrected")):
        dy = (sim["y"] - ideal["y"]) * 100
        ax2.plot(sim["x"], dy, color=color)
        ax2.annotate(f"{name}: {dy[-1]:+.1f} cm", (sim["x"][-1], dy[-1]),
                     textcoords="offset points", xytext=(-4, 6), ha="right")
    ax2.margins(y=0.15)
    ax2.set_xlabel("x (m)")
    ax2.set_ylabel("y offset to ideal (cm)")
    ax2.set_title("Built-up lateral offset")

    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_characteristic(characteristic, k_full_lock, k_full_lock_assumed, k_lane_change):
    # Static view of the distorted steering characteristic up to full lock
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.5))
    lane_change_label = f"lane change 120 km/h (|k| ≤ {k_lane_change:.5f} 1/m)"

    ax = axs[0]
    k_req = np.linspace(0.0, k_full_lock, 601)
    ax.plot(k_req, k_req, color=IDEAL, ls="--", label="ideal")
    ax.plot(k_req, characteristic(k_req), color=UNCORRECTED, label="distorted")
    ax.plot([k_full_lock_assumed], [k_full_lock], "o", color=UNCORRECTED)
    ax.annotate(f"full lock: {k_full_lock_assumed} → {k_full_lock}", (k_full_lock_assumed, k_full_lock),
                textcoords="offset points", xytext=(8, -16))
    ax.set_xlabel("requested curvature (1/m)")
    ax.set_ylabel("applied curvature (1/m)")
    ax.set_title("Steering characteristic")
    ax.legend()

    ax = axs[1]
    k_req = np.linspace(k_full_lock_assumed / 1000, k_full_lock_assumed, 400)
    ax.plot(k_req, (characteristic(k_req) / k_req - 1.0) * 100, color=UNCORRECTED)
    ax.axvline(k_lane_change, color=CORRECTED, ls=":", label=lane_change_label)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("requested curvature (1/m)")
    ax.set_ylabel("error (%)")
    ax.set_title("Curvature error up to full lock")
    ax.legend()

    ax = axs[2]
    k_des = np.linspace(k_full_lock / 1000, k_full_lock, 400)
    ax.plot(k_des, correction_factor(characteristic, k_full_lock_assumed, k_des), color=CORRECTED)
    ax.axvline(k_lane_change, color=CORRECTED, ls=":", label=lane_change_label)
    ax.set_xlabel("desired curvature (1/m)")
    ax.set_ylabel("k_sent / k_des")
    ax.set_title("Theoretical correction factor")
    ax.legend()

    fig.tight_layout()
    return fig


def plot_scenario(ideal, uncorrected, corrected, title):
    fig, axs = plt.subplots(2, 2, figsize=(13, 8))

    ax = axs[0, 0]
    ax.plot(ideal["x"], ideal["y"], color=IDEAL, ls="--", label="ideal")
    ax.plot(uncorrected["x"], uncorrected["y"], color=UNCORRECTED, label="distorted, no correction")
    ax.plot(corrected["x"], corrected["y"], color=CORRECTED, label="distorted, corrected")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Trajectory")
    ax.legend()

    ax = axs[0, 1]
    t = corrected["t"]
    ax.plot(t, corrected["k_meas"], color=CORRECTED, lw=0.8, alpha=0.35, label="k_meas (corrected, noisy)")
    ax.plot(t, ideal["k_des"], color=IDEAL, ls="--", label="k_des (desired)")
    ax.plot(t, uncorrected["k_applied"], color=UNCORRECTED, label="k_applied, no correction")
    ax.plot(t, corrected["k_applied"], color=CORRECTED, label="k_applied, corrected")
    ax.plot(t, corrected["k_sent"] - corrected["k_des"], color=CORRECTED, ls=":", label="offset k_sent - k_des")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("curvature (1/m)")
    ax.set_title("Curvature")
    ax.legend(fontsize=8)

    ax = axs[1, 0]
    ax.plot(t, corrected["error_factor"], color=IDEAL, ls="--", label="error factor (true)")
    ax.plot(t, corrected["error_factor_est"], color=CORRECTED, label="error factor (estimated)")
    ax.plot(t, 1.0 / corrected["error_factor"], color=IDEAL, ls=":", label="correction factor (true)")
    ax.plot(t, 1.0 / corrected["error_factor_est"], color=CORRECTED, ls=":", label="correction factor (estimated)")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("factor (-)")
    ax.set_title("Error and correction factor")
    ax.legend(fontsize=8)

    ax = axs[1, 1]
    ax.plot(t, ideal["a_y"], color=IDEAL, ls="--", label="ideal")
    ax.plot(t, uncorrected["a_y"], color=UNCORRECTED, label="no correction")
    ax.plot(t, corrected["a_y"], color=CORRECTED, label="corrected")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("a_y (m/s²)")
    ax.set_title("Lateral acceleration")
    ax.legend()

    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_latency_comparison(ideal, corrected_runs, uncorrected, labels, uncorrected_case):
    fig, ax = plt.subplots(figsize=(12, 4))
    for case, sim in corrected_runs.items():
        ax.plot(sim["t"], (sim["y"] - ideal["y"]) * 100, color=LATENCY_COLORS[case],
                label=f"corrected, latency {labels[case]}")
    ax.plot(uncorrected["t"], (uncorrected["y"] - ideal["y"]) * 100, color=UNCORRECTED, ls="--",
            label=f"no correction, latency {labels[uncorrected_case]}")
    ax.axhline(0.0, color=IDEAL, lw=0.5)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("Δy to ideal (cm)")
    ax.set_title("Lateral deviation from the ideal lane change")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.tight_layout()
    return fig
