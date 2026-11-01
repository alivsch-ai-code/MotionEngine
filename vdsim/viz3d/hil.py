"""Hardware-in-the-Loop (HIL) Vorbereitung.

Dieses Modul definiert die Schnittstellen, um vdsim an reale oder
HIL-Hardware anzubinden:

  1. **SIL** (Software-in-the-Loop, aktuell):
     Alles in Python, CARLA optional für 3D-Rendering.

  2. **MIL** (Model-in-the-Loop):
     vdsim-Fahrzeugmodell gegen MATLAB/Simulink-Modell austauschen.
     → vdsim.matlab.component.MATLABNode als Vehicle-Plant einsetzen.

  3. **HIL** (Hardware-in-the-Loop):
     vdsim-Controller als C/C++ kompilieren (vdsim.runtime.build),
     auf einem Echtzeit-Rechner (dSPACE, ETAS, Speedgoat) ausführen,
     und über CAN/Ethernet mit dem Prüfstand kommunizieren.

  4. **VIL** (Vehicle-in-the-Loop):
     vdsim-Planer + CARLA-Rendering auf dem Fahrzeugrechner,
     Sensorbilder von CARLA statt echter Kameras (closed-loop Validierung
     vor der Realfahrt).

Für Stufe 3/4 exportiert dieses Modul die Stellgrößen-Schnittstelle als
standardisierte Signale (CAN-DBC, Protobuf, ROS2-Nachrichten).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np

from ..framework.types import ActuatorCommand, ControlCommand, EgoState


@dataclass
class CANSignal:
    name: str
    start_bit: int
    length: int
    scale: float = 1.0
    offset: float = 0.0
    unit: str = ""
    byte_order: str = "little_endian"


CONTROL_CAN_SIGNALS = {
    0x100: [
        CANSignal("steer_angle", 0, 16, 0.001, 0.0, "rad"),
        CANSignal("steer_rate", 16, 16, 0.001, 0.0, "rad/s"),
        CANSignal("accel_request", 32, 16, 0.01, -10.0, "m/s^2"),
        CANSignal("direction", 48, 8, 1.0, 0.0, ""),
    ],
    0x101: [
        CANSignal("drive_torque_fl", 0, 16, 0.1, 0.0, "Nm"),
        CANSignal("drive_torque_fr", 16, 16, 0.1, 0.0, "Nm"),
        CANSignal("drive_torque_rl", 32, 16, 0.1, 0.0, "Nm"),
        CANSignal("drive_torque_rr", 48, 16, 0.1, 0.0, "Nm"),
    ],
    0x102: [
        CANSignal("brake_torque_fl", 0, 16, 0.1, 0.0, "Nm"),
        CANSignal("brake_torque_fr", 16, 16, 0.1, 0.0, "Nm"),
        CANSignal("brake_torque_rl", 32, 16, 0.1, 0.0, "Nm"),
        CANSignal("brake_torque_rr", 48, 16, 0.1, 0.0, "Nm"),
    ],
}

EGO_CAN_SIGNALS = {
    0x200: [
        CANSignal("x", 0, 32, 0.001, 0.0, "m"),
        CANSignal("y", 32, 32, 0.001, 0.0, "m"),
    ],
    0x201: [
        CANSignal("psi", 0, 16, 0.0001, 0.0, "rad"),
        CANSignal("vx", 16, 16, 0.01, 0.0, "m/s"),
        CANSignal("vy", 32, 16, 0.01, 0.0, "m/s"),
        CANSignal("yaw_rate", 48, 16, 0.001, 0.0, "rad/s"),
    ],
}


def control_to_can(cmd):
    """ControlCommand / ActuatorCommand → CAN-Bytes (dict message_id → 8 bytes)."""
    messages = {}
    if isinstance(cmd, ControlCommand):
        data = bytearray(8)
        _pack16(data, 0, cmd.steer_angle or 0.0, 0.001, 0.0)
        _pack16(data, 2, cmd.steer_rate or 0.0, 0.001, 0.0)
        _pack16(data, 4, cmd.accel or 0.0, 0.01, -10.0)
        data[6] = max(min(cmd.direction, 1), -1) + 1
        messages[0x100] = bytes(data)
    elif isinstance(cmd, ActuatorCommand):
        for msg_id, torques in ((0x101, cmd.drive_torque), (0x102, cmd.brake_torque)):
            data = bytearray(8)
            for i in range(4):
                _pack16(data, i * 2, float(torques[i]), 0.1, 0.0)
            messages[msg_id] = bytes(data)
    return messages


def ego_from_can(messages):
    """CAN-Bytes (dict message_id → bytes) → EgoState."""
    ego = EgoState()
    if 0x200 in messages:
        d = messages[0x200]
        ego.x = _unpack32(d, 0, 0.001, 0.0)
        ego.y = _unpack32(d, 4, 0.001, 0.0)
    if 0x201 in messages:
        d = messages[0x201]
        ego.psi = _unpack16(d, 0, 0.0001, 0.0)
        ego.vx = _unpack16(d, 2, 0.01, 0.0)
        ego.vy = _unpack16(d, 4, 0.01, 0.0)
        ego.r = _unpack16(d, 6, 0.001, 0.0)
    return ego


def _pack16(buf, offset, value, scale, phys_offset):
    raw = int(round((value - phys_offset) / scale))
    struct.pack_into("<h", buf, offset, max(-32768, min(32767, raw)))


def _unpack16(buf, offset, scale, phys_offset):
    return struct.unpack_from("<h", buf, offset)[0] * scale + phys_offset


def _unpack32(buf, offset, scale, phys_offset):
    return struct.unpack_from("<i", buf, offset)[0] * scale + phys_offset


def generate_dbc(path="vdsim_control.dbc"):
    """Generiert eine CAN-DBC-Datei für die Stellgrößen- und Zustandssignale."""
    lines = ['VERSION ""', "", "NS_ :", "", "BS_:", "", "BU_: vdsim vehicle", ""]
    for msg_id, signals in {**CONTROL_CAN_SIGNALS, **EGO_CAN_SIGNALS}.items():
        name = f"vdsim_{msg_id:03X}"
        sender = "vdsim" if msg_id < 0x200 else "vehicle"
        lines.append(f'BO_ {msg_id} {name}: 8 {sender}')
        for s in signals:
            bo = 1 if s.byte_order == "big_endian" else 0
            lines.append(f' SG_ {s.name} : {s.start_bit}|{s.length}@{1 - bo}+ '
                         f'({s.scale},{s.offset}) [0|0] "{s.unit}" Vector__XXX')
        lines.append("")
    from pathlib import Path
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return path
