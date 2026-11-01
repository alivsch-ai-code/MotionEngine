"""OpenDRIVE (.xodr) import: reference line of a road (line, arc, spiral, poly3, paramPoly3) and lane centers."""

import xml.etree.ElementTree as ET

import numpy as np
from scipy.integrate import cumulative_trapezoid

from .trajectory import Trajectory


def _sample_geometry(geom, ds):
    s0 = float(geom.get("s"))
    x0, y0, hdg, length = (float(geom.get(k)) for k in ("x", "y", "hdg", "length"))
    n = max(int(np.ceil(length / ds)), 2)
    u = np.linspace(0.0, length, n + 1)
    child = geom[0]
    tag = child.tag
    if tag in ("line", "arc", "spiral"):
        if tag == "line":
            k = np.zeros_like(u)
        elif tag == "arc":
            k = np.full_like(u, float(child.get("curvature")))
        else:
            k0, k1 = float(child.get("curvStart")), float(child.get("curvEnd"))
            k = k0 + (k1 - k0) * u / length
        fine = np.linspace(0.0, length, 8 * n + 1)
        kf = np.interp(fine, u, k)
        psi = hdg + cumulative_trapezoid(kf, fine, initial=0.0)
        x = x0 + cumulative_trapezoid(np.cos(psi), fine, initial=0.0)
        y = y0 + cumulative_trapezoid(np.sin(psi), fine, initial=0.0)
        return s0 + u, x[::8], y[::8]
    if tag == "poly3":
        a, b, c, d = (float(child.get(k)) for k in "abcd")
        lu, lv = u, a + b * u + c * u**2 + d * u**3
    elif tag == "paramPoly3":
        coef = {k: float(child.get(k)) for k in ("aU", "bU", "cU", "dU", "aV", "bV", "cV", "dV")}
        p = u / length if child.get("pRange", "normalized") == "normalized" else u
        lu = coef["aU"] + coef["bU"] * p + coef["cU"] * p**2 + coef["dU"] * p**3
        lv = coef["aV"] + coef["bV"] * p + coef["cV"] * p**2 + coef["dV"] * p**3
    else:
        raise ValueError(f"unsupported OpenDRIVE geometry '{tag}'")
    x = x0 + lu * np.cos(hdg) - lv * np.sin(hdg)
    y = y0 + lu * np.sin(hdg) + lv * np.cos(hdg)
    return s0 + u, x, y


def _poly(entry, ds):
    a, b, c, d = (float(entry.get(k, 0.0)) for k in "abcd")
    return a + b * ds + c * ds**2 + d * ds**3


def _lane_center_offset(road, s_values, lane_id):
    # lateral offset of the center of `lane_id` (negative = right of the reference line)
    lanes = road.find("lanes")
    offsets = np.zeros_like(s_values)
    if lanes is None:
        return offsets
    lane_offsets = sorted(lanes.findall("laneOffset"), key=lambda e: float(e.get("s")))
    sections = sorted(lanes.findall("laneSection"), key=lambda e: float(e.get("s")))
    for i, s in enumerate(s_values):
        base = 0.0
        active = [lo for lo in lane_offsets if float(lo.get("s")) <= s]
        if active:
            base = _poly(active[-1], s - float(active[-1].get("s")))
        if lane_id == 0 or not sections:
            offsets[i] = base
            continue
        section = [sec for sec in sections if float(sec.get("s")) <= s] or sections[:1]
        section = section[-1]
        ds = s - float(section.get("s"))
        side = section.find("right" if lane_id < 0 else "left")
        widths = {}
        if side is not None:
            for lane in side.findall("lane"):
                entries = [w for w in lane.findall("width") if float(w.get("sOffset")) <= ds]
                if entries:
                    widths[abs(int(lane.get("id")))] = _poly(entries[-1], ds - float(entries[-1].get("sOffset")))
        k = abs(lane_id)
        dist = sum(widths.get(j, 0.0) for j in range(1, k)) + widths.get(k, 0.0) / 2
        offsets[i] = base + np.sign(lane_id) * dist
    return offsets


def load_opendrive(path, road_id=None, lane_id=-1, ds=0.5, speed_kmh=None):
    root = ET.parse(path).getroot()
    roads = root.findall("road")
    if not roads:
        raise ValueError("no <road> in OpenDRIVE file")
    road = next((r for r in roads if r.get("id") == str(road_id)), roads[0]) if road_id is not None else roads[0]
    s_all, x_all, y_all = [], [], []
    for geom in sorted(road.find("planView").findall("geometry"), key=lambda g: float(g.get("s"))):
        s, x, y = _sample_geometry(geom, ds)
        s_all.append(s[:-1]); x_all.append(x[:-1]); y_all.append(y[:-1])
    s_all.append(s[-1:]); x_all.append(x[-1:]); y_all.append(y[-1:])
    s, x, y = np.concatenate(s_all), np.concatenate(x_all), np.concatenate(y_all)

    ref = Trajectory(x, y)
    offset = _lane_center_offset(road, s, lane_id)
    nx, ny = -np.sin(ref.psi), np.cos(ref.psi)
    if len(nx) != len(offset):
        offset = np.interp(ref.s, s - s[0], offset)
    lx, ly = ref.x + offset * nx, ref.y + offset * ny

    if speed_kmh is None:
        speed = road.find("type/speed")
        speed_kmh = float(speed.get("max")) if speed is not None and speed.get("max", "").replace(".", "").isdigit() else 50.0
        if speed is not None and speed.get("unit") == "mph":
            speed_kmh *= 1.609
    traj = Trajectory(lx, ly, speed_kmh / 3.6, name=f"opendrive road {road.get('id')}")
    traj.boundaries = [(ref.x, ref.y)]
    traj.metadata.update(source="opendrive", road_id=road.get("id"), lane_id=lane_id)
    return traj
