"""Research mode: batch simulation, parameter sweeps, Monte Carlo, controller/planner comparison.

A job is a plain dict (picklable, JSON-serializable):

    {"label": "baseline",
     "scenario": "highway_cut_in" | {scenario spec dict},
     "scenario_params": {"cut_in_gap": 12.0},       # overrides of the scenario parameters
     "stack": {"controller": {"component": "tracking_controller/werling_bilevel", "params": {...}}},
     "seed": 1, "duration": None, "snapshots": False}

Overrides are given as dotted paths into the job, e.g.
    "stack.planner.params.cost.k_jerk"  or  "scenario_params.lead_speed"

Every run is deterministic for a given job (seeds are part of the job), so batch results
are reproducible and independent of the number of worker processes.
"""

from __future__ import annotations

import copy
import itertools
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from ..framework.context import stable_seed
from ..framework.knowledge import trace


def set_path(job, dotted, value):
    parts = dotted.split(".")
    obj = job
    for part in parts[:-1]:
        if part not in obj or obj[part] is None:
            obj[part] = {}
        obj = obj[part]
    obj[parts[-1]] = value
    return job


def get_path(job, dotted, default=None):
    obj = job
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return default
        obj = obj[part]
    return obj


def run_job(job):
    # Executes one job; returns a light, picklable record (KPIs, metadata, optional saved path)
    from ..ad import run_scenario
    start = time.perf_counter()
    try:
        result = run_scenario(job["scenario"], stack=job.get("stack"), seed=job.get("seed"),
                              duration=job.get("duration"), scenario_params=job.get("scenario_params"),
                              record_snapshots=job.get("snapshots", False))
        record = {"label": job.get("label", ""), "job": job, "kpis": result.kpis, "ok": True,
                  "stop_reason": result.metadata.get("stop_reason", ""), "wall_time": time.perf_counter() - start,
                  "profile": result.profile}
        if job.get("save_dir"):
            import re
            safe = re.sub(r"[^\w\-]+", "_", str(job.get("label") or "run")).strip("_") or "run"
            path = Path(job["save_dir"]) / safe
            record["path"] = str(result.save(path))
        return record
    except Exception as exc:
        import traceback
        return {"label": job.get("label", ""), "job": job, "kpis": {}, "ok": False, "error": repr(exc),
                "traceback": traceback.format_exc(), "wall_time": time.perf_counter() - start}


def run_batch(jobs, workers=0, progress=None):
    # workers = 0 -> sequential in this process; > 0 -> process pool (order of the result list = job order)
    jobs = list(jobs)
    records = [None] * len(jobs)
    if workers and workers > 0 and len(jobs) > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(run_job, job): i for i, job in enumerate(jobs)}
            done = 0
            for fut in as_completed(futures):
                records[futures[fut]] = fut.result()
                done += 1
                if progress:
                    progress(done, len(jobs))
    else:
        for i, job in enumerate(jobs):
            records[i] = run_job(job)
            if progress:
                progress(i + 1, len(jobs))
    return BatchResult(records)


@trace("montgomery2017", concept="full_factorial_design", note="vollfaktorieller Versuchsplan")
def parameter_sweep(base_job, grid, label_fmt=None):
    # full factorial grid: {"stack.planner.params.cost.k_jerk": [0.1, 1, 10], ...} -> list of jobs
    keys = list(grid)
    jobs = []
    for values in itertools.product(*(grid[k] for k in keys)):
        job = copy.deepcopy(base_job)
        for k, v in zip(keys, values):
            set_path(job, k, v)
        job["label"] = (label_fmt.format(**dict(zip([k.split(".")[-1] for k in keys], values))) if label_fmt
                        else ", ".join(f"{k.split('.')[-1]}={v}" for k, v in zip(keys, values)))
        job["sweep"] = dict(zip(keys, values))
        jobs.append(job)
    return jobs


def _sample(spec, rng):
    kind = spec.get("dist", "uniform")
    if kind == "uniform":
        return float(rng.uniform(spec["low"], spec["high"]))
    if kind == "normal":
        value = float(rng.normal(spec["mean"], spec["std"]))
        if "low" in spec or "high" in spec:
            value = float(np.clip(value, spec.get("low", -np.inf), spec.get("high", np.inf)))
        return value
    if kind == "lognormal":
        return float(rng.lognormal(spec["mean"], spec["sigma"]))
    if kind == "choice":
        values = spec["values"]
        return values[int(rng.integers(len(values)))]
    if kind == "integer":
        return int(rng.integers(spec["low"], spec["high"] + 1))
    raise ValueError(f"unknown distribution '{kind}'")


