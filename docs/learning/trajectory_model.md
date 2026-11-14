# Learned trajectory planner

`vdsim.learning.trajectory` trains a network that finds the trajectory of a planning cycle. The network
proposes; the Werling planner verifies. It is available as a Python API (`train_planner`,
`LearnedPlanner`), through the REST service (`POST /models/train` with `kind: "trajectory_planner"`,
`POST /models/{id}/drive`, `model` in `POST /plan`), on the web app's **Neural models** page and as the
stack component `trajectory_planner/learned`.

## 1. Idea

The Werling planner (teacher) builds a set of candidate trajectories in every cycle and selects the
cheapest valid one. A candidate is defined by four numbers:

| Number | Meaning |
|---|---|
| δ | end offset of the lateral motion relative to the target lane, m |
| τ_lat | end time of the lateral motion, s |
| ν | end speed relative to the target speed, m/s |
| τ_lon | end time of the longitudinal motion, s |

The network learns the teacher's choice from demonstrations (imitation learning):

```
situation  ->  MLP (tanh, NumPy)  ->  (δ, τ_lat, ν, τ_lon)
```

A plain regression of this choice is not safe to drive: where the teacher swerves left in one situation
and right in a similar one, the average points at the obstacle. So the proposal is never driven
directly. `LearnedPlanner` uses it as the center of a small search:

1. It builds only the candidates next to the proposal, on the teacher's grid: 7 end offsets, 5 lateral
   end times, 7 end speeds, 5 longitudinal end times. The lane center and the choice of the previous
   cycle are always included.
2. It checks them with the teacher's restrictions and collision check and takes the cheapest valid one.
3. It hands the cycle to the complete search of the teacher if
   - no candidate of the local set is valid, or
   - the best one lies on the border of the local set although the grid continues there (the optimum
     is probably outside).

Every trajectory that leaves the planner therefore passed the same checks as with the teacher alone.

## 2. Inputs

31 features, all relative to the target lane:

| Group | Features |
|---|---|
| Start state | d, ḋ, d̈, ṡ, s̈ |
| Task | target speed, corridor bounds d_min and d_max |
| Road | curvature at 0, 15, 30 and 60 m ahead |
| Objects | the 3 nearest: present, distance ahead, lateral offset, relative speed |
| Previous cycle | present, δ, remaining τ_lat, ν, remaining τ_lon |
| Grid | position of the start time on the two absolute end-time grids |

The previous choice is the most informative input. By Bellman's principle the best trajectory of a cycle
is usually the rest of the previous one (Werling 2011, 3.4.2). Without these inputs the end times could
not be learned (R² below 0 for the longitudinal targets); with them R² is 0.45 to 0.83.

## 3. Training data

`sample_plan_dataset` draws random situations and lets the teacher drive each for 1 to 8 cycles:

- road: straight, curve or S-curve, radius 90 to 400 m;
- one to three lanes; the vehicle starts on the target lane, on the neighbor lane (lane change) or
  anywhere in the corridor;
- speed 6 to 33 m/s, target speed within about ±4 m/s of it;
- 0 to 3 objects ahead, standing or moving, not closer than a braking distance at 4 m/s².

A cycle becomes a sample if the teacher found a valid trajectory inside the model's scope. One sample
takes about 25 ms on one core.

## 4. Scope

- Inside: fast driving (lateral motion over time), velocity mode, static and moving objects, lane
  offsets, curves.
- Outside (the teacher plans these cycles): slow driving with the d(s) mode, reverse driving, and the
  modes following, merging and stopping.

## 5. Results

Mid-size sedan, planner configuration `default`, hidden layers 96-96, 4 vCPU. Evaluation on held-out
situations (40 for the first two rows, 60 for the last): the guided planner and the teacher drive the same
situation for 10 cycles.

| Demonstrations | Training time | Cycles solved by the network¹ | Same trajectory as the teacher² | Cost in closed loop vs. teacher | Time per cycle (teacher) |
|---|---|---|---|---|---|
| 600 | 23 s | 96.1 % | 76 % | +5.1 % | 11.9 ms (13.9 ms) |
| 1500 | 48 s | 98.7 % | 74 % | +10 % | 10.9 ms (14.4 ms) |
| 4000 | 108 s | 99.0 % | 91 % | +7.1 % | 9.6 ms (13.6 ms) |

