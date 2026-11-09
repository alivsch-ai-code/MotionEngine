"""Parking planner: Hybrid A* with Reeds-Shepp analytic expansion and an exact footprint collision check.

Search (Dolgov, Thrun, Montemerlo and Diebel 2010; Kurzer 2016):
    * nodes are continuous poses (x, y, theta) of the reference point P (see steering.py); a node is
      closed per cell of a 3D grid (xy resolution, heading bins), so the search stays finite while the
      path stays exactly drivable;
    * motion primitives are arcs of constant curvature (n_steer values in [-kappa_max, kappa_max]) of
      arc length `step`, driven forward or backward;
    * cost g: travelled length (reverse weighted with reverse_penalty), a penalty per direction change
      (gear switch), and penalties for steering effort and steering changes;
    * heuristic h: max of the Reeds-Shepp length without obstacles (non-holonomic, admissible) and the
      shortest 8-connected grid distance around the obstacles for a disc of the vehicle's half width
      (holonomic with obstacles);
    * analytic expansion: from promising nodes all Reeds-Shepp words to the goal are tried in order of
      cost; the first collision-free word completes the path, so the goal pose is reached exactly.

Collision: obstacles are polygons rasterized into an occupancy grid; the Euclidean distance transform
gives the clearance of every cell. A pose is free if every sample point on the outline of the vehicle
rectangle (spacing below the grid resolution) has a clearance of at least `margin`; poses whose
center clearance exceeds the circumscribed radius are accepted without sampling.
"""

from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass, field

import numpy as np

from .reeds_shepp import all_paths, sample
from .steering import SteeringGeometry


@dataclass
class Footprint:
    """Vehicle rectangle relative to the planning reference point P (along the axis, forward > 0)."""
    front: float      # distance from P to the front bumper, m
    rear: float       # distance from P to the rear bumper, m
    width: float      # m

    @classmethod
    def from_vehicle(cls, vehicle, geometry: SteeringGeometry, front_overhang=None, rear_overhang=None):
        v = getattr(vehicle, "vehicle", vehicle)
        rest = max(float(v.length) - float(v.wheelbase), 0.0)
        fo = 0.5 * rest if front_overhang is None else float(front_overhang)
        ro = rest - fo if rear_overhang is None else float(rear_overhang)
        x_front_bumper = geometry.x_front + fo
        x_rear_bumper = geometry.x_rear - ro
        return cls(front=x_front_bumper - geometry.x_ref, rear=geometry.x_ref - x_rear_bumper, width=float(v.width))

    @property
    def length(self):
        return self.front + self.rear

    def outline(self, spacing=0.08):
        """Sample points on the rectangle outline in the vehicle frame of P, shape (n, 2)."""
        nx = max(int(math.ceil(self.length / spacing)), 2)
        ny = max(int(math.ceil(self.width / spacing)), 2)
        xs = np.linspace(-self.rear, self.front, nx + 1)
        ys = np.linspace(-0.5 * self.width, 0.5 * self.width, ny + 1)
        pts = np.concatenate([np.c_[xs, np.full_like(xs, ys[0])], np.c_[xs, np.full_like(xs, ys[-1])],
                              np.c_[np.full_like(ys, xs[0]), ys], np.c_[np.full_like(ys, xs[-1]), ys]])
        return pts

    def corners(self, x, y, theta):
        c, s = math.cos(theta), math.sin(theta)
        local = [(self.front, 0.5 * self.width), (self.front, -0.5 * self.width),
                 (-self.rear, -0.5 * self.width), (-self.rear, 0.5 * self.width)]
        return [(x + c * a - s * b, y + s * a + c * b) for a, b in local]


