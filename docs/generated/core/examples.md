# Kern – Konventionen, Parameter, Schnittstellen, Registry – Beispiele

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · **Beispiele** · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## [examples/custom_nodes/python/my_behavior_planner.py](../../../examples/custom_nodes/python/my_behavior_planner.py)

Custom node (Python): simple behavior planner with the ports of BehaviorPlannerBase.

Graph spec: "python:examples/custom_nodes/python/my_behavior_planner.py:SimpleBehaviorPlanner"

    inputs:  ego, objects (ObjectList), prediction, world, trajectory (feedback, optional)
    output:  behavior (BehaviorCommand)

Lane keeping on a straight lane (reference line along x at y = lane_y) with
    velocity mode   v_ref = target speed
    following mode  if an object is ahead in the lane closer than the detection range:
                    lead_id, standstill gap k0 and time gap kv (Werling Tab. 3.1),
                    target speed limited to the speed of the lead vehicle
The corridor d_min/d_max is the lane minus half the vehicle width.

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/custom_nodes/python/my_behavior_planner.py`

## [examples/custom_nodes/python/my_collision_checker.py](../../../examples/custom_nodes/python/my_collision_checker.py)

Example: own collision checker for the Werling trajectory planner (kind="collision_checker").

Exact rectangle overlap test with the separating axis theorem (SAT) instead of the circle
approximation. Usage:

    "collision": {"checker": "python:examples/custom_nodes/python/my_collision_checker.py:BoxCollisionChecker"}

The checker receives once per cycle the prediction, the common time grid of the check horizon
and the ego geometry (prepare) and then evaluates batches of candidates (check). It must return
the time of the first collision so that the planner can select the fallback trajectory.

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/custom_nodes/python/my_collision_checker.py`

## [examples/custom_nodes/python/my_controller_node.py](../../../examples/custom_nodes/python/my_controller_node.py)

Custom node (Python): Pure-Pursuit tracking controller with the ports of TrackingControllerBase.

Graph spec: "python:examples/custom_nodes/python/my_controller_node.py:PurePursuitController"

    inputs:  ego (EgoState), trajectory (PlannedTrajectory)
    outputs: command (ControlCommand: steer_angle + accel), status (ControllerStatus)

The same algorithm is implemented natively in ../rust/my_controller_node and
../cpp/my_controller_node; tests compare the three implementations.

Algorithm (rear-axle based pure pursuit, Coulter 1992):
    lookahead  L_d = L_d0 + k_v |v_x|
    target     first trajectory point after the nearest one with distance >= L_d from the rear axle
    steering   delta = atan2(2 l sin(alpha), L_d),  alpha = angle to the target in the vehicle frame
    speed      a = a_ref(t) + k_p (v_ref(t) - v_x)

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/custom_nodes/python/my_controller_node.py`

## [examples/custom_nodes/python/my_cost_function.py](../../../examples/custom_nodes/python/my_cost_function.py)

Example: own cost term for the Werling trajectory planner (kind="cost_term").

Usage in a planner configuration (configs/planning/*.json or API):

    "cost": {"custom": [{"spec": "python:examples/custom_nodes/python/my_cost_function.py:KeepRightCost",
                         "params": {"weight": 2.0}}]}

A separable term implements lateral() and/or longitudinal() and is evaluated on the candidate
sets (cheap, enters the cost sorting). A term with SCOPE = "combined" implements combined()
and is evaluated in the re-ranking window on world trajectories. Only the consistent Werling
terms keep the Bellman guarantee; an additional term shifts the optimum (see theory.md).

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/custom_nodes/python/my_cost_function.py`

## [examples/custom_nodes/python/my_planner_node.py](../../../examples/custom_nodes/python/my_planner_node.py)

Custom node (Python): simple lane-keeping trajectory planner with the ports of TrajectoryPlannerBase.

Graph spec: "python:examples/custom_nodes/python/my_planner_node.py:LaneKeepingPlanner"

    inputs:  ego (EgoState), behavior (BehaviorCommand), prediction (Prediction),
             status (ControllerStatus, feedback port: value of the previous step)
    outputs: trajectory (PlannedTrajectory, absolute time), debug (PlannerDebug)

One candidate only (no optimization): the lateral offset d moves from the current value to
d_ref with a quintic smoothstep (zero lateral velocity/acceleration at both ends) and the
speed approaches the target speed exponentially. The trajectory follows the reference line
of the behavior command (straight line along the ego heading if there is none).

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/custom_nodes/python/my_planner_node.py`

## [examples/custom_nodes/python/my_sensor_fusion_module.py](../../../examples/custom_nodes/python/my_sensor_fusion_module.py)

Custom node (Python): fusion of two noisy object lists with the ports of PerceptionBase.

Graph spec: "python:examples/custom_nodes/python/my_sensor_fusion_module.py:TwoSensorFusion"

    inputs:  world (WorldState: ground truth objects), ego (EgoState)
    outputs: objects (ObjectList, fused + smoothed), ego_estimate (EgoState)

Two virtual sensors measure every ground-truth object with different accuracy
(radar: precise in x and speed, camera: precise in y). The measurements are fused per
object with inverse-variance weighting and then smoothed over time with an alpha filter.
Noise comes from context.rng(name) only, so runs are reproducible.

    fused  z = (z_r / s_r^2 + z_c / s_c^2) / (1 / s_r^2 + 1 / s_c^2)
    smooth x_k = x_{k-1} + alpha (z_k - x_{k-1})

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/custom_nodes/python/my_sensor_fusion_module.py`