@trace("saltelli2008", concept="monte_carlo", note="Monte-Carlo-Stichprobe der Eingangsparameter")
def monte_carlo(base_job, distributions, n, seed=0, vary_scenario_seed=True):
    # n jobs with parameters drawn from `distributions` ({path: {"dist": ..., ...}}); reproducible via seed
    rng = np.random.default_rng(stable_seed("monte_carlo", seed))
    jobs = []
    for i in range(n):
        job = copy.deepcopy(base_job)
        drawn = {path: _sample(spec, rng) for path, spec in distributions.items()}
        for path, value in drawn.items():
            set_path(job, path, value)
        if vary_scenario_seed:
            job["seed"] = int(stable_seed("mc_run", seed, i) % 100000)
        job["label"] = f"MC {i + 1:03d}"
        job["sample"] = drawn
        jobs.append(job)
    return jobs


def compare_components(base_job, layer, variants):
    # one job per component variant of a layer, e.g. layer="controller",
    # variants={"Werling": {"component": "tracking_controller/werling_bilevel"}, "Stanley": {...}}
    jobs = []
    for label, spec in variants.items():
        job = copy.deepcopy(base_job)
        job.setdefault("stack", {})[layer] = spec if isinstance(spec, dict) else {"component": spec}
        job["label"] = label
        jobs.append(job)
    return jobs


def compare_controllers(base_job, variants):
    return compare_components(base_job, "controller", variants)


def compare_planners(base_job, variants):
    return compare_components(base_job, "planner", variants)


class BatchResult:
    def __init__(self, records):
        self.records = list(records)

    def __len__(self):
        return len(self.records)

    @property
    def ok(self):
        return [r for r in self.records if r.get("ok")]

    @property
    def failed(self):
        return [r for r in self.records if not r.get("ok")]

    def kpi_keys(self):
        keys = []
        for r in self.records:
            for k in r.get("kpis", {}):
                if k not in keys and isinstance(r["kpis"][k], (int, float)):
                    keys.append(k)
        return keys

    def table(self, keys=None):
        # {kpi: {"labels": [...], "values": [...]}} for dashboards and comparison plots
        keys = keys or self.kpi_keys()
        labels = [r.get("label", "") for r in self.records]
        return {k: {"labels": labels, "values": [r.get("kpis", {}).get(k, np.nan) for r in self.records]}
                for k in keys}

    def column(self, key):
        return np.array([r.get("kpis", {}).get(key, np.nan) for r in self.records], dtype=float)

    def statistics(self, keys=None):
        # Monte Carlo statistics: mean, std, percentiles and share of failed runs per KPI
        stats = {}
        for k in keys or self.kpi_keys():
            col = self.column(k)
            col = col[np.isfinite(col)]
            if not len(col):
                continue
            stats[k] = {"mean": float(col.mean()), "std": float(col.std(ddof=1)) if len(col) > 1 else 0.0,
                        "min": float(col.min()), "p05": float(np.percentile(col, 5)),
                        "p50": float(np.percentile(col, 50)), "p95": float(np.percentile(col, 95)),
                        "max": float(col.max()), "n": int(len(col))}
        collisions = self.column("collision")
        stats["_runs"] = {"n": len(self.records), "failed": len(self.failed),
                          "collision_rate": float(np.nanmean(collisions)) if len(collisions) else np.nan}
        return stats

    def sensitivity(self, kpi):
        # linear sensitivity (standardized regression coefficient) of a KPI w.r.t. swept/sampled parameters
        rows = [r for r in self.ok if "sample" in r["job"] or "sweep" in r["job"]]
        if len(rows) < 3:
            return {}
        params = sorted({p for r in rows for p in (r["job"].get("sample") or r["job"].get("sweep") or {})})
        X = np.array([[float((r["job"].get("sample") or r["job"].get("sweep"))[p]) for p in params] for r in rows])
        y = np.array([r["kpis"].get(kpi, np.nan) for r in rows], dtype=float)
        mask = np.isfinite(y)
        X, y = X[mask], y[mask]
        if len(y) < len(params) + 2 or np.std(y) == 0:
            return {}
        Xs = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1)
        ys = (y - y.mean()) / y.std()
        coef, *_ = np.linalg.lstsq(np.column_stack([Xs, np.ones(len(ys))]), ys, rcond=None)
        return dict(zip(params, coef[:-1].tolist()))

    def best(self, kpi, lower_is_better=True):
        col = self.column(kpi)
        if not np.any(np.isfinite(col)):
            return None
        i = int(np.nanargmin(col) if lower_is_better else np.nanargmax(col))
        return self.records[i]

    def to_json(self, path):
        def clean(obj):
            if isinstance(obj, dict):
                return {str(k): clean(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [clean(v) for v in obj]
            if isinstance(obj, (np.floating, np.integer)):
                return obj.item()
            if isinstance(obj, float) and not np.isfinite(obj):
                return None
            return obj
        Path(path).write_text(json.dumps(clean(self.records), indent=1, default=str), encoding="utf-8")
        return path

    def to_csv(self, path):
        keys = self.kpi_keys()
        lines = [";".join(["label", *keys])]
        for r in self.records:
            lines.append(";".join([str(r.get("label", ""))] + [f"{r.get('kpis', {}).get(k, '')}" for k in keys]))
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        return path
