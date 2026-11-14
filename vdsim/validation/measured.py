"""Lateral dynamics of the single-track model against measurements of real cars.

Data: commaSteeringControl (comma.ai, MIT license), logs of production cars at 10 Hz with the measured
speed, steering wheel angle, road roll and lateral acceleration (from the device's localizer).
Vehicle parameters: the public specifications of the same project (opendbc): wheelbase, steering ratio,
position of the center of gravity, and axle cornering stiffness and yaw inertia scaled from a reference
car. Nothing is fitted to the measurements.

    cfg = vehicle_config(PublicSpecs(wheelbase=2.84, steer_ratio=13.56))
    segments = load_segments("GENESIS_G70_2018.zip")
    result = compare(cfg, segments)

The model is replayed open loop: the measured steering angle and speed are the inputs, the lateral
acceleration is the output. Two predictions are compared with the measurement:

    steady   a_y = v^2 delta / (l + EG v^2)                 (steady-state gain of the linear single-track model)
    dynamic  [v_y, r]' = A(v) [v_y, r] + B(v) delta,  a_y = v r + v_y'   (the same model with its dynamics)

Conventions of the data set: a positive steering angle (to the left) gives a negative lateral acceleration,
so the model output is negated. The road roll is not used: with fixed parameters the roll compensation of
the reference model did not reduce the error on this data.

Steering angle offset: the zero of a steering angle sensor is off by a fraction of a degree in every car.
The data source estimates it while driving and does not publish it. `compare` reports the result without
any correction and, separately, with one offset per drive estimated from the data (`calibrate_offset`).
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..analysis import LinearSingleTrackAnalysis
from ..core.parameters import load_vehicle_preset

# reference car of the parameter source (opendbc, VehicleDynamicsParams): axle stiffness and inertia are
# scaled from these values to another car
REF_MASS, REF_WHEELBASE, REF_FRONT_SHARE = 1462.0, 2.70, 0.4
REF_STIFFNESS_FRONT, REF_STIFFNESS_REAR, REF_INERTIA = 192150.0, 202500.0, 2500.0
COLUMNS = ("t", "vEgo", "steeringAngleDeg", "roll", "latAccelLocalizer", "latAccelSteeringAngle")


@dataclass
class PublicSpecs:
    wheelbase: float                      # m
    steer_ratio: float                    # steering wheel angle / road-wheel angle
    center_to_front_ratio: float = 0.4    # distance CoG - front axle / wheelbase
    tire_stiffness_factor: float = 1.0
    mass: float = 1600.0                  # kg; cancels in the lateral model (stiffness and inertia scale with it)


def vehicle_config(specs, preset="mid_size_sedan"):
    """VehicleConfig with the lateral parameters of a car given by its public specifications."""
    cfg = load_vehicle_preset(preset)
    v, t = cfg.vehicle, cfg.tires
    lf = specs.wheelbase * specs.center_to_front_ratio
    lr = specs.wheelbase - lf
    scale = specs.mass / REF_MASS
    c_front = REF_STIFFNESS_FRONT * specs.tire_stiffness_factor * scale * (lr / specs.wheelbase) / (1.0 - REF_FRONT_SHARE)
    c_rear = REF_STIFFNESS_REAR * specs.tire_stiffness_factor * scale * (lf / specs.wheelbase) / REF_FRONT_SHARE
    v.mass, v.wheelbase, v.cg_to_front = specs.mass, specs.wheelbase, lf
    v.inertia_z = REF_INERTIA * scale * specs.wheelbase**2 / REF_WHEELBASE**2
    v.steering_ratio = specs.steer_ratio
    t.model = "linear"
    t.cornering_stiffness_front, t.cornering_stiffness_rear = c_front / 2.0, c_rear / 2.0      # per tire
    # the tire model changes the stiffness with the wheel load: scale the parameters until the axle stiffness of
    # the single-track model is the specified one
    for _ in range(3):
        model = LinearSingleTrackAnalysis(cfg).model
        t.cornering_stiffness_front *= c_front / model.c_front
        t.cornering_stiffness_rear *= c_rear / model.c_rear
    return cfg


def load_segments(path, limit=None):
    """Segments of one platform: the zip file of the data set, or a folder with its CSV files."""
    out = []
    if Path(path).is_dir():
        for file in sorted(Path(path).glob("*.csv"))[:limit]:
            with file.open(encoding="utf-8") as f:
                seg = read_csv(f)
            if seg is not None:
                seg["name"] = file.name
                out.append(seg)
        return out
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist() if n.endswith(".csv"))
        for name in names[:limit]:
            with z.open(name) as f:
                seg = read_csv(io.TextIOWrapper(f, encoding="utf-8"))
            if seg is not None:
                seg["name"] = name
                out.append(seg)
    return out


def read_csv(handle):
    rows = list(csv.DictReader(handle))
    if len(rows) < 20 or any(c not in rows[0] for c in COLUMNS):
        return None
    try:
        return {c: np.array([float(r[c]) for r in rows]) for c in COLUMNS}
    except ValueError:
        return None


def predict(cfg, seg, offset_deg=0.0, substeps=5):
    """Lateral acceleration of the single-track model for the measured steering angle and speed."""
    analysis = LinearSingleTrackAnalysis(cfg)
    t, v = seg["t"], np.maximum(seg["vEgo"], 0.1)
    delta = np.radians(seg["steeringAngleDeg"] - offset_deg) / cfg.vehicle.steering_ratio
    eg = analysis.understeer_gradient
    steady = -delta * v**2 / (cfg.vehicle.wheelbase + eg * v**2)
    dynamic = np.zeros_like(t)
    x = None
    for k in range(len(t)):
        A, B = analysis.model.state_space(float(v[k]))
        u = B[:, 0] * delta[k]
        if x is None:
            x = -np.linalg.solve(A, u)                                   # start in steady state
        dt = (t[k] - t[k - 1]) / substeps if k else 0.0
        for _ in range(substeps if k else 0):                            # implicit Euler, stable at 10 Hz data
            x = np.linalg.solve(np.eye(2) - dt * A, x + dt * u)
        dynamic[k] = -((A @ x + u)[0] + v[k] * x[1])
    return {"steady": steady, "dynamic": dynamic}


def calibrate_offset(cfg, seg, v_min=10.0):
    """Steering angle offset of one drive (deg): least-squares fit of the steady-state model to the measurement."""
    analysis = LinearSingleTrackAnalysis(cfg)
    keep = seg["vEgo"] >= v_min
    if keep.sum() < 20:
        return 0.0
    v = seg["vEgo"][keep]
    gain = -(v**2) / (cfg.vehicle.wheelbase + analysis.understeer_gradient * v**2) / cfg.vehicle.steering_ratio
    # measured = gain * rad(angle - offset)  ->  offset = sum(gain * (gain * angle - measured)) / sum(gain^2)
    angle = np.radians(seg["steeringAngleDeg"][keep])
    return float(np.degrees(np.sum(gain * (gain * angle - seg["latAccelLocalizer"][keep])) / np.sum(gain * gain)))


def _metrics(pred, meas):
    err = pred - meas
    var = float(np.var(meas))
    slope = float(np.sum(pred * meas) / max(np.sum(pred * pred), 1e-12))     # measured = slope * predicted
    return {"rmse": float(np.sqrt(np.mean(err**2))), "bias": float(np.mean(err)),
            "r2": float(1.0 - np.mean(err**2) / var) if var > 0 else None, "slope": slope, "n": int(len(meas))}


def compare(cfg, segments, v_min=10.0, speed_bins=(10.0, 20.0, 30.0, 45.0), ay_bins=(0.0, 0.5, 1.0, 2.0, 6.0)):
    """Model against measurement over all segments. Samples below v_min are left out (parking, turning)."""
    cols = {k: [] for k in ("v", "meas", "steady", "dynamic", "reference", "steady_cal", "dynamic_cal")}
    offsets = []
    for seg in segments:
        p = predict(cfg, seg)
        offsets.append(calibrate_offset(cfg, seg, v_min))
        q = predict(cfg, seg, offsets[-1])
        keep = (seg["vEgo"] >= v_min) & np.isfinite(seg["latAccelLocalizer"])
        for key, arr in (("v", seg["vEgo"]), ("meas", seg["latAccelLocalizer"]), ("steady", p["steady"]), ("dynamic", p["dynamic"]),
                         ("reference", seg["latAccelSteeringAngle"]), ("steady_cal", q["steady"]), ("dynamic_cal", q["dynamic"])):
            cols[key].append(arr[keep])
    c = {k: np.concatenate(v) if v else np.zeros(0) for k, v in cols.items()}
    n = len(c["v"])
    out = {"segments": len(segments), "samples": int(n), "hours": float(n / 36000.0),
           "measured_rms": float(np.sqrt(np.mean(c["meas"] ** 2))) if n else 0.0,
           "measured_max": float(np.max(np.abs(c["meas"]))) if n else 0.0,
           "steady": _metrics(c["steady"], c["meas"]), "dynamic": _metrics(c["dynamic"], c["meas"]),
           "steady_calibrated": _metrics(c["steady_cal"], c["meas"]), "dynamic_calibrated": _metrics(c["dynamic_cal"], c["meas"]),
           "offset_deg": {"mean": float(np.mean(offsets)), "std": float(np.std(offsets))} if offsets else None,
           "reference_model": _metrics(c["reference"], c["meas"]), "by_speed": [], "by_lateral_acceleration": []}
    for name, bins, x in (("by_speed", speed_bins, c["v"]), ("by_lateral_acceleration", ay_bins, np.abs(c["meas"]))):
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = (x >= lo) & (x < hi)
            if m.sum() > 50:
                out[name].append({"from": lo, "to": hi, "uncalibrated": _metrics(c["dynamic"][m], c["meas"][m]),
                                  "calibrated": _metrics(c["dynamic_cal"][m], c["meas"][m])})
    return out
