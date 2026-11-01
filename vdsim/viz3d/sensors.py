"""Synthetische Sensoren: Kamera, LiDAR, Radar über CARLA-Sensor-Actors.

Jeder Sensor wird als CARLA-Actor an das Ego-Fahrzeug gehängt und liefert
Roh-Frames über einen Callback. Die Bilder/Punktwolken können live gestreamt
(pygame/open3d) oder gespeichert werden.

Sensor-Presets (typische AD-Konfigurationen):

    camera_front     RGB-Frontkamera 1920×1080 @20 Hz, FOV 90°
    camera_rear      RGB-Rückkamera 1280×720 @10 Hz
    depth_front      Tiefenkamera (Stereo-Ersatz) gleiche Pose wie camera_front
    semantic_front   Semantische Segmentierung (Ground Truth)
    lidar_top        Velodyne-64-ähnlich, 360°, 120k Punkte/s
    radar_front      Langstreckenradar 77 GHz, ±30°, 100 m Reichweite
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..core.logging_setup import get_logger

log = get_logger("viz3d.sensors")


@dataclass
class SensorSpec:
    name: str
    type: str
    transform_xyz: tuple = (0.0, 0.0, 0.0)
    transform_rpy: tuple = (0.0, 0.0, 0.0)
    attributes: dict = field(default_factory=dict)
    fps: float = 20.0


PRESETS = {
    "camera_front": SensorSpec(
        "camera_front", "sensor.camera.rgb",
        transform_xyz=(2.0, 0.0, 1.5), transform_rpy=(0, -5, 0),
        attributes={"image_size_x": "1920", "image_size_y": "1080", "fov": "90"},
        fps=20.0,
    ),
    "camera_rear": SensorSpec(
        "camera_rear", "sensor.camera.rgb",
        transform_xyz=(-2.0, 0.0, 1.5), transform_rpy=(0, -10, 180),
        attributes={"image_size_x": "1280", "image_size_y": "720", "fov": "110"},
        fps=10.0,
    ),
    "depth_front": SensorSpec(
        "depth_front", "sensor.camera.depth",
        transform_xyz=(2.0, 0.0, 1.5), transform_rpy=(0, -5, 0),
        attributes={"image_size_x": "1920", "image_size_y": "1080", "fov": "90"},
        fps=20.0,
    ),
    "semantic_front": SensorSpec(
        "semantic_front", "sensor.camera.semantic_segmentation",
        transform_xyz=(2.0, 0.0, 1.5), transform_rpy=(0, -5, 0),
        attributes={"image_size_x": "960", "image_size_y": "540", "fov": "90"},
        fps=10.0,
    ),
    "lidar_top": SensorSpec(
        "lidar_top", "sensor.lidar.ray_cast",
        transform_xyz=(0.0, 0.0, 2.4),
        attributes={
            "channels": "64", "range": "100.0", "rotation_frequency": "20",
            "points_per_second": "1200000", "upper_fov": "2.0", "lower_fov": "-24.8",
        },
        fps=20.0,
    ),
    "radar_front": SensorSpec(
        "radar_front", "sensor.other.radar",
        transform_xyz=(2.5, 0.0, 0.8),
        attributes={"horizontal_fov": "60", "vertical_fov": "10", "range": "100",
                     "points_per_second": "1500"},
        fps=20.0,
    ),
}


class SensorHandle:
    def __init__(self, spec, carla_actor, save_dir=None):
        self.spec = spec
        self.actor = carla_actor
        self.save_dir = Path(save_dir) if save_dir else None
        self.frames = []
        self._frame_count = 0

    def _callback(self, data):
        self._frame_count += 1
        if self.save_dir is not None:
            path = self.save_dir / f"{self.spec.name}_{self._frame_count:06d}"
            if "camera" in self.spec.type:
                data.save_to_disk(str(path.with_suffix(".png")))
            elif "lidar" in self.spec.type:
                data.save_to_disk(str(path.with_suffix(".ply")))
        frame = {"frame": self._frame_count, "timestamp": data.timestamp}
        if "camera" in self.spec.type:
            arr = np.frombuffer(data.raw_data, dtype=np.uint8)
            w, h = int(data.width), int(data.height)
            frame["image"] = arr.reshape(h, w, 4)[:, :, :3]
        elif "lidar" in self.spec.type:
            pts = np.frombuffer(data.raw_data, dtype=np.float32).reshape(-1, 4)
            frame["points"] = pts[:, :3]
            frame["intensity"] = pts[:, 3]
        elif "radar" in self.spec.type:
            frame["detections"] = [(d.depth, d.azimuth, d.altitude, d.velocity) for d in data]
        self.frames.append(frame)
        if len(self.frames) > 100:
            self.frames.pop(0)

    @property
    def latest(self):
        return self.frames[-1] if self.frames else None

    def destroy(self):
        if self.actor is not None and self.actor.is_alive:
            self.actor.stop()
            self.actor.destroy()


class SensorRig:
    """Sensoraufbau am Ego-Fahrzeug."""

    def __init__(self, conn, ego_actor, save_dir=None):
        self.conn = conn
        self.ego = ego_actor
        self.save_dir = save_dir
        self.sensors: dict[str, SensorHandle] = {}
        self._bp_lib = conn.world.get_blueprint_library()

    def attach(self, spec_or_name):
        import carla
        if isinstance(spec_or_name, str):
            spec = PRESETS.get(spec_or_name)
            if spec is None:
                raise KeyError(f"unbekannter Sensor-Preset '{spec_or_name}' (verfügbar: {sorted(PRESETS)})")
        else:
            spec = spec_or_name

        bp = self._bp_lib.find(spec.type)
        for k, v in spec.attributes.items():
            if bp.has_attribute(k):
                bp.set_attribute(k, str(v))
        if bp.has_attribute("sensor_tick"):
            bp.set_attribute("sensor_tick", str(1.0 / spec.fps))

        x, y, z = spec.transform_xyz
        p, ya, r = spec.transform_rpy
        tf = carla.Transform(carla.Location(x=x, y=-y, z=z), carla.Rotation(pitch=p, yaw=-ya, roll=r))

        actor = self.conn.world.spawn_actor(bp, tf, attach_to=self.ego)
        sd = Path(self.save_dir) / spec.name if self.save_dir else None
        if sd:
            sd.mkdir(parents=True, exist_ok=True)
        handle = SensorHandle(spec, actor, sd)
        actor.listen(handle._callback)
        self.sensors[spec.name] = handle
        log.info("Sensor '%s' (%s) angehängt", spec.name, spec.type)
        return handle

    def attach_preset(self, *names):
        for name in names:
            self.attach(name)

    def destroy_all(self):
        for h in self.sensors.values():
            h.destroy()
        self.sensors.clear()
