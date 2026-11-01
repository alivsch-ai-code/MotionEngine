"""Export der vdsim-RoadNetwork als OpenDRIVE (.xodr) für CARLA.

CARLA kann beliebige Straßennetze über client.generate_opendrive_world() laden.
Dieses Modul konvertiert die vdsim-Referenzlinien (curvature-continuous) in eine
minimale OpenDRIVE-1.6-Datei mit Spuren, Fahrbahnmarkierungen und Ampeln.

Für einfache Szenarien (Autobahn, Landstraße) reicht alternativ eine vorhandene
CARLA-Karte (Town04 = Autobahn, Town03 = ländlich, Town05 = urban).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from ..core.logging_setup import get_logger

log = get_logger("viz3d.road_export")

CARLA_MAPS = {
    "highway": "Town04",
    "autobahn": "Town04",
    "rural": "Town07",
    "landstra": "Town07",
    "urban": "Town03",
    "innerort": "Town03",
    "intersection": "Town05",
    "kreuzung": "Town05",
    "parking": "Town03",
    "park": "Town03",
    "roundabout": "Town03",
    "kreisverkehr": "Town03",
}


def suggest_carla_map(road_network):
    name = getattr(road_network, "name", "").lower()
    for key, town in CARLA_MAPS.items():
        if key in name:
            return town
    lanes = road_network.lanes if hasattr(road_network, "lanes") else {}
    n = len(lanes) if isinstance(lanes, dict) else len(list(lanes))
    if n <= 3:
        return "Town07"
    return "Town04"


def road_to_opendrive(road_network, ds=1.0):
    """Minimaler OpenDRIVE-Export (Geometrie aus Polylinien, ein Road pro Lane-Kette).

    Gibt den XML-String zurück. Die Genauigkeit reicht für die CARLA-Visualisierung,
    ist aber keine vollständige ASAM-konforme xodr-Datei (keine Elevation, kein
    superelevation, vereinfachte Verbindungen).
    """
    root = ET.Element("OpenDRIVE")
    header = ET.SubElement(root, "header", revMajor="1", revMinor="6",
                           name=getattr(road_network, "name", "vdsim"))
    ET.SubElement(header, "geoReference").text = "+proj=utm +zone=32 +datum=WGS84"

    lanes = road_network.lanes if isinstance(road_network.lanes, dict) else {l.id: l for l in road_network.lanes}
    visited = set()
    road_id = 0

    for lid, lane in lanes.items():
        if lid in visited or lane.junction is not None:
            continue
        chain = _build_chain(lanes, lid, visited)
        if not chain:
            continue
        _add_road(root, road_id, chain, lanes, ds)
        road_id += 1

    for lid, lane in lanes.items():
        if lid in visited:
            continue
        visited.add(lid)
        _add_road(root, road_id, [lid], lanes, ds)
        road_id += 1

    tls = getattr(road_network, "traffic_lights", None)
    if tls:
        _add_signals(root, tls if isinstance(tls, dict) else {t.id: t for t in tls}, lanes)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def export(road_network, path, ds=1.0):
    xodr = road_to_opendrive(road_network, ds)
    Path(path).write_text(xodr, encoding="utf-8")
    log.info("OpenDRIVE geschrieben: %s (%d Bytes)", path, len(xodr))
    return path


def _build_chain(lanes, start_id, visited):
    chain = [start_id]
    visited.add(start_id)
    lid = start_id
    while True:
        lane = lanes[lid]
        succ = [s for s in lane.successors if s in lanes and s not in visited and lanes[s].junction is None]
        if not succ:
            break
        lid = succ[0]
        visited.add(lid)
        chain.append(lid)
    return chain


def _add_road(root, road_id, chain, lanes, ds):
    first = lanes[chain[0]]
    center = first.center
    for lid in chain[1:]:
        next_lane = lanes[lid]
        center = _concat_lines(center, next_lane.center)

    s_arr = center.s
    x_arr, y_arr = center.x, center.y
    theta = center.theta if hasattr(center, "theta") else np.unwrap(np.arctan2(np.gradient(y_arr), np.gradient(x_arr)))
    length = float(s_arr[-1] - s_arr[0])

    road = ET.SubElement(root, "road", name=chain[0], length=f"{length:.4f}", id=str(road_id), junction="-1")
    plan = ET.SubElement(road, "planView")

    step = max(int(ds / max(np.mean(np.diff(s_arr)), 0.01)), 1)
    indices = list(range(0, len(s_arr) - 1, step))
    if indices[-1] != len(s_arr) - 2:
        indices.append(len(s_arr) - 2)

    for i in indices:
        j = min(i + step, len(s_arr) - 1)
        seg_len = float(s_arr[j] - s_arr[i])
        if seg_len < 1e-6:
            continue
        geo = ET.SubElement(plan, "geometry", s=f"{float(s_arr[i] - s_arr[0]):.4f}",
                            x=f"{float(x_arr[i]):.6f}", y=f"{float(y_arr[i]):.6f}",
                            hdg=f"{float(theta[i]):.6f}", length=f"{seg_len:.4f}")
        kappa_i = float(center.kappa[i]) if hasattr(center, "kappa") else 0.0
        kappa_j = float(center.kappa[j]) if hasattr(center, "kappa") else 0.0
        if abs(kappa_i) < 1e-6 and abs(kappa_j) < 1e-6:
            ET.SubElement(geo, "line")
        elif abs(kappa_j - kappa_i) < 1e-6:
            ET.SubElement(geo, "arc", curvature=f"{kappa_i:.8f}")
        else:
            ET.SubElement(geo, "spiral", curvStart=f"{kappa_i:.8f}", curvEnd=f"{kappa_j:.8f}")

    _add_lanes_section(road, first)


def _add_lanes_section(road, lane):
    lanes_el = ET.SubElement(road, "lanes")
    ls = ET.SubElement(lanes_el, "laneSection", s="0")
    center_el = ET.SubElement(ls, "center")
    ET.SubElement(center_el, "lane", id="0", type="none", level="false")
    right = ET.SubElement(ls, "right")
    rl = ET.SubElement(right, "lane", id="-1", type="driving", level="false")
    w = ET.SubElement(rl, "width", sOffset="0", a=f"{lane.width:.2f}", b="0", c="0", d="0")
    rm_type = "broken" if lane.marking_right == "dashed" else "solid" if lane.marking_right == "solid" else "none"
    ET.SubElement(rl, "roadMark", sOffset="0", type=rm_type, weight="standard", color="white", width="0.12")


def _add_signals(root, traffic_lights, lanes):
    for tl_id, tl in traffic_lights.items():
        x = getattr(tl, "x", 0.0)
        y = getattr(tl, "y", 0.0)
        for road in root.findall("road"):
            signals = road.find("signals")
            if signals is None:
                signals = ET.SubElement(road, "signals")
            sig = ET.SubElement(signals, "signal", s="0", t="0", id=str(tl_id),
                                name=str(tl_id), dynamic="yes", orientation="+",
                                country="DE", type="1.000.001")


def _concat_lines(a, b):
    from ..geometry.reference_line import ReferenceLine
    if hasattr(a, "append"):
        return a.append(b)
    s2 = b.s + (a.s[-1] - b.s[0])
    return ReferenceLine(
        s=np.concatenate([a.s, s2[1:]]),
        x=np.concatenate([a.x, b.x[1:]]),
        y=np.concatenate([a.y, b.y[1:]]),
        name=a.name,
    )
