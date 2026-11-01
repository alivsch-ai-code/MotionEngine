"""matplotlib figures: path, state overview, tire curves, GGV, Bode, heatmaps, energy, run comparison."""

import matplotlib.pyplot as plt
import numpy as np

from ..core.conventions import WHEEL_NAMES, G

# categorical colors in fixed order (validated palette), neutral reference color
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
REFERENCE = "#555555"
WHEEL_COLORS = dict(zip(WHEEL_NAMES, COLORS[:4]))


def _style(ax, title=None, xlabel=None, ylabel=None):
    if title:
        ax.set_title(title, fontsize=10)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def plot_path(ax, result, color=COLORS[0], label="Fahrzeug", reference=True, outlines=True):
    traj = result.metadata.get("trajectory", {})
    if reference and traj:
        for bx, by in traj.get("boundaries", []):
            ax.plot(bx, by, color="#aaaaaa", lw=0.8)
        ax.plot(traj["x"], traj["y"], color=REFERENCE, ls="--", lw=1.0, label="Referenz")
        cones = np.array(traj.get("cones", []))
        if len(cones):
            ax.plot(cones[:, 0], cones[:, 1], "^", color=COLORS[1], ms=4, label="Pylonen")
    ax.plot(result["x"], result["y"], color=color, lw=1.6, label=label)
    if outlines:
        vehicle = result.metadata.get("vehicle", {}).get("vehicle", {})
        length, width = vehicle.get("length", 4.8), vehicle.get("width", 1.85)
        t = result["t"]
        for ti in np.arange(0, t[-1], max(t[-1] / 12, 0.5)):
            i = int(np.searchsorted(t, ti))
            x, y, psi = result["x"][i], result["y"][i], result["psi"][i]
            corners = np.array([[1, 1], [1, -1], [-1, -1], [-1, 1], [1, 1]]) * [length / 2, width / 2]
            c, s = np.cos(psi), np.sin(psi)
            ax.plot(x + corners[:, 0] * c - corners[:, 1] * s, y + corners[:, 0] * s + corners[:, 1] * c,
                    color=color, lw=0.6, alpha=0.6)
    _style(ax, "Fahrzeugpfad", "x (m)", "y (m)")
    span_x = np.ptp(result["x"]) or 1.0
    span_y = np.ptp(result["y"]) or 1.0
    if span_y / span_x > 0.05:
        ax.set_aspect("equal", adjustable="datalim")
    ax.legend(fontsize=8, loc="best")


def overview_figure(result, title=None):
    fig, axs = plt.subplots(3, 2, figsize=(14, 10), layout="constrained")
    t = result["t"]
    plot_path(axs[0, 0], result)
    ax = axs[0, 1]
    ax.plot(t, result["speed"] * 3.6, color=COLORS[0], label="v")
    ax.plot(t, result["v_ref"] * 3.6, color=REFERENCE, ls="--", label="v_ref")
    _style(ax, "Geschwindigkeit", "t (s)", "km/h")
    ax.legend(fontsize=8)
    ax = axs[1, 0]
    ax.plot(t, np.degrees(result["delta_f"]), color=COLORS[0], label="Radlenkwinkel vorne")
    if np.any(result["delta_r"] != 0):
        ax.plot(t, np.degrees(result["delta_r"]), color=COLORS[2], label="hinten")
    ax.plot(t, np.degrees(result["steer_request"]), color=REFERENCE, ls="--", lw=0.8, label="Anforderung")
    _style(ax, "Lenkwinkel", "t (s)", "°")
    ax.legend(fontsize=8)
    ax = axs[1, 1]
    ax.plot(t, result["ay"], color=COLORS[0], label="a_y")
    ax.plot(t, result["ax"], color=COLORS[1], label="a_x")
    _style(ax, "Beschleunigungen", "t (s)", "m/s²")
    ax.legend(fontsize=8)
    ax = axs[2, 0]
    ax.plot(t, np.degrees(result["r"]), color=COLORS[0], label="Gierrate (°/s)")
    ax.plot(t, np.degrees(result["beta"]), color=COLORS[1], label="Schwimmwinkel (°)")
    ax.plot(t, np.degrees(result["roll"]), color=COLORS[2], label="Wankwinkel (°)")
    _style(ax, "Gierrate, Schwimm- und Wankwinkel", "t (s)", "°/s bzw. °")
    ax.legend(fontsize=8)
    ax = axs[2, 1]
    ax.plot(t, result["lateral_error"] * 100, color=COLORS[0])
    ax.axhline(0, color=REFERENCE, lw=0.6)
    _style(ax, "Bahnabweichung", "t (s)", "cm")
    fig.suptitle(title or result.name)
    return fig


