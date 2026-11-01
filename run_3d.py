#!/usr/bin/env python
"""3D-Visualisierung der vdsim-Simulation in CARLA.

Voraussetzungen:
    1. CARLA >= 0.9.15 installiert und Server gestartet
    2. pip install carla numpy

Aufruf:
    python run_3d.py                          # Replay: werling_highway
    python run_3d.py --scenario cut_in        # anderes Szenario
    python run_3d.py --mode online            # Echtzeit-Kosimulation
    python run_3d.py --sensors camera_front lidar_top --save-dir ./output
    python run_3d.py --speed 0.5              # Zeitlupe
    python run_3d.py --weather CloudyNoon     # Bewölkt
    python run_3d.py --map Town04             # bestimmte CARLA-Karte
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="vdsim 3D-Visualisierung via CARLA")
    parser.add_argument("--scenario", default="werling_highway", help="Szenarioname (default: werling_highway)")
    parser.add_argument("--mode", choices=["replay", "online"], default="replay",
                        help="replay = erst simulieren, dann abspielen; online = synchrone Kosimulation")
    parser.add_argument("--duration", type=float, default=None, help="Simulationsdauer (s)")
    parser.add_argument("--speed", type=float, default=1.0, help="Abspielgeschwindigkeit (nur replay)")
    parser.add_argument("--host", default="localhost", help="CARLA-Server Host")
    parser.add_argument("--port", type=int, default=2000, help="CARLA-Server Port")
    parser.add_argument("--map", default=None, help="CARLA-Karte (z.B. Town04)")
    parser.add_argument("--weather", default="ClearNoon",
                        help="Wetter-Preset (ClearNoon, CloudyNoon, WetNoon, HardRainNoon, SoftRainSunset, ...)")
    parser.add_argument("--sensors", nargs="*", default=None,
                        help="Sensor-Presets (camera_front, camera_rear, depth_front, semantic_front, lidar_top, radar_front)")
    parser.add_argument("--save-dir", default=None, help="Verzeichnis für Sensor-Aufnahmen")
    parser.add_argument("--no-follow", action="store_true", help="Kamera folgt dem Ego nicht")
    parser.add_argument("--camera-z", type=float, default=15.0, help="Kamerahöhe über dem Ego (m)")
    parser.add_argument("--camera-pitch", type=float, default=-60.0, help="Kameraneigung (Grad)")
    parser.add_argument("--seed", type=int, default=0, help="Zufalls-Seed")
    args = parser.parse_args()

    try:
        import carla
    except ImportError:
        print("FEHLER: Python-Paket 'carla' nicht gefunden.")
        print()
        print("Installation:")
        print("  pip install carla")
        print()
        print("Oder CARLA-eigenes Egg/Whl einbinden:")
        print("  sys.path.append('<CARLA_ROOT>/PythonAPI/carla/dist/carla-0.9.15-py3.10-win-amd64.egg')")
        print()
        print("CARLA-Server herunterladen:")
        print("  https://github.com/carla-simulator/carla/releases")
        sys.exit(1)

    if args.mode == "replay":
        print(f"Simulation von '{args.scenario}' ...")
        from vdsim.ad import run_scenario
        result = run_scenario(args.scenario, seed=args.seed, duration=args.duration, record_snapshots=True)
        print(f"Simulation abgeschlossen: {result.metadata.get('stop_reason', '?')}")
        print(f"  Dauer: {result.duration:.1f} s, KPIs: {len(result.kpis)}")
        print()
        print(f"Replay in CARLA ({args.host}:{args.port}) ...")
        from vdsim.viz3d.replay import play
        play(result, host=args.host, port=args.port, speed=args.speed,
             follow_ego=not args.no_follow, camera_z=args.camera_z, camera_pitch=args.camera_pitch,
             map_name=args.map, sensors=args.sensors, save_dir=args.save_dir, weather=args.weather)

    elif args.mode == "online":
        print(f"Online-Kosimulation von '{args.scenario}' in CARLA ...")
        from vdsim.viz3d.cosim import CARLABridge
        bridge = CARLABridge(
            scenario=args.scenario, seed=args.seed,
            host=args.host, port=args.port, map_name=args.map, weather=args.weather,
            follow_ego=not args.no_follow, camera_z=args.camera_z, camera_pitch=args.camera_pitch,
        )
        result = bridge.run_online(
            duration=args.duration, sensors=args.sensors, save_dir=args.save_dir,
            progress=lambda t, te: print(f"\r  t={t:.1f}/{te:.1f} s", end="", flush=True),
        )
        print()
        print(f"Kosimulation beendet: {result.metadata.get('stop_reason', '?')}")
        for k, v in sorted(result.kpis.items()):
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}")


if __name__ == "__main__":
    main()
