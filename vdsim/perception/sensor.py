"""Object sensor model and ground-truth perception.

perception/object_sensor  ground truth -> ObjectList with range, field of view, optional simple
                          occlusion (angular shadowing by closer objects), polar position noise
                          (range + azimuth), additive position / speed / heading / acceleration
                          noise, detection probability and latency; ego estimate with optional
                          localization noise. All randomness from context.rng (reproducible).
perception/ground_truth   passes the ground truth through unchanged.
"""

from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass, replace

import numpy as np

from ..core.parameters import param
from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import PerceptionBase
from ..framework.types import EgoState, ObjectList
from ..geometry.reference_line import wrap_angle


@dataclass
class ObjectSensorParams:
    range: float = param(150.0, "m", "Reichweite", min=1.0, max=1000.0)
    fov_deg: float = param(360.0, "°", "Öffnungswinkel", min=1.0, max=360.0)
    heading_offset_deg: float = param(0.0, "°", "Ausrichtung des Sensors (0 = nach vorn)", min=-180.0, max=180.0)
    mount_x: float = param(0.0, "m", "Einbauort vor dem Schwerpunkt", min=-5.0, max=5.0)
    cycle_time: float = param(0.1, "s", "Messzyklus", min=0.0, max=1.0)
    latency: float = param(0.0, "s", "Latenz", min=0.0, max=2.0)
    detection_probability: float = param(1.0, "-", "Erkennungswahrscheinlichkeit", min=0.0, max=1.0)
    occlusion: bool = param(False, "", "einfache Verdeckung")
    occlusion_fraction: float = param(0.75, "-", "verdeckter Winkelanteil für Nichterkennung", min=0.05, max=1.0)
    occlusion_rays: int = param(9, "-", "Strahlen pro Objekt (Verdeckung)", min=3, max=50)
    range_sigma: float = param(0.0, "m", "Entfernungsrauschen σ_r", min=0.0, max=5.0)
    azimuth_sigma_deg: float = param(0.0, "°", "Winkelrauschen σ_φ", min=0.0, max=10.0)
    pos_sigma: float = param(0.0, "m", "Positionsrauschen σ_xy", min=0.0, max=5.0)
    vel_sigma: float = param(0.0, "m/s", "Geschwindigkeitsrauschen σ_v", min=0.0, max=5.0)
    heading_sigma_deg: float = param(0.0, "°", "Orientierungsrauschen σ_ψ", min=0.0, max=30.0)
    accel_sigma: float = param(0.0, "m/s²", "Beschleunigungsrauschen σ_a", min=0.0, max=5.0)
    ego_pos_sigma: float = param(0.0, "m", "Lokalisierungsrauschen Position", min=0.0, max=5.0)
    ego_heading_sigma_deg: float = param(0.0, "°", "Lokalisierungsrauschen Gierwinkel", min=0.0, max=10.0)
    ego_vel_sigma: float = param(0.0, "m/s", "Rauschen Eigengeschwindigkeit", min=0.0, max=2.0)
    update_frenet: bool = param(True, "", "s, d nach Rauschen neu auf die Spur projizieren")


@trace("vdsim", section="perception", concept="sensor_model",
       note="Sichtbereich (Reichweite, Öffnungswinkel) und Winkelverdeckung durch nähere Objekte")
def visibility(sx, sy, heading, objects, rng_max, fov, occlusion=False, frac=0.75, rays=9):
    # boolean mask of the objects inside range / field of view and (optionally) not occluded
    n = len(objects)
    if n == 0:
        return np.zeros(0, dtype=bool)
    from ..world.collision import rect_corners
    ox = np.array([o.x for o in objects])
    oy = np.array([o.y for o in objects])
    corners = rect_corners(ox, oy, [o.psi for o in objects], [o.length for o in objects], [o.width for o in objects])
    dist_c = np.hypot(corners[..., 0] - sx, corners[..., 1] - sy)          # (n, 4)
    dist = np.hypot(ox - sx, oy - sy)
    bear_c = np.arctan2(corners[..., 1] - sy, corners[..., 0] - sx)
    center = np.arctan2(oy - sy, ox - sx)
    rel = wrap_angle(bear_c - center[:, None])
    lo, hi = center + rel.min(axis=1), center + rel.max(axis=1)
    in_range = dist_c.min(axis=1) <= rng_max
    if fov >= 2 * np.pi - 1e-9:
        in_fov = np.ones(n, dtype=bool)
    else:
        half = 0.5 * fov
        a_lo, a_hi = wrap_angle(lo - heading), wrap_angle(hi - heading)
        a_c = wrap_angle(center - heading)
        in_fov = (np.abs(a_c) <= half) | (np.abs(a_lo) <= half) | (np.abs(a_hi) <= half)
    vis = in_range & in_fov
    if occlusion and n > 1:
        order = np.argsort(dist)
        for k, i in enumerate(order):
            if not vis[i]:
                continue
            closer = order[:k]
            if len(closer) == 0:
                continue
            ang = np.linspace(lo[i], hi[i], rays)
            rel_c = wrap_angle(ang[:, None] - center[closer][None, :])
            inside = (rel_c >= (lo[closer] - center[closer])[None, :]) & (rel_c <= (hi[closer] - center[closer])[None, :])
            blocked = np.any(inside & (dist[closer] < dist[i])[None, :], axis=1)
            if blocked.mean() >= frac:
                vis[i] = False
    return vis


