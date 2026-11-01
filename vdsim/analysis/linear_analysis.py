"""Linear single-track analysis: understeer, steady-state gains, eigenvalues, frequency response."""

import numpy as np

from ..core.conventions import G
from ..vehicle_models.bicycle_model import LinearBicycleModel


class LinearSingleTrackAnalysis:
    def __init__(self, config):
        self.config = config
        self.model = LinearBicycleModel(config)
        self.p = config.vehicle

    @property
    def understeer_gradient(self):
        return self.model.understeer_gradient()  # rad / (m/s^2)

    @property
    def characteristic_speed(self):
        # speed of maximum yaw-rate gain (understeer); nan if oversteering
        eg = self.understeer_gradient
        return float(np.sqrt(self.p.wheelbase / eg)) if eg > 0 else float("nan")

    @property
    def critical_speed(self):
        # speed at which an oversteering vehicle becomes unstable; nan if understeering
        eg = self.understeer_gradient
        return float(np.sqrt(-self.p.wheelbase / eg)) if eg < 0 else float("nan")

    def steady_state_gains(self, speed):
        # yaw-rate, lateral-acceleration and side-slip gain per road-wheel angle
        p, eg = self.p, self.understeer_gradient
        yaw_gain = speed / (p.wheelbase + eg * speed**2)
        A, B = self.model.state_space(speed)
        vy, r = -np.linalg.solve(A, B[:, 0])
        return {"yaw_rate": yaw_gain, "lateral_acceleration": yaw_gain * speed,
                "side_slip": float(np.arctan2(vy, speed)), "curvature": yaw_gain / speed}

    def eigen(self, speed):
        # natural frequency (Hz), damping ratio and eigenvalues of the lateral/yaw dynamics
        A, _ = self.model.state_space(speed)
        lam = np.linalg.eigvals(A)
        wn = float(np.sqrt(abs(np.prod(lam))))
        zeta = float(-np.sum(lam).real / (2 * wn)) if wn > 0 else float("nan")
        return {"eigenvalues": lam, "natural_frequency": wn / (2 * np.pi), "damping": zeta}

    def frequency_response(self, speed, frequencies=None):
        # Bode data of yaw rate / delta and lateral acceleration / delta
        f = np.logspace(-1.3, 1.0, 200) if frequencies is None else np.asarray(frequencies)
        A, B = self.model.state_space(speed)
        yaw, lat = [], []
        for w in 2 * np.pi * f:
            x = np.linalg.solve(1j * w * np.eye(2) - A, B[:, 0])  # [vy, r] per delta
            vy_dot = 1j * w * x[0]
            yaw.append(x[1])
            lat.append(vy_dot + speed * x[1])
        yaw, lat = np.array(yaw), np.array(lat)
        return {"frequency": f, "yaw_gain": np.abs(yaw), "yaw_phase": np.degrees(np.unwrap(np.angle(yaw))),
                "ay_gain": np.abs(lat), "ay_phase": np.degrees(np.unwrap(np.angle(lat)))}

    def summary(self, speeds=(10.0, 20.0, 30.0, 40.0)):
        rows = []
        for v in speeds:
            gains, eig = self.steady_state_gains(v), self.eigen(v)
            rows.append({"speed": v, "yaw_gain": gains["yaw_rate"], "ay_gain": gains["lateral_acceleration"],
                         "natural_frequency": eig["natural_frequency"], "damping": eig["damping"]})
        return {"understeer_gradient_deg_per_g": np.degrees(self.understeer_gradient) * G,
                "characteristic_speed_kmh": self.characteristic_speed * 3.6,
                "critical_speed_kmh": self.critical_speed * 3.6,
                "cornering_stiffness_front": self.model.c_front, "cornering_stiffness_rear": self.model.c_rear,
                "per_speed": rows}
