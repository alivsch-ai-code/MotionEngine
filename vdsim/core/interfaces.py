"""Abstract interfaces between the layers.

    TireModel           slip + load -> tire forces
    VehicleModel        state + ControlInput -> state derivative (+ output signals)
    LateralController   VehicleState + reference -> road-wheel steering angle
    LongitudinalController  VehicleState + reference -> acceleration request
    ChassisSystem       modifies the ControlInput (ABS, ESP, TCS, rear steering, ...)
    Sensor              true VehicleState -> measured VehicleState
"""

from abc import ABC, abstractmethod


class TireModel(ABC):
    registry_name = "base"

    @abstractmethod
    def forces(self, alpha, kappa, fz, mu=1.0, camber=0.0):
        # Returns (fx, fy, mz); accepts scalars or numpy arrays
        ...


class VehicleModel(ABC):
    registry_name = "base"
    state_names = ()
    has_wheel_dynamics = False
    has_roll_dynamics = False

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def initial_state(self, x=0.0, y=0.0, psi=0.0, speed=0.0):
        ...

    @abstractmethod
    def derivatives(self, t, state, u, env, with_outputs=False):
        # Returns ds/dt, or (ds/dt, outputs) when with_outputs is True.
        # outputs is a dict of named signals (ax, ay, slip angles, forces, ...).
        ...

    @abstractmethod
    def vehicle_state(self, t, state, outputs):
        # Model state vector -> common VehicleState
        ...


class LateralController(ABC):
    registry_name = "base"

    def reset(self):
        self._hint = 0  # path search index of this controller

    @abstractmethod
    def steer(self, t, state, reference):
        # Returns the requested front road-wheel angle in rad
        ...


class LongitudinalController(ABC):
    registry_name = "base"

    def reset(self):
        self._hint = 0

    @abstractmethod
    def acceleration(self, t, state, reference, env):
        # Returns the requested longitudinal acceleration in m/s^2
        ...


class ChassisSystem(ABC):
    registry_name = "base"

    def reset(self):
        pass

    @abstractmethod
    def apply(self, t, state, u, dt):
        # Returns the modified ControlInput and records its own activity in self.signals
        ...


class Sensor(ABC):
    @abstractmethod
    def measure(self, t, state):
        ...
