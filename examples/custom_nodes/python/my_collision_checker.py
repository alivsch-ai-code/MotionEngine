"""Example: own collision checker for the Werling trajectory planner (kind="collision_checker").

Exact rectangle overlap test with the separating axis theorem (SAT) instead of the circle
approximation. Usage:

    "collision": {"checker": "python:examples/custom_nodes/python/my_collision_checker.py:BoxCollisionChecker"}

The checker receives once per cycle the prediction, the common time grid of the check horizon
and the ego geometry (prepare) and then evaluates batches of candidates (check). It must return
the time of the first collision so that the planner can select the fallback trajectory.
"""

from dataclasses import dataclass

import numpy as np

from vdsim.core.parameters import param
from vdsim.framework.knowledge import ComponentDoc
from vdsim.planning.collision import CollisionChecker, CollisionResult


@dataclass
class BoxCheckerParams:
    use_margin: bool = param(True, "", "Sicherheitsabstände der Planer-Einstellung verwenden")


class BoxCollisionChecker(CollisionChecker):
    NAME, VERSION, LABEL = "boxes_sat", "1.0.0", "Rechteck-Kollisionsprüfung (SAT, Beispiel)"
    PARAMS = BoxCheckerParams
    DOC = ComponentDoc(summary="Exakte Überlappung orientierter Rechtecke mit dem Trennachsensatz.",
                       limitations=["Abstand (clearance) nur grob über die Mittelpunktsdistanz genähert"])

    def prepare(self, prediction, t_abs, geometry, settings, ctx):
        self.t_abs = np.asarray(t_abs, dtype=float)
        self.geometry, self.settings, self.ctx = geometry, settings, ctx
        ramp = np.ones_like(self.t_abs) if settings.margin_ramp <= 0 else \
            np.clip((self.t_abs - self.t_abs[0]) / settings.margin_ramp, 0.0, 1.0)
        self.objects = []
        for obj in (prediction.objects if prediction is not None else []):
            if len(obj.t) == 0:
                continue
            margin = settings.margin_for(obj.type) * ramp if self.params.use_margin else 0.0 * ramp
            self.objects.append({"id": obj.id, "x": np.interp(self.t_abs, obj.t, obj.x),
                                 "y": np.interp(self.t_abs, obj.t, obj.y),
                                 "psi": np.interp(self.t_abs, obj.t, np.unwrap(obj.psi)),
                                 "hl": 0.5 * obj.length + margin, "hw": 0.5 * obj.width + margin})

    def check(self, batch):
        b, k = batch.x.shape
        collides = np.zeros((b, k), dtype=bool)
        first_obj = -np.ones((b, k), dtype=int)
        clearance = np.full((b, k), np.inf)
        g = self.geometry
        off = g.center_offset(self.ctx.reference_point)
        psi = batch.psi
        ux, uy = np.cos(psi), np.sin(psi)
        cx, cy = batch.x + off * ux, batch.y + off * uy
        hl, hw = 0.5 * g.length, 0.5 * g.width
        for o in self.objects:
            ox, oy = np.cos(o["psi"]), np.sin(o["psi"])
            dx, dy = o["x"] - cx, o["y"] - cy
            sep = np.zeros((b, k), dtype=bool)
            for ax, ay in ((ux, uy), (-uy, ux), (ox + 0 * ux, oy + 0 * uy), (-oy + 0 * ux, ox + 0 * uy)):
                r_e = hl * np.abs(ux * ax + uy * ay) + hw * np.abs(-uy * ax + ux * ay)
                r_o = o["hl"] * np.abs(ox * ax + oy * ay) + o["hw"] * np.abs(-oy * ax + ox * ay)
                sep |= np.abs(dx * ax + dy * ay) > r_e + r_o
            hit = ~sep
            first_obj = np.where(hit & ~collides, o["id"], first_obj)
            collides |= hit
            clearance = np.minimum(clearance, np.hypot(dx, dy) - np.hypot(hl, hw) - np.hypot(o["hl"], o["hw"]))
        any_hit = collides.any(axis=1)
        k_first = np.argmax(collides, axis=1)
        return CollisionResult(any_hit, np.where(any_hit, self.t_abs[k_first], np.inf),
                               np.where(any_hit, first_obj[np.arange(b), k_first], -1), clearance)

    def geometry_info(self):
        return {"type": "boxes", "objects": {str(o["id"]): {"half_length": float(np.max(o["hl"])),
                                                            "half_width": float(np.max(o["hw"]))}
                                             for o in self.objects}}
