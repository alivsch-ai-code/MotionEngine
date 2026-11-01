"""Environment: road friction maps, wind, road profile and other traffic (lead vehicle)."""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class FrictionPatch:
    # Rectangular area with its own friction coefficient (later patches override earlier ones)
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    mu: float
    name: str = ""


@dataclass
class FrictionMap:
    # Road friction factor relative to dry asphalt (1.0); multiplied with the tire's mu
    base: float = 1.0
    patches: list = field(default_factory=list)
    grid_x: np.ndarray = None   # optional regular grid (bilinear interpolation)
    grid_y: np.ndarray = None
    grid_mu: np.ndarray = None  # shape (len(grid_y), len(grid_x))

    def mu_at(self, x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        mu = np.full(np.broadcast(x, y).shape, self.base)
        if self.grid_mu is not None:
            mu = _bilinear(self.grid_x, self.grid_y, self.grid_mu, x, y)
        for patch in self.patches:
            inside = (x >= patch.x_min) & (x <= patch.x_max) & (y >= patch.y_min) & (y <= patch.y_max)
            mu = np.where(inside, patch.mu, mu)
        return mu if mu.ndim else float(mu)

    def to_dict(self):
        data = {"base": self.base, "patches": [vars(p) for p in self.patches]}
        if self.grid_mu is not None:
            data["grid"] = {"x": self.grid_x.tolist(), "y": self.grid_y.tolist(), "mu": self.grid_mu.tolist()}
        return data

    @classmethod
    def from_dict(cls, data):
        fmap = cls(base=data.get("base", 1.0), patches=[FrictionPatch(**p) for p in data.get("patches", [])])
        if "grid" in data:
            fmap.grid_x = np.asarray(data["grid"]["x"], dtype=float)
            fmap.grid_y = np.asarray(data["grid"]["y"], dtype=float)
            fmap.grid_mu = np.asarray(data["grid"]["mu"], dtype=float)
        return fmap

    # presets
    @classmethod
    def uniform(cls, mu=1.0):
        return cls(base=mu)

    @classmethod
    def split_mu(cls, mu_left=0.2, mu_right=1.0, x_start=0.0, x_end=1e6):
        # left half of the road (y > 0) slippery, e.g. for split-mu braking
        return cls(base=mu_right, patches=[FrictionPatch(x_start, x_end, 0.0, 1e6, mu_left, "split-mu")])

    @classmethod
    def patch(cls, x_start, x_end, mu_patch, base=1.0, width=1e6):
        return cls(base=base, patches=[FrictionPatch(x_start, x_end, -width, width, mu_patch, "patch")])


def _bilinear(gx, gy, values, x, y):
    ix = np.clip(np.searchsorted(gx, x) - 1, 0, len(gx) - 2)
    iy = np.clip(np.searchsorted(gy, y) - 1, 0, len(gy) - 2)
    tx = np.clip((x - gx[ix]) / (gx[ix + 1] - gx[ix]), 0, 1)
    ty = np.clip((y - gy[iy]) / (gy[iy + 1] - gy[iy]), 0, 1)
    v00, v10 = values[iy, ix], values[iy, ix + 1]
    v01, v11 = values[iy + 1, ix], values[iy + 1, ix + 1]
    return (1 - ty) * ((1 - tx) * v00 + tx * v10) + ty * ((1 - tx) * v01 + tx * v11)


@dataclass
class RoadProfile:
    # Road height z(x): discrete bumps plus optional ISO 8608 random roughness
    bumps: list = field(default_factory=list)  # dicts: x, height, length (cosine bump)
    roughness_class: str = ""                    # "A".."E" (ISO 8608), empty = smooth
    length: float = 2000.0
    seed: int = 0
    _x: np.ndarray = None
    _z: np.ndarray = None

    def __post_init__(self):
        if self.roughness_class:
            self._x, self._z = iso8608_profile(self.roughness_class, self.length, seed=self.seed)

    def height(self, x, y=0.0):
        x = np.asarray(x, dtype=float)
        z = np.zeros_like(x)
        for bump in self.bumps:
            xi = (x - bump["x"]) / bump["length"]
            inside = (xi >= 0) & (xi <= 1)
            z = z + np.where(inside, bump["height"] * 0.5 * (1 - np.cos(2 * np.pi * xi)), 0.0)
        if self._z is not None:
            z = z + np.interp(x, self._x, self._z)
        return z

    def to_dict(self):
        return {"bumps": self.bumps, "roughness_class": self.roughness_class, "length": self.length, "seed": self.seed}


def iso8608_profile(roughness_class, length, dx=0.05, seed=0):
    # Random road profile from the ISO 8608 displacement PSD Gd(n) = Gd(n0) (n/n0)^-2, n0 = 0.1 cycles/m
    gd_n0 = {"A": 16e-6, "B": 64e-6, "C": 256e-6, "D": 1024e-6, "E": 4096e-6}[roughness_class.upper()]
    rng = np.random.default_rng(seed)
    n = np.arange(0.011, 2.83, 0.01)
    amplitude = np.sqrt(2 * gd_n0 * (n / 0.1) ** -2 * 0.01)
    x = np.arange(0.0, length, dx)
    phase = rng.uniform(0, 2 * np.pi, len(n))
    z = (amplitude[:, None] * np.cos(2 * np.pi * n[:, None] * x[None, :] + phase[:, None])).sum(axis=0)
    return x, z


@dataclass
class LeadVehicle:
    # Vehicle driving ahead on the same path; speed given as a (time, speed) table
    initial_gap: float = 50.0
    time: list = field(default_factory=lambda: [0.0, 1e6])
    speed: list = field(default_factory=lambda: [20.0, 20.0])
    length: float = 4.5
    s: float = 0.0  # path coordinate of its rear bumper, set by the simulator

    def speed_at(self, t):
        return float(np.interp(t, self.time, self.speed))

    def to_dict(self):
        return {"initial_gap": self.initial_gap, "time": list(self.time), "speed": list(self.speed), "length": self.length}


@dataclass
class Environment:
    friction: FrictionMap = field(default_factory=FrictionMap)
    wind_speed: float = 0.0     # head wind > 0, m/s
    road: RoadProfile = field(default_factory=RoadProfile)
    lead_vehicle: LeadVehicle = None

    def mu_at(self, x, y):
        return self.friction.mu_at(x, y)

    def road_height(self, x, y=0.0):
        return self.road.height(x, y)

    def to_dict(self):
        return {"friction": self.friction.to_dict(), "wind_speed": self.wind_speed, "road": self.road.to_dict(),
                "lead_vehicle": self.lead_vehicle.to_dict() if self.lead_vehicle else None}

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        lead = data.get("lead_vehicle")
        return cls(friction=FrictionMap.from_dict(data.get("friction", {})),
                   wind_speed=data.get("wind_speed", 0.0),
                   road=RoadProfile(**data.get("road", {})),
                   lead_vehicle=LeadVehicle(**lead) if lead else None)