def tire_figure(result):
    fig, axs = plt.subplots(2, 2, figsize=(14, 8), sharex=True, layout="constrained")
    t = result["t"]
    util = np.hypot(result["fx"], result["fy"]) / np.maximum(result["mu"] * result["fz"], 1.0)
    for ax, key, title, scale, unit in ((axs[0, 0], "fz", "Radlasten", 1e-3, "kN"),
                                        (axs[0, 1], "slip_angle", "Schräglaufwinkel", np.degrees(1), "°"),
                                        (axs[1, 0], "slip_ratio", "Längsschlupf", 100, "%")):
        for i, w in enumerate(WHEEL_NAMES):
            ax.plot(t, result[key][:, i] * scale, color=WHEEL_COLORS[w], label=w)
        _style(ax, title, None, unit)
        ax.legend(fontsize=8, ncol=4)
    ax = axs[1, 1]
    for i, w in enumerate(WHEEL_NAMES):
        ax.plot(t, util[:, i], color=WHEEL_COLORS[w], label=w)
    ax.axhline(1.0, color=REFERENCE, ls="--", lw=0.8)
    _style(ax, "Reibwertausnutzung", "t (s)", "-")
    ax.legend(fontsize=8, ncol=4)
    axs[1, 0].set_xlabel("t (s)")
    fig.suptitle("Reifen")
    return fig


def plot_tire_curves(tire_params, loads=(2000.0, 4000.0, 6000.0), axes=None):
    from ..tire_models import create_tires
    front, _ = create_tires(tire_params)
    if axes is None:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    else:
        fig = axes[0].figure
    alpha = np.radians(np.linspace(-15, 15, 300))
    kappa = np.linspace(-0.4, 0.4, 300)
    for color, fz in zip(COLORS, loads):
        _, fy, _ = front.forces(alpha, 0.0, fz, tire_params.mu)
        fx, _, _ = front.forces(0.0, kappa, fz, tire_params.mu)
        axes[0].plot(np.degrees(alpha), fy / 1000, color=color, label=f"Fz = {fz / 1000:.0f} kN")
        axes[1].plot(kappa * 100, fx / 1000, color=color, label=f"Fz = {fz / 1000:.0f} kN")
    _style(axes[0], f"Seitenkraft ({tire_params.model})", "Schräglaufwinkel (°)", "Fy (kN)")
    _style(axes[1], f"Umfangskraft ({tire_params.model})", "Längsschlupf (%)", "Fx (kN)")
    for ax in axes:
        ax.legend(fontsize=8)
    return fig


def plot_ggv(ax, result, mu=1.0):
    sc = ax.scatter(result["ay"], result["ax"], c=result["speed"] * 3.6, s=4, cmap="Blues")
    angle = np.linspace(0, 2 * np.pi, 200)
    ax.plot(mu * G * np.cos(angle), mu * G * np.sin(angle), color=REFERENCE, ls="--", lw=0.8, label="µ g")
    ax.set_aspect("equal")
    _style(ax, "GGV-Diagramm", "a_y (m/s²)", "a_x (m/s²)")
    ax.figure.colorbar(sc, ax=ax, label="v (km/h)")
    ax.legend(fontsize=8)


