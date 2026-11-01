"""Runtime benchmarking of the automated-driving stack (per node, planner cycles, real-time factor)."""

from __future__ import annotations

import time

import numpy as np


def benchmark(scenario, stack=None, repeats=3, duration=None, seed=0):
    # Runs the scenario `repeats` times and aggregates the executor profile of every node
    from ..ad import run_scenario
    per_node = {}
    walls, sims, plan_times = [], [], []
    for k in range(repeats):
        start = time.perf_counter()
        result = run_scenario(scenario, stack=stack, seed=seed, duration=duration, record_snapshots=True)
        walls.append(time.perf_counter() - start)
        sims.append(result.duration)
        for node, stats in (result.profile or {}).items():
            per_node.setdefault(node, []).append(stats)
        plan_times += [s.get("compute_time", np.nan) for s in result.snapshots]
    nodes = {}
    for node, runs in per_node.items():
        mean = [r.get("mean", np.nan) for r in runs]
        p95 = [r.get("p95", np.nan) for r in runs]
        mx = [r.get("max", np.nan) for r in runs]
        calls = [r.get("calls", 0) for r in runs]
        nodes[node] = {"mean_ms": 1e3 * float(np.nanmean(mean)), "p95_ms": 1e3 * float(np.nanmean(p95)),
                       "max_ms": 1e3 * float(np.nanmax(mx)), "calls": int(np.mean(calls)),
                       "total_s": float(np.nanmean([r.get("total", np.nan) for r in runs]))}
    plan = np.asarray(plan_times, dtype=float) * 1e3
    plan = plan[np.isfinite(plan)]
    return {
        "repeats": repeats,
        "wall_time_s": float(np.mean(walls)),
        "simulated_s": float(np.mean(sims)),
        "real_time_factor": float(np.mean(sims) / max(np.mean(walls), 1e-9)),
        "nodes": nodes,
        "planner_cycle_ms": ({"mean": float(plan.mean()), "p95": float(np.percentile(plan, 95)),
                              "max": float(plan.max()), "n": int(len(plan))} if len(plan) else {}),
    }


def format_benchmark(report):
    lines = [f"Echtzeitfaktor {report['real_time_factor']:.2f} "
             f"({report['simulated_s']:.1f} s simuliert in {report['wall_time_s']:.2f} s)",
             f"{'Knoten':<26}{'Aufrufe':>9}{'Mittel ms':>11}{'p95 ms':>9}{'Max ms':>9}{'Gesamt s':>10}"]
    for node, s in sorted(report["nodes"].items(), key=lambda kv: -kv[1]["total_s"]):
        lines.append(f"{node:<26}{s['calls']:>9}{s['mean_ms']:>11.3f}{s['p95_ms']:>9.3f}{s['max_ms']:>9.2f}"
                     f"{s['total_s']:>10.2f}")
    pc = report.get("planner_cycle_ms")
    if pc:
        lines.append(f"Planungszyklus: Mittel {pc['mean']:.1f} ms, p95 {pc['p95']:.1f} ms, Max {pc['max']:.1f} ms")
    return "\n".join(lines)
