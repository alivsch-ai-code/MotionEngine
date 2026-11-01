#!/usr/bin/env python
"""Generate every figure used by the README from the actual code.

Run from the repository root:
    python scripts/generate_readme_figures.py            # all figures
    python scripts/generate_readme_figures.py diagrams   # SVG diagrams only
    python scripts/generate_readme_figures.py results    # simulation results only

Diagrams go to docs/images/*.svg (text stored as outlines, so they render identically
everywhere); simulation results go to docs/images/results/*.png.
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT, ROOT / "examples" / "planning", ROOT / "examples" / "stabilization"):
    sys.path.insert(0, str(extra))

IMAGES = ROOT / "docs" / "images"
RESULTS = IMAGES / "results"

# GitHub dark surfaces and ink; series are the validated dark categorical slots, in fixed order
SURFACE, CARD, CARD_2 = "#0d1117", "#161b22", "#21262d"
HAIRLINE, AXIS = "#21262d", "#30363d"
INK, INK_2, MUTED = "#f0f6fc", "#c9d1d9", "#8b949e"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"
SERIES = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA]
VIOLET = "#9085e9"

STATUS_COLORS = {0: AQUA, 1: "#484f58", 2: ORANGE, 3: "#30363d"}
STATUS_LABELS = {0: "Valid", 1: "Constraint violated", 2: "Collision", 3: "Not checked (lazy search)"}

plt.rcParams.update({
    "svg.fonttype": "path", "svg.hashsalt": "motionengine",
    "font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans", "font.size": 11,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK_2, "axes.titlecolor": INK, "axes.linewidth": 0.8,
    "axes.titlesize": 13, "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.titlepad": 10,
    "axes.labelsize": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": HAIRLINE, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "lines.linewidth": 2.0, "lines.solid_capstyle": "round",
    "legend.frameon": False, "legend.fontsize": 10, "legend.labelcolor": INK_2,
    "text.color": INK,
})


def save_svg(fig, name):
    fig.savefig(IMAGES / name, format="svg", metadata={"Date": None, "Creator": "MotionEngine"})
    plt.close(fig)
    print(f"wrote docs/images/{name}")


def save_png(fig, name):
    RESULTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(RESULTS / name, dpi=170, metadata={"Software": "MotionEngine"})
    plt.close(fig)
    print(f"wrote docs/images/results/{name}")


def canvas(width, height):
    # pixel-like drawing surface: origin top left, y down
    fig = plt.figure(figsize=(width / 100, height / 100))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")
    return fig, ax


def card(ax, x, y, w, h, face=CARD, edge=AXIS, lw=1.0, radius=10):
    ax.add_patch(FancyBboxPatch((x + radius, y + radius), w - 2 * radius, h - 2 * radius,
                                boxstyle=f"round,pad={radius},rounding_size={radius}", fc=face, ec=edge, lw=lw))


def arrow(ax, p0, p1, color=MUTED, lw=1.6, style="-|>", scale=13, connection="arc3", zorder=3):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=scale, color=color, lw=lw, shrinkA=0,
                                 shrinkB=0, connectionstyle=connection, zorder=zorder, joinstyle="miter"))


# ----------------------------------------------------------------------------------- diagrams
def architecture():
    width, height = 1280, 660
    fig, ax = canvas(width, height)
    ax.text(40, 48, "MotionEngine system architecture", fontsize=19, fontweight="bold")
    ax.text(40, 76, "Closed-loop stack. Every block is an exchangeable component behind a versioned plugin interface.",
            fontsize=11.5, color=MUTED)

    stack = [("Perception", BLUE, ["ground_truth", "object_sensor"]),
             ("Prediction", BLUE, ["constant_velocity", "constant_acceleration", "lane_following"]),
             ("Behavior", VIOLET, ["rule_based"]),
             ("Motion planning", AQUA, ["werling (Frenet)", "sequential", "frenet_naive"]),
             ("Stabilization", ORANGE, ["Werling bi-level", "Stanley · Pure Pursuit", "LQR · MPC"])]
    box_w, box_h, gap, x0, y0 = 212, 158, 35, 40, 112
    for i, (title, color, items) in enumerate(stack):
        x = x0 + i * (box_w + gap)
        card(ax, x, y0, box_w, box_h)
        ax.add_patch(Rectangle((x + 18, y0 + 20), 26, 3.5, fc=color, ec="none"))
        ax.text(x + 18, y0 + 48, title, fontsize=13.5, fontweight="bold", va="center")
        for k, item in enumerate(items):
            ax.text(x + 18, y0 + 80 + 22 * k, item, fontsize=10.5, color=INK_2, va="center")
        if i:
            arrow(ax, (x - gap + 4, y0 + box_h / 2), (x - 4, y0 + box_h / 2))

    py, ph = 330, 150
    card(ax, x0, py, width - 2 * x0, ph)
    ax.add_patch(Rectangle((x0 + 18, py + 20), 26, 3.5, fc=YELLOW, ec="none"))
    ax.text(x0 + 18, py + 48, "Plant and world", fontsize=13.5, fontweight="bold", va="center")
    plant = [("Vehicle models", ["Kinematic and linear bicycle", "Nonlinear bicycle", "Double-track · Multibody"]),
             ("Tire models", ["Linear · Brush", "Pacejka Magic Formula"]),
             ("Actuation and ADAS", ["Steering actuator", "Powertrain · Brakes", "ABS · TCS · ESP · ACC · AEB"]),
             ("World and traffic", ["Road network · Actors", "Scenario engine", "Collision detection (SAT)"]),
             ("Simulation", ["RK4 · Heun · Euler · Adaptive", "Auto-substep from stable_dt", "KPI reporting"])]
    for i, (title, items) in enumerate(plant):
        x = x0 + 18 + i * (box_w + gap)
        ax.text(x, py + 78, title, fontsize=10.5, fontweight="bold", color=INK_2, va="center")
        for k, item in enumerate(items):
            ax.text(x, py + 98 + 16 * k, item, fontsize=9.3, color=MUTED, va="center")

    cx = x0 + 4 * (box_w + gap) + box_w / 2
    arrow(ax, (cx, y0 + box_h + 4), (cx, py - 4))
    ax.text(cx - 10, (y0 + box_h + py) / 2, "actuator commands", fontsize=10, color=MUTED, ha="right", va="center")
    fx = x0 + box_w / 2
    arrow(ax, (fx, py - 4), (fx, y0 + box_h + 4))
    ax.text(fx + 10, (y0 + box_h + py) / 2, "vehicle state and world", fontsize=10, color=MUTED, va="center")

    fy = 504
    card(ax, x0, fy, width - 2 * x0, 56, face=CARD_2)
    ax.text(width / 2, fy + 28, "Tooling:  Runtime graph executor  ·  Desktop GUI  ·  3D view  ·  MATLAB bridge  ·  "
            "Python / C++ / Rust nodes  ·  REST API", ha="center", va="center", fontsize=11, color=INK_2)
    cy = 574
    card(ax, x0, cy, width - 2 * x0, 56, face=CARD_2)
    ax.text(width / 2, cy + 28, "Core:  Interfaces  ·  Plugin registry  ·  Parameters  ·  ISO 8855 conventions  ·  "
            "Geometry and reference lines  ·  Logging", ha="center", va="center", fontsize=11, color=INK_2)
    save_svg(fig, "architecture_overview.svg")


def frenet():
    from vdsim.geometry import ReferenceLine
    from vdsim.planning.polynomials import polyval, quintic_coefficients

    width, height = 1280, 640
    fig = plt.figure(figsize=(width / 100, height / 100))
    fig.text(40 / width, 1 - 48 / height, "Frenet coordinates", fontsize=19, fontweight="bold")
    fig.text(40 / width, 1 - 76 / height, "Trajectory candidates are quintic polynomials d(t) sampled relative to a "
             "curved reference line (Werling, 2011).", fontsize=11.5, color=MUTED)

    ax = fig.add_axes([30 / width, 30 / height, 810 / width, 530 / height])
    ax.axis("off")
    ax.set_aspect("equal")

    road = ReferenceLine.from_segments([("straight", 12.0), ("arc", 24.0, 1 / 30.0), ("arc", 24.0, -1 / 30.0),
                                        ("straight", 10.0)], ds=0.1, transition=8.0)

    def label(s, d, text, **kwargs):
        x, y = road.point(s, d)
        ax.text(x, y, text, ha=kwargs.pop("ha", "center"), va="center", **kwargs)

    for d, lw, color in ((-1.75, 1.3, AXIS), (5.25, 1.3, AXIS), (1.75, 1.1, "#484f58")):
        xb, yb = road.point(road.s, d)
        ax.plot(xb, yb, color=color, lw=lw, ls=(0, (7, 6)) if d == 1.75 else "-")
    ax.plot(road.x, road.y, color=MUTED, lw=1.6)

    s0, d0, tau, v = 16.0, 3.5, 4.0, 7.5
    t = np.linspace(0.0, tau, 60)
    best = 0.0
    for target in (-1.0, 0.0, 1.0, 2.25, 3.5, 4.5):
        c = quintic_coefficients(d0, 0.0, 0.0, target, 0.0, 0.0, tau)
        d = polyval(c[None, :], t[None, :])[0][0]
        xc, yc = road.point(s0 + v * t, d)
        selected = target == best
        ax.plot(xc, yc, color=AQUA if selected else "#6e7681", lw=3.0 if selected else 1.4, zorder=5 if selected else 2)
        ax.plot(xc[-1], yc[-1], "o", ms=8 if selected else 5, color=AQUA if selected else "#6e7681", zorder=6, mec=SURFACE)

    xs, ys = road.point(np.linspace(0.0, s0, 200))
    ax.plot(xs, ys, color=BLUE, lw=3.4, zorder=3)
    fx, fy, th, _, _ = road.evaluate(s0)
    ex, ey = road.point(s0, d0)
    nx, ny, tx, ty = -math.sin(th), math.cos(th), math.cos(th), math.sin(th)

    arrow(ax, (fx, fy), (fx + 5.5 * tx, fy + 5.5 * ty), color=INK_2, lw=1.6, scale=13, zorder=6)
    arrow(ax, (fx, fy), (ex - 0.1 * nx, ey - 0.1 * ny), color=ORANGE, lw=2.4, scale=15, zorder=7)
    rear = (ex - 2.3 * tx - 0.92 * nx, ey - 2.3 * ty - 0.92 * ny)
    ax.add_patch(Rectangle(rear, 4.6, 1.84, angle=math.degrees(th), rotation_point="xy", fc=YELLOW, ec=SURFACE, lw=1.2,
                           zorder=8))
    ax.add_patch(Circle((fx, fy), 0.42, fc=INK, ec=SURFACE, lw=1.4, zorder=9))
    ax.add_patch(Circle((road.x[0], road.y[0]), 0.42, fc=BLUE, ec=SURFACE, lw=1.4, zorder=9))

    label(0.0, -3.2, "$s = 0$", fontsize=11.5, color=INK_2)
    label(7.5, -3.3, "arc length $s$", fontsize=13, color=INK)
    label(s0 - 1.2, 1.2, "$d$", fontsize=14, color=INK, ha="right")
    label(s0, d0 + 2.0, "ego vehicle", fontsize=11.5, color=INK)
    label(s0 + 6.8, -1.0, r"$\vec{t}_r$", fontsize=13, color=INK_2)
    label(s0 + 0.4, -3.2, "foot point", fontsize=11.5, color=INK_2)
    label(road.length - 3.0, -3.2, "reference line", fontsize=11.5, color=MUTED)
    send = s0 + v * tau
    label(send + 5.5, best, "selected", fontsize=11.5, color=INK)
    label(send + 6.2, 4.5, "candidates", fontsize=11.5, color=MUTED)

    xa, ya = road.point(road.s, -5.0)
    xb, yb = road.point(road.s, 7.0)
    ax.set_xlim(min(xa.min(), xb.min()) - 1.0, max(xa.max(), xb.max()) + 1.0)
    ax.set_ylim(min(ya.min(), yb.min()) - 1.0, max(ya.max(), yb.max()) + 1.0)

    px, py, pw, ph = 868, 130, 372, 420
    panel = fig.add_axes([0, 0, 1, 1], facecolor="none")
    panel.set_xlim(0, width)
    panel.set_ylim(height, 0)
    panel.axis("off")
    card(panel, px, py, pw, ph)
    panel.text(px + 24, py + 36, "Transformations", fontsize=13.5, fontweight="bold", va="center")
    rows = [("Frenet to world", None), (r"$x = x_r(s) - d\,\sin\theta_r$", 0), (r"$y = y_r(s) + d\,\cos\theta_r$", 0),
            ("Rates", None), (r"$\dot{s} = \dfrac{v\,\cos\Delta\theta}{1 - \kappa_r d}$", 1),
            (r"$\dot{d} = v\,\sin\Delta\theta$", 0), (r"$d' = (1 - \kappa_r d)\,\tan\Delta\theta$", 0),
            ("Heading error", None), (r"$\Delta\theta = \theta - \theta_r$", 0)]
    y = py + 78
    for text, kind in rows:
        if kind is None:
            panel.text(px + 24, y, text, fontsize=10.5, color=MUTED, va="center")
            y += 30
        else:
            panel.text(px + 24, y + (10 if kind else 0), text, fontsize=13.5, color=INK, va="center")
            y += 66 if kind else 35
    save_svg(fig, "frenet_coordinates.svg")


def vehicle_dynamics():
    width, height = 1280, 660
    fig = plt.figure(figsize=(width / 100, height / 100))
    fig.text(40 / width, 1 - 48 / height, "Single-track (bicycle) model", fontsize=19, fontweight="bold")
    fig.text(40 / width, 1 - 76 / height, "ISO 8855: x forward, y left, z up. Positive angles counterclockwise.",
             fontsize=11.5, color=MUTED)

    ax = fig.add_axes([30 / width, 70 / height, 670 / width, 510 / height])
    ax.axis("off")
    ax.set_aspect("equal")
    ax.set_xlim(-4.3, 4.9)
    ax.set_ylim(-3.25, 3.75)

    psi, delta, beta = math.radians(14), math.radians(24), math.radians(17)
    lf, lr = 2.0, 2.15
    ex, ey = math.cos(psi), math.sin(psi)
    px, py = -ey, ex

    def body(a, b):
        return a * ex + b * px, a * ey + b * py

    corners = [body(lf + 0.8, 0.85), body(-lr - 0.7, 0.85), body(-lr - 0.7, -0.85), body(lf + 0.8, -0.85)]
    ax.add_patch(Polygon(corners, closed=True, fc=CARD, ec=AXIS, lw=1.4, joinstyle="round"))
    ax.plot(*zip(body(-lr - 1.1, 0), body(lf + 1.65, 0)), color="#484f58", lw=1.1, ls=(0, (6, 5)))
    ax.text(*body(lf + 1.72, 0.12), "$x_V$", fontsize=13, color=INK_2)

    def wheel(cx, cy, angle):
        length, thickness = 0.86, 0.24
        c, s = math.cos(angle), math.sin(angle)
        pts = [(cx + a * c - b * s, cy + a * s + b * c)
               for a, b in ((length / 2, thickness / 2), (-length / 2, thickness / 2),
                            (-length / 2, -thickness / 2), (length / 2, -thickness / 2))]
        ax.add_patch(Polygon(pts, closed=True, fc=YELLOW, ec=SURFACE, lw=1.0, zorder=4))

    fx, fy = body(lf, 0)
    rx, ry = body(-lr, 0)
    wheel(fx, fy, psi + delta)
    wheel(rx, ry, psi)

    wheel_dir = (math.cos(psi + delta), math.sin(psi + delta))
    ax.plot([fx, fx + 1.4 * wheel_dir[0]], [fy, fy + 1.4 * wheel_dir[1]], color=YELLOW, lw=1.2)
    ax.add_patch(Arc((fx, fy), 2.2, 2.2, theta1=math.degrees(psi), theta2=math.degrees(psi + delta), color=YELLOW, lw=1.5))
    mid = psi + delta / 2
    ax.text(fx + 1.27 * math.cos(mid), fy + 1.27 * math.sin(mid), r"$\delta$", fontsize=14, color=INK, va="center")

    # lateral tire forces act normal to the wheel planes
    fyf = (-math.sin(psi + delta), math.cos(psi + delta))
    arrow(ax, (fx, fy), (fx + 1.5 * fyf[0], fy + 1.5 * fyf[1]), color=BLUE, lw=2.2, scale=14, zorder=5)
    ax.text(fx + 1.72 * fyf[0], fy + 1.72 * fyf[1] + 0.08, "$F_{y,f}$", fontsize=13, color=INK, ha="center", va="center")
    arrow(ax, (rx, ry), (rx + 1.3 * px, ry + 1.3 * py), color=BLUE, lw=2.2, scale=14, zorder=5)
    ax.text(rx + 1.5 * px, ry + 1.5 * py + 0.08, "$F_{y,r}$", fontsize=13, color=INK, ha="center", va="center")

    # velocity at the center of gravity and sideslip angle
    vdir = (math.cos(psi + beta), math.sin(psi + beta))
    arrow(ax, (0, 0), (1.75 * vdir[0], 1.75 * vdir[1]), color=AQUA, lw=2.4, scale=15, zorder=6)
    ax.text(1.9 * vdir[0], 1.9 * vdir[1] + 0.06, "$v$", fontsize=14, color=INK, va="center")
    ax.add_patch(Arc((0, 0), 2.5, 2.5, theta1=math.degrees(psi), theta2=math.degrees(psi + beta), color=AQUA, lw=1.5, zorder=6))
    midb = psi + beta / 2
    ax.text(1.42 * math.cos(midb), 1.42 * math.sin(midb) - 0.02, r"$\beta$", fontsize=14, color=INK, va="center")

    # positive yaw rate is counterclockwise
    radius, a_end = 0.56, math.radians(310)
    ax.add_patch(Arc((0, 0), 2 * radius, 2 * radius, theta1=62, theta2=math.degrees(a_end), color=MAGENTA, lw=1.8, zorder=7))
    tip = (radius * math.cos(a_end + 0.1), radius * math.sin(a_end + 0.1))
    arrow(ax, (radius * math.cos(a_end - 0.1), radius * math.sin(a_end - 0.1)), tip, color=MAGENTA, lw=1.8, scale=14, zorder=7)
    ax.text(-0.83, 0.02, "$r$", fontsize=14, color=INK, va="center", ha="center")

    ax.add_patch(Circle((0, 0), 0.11, fc=INK, ec=SURFACE, lw=1.2, zorder=8))
    ax.text(*body(0.0, 0.33), "CoG", fontsize=10.5, color=INK, ha="center", va="center", zorder=8)

    off = -1.4
    for a, b, text in ((0.0, lf, "$l_f$"), (-lr, 0.0, "$l_r$")):
        arrow(ax, body(a, off), body(b, off), color=MUTED, lw=1.2, style="<|-|>", scale=10)
        ax.text(*body((a + b) / 2, off - 0.3), text, fontsize=13, color=INK_2, ha="center", va="center")
    for a in (-lr, 0.0, lf):
        ax.plot(*zip(body(a, -0.12), body(a, off - 0.12)), color=AXIS, lw=0.9)

    # inertial frame with the yaw angle
    ox, oy = -3.95, -2.85
    arrow(ax, (ox, oy), (ox + 1.15, oy), color=MUTED, lw=1.3, scale=10)
    arrow(ax, (ox, oy), (ox, oy + 1.15), color=MUTED, lw=1.3, scale=10)
    ax.plot([ox, ox + 1.1 * ex], [oy, oy + 1.1 * ey], color="#484f58", lw=1.1, ls=(0, (6, 5)))
    ax.add_patch(Arc((ox, oy), 1.5, 1.5, theta1=0, theta2=math.degrees(psi), color=MUTED, lw=1.2))
    ax.text(ox + 1.28, oy - 0.02, "$X$", fontsize=12, color=INK_2, va="center")
    ax.text(ox, oy + 1.32, "$Y$", fontsize=12, color=INK_2, ha="center")
    ax.text(ox + 0.92, oy + 0.32, r"$\psi$", fontsize=12, color=INK_2, va="center")

    pl, pt, pw, ph = 728, 112, 512, 442
    panel = fig.add_axes([0, 0, 1, 1], facecolor="none")
    panel.set_xlim(0, width)
    panel.set_ylim(height, 0)
    panel.axis("off")
    card(panel, pl, pt, pw, ph)
    blocks = [("Kinematic", "4 states", AQUA,
               [r"$\dot{x} = v\cos(\psi + \beta) \qquad \dot{y} = v\sin(\psi + \beta)$",
                r"$\dot{\psi} = \dfrac{v\cos\beta}{l}\,\tan\delta \qquad \dot{v} = a$"], (32, 48)),
              ("Linear", "6 states", BLUE,
               [r"$\dot{v}_y = -\dfrac{c_f + c_r}{m v_x}\,v_y - \left(v_x + \dfrac{c_f l_f - c_r l_r}{m v_x}\right) r + \dfrac{c_f}{m}\,\delta$",
                r"$\dot{r} = -\dfrac{c_f l_f - c_r l_r}{I_z v_x}\,v_y - \dfrac{c_f l_f^2 + c_r l_r^2}{I_z v_x}\,r + \dfrac{c_f l_f}{I_z}\,\delta$"],
               (54, 56)),
              ("Nonlinear", "6 states", ORANGE,
               [r"$\alpha_f = \delta - \arctan\dfrac{v_y + l_f r}{v_x} \qquad \alpha_r = -\arctan\dfrac{v_y - l_r r}{v_x}$",
                r"$F_y = f(\alpha, \kappa, F_z, \mu)$"], (46, 32))]
    y = pt + 34
    for title, states, color, equations, steps in blocks:
        panel.add_patch(Rectangle((pl + 24, y - 8), 4, 16, fc=color, ec="none"))
        panel.text(pl + 38, y, title, fontsize=13, fontweight="bold", va="center")
        panel.text(pl + pw - 24, y, states, fontsize=10.5, color=MUTED, va="center", ha="right")
        y += 24
        for eq, step in zip(equations, steps):
            y += step / 2
            panel.text(pl + 24, y, eq, fontsize=12.5, color=INK, va="center")
            y += step / 2 + 4
        y += 14
    panel.text(40, height - 34, "Model hierarchy:  kinematic  →  linear  →  nonlinear bicycle  →  double-track "
               "(12 DOF)  →  multibody (24 DOF)", fontsize=11, color=MUTED, va="center")
    save_svg(fig, "vehicle_dynamics.svg")

def measure_planning_funnel():
    # candidate counts of one real planning cycle: the most demanding cycle of the evasion scenario
    import evasion

    from vdsim.framework.plugins import create_component
    from vdsim.framework.types import EgoState
    from vdsim.geometry import ReferenceLine
    from vdsim.planning.simulation import run_closed_loop

    road = ReferenceLine.straight(400.0, ds=0.5)
    planner = create_component("trajectory_planner/werling")
    log = run_closed_loop(planner, evasion.behavior(road), EgoState(vx=evasion.V), 12.0, evasion.prediction)
    k = int(np.argmax([d.n_checked for d in log.debug]))
    dbg = log.debug[k]
    mode = dbg.modes[dbg.mode]
    return {"t": float(log.t[k]), "n_lateral": int(dbg.info["n_lateral"]), "n_lon": int(dbg.info["n_longitudinal"][dbg.mode]),
            "combinations": int(mode["n_candidates"]), "feasible": int(mode["n_feasible"]), "checked": int(mode["n_checked"])}


def planning_pipeline():
    m = measure_planning_funnel()
    width, height = 1280, 470
    fig, ax = canvas(width, height)
    ax.text(40, 48, "Trajectory planning cycle", fontsize=19, fontweight="bold")
    ax.text(40, 76, "One Werling planning cycle. Candidates are checked lazily in ascending cost, so the search "
            "stops at the first valid trajectory.", fontsize=11.5, color=MUTED)
    stages = [("Start state", BLUE, ["Previous plan at", "$t_0 + t_{comp}$", "or re-initialization"]),
              ("Candidate sets", AQUA, ["Quintic lateral $d(t)$", "Quartic / quintic", "longitudinal $s(t)$"]),
              ("Pre-filter", VIOLET, ["Cost in closed form", "Frenet limits on", "acceleration"]),
              ("Lazy search", YELLOW, ["Ascending cost", "Constraints, then", "collision check"]),
              ("Mode selection", ORANGE, ["Replacement strategy", "across longitudinal", "modes, or fallback"])]
    box_w, box_h, gap, x0, y0 = 212, 136, 35, 40, 104
    for i, (title, color, lines) in enumerate(stages):
        x = x0 + i * (box_w + gap)
        card(ax, x, y0, box_w, box_h)
        ax.add_patch(Rectangle((x + 18, y0 + 18), 26, 3.5, fc=color, ec="none"))
        ax.text(x + 18, y0 + 44, title, fontsize=13.5, fontweight="bold", va="center")
        for k, line in enumerate(lines):
            ax.text(x + 18, y0 + 72 + 20 * k, line, fontsize=10.5, color=INK_2, va="center")
        if i:
            arrow(ax, (x - gap + 4, y0 + box_h / 2), (x - 4, y0 + box_h / 2))

    py, ph = 268, 170
    card(ax, x0, py, width - 2 * x0, ph)
    ax.text(x0 + 24, py + 34, f"Measured candidate counts, evasion scenario at t = {m['t']:.1f} s", fontsize=13,
            fontweight="bold", va="center")
    ax.text(width - x0 - 24, py + 34, f"{m['n_lateral']} lateral × {m['n_lon']} longitudinal candidates", fontsize=10.5,
            color=MUTED, ha="right", va="center")
    counts = [(f"{m['combinations']:,}", "combinations"), (f"{m['feasible']:,}", "after pre-filter"),
              (f"{m['checked']:,}", "checked in full"), ("1", "selected trajectory")]
    bar_max = width - 2 * x0 - 48 - 330
    for i, (value, label) in enumerate(counts):
        y = py + 66 + 26 * i
        n = float(value.replace(",", ""))
        length = max(bar_max * n / m["combinations"], 4)
        ax.text(x0 + 24, y, label, fontsize=10.5, color=INK_2, va="center")
        ax.add_patch(Rectangle((x0 + 190, y - 8), length, 16, fc=BLUE if i < 3 else AQUA, ec="none"))
        ax.text(x0 + 190 + length + 10, y, value, fontsize=11.5, color=INK, va="center", fontweight="semibold")
    print(f"planning funnel: {m}")
    save_svg(fig, "planning_pipeline.svg")


# ----------------------------------------------------------------------------------- results
def draw_box(ax, x, y, psi, length, width, color, alpha=1.0, zorder=5):
    c, s = math.cos(psi), math.sin(psi)
    pts = [(x + a * c - b * s, y + a * s + b * c) for a, b in ((length / 2, width / 2), (length / 2, -width / 2),
                                                                (-length / 2, -width / 2), (-length / 2, width / 2))]
    ax.add_patch(Polygon(pts, closed=True, fc=color, ec=SURFACE, lw=1.0, alpha=alpha, zorder=zorder))


def candidates(ax, dbg, frenet=False):
    xs, ys = (dbg.candidates_s, dbg.candidates_d) if frenet else (dbg.candidates_x, dbg.candidates_y)
    for status in (3, 1, 2, 0):
        for i in np.flatnonzero(dbg.candidates_status == status):
            if i != dbg.best_index:
                ax.plot(xs[i], ys[i], color=STATUS_COLORS[status], lw=0.8, alpha=0.8, solid_capstyle="butt")
    b = dbg.best_index
    ax.plot(xs[b], ys[b], color=BLUE, lw=2.6, zorder=4, label="Selected trajectory")
    for status in (0, 1, 2, 3):
        if np.any(dbg.candidates_status == status):
            ax.plot([], [], color=STATUS_COLORS[status], lw=1.6, label=STATUS_LABELS[status])


def result_lane_change():
    import lane_change

    from vdsim.geometry import ReferenceLine

    log, _ = lane_change.run(ReferenceLine.straight(400.0, ds=0.5))
    t = np.array(log.t)
    d = np.array([tr.d[0] for tr in log.trajectories])
    ay = np.array([tr.v[0] ** 2 * tr.kappa[0] for tr in log.trajectories])
    dbg, tr = log.debug[5], log.trajectories[5]
    fig = plt.figure(figsize=(12.4, 5.2), layout="constrained")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.7, 1])
    ax = fig.add_subplot(gs[:, 0])
    candidates(ax, dbg, frenet=True)
    ax.set_xlim(tr.s[0] - 3, tr.s[0] + 85)
    ax.set_title(f"Candidate set at t = {log.t[5]:.1f} s, relative to the target lane")
    ax.set_xlabel("Arc length s / m")
    ax.set_ylabel("Lateral offset d / m")
    ax.legend(loc="lower right", frameon=True, facecolor=SURFACE, edgecolor="none", framealpha=0.9)
    a1 = fig.add_subplot(gs[0, 1])
    a1.plot(t, d, color=BLUE)
    a1.set_title("Lateral offset")
    a1.set_ylabel("d / m")
    a2 = fig.add_subplot(gs[1, 1], sharex=a1)
    a2.plot(t, ay, color=BLUE)
    a2.set_title("Lateral acceleration")
    a2.set_ylabel("$a_y$ / m/s²")
    a2.set_xlabel("Time / s")
    save_png(fig, "lane_change.png")


def result_following():
    import following

    from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode
    from vdsim.geometry import ReferenceLine
    from vdsim.planning import WerlingPlanner
    from vdsim.planning.simulation import run_closed_loop

    road = ReferenceLine.straight(2000.0, ds=0.5)
    modes = [LongitudinalMode("velocity", {"v_ref": 25.0}),
             LongitudinalMode("following", {"lead_id": 1, "k0": following.K0, "kv": following.KV})]

    def behavior(t, ego):
        return BehaviorCommand(t=t, reference_line=road, target_speed=25.0, modes=modes, d_min=-1.75, d_max=1.75)

    planner = WerlingPlanner()
    log = run_closed_loop(planner, behavior, EgoState(vx=22.0), 45.0, following.prediction)
    t = np.array(log.t)
    lead = np.array([following.lead_state(ti) for ti in t])
    gap = (lead[:, 0] - 2.25) - (log.array("x") + planner.geometry.extent("cog")[0])
    desired = following.K0 + following.KV * lead[:, 1]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12.4, 5.6), sharex=True, layout="constrained")
    a1.plot(t, log.array("vx"), color=BLUE, label="Ego vehicle")
    a1.plot(t, lead[:, 1], color=ORANGE, label="Lead vehicle")
    a1.set_title("Speed")
    a1.set_ylabel("v / m/s")
    a1.legend(loc="upper right", ncols=2)
    a2.plot(t, gap, color=BLUE, label="Measured gap")
    a2.plot(t, desired, color=ORANGE, label="Desired gap")
    a2.set_title("Bumper-to-bumper gap")
    a2.set_ylabel("Gap / m")
    a2.set_xlabel("Time / s")
    a2.legend(loc="upper right", ncols=2)
    save_png(fig, "following.png")


def result_evasion():
    import evasion

    from vdsim.framework.plugins import create_component
    from vdsim.framework.types import EgoState
    from vdsim.geometry import ReferenceLine
    from vdsim.planning.simulation import run_closed_loop

    road = ReferenceLine.straight(400.0, ds=0.5)
    fig = plt.figure(figsize=(12.4, 5.5), layout="constrained")
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1])
    top, bottom = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    for name, spec, color in (("Werling (combined)", "trajectory_planner/werling", BLUE),
                              ("Sequential (longitudinal first)", "trajectory_planner/sequential", ORANGE)):
        planner = create_component(spec)
        log = run_closed_loop(planner, evasion.behavior(road), EgoState(vx=evasion.V), 12.0, evasion.prediction)
        t = np.array(log.t)
        bottom.plot(t, log.array("vx"), color=color, label=name)
        if spec.endswith("werling"):
            k = int(np.argmax([d.n_checked for d in log.debug]))
            top.grid(False)
            for d, style in ((-1.75, "-"), (1.75, (0, (6, 5))), (5.25, "-")):
                top.axhline(d, color="#484f58", lw=1.0, ls=style)
            candidates(top, log.debug[k])
            for obj in evasion.prediction(t[k]).objects:
                x, y, psi, _ = obj.state_at(t[k])
                draw_box(top, x, y, psi, obj.length, obj.width, YELLOW)
            ego = log.ego[k]
            draw_box(top, ego.x + planner.geometry.center_offset("cog"), ego.y, ego.psi, planner.geometry.length,
                     planner.geometry.width, BLUE)
            top.plot(log.array("x"), log.array("y"), color=INK, lw=1.2, label="Driven path (full run)", zorder=3)
            top.set_xlim(ego.x - 7, ego.x + 63)
            top.set_ylim(-2.6, 6.2)
            top.set_aspect("equal")
            top.set_title(f"Parked car with oncoming traffic, t = {t[k]:.1f} s ({log.debug[k].n_checked:,} candidates checked)")
            top.set_ylabel("y / m")
            top.set_xlabel("x / m")
            top.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncols=6, fontsize=9)
    bottom.set_title("Speed profile")
    bottom.set_ylabel("v / m/s")
    bottom.set_xlabel("Time / s")
    bottom.legend(loc="lower right")
    save_png(fig, "evasion.png")


def result_stopping():
    from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode
    from vdsim.geometry import ReferenceLine
    from vdsim.planning import WerlingPlanner
    from vdsim.planning.simulation import run_closed_loop

    s_stop = 120.0
    road = ReferenceLine.straight(400.0, ds=0.5)

    def behavior(t, ego):
        return BehaviorCommand(t=t, reference_line=road, target_speed=14.0, d_min=-1.75, d_max=1.75,
                               modes=[LongitudinalMode("stopping", {"s_stop": s_stop})], maneuver="stop")

    planner = WerlingPlanner()
    log = run_closed_loop(planner, behavior, EgoState(y=0.6, vx=14.0), 25.0)
    t = np.array(log.t)
    front = log.array("x") + planner.geometry.extent("cog")[0]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12.4, 5.6), sharex=True, layout="constrained")
    a1.plot(t, front, color=BLUE, label="Vehicle front")
    a1.axhline(s_stop, color=ORANGE, lw=1.6, label="Stop line")
    a1.set_title("Position")
    a1.set_ylabel("x / m")
    a1.legend(loc="lower right")
    a2.plot(t, log.array("vx"), color=BLUE)
    a2.set_title("Speed")
    a2.set_ylabel("v / m/s")
    a2.set_xlabel("Time / s")
    save_png(fig, "stopping.png")
    print(f"stopping: front error {front[-1] - s_stop:+.3f} m")


def result_consistency():
    from vdsim.framework.plugins import create_component
    from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode
    from vdsim.geometry import ReferenceLine
    from vdsim.planning.simulation import run_closed_loop

    road = ReferenceLine.straight(500.0, ds=0.5)

    def behavior(t, ego):
        return BehaviorCommand(t=t, reference_line=road, target_speed=15.0, d_min=-5.25, d_max=5.25,
                               modes=[LongitudinalMode("velocity", {"v_ref": 15.0})])

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.6), sharey=True, layout="constrained")
    for ax, spec, title in zip(axes, ("trajectory_planner/werling", "trajectory_planner/frenet_naive"),
                               ("Werling: absolute time grid", "Naive Frenet: relative time grid")):
        runs = {period: run_closed_loop(create_component(spec), behavior, EgoState(y=2.0, vx=15.0), 8.0, period=period)
                for period in (0.1, 0.5, 1.0)}
        base_t, base_y = np.array(runs[0.1].t), runs[0.1].array("y")
        for color, period in zip(SERIES, (0.5, 1.0)):
            t = np.array(runs[period].t)
            deviation = runs[period].array("y") - np.interp(t, base_t, base_y)
            ax.plot(t, deviation * 100, color=color, marker="o", ms=6, mec=SURFACE, label=f"Replan every {period:.1f} s")
            print(f"consistency {spec} period {period}: max |dev| = {np.max(np.abs(deviation)) * 100:.2f} cm")
        ax.set_title(title)
        ax.set_xlabel("Time / s")
        ax.legend(loc="upper right")
    axes[0].set_ylabel("Offset from the 0.1 s replanning run / cm")
    save_png(fig, "consistency.png")

def result_controllers():
    from controller_comparison import CONTROLLERS

    from vdsim.core.parameters import load_vehicle_preset
    from vdsim.stabilization.simulate import run_closed_loop
    from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_lateral_offset

    names = {"werling_bilevel": "Werling bi-level", "pure_pursuit": "Pure Pursuit", "stanley": "Stanley", "lqr": "LQR",
             "mpc": "MPC"}
    cfg = load_vehicle_preset("mid_size_sedan")
    path = path_from_lateral_offset([(40, 50, 3.5), (120, 50, -3.5)], 300)
    traj = build_trajectory(path, SpeedProfile([(0, 15), (3, 15), (8, 20), (12, 20)]), reference_point="cog")
    p0 = traj.sample(0)
    logs = {}
    for spec, params in CONTROLLERS:
        key = spec if spec != "composite" else params["lateral"]
        logs[key], _ = run_closed_loop(spec, traj, cfg, duration=11.0, plant="werling_desm", controller_params=params,
                                       ego_initial=dict(x=p0.x, y=p0.y + 0.3, psi=p0.theta, v=15.0))
    colors = dict(zip(logs, SERIES))
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8), sharey=True, layout="constrained")
    groups = ((list(logs)[:3], "Werling and geometric controllers"), ([list(logs)[0]] + list(logs)[3:], "Werling and model-based controllers"))
    for ax, (group, title) in zip(axes, groups):
        for key in group:
            ax.plot(logs[key]["t"], logs[key]["e_n"], color=colors[key], label=names[key])
        ax.axhline(0.0, color=AXIS, lw=1.0)
        ax.set_title(title)
        ax.set_xlabel("Time / s")
        ax.legend(loc="upper right")
    axes[0].set_ylabel("Lateral error $e_n$ / m")
    save_png(fig, "controller_comparison.png")


def result_gust():
    from highway_gust import GUST

    from vdsim.core.parameters import load_vehicle_preset
    from vdsim.stabilization.simulate import run_closed_loop
    from vdsim.stabilization.trajectories import (SpeedProfile, build_trajectory, path_from_lateral_offset,
                                                  replan_from_prediction)

    cfg = load_vehicle_preset("mid_size_sedan")
    path = path_from_lateral_offset([(60, 50, 3.5), (140, 50, -3.5)], 450)
    traj = build_trajectory(path, SpeedProfile([(0, 30.0), (13, 30.0)]), reference_point="cog")

    def planner(t, ego, status, tr):
        if status is not None and status.reinit_request and \
                not (tr.reinitialized and tr.metadata.get("replanned_at", -1) >= status.prediction["t"] - 0.2):
            return replan_from_prediction(tr, status.prediction, blend_time=3.0)
        return tr

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12.4, 5.6), sharex=True, layout="constrained")
    for color, (label, provider) in zip(SERIES, (("Bi-level with re-initialization", planner), ("Low-level only", None))):
        log, _ = run_closed_loop("werling_bilevel", traj, cfg, duration=12.0, provider=provider,
                                 ego_initial=dict(x=0.0, y=0.0, psi=0.0, v=30.0), plant_params={"disturbances": GUST})
        a1.plot(log["t"], log["y"], color=color, label=label)
        a2.plot(log["t"], log["e_n"], color=color, label=label)
    a1.plot(traj.t, traj.y, color=MUTED, lw=1.2, label="Original reference", zorder=1)
    for ax in (a1, a2):
        ax.axvspan(GUST[0]["t"], GUST[0]["t"] + GUST[0]["duration"], color=CARD_2, lw=0, zorder=0)
    a1.text(GUST[0]["t"] + 0.2, a1.get_ylim()[1] * 0.92, "Side-wind gust", fontsize=10, color=INK_2, ha="center")
    a1.set_title("Lateral position at 30 m/s")
    a1.set_ylabel("y / m")
    a1.legend(loc="upper right")
    a2.set_title("Lateral tracking error against the active trajectory")
    a2.set_ylabel("$e_n$ / m")
    a2.set_xlabel("Time / s")
    save_png(fig, "highway_gust.png")


def result_slow_tracking():
    import slow_comparison

    from vdsim.core.parameters import load_vehicle_preset
    from vdsim.stabilization.simulate import run_closed_loop

    cfg = load_vehicle_preset("mid_size_sedan")
    lh, wheelbase = cfg.vehicle.cg_to_rear, cfg.vehicle.wheelbase
    cases = [("Forward, orientation stabilized", 1, "orientation", "werling_desm"),
             ("Reverse, orientation stabilized", -1, "orientation", "werling_kesm"),
             ("Forward, center stabilized", 1, "center", "werling_desm")]
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 5.0), layout="constrained")
    for ax, color, (label, direction, slow, plant) in zip(axes, SERIES, cases):
        traj = slow_comparison.stored_trajectory(direction)
        p0 = traj.sample(0)
        ego0 = dict(x=p0.x + lh * math.cos(p0.psi), y=p0.y + lh * math.sin(p0.psi), psi=p0.psi, v=0.0,
                    delta=math.atan(wheelbase * direction * p0.kappa))
        log, _ = run_closed_loop("werling_bilevel", traj, cfg, duration=60.0, plant=plant, ego_initial=ego0,
                                 controller_params={"forward_slow": slow, "reinit_enabled": False})
        ax.plot(traj.x, traj.y, color=MUTED, lw=1.2, label="Reference (rear axle)")
        ax.plot(log["x"], log["y"], color=color, lw=2.0, label="Driven (CoG)")
        for tk in np.arange(0.0, log["t"][-1], 6.0):
            i = int(np.argmin(np.abs(log["t"] - tk)))
            draw_box(ax, log["x"][i], log["y"][i], log["psi"][i], 4.8, 1.85, AXIS, zorder=1)
        ax.set_aspect("equal", adjustable="datalim")
        ax.set_title(f"{label}\nmax |$e_n$| = {np.max(np.abs(log['e_n'])) * 100:.1f} cm", fontsize=11.5)
        ax.set_xlabel("x / m")
        ax.legend(loc="upper left", fontsize=9)
    axes[0].set_ylabel("y / m")
    save_png(fig, "slow_tracking.png")


DIAGRAMS = [architecture, frenet, vehicle_dynamics, planning_pipeline]
RESULT_FIGURES = [result_lane_change, result_following, result_evasion, result_stopping, result_consistency,
                  result_controllers, result_gust, result_slow_tracking]


def main():
    selection = sys.argv[1:] or ["diagrams", "results"]
    jobs = {"diagrams": DIAGRAMS, "results": RESULT_FIGURES}
    for job in (fn for key in selection for fn in jobs.get(key, [f for f in DIAGRAMS + RESULT_FIGURES if f.__name__ == key])):
        job()


if __name__ == "__main__":
    main()