def plot_bode(config, speeds=(10.0, 20.0, 30.0, 40.0), axes=None):
    from ..analysis import LinearSingleTrackAnalysis
    analysis = LinearSingleTrackAnalysis(config)
    if axes is None:
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, layout="constrained")
    else:
        fig = axes[0, 0].figure
    for color, v in zip(COLORS, speeds):
        fr = analysis.frequency_response(v)
        label = f"{v * 3.6:.0f} km/h"
        axes[0, 0].semilogx(fr["frequency"], 20 * np.log10(fr["yaw_gain"]), color=color, label=label)
        axes[1, 0].semilogx(fr["frequency"], fr["yaw_phase"], color=color)
        axes[0, 1].semilogx(fr["frequency"], 20 * np.log10(fr["ay_gain"]), color=color, label=label)
        axes[1, 1].semilogx(fr["frequency"], fr["ay_phase"], color=color)
    _style(axes[0, 0], "Gierrate / Radlenkwinkel", None, "Betrag (dB)")
    _style(axes[1, 0], None, "f (Hz)", "Phase (°)")
    _style(axes[0, 1], "Querbeschleunigung / Radlenkwinkel", None, "Betrag (dB)")
    _style(axes[1, 1], None, "f (Hz)", "Phase (°)")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Bode-Diagramm (lineares Einspurmodell)")
    return fig


def heatmap_figure(result):
    # wheel loads and friction utilization over time, plus beta / beta-rate phase plane
    fig = plt.figure(figsize=(14, 8), layout="constrained")
    gs = fig.add_gridspec(2, 2)
    t = result["t"]
    util = np.hypot(result["fx"], result["fy"]) / np.maximum(result["mu"] * result["fz"], 1.0)
    for row, (data, title, cmap, label) in enumerate(((result["fz"] / 1000, "Reifenbelastung (Radlast)", "Blues", "kN"),
                                                      (util, "Reibwertausnutzung", "Oranges", "-"))):
        ax = fig.add_subplot(gs[row, 0])
        im = ax.imshow(data.T, aspect="auto", cmap=cmap, extent=[t[0], t[-1], 3.5, -0.5],
                       vmin=0, vmax=None if row == 0 else 1.0, interpolation="nearest")
        ax.set_yticks(range(4))
        ax.set_yticklabels(WHEEL_NAMES)
        _style(ax, title, "t (s)", None)
        ax.grid(False)
        fig.colorbar(im, ax=ax, label=label)
    ax = fig.add_subplot(gs[0, 1])
    reserve = 1 - util.max(axis=1)
    ax.fill_between(t, reserve, color=COLORS[2], alpha=0.4)
    ax.plot(t, reserve, color=COLORS[2])
    _style(ax, "Stabilitätsreserve (1 - max. Ausnutzung)", "t (s)", "-")
    ax = fig.add_subplot(gs[1, 1])
    beta = np.degrees(result["beta"])
    beta_rate = np.gradient(beta, t) if len(t) > 2 else np.zeros_like(beta)
    ax.axhline(0, color=REFERENCE, lw=0.6)
    ax.axvline(0, color=REFERENCE, lw=0.6)
    ax.plot(beta, beta_rate, color=COLORS[0], lw=0.8)
    _style(ax, "Phasenebene Schwimmwinkel", "β (°)", "dβ/dt (°/s)")
    return fig