## [examples/custom_nodes/python/my_vehicle_model.py](../../../examples/custom_nodes/python/my_vehicle_model.py)

Custom node (Python): kinematic single-track vehicle with the ports of VehiclePlantBase.

Graph spec: "python:examples/custom_nodes/python/my_vehicle_model.py:KinematicBicyclePlant"

    input:  control (ControlInput: steer_front, drive/brake torque per wheel)
    output: ego (EgoState at the CoG)
    no direct feedthrough: output(t) from the state, update(t, inputs, dt) integrates

The file also contains CommandToControl, a simplified stand-in for the layers Vehicle
Dynamics + Actuators (ControlCommand -> ControlInput), so the example chain can be closed
with Python custom nodes only.

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/custom_nodes/python/my_vehicle_model.py`

## [examples/stabilization/controller_comparison.py](../../../examples/stabilization/controller_comparison.py)

Comparison of all tracking controllers on the same trajectory (double lane change 15 -> 20 m/s, initial
lateral offset 0.3 m) on the DESM plant and on the double-track model (model error).

Output: examples/stabilization/output/controller_comparison.csv and controller_comparison.png

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/stabilization/controller_comparison.py`

## [examples/stabilization/highway_gust.py](../../../examples/stabilization/highway_gust.py)

Fast driving (30 m/s) with an evasive maneuver and a strong side-wind gust: bi-level stabilization.

Low-level: exact I/O linearization (Satz 8) with speed dependent look-ahead lambda(zeta, v) (4.70) and the
dynamic reference transformation (4.71)-(4.74). High-level: the elliptic error-rate measure (4.5.1)
triggers a re-initialization, the planner (stand-in: replan_from_prediction) restarts the trajectory at the
predicted vehicle state (4.5.2) and merges back into the lane. Compared: with and without re-initialization.

Output: examples/stabilization/output/highway_gust.png

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/stabilization/highway_gust.py`

## [examples/stabilization/reverse_maneuver.py](../../../examples/stabilization/reverse_maneuver.py)

Reverse driving with the bi-level controller: forward arc, stop, reverse into a parking position.

The planner is replaced by two stored rear-axle trajectories; at standstill the direction varsigma of the
active trajectory switches from +1 to -1, and the werling_bilevel controller changes from the controller
without orientation stabilization (Satz 6) to the one with orientation stabilization (Satz 4) - without a
steering angle jump. Plant: werling_kesm (drives backwards).

Output: examples/stabilization/output/reverse_maneuver.png

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/stabilization/reverse_maneuver.py`

## [examples/stabilization/slow_comparison.py](../../../examples/stabilization/slow_comparison.py)

Werling 5.2: comparison of the low-level controllers on a stored slow stop-and-go trajectory.

(a) forward with orientation stabilization (Satz 4), (b) reverse with orientation stabilization,
(c) forward without orientation stabilization (Satz 6, geometric center). The trajectory starts with
v_d = 0 directly at the rear axle of the waiting vehicle (no initial tracking error), stops for one
second every few meters and changes its curvature permanently. Plant: werling_desm (forward) /
werling_kesm (reverse), full chain split range -> actuator -> plant.

Output: examples/stabilization/output/slow_comparison_signals.png, slow_comparison_path.png

Verwendet: `vdsim.core.parameters`

Ausführen: `python examples/stabilization/slow_comparison.py`

## [run_ad.py](../../../run_ad.py)

Command line for the automated-driving platform (Werling trajectory planning and stabilization).

python run_ad.py --list                          scenarios and components
python run_ad.py highway_cut_in                  run a scenario with the default stack, print KPIs
python run_ad.py highway_cut_in --controller tracking_controller/stanley_pi --save out/run1
python run_ad.py highway_cut_in --compare-controllers werling_bilevel stanley_pi lqr_ff_fb
python run_ad.py highway_cut_in --sweep stack.planner.params.cost.k_jerk=0.5,1,2
python run_ad.py highway_cut_in --monte-carlo 20 --vary scenario_params.lead_speed=normal:20:2
python run_ad.py highway_cut_in --benchmark 3

Verwendet: `vdsim.core.logging_setup`

Ausführen: `python run_ad.py`

## [run_scenario.py](../../../run_scenario.py)

Command line: run scenarios, print KPIs, export results and reports.

python run_scenario.py --list
python run_scenario.py iso_doppelspurwechsel_80 --plot
python run_scenario.py kreisfahrt_r40 bremsen_100_abs --report bericht.pdf --summary bericht.md
python run_scenario.py configs/scenarios/slalom_60.json --csv slalom.csv
python run_scenario.py --all

Verwendet: `vdsim.core.logging_setup`

Ausführen: `python run_scenario.py`
