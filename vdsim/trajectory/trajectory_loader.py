"""Trajectory import: CSV, JSON, GPS (CSV/GPX/NMEA), MATLAB, ROS nav_msgs/Path, OpenDRIVE."""

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from ..core.registry import get, register
from .opendrive import load_opendrive
from .trajectory import Trajectory

EARTH_RADIUS = 6371000.0


def geodetic_to_local(lat, lon, lat0=None, lon0=None):
    # Equirectangular projection around the first point (accurate for test tracks of a few km)
    lat, lon = np.asarray(lat, dtype=float), np.asarray(lon, dtype=float)
    lat0 = lat[0] if lat0 is None else lat0
    lon0 = lon[0] if lon0 is None else lon0
    x = np.radians(lon - lon0) * EARTH_RADIUS * np.cos(np.radians(lat0))
    y = np.radians(lat - lat0) * EARTH_RADIUS
    return x, y


def _speed_from_time(x, y, t):
    t = np.asarray(t, dtype=float)
    if len(t) < 2 or np.any(np.diff(t) <= 0):
        return None
    ds = np.hypot(np.diff(x), np.diff(y))
    v = ds / np.diff(t)
    return np.concatenate([v[:1], (v[1:] + v[:-1]) / 2, v[-1:]])


def _columns(header):
    return {name.strip().lower(): i for i, name in enumerate(header)}


@register("trajectory_loader", "csv")
def load_csv(path, speed=None, **_):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [row for row in csv.reader(f) if row and not row[0].startswith("#")]
    cols = _columns(rows[0])
    data = np.array([[float(v) if v.strip() else np.nan for v in row] for row in rows[1:]])

    def col(*names):
        for name in names:
            for key, idx in cols.items():
                if key == name or key.endswith(name):
                    return data[:, idx]
        return None

    lat, lon = col("lat", "latitude"), col("lon", "lng", "longitude")
    if lat is not None and lon is not None:
        x, y = geodetic_to_local(lat, lon)
        source = "gps"
    else:
        x, y = col("x", "pose.position.x", "position.x"), col("y", "pose.position.y", "position.y")
        source = "csv"
        if x is None or y is None:
            raise ValueError(f"CSV needs x/y or lat/lon columns, found {list(cols)}")
    v = col("v", "speed", "velocity")
    v_kmh = col("v_kmh", "speed_kmh")
    if v_kmh is not None:
        v = v_kmh / 3.6
    if v is None:
        t = col("t", "time", "timestamp", "%time")
        if t is not None and np.nanmax(t) > 1e12:
            t = t * 1e-9  # ROS nanoseconds
        v = _speed_from_time(x, y, t) if t is not None else None
    traj = Trajectory(x, y, v if v is not None else speed, name=Path(path).stem)
    traj.metadata["source"] = source
    return traj


@register("trajectory_loader", "json")
def load_json(path, speed=None, **_):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "poses" in data:
        return _ros_path(data, Path(path).stem, speed)
    if isinstance(data, dict) and "x" in data and "y" in data:
        traj = Trajectory.from_dict(data)
        if speed is not None and "v" not in data:
            traj.v[:] = speed
        return traj
    points = data.get("waypoints", data) if isinstance(data, dict) else data
    x = [p["x"] for p in points]
    y = [p["y"] for p in points]
    v = [p.get("v", p.get("v_kmh", 36.0) / 3.6) for p in points]
    return Trajectory(x, y, v, name=Path(path).stem)


def _ros_path(msg, name, speed=None):
    poses = msg["poses"]
    x = [p["pose"]["position"]["x"] for p in poses]
    y = [p["pose"]["position"]["y"] for p in poses]
    stamps = []
    for p in poses:
        stamp = p.get("header", {}).get("stamp")
        if isinstance(stamp, dict):
            stamps.append(stamp.get("secs", stamp.get("sec", 0)) + 1e-9 * stamp.get("nsecs", stamp.get("nanosec", 0)))
    v = _speed_from_time(x, y, stamps) if len(stamps) == len(poses) else None
    traj = Trajectory(x, y, v if v is not None else speed, name=name)
    traj.metadata["source"] = "ros"
    return traj


@register("trajectory_loader", "ros")
def load_ros(path, speed=None, **_):
    # nav_msgs/Path as YAML (rostopic echo / ros2 topic echo) or JSON
    import yaml
    text = Path(path).read_text(encoding="utf-8")
    for doc in yaml.safe_load_all(text):
        if isinstance(doc, dict) and "poses" in doc:
            return _ros_path(doc, Path(path).stem, speed)
    raise ValueError("no nav_msgs/Path with 'poses' found")


