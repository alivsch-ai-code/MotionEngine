# Geometrie – Referenzkurven und Frenet-Koordinaten – Beispiele

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

Verwendet: `vdsim.geometry`, `vdsim.geometry.reference_line`

Ausführen: `python examples/custom_nodes/python/my_behavior_planner.py`

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

Verwendet: `vdsim.geometry`, `vdsim.geometry.reference_line`

Ausführen: `python examples/custom_nodes/python/my_planner_node.py`

## [examples/planning/consistency.py](../../../examples/planning/consistency.py)

Zeitliche Konsistenz (Werling 2011, 3.2, Satz 3, Abb. 3.2).

Rückkehr zur Spurmitte aus 2 m Querablage mit zyklischer Neuplanung bei drei Planungsperioden:
Werling-Planer (absolutes Endzeitraster, Start auf der alten Trajektorie) gegen den naiven
Frenet-Planer (relatives Raster, Neuplanung vom Messzustand). Der konsistente Planer liefert
unabhängig von der Periode dieselbe Bewegung.
Bild: examples/planning/output/consistency.png

Verwendet: `vdsim.geometry`, `vdsim.geometry.reference_line`

Ausführen: `python examples/planning/consistency.py`

## [examples/planning/evasion.py](../../../examples/planning/evasion.py)

Ausweichen um ein liegengebliebenes Fahrzeug bei Gegenverkehr (Werling 2011, 3.5.4, 5.3).

Ein stehendes Fahrzeug blockiert die eigene Spur, auf der Gegenspur kommt ein Fahrzeug
entgegen. Der Werling-Planer optimiert Quer- und Längsbewegung kombiniert: er verzögert leicht,
lässt den Gegenverkehr passieren und weicht dann aus. Zum Vergleich der sequentielle Planer
(erst längs, dann quer, Werling 3.1).
Bild: examples/planning/output/evasion.png

Verwendet: `vdsim.geometry`, `vdsim.geometry.reference_line`

Ausführen: `python examples/planning/evasion.py`

## [examples/planning/following.py](../../../examples/planning/following.py)

Folgefahrt hinter einem bremsenden Vorderfahrzeug (Werling 2011, 3.5.2) mit Ablösestrategie.

Aktiv sind Geschwindigkeithalten (v_ref = 25 m/s) und Folgen (s_ref = s_v - [k0 + kv ṡ_v]).
Der Modus mit dem kleinsten Anfangsruck setzt sich durch (Schritt 6). Das Vorderfahrzeug fährt
mit 15 m/s, bremst ab t = 12 s mit -2 m/s² bis 5 m/s und beschleunigt ab t = 25 s wieder.
Bild: examples/planning/output/following.png

Verwendet: `vdsim.geometry`, `vdsim.geometry.reference_line`

Ausführen: `python examples/planning/following.py`

## [examples/planning/lane_change.py](../../../examples/planning/lane_change.py)

Spurwechsel mit dem Werling-Planer auf gerader und gekrümmter Straße (Werling 2011, 3.5.1).

Die Verhaltensebene legt die Referenzkurve auf die Mitte der Zielspur; der Planer führt den
Spurwechsel als Rückkehr auf d = 0 aus. Ausgabe: Draufsicht mit Kandidatensatz, d(t), Quer-
beschleunigung und Geschwindigkeit; Bild in examples/planning/output/lane_change.png.

Verwendet: `vdsim.geometry`, `vdsim.geometry.reference_line`

Ausführen: `python examples/planning/lane_change.py`

## [examples/planning/stopping.py](../../../examples/planning/stopping.py)

Anhalten an einer Haltelinie aus 50 km/h (Werling 2011, 3.5.2) mit Regimewechsel.

Unterhalb von v_s - Hysterese wechselt der Planer von d(t) mit Schwerpunkt auf d(s) mit
Hinterachsmitte (3.5.1, 3.5.4). Die Fahrzeugfront steht exakt auf der Haltelinie.
Bild: examples/planning/output/stopping.png

Verwendet: `vdsim.geometry`, `vdsim.geometry.reference_line`

Ausführen: `python examples/planning/stopping.py`
