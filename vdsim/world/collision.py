"""Collision detection between oriented rectangles with the separating axis theorem (SAT).

Two convex polygons are disjoint iff there is an axis (for rectangles: one of the four edge
normals) on which their projections do not overlap. Vectorized for one rectangle against many.
"""

from __future__ import annotations

import numpy as np

from ..framework.knowledge import trace


def rect_corners(x, y, psi, length, width):
    # corners (N, 4, 2) of rectangles centered at (x, y) with orientation psi
    x, y, psi = np.atleast_1d(x).astype(float), np.atleast_1d(y).astype(float), np.atleast_1d(psi).astype(float)
    hl = 0.5 * np.broadcast_to(np.asarray(length, dtype=float), x.shape)
    hw = 0.5 * np.broadcast_to(np.asarray(width, dtype=float), x.shape)
    c, s = np.cos(psi), np.sin(psi)
    lx = np.stack([hl, -hl, -hl, hl], axis=1)
    ly = np.stack([hw, hw, -hw, -hw], axis=1)
    cx = x[:, None] + lx * c[:, None] - ly * s[:, None]
    cy = y[:, None] + lx * s[:, None] + ly * c[:, None]
    return np.stack([cx, cy], axis=2)


@trace("gottschalk1996", concept="sat_collision", note="Trennachsensatz für orientierte Rechtecke (OBB)")
def sat_overlap(a, b):
    # a: (4, 2) corners of one rectangle, b: (N, 4, 2) corners of N rectangles -> bool array (N,)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if b.ndim == 2:
        b = b[None]
    n = len(b)
    if n == 0:
        return np.zeros(0, dtype=bool)
    ea = np.array([a[1] - a[0], a[2] - a[1]])                    # (2, 2) edges of a
    eb = np.stack([b[:, 1] - b[:, 0], b[:, 2] - b[:, 1]], axis=1)  # (N, 2, 2)
    axes = np.concatenate([np.broadcast_to(ea, (n, 2, 2)), eb], axis=1)  # (N, 4, 2)
    axes = np.stack([-axes[..., 1], axes[..., 0]], axis=-1)       # normals
    pa = np.einsum("nkd,cd->nkc", axes, a)                        # (N, 4 axes, 4 corners)
    pb = np.einsum("nkd,ncd->nkc", axes, b)
    separated = (pa.max(axis=2) < pb.min(axis=2)) | (pb.max(axis=2) < pa.min(axis=2))
    return ~np.any(separated, axis=1)


def collisions(x, y, psi, length, width, objects, margin=0.0):
    # ids of objects (ObjectState-like) overlapping the rectangle (x, y, psi, length, width)
    if not objects:
        return []
    ox = np.array([o.x for o in objects])
    oy = np.array([o.y for o in objects])
    rad = 0.5 * np.hypot(length, width) + 0.5 * np.hypot([o.length for o in objects], [o.width for o in objects])
    near = np.hypot(ox - x, oy - y) <= rad + 2 * margin
    if not np.any(near):
        return []
    idx = np.flatnonzero(near)
    a = rect_corners(x, y, psi, length + 2 * margin, width + 2 * margin)[0]
    b = rect_corners(ox[idx], oy[idx], [objects[i].psi for i in idx], [objects[i].length for i in idx],
                     [objects[i].width for i in idx])
    hit = sat_overlap(a, b)
    return [objects[i].id for i in idx[hit]]


def pairwise_collisions(objects):
    # all colliding pairs (id_a, id_b) among the objects (O(N^2) prefilter by distance)
    pairs = []
    if len(objects) < 2:
        return pairs
    ox = np.array([o.x for o in objects])
    oy = np.array([o.y for o in objects])
    rad = 0.5 * np.hypot([o.length for o in objects], [o.width for o in objects])
    corners = rect_corners(ox, oy, [o.psi for o in objects], [o.length for o in objects], [o.width for o in objects])
    for i in range(len(objects) - 1):
        d = np.hypot(ox[i + 1:] - ox[i], oy[i + 1:] - oy[i])
        cand = np.flatnonzero(d <= rad[i] + rad[i + 1:]) + i + 1
        if len(cand):
            hit = sat_overlap(corners[i], corners[cand])
            pairs += [(objects[i].id, objects[j].id) for j in cand[hit]]
    return pairs
