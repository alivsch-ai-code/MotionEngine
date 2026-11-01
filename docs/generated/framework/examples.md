# Komponenten-Framework der AD-Plattform – Beispiele

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

Verwendet: `vdsim.framework.knowledge`, `vdsim.framework.layers`, `vdsim.framework.types`

Ausführen: `python examples/custom_nodes/python/my_behavior_planner.py`

## [examples/custom_nodes/python/my_collision_checker.py](../../../examples/custom_nodes/python/my_collision_checker.py)

Example: own collision checker for the Werling trajectory planner (kind="collision_checker").

Exact rectangle overlap test with the separating axis theorem (SAT) instead of the circle
approximation. Usage:

    "collision": {"checker": "python:examples/custom_nodes/python/my_collision_checker.py:BoxCollisionChecker"}

The checker receives once per cycle the prediction, the common time grid of the check horizon
and the ego geometry (prepare) and then evaluates batches of candidates (check). It must return
the time of the first collision so that the planner can select the fallback trajectory.

Verwendet: `vdsim.framework.knowledge`

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

Verwendet: `vdsim.framework.knowledge`, `vdsim.framework.layers`, `vdsim.framework.types`

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

Verwendet: `vdsim.framework.knowledge`

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

Verwendet: `vdsim.framework.knowledge`, `vdsim.framework.layers`, `vdsim.framework.types`

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

Verwendet: `vdsim.framework.knowledge`, `vdsim.framework.layers`, `vdsim.framework.types`

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

Verwendet: `vdsim.framework.component`, `vdsim.framework.knowledge`, `vdsim.framework.layers`, `vdsim.framework.types`

Ausführen: `python examples/custom_nodes/python/my_vehicle_model.py`

## [examples/planning/consistency.py](../../../examples/planning/consistency.py)

Zeitliche Konsistenz (Werling 2011, 3.2, Satz 3, Abb. 3.2).

Rückkehr zur Spurmitte aus 2 m Querablage mit zyklischer Neuplanung bei drei Planungsperioden:
Werling-Planer (absolutes Endzeitraster, Start auf der alten Trajektorie) gegen den naiven
Frenet-Planer (relatives Raster, Neuplanung vom Messzustand). Der konsistente Planer liefert
unabhängig von der Periode dieselbe Bewegung.
Bild: examples/planning/output/consistency.png

Verwendet: `vdsim.framework.plugins`, `vdsim.framework.types`

Ausführen: `python examples/planning/consistency.py`

## [examples/planning/evasion.py](../../../examples/planning/evasion.py)

Ausweichen um ein liegengebliebenes Fahrzeug bei Gegenverkehr (Werling 2011, 3.5.4, 5.3).

Ein stehendes Fahrzeug blockiert die eigene Spur, auf der Gegenspur kommt ein Fahrzeug
entgegen. Der Werling-Planer optimiert Quer- und Längsbewegung kombiniert: er verzögert leicht,
lässt den Gegenverkehr passieren und weicht dann aus. Zum Vergleich der sequentielle Planer
(erst längs, dann quer, Werling 3.1).
Bild: examples/planning/output/evasion.png

Verwendet: `vdsim.framework.plugins`, `vdsim.framework.types`

Ausführen: `python examples/planning/evasion.py`

## [examples/planning/following.py](../../../examples/planning/following.py)

Folgefahrt hinter einem bremsenden Vorderfahrzeug (Werling 2011, 3.5.2) mit Ablösestrategie.

Aktiv sind Geschwindigkeithalten (v_ref = 25 m/s) und Folgen (s_ref = s_v - [k0 + kv ṡ_v]).
Der Modus mit dem kleinsten Anfangsruck setzt sich durch (Schritt 6). Das Vorderfahrzeug fährt
mit 15 m/s, bremst ab t = 12 s mit -2 m/s² bis 5 m/s und beschleunigt ab t = 25 s wieder.
Bild: examples/planning/output/following.png

Verwendet: `vdsim.framework.types`

Ausführen: `python examples/planning/following.py`

## [examples/planning/lane_change.py](../../../examples/planning/lane_change.py)

Spurwechsel mit dem Werling-Planer auf gerader und gekrümmter Straße (Werling 2011, 3.5.1).

Die Verhaltensebene legt die Referenzkurve auf die Mitte der Zielspur; der Planer führt den
Spurwechsel als Rückkehr auf d = 0 aus. Ausgabe: Draufsicht mit Kandidatensatz, d(t), Quer-
beschleunigung und Geschwindigkeit; Bild in examples/planning/output/lane_change.png.

Verwendet: `vdsim.framework.types`

Ausführen: `python examples/planning/lane_change.py`

## [examples/planning/stopping.py](../../../examples/planning/stopping.py)

Anhalten an einer Haltelinie aus 50 km/h (Werling 2011, 3.5.2) mit Regimewechsel.

Unterhalb von v_s - Hysterese wechselt der Planer von d(t) mit Schwerpunkt auf d(s) mit
Hinterachsmitte (3.5.1, 3.5.4). Die Fahrzeugfront steht exakt auf der Haltelinie.
Bild: examples/planning/output/stopping.png

Verwendet: `vdsim.framework.types`

Ausführen: `python examples/planning/stopping.py`
