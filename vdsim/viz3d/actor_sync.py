"""Synchronisation von vdsim-Akteuren mit CARLA-Fahrzeugen/Fußgängern.

Jeder vdsim-Akteur (EgoState, ObjectState) wird auf ein CARLA-Actor abgebildet:
  - car/truck     → vehicle.* Blueprint (Tesla, Audi, Mercedes, Lkw)
  - pedestrian    → walker.pedestrian.*
  - cyclist       → vehicle.bh.crossbike
  - static        → static.prop.* oder vehicle.* mit angezogener Handbremse

Die Positionen werden jeden Tick per set_transform() gesetzt (kinematische
Steuerung, da die vdsim-Physik autoritativ ist).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..core.logging_setup import get_logger

log = get_logger("viz3d.actor_sync")

BLUEPRINTS = {
    "car": [
        "vehicle.tesla.model3",
        "vehicle.audi.a2",
        "vehicle.bmw.grandtourer",
        "vehicle.mercedes.coupe_2020",
        "vehicle.dodge.charger_2020",
    ],
    "truck": [
        "vehicle.carlamotors.firetruck",
        "vehicle.tesla.cybertruck",
    ],
    "pedestrian": [
        "walker.pedestrian.0001",
        "walker.pedestrian.0002",
        "walker.pedestrian.0003",
    ],
    "cyclist": [
        "vehicle.bh.crossbike",
        "vehicle.diamondback.century",
    ],
    "static": [
        "vehicle.audi.a2",
    ],
}

EGO_BLUEPRINT = "vehicle.tesla.model3"
EGO_COLOR = "0,120,255"


@dataclass
class ActorHandle:
    vdsim_id: int
    carla_actor: object = None
    blueprint_id: str = ""
    obj_type: str = "car"


class ActorManager:
    """Verwaltet die Zuordnung vdsim-ID → CARLA-Actor."""

    def __init__(self, conn, ego_blueprint=EGO_BLUEPRINT):
        self.conn = conn
        self.ego_blueprint = ego_blueprint
        self.handles: dict[int, ActorHandle] = {}
        self._bp_lib = conn.world.get_blueprint_library()
        self._rng = np.random.default_rng(42)

    def _pick_bp(self, obj_type, obj_id):
        choices = BLUEPRINTS.get(obj_type, BLUEPRINTS["car"])
        idx = obj_id % len(choices)
        bp = self._bp_lib.find(choices[idx])
        if bp is None:
            bp = self._bp_lib.filter("vehicle.*")[0]
        if bp.has_attribute("color"):
            colors = bp.get_attribute("color").recommended_values
            if colors:
                bp.set_attribute("color", colors[int(self._rng.integers(len(colors)))])
        bp.set_attribute("role_name", f"vdsim_{obj_id}")
        return bp

    def spawn_ego(self, ego_state, z=0.5):
        bp = self._bp_lib.find(self.ego_blueprint)
        if bp.has_attribute("color"):
            bp.set_attribute("color", EGO_COLOR)
        bp.set_attribute("role_name", "vdsim_ego")
        t = _transform(ego_state.x, ego_state.y, ego_state.psi, z)
        actor = self.conn.world.try_spawn_actor(bp, t)
        if actor is None:
            log.error("Ego konnte nicht gespawnt werden bei (%.1f, %.1f)", ego_state.x, ego_state.y)
            return None
        actor.set_simulate_physics(False)
        self.handles[0] = ActorHandle(0, actor, self.ego_blueprint, "car")
        log.info("Ego gespawnt: %s (id=%d)", self.ego_blueprint, actor.id)
        return actor

    def spawn_object(self, obj, z=0.5):
        bp = self._pick_bp(obj.type, obj.id)
        t = _transform(obj.x, obj.y, obj.psi, z)
        actor = self.conn.world.try_spawn_actor(bp, t)
        if actor is None:
            log.warning("Objekt %d (%s) konnte nicht gespawnt werden", obj.id, obj.type)
            return None
        actor.set_simulate_physics(False)
        self.handles[obj.id] = ActorHandle(obj.id, actor, bp.id, obj.type)
        return actor

    def update_ego(self, ego_state, z=0.5):
        h = self.handles.get(0)
        if h is None or h.carla_actor is None:
            self.spawn_ego(ego_state, z)
            return
        h.carla_actor.set_transform(_transform(ego_state.x, ego_state.y, ego_state.psi, z))

    def update_object(self, obj, z=0.5):
        h = self.handles.get(obj.id)
        if h is None:
            self.spawn_object(obj, z)
            return
        if h.carla_actor is not None:
            h.carla_actor.set_transform(_transform(obj.x, obj.y, obj.psi, z))

    def update_objects(self, objects, z=0.5):
        alive = {0}
        for obj in objects:
            self.update_object(obj, z)
            alive.add(obj.id)
        for oid in list(self.handles):
            if oid not in alive and oid != 0:
                h = self.handles.pop(oid)
                if h.carla_actor is not None:
                    h.carla_actor.destroy()

    def update_traffic_lights(self, tl_states):
        import carla
        carla_tls = self.conn.world.get_actors().filter("*traffic_light*")
        state_map = {"red": carla.TrafficLightState.Red, "yellow": carla.TrafficLightState.Yellow,
                     "green": carla.TrafficLightState.Green}
        for tl in carla_tls:
            vdsim_id = tl.get_opendrive_id() if hasattr(tl, "get_opendrive_id") else ""
            if vdsim_id in tl_states:
                tl.set_state(state_map.get(tl_states[vdsim_id], carla.TrafficLightState.Off))
                tl.set_green_time(9999)
                tl.set_red_time(9999)
                tl.freeze(True)

    def destroy_all(self):
        for h in self.handles.values():
            if h.carla_actor is not None:
                try:
                    h.carla_actor.destroy()
                except Exception:
                    pass
        self.handles.clear()


def _transform(x, y, psi, z=0.5):
    import carla
    return carla.Transform(
        carla.Location(x=float(x), y=float(-y), z=float(z)),
        carla.Rotation(yaw=float(-math.degrees(psi))),
    )