class OccupancyMap:
    """Rasterized obstacles with a clearance (distance transform) layer."""

    def __init__(self, polygons, bounds, resolution=0.05):
        from matplotlib.path import Path
        from scipy.ndimage import distance_transform_edt

        self.xmin, self.xmax, self.ymin, self.ymax = (float(b) for b in bounds)
        self.res = float(resolution)
        self.nx = int(math.ceil((self.xmax - self.xmin) / self.res)) + 1
        self.ny = int(math.ceil((self.ymax - self.ymin) / self.res)) + 1
        gx = self.xmin + self.res * np.arange(self.nx)
        gy = self.ymin + self.res * np.arange(self.ny)
        X, Y = np.meshgrid(gx, gy, indexing="ij")
        pts = np.c_[X.ravel(), Y.ravel()]
        occ = np.zeros(self.nx * self.ny, dtype=bool)
        for poly in polygons:
            poly = np.asarray(poly, dtype=float)
            lo, hi = poly.min(axis=0), poly.max(axis=0)
            box = (pts[:, 0] >= lo[0] - self.res) & (pts[:, 0] <= hi[0] + self.res) & \
                  (pts[:, 1] >= lo[1] - self.res) & (pts[:, 1] <= hi[1] + self.res)
            if box.any():
                occ[box] |= Path(poly).contains_points(pts[box], radius=self.res * 0.5)
        occ = occ.reshape(self.nx, self.ny)
        # the map border counts as an obstacle
        occ[0, :] = occ[-1, :] = occ[:, 0] = occ[:, -1] = True
        self.occupied = occ
        self.clearance = distance_transform_edt(~occ) * self.res

    def lookup(self, x, y):
        # the border cells are occupied (clearance 0), so clamping outside points to the border is exact
        i = ((np.asarray(x) - self.xmin) * (1.0 / self.res) + 0.5).astype(np.int64)
        j = ((np.asarray(y) - self.ymin) * (1.0 / self.res) + 0.5).astype(np.int64)
        np.minimum(np.maximum(i, 0, out=i), self.nx - 1, out=i)
        np.minimum(np.maximum(j, 0, out=j), self.ny - 1, out=j)
        return self.clearance[i, j]


class CollisionChecker:
    def __init__(self, occupancy: OccupancyMap, footprint: Footprint, margin=0.15):
        self.map = occupancy
        self.fp = footprint
        self.margin = float(margin)
        # outline points at the spacing of the margin: discs of radius margin around them cover the edge,
        # so the effective margin is at least sqrt(margin^2 - (spacing/2)^2) ~ 0.87 margin
        self.outline = footprint.outline(spacing=max(min(self.margin, 0.2), 2 * occupancy.res))
        cx = 0.5 * (footprint.front - footprint.rear)
        self.center_offset = cx
        self.radius = math.hypot(0.5 * footprint.length, 0.5 * footprint.width)
        # three circles covering the rectangle: a cheap sufficient test before the outline test
        seg = footprint.length / 3.0
        self.circle_x = np.array([-footprint.rear + seg * (i + 0.5) for i in range(3)])
        self.circle_r = math.hypot(0.5 * seg, 0.5 * footprint.width)

    def free(self, x, y, theta):
        """Vectorized over arrays of poses: True where the vehicle rectangle keeps the margin."""
        x, y, theta = np.atleast_1d(x), np.atleast_1d(y), np.atleast_1d(theta)
        c, s = np.cos(theta), np.sin(theta)
        cxw, cyw = x + c * self.center_offset, y + s * self.center_offset
        ok = self.map.lookup(cxw, cyw) >= self.radius + self.margin
        need = ~ok
        if need.any():
            px = x[need, None] + c[need, None] * self.circle_x[None, :]
            py = y[need, None] + s[need, None] * self.circle_x[None, :]
            ok[need] = self.map.lookup(px, py).min(axis=1) >= self.circle_r + self.margin
            need = ~ok
        if need.any():
            px = x[need, None] + c[need, None] * self.outline[None, :, 0] - s[need, None] * self.outline[None, :, 1]
            py = y[need, None] + s[need, None] * self.outline[None, :, 0] + c[need, None] * self.outline[None, :, 1]
            clear = self.map.lookup(px, py).min(axis=1)
            # the center must not lie inside an obstacle either (outline points could straddle a thin one)
            inner = self.map.lookup(cxw[need], cyw[need]) > 0
            ok[need] = (clear >= self.margin) & inner
        return ok

    def min_clearance(self, x, y, theta):
        x, y, theta = np.atleast_1d(x), np.atleast_1d(y), np.atleast_1d(theta)
        c, s = np.cos(theta), np.sin(theta)
        px = x[:, None] + c[:, None] * self.outline[None, :, 0] - s[:, None] * self.outline[None, :, 1]
        py = y[:, None] + s[:, None] * self.outline[None, :, 0] + c[:, None] * self.outline[None, :, 1]
        return self.map.lookup(px, py).min(axis=1)