def suspension_figure(result):
    # suspension travel per wheel and body motion (multibody model)
    fig, axs = plt.subplots(2, 1, figsize=(12, 7), sharex=True, layout="constrained")
    t = result["t"]
    if "suspension_travel" in result:
        for i, w in enumerate(WHEEL_NAMES):
            axs[0].plot(t, result["suspension_travel"][:, i] * 1000, color=WHEEL_COLORS[w], label=w)
        axs[0].legend(fontsize=8, ncol=4)
    else:
        axs[0].text(0.5, 0.5, "Federwege nur im Mehrkörpermodell", ha="center", transform=axs[0].transAxes)
    _style(axs[0], "Federwege (+ = Einfedern)", None, "mm")
    axs[1].plot(t, result["heave"] * 1000, color=COLORS[0], label="Hub (mm)")
    axs[1].plot(t, np.degrees(result["roll"]), color=COLORS[1], label="Wanken (°)")
    axs[1].plot(t, np.degrees(result["pitch"]), color=COLORS[2], label="Nicken (°)")
    _style(axs[1], "Aufbaubewegung", "t (s)", "mm bzw. °")
    axs[1].legend(fontsize=8)
    return fig


def energy_figure(result):
    fig, axs = plt.subplots(2, 1, figsize=(12, 6), sharex=True, layout="constrained")
    t = result["t"]
    if "power_battery" in result:
        axs[0].plot(t, result["power_battery"] / 1000, color=COLORS[0], label="Batterie/Kraftstoff")
    axs[0].plot(t, result.get("force_drive", np.zeros_like(t)) * result["speed"] / 1000, color=COLORS[1],
                label="Antrieb mechanisch")
    _style(axs[0], "Leistung", None, "kW")
    axs[0].legend(fontsize=8)
    axs[1].plot(t, result["energy_drive"] / 3.6e6, color=COLORS[0], label="Energiebedarf")
    axs[1].plot(t, result["energy_regen"] / 3.6e6, color=COLORS[2], label="Rekuperiert")
    _style(axs[1], "Energie", "t (s)", "kWh")
    axs[1].legend(fontsize=8)
    return fig


def compare_figure(results, signals=(("speed", "Geschwindigkeit", 3.6, "km/h"), ("ay", "Querbeschleunigung", 1, "m/s²"),
                                     ("r", "Gierrate", np.degrees(1), "°/s"), ("lateral_error", "Bahnabweichung", 1, "m"))):
    fig = plt.figure(figsize=(14, 9), layout="constrained")
    gs = fig.add_gridspec(3, 2)
    ax_path = fig.add_subplot(gs[0, :])
    for i, result in enumerate(results):
        plot_path(ax_path, result, COLORS[i % len(COLORS)], result.name, reference=(i == 0), outlines=False)
    for k, (key, title, scale, unit) in enumerate(signals):
        ax = fig.add_subplot(gs[1 + k // 2, k % 2])
        for i, result in enumerate(results):
            ax.plot(result["t"], result[key] * scale, color=COLORS[i % len(COLORS)], label=result.name)
        _style(ax, title, "t (s)", unit)
    fig.axes[1].legend(fontsize=8)
    fig.suptitle("Vergleich der Simulationsläufe")
    return fig


def quasi_static_figure(config):
    from ..analysis import QuasiStaticAnalysis
    qa = QuasiStaticAnalysis(config)
    ay = np.linspace(0, 9, 60)
    loads = np.array([qa.wheel_loads(0, a)[0] for a in ay])
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5), layout="constrained")
    for i, w in enumerate(WHEEL_NAMES):
        axs[0].plot(ay, loads[:, i] / 1000, color=WHEEL_COLORS[w], label=w)
    _style(axs[0], "Radlasten (Linkskurve)", "a_y (m/s²)", "kN")
    axs[0].legend(fontsize=8)
    axs[1].plot(ay, np.degrees(qa.roll_gradient * ay), color=COLORS[0])
    _style(axs[1], f"Wankwinkel ({np.degrees(qa.roll_gradient) * G:.2f} °/g)", "a_y (m/s²)", "°")
    cam = np.array([qa.camber_at(a) for a in ay])
    axs[2].plot(ay, cam[:, 0], color=COLORS[0], label="vorne außen")
    axs[2].plot(ay, cam[:, 1], color=COLORS[1], label="hinten außen")
    _style(axs[2], "Sturz zur Fahrbahn (kurvenaußen)", "a_y (m/s²)", "°")
    axs[2].legend(fontsize=8)
    return fig
