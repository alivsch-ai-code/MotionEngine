"""Chassis control systems: which ones are switched on and in which order they act."""

from . import active_suspension, esp_controller, rear_axle_steering, slip_control, torque_vectoring  # noqa: F401

SYSTEM_FLAGS = {"abs": "abs_enabled", "tcs": "tcs_enabled", "esp": "esp_enabled",
                "rear_steering": "rear_steering_enabled", "torque_vectoring": "torque_vectoring_enabled",
                "active_roll": "active_roll_enabled", "active_damping": "active_damping_enabled"}


def enabled_systems(config):
    # names of the chassis systems switched on in the vehicle configuration, in execution order
    order = ["rear_steering", "torque_vectoring", "esp", "tcs", "abs", "active_roll", "active_damping"]
    return [name for name in order if getattr(config.systems, SYSTEM_FLAGS[name])]