@dataclass
class PlannerSettings:
    xy_resolution: float = 0.3        # m, closed-set cell size
    heading_bins: int = 72            # 5 deg
    step: float = 0.6                 # m, arc length of a motion primitive
    n_steer: int = 5                  # curvature values per direction
    reverse_penalty: float = 1.3      # cost factor of reverse driving
    switch_penalty: float = 4.0       # m equivalent per direction change
    steer_penalty: float = 0.3        # m equivalent at full lock per primitive
    steer_change_penalty: float = 2.0 # m equivalent per full-range steering change (smoother paths)
    margin: float = 0.15              # m, clearance to obstacles
    curvature_reserve: float = 0.9    # share of the maximum curvature used for planning (control headroom)
    max_nodes: int = 40000
    time_limit: float = 12.0          # s
    analytic_every: int = 4           # try a Reeds-Shepp shot every n expansions (always when h is small)
    analytic_radius: float = 12.0     # m, always try a shot closer than this
    analytic_candidates: int = 8      # Reeds-Shepp words tried per shot (cheapest first)
    improve_nodes: int = 400          # expansions after the first solution to look for a cheaper one
    holonomic_resolution: float = 0.25
    allow_reverse: bool = True
    max_cusps: int = 12
    escape_clearance: float = 0.6     # m, below this outline clearance a pose counts as cramped (fine grid,
                                      # moves to the limit)


@dataclass
class ParkingPath:
    success: bool
    message: str
    x: np.ndarray = field(default_factory=lambda: np.zeros(0))
    y: np.ndarray = field(default_factory=lambda: np.zeros(0))
    theta: np.ndarray = field(default_factory=lambda: np.zeros(0))       # vehicle heading
    direction: np.ndarray = field(default_factory=lambda: np.zeros(0))   # +1 forward, -1 reverse
    kappa: np.ndarray = field(default_factory=lambda: np.zeros(0))       # curvature of P, left > 0 (vehicle frame)
    s: np.ndarray = field(default_factory=lambda: np.zeros(0))           # travelled distance
    segments: list = field(default_factory=list)   # [{"direction", "start", "end", "length"}]
    nodes_expanded: int = 0
    compute_time: float = 0.0
    analytic_word: str = ""

    @property
    def length(self):
        return float(self.s[-1]) if len(self.s) else 0.0

    @property
    def cusps(self):
        return max(len(self.segments) - 1, 0)


def _segments(direction):
    segs = []
    start = 0
    for i in range(1, len(direction) + 1):
        if i == len(direction) or direction[i] != direction[start]:
            segs.append((start, i - 1, int(direction[start])))
            start = i
    return segs


def _join(parts) -> ParkingPath:
    """Concatenate (x, y, theta, direction, kappa) pieces whose end and start poses coincide."""
    X, Y, TH, D, K = (np.concatenate([p[i] if j == 0 else p[i][1:] for j, p in enumerate(parts)])
                      for i in range(5))
    S = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(X), np.diff(Y)))])
    segs = [{"direction": d, "start": a, "end": b, "length": float(S[b] - S[a])} for a, b, d in _segments(D)]
    segs = [sg for sg in segs if sg["length"] > 1e-6] or segs
    for prev, seg in zip(segs, segs[1:], strict=False):
        seg["start"] = prev["end"]
        seg["length"] = float(S[seg["end"]] - S[seg["start"]])
    return ParkingPath(True, "ok", X, Y, TH, D, K, S, segs)


