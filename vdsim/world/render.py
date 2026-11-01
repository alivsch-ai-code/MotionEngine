"""Top-view rendering of road networks, traffic participants and the ego vehicle (matplotlib)."""

from __future__ import annotations

import numpy as np

from .collision import rect_corners

TYPE_COLORS = {"car": "#5b7aa5", "truck": "#8c6d31", "pedestrian": "#d1495b", "cyclist": "#e09f3e",
               "static": "#6c757d", "unknown": "#999999"}
EGO_COLOR = "#00798c"
LIGHT_COLORS = {"red": "#d62728", "yellow": "#f2c14e", "green": "#2ca02c", "red_yellow": "#ff7f0e"}
ROAD_FILL = {"driving": "#d4d4d4", "merge": "#cfcfcf", "exit": "#cfcfcf", "parking": "#e4e1d8", "crosswalk": "#e8e8e8"}


def _runs(lane, side):
    # boundary split into runs of equal marking
    x, y = lane.boundary(side)
    kinds = [lane.marking(side, s) for s in lane.center.s]
    out, start = [], 0
    for i in range(1, len(kinds) + 1):
        if i == len(kinds) or kinds[i] != kinds[start]:
            out.append((kinds[start], x[start:i + 1], y[start:i + 1]))
            start = i
    return out


def draw_road(ax, road, t=0.0, centerlines=True, zorder=0):
    for lane in road.lanes.values():
        xl, yl = lane.boundary("left")
        xr, yr = lane.boundary("right")
        ax.fill(np.concatenate([xl, xr[::-1]]), np.concatenate([yl, yr[::-1]]),
                color=ROAD_FILL.get(lane.type, "#d4d4d4"), lw=0, zorder=zorder)
    for lane in road.lanes.values():
        for side in ("left", "right"):
            for kind, x, y in _runs(lane, side):
                if kind == "solid":
                    ax.plot(x, y, "-", color="#ffffff", lw=1.1, zorder=zorder + 1)
                elif kind == "dashed":
                    ax.plot(x, y, linestyle=(0, (4, 4)), color="#ffffff", lw=1.0, zorder=zorder + 1)
                elif kind == "curb":
                    ax.plot(x, y, "-", color="#555555", lw=1.4, zorder=zorder + 1)
        if centerlines:
            c = lane.center
            ax.plot(c.x, c.y, linestyle=(0, (1, 3)), color="#8a8a8a", lw=0.5, zorder=zorder + 1)
    for z in road.conflict_zones.values():
        ax.add_patch(_circle(z.x, z.y, z.radius, "#7f7f7f"))
    for p in road.parking_spots.values():
        c = p.corners()
        ax.plot(np.r_[c[:, 0], c[0, 0]], np.r_[c[:, 1], c[0, 1]], "--", color="#2a9d8f", lw=1.0, zorder=zorder + 2)
    states = road.light_phases(t)
    for sl in road.stop_lines:
        lane = road.lanes[sl.lane_id]
        x0, y0, _ = lane.pose(sl.s, -0.5 * lane.width)
        x1, y1, _ = lane.pose(sl.s, 0.5 * lane.width)
        style = "-" if sl.kind in ("stop", "traffic_light") else (0, (2, 2))
        ax.plot([x0, x1], [y0, y1], linestyle=style, color="#ffffff", lw=2.2, zorder=zorder + 2)
    for lid, tl in road.traffic_lights.items():
        ax.plot(tl.x, tl.y, "o", ms=6, color=LIGHT_COLORS.get(states.get(lid), "#999"), mec="#222", mew=0.6,
                zorder=zorder + 5)


def _circle(x, y, r, color):
    from matplotlib.patches import Circle
    return Circle((x, y), r, fill=False, ls=":", lw=0.8, ec=color, zorder=1)


def draw_objects(ax, objects, colors=None, hidden=(), labels=True, zorder=5):
    from matplotlib.patches import Polygon
    colors = colors or {}
    for o in objects:
        c = rect_corners(o.x, o.y, o.psi, o.length, o.width)[0]
        col = colors.get(o.id, TYPE_COLORS.get(o.type, "#999999"))
        is_hidden = o.id in hidden
        ax.add_patch(Polygon(c, closed=True, fc="none" if is_hidden else col, ec=col if is_hidden else "#222222",
                             lw=0.8, ls="--" if is_hidden else "-", zorder=zorder))
        if labels:
            ax.text(o.x, o.y, str(o.id), fontsize=6, ha="center", va="center", color="#ffffff" if not is_hidden
                    else col, zorder=zorder + 1)


def draw_ego(ax, x, y, psi, length=4.8, width=1.85, zorder=8):
    from matplotlib.patches import Polygon
    c = rect_corners(x, y, psi, length, width)[0]
    ax.add_patch(Polygon(c, closed=True, fc=EGO_COLOR, ec="#0b3c49", lw=1.0, zorder=zorder))
    ax.annotate("", xy=(x + 0.5 * length * np.cos(psi), y + 0.5 * length * np.sin(psi)), xytext=(x, y),
                arrowprops={"arrowstyle": "->", "color": "#ffffff", "lw": 1.0}, zorder=zorder + 1)


def render_scenario(scenario, objects=None, t=0.0, ax=None, ego=None, trails=None, hidden=(), bounds=None, title=None,
                    show_ego=True, figsize=(10, 6)):
    # Draw a ScenarioInstance (or RoadNetwork): road, objects (default: initial actor states), ego (dict or
    # EgoState-like with x, y, psi), trails {id: (xs, ys)}. Returns (fig, ax).
    import matplotlib.pyplot as plt
    road = getattr(scenario, "road", scenario)
    colors = {}
    if objects is None and hasattr(scenario, "actors"):
        sim = scenario.simulator()
        objects = sim.object_states(include_hidden=True)
        hidden = [a.id for a in sim.actors if not a.visible]
        colors = {a.id: a.color for a in sim.actors if a.color}
    elif hasattr(scenario, "actors"):
        colors = {a.id: a.color for a in scenario.actors if getattr(a, "color", None)}
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
    ax.set_facecolor("#f4f1ea")
    draw_road(ax, road, t)
    if trails:
        for oid, (xs, ys) in trails.items():
            ax.plot(xs, ys, "-", lw=0.8, alpha=0.6, color=EGO_COLOR if oid == 0 else colors.get(oid, "#555555"),
                    zorder=3)
    draw_objects(ax, objects or [], colors, set(hidden))
    if show_ego:
        if ego is None and hasattr(scenario, "ego_initial"):
            ego = scenario.ego_initial
        if ego is not None:
            get = (lambda k: ego[k]) if isinstance(ego, dict) else (lambda k: getattr(ego, k))
            draw_ego(ax, get("x"), get("y"), get("psi"))
    ax.set_aspect("equal")
    if bounds is not None:
        ax.set_xlim(bounds[0], bounds[1])
        ax.set_ylim(bounds[2], bounds[3])
    ax.set_xlabel("x / m")
    ax.set_ylabel("y / m")
    if title is None and hasattr(scenario, "metadata"):
        title = f"{scenario.metadata.get('label', scenario.name)}  (t = {t:.1f} s)"
    if title:
        ax.set_title(title, fontsize=10)
    return fig, ax
