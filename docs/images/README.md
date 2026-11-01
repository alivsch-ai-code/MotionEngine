# Visual Assets

Diagrams and result figures used in the README and documentation.

Everything except `banner.svg` is generated from the code:

```bash
python scripts/generate_readme_figures.py            # all figures
python scripts/generate_readme_figures.py diagrams   # SVG diagrams only
python scripts/generate_readme_figures.py results    # simulation results only
```

Do not edit the generated files by hand. Change the script and regenerate them.

## Diagrams

| File | Description |
|---|---|
| `banner.svg` | Hero banner (hand-written) |
| `architecture_overview.svg` | System architecture |
| `frenet_coordinates.svg` | Frenet frame with quintic candidates on a real reference line |
| `planning_pipeline.svg` | Planning cycle with candidate counts measured in the evasion scenario |
| `vehicle_dynamics.svg` | Single-track model and the implemented equations |

SVG text is stored as outlines, so the diagrams render the same with any installed font.

## Simulation results (`results/`)

| File | Scenario |
|---|---|
| `evasion.png` | Parked car with oncoming traffic, Werling and sequential planner |
| `consistency.png` | Result deviation across replanning periods |
| `controller_comparison.png` | Five tracking controllers on a double lane change |
| `highway_gust.png` | Side-wind gust at 30 m/s |
| `lane_change.png` | Lane change at 20 m/s |
| `following.png` | Following a braking lead vehicle |
| `stopping.png` | Stopping at a stop line |
| `slow_tracking.png` | Low-speed stop-and-go tracking, forward and reverse |

These figures are committed on purpose. The raw example outputs in `examples/*/output/` are git-ignored and do not exist on GitHub, so the README must not link to them.