class ObjectSensor(PerceptionBase):
    NAME, VERSION = "object_sensor", "1.0.0"
    LABEL = "Objektsensor (Reichweite, Rauschen, Latenz)"
    PARAMS = ObjectSensorParams
    PERIOD = None          # ego estimate every step, objects every cycle_time
    DOC = ComponentDoc(
        summary="Erzeugt aus der Ground Truth eine gestörte Objektliste und eine Eigenzustandsschätzung.",
        purpose="Realistischere Eingangsdaten für Prädiktion und Verhalten: begrenzte Sicht, Verdeckung, "
                "Messrauschen, Fehldetektionen und Latenz; reproduzierbar über den Szenario-Seed.",
        theory="Polares Messmodell: $r_m = r + n_r$, $\\varphi_m = \\varphi + n_\\varphi$ mit "
               "$n \\sim \\mathcal{N}(0, \\sigma^2)$, zusätzlich additives Rauschen auf Position, Geschwindigkeit, "
               "Orientierung und Beschleunigung. Ein Objekt ist sichtbar, wenn ein Eckpunkt in Reichweite liegt, "
               "es den Öffnungswinkel schneidet und nicht überwiegend von näheren Objekten abgeschattet wird.",
        assumptions=["Objekte als Rechtecke, Verdeckung nur in der Ebene (keine Höheninformation)",
                     "Rauschen weiß und normalverteilt, Objekte unabhängig"],
        limitations=["kein Tracking, keine Falschalarme (Geisterobjekte)", "keine Sensorfusion mehrerer Sensoren"],
        references=["bar_shalom2001"],
        concepts=["sensor_model"],
        validation=["tests/perception/test_perception_sensor.py"],
        extension_points=["weitere Sensoren als eigene Komponente der Ebene perception"],
    )

    def reset(self, context):
        super().reset(context)
        self.rng = context.rng(f"perception/{self.instance_name}")
        self.rng_ego = context.rng(f"perception/{self.instance_name}/ego")
        self.buffer = deque()
        self.t_next = None
        self.output_list = ObjectList(t=0.0, objects=[])

    def _measure(self, t, world, ego):
        p = self.params
        road = world.road if world.road is not None else getattr(self.context, "road", None)
        objs = sorted(world.objects, key=lambda o: o.id)
        heading = ego.psi + np.radians(p.heading_offset_deg)
        sx, sy = ego.point_ahead(p.mount_x)
        vis = visibility(sx, sy, heading, objs, p.range, np.radians(p.fov_deg), p.occlusion, p.occlusion_fraction,
                         int(p.occlusion_rays))
        n = len(objs)
        noise = self.rng.standard_normal((n, 7)) if n else np.zeros((0, 7))
        detect = self.rng.random(n) < p.detection_probability if n else np.zeros(0, dtype=bool)
        out = []
        for i, o in enumerate(objs):
            if not (vis[i] and detect[i]):
                continue
            m = copy.copy(o)
            r = np.hypot(o.x - sx, o.y - sy) + p.range_sigma * noise[i, 0]
            phi = np.arctan2(o.y - sy, o.x - sx) + np.radians(p.azimuth_sigma_deg) * noise[i, 1]
            m.x = float(sx + r * np.cos(phi) + p.pos_sigma * noise[i, 2])
            m.y = float(sy + r * np.sin(phi) + p.pos_sigma * noise[i, 3])
            m.v = float(max(o.v + p.vel_sigma * noise[i, 4], 0.0))
            m.psi = float(o.psi + np.radians(p.heading_sigma_deg) * noise[i, 5])
            m.a = float(o.a + p.accel_sigma * noise[i, 6])
            if p.update_frenet and road is not None and o.lane_id in getattr(road, "lanes", {}) and o.s is not None:
                from ..world.actors import project_near
                s, d = project_near(road.lanes[o.lane_id], m.x, m.y, o.s)
                m.s, m.d = float(s), float(d)
            out.append(m)
        return ObjectList(t=float(world.t if world.t is not None else t), objects=out)

    def _ego_estimate(self, ego):
        p = self.params
        if p.ego_pos_sigma == 0 and p.ego_heading_sigma_deg == 0 and p.ego_vel_sigma == 0:
            return ego
        n = self.rng_ego.standard_normal(4)
        return replace(ego, x=ego.x + p.ego_pos_sigma * n[0], y=ego.y + p.ego_pos_sigma * n[1],
                       psi=ego.psi + np.radians(p.ego_heading_sigma_deg) * n[2], vx=ego.vx + p.ego_vel_sigma * n[3])

    def step(self, t, inputs):
        world, ego = inputs.get("world"), inputs.get("ego")
        if ego is None:
            ego = EgoState(t=t)
        p = self.params
        if world is not None and (self.t_next is None or t >= self.t_next - 1e-9):
            self.buffer.append(self._measure(t, world, ego))
            self.t_next = t + p.cycle_time if p.cycle_time > 0 else t
        while self.buffer and self.buffer[0].t <= t - p.latency + 1e-9:
            self.output_list = self.buffer.popleft()
        self.signals["n_objects"] = float(len(self.output_list.objects))
        return {"objects": self.output_list, "ego_estimate": self._ego_estimate(ego)}


class GroundTruthPerception(PerceptionBase):
    NAME, VERSION = "ground_truth", "1.0.0"
    LABEL = "Ground Truth (ungestört)"
    PERIOD = None
    DOC = ComponentDoc(
        summary="Gibt die Objekte der Szenario-Engine und den wahren Eigenzustand unverändert weiter.",
        purpose="Referenz für die Entwicklung von Prädiktion, Verhalten und Planung ohne Wahrnehmungsfehler.",
        concepts=["sensor_model"],
        validation=["tests/perception/test_perception_sensor.py"],
    )

    def step(self, t, inputs):
        world, ego = inputs.get("world"), inputs.get("ego")
        objs = [copy.copy(o) for o in (world.objects if world is not None else [])]
        return {"objects": ObjectList(t=float(world.t) if world is not None else t, objects=objs),
                "ego_estimate": ego if ego is not None else EgoState(t=t)}
