"""Parking situations: parallel, perpendicular and angled spots, entered forward or in reverse, left or right.

Layout (right side, mirrored for the left): the street runs along +x, the curb or the end of the parking
row is at y = 0, the parked vehicles stand on y > 0 and the driving lane (or the aisle of a parking lot)
lies above them. The ego vehicle starts in the lane before the spot; the goal is the vehicle centered in
the spot. Dimensions follow common design guidelines (EAR 2005 / FGSV, ADAC): parallel spots 2.0-2.5 m
deep and ~1.2-1.5 x vehicle length long when tight, perpendicular spots 2.5 m x 5.0 m with a 6.0 m aisle,
angled spots (45/60 deg) with a 3.5-5.0 m one-way aisle.

All poses here are of the vehicle's geometric center; `to_reference` converts to the planner reference
point P of a steering geometry.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

KINDS = ("parallel", "perpendicular", "angled")
ENTRIES = ("reverse", "forward")
SIDES = ("right", "left")


@dataclass
class Obstacle:
    kind: str                 # car, curb, wall
    polygon: list             # [(x, y), ...]


@dataclass
class ParkingScenario:
    kind: str
    entry: str
    side: str
    start: tuple              # (x, y, heading) of the vehicle center
    goal: tuple
    obstacles: list           # [Obstacle]
    spot: list                # polygon of the target spot (display)
    bounds: tuple             # (xmin, xmax, ymin, ymax)
    final_direction: int      # required direction of the last move (-1 reverse, +1 forward)
    info: dict = field(default_factory=dict)

    @property
    def polygons(self):
        return [o.polygon for o in self.obstacles]


def _rect(cx, cy, length, width, heading=0.0):
    c, s = math.cos(heading), math.sin(heading)
    out = []
    for a, b in ((0.5 * length, 0.5 * width), (0.5 * length, -0.5 * width), (-0.5 * length, -0.5 * width),
                 (-0.5 * length, 0.5 * width)):
        out.append((cx + c * a - s * b, cy + s * a + c * b))
    return out


def _mirror(sc: ParkingScenario) -> ParkingScenario:
    def m(p):
        return (p[0], -p[1])

    def mp(pose):
        return (pose[0], -pose[1], -pose[2])
    return ParkingScenario(sc.kind, sc.entry, "left", mp(sc.start), mp(sc.goal),
                           [Obstacle(o.kind, [m(p) for p in o.polygon]) for o in sc.obstacles],
                           [m(p) for p in sc.spot], (sc.bounds[0], sc.bounds[1], -sc.bounds[3], -sc.bounds[2]),
                           sc.final_direction, dict(sc.info))


def parallel(vehicle_length=4.8, vehicle_width=1.85, gap_length=None, spot_depth=2.2, lane_width=3.5,
             entry="reverse", neighbor_length=4.6, neighbor_width=1.85, curb_offset=0.25, lanes=2):
    # default: comfortable gap (two to three moves); vehicle_length + 1.4 m is a tight spot with many moves
    gap = gap_length if gap_length is not None else (vehicle_length + 1.8 if entry == "reverse" else
                                                     vehicle_length + 2.6)
    obstacles = [Obstacle("curb", [(-40, -1.0), (40, -1.0), (40, 0.0), (-40, 0.0)])]
    yc = 0.5 * spot_depth
    for cx in (-0.5 * gap - 0.5 * neighbor_length, 0.5 * gap + 0.5 * neighbor_length,
               -0.5 * gap - 1.5 * neighbor_length - 1.2, 0.5 * gap + 1.5 * neighbor_length + 1.2):
        obstacles.append(Obstacle("car", _rect(cx, min(yc, curb_offset + 0.5 * neighbor_width), neighbor_length,
                                               neighbor_width)))
    top = spot_depth + lanes * lane_width
    obstacles.append(Obstacle("wall", [(-40, top), (40, top), (40, top + 1.0), (-40, top + 1.0)]))
    goal_y = curb_offset + 0.5 * vehicle_width
    lane_y = spot_depth + 0.5 * lane_width
    start = (-0.5 * gap - 14.0, lane_y, 0.0)
    spot = [(-0.5 * gap, 0.0), (0.5 * gap, 0.0), (0.5 * gap, spot_depth), (-0.5 * gap, spot_depth)]
    return ParkingScenario("parallel", entry, "right", start, (0.0, goal_y, 0.0), obstacles, spot,
                           (-35.0, 35.0, -1.5, top + 1.5), -1 if entry == "reverse" else 1,
                           {"gap_length": gap, "spot_depth": spot_depth, "lane_width": lane_width})


def perpendicular(vehicle_length=4.8, vehicle_width=1.85, spot_width=2.5, spot_depth=5.0, aisle_width=6.0,
                  entry="reverse", neighbor_length=4.6, neighbor_width=1.85, neighbors=True):
    obstacles = [Obstacle("wall", [(-40, -1.0), (40, -1.0), (40, 0.0), (-40, 0.0)])]
    if neighbors:
        for k in (-2, -1, 1, 2):
            cx = k * spot_width
            obstacles.append(Obstacle("car", _rect(cx, 0.5 * spot_depth, neighbor_length, neighbor_width,
                                                   math.pi / 2)))
    top = spot_depth + aisle_width
    # opposite parking row (end of the aisle)
    obstacles.append(Obstacle("wall", [(-40, top), (40, top), (40, top + 1.0), (-40, top + 1.0)]))
    heading = math.pi / 2 if entry == "reverse" else -math.pi / 2
    goal = (0.0, 0.2 + 0.5 * vehicle_length, heading)
    start = (-14.0, spot_depth + 0.5 * aisle_width, 0.0)
    spot = [(-0.5 * spot_width, 0.0), (0.5 * spot_width, 0.0), (0.5 * spot_width, spot_depth),
            (-0.5 * spot_width, spot_depth)]
    return ParkingScenario("perpendicular", entry, "right", start, goal, obstacles, spot,
                           (-30.0, 30.0, -1.5, top + 1.5), -1 if entry == "reverse" else 1,
                           {"spot_width": spot_width, "spot_depth": spot_depth, "aisle_width": aisle_width})


def angled(vehicle_length=4.8, vehicle_width=1.85, angle_deg=60.0, spot_width=2.5, spot_depth=5.0,
           aisle_width=4.5, entry="forward", neighbor_length=4.6, neighbor_width=1.85, neighbors=True):
    a = math.radians(angle_deg)
    # spots lean in the driving direction: forward entry turns right by (pi - a) ... the spot axis points
    # from the aisle into the row at heading -a (driving along +x)
    axis = -a
    pitch = spot_width / math.sin(a)                # spacing of the spots along the street
    depth_y = spot_depth * math.sin(a)              # extent of a spot normal to the street
    # back of the row: below the deepest corner of a vehicle centered in a spot, plus 0.3 m
    reach = 0.5 * vehicle_length * math.sin(a) + 0.5 * vehicle_width * math.cos(a)
    y_back = 0.5 * depth_y - reach - 0.3
    obstacles = [Obstacle("wall", [(-40, y_back - 1.0), (40, y_back - 1.0), (40, y_back), (-40, y_back)])]

    def center(k):
        # center of spot k: on the line from the aisle edge into the row
        x0 = k * pitch
        return x0 + 0.5 * spot_depth * math.cos(axis), depth_y * 0.5
    if neighbors:
        for k in (-2, -1, 1, 2):
            cx, cy = center(k)
            obstacles.append(Obstacle("car", _rect(cx, cy, neighbor_length, neighbor_width, axis)))
    top = depth_y + aisle_width
    obstacles.append(Obstacle("wall", [(-40, top), (40, top), (40, top + 1.0), (-40, top + 1.0)]))
    cx, cy = center(0)
    heading = axis if entry == "forward" else axis + math.pi
    goal = (cx, cy, heading)
    start = (-16.0, depth_y + 0.5 * aisle_width, 0.0)
    spot = _rect(cx, cy, spot_depth, spot_width, axis)
    return ParkingScenario("angled", entry, "right", start, goal, obstacles, spot,
                           (-30.0, 30.0, y_back - 1.5, top + 1.5), 1 if entry == "forward" else -1,
                           {"angle_deg": angle_deg, "spot_width": spot_width, "aisle_width": aisle_width})


def build_scenario(kind="parallel", entry="reverse", side="right", **kw) -> ParkingScenario:
    if kind not in KINDS:
        raise ValueError(f"unknown parking kind '{kind}', available: {KINDS}")
    if entry not in ENTRIES:
        raise ValueError(f"unknown entry '{entry}', available: {ENTRIES}")
    if side not in SIDES:
        raise ValueError(f"unknown side '{side}', available: {SIDES}")
    builders: dict[str, Callable[..., ParkingScenario]] = {"parallel": parallel, "perpendicular": perpendicular,
                                                           "angled": angled}
    sc = builders[kind](entry=entry, **kw)
    return _mirror(sc) if side == "left" else sc


def center_to_reference(pose, footprint):
    """Vehicle-center pose -> pose of the planner reference point P."""
    off = 0.5 * (footprint.front - footprint.rear)      # center ahead of P
    return (pose[0] - off * math.cos(pose[2]), pose[1] - off * math.sin(pose[2]), pose[2])


def reference_to_center(x, y, theta, footprint):
    off = 0.5 * (footprint.front - footprint.rear)
    return x + off * math.cos(theta), y + off * math.sin(theta)
