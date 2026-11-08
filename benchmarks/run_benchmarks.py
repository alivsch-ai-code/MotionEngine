"""Reproducible performance benchmarks: simulation throughput, planning latency, memory, API latency.

    python benchmarks/run_benchmarks.py                 # all, writes benchmarks/results/latest.json
    python benchmarks/run_benchmarks.py --quick         # fewer repetitions
    python benchmarks/run_benchmarks.py --profile       # also cProfile hotspots of sim and planner

Every number in benchmarks/README.md comes from this script; the JSON records the hardware and
the library versions. Timings are the median of the repetitions (wall clock, single thread).
"""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import os
import platform
import pstats
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")

from vdsim.core.parameters import load_vehicle_preset  # noqa: E402
from vdsim.core.registry import create  # noqa: E402
from vdsim.simulation.environment import Environment  # noqa: E402
from vdsim.simulation.scenario import Scenario  # noqa: E402
from vdsim.simulation.simulator import Simulator  # noqa: E402
from vdsim.simulation.vehicle_state import ControlInput  # noqa: E402

MODELS = ["bicycle_kinematic", "bicycle_linear", "bicycle_nonlinear", "double_track", "multibody"]


def median_time(fn, repeats):
    times = []
    for _ in range(repeats):
        tic = time.perf_counter()
        fn()
        times.append(time.perf_counter() - tic)
    return statistics.median(times)


def environment():
    import scipy
    cpu = platform.processor() or platform.machine()
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "cpu": cpu, "cpus": os.cpu_count(), "platform": platform.platform()}


# ----------------------------------------------------------------------------- vehicle models
def bench_derivatives(repeats):
    cfg = load_vehicle_preset("mid_size_sedan")
    env, u = Environment(), ControlInput(steer_front=0.02)
    out = {}
    for name in MODELS:
        model = create("vehicle_model", name, cfg)
        s = model.initial_state(speed=20.0)
        n = 2000
        t = median_time(lambda: [model.derivatives(0.0, s, u, env) for _ in range(n)], repeats)
        out[name] = {"states": len(s), "derivative_us": 1e6 * t / n}
    return out


def bench_simulation(repeats):
    out = {}
    for name in MODELS:
        def run():
            sim = Simulator.from_scenario(Scenario(name="b", model=name, maneuver="iso_double_lane_change",
                                                   duration=5.0))
            run.result = sim.run()
            run.sim = sim
        t = median_time(run, repeats)
        steps = len(run.result["t"]) - 1
        out[name] = {"simulated_s": float(run.sim.t), "wall_s": t, "real_time_factor": run.sim.t / t,
                     "control_steps_per_s": steps / t, "dt_model": run.sim.dt_model}
    return out


def bench_memory():
    out = {}
    for label, kwargs in {"iso_dlc_double_track_8s": dict(model="double_track", maneuver="iso_double_lane_change"),
                          "straight_bicycle_60s": dict(model="bicycle_nonlinear", maneuver="straight",
                                                       maneuver_params={"length": 2000, "speed_kmh": 100},
                                                       duration=60.0)}.items():
        tracemalloc.start()
        sim = Simulator.from_scenario(Scenario(name=label, **kwargs))
        result = sim.run()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        out[label] = {"simulated_s": float(sim.t), "samples": len(result["t"]), "peak_mib": peak / 2 ** 20}
    return out


# ----------------------------------------------------------------------------- planner
def bench_planner(repeats):
    from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
    from vdsim.geometry import ReferenceLine
    from vdsim.planning import create_planner
    from vdsim.planning.simulation import constant_velocity_object

    road = ReferenceLine.straight(600.0)
    out = {}
    cases = {"free_road": [], "two_obstacles": [(1, 40.0, 0.0, 8.0), (2, 70.0, 3.5, 12.0)],
             "ten_obstacles": [(i, 20.0 + 15 * i, 3.5 * ((i % 3) - 1), 5.0 + i) for i in range(10)]}
    for config in ("default", "comfort", "sporty"):
        for case, obstacles in cases.items():
            planner = create_planner(config)
            planner.reset(None)
            ego = EgoState(vx=15.0)
            beh = BehaviorCommand(reference_line=road, target_speed=15.0, d_min=-5.25, d_max=5.25,
                                  modes=[LongitudinalMode("velocity", {"v_ref": 15.0})])
            pred = Prediction(t0=0.0, objects=[constant_velocity_object(i, x, y, 0.0, v) for i, x, y, v in obstacles])
            planner.plan_cycle(0.0, ego, beh, pred)   # warm-up (imports, caches)
            times, n_cand, n_checked = [], 0, 0
            for _ in range(repeats * 5):
                planner.reset(None)
                tic = time.perf_counter()
                _, dbg = planner.plan_cycle(0.0, ego, beh, pred)
                times.append(time.perf_counter() - tic)
                n_cand, n_checked = dbg.n_candidates, dbg.n_checked
            out[f"{config}/{case}"] = {"cycle_ms_median": 1e3 * statistics.median(times),
                                       "cycle_ms_p95": 1e3 * float(np.percentile(times, 95)),
                                       "candidates": int(n_cand), "checked": int(n_checked)}
    return out