@register("trajectory_loader", "gpx")
def load_gpx(path, speed=None, **_):
    root = ET.parse(path).getroot()
    ns = {"g": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else {}
    tag = "g:trkpt" if ns else "trkpt"
    points = root.findall(f".//{tag}", ns) or root.findall(".//g:rtept" if ns else ".//rtept", ns)
    lat = [float(p.get("lat")) for p in points]
    lon = [float(p.get("lon")) for p in points]
    x, y = geodetic_to_local(lat, lon)
    times = []
    for p in points:
        el = p.find("g:time" if ns else "time", ns)
        if el is not None:
            from datetime import datetime
            times.append(datetime.fromisoformat(el.text.replace("Z", "+00:00")).timestamp())
    v = _speed_from_time(x, y, times) if len(times) == len(points) else None
    traj = Trajectory(x, y, v if v is not None else speed, name=Path(path).stem)
    traj.metadata["source"] = "gps"
    return traj


@register("trajectory_loader", "nmea")
def load_nmea(path, speed=None, **_):
    # $GPRMC / $GNRMC sentences (position + speed over ground)
    lat, lon, v = [], [], []
    for line in Path(path).read_text(encoding="ascii", errors="ignore").splitlines():
        parts = line.strip().split("*")[0].split(",")
        if len(parts) > 7 and parts[0][3:] == "RMC" and parts[2] == "A":
            la = float(parts[3][:2]) + float(parts[3][2:]) / 60
            lo = float(parts[5][:3]) + float(parts[5][3:]) / 60
            lat.append(-la if parts[4] == "S" else la)
            lon.append(-lo if parts[6] == "W" else lo)
            v.append(float(parts[7] or 0.0) * 0.514444)
    x, y = geodetic_to_local(lat, lon)
    traj = Trajectory(x, y, v, name=Path(path).stem)
    traj.metadata["source"] = "gps"
    return traj


@register("trajectory_loader", "matlab")
def load_matlab(path, speed=None, **_):
    # .mat (v5/v7) with variables x, y[, v] or a struct with these fields, or an N x 2/3 matrix
    from scipy.io import loadmat
    data = {k: v for k, v in loadmat(path, squeeze_me=True, struct_as_record=False).items() if not k.startswith("__")}
    for value in list(data.values()):
        if hasattr(value, "_fieldnames"):
            data.update({f: getattr(value, f) for f in value._fieldnames})
    traj = None
    if "x" in data and "y" in data:
        v = data.get("v", data.get("speed", speed))
        traj = Trajectory(np.ravel(data["x"]), np.ravel(data["y"]), None if v is None else np.ravel(v) if np.ndim(v) else v,
                          name=Path(path).stem)
    else:
        for value in data.values():
            arr = np.asarray(value)
            if arr.ndim == 2 and arr.shape[1] in (2, 3):
                traj = Trajectory(arr[:, 0], arr[:, 1], arr[:, 2] if arr.shape[1] == 3 else speed, name=Path(path).stem)
                break
    if traj is not None:
        traj.metadata["source"] = "matlab"
        return traj
    raise ValueError(f"no trajectory found in {path}, variables: {list(data)}")


@register("trajectory_loader", "opendrive")
def load_xodr(path, speed=None, road_id=None, lane_id=-1, **_):
    return load_opendrive(path, road_id=road_id, lane_id=lane_id, speed_kmh=speed * 3.6 if speed else None)


EXTENSIONS = {".csv": "csv", ".json": "json", ".gpx": "gpx", ".nmea": "nmea", ".mat": "matlab",
              ".yaml": "ros", ".yml": "ros", ".xodr": "opendrive"}
FILE_FILTER = ("Trajektorien (*.csv *.json *.gpx *.nmea *.mat *.yaml *.yml *.xodr);;CSV (*.csv);;JSON (*.json);;"
               "GPS (*.gpx *.nmea *.csv);;MATLAB (*.mat);;ROS nav_msgs/Path (*.yaml *.yml *.json);;OpenDRIVE (*.xodr)")


def load_trajectory(path, speed=None, **options):
    # speed (m/s) is used when the file has no speed information
    path = Path(path)
    kind = EXTENSIONS.get(path.suffix.lower())
    if kind is None:
        raise ValueError(f"unsupported trajectory format '{path.suffix}', supported: {sorted(EXTENSIONS)}")
    traj = get("trajectory_loader", kind)(path, speed=speed, **options)
    traj.metadata.setdefault("file", str(path))
    return traj
