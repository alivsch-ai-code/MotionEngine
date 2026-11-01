"""Scenario engine: world component "world/scenario_engine" (layer ScenarioWorld).

Simulates the traffic participants of context.scenario (ScenarioInstance) synchronously with the
executor and produces the WorldState ground truth: objects, traffic-light states, collision
detection ego <-> actors (SAT with the ego outline from context.vehicle), off-road detection and
events (actor triggers, collisions, scheduled disturbances such as the lateral_impulse gust of
Werling 5.3.2, goal reached).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.parameters import param
from ..framework.knowledge import ComponentDoc
from ..framework.layers import ScenarioWorldBase
from ..framework.types import ObjectState, WorldState
from .actors import EGO_ID, TrafficSimulator
from .collision import collisions, rect_corners


@dataclass
class ScenarioEngineParams:
    max_dt: float = param(0.05, "s", "max. Teilschritt der Akteure", min=0.005, max=0.5)
    collision_margin: float = param(0.0, "m", "Sicherheitszuschlag Kollisionsprüfung", min=0.0, max=2.0)
    offroad_tolerance: float = param(0.3, "m", "Toleranz Fahrbahnrand", min=0.0, max=3.0)
    detect_offroad: bool = param(True, "", "Off-Road-Erkennung")
    ego_length: float = param(4.8, "m", "Ego-Länge (ohne Fahrzeugkonfiguration)", min=1.0, max=20.0)
    ego_width: float = param(1.85, "m", "Ego-Breite (ohne Fahrzeugkonfiguration)", min=0.5, max=3.0)
    ego_center_auto: bool = param(True, "", "Mittelpunkt aus Radstand und Schwerpunktlage")
    ego_center_offset: float = param(0.0, "m", "Mittelpunkt vor dem Schwerpunkt (manuell)", min=-3.0, max=3.0)
    goal_radius: float = param(3.0, "m", "Zielradius (Ereignis goal_reached)", min=0.1, max=50.0)


class ScenarioEngine(ScenarioWorldBase):
    NAME, VERSION = "scenario_engine", "1.0.0"
    LABEL = "Szenario-Engine"
    PARAMS = ScenarioEngineParams
    PERIOD = None
    DOC = ComponentDoc(
        summary="Simuliert die Verkehrsteilnehmer eines Szenarios und liefert die Ground Truth (WorldState).",
        purpose="Reproduzierbare Testszenarien für die gesamte Wirkkette: Akteure mit IDM/MOBIL, "
                "skriptbaren Triggern, Ampeln, Kollisions- und Off-Road-Erkennung sowie Störungsereignissen.",
        theory="Synchrones Update aller Akteure (Beschleunigungen aus dem Zustand zur Zeit t, dann Integration "
               "mit Teilschritten $h \\le h_{max}$). Kollisionen zwischen orientierten Rechtecken mit dem "
               "Trennachsensatz (SAT).",
        assumptions=["Ego-Umriss als Rechteck; Mittelpunkt in der Mitte zwischen den Achsen (Überhänge gleich)",
                     "Akteure reagieren auf das Ego über IDM, sofern es ihre Spur belegt"],
        limitations=["keine Fahrzeugdynamik der Akteure (kinematische Bewegung entlang der Spur)",
                     "Störungen wie die Seitenwindböe werden nur als Ereignis gemeldet, nicht selbst eingeprägt"],
        references=["treiber2000", "kesting2007", "werling2011", "gottschalk1996", "asam_openscenario"],
        concepts=["scenario_engine", "sat_collision", "idm", "mobil"],
        validation=["tests/world/test_world_engine.py", "tests/world/test_world_actors.py"],
        extension_points=["neue Szenariotypen über @scenario_type in vdsim.world.library",
                          "neue Akteurtypen als Unterklasse von vdsim.world.actors.Actor"],
    )

    def reset(self, context):
        super().reset(context)
        from .scenario import ScenarioInstance, build_scenario
        scen = getattr(context, "scenario", None)
        if scen is None:
            raise ValueError("world/scenario_engine needs context.scenario (ScenarioInstance or spec)")
        if not isinstance(scen, ScenarioInstance):
            scen = build_scenario(scen, seed=getattr(context, "seed", None))
            context.scenario = scen
        if getattr(context, "road", None) is None:
            context.road = scen.road
        self.scenario = scen
        self.road = scen.road
        p = self.params
        veh = getattr(getattr(context, "vehicle", None), "vehicle", None)
        if veh is not None:
            self.ego_length, self.ego_width = float(veh.length), float(veh.width)
            l_f, l_r = float(veh.cg_to_front), float(veh.wheelbase - veh.cg_to_front)
            self.center_offset = 0.5 * (l_f - l_r) if p.ego_center_auto else p.ego_center_offset
        else:
            self.ego_length, self.ego_width = p.ego_length, p.ego_width
            self.center_offset = p.ego_center_offset
        self.sim = TrafficSimulator(self.road, scen.fresh_actors(), p.max_dt, self.ego_length, self.ego_width)
        self.t_last = None
        self.was_colliding = set()
        self.was_offroad = False
        self.goal_reached = False
        self.pending = [dict(d) for d in scen.disturbances]
        self.events_log = []
        self._ego_hint = None

    # ------------------------------------------------------------------ helpers
    def ego_object(self, ego):
        if ego is None:
            e = self.scenario.ego_initial
            x, y, psi, v = e["x"], e["y"], e["psi"], e.get("v", 0.0)
            ax = 0.0
        else:
            x, y, psi, v, ax = ego.x, ego.y, ego.psi, float(np.hypot(ego.vx, ego.vy)), ego.ax
        cx, cy = x + self.center_offset * np.cos(psi), y + self.center_offset * np.sin(psi)
        loc = self.road.lane_at(cx, cy, psi, margin=0.5 * self.ego_width,
                                prefer=self.scenario.mission.get("route", ()))
        return ObjectState(id=EGO_ID, type="car", x=float(cx), y=float(cy), psi=float(psi), v=v, a=float(ax),
                           length=self.ego_length, width=self.ego_width, lane_id=loc.lane_id if loc else None,
                           s=loc.s if loc else None, d=loc.d if loc else None)

    def _disturbances(self, t, ego_obj):
        events, active = [], []
        for d in self.pending:
            t0 = d.get("t")
            if t0 is None and "trigger" in d:
                trig = d["trigger"]
                if trig.get("kind") == "ego_x" and ego_obj.x >= trig.get("value", 0.0):
                    d["t"] = t0 = t
            if t0 is None:
                continue
            if not d.get("_fired") and t >= t0 - 1e-9:
                d["_fired"] = True
                events.append({k: v for k, v in d.items() if not k.startswith("_")})
            if t0 - 1e-9 <= t < t0 + d.get("duration", 0.0):
                active.append({k: v for k, v in d.items() if not k.startswith("_")})
        return events, active

    # ------------------------------------------------------------------ step
    def step(self, t, inputs):
        ego = inputs.get("ego")
        ego_obj = self.ego_object(ego)
        events = []
        if self.t_last is not None and t > self.t_last + 1e-12:
            events += self.sim.step(self.t_last, t - self.t_last, ego_obj)
        else:
            self.sim.ego = ego_obj
        self.t_last = t
        visible = self.sim.object_states()
        everything = self.sim.object_states(include_hidden=True)
        p = self.params
        hits = collisions(ego_obj.x, ego_obj.y, ego_obj.psi, self.ego_length, self.ego_width, everything,
                          p.collision_margin) if ego is not None else []
        for h in hits:
            if h not in self.was_colliding:
                events.append({"t": t, "type": "collision", "actor": h})
        self.was_colliding = set(hits)
        off = False
        if p.detect_offroad and ego is not None:
            corners = rect_corners(ego_obj.x, ego_obj.y, ego_obj.psi, self.ego_length, self.ego_width)[0]
            off = not bool(np.all(self.road.drivable(corners[:, 0], corners[:, 1], p.offroad_tolerance)))
            if off and not self.was_offroad:
                events.append({"t": t, "type": "off_road"})
        self.was_offroad = off
        dist_events, active = self._disturbances(t, ego_obj)
        events += dist_events
        goal = self.scenario.mission.get("goal")
        if goal and not self.goal_reached and ego is not None and self._goal_check(goal, ego_obj):
            self.goal_reached = True
            events.append({"t": t, "type": "goal_reached"})
        self.events_log += events
        info = {"ego_lane": ego_obj.lane_id, "ego_s": ego_obj.s, "ego_d": ego_obj.d,
                "hidden": [o.id for o in everything if o.id not in {v.id for v in visible}],
                "light_phases": self.road.light_phases(t), "active_disturbances": active,
                "goal_reached": self.goal_reached, "scenario": self.scenario.name}
        self.signals.update({"n_objects": float(len(visible)), "collision": float(bool(hits)), "off_road": float(off)})
        return {"world": WorldState(t=t, objects=visible, road=self.road, traffic_lights=self.road.light_states(t),
                                    collision=bool(hits), collision_with=hits[0] if hits else None, off_road=off,
                                    events=events, info=info)}

    def _goal_check(self, goal, ego_obj):
        if "x" in goal and "y" in goal:
            return np.hypot(ego_obj.x - goal["x"], ego_obj.y - goal["y"]) <= goal.get("radius", self.params.goal_radius)
        if "lane" in goal and goal["lane"] in self.road.lanes:
            lane = self.road.lanes[goal["lane"]]
            s, d = lane.center.project(ego_obj.x, ego_obj.y)
            return abs(d) <= 0.5 * lane.width and abs(s - goal.get("s", 0.0)) <= goal.get("radius",
                                                                                         self.params.goal_radius)
        return False
