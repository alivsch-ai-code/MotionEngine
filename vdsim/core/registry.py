"""Plugin registry: models, controllers, maneuvers and importers register by name.

Extending the platform means writing a class and decorating it, e.g.

    @register("tire_model", "my_tire")
    class MyTire(TireModel): ...

Everything that selects components by name (scenarios, GUI) uses this registry.
"""

from collections import defaultdict

_REGISTRY = defaultdict(dict)

KINDS = (
    "vehicle_model",
    "tire_model",
    "lateral_controller",
    "longitudinal_controller",
    "chassis_system",
    "maneuver",
    "trajectory_loader",
)


def register(kind, name):
    if kind not in KINDS:
        raise ValueError(f"unknown registry kind '{kind}', expected one of {KINDS}")

    def decorator(obj):
        _REGISTRY[kind][name] = obj
        obj.registry_name = name
        return obj

    return decorator


def get(kind, name):
    _load_builtin_plugins()
    try:
        return _REGISTRY[kind][name]
    except KeyError:
        raise KeyError(f"no {kind} named '{name}', available: {sorted(_REGISTRY[kind])}") from None


def create(kind, name, *args, **kwargs):
    return get(kind, name)(*args, **kwargs)


def available(kind):
    _load_builtin_plugins()
    return sorted(_REGISTRY[kind])


_loaded = False


def _load_builtin_plugins():
    # Import the built-in modules once so that their @register decorators run
    global _loaded
    if _loaded:
        return
    _loaded = True
    from .. import controllers, tire_models, trajectory, vehicle_models  # noqa: F401
