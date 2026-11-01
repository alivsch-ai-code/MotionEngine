"""Lazy selection of the best admissible trajectory per longitudinal mode (Werling 2011, 3.5.5).

    step 5  the combined set is checked in ascending total cost; candidates are transformed into
            world coordinates in batches and tested for restrictions and collisions; the first
            valid trajectory is the best one (optimization heuristic, 3.2). If non-separable cost
            terms are active, the first `rerank_window` valid candidates are re-ranked with them.
    step 6  replacement strategy (Ablösestrategie): among the modes, the trajectory with the
            smallest signed initial jerk a_dot(0) wins (most decelerating / least accelerating).
    fallback if no candidate is valid, the trajectory that stays collision free (and within the
            restrictions) for the longest time is followed (Werling 5.3, footnote 10); valid=False.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..framework.knowledge import trace
from .combination import frenet_to_world, time_to_arc

STATUS_VALID, STATUS_CONSTRAINT, STATUS_COLLISION, STATUS_UNCHECKED = 0, 1, 2, 3


@dataclass
class SelectionSettings:
    batch_min: int = 32
    batch_max: int = 512
    max_checks: int = 4000
    rerank_window: int = 1
    brake_candidates: int = 8


@dataclass
class ModeResult:
    label: str
    kind: str
    lat: object
    lon: object
    evaluator: object
    order: np.ndarray                       # combined indices in ascending separable cost
    total: np.ndarray                       # separable total cost of all combined indices
    n_candidates: int = 0
    n_feasible: int = 0
    status: np.ndarray = None               # (n,) int8, STATUS_*
    t_constraint: np.ndarray = None         # (n,) first restriction violation (inf: none, nan: not checked)
    t_collision: np.ndarray = None          # (n,) first collision (inf: none, nan: not checked)
    reason: dict = field(default_factory=dict)        # combined index -> reason (invalid candidates)
    violations: dict = field(default_factory=dict)    # constraint name -> count
    checked: list = field(default_factory=list)       # checked combined indices (in check order)
    best: int | None = None
    best_cost: float = np.inf
    combined_costs: dict = field(default_factory=dict)
    initial_jerk: float = np.nan
    fallback: int | None = None
    fallback_time: float = -np.inf
    target: object = None
    note: str = ""

    def split(self, c):
        n_lon = len(self.lon)
        return int(c // n_lon), int(c % n_lon)

    @property
    def n_checked(self):
        return len(self.checked)


@trace("werling2011", section="3.5.5", equation="Schritt 4-5", concept="lazy_selection",
       note="Prüfung in aufsteigender Kostenreihenfolge, erste gültige Trajektorie ist die beste")
def select_mode(label, lat, lon, evaluator, cost_model, constraints, checker, ctx, settings, k_lat=1.0, k_lon=1.0):
    n_lat, n_lon = len(lat), len(lon)
    total = ((k_lat * lat.total)[:, None] + (k_lon * lon.total)[None, :]).ravel()
    feasible = (lat.feasible[:, None] & lon.feasible[None, :]).ravel()
    n = len(total)
    res = ModeResult(label=label, kind=lon.kind, lat=lat, lon=lon, evaluator=evaluator, order=np.zeros(0, int),
                     total=total, n_candidates=n, status=np.full(n, STATUS_UNCHECKED, dtype=np.int8),
                     t_constraint=np.full(n, np.nan), t_collision=np.full(n, np.nan))
    idx = np.flatnonzero(feasible)
    if len(idx) == 0:
        # everything pre-filtered: check the full set (otherwise no fallback would be possible)
        idx = np.arange(n)
        res.note = "Vorfilter verwirft alle Kandidaten"
    res.n_feasible = int(np.count_nonzero(feasible))
    order = idx[np.argsort(total[idx], kind="stable")]
    res.order = order
    window = max(int(settings.rerank_window), 1)
    valid_list = []
    pos, bs = 0, settings.batch_min
    while pos < len(order) and len(res.checked) < settings.max_checks:
        cidx = order[pos:pos + bs]
        pos += len(cidx)
        bs = min(bs * 2, settings.batch_max)
        _check(res, evaluator, constraints, checker, cidx, n_lon, valid_list)
        if len(valid_list) >= window:
            break
    if not valid_list and pos < len(order) and settings.brake_candidates > 0:
        # budget exhausted without a valid candidate: additionally check the most braking longitudinal
        # candidates with every lateral candidate (fallback "maximum admissible deceleration", Werling 5.3)
        brake = np.argsort(lon.sd[:, -1], kind="stable")[:settings.brake_candidates]
        extra = (np.arange(n_lat)[:, None] * n_lon + brake[None, :]).ravel()
        extra = extra[res.status[extra] == STATUS_UNCHECKED]
        if len(extra):
            _check(res, evaluator, constraints, checker, extra, n_lon, valid_list)
    if valid_list:
        cand = valid_list[:window]
        best_total = total[np.array(cand)]
        comb_costs = {}
        if cost_model.combined_terms:
            ci = np.array(cand)
            batch = evaluator.batch(ci // n_lon, ci % n_lon)
            coll = checker.check(batch)
            extra_cost, comb_costs = cost_model.combined(batch, coll, ctx)
            best_total = best_total + extra_cost
        r = int(np.argmin(best_total))
        res.best = int(cand[r])
        res.best_cost = float(best_total[r])
        res.combined_costs = {k: float(v[r]) for k, v in comb_costs.items()}
    else:
        res.fallback, res.fallback_time = fallback_candidate(res)
    return res


def _check(res, evaluator, constraints, checker, cidx, n_lon, valid_list):
    # restrictions and collisions of one batch of combined indices; results are recorded in res.
    # The collision check runs only for candidates within the vehicle restrictions.
    batch = evaluator.batch(cidx // n_lon, cidx % n_lon)
    c_ok, c_t, c_reason, per = constraints.check(batch)
    for name, mask in per.items():
        cnt = int(np.count_nonzero(mask))
        if cnt:
            res.violations[name] = res.violations.get(name, 0) + cnt
    res.checked.extend(int(c) for c in cidx)
    res.t_constraint[cidx] = c_t
    res.status[cidx[~c_ok]] = STATUS_CONSTRAINT
    for c, why in zip(cidx[~c_ok], c_reason[~c_ok]):
        res.reason[int(c)] = str(why)
    if np.any(c_ok):
        sub = cidx[c_ok]
        coll = checker.check(batch.subset(c_ok))
        res.t_collision[sub] = coll.t_collision
        hit = coll.collides
        res.status[sub[hit]] = STATUS_COLLISION
        for c, oid in zip(sub[hit], coll.object_id[hit]):
            res.reason[int(c)] = f"Objekt {int(oid)}"
        ok = sub[~hit]
        res.status[ok] = STATUS_VALID
        valid_list.extend(int(c) for c in ok)


@trace("werling2011", section="5.3", note="Fußnote 10: längste kollisionsfreie Trajektorie", concept="fallback")
def fallback_candidate(res):
    # longest admissible trajectory: among candidates within the vehicle restrictions the one with the
    # latest first collision; if every candidate violates a restriction, the latest first violation
    if not res.checked:
        return None, -np.inf
    checked = np.array(res.checked)
    c_ok = np.isinf(res.t_constraint[checked])
    if np.any(c_ok):
        pool, score = checked[c_ok], res.t_collision[checked[c_ok]]
    else:
        pool, score = checked, res.t_constraint[checked]
    # ties on the time grid: the lowest speed at that time (maximum admissible deceleration, Werling 5.3),
    # then the cheaper candidate (lexsort is stable, `checked` is in cost order)
    grid = res.lon.t0 + res.lon.grid
    k = np.clip(np.searchsorted(grid, np.minimum(score, grid[-1]) - 1e-9), 0, len(grid) - 1)
    speed = res.lon.sd[pool % len(res.lon), k]
    t_key = np.round(np.where(np.isfinite(score), score, 1e9), 6)
    best = int(np.lexsort((speed, -t_key))[0])
    return int(pool[best]), float(score[best])


@trace("werling2011", section="3.5.5", equation="Schritt 6", concept="replacement_strategy",
       note="Ablösestrategie: kleinster vorzeichenbehafteter Anfangsruck a_dot(0) setzt sich durch")
def initial_jerk(res, c, h=1e-3):
    # signed initial jerk a_dot(0) of the world trajectory (exact polynomials, central difference)
    i, j = res.split(c)
    lat, lon, ctx = res.lat, res.lon, res.evaluator.ctx
    t = np.array([0.0, h])
    s, sd, sdd, _ = lon.poly.evaluate(t, idx=np.array([j]))
    if lat.mode == "arc":
        d, d_p, d_pp, _ = lat.poly.evaluate(np.maximum(s - lat.s0, 0.0), idx=np.array([i]))
    else:
        d, dd, ddd, _ = lat.poly.evaluate(t, idx=np.array([i]))
        d_p, d_pp = time_to_arc(sd, sdd, dd, ddd)
    w = frenet_to_world(ctx.reference_line, s, sd, sdd, d, d_p, d_pp)
    return float((w["a"][0, 1] - w["a"][0, 0]) / h)


def choose_mode(results):
    # step 6 over all modes with a valid trajectory; None if every mode failed
    ok = [r for r in results if r.best is not None]
    if not ok:
        return None
    for r in ok:
        r.initial_jerk = initial_jerk(r, r.best)
    return min(ok, key=lambda r: (r.initial_jerk, r.best_cost))


def choose_fallback(results):
    pool = [r for r in results if r.fallback is not None]
    if not pool:
        return None
    best = max(pool, key=lambda r: r.fallback_time)
    best.initial_jerk = initial_jerk(best, best.fallback)
    return best