def _reverse_piece(path: ParkingPath, end: int):
    """Poses path[end] -> path[0] driven backwards (opposite directions, same curvature)."""
    x, y, th = path.x[:end + 1][::-1], path.y[:end + 1][::-1], path.theta[:end + 1][::-1]
    d = path.direction[:end + 1]
    k = path.kappa[:end + 1]
    n = end + 1
    rd = np.empty(n)
    rk = np.empty(n)
    rd[1:] = -d[::-1][:-1]
    rk[1:] = k[::-1][:-1]
    rd[0], rk[0] = (rd[1], rk[1]) if n > 1 else (1.0, 0.0)
    return (x, y, th, rd, rk)


def _holonomic_heuristic(occ: OccupancyMap, goal, half_width, res):
    # Dijkstra from the goal on a coarse grid; cells closer than the half width to an obstacle are blocked
    step = max(int(round(res / occ.res)), 1)
    clear = occ.clearance[::step, ::step]
    nx, ny = clear.shape
    blocked = clear < half_width * 0.9
    dist = np.full((nx, ny), np.inf)
    gi = int(round((goal[0] - occ.xmin) / (occ.res * step)))
    gj = int(round((goal[1] - occ.ymin) / (occ.res * step)))
    gi, gj = min(max(gi, 0), nx - 1), min(max(gj, 0), ny - 1)
    dist[gi, gj] = 0.0
    heap = [(0.0, gi, gj)]
    cell = occ.res * step
    nbrs = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))]
    while heap:
        d, i, j = heapq.heappop(heap)
        if d > dist[i, j]:
            continue
        for di, dj, w in nbrs:
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny and not blocked[a, b]:
                nd = d + w * cell
                if nd < dist[a, b]:
                    dist[a, b] = nd
                    heapq.heappush(heap, (nd, a, b))

    def h(x, y):
        i = int(round((x - occ.xmin) / cell))
        j = int(round((y - occ.ymin) / cell))
        if 0 <= i < nx and 0 <= j < ny:
            v = dist[i, j]
            return v if np.isfinite(v) else 1e6
        return 1e6
    return h


def _arc(x, y, th, kappa, d, n):
    # n poses along an arc of signed length d (negative = reverse), exact integration
    ds = np.linspace(d / n, d, n)
    if abs(kappa) < 1e-9:
        return x + ds * math.cos(th), y + ds * math.sin(th), np.full(n, th)
    th_new = th + ds * kappa
    return x + (np.sin(th_new) - math.sin(th)) / kappa, y - (np.cos(th_new) - math.cos(th)) / kappa, th_new


