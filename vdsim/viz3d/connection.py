"""Verbindung zum CARLA-Server und Grundkonfiguration der Welt."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.logging_setup import get_logger

log = get_logger("viz3d.connection")


@dataclass
class CARLAConnection:
    host: str = "localhost"
    port: int = 2000
    timeout: float = 10.0
    client: object = field(default=None, repr=False)
    world: object = field(default=None, repr=False)

    def ensure(self):
        if self.client is not None:
            return self
        import carla
        self.client = carla.Client(self.host, self.port)
        self.client.set_timeout(self.timeout)
        self.world = self.client.get_world()
        log.info("CARLA %s verbunden (%s:%d)", self.client.get_server_version(), self.host, self.port)
        return self

    def set_synchronous(self, dt=0.01, no_rendering=False):
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = dt
        settings.no_rendering_mode = no_rendering
        self.world.apply_settings(settings)
        log.info("synchroner Modus: dt=%.3f s, no_rendering=%s", dt, no_rendering)

    def set_weather(self, preset="ClearNoon"):
        import carla
        weather = getattr(carla.WeatherParameters, preset, None)
        if weather is None:
            log.warning("Wetter-Preset '%s' unbekannt", preset)
            return
        self.world.set_weather(weather)

    def load_map(self, name="Town04"):
        self.world = self.client.load_world(name)
        log.info("Karte '%s' geladen", name)

    def load_opendrive(self, xodr_path):
        import carla
        with open(xodr_path, encoding="utf-8") as f:
            xodr = f.read()
        self.world = self.client.generate_opendrive_world(
            xodr,
            carla.OpendriveGenerationParameters(
                vertex_distance=2.0,
                max_road_length=500.0,
                wall_height=0.0,
                additional_width=0.6,
                smooth_junctions=True,
                enable_mesh_visibility=True,
            ),
        )
        log.info("OpenDRIVE-Welt geladen aus '%s'", xodr_path)

    def spectator_follow(self, transform, z_offset=15.0, pitch=-60.0):
        import carla
        spec = self.world.get_spectator()
        loc = transform.location + carla.Location(z=z_offset)
        spec.set_transform(carla.Transform(loc, carla.Rotation(pitch=pitch, yaw=transform.rotation.yaw)))

    def cleanup_actors(self, tag="vdsim"):
        actors = self.world.get_actors()
        to_destroy = [a for a in actors if a.attributes.get("role_name", "").startswith(tag)]
        for a in to_destroy:
            a.destroy()
        if to_destroy:
            log.info("%d vdsim-Akteure entfernt", len(to_destroy))

    def tick(self):
        return self.world.tick()


_conn = None


def connect(host="localhost", port=2000, timeout=10.0) -> CARLAConnection:
    global _conn
    if _conn is not None and _conn.host == host and _conn.port == port:
        try:
            _conn.world.get_spectator()
            return _conn
        except Exception:
            _conn = None
    _conn = CARLAConnection(host, port, timeout).ensure()
    return _conn
