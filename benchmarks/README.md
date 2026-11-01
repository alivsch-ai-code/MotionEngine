# Benchmarks

This directory contains performance benchmarks for MotionEngine.

## Running Benchmarks

```bash
python -m pytest benchmarks/ -v
```

## Benchmark Areas

### Planning Latency

Measures the time to complete one planning cycle (sampling → evaluation → selection):

| Scenario | Candidates | Planning Time | Hardware |
|---|---|---|---|
| Highway (3 lanes) | ~5000 | TBD | — |
| Urban (obstacles) | ~3000 | TBD | — |

### Simulation Throughput

Measures simulation steps per second for each vehicle model:

| Model | States | Steps/sec | Real-time Factor |
|---|---|---|---|
| Kinematic bicycle | 4 | TBD | — |
| Linear bicycle | 6 | TBD | — |
| Double-track | 12 | TBD | — |
| Multibody | 24 | TBD | — |

### Memory Usage

Measures peak memory during a full scenario simulation:

| Scenario | Duration | Peak Memory |
|---|---|---|
| ISO DLC 80 km/h | ~8s | TBD |
| Highway ACC 60s | ~60s | TBD |

## Contributing Benchmarks

When adding benchmarks, include:
1. Hardware specification (CPU, RAM)
2. Python version
3. NumPy/SciPy version
4. Number of iterations for statistical significance
