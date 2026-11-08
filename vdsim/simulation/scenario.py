"""Scenario definition (JSON) and scenario management."""

import inspect
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..core.logging_setup import get_logger
from ..core.parameters import VehicleConfig, default_config_dir, load_vehicle_preset
from ..core.registry import get

log = get_logger("scenario")


@dataclass
class Scenario:
    name: str = "Neues Szenario"
    description: str = ""
    vehicle: object = "mid_size_sedan"           # preset name or full VehicleConfig dict
    vehicle_overrides: dict = field(default_factory=dict)  # e.g. {"tires.mu": 0.8}
    model: str = "double_track"
    maneuver: str = "iso_double_lane_change"
    maneuver_params: dict = field(default_factory=dict)
    trajectory_file: str = ""                    # imported trajectory instead of a maneuver
    trajectory_options: dict = field(default_factory=dict)
    lateral_controller: str = "stanley"
    lateral_params: dict = field(default_factory=dict)
    longitudinal_controller: str = "speed_pi"
    longitudinal_params: dict = field(default_factory=dict)
    steering_actuator: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    duration: float = 0.0                        # 0 = automatic
    dt_control: float = 0.01
    dt_model: float = 0.0                        # 0 = recommended step of the model
    solver: str = "rk4"
    initial_speed: float = None                  # m/s, None = speed of the trajectory start

    # building blocks
    def build_config(self):
        config = (VehicleConfig.from_dict(self.vehicle) if isinstance(self.vehicle, dict)
                  else load_vehicle_preset(self.vehicle))
        for dotted, value in self.vehicle_overrides.items():
            group, name = dotted.split(".", 1)
            target = getattr(config, group)
            # dataclasses accept any attribute: a typo would silently leave the parameter unchanged
            if name not in getattr(target, "__dataclass_fields__", {}):
                raise AttributeError(f"unknown vehicle parameter '{dotted}'")
            setattr(target, name, value)
        return config

    def build_trajectory(self, config=None):
        from ..trajectory import load_trajectory
        if self.trajectory_file:
            return load_trajectory(self.trajectory_file, **self.trajectory_options)
        fn = get("maneuver", self.maneuver)
        params = dict(self.maneuver_params)
        accepted = inspect.signature(fn).parameters
        if config is not None:
            if "steering_ratio" in accepted:
                params.setdefault("steering_ratio", config.vehicle.steering_ratio)
            if "vehicle_width" in accepted:
                params.setdefault("vehicle_width", config.vehicle.width)
        return fn(**params)

    # serialization
    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(data) - known
        if unknown:
            log.warning("ignoring unknown scenario keys %s", sorted(unknown))
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


class ScenarioManager:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory else default_config_dir() / "scenarios"
        self.directory.mkdir(parents=True, exist_ok=True)

    def names(self):
        return sorted(p.stem for p in self.directory.glob("*.json"))

    def path(self, name):
        return self.directory / f"{name}.json"

    def load(self, name):
        return Scenario.load(self.path(name))

    def save(self, scenario, name=None):
        name = name or _slug(scenario.name)
        scenario.save(self.path(name))
        return name

    def delete(self, name):
        self.path(name).unlink(missing_ok=True)

    def all(self):
        return {name: self.load(name) for name in self.names()}


def _slug(text):
    keep = "".join(c.lower() if c.isalnum() else "_" for c in text)
    return "_".join(filter(None, keep.split("_"))) or "scenario"
