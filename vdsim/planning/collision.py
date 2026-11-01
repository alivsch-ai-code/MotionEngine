"""Static and dynamic collision checking (Werling 2011, 3.5.4; Ziegler/Stiller 2010).

The vehicle geometries are approximated by circles along the longitudinal axis
(Ziegler and Stiller, "Fast collision checking for intelligent vehicle motion planning", IEEE IV
2010): a rectangle L x W is covered by n circles with centers spaced L/n and radius
r = sqrt((L/(2n))^2 + (W/2)^2). Two vehicles collide if the distance of any two circle centers
is below r_ego + r_obj + margin.

    * zero side slip at the reference point: the ego outline is aligned with the trajectory
      direction theta (psi = theta + pi when reversing)
    * common check horizon for all candidates (default 3.0 s): long polynomials are cut, short
      ones continue on their target manifold (Fig. 3.9)
    * safety margin per object type, built up linearly over dt_ramp along each candidate
      (Fig. 3.10): robust against measurement noise without switching the restriction off
    * the time of the first collision is returned (fallback: follow the trajectory that stays
      collision free for the longest time)

Custom checkers derive from CollisionChecker (kind="collision_checker") and implement
prepare() and check().
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..core.parameters import param
from ..framework.component import Component
from ..framework.knowledge import ComponentDoc, trace
from ..framework.plugins import component


@dataclass
class CollisionSettings:
    checker: str = param("collision_checker/circles", "", "Kollisionsprüfer (Spec)")
    horizon: float = param(3.0, "s", "Einheitlicher Prüfhorizont", min=0.5, max=10.0)
    dt: float = param(0.1, "s", "Zeitraster der Prüfung", min=0.01, max=0.5)
    margin_ramp: float = param(1.0, "s", "Aufbauzeit Δt des Sicherheitsabstands (Abb. 3.10)", min=0.0, max=5.0)
    margin_car: float = param(0.5, "m", "Sicherheitsabstand Pkw", min=0.0, max=5.0)
    margin_truck: float = param(0.7, "m", "Sicherheitsabstand Lkw", min=0.0, max=5.0)
    margin_pedestrian: float = param(1.5, "m", "Sicherheitsabstand Fußgänger", min=0.0, max=5.0)
    margin_cyclist: float = param(1.0, "m", "Sicherheitsabstand Radfahrer", min=0.0, max=5.0)
    margin_static: float = param(0.3, "m", "Sicherheitsabstand statische Hindernisse", min=0.0, max=5.0)
    margin_unknown: float = param(0.5, "m", "Sicherheitsabstand unbekannt", min=0.0, max=5.0)
    min_probability: float = param(0.05, "-", "Prädiktionen mit kleinerer Wahrscheinlichkeit ignorieren", min=0.0, max=1.0)
    front_overhang: float = param(-1.0, "m", "Überhang vorne (< 0: aus Länge und Radstand)", min=-1.0, max=3.0)
    rear_overhang: float = param(-1.0, "m", "Überhang hinten (< 0: aus Länge und Radstand)", min=-1.0, max=3.0)
    n_circles_ego: int = param(3, "", "Kreise Ego-Fahrzeug", min=1, max=10)
    max_circles_object: int = param(5, "", "Max. Kreise je Objekt", min=1, max=20)
    checker_params: dict = field(default_factory=dict, metadata={"label": "Parameter eines eigenen Prüfers",
                                                                  "unit": ""})

    def margin_for(self, obj_type):
        return float(getattr(self, f"margin_{obj_type}", self.margin_unknown))


@dataclass
class CollisionResult:
    collides: np.ndarray          # (B,) bool
    t_collision: np.ndarray       # (B,) absolute time of the first collision (inf if free)
    object_id: np.ndarray         # (B,) id of the first colliding object (-1 if free)
    clearance: np.ndarray         # (B, K) smallest geometric clearance to any object (inf if none)


def circle_cover(length, width, n):
    # Ziegler/Stiller: n circles covering a rectangle -> (offsets along the axis from the center, radius)
    n = max(int(n), 1)
    offs = -0.5 * length + length / (2 * n) * (2 * np.arange(n) + 1)
    return offs, float(np.hypot(length / (2 * n), 0.5 * width))


class CollisionChecker(Component):
    KIND, CATEGORY = "collision_checker", "Planer-Kollisionsprüfung"
    LABEL = "Kollisionsprüfer"

    def prepare(self, prediction, t_abs, geometry, settings, ctx):
        # called once per planning cycle: t_abs is the common time grid of the check horizon
        raise NotImplementedError

    def check(self, batch):
        raise NotImplementedError

    def geometry_info(self):
        return {}

    def step(self, t, inputs):
        return {}


@dataclass
class CircleCheckerParams:
    n_circles_ego: int = param(-1, "", "Kreise Ego (< 0: aus Planer-Einstellung)", min=-1, max=10)


@component
class CircleCollisionChecker(CollisionChecker):
    NAME, VERSION, LABEL = "circles", "1.0.0", "Kreisapproximation (Ziegler/Stiller)"
    PARAMS = CircleCheckerParams
    DOC = ComponentDoc(
        summary="Kollisionsprüfung mit Kreisüberdeckung der Fahrzeugumrisse, statisch und dynamisch über die Prädiktion.",
        purpose="Schnelle Überlappungsprüfung tausender Kandidaten (Werling 3.5.4).",
        assumptions=["Schwimmwinkel am Referenzpunkt = 0 (Ausrichtung = Trajektorienrichtung)",
                     "Objekte als Rechtecke entlang ihrer prädizierten Ausrichtung"],
        limitations=["zeitdiskrete Prüfung: bei sehr hohen Relativgeschwindigkeiten kann ein Durchtunneln zwischen "
                     "zwei Abtastpunkten auftreten (Raster collision.dt verkleinern)"],
        references=["werling2011", "ziegler2010iv"], equations=["werling2011:Abb. 3.10"],
        concepts=["collision_circles", "safety_margin_ramp"])

    def prepare(self, prediction, t_abs, geometry, settings, ctx):
        self.settings = settings
        self.t_abs = np.asarray(t_abs, dtype=float)
        n_ego = self.params.n_circles_ego if self.params.n_circles_ego > 0 else settings.n_circles_ego
        self.ego_offsets, self.ego_radius = circle_cover(geometry.length, geometry.width, n_ego)
        self.ego_offsets = self.ego_offsets + geometry.center_offset(ctx.reference_point)
        ramp = np.ones_like(self.t_abs) if settings.margin_ramp <= 0 else \
            np.clip((self.t_abs - self.t_abs[0]) / settings.margin_ramp, 0.0, 1.0)
        self.ramp = ramp
        centers, radii, margins, owner, self.objects = [], [], [], [], []
        for obj in (prediction.objects if prediction is not None else []):
            if len(obj.t) == 0 or obj.probability < settings.min_probability:
                continue
            x = np.interp(self.t_abs, obj.t, obj.x)
            y = np.interp(self.t_abs, obj.t, obj.y)
            psi = np.interp(self.t_abs, obj.t, np.unwrap(obj.psi)) if len(obj.psi) == len(obj.t) else \
                np.zeros_like(self.t_abs)
            n = int(np.clip(np.ceil(obj.length / max(obj.width, 0.1)), 1, settings.max_circles_object))
            offs, r = circle_cover(obj.length, obj.width, n)
            for o in offs:
                centers.append(np.stack([x + o * np.cos(psi), y + o * np.sin(psi)], axis=-1))
                radii.append(r)
                margins.append(settings.margin_for(obj.type))
                owner.append(len(self.objects))
            self.objects.append({"id": int(obj.id), "type": obj.type, "radius": r, "n": n,
                                 "margin": settings.margin_for(obj.type)})
        self.centers = np.array(centers).reshape(len(centers), len(self.t_abs), 2) if centers else \
            np.zeros((0, len(self.t_abs), 2))
        self.radii = np.asarray(radii, dtype=float)
        self.margins = np.asarray(margins, dtype=float)
        self.owner = np.asarray(owner, dtype=int)

    @trace("ziegler2010iv", section="III", concept="collision_circles",
           note="Kreisüberdeckung, Überlappung |c_i - c_j| < r_i + r_j + Sicherheitsabstand(t)")
    def check(self, batch):
        b, k = batch.x.shape
        if len(self.radii) == 0:
            return CollisionResult(np.zeros(b, dtype=bool), np.full(b, np.inf), -np.ones(b, dtype=int),
                                   np.full((b, k), np.inf))
        psi = batch.psi
        cs, sn = np.cos(psi), np.sin(psi)
        ex = batch.x[:, :, None] + self.ego_offsets[None, None, :] * cs[:, :, None]     # (B, K, n)
        ey = batch.y[:, :, None] + self.ego_offsets[None, None, :] * sn[:, :, None]
        ox = self.centers[:, :, 0].T                                                     # (K, C)
        oy = self.centers[:, :, 1].T
        dx = ex[:, :, :, None] - ox[None, :, None, :]
        dy = ey[:, :, :, None] - oy[None, :, None, :]
        dist = np.sqrt((dx * dx + dy * dy).min(axis=2))                                  # (B, K, C)
        clear = dist - self.ego_radius - self.radii[None, None, :]
        need = self.margins[None, :] * self.ramp[:, None]                                # (K, C) Fig. 3.10
        hit = clear < need[None, :, :]
        hit_t = hit.any(axis=2)
        collides = hit_t.any(axis=1)
        first = np.argmax(hit_t, axis=1)
        t_col = np.where(collides, self.t_abs[first], np.inf)
        circ = np.argmax(hit[np.arange(b), first, :], axis=1)
        ids = np.array([o["id"] for o in self.objects])
        obj_id = np.where(collides, ids[self.owner[circ]], -1)
        return CollisionResult(collides, t_col, obj_id, clear.min(axis=2))

    @trace("werling2011", section="3.5.4", equation="Abb. 3.10", concept="safety_margin_ramp",
           note="Sicherheitsabstand linear über Δt aufgebaut")
    def geometry_info(self):
        return {"ego_radius": float(self.ego_radius), "ego_offsets": [float(o) for o in self.ego_offsets],
                "objects": {str(o["id"]): {"radius": float(o["radius"]), "n": o["n"], "margin": o["margin"],
                                           "type": o["type"]} for o in self.objects},
                "margin_ramp": {"dt": float(self.settings.margin_ramp),
                                "t": [float(v) for v in self.t_abs - self.t_abs[0]],
                                "factor": [float(v) for v in self.ramp]}}
