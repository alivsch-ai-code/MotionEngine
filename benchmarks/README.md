# Benchmarks

Every number on this page is measured with `benchmarks/run_benchmarks.py` and stored with the hardware
and library versions in `benchmarks/results/latest.json`. Do not edit the tables by hand; rerun the
script and copy the values (rule 4 in `AGENTS.md`).

```bash
python benchmarks/run_benchmarks.py --profile    # ~3 min, writes benchmarks/results/latest.json
python benchmarks/run_benchmarks.py --quick      # fewer repetitions
```

Timings are medians of 7 repetitions (simulation: 3), wall clock, single thread.

**Environment of the tables below** (2026-11-08): Intel Xeon @ 2.10 GHz, 4 vCPUs, Linux 6.18,
Python 3.13.18, NumPy 2.5.4, SciPy 1.18.1. `2026-11-08-before-optimization.json` holds the same
measurement before the two optimizations of the review (planner debug snapshot, result storage).

## Vehicle models

One evaluation of `derivatives()` and a closed-loop ISO double lane change (5 s simulated,
`dt_control` = 10 ms, `dt_model` = 2 ms, RK4, Stanley + PI).

| Model | States | derivatives() | Wall time for 5 s | Real-time factor |
|---|---:|---:|---:|---:|
| `bicycle_kinematic` | 4 | 12 µs | 0.36 s | 13.8 |
| `bicycle_linear` | 6 | 19 µs | 0.37 s | 13.5 |
| `bicycle_nonlinear` | 6 | 54 µs | 0.77 s | 6.5 |
| `double_track` | 12 | 103 µs | 1.56 s | 3.2 |
| `multibody` | 24 | 141 µs | 2.08 s | 2.4 |

Hotspot (cProfile, double-track run): `DoubleTrackModel.derivatives` 32 % self time, Pacejka
`forces` 14 %; the remaining time is spread over NumPy calls on 4-element arrays, where the
per-call overhead dominates. Next step if needed: evaluate the four wheels with scalar math or Numba.

## Memory

Peak traced Python memory (`tracemalloc`) of a complete run including the result.

| Run | Samples | Before | After |
|---|---:|---:|---:|
| ISO double lane change, double track, 9.7 s | 967 | 6.0 MiB | 2.8 MiB |
| Straight, nonlinear single track, 60 s | 6 001 | 37.4 MiB | 17.3 MiB |

Change: `SimulationResult.append` stores scalars as Python floats instead of 0-d NumPy arrays.

## Planning latency

One Werling planning cycle on a straight road, ego at 15 m/s, configurations from `configs/planning`.

| Configuration / scene | Candidates | Before (median) | After (median) | After (p95) |
|---|---:|---:|---:|---:|
| default, free road | 18 000 | 12.0 ms | 7.2 ms | 8.5 ms |
| default, 2 obstacles | 18 000 | 12.8 ms | 8.4 ms | 9.8 ms |
| default, 10 obstacles | 18 000 | 14.6 ms | 9.5 ms | 11.9 ms |
| comfort, free road | 27 000 | 15.4 ms | 8.1 ms | 11.7 ms |
| comfort, 10 obstacles | 27 000 | 18.3 ms | 11.0 ms | 12.1 ms |
| sporty, free road | 16 200 | 12.1 ms | 7.0 ms | 9.6 ms |
| sporty, 10 obstacles | 16 200 | 17.9 ms | 9.3 ms | 11.0 ms |

Scaling with the lateral offset grid (`sampling.lat_d_step`, default configuration, free road):

| `lat_d_step` | Candidates | Before | After |
|---:|---:|---:|---:|
| 1.0 m | 8 400 | 11.8 ms | 6.5 ms |
| 0.5 m | 18 000 | 12.6 ms | 7.0 ms |
| 0.25 m | 34 800 | 19.4 ms | 8.8 ms |
| 0.125 m | 68 400 | 40.3 ms | 10.9 ms |

Change: the debug snapshot of every cycle (`WerlingPlanner._debug`) built a Python set of all ordered
candidates and called `np.setdiff1d`; it took about half of the cycle and grew with the candidate count.
A boolean mask gives the same snapshot. The lazy selection itself checks only 32 candidates here.

## REST service

`fastapi.testclient` in-process (no network), median of 7 calls.

| Request | Latency |
|---|---:|
| `GET /health` | 4.8 ms |
| `GET /vehicle/mid_size_sedan` | 6.1 ms |
| `POST /predict` (50 objects, 6 s horizon) | 10.4 ms |
| `POST /plan` (1 cycle) | 51.6 ms |
| `POST /simulate` (`bicycle_linear`, 5 s) | 336 ms |

`/plan` spends most of its time creating the planner from its configuration for every request
(one cycle itself takes ~7 ms); a per-configuration planner pool is the next optimization.

## AD stack (closed loop)

Wall time of the full stack (perception, prediction, behavior, Werling planner, controller, plant)
for the library scenarios with their own seeds, measured while checking the mission criteria:

| Scenario | Simulated | Wall | Mission |
|---|---:|---:|---|
| `einscherer` | 25.0 s | 13.9 s | passed |
| `notausweichen_hindernis` | 25.0 s | 11.5 s | passed |
| `einfaedeln_lkw` | 35.0 s | 41.7 s | passed |
| `innerorts_werling` | 66.7 s | 79.5 s | passed |
| `verkehrsdichte_20` | 60.0 s | 128.5 s | passed |
| `laengsparken_rueckwaerts` | 50.0 s | 42.4 s | **failed** (review finding F2) |
