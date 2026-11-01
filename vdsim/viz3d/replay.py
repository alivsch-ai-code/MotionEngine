"""Modus A: Replay einer fertigen vdsim-Simulation in CARLA.

    from vdsim.ad import run_scenario
    from vdsim.viz3d.replay import play

    result = run_scenario("werling_highway", record_snapshots=True)
    play(result, speed=1.0, follow_ego=True, sensors=["camera_front"])

Der CARLA-Server muss laufen. Die Simulation wird Tick-für-Tick abgespielt;
Fahrzeuge und Fußgänger bewegen sich synchron zu den aufgezeichneten Positionen.
Optional werden Sensoren am Ego montiert und die Frames gespeichert.
"""

from __future__ import annotations

import time

import numpy as np

from ..core.logging_setup import get_logger
from .actor_sync import ActorManager
from .connection import connect
from .road_export import suggest_carla_map
from .sensors import SensorRig

log = get_logger("viz3d.replay")


def play(result, host="localhost", port=2000, speed=1.0, follow_ego=True,
         camera_z=15.0, camera_pitch=-60.0, map_name=None, use_opendrive=False,
         sensors=None, save_dir=None, on_frame=None, weather="ClearNoon"):
    """Spielt ein ADResult in CARLA ab.

    Args:
        result:         ADResult aus vdsim.ad.run_scenario
        speed:          Abspielgeschwindigkeit (1.0 = Echtzeit, 2.0 = doppelt)
        follow_ego:     Spectator-Kamera folgt dem Ego
        map_name:       CARLA-Karte (None = automatisch nach Szenariotyp)
        use_opendrive:  True = vdsim-Straßennetz als OpenDRIVE laden
        sensors:        Liste von Sensor-Preset-Namen (z. B. ["camera_front", "lidar_top"])
        save_dir:       Verzeichnis für Sensor-Frames (None = kein Speichern)
        on_frame:       Callback(t, ego_state, sensor_rig) pro Tick
        weather:        CARLA WeatherParameters Preset
    """
    from ..framework.types import EgoState, ObjectState

    conn = connect(host, port)
    signals = result.signals
    t_arr = signals["t"]
    dt = float(np.median(np.diff(t_arr)))
    n = len(t_arr)

    if use_opendrive and result.road:
        from .road_export import road_to_opendrive
        xodr = road_to_opendrive(result.road)
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(suffix=".xodr", delete=False, mode="w", encoding="utf-8") as f:
            f.write(xodr)
            conn.load_opendrive(f.name)
    elif map_name:
        conn.load_map(map_name)
    else:
        town = suggest_carla_map(type("R", (), {"name": result.scenario.get("type", "highway"), "lanes": {}}))
        log.info("Automatische Kartenwahl: %s (Szenariotyp: %s)", town, result.scenario.get("type", ""))

    conn.set_synchronous(dt=dt)
    conn.set_weather(weather)
    conn.cleanup_actors()

    mgr = ActorManager(conn)
    ego0 = _ego_at(signals, 0)
    mgr.spawn_ego(ego0)

    obj_times = {}
    for oid, rec in result.objects.items():
        obj_times[oid] = (np.array(rec["t"]), np.array(rec["x"]), np.array(rec["y"]),
                          np.array(rec["psi"]), rec.get("type", "car"), float(rec.get("length", 4.5)),
                          float(rec.get("width", 1.8)))

    rig = None
    if sensors and mgr.handles.get(0) and mgr.handles[0].carla_actor:
        rig = SensorRig(conn, mgr.handles[0].carla_actor, save_dir)
        for s in sensors:
            rig.attach(s)

    log.info("Replay: %.1f s, %d Schritte, dt=%.3f s, speed=%.1fx", t_arr[-1] - t_arr[0], n, dt, speed)
    wall_dt = dt / max(speed, 0.01)

    try:
        for k in range(n):
            t = float(t_arr[k])
            wall0 = time.perf_counter()

            ego = _ego_at(signals, k)
            mgr.update_ego(ego)

            objs = _objects_at(obj_times, t)
            mgr.update_objects(objs)

            tl = {}
            if "collision" in signals:
                pass
            mgr.update_traffic_lights(tl)

            conn.tick()

            if follow_ego:
                import carla
                tf = mgr.handles[0].carla_actor.get_transform()
                conn.spectator_follow(tf, camera_z, camera_pitch)

            if on_frame and rig:
                on_frame(t, ego, rig)

            elapsed = time.perf_counter() - wall0
            sleep = wall_dt - elapsed
            if sleep > 0.001:
                time.sleep(sleep)

    except KeyboardInterrupt:
        log.info("Replay abgebrochen bei t=%.1f s", t)
    finally:
        if rig:
            rig.destroy_all()
        mgr.destroy_all()
        log.info("Replay beendet")


def _ego_at(signals, k):
    from ..framework.types import EgoState
    return EgoState(
        t=float(signals["t"][k]),
        x=float(signals.get("ego_x", [0])[min(k, len(signals.get("ego_x", [0])) - 1)]),
        y=float(signals.get("ego_y", [0])[min(k, len(signals.get("ego_y", [0])) - 1)]),
        psi=float(signals.get("ego_psi", [0])[min(k, len(signals.get("ego_psi", [0])) - 1)]),
        vx=float(signals.get("ego_vx", [0])[min(k, len(signals.get("ego_vx", [0])) - 1)]),
    )


def _objects_at(obj_times, t):
    from ..framework.types import ObjectState
    out = []
    for oid, (ts, xs, ys, psis, otype, length, width) in obj_times.items():
        if len(ts) == 0 or t < ts[0] - 0.5 or t > ts[-1] + 0.5:
            continue
        out.append(ObjectState(
            id=oid, type=otype, length=length, width=width,
            x=float(np.interp(t, ts, xs)),
            y=float(np.interp(t, ts, ys)),
            psi=float(np.interp(t, ts, np.unwrap(psis))),
        ))
    return out
