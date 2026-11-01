"""Custom node (Python): fusion of two noisy object lists with the ports of PerceptionBase.

Graph spec: "python:examples/custom_nodes/python/my_sensor_fusion_module.py:TwoSensorFusion"

    inputs:  world (WorldState: ground truth objects), ego (EgoState)
    outputs: objects (ObjectList, fused + smoothed), ego_estimate (EgoState)

Two virtual sensors measure every ground-truth object with different accuracy
(radar: precise in x and speed, camera: precise in y). The measurements are fused per
object with inverse-variance weighting and then smoothed over time with an alpha filter.
Noise comes from context.rng(name) only, so runs are reproducible.

    fused  z = (z_r / s_r^2 + z_c / s_c^2) / (1 / s_r^2 + 1 / s_c^2)
    smooth x_k = x_{k-1} + alpha (z_k - x_{k-1})
"""

import copy
from dataclasses import dataclass, replace

from vdsim.core.parameters import param
from vdsim.framework.knowledge import ComponentDoc
from vdsim.framework.layers import PerceptionBase
from vdsim.framework.types import ObjectList


@dataclass
class FusionParams:
    radar_sigma_x: float = param(0.2, "m", "Radar σ x", min=0.0)
    radar_sigma_y: float = param(0.8, "m", "Radar σ y", min=0.0)
    radar_sigma_v: float = param(0.1, "m/s", "Radar σ v", min=0.0)
    camera_sigma_x: float = param(1.0, "m", "Kamera σ x", min=0.0)
    camera_sigma_y: float = param(0.2, "m", "Kamera σ y", min=0.0)
    camera_sigma_v: float = param(0.5, "m/s", "Kamera σ v", min=0.0)
    alpha: float = param(0.3, "-", "Glättungsfaktor", min=0.0, max=1.0)


def _fuse(z1, s1, z2, s2):
    w1, w2 = 1.0 / max(s1, 1e-6) ** 2, 1.0 / max(s2, 1e-6) ** 2
    return (w1 * z1 + w2 * z2) / (w1 + w2)


class TwoSensorFusion(PerceptionBase):
    NAME = "my_two_sensor_fusion"
    VERSION = "1.0.0"
    LABEL = "Fusion zweier Sensoren (Beispiel, Python)"
    PARAMS = FusionParams
    DOC = ComponentDoc(summary="Fusion von Radar- und Kamera-Objektlisten (Varianzgewichtung) mit Alpha-Glättung.",
                       purpose="Beispiel für einen Custom Node mit den Ports der Ebene Perception.",
                       assumptions=["bekannte Zuordnung über die Objekt-ID", "unkorreliertes Gaußrauschen"])

    def reset(self, context):
        super().reset(context)
        self.rng_radar = context.rng(f"{self.instance_name}/radar")
        self.rng_camera = context.rng(f"{self.instance_name}/camera")
        self.tracks = {}            # id -> (x, y, v)

    def step(self, t, inputs):
        world, ego = inputs["world"], inputs["ego"]
        p = self.params
        out = []
        seen = set()
        for obj in getattr(world, "objects", []) or []:
            r = self.rng_radar.normal(0.0, 1.0, 3) * (p.radar_sigma_x, p.radar_sigma_y, p.radar_sigma_v)
            c = self.rng_camera.normal(0.0, 1.0, 3) * (p.camera_sigma_x, p.camera_sigma_y, p.camera_sigma_v)
            z = (_fuse(obj.x + r[0], p.radar_sigma_x, obj.x + c[0], p.camera_sigma_x),
                 _fuse(obj.y + r[1], p.radar_sigma_y, obj.y + c[1], p.camera_sigma_y),
                 _fuse(obj.v + r[2], p.radar_sigma_v, obj.v + c[2], p.camera_sigma_v))
            prev = self.tracks.get(obj.id)
            est = z if prev is None else tuple(a + p.alpha * (b - a) for a, b in zip(prev, z))
            self.tracks[obj.id] = est
            seen.add(obj.id)
            out.append(replace(obj, x=float(est[0]), y=float(est[1]), v=float(est[2])))
        for oid in [k for k in self.tracks if k not in seen]:
            del self.tracks[oid]
        self.signals["n_objects"] = float(len(out))
        return {"objects": ObjectList(t=t, objects=out), "ego_estimate": copy.copy(ego) if ego is not None else None}
