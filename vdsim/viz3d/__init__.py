"""3D-Visualisierung der vdsim-Simulation via CARLA (Open Source, Unreal Engine).

Zwei Betriebsmodi:

    Replay       ADResult aus einer abgeschlossenen Simulation in CARLA abspielen
                 (kamera-verfolgt, freie Kamera, Vogelperspektive)

    CoSim        vdsim und CARLA laufen synchron: CARLA rendert und liefert optional
                 synthetische Sensordaten (Kamera, LiDAR, Radar), vdsim steuert
                 Planung und Regelung

Voraussetzung: CARLA >= 0.9.15 (Server + Python-Client-Bibliothek `carla`)

    pip install carla          # oder CARLA-eigenes .egg / .whl
    # CARLA-Server starten:   ./CarlaUE4.sh -RenderOffScreen  (Linux)
    #                         CarlaUE4.exe                     (Windows)

Einstieg:

    from vdsim.viz3d import replay, cosim

    # Modus A: Replay einer fertigen Simulation
    result = run_scenario("werling_highway")
    replay.play(result, follow_ego=True, speed=1.0)

    # Modus B: Kosimulation
    bridge = cosim.CARLABridge(scenario="werling_highway")
    bridge.run(duration=48.0, sensors=["camera_front", "lidar_top"])
"""

from .connection import connect, CARLAConnection
from . import replay, cosim, road_export, sensors

__all__ = ["connect", "CARLAConnection", "replay", "cosim", "road_export", "sensors"]
