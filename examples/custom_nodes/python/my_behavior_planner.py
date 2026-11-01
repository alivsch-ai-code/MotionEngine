"""Custom node (Python): simple behavior planner with the ports of BehaviorPlannerBase.

Graph spec: "python:examples/custom_nodes/python/my_behavior_planner.py:SimpleBehaviorPlanner"

    inputs:  ego, objects (ObjectList), prediction, world, trajectory (feedback, optional)
    output:  behavior (BehaviorCommand)

Lane keeping on a straight lane (reference line along x at y = lane_y) with
    velocity mode   v_ref = target speed
    following mode  if an object is ahead in the lane closer than the detection range:
                    lead_id, standstill gap k0 and time gap kv (Werling Tab. 3.1),
                    target speed limited to the speed of the lead vehicle
The corridor d_min/d_max is the lane minus half the vehicle width.
"""

from dataclasses import dataclass

from vdsim.core.parameters import param
from vdsim.framework.knowledge import ComponentDoc
from vdsim.framework.layers import BehaviorPlannerBase
from vdsim.framework.types import BehaviorCommand, LongitudinalMode
from vdsim.geometry import ReferenceLine


@dataclass
class SimpleBehaviorParams:
    target_speed: float = param(15.0, "m/s", "Wunschgeschwindigkeit", min=0.0)
    lane_y: float = param(0.0, "m", "Spurmitte y")
    lane_width: float = param(3.5, "m", "Spurbreite", min=2.0)
    vehicle_width: float = param(1.8, "m", "Fahrzeugbreite", min=1.0)
    detection_range: float = param(80.0, "m", "Folgefahrt ab Abstand", min=5.0)
    k0: float = param(5.0, "m", "Mindestabstand", min=0.0)
    kv: float = param(1.5, "s", "Zeitlücke", min=0.0)


class SimpleBehaviorPlanner(BehaviorPlannerBase):
    NAME = "my_simple_behavior"
    VERSION = "1.0.0"
    LABEL = "Einfache Verhaltensplanung (Beispiel, Python)"
    PARAMS = SimpleBehaviorParams
    DOC = ComponentDoc(summary="Spurhalten mit Wunschgeschwindigkeit oder Folgefahrt auf geradem Fahrstreifen.",
                       purpose="Beispiel für einen Custom Node mit den Ports der Ebene Behavior Planning.",
                       references=["werling2011"])

    def reset(self, context):
        super().reset(context)
        p = self.params
        self.line = ReferenceLine.straight(5000.0, -1000.0, p.lane_y, 0.0, ds=1.0, name="lane")
        self.lead_id = None

    def step(self, t, inputs):
        ego, objects = inputs["ego"], inputs["objects"]
        if ego is None:
            return {}
        p = self.params
        lead = None
        for o in getattr(objects, "objects", []) or []:
            gap = o.x - ego.x
            if 0.0 < gap < p.detection_range and abs(o.y - p.lane_y) < p.lane_width / 2:
                if lead is None or gap < lead.x - ego.x:
                    lead = o
        modes = [LongitudinalMode("velocity", {"v_ref": p.target_speed})]
        speed = p.target_speed
        if lead is not None:
            modes.append(LongitudinalMode("following", {"lead_id": lead.id, "k0": p.k0, "kv": p.kv}))
            speed = min(speed, max(lead.v, 0.0))
        self.lead_id = None if lead is None else lead.id
        half = p.lane_width / 2 - p.vehicle_width / 2
        self.signals.update(target_speed=speed, following=float(lead is not None))
        return {"behavior": BehaviorCommand(t=t, reference_line=self.line, lane_id="lane", target_speed=speed,
                                            modes=modes, d_ref=0.0, d_min=-half, d_max=half, direction=1,
                                            maneuver="lane_keeping" if lead is None else "following")}