class ParkingPlanner:
    """Hybrid A* parking planner for one steering geometry, footprint and obstacle set."""

    def __init__(self, geometry: SteeringGeometry, footprint: Footprint, polygons, bounds,
                 settings: PlannerSettings | None = None, map_resolution=0.05):
        self.geo = geometry
        self.fp = footprint
        self.cfg = settings or PlannerSettings()
        self.map = OccupancyMap(polygons, bounds, map_resolution)
        self.check = CollisionChecker(self.map, footprint, self.cfg.margin)
        # plan with a curvature reserve: the controller needs steering headroom to correct deviations
        self.kmax = self.cfg.curvature_reserve * geometry.max_curvature
        self.radius = 1.0 / self.kmax

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _key(x, y, th, cfg):
        r = cfg.xy_resolution
        b = int(round((th % (2 * math.pi)) / (2 * math.pi) * cfg.heading_bins)) % cfg.heading_bins
        return int(math.floor(x / r)), int(math.floor(y / r)), b

    def _rs_cost(self, p):
        segs = p.segments
        c = 0.0
        last = None
        for kind, s in segs:
            c += abs(s) * (self.cfg.reverse_penalty if s < 0 else 1.0)
            if kind != "S":
                c += self.cfg.steer_penalty * abs(s) / self.cfg.step
            if last is not None and (s > 0) != (last > 0):
                c += self.cfg.switch_penalty
            last = s
        return c

    def _try_analytic(self, node_pose, goal, direction_in, final_direction=0, first_direction=0):
        paths = all_paths(node_pose, goal, self.radius)
        if not self.cfg.allow_reverse:
            paths = [p for p in paths if all(s > 0 for _, s in p.segments)]
        if final_direction:
            paths = [p for p in paths if p.segments and (p.segments[-1][1] > 0) == (final_direction > 0)]
        if first_direction:
            paths = [p for p in paths if p.segments and (p.segments[0][1] > 0) == (first_direction > 0)]
        scored = []
        for p in paths:
            c = self._rs_cost(p)
            if p.segments and direction_in and (p.segments[0][1] > 0) != (direction_in > 0):
                c += self.cfg.switch_penalty
            scored.append((c, p))
        scored.sort(key=lambda cp: cp[0])
        for c, p in scored[:self.cfg.analytic_candidates]:
            smp = sample(p, node_pose, step=0.15)
            if self.check.free(smp["x"], smp["y"], smp["theta"]).all():
                return c, p, smp
        return None

    # ------------------------------------------------------------------ search
    def plan(self, start, goal, final_direction: int = 0) -> ParkingPath:
        """start, goal: (x, y, theta) of the reference point P. final_direction: required direction of the
        last move into the goal (-1 reverse in, +1 forward in, 0 any).

        1) The way out of the spot is planned from the goal with moves driven to the limit (multi-maneuver
           parking, Vorobieva et al. 2015). Short fixed steps gain only centimeters per gear change in a
           tight spot; moves to the limit use all the space there is.
        2) One Hybrid A* search from the start; its analytic shots may end at the goal or at any gear-change
           pose of the way out, from where the way out is driven backwards into the spot."""
        tic = time.perf_counter()
        cfg = self.cfg
        if not self.check.free(*start)[0]:
            return ParkingPath(False, "start pose collides", compute_time=time.perf_counter() - tic)
        if not self.check.free(*goal)[0]:
            return ParkingPath(False, "goal pose collides", compute_time=time.perf_counter() - tic)
        escapes = self._escape(goal, -final_direction, cfg.escape_clearance, min(0.2 * cfg.time_limit, 2.0),
                               max_exits=4)
        targets = [(tuple(goal), None)]
        for escape in escapes:
            for e in sorted({sg["end"] for sg in escape.segments}):
                if e > 0:
                    targets.append(((float(escape.x[e]), float(escape.y[e]), float(escape.theta[e])),
                                    _reverse_piece(escape, e)))
        from dataclasses import replace
        rest = max(cfg.time_limit - (time.perf_counter() - tic), 0.5)
        found = self._search(start, goal, final_direction, replace(cfg, time_limit=rest), targets=targets)
        if found.success:
            found = self.shortcut(found)
        found.compute_time = time.perf_counter() - tic
        if not found.success and not escapes:
            found.message = "no way into the spot found (spot too small for this vehicle?)"
        return found

    def shortcut(self, path: ParkingPath, min_gain=0.05) -> ParkingPath:
        """Path smoothing within each move: a stretch between two poses of the same move is replaced by the
        shortest Reeds-Shepp path that keeps the move's direction (no extra cusp) if it is collision-free and
        shorter. Removes the zig-zag of the search primitives (greedy shortcutting, LaValle 2006, 7.1)."""
        pieces = []
        for seg in path.segments:
            a, b, d = seg["start"], seg["end"], int(seg["direction"])
            xs, ys, ths = path.x[a:b + 1], path.y[a:b + 1], path.theta[a:b + 1]
            ks, ds = path.kappa[a:b + 1], path.direction[a:b + 1]
            out = [(xs[:1], ys[:1], ths[:1], ds[:1], ks[:1])]
            i = 0
            n = len(xs)
            while i < n - 1:
                done = False
                for j in range(n - 1, i, -max((n - i) // 6, 1)):
                    if j <= i + 1:
                        break
                    rs = [p for p in all_paths((xs[i], ys[i], ths[i]), (xs[j], ys[j], ths[j]), self.radius)
                          if p.segments and all((sgm > 0) == (d > 0) for _, sgm in p.segments)]
                    if not rs:
                        continue
                    p = min(rs, key=lambda q: q.length)
                    old = float(np.sum(np.hypot(np.diff(xs[i:j + 1]), np.diff(ys[i:j + 1]))))
                    if p.length > old - min_gain:
                        continue
                    smp = sample(p, (xs[i], ys[i], ths[i]), step=0.1)
                    if self.check.free(smp["x"], smp["y"], smp["theta"]).all():
                        out.append((smp["x"][1:], smp["y"][1:], smp["theta"][1:], smp["direction"][1:],
                                    smp["kappa"][1:]))
                        i, done = j, True
                        break
                if not done:
                    out.append((xs[i + 1:i + 2], ys[i + 1:i + 2], ths[i + 1:i + 2], ds[i + 1:i + 2], ks[i + 1:i + 2]))
                    i += 1
            pieces.append(tuple(np.concatenate([o[k] for o in out]) for k in range(5)))
        if not pieces:
            return path
        joined = _join(pieces)
        joined.nodes_expanded, joined.analytic_word, joined.message = path.nodes_expanded, path.analytic_word, path.message
        return joined

    def _escape(self, pose, first_direction, exit_clearance, time_limit, max_exits=4) -> list:
        """Way out of the spot: each move keeps its steering (full or half lock either way, or straight) until
        the clearance margin is reached, then the gear changes. Best-first over the move sequence; ends at
        the first pose that keeps exit_clearance and is at least half a vehicle length from the spot. Returns
        up to max_exits ways out that leave with different first moves (geometrically different exits)."""
        tic = time.perf_counter()
        cfg = self.cfg
        ds, max_len = 0.05, 4.0
        n = int(max_len / ds)
        steer = (self.kmax, 0.5 * self.kmax, 0.0, -0.5 * self.kmax, -self.kmax)
        away = 0.5 * self.fp.length
        nodes = [[pose[0], pose[1], pose[2], 0.0, -1, 0, 0.0, 0, None]]
        heap = [(0.0, 0)]
        seen = set()
        expanded = 0
        found: list = []
        first_moves: set = set()

        def score(xs, ys, clear):
            # remaining "distance" to the exit condition: clearance deficit and distance still to cover
            return 3.0 * max(exit_clearance - clear, 0.0) + max(away - math.hypot(xs - pose[0], ys - pose[1]), 0.0)

        while heap and time.perf_counter() - tic < time_limit and expanded < cfg.max_nodes:
            _, idx = heapq.heappop(heap)
            x, y, th, g, parent, d_in, _k, cusps = nodes[idx][:8]
            key = (round(x / 0.05), round(y / 0.05), round((th % (2 * math.pi)) / math.radians(2.0)), d_in)
            if key in seen:
                continue
            seen.add(key)
            expanded += 1
            for d in (1, -1):
                if (parent < 0 and first_direction and d != first_direction) or d == d_in:
                    continue          # a move ends at the limit: the next one uses the other gear
                if d_in != 0 and cusps >= 2 * cfg.max_cusps:
                    continue
                for k in steer:
                    xs, ys, ths = _arc(x, y, th, k, d * max_len, n)
                    free = self.check.free(xs, ys, ths)
                    stop = n if free.all() else int(np.argmin(free))
                    if stop < 2:
                        continue
                    xs, ys, ths = xs[:stop], ys[:stop], ths[:stop]
                    clear = self.check.min_clearance(xs, ys, ths)
                    dist = np.hypot(xs - pose[0], ys - pose[1])
                    out = np.flatnonzero((clear >= exit_clearance) & (dist >= away))
                    if len(out):
                        xs, ys, ths = xs[:out[0] + 1], ys[:out[0] + 1], ths[:out[0] + 1]
                    ng = g + ds * len(xs) + (cfg.switch_penalty * 0.25 if d_in else 0.0)
                    nodes.append([float(xs[-1]), float(ys[-1]), float(ths[-1]), ng, idx, d, k,
                                  cusps + (1 if d_in else 0), (xs, ys, ths)])
                    if len(out):
                        # first move of this way out: one exit per first move keeps the exits diverse
                        j = len(nodes) - 1
                        while nodes[j][4] > 0:
                            j = nodes[j][4]
                        if j not in first_moves:
                            first_moves.add(j)
                            found.append(self._assemble(nodes, len(nodes) - 1, None, None, expanded, tic))
                            if len(found) >= max_exits:
                                return found
                        continue
                    heapq.heappush(heap, (ng + score(xs[-1], ys[-1], float(clear[-1])), len(nodes) - 1))
        return found

    def _search(self, start, goal, final_direction, cfg: PlannerSettings, targets=None) -> ParkingPath:
        """Hybrid A* from start to goal (or to one of the targets [(pose, tail)], see plan)."""
        tic = time.perf_counter()
        h_hol = _holonomic_heuristic(self.map, goal, 0.5 * self.fp.width, cfg.holonomic_resolution)
        kappas = np.linspace(-self.kmax, self.kmax, cfg.n_steer)
        dirs = (1, -1) if cfg.allow_reverse else (1,)
        n_sub = max(int(math.ceil(cfg.step / 0.1)), 2)
        # motion primitives in the node frame: (direction, kappa) -> n_sub poses, computed once
        prims = [(d, float(k)) for d in dirs for k in kappas]
        lx = np.zeros((len(prims), n_sub))
        ly = np.zeros_like(lx)
        lth = np.zeros_like(lx)
        for i, (d, k) in enumerate(prims):
            lx[i], ly[i], lth[i] = _arc(0.0, 0.0, 0.0, k, d * cfg.step, n_sub)
        p_dir = np.array([d for d, _ in prims])
        p_k = np.array([k for _, k in prims])
        p_cost = cfg.step * np.where(p_dir < 0, cfg.reverse_penalty, 1.0) + cfg.steer_penalty * np.abs(p_k) / self.kmax
        cands = targets or [(tuple(goal), None)]

        def h_rs(x, y, th):
            rs = all_paths((x, y, th), goal, self.radius)
            return min((p.length for p in rs), default=0.0)

        # node: [x, y, th, g, parent, direction, kappa, cusps, poses, rs_checked]
        nodes = [[start[0], start[1], start[2], 0.0, -1, 0, 0.0, 0, None, False]]
        open_heap = [(h_hol(start[0], start[1]), 0)]
        closed = {}
        expanded = 0
        best = None          # (total cost, path); after the first hit the search continues a little
        stop_at = None
        while open_heap:
            if expanded >= cfg.max_nodes or time.perf_counter() - tic > cfg.time_limit:
                break
            if stop_at is not None and expanded >= stop_at:
                break
            f, idx = heapq.heappop(open_heap)
            if best is not None and f >= best[0]:
                break
            node = nodes[idx]
            x, y, th, g, parent, d_in, k_in, cusps = node[:8]
            key = self._key(x, y, th, cfg)
            if key in closed and closed[key] <= g + 1e-9:
                continue
            if not node[9]:
                # lazy heuristic: the Reeds-Shepp term only for nodes that reach the top of the queue
                node[9] = True
                h = max(f - g, h_rs(x, y, th))
                if g + h > f + 1e-9:
                    heapq.heappush(open_heap, (g + h, idx))
                    continue
            closed[key] = g
            expanded += 1
            if f - g < cfg.analytic_radius and (expanded % cfg.analytic_every == 1 or f - g < 0.5 * cfg.analytic_radius):
                # the goal itself, then the nearest gear-change poses of the way out of the spot
                order = [cands[0]] + sorted(cands[1:], key=lambda c: math.hypot(c[0][0] - x, c[0][1] - y))[:3]
                for pose, tail in order:
                    shot = self._try_analytic((x, y, th), pose, d_in, final_direction if tail is None else 0)
                    if shot is None:
                        continue
                    total = g + shot[0] + (self._tail_cost(tail) if tail is not None else 0.0)
                    if best is not None and total >= best[0]:
                        continue
                    path = self._assemble(nodes, idx, shot[1], shot[2], expanded, tic)
                    if tail is not None:
                        joined = _join([(path.x, path.y, path.theta, path.direction, path.kappa), tail])
                        joined.analytic_word = path.analytic_word
                        joined.message = "via the way out of the spot"
                        path = joined
                    best = (total, path)
                    if stop_at is None:
                        stop_at = expanded + cfg.improve_nodes
            c, sn = math.cos(th), math.sin(th)
            X = x + c * lx - sn * ly
            Y = y + sn * lx + c * ly
            TH = th + lth
            ok = self.check.free(X.ravel(), Y.ravel(), TH.ravel()).reshape(X.shape).all(axis=1)
            for i in np.flatnonzero(ok):
                d, k = int(p_dir[i]), float(p_k[i])
                switch = d_in != 0 and d != d_in
                if switch and cusps >= cfg.max_cusps:
                    continue
                ng = g + float(p_cost[i]) + cfg.steer_change_penalty * abs(k - k_in) / (2 * self.kmax)
                if switch:
                    ng += cfg.switch_penalty
                nx_, ny_, nth = float(X[i, -1]), float(Y[i, -1]), float(TH[i, -1])
                nk = self._key(nx_, ny_, nth, cfg)
                if nk in closed and closed[nk] <= ng:
                    continue
                nodes.append([nx_, ny_, nth, ng, idx, d, k, cusps + (1 if switch else 0), (X[i], Y[i], TH[i]),
                              False])
                heapq.heappush(open_heap, (ng + h_hol(nx_, ny_), len(nodes) - 1))
        if best is not None:
            best[1].nodes_expanded = expanded
            best[1].compute_time = time.perf_counter() - tic
            return best[1]
        return ParkingPath(False, "no path found within the search limits", nodes_expanded=expanded,
                           compute_time=time.perf_counter() - tic)

    def _tail_cost(self, tail):
        x, y, _th, d, _k = tail
        steps = np.hypot(np.diff(x), np.diff(y))
        dd = d[1:]
        length = float(np.sum(steps * np.where(dd < 0, self.cfg.reverse_penalty, 1.0)))
        return length + self.cfg.switch_penalty * float(np.count_nonzero(np.diff(dd)))

    def _assemble(self, nodes, idx, rs_path, rs_samples, expanded, tic):
        chain = []
        while idx >= 0:
            chain.append(nodes[idx])
            idx = nodes[idx][4]
        chain.reverse()
        x0, y0, th0 = chain[0][0], chain[0][1], chain[0][2]
        X, Y, TH, D, K = [x0], [y0], [th0], [], []
        for nd in chain[1:]:
            xs, ys, ths = nd[8]
            X.extend(xs.tolist())
            Y.extend(ys.tolist())
            TH.extend(ths.tolist())
            D.extend([nd[5]] * len(xs))
            K.extend([nd[6]] * len(xs))
        if rs_samples is not None:
            X.extend(rs_samples["x"][1:].tolist())
            Y.extend(rs_samples["y"][1:].tolist())
            TH.extend(rs_samples["theta"][1:].tolist())
            D.extend(rs_samples["direction"][1:].tolist())
            K.extend(rs_samples["kappa"][1:].tolist())
        if not D:
            return ParkingPath(True, "already at the goal", np.array(X), np.array(Y), np.array(TH),
                               np.ones(1), np.zeros(1), np.zeros(1), [], expanded, time.perf_counter() - tic)
        D.insert(0, D[0])
        K.insert(0, K[0])
        X, Y, TH, D, K = (np.array(a, dtype=float) for a in (X, Y, TH, D, K))
        step = np.hypot(np.diff(X), np.diff(Y))
        # zero-length joints between segments carry no distance
        S = np.concatenate([[0.0], np.cumsum(step)])
        segs = [{"direction": d, "start": a, "end": b, "length": float(S[b] - S[a])}
                for a, b, d in _segments(D) if b > a or len(D) == 1]
        # drop zero-length segments; every segment starts at the cusp where the previous one ended
        segs = [s for s in segs if s["length"] > 1e-6] or segs
        for prev, seg in zip(segs, segs[1:], strict=False):
            seg["start"] = prev["end"]
            seg["length"] = float(S[seg["end"]] - S[seg["start"]])
        return ParkingPath(True, "ok", X, Y, TH, D, K, S, segs, expanded, time.perf_counter() - tic,
                           rs_path.word() if rs_path is not None else "")