def bench_scaling(repeats):
    # planner cycle time against the number of candidates (lateral end-time and offset grid)
    from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
    from vdsim.geometry import ReferenceLine
    from vdsim.planning import create_planner

    road = ReferenceLine.straight(600.0)
    out = []
    for d_step in (1.0, 0.5, 0.25, 0.125):
        planner = create_planner("default", **{"sampling.lat_d_step": d_step})
        planner.reset(None)
        beh = BehaviorCommand(reference_line=road, target_speed=15.0, modes=[LongitudinalMode("velocity",
                                                                                               {"v_ref": 15.0})])
        planner.plan_cycle(0.0, EgoState(vx=15.0), beh, Prediction())
        times, n = [], 0
        for _ in range(repeats * 3):
            planner.reset(None)
            tic = time.perf_counter()
            _, dbg = planner.plan_cycle(0.0, EgoState(vx=15.0), beh, Prediction())
            times.append(time.perf_counter() - tic)
            n = dbg.n_candidates
        out.append({"lat_d_step": d_step, "candidates": int(n), "cycle_ms_median": 1e3 * statistics.median(times)})
    return out


# ----------------------------------------------------------------------------- API
def bench_api(repeats):
    try:
        from fastapi.testclient import TestClient

        from vdsim.service.app import create_app
    except ImportError:
        return {"skipped": "fastapi not installed (pip install -e .[api])"}
    client = TestClient(create_app(api_key=""))
    calls = {
        "GET /health": lambda: client.get("/health"),
        "GET /vehicle/mid_size_sedan": lambda: client.get("/vehicle/mid_size_sedan"),
        "POST /predict (50 objects)": lambda: client.post("/predict", json={"objects": [
            {"id": i, "x": i, "v": 10.0} for i in range(50)]}),
        "POST /plan (1 cycle)": lambda: client.post("/plan", json={"target_offset": 3.5}),
        "POST /simulate (bicycle_linear, 5 s)": lambda: client.post("/simulate", json={
            "model": "bicycle_linear", "maneuver": "step_steer", "duration": 5.0}),
    }
    out = {}
    for label, call in calls.items():
        call()
        out[label] = {"latency_ms_median": 1e3 * median_time(call, repeats)}
    return out


# ----------------------------------------------------------------------------- profiling
def profile_hotspots(top=12):
    def sim():
        Simulator.from_scenario(Scenario(name="p", model="double_track", maneuver="iso_double_lane_change",
                                         duration=4.0)).run()

    def plan():
        from vdsim.framework.types import BehaviorCommand, EgoState, LongitudinalMode, Prediction
        from vdsim.geometry import ReferenceLine
        from vdsim.planning import create_planner
        road = ReferenceLine.straight(600.0)
        planner = create_planner("default")
        planner.reset(None)
        beh = BehaviorCommand(reference_line=road, target_speed=15.0, d_min=-5.25, d_max=5.25,
                              modes=[LongitudinalMode("velocity", {"v_ref": 15.0})])
        for k in range(30):
            planner.plan_cycle(0.1 * k, EgoState(t=0.1 * k, x=1.5 * k, vx=15.0), beh, Prediction(t0=0.1 * k))

    out = {}
    for label, fn in (("simulation_double_track", sim), ("planner_30_cycles", plan)):
        prof = cProfile.Profile()
        prof.enable()
        fn()
        prof.disable()
        stream = io.StringIO()
        stats = pstats.Stats(prof, stream=stream).sort_stats("tottime")
        rows = []
        for (file, line, func), (_, ncalls, tottime, cumtime, _) in sorted(
                stats.stats.items(), key=lambda kv: -kv[1][2])[:top]:
            rows.append({"function": f"{Path(file).name}:{line}:{func}", "calls": ncalls,
                         "tottime_s": round(tottime, 4), "cumtime_s": round(cumtime, 4)})
        out[label] = {"total_s": round(stats.total_tt, 3), "top": rows}
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--out", default=str(ROOT / "benchmarks" / "results" / "latest.json"))
    args = parser.parse_args(argv)
    repeats = 3 if args.quick else 7
    report = {"environment": environment(), "repeats": repeats}
    for key, fn in (("derivatives", lambda: bench_derivatives(repeats)),
                    ("simulation", lambda: bench_simulation(max(repeats // 2, 1))),
                    ("memory", bench_memory),
                    ("planner", lambda: bench_planner(repeats)),
                    ("planner_scaling", lambda: bench_scaling(repeats)),
                    ("api", lambda: bench_api(repeats))):
        tic = time.perf_counter()
        report[key] = fn()
        print(f"{key:<16} done in {time.perf_counter() - tic:6.1f} s", flush=True)
    if args.profile:
        report["hotspots"] = profile_hotspots()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