¹ Of the cycles that have a valid trajectory. ² First cycle of each situation, where both planners
start from the same state.

With 4000 demonstrations (60 situations, 600 cycles):

- 1.0 % of the cycles needed the complete search; 3.8 % had no valid trajectory at all, with either
  planner.
- In 93 % of the first cycles the cost is within 5 % of the teacher's; the mean cost ratio is 1.009.
- Cycles without a valid trajectory: 23, the same 23 as with the teacher alone. Collisions: 0 for both.
- In the stack (`einscherer`, 4 s): more than half of the cycles come from the network path and the
  minimum distance matches the teacher's within 1 m (tested).

What the numbers say:

- The network path almost always finds a valid trajectory, and in most cycles the teacher's.
- Where it differs, the trajectory is valid but a little more expensive: about 7 % more accumulated cost
  over a drive. Single first cycles can be far off (up to 4 times the teacher's cost in the evaluation)
  when the best trajectory lies outside the local set but not on its border.
- The gain in computing time is about 30 %. It is limited because the teacher is already lazy: it sorts
  the candidates by cost and checks only until it has enough valid ones.

## 6. Learning approaches

`train_planner(approach=...)` and the training form offer three approaches. Same budget (4000 demonstrations,
hidden layers 96-96), same 60 held-out situations:

| Approach | Idea | Cycles solved by the network | Same trajectory as the teacher | Cost within 5 % | Cost in closed loop | Training time |
|---|---|---|---|---|---|---|
| Regression | predict the four numbers of the teacher's choice | 99.0 % | 91 % | 93 % | +7.1 % | 113 s |
| Classification | end offset and end speed as classes of the teacher's grid, end times as numbers | 96.4 % | 82 % | 89 % | +9.3 % | 120 s |
| DAgger | regression; then the learned planner drives and the teacher labels the states it reaches (2 rounds); training on all data | 97.7 % | 91 % | 95 % | +7.0 % | 131 s |

- Regression is the default. It is the best or equal in every column.
- Classification avoids averaging two valid choices, but it needs more data per class: most demonstrations
  have the class "lane center, target speed", the others are rare.
- DAgger (Ross et al. 2011) brings no clear gain here. The local search and the fallback to the teacher
  already keep the learned planner close to the teacher's states, so the states it visits differ little
  from the demonstrations.

**Training situations** can be set (`situations`): speed range, largest number of objects, share of curves,
share of lane changes. Train on the situations the model will meet.

**Your own model:** any model that maps the 31 inputs to the 4 outputs can be connected as an ONNX file or an
HTTP endpoint (`POST /models/connect` with `kind: "trajectory_planner"`, or the Connect tab). It is compared
with the Werling planner on 20 situations when it is connected. Every proposal is verified by the planner,
so a poor model costs computing time, not safety.

## 7. Use

```python
from vdsim.learning import ModelStore, train_planner

net, meta = train_planner(n_samples=4000)
model = ModelStore().save({**meta, "name": "my planner"}, net.to_bytes())

from vdsim import api
result = api.run("einscherer", stack={"planner": {"component": "trajectory_planner/learned",
                                                  "params": {"model": model["id"]}}})
```

Each planner snapshot records where the trajectory came from (`info["source"]`: `network`, `teacher`,
`out_of_scope` or `infeasible`).

## 8. Limits

- The model imitates one planner configuration and one vehicle. Train again after changing cost weights,
  sampling grids or the vehicle.
- The cost difference is measured, not bounded. Use the teacher where the optimum matters more than the
  computing time.
- Training situations are synthetic. Situations far from them (dense traffic, very narrow corridors)
  fall back to the teacher more often.

## 9. References

- M. Werling: Ein neues Konzept für die Trajektoriengenerierung und -stabilisierung in zeitkritischen
  Verkehrsszenarien. KIT Scientific Publishing, 2011.
- M. Bojarski et al.: End to end learning for self-driving cars. arXiv:1604.07316, 2016.
- S. Ross, G. Gordon, D. Bagnell: A reduction of imitation learning and structured prediction to
  no-regret online learning. AISTATS, 2011.
- F. Codevilla, E. Santana, A. López, A. Gaidon: Exploring the limitations of behavior cloning for
  autonomous driving. ICCV, 2019.
