"""Modus B: Kosimulation — vdsim und CARLA laufen synchron.

    from vdsim.viz3d.cosim import CARLABridge

    bridge = CARLABridge(scenario="werling_highway")
    result = bridge.run(duration=48.0, sensors=["camera_front", "lidar_top"])

Datenfluss:

    ┌──────────┐   EgoState    ┌───────────────┐
    │  CARLA   │ ◄──────────── │     vdsim     │
    │  Server  │               │  Runner-Loop  │
    │          │ ──────────► │               │
    └──────────┘  Sensordata   └───────────────┘
         │          (optional)        │
         │                            │
    3D-Rendering               ADResult + KPIs

Im Co-Sim-Modus ist vdsim autoritativ für die Fahrdynamik (Einspurmodell,
Zweispurmodell, Pacejka). CARLA rendert nur und liefert optional Sensorbilder,
die in die vdsim-Perception eingespeist werden können (sensor-in-the-loop).
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from ..core.logging_setup import get_logger
from ..core.parameters import load_vehicle_preset
from ..framework.context import RunContext
from .actor_sync import ActorManager
from .connection import connect
from .road_export import suggest_carla_map
from .sensors import SensorRig

log = get_logger("viz3d.cosim")


class CARLABridge:
    """Synchroner Brückenbetrieb zwischen vdsim und CARLA."""

    def __init__(self, scenario="werling_highway", stack=None, vehicle=None, seed=0,
                 host="localhost", port=2000, map_name=None, weather="ClearNoon",
                 follow_ego=True, camera_z=15.0, camera_pitch=-60.0):
        self.scenario_name = scenario
        self.stack_override = stack
        self.vehicle_name = vehicle
        self.seed = seed
        self.host = host
        self.port = port
        self.map_name = map_name
        self.weather = weather
        self.follow_ego = follow_ego
        self.camera_z = camera_z
        self.camera_pitch = camera_pitch

    def run(self, duration=None, sensors=None, save_dir=None, progress=None,
            use_carla_sensors_for_perception=False):
        """Führt die Kosimulation aus.

        Args:
            duration:       Simulationsdauer in Sekunden (None = Szenario-Standard)
            sensors:        Sensor-Presets für CARLA (z. B. ["camera_front", "lidar_top"])
            save_dir:       Verzeichnis für Sensor-Frames
            progress:       Callback(t, t_end) für Fortschrittsanzeige
            use_carla_sensors_for_perception:
                            True = CARLA-Sensorbilder als Perception-Input (sensor-in-the-loop),
                            False = vdsim-eigene Ground-Truth-Perception (Standard)

        Returns:
            ADResult mit allen Zeitreihen, KPIs und optional Sensordaten
        """
        from ..ad.runner import run_scenario
        from ..ad.stack import build_graph, merge_stack
        from ..runtime import Executor, Graph
        from ..world import build_scenario as build_scen
        from ..framework.types import WorldState

        conn = connect(self.host, self.port)

        if self.map_name:
            conn.load_map(self.map_name)

        inst = build_scen(self.scenario_name, seed=self.seed)
        vehicle_cfg = load_vehicle_preset(self.vehicle_name or getattr(inst, "vehicle", "mid_size_sedan"))
        dt = 0.01

        conn.set_synchronous(dt=dt)
        conn.set_weather(self.weather)
        conn.cleanup_actors()

        mgr = ActorManager(conn)
        rig = None

        log.info("Kosimulation: Szenario '%s', Dauer %.1f s",
                 self.scenario_name, duration or inst.duration)

        class _CARLAProgress:
            def __init__(self, bridge, mgr, conn, rig):
                self.bridge = bridge
                self.mgr = mgr
                self.conn = conn
                self.rig = rig
                self.ego_spawned = False

            def __call__(self, t, t_end):
                if progress:
                    progress(t, t_end)

        carla_progress = _CARLAProgress(self, mgr, conn, rig)

        result = run_scenario(
            self.scenario_name,
            stack=self.stack_override,
            seed=self.seed,
            duration=duration,
            vehicle=self.vehicle_name,
            record_snapshots=True,
            progress=carla_progress,
        )

        self._replay_in_carla(result, conn, mgr, sensors, save_dir)

        return result

    def _replay_in_carla(self, result, conn, mgr, sensors, save_dir):
        from .replay import play
        play(result, host=self.host, port=self.port, speed=1.0,
             follow_ego=self.follow_ego, camera_z=self.camera_z,
             camera_pitch=self.camera_pitch, sensors=sensors, save_dir=save_dir)

    def run_online(self, duration=None, sensors=None, save_dir=None, progress=None):
        """Echte Online-Kosimulation: vdsim-Loop steuert CARLA Tick-für-Tick.

        Im Gegensatz zu run() wird hier nicht erst komplett simuliert und dann
        abgespielt, sondern jeder Zeitschritt synchron ausgeführt:
          1. vdsim berechnet einen Schritt (Planer, Regler, Fahrzeugmodell)
          2. Die neue Ego-Position wird an CARLA übertragen
          3. CARLA rendert und liefert Sensorbilder
          4. Optional: Sensorbilder → vdsim-Perception
        """
        from ..ad.runner import _spec_dict, _road_geometry, _Recorder, _apply_kicks
        from ..ad.results import ADResult
        from ..ad.stack import build_graph, merge_stack
        from ..runtime import Executor, Graph
        from ..world import build_scenario as build_scen
        from ..framework.types import WorldState
        import math

        conn = connect(self.host, self.port)
        if self.map_name:
            conn.load_map(self.map_name)

        spec = _spec_dict(self.scenario_name)
        inst = build_scen(spec, seed=self.seed)
        vehicle_cfg = load_vehicle_preset(self.vehicle_name or getattr(inst, "vehicle", "mid_size_sedan"))

        full_stack = merge_stack(
            (spec.get("stack") if isinstance(spec, dict) else None),
            self.stack_override,
        )
        g_dict = build_graph(full_stack)
        g = Graph.from_dict(g_dict)
        g.validate().raise_for_errors()

        dt = g.base_dt
        conn.set_synchronous(dt=dt)
        conn.set_weather(self.weather)
        conn.cleanup_actors()

        context = RunContext(dt=dt, seed=self.seed, vehicle=vehicle_cfg, road=inst.road, scenario=inst)
        ex = Executor(g, context, recorder=False)
        res = ADResult(self.scenario_name, spec if isinstance(spec, dict) else {}, full_stack, self.seed)
        rec = _Recorder(res, ex, True, vehicle_cfg)
        ex.add_listener(step=rec)

        t_end = float(duration or getattr(inst, "duration", None) or 30.0)

        mgr = ActorManager(conn)
        rig = None

        ex.reset()
        ego = ex.values.get("plant.ego")
        if ego:
            mgr.spawn_ego(ego)

        if sensors and mgr.handles.get(0) and mgr.handles[0].carla_actor:
            rig = SensorRig(conn, mgr.handles[0].carla_actor, save_dir)
            for s in sensors:
                rig.attach(s)

        log.info("Online-Kosimulation: %.1f s, dt=%.3f s", t_end, dt)

        try:
            while ex.t < t_end - 1e-9:
                ex.step()
                _apply_kicks(ex, rec)

                ego = ex.values.get("plant.ego")
                if ego is not None:
                    mgr.update_ego(ego)

                    if not all(math.isfinite(getattr(ego, f)) for f in ("x", "y", "vx", "psi")):
                        break

                world = ex.values.get("world.world")
                if isinstance(world, WorldState):
                    mgr.update_objects(world.objects)
                    mgr.update_traffic_lights(world.traffic_lights)

                    if rec.collision:
                        break

                conn.tick()

                if self.follow_ego and mgr.handles.get(0) and mgr.handles[0].carla_actor:
                    tf = mgr.handles[0].carla_actor.get_transform()
                    conn.spectator_follow(tf, self.camera_z, self.camera_pitch)

                if progress:
                    progress(ex.t, t_end)

        except KeyboardInterrupt:
            log.info("Kosimulation abgebrochen bei t=%.1f s", ex.t)
        finally:
            ex.close()
            if rig:
                rig.destroy_all()
            mgr.destroy_all()

        res.road = _road_geometry(inst.road)
        res.finalize()
        from ..research.metrics import evaluate
        evaluate(res)
        log.info("Online-Kosimulation beendet: %d Schritte, %.1f s", len(res._rows or []), ex.t)
        return res
