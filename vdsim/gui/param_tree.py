"""Builds pyqtgraph parameter trees from the parameter dataclasses (labels, units, limits) and back."""

from pyqtgraph.parametertree import Parameter

from ..core.parameters import field_info
from ..core.registry import available

GROUPS = [("vehicle", "Fahrzeug"), ("tires", "Reifen"), ("chassis", "Fahrwerk"), ("powertrain", "Antriebsstrang"),
          ("brakes", "Bremse"), ("systems", "Regelsysteme")]
CHOICES = {("tires", "model"): lambda: available("tire_model"),
           ("powertrain", "type"): lambda: ["ev", "ice"],
           ("powertrain", "layout"): lambda: ["fwd", "rwd", "awd"]}


def _child(group, name, value, meta):
    unit = meta.get("unit", "")
    title = f"{meta.get('label') or name} [{unit}]" if unit and unit != "-" else (meta.get("label") or name)
    spec = {"name": name, "title": title}
    if (group, name) in CHOICES:
        spec.update(type="list", limits=CHOICES[(group, name)](), value=value)
    elif isinstance(value, bool):
        spec.update(type="bool", value=value)
    elif isinstance(value, (int, float)):
        spec.update(type="float", value=float(value), decimals=6)
        limits = (meta.get("min"), meta.get("max"))
        if any(v is not None for v in limits):
            spec["limits"] = (limits[0] if limits[0] is not None else -1e12, limits[1] if limits[1] is not None else 1e12)
    elif isinstance(value, list):
        spec.update(type="str", value=", ".join(f"{v:g}" for v in value))
        spec["list_field"] = True
    else:
        spec.update(type="str", value=str(value))
    return spec


def config_to_parameter(config):
    children = []
    for group, title in GROUPS:
        obj = getattr(config, group)
        children.append({"name": group, "title": title, "type": "group",
                         "children": [_child(group, n, v, m) for n, v, m in field_info(obj)]})
    return Parameter.create(name="vehicle_config", type="group", children=children)


def parameter_to_config(root, config):
    # write the values of the tree back into a (copied) VehicleConfig
    config = config.copy()
    for group, _ in GROUPS:
        obj = getattr(config, group)
        for child in root.child(group).children():
            current = getattr(obj, child.name())
            value = child.value()
            if isinstance(current, list):
                value = [float(v) for v in str(value).replace(";", ",").split(",") if v.strip()]
            elif isinstance(current, bool):
                value = bool(value)
            elif isinstance(current, float):
                value = float(value)
            setattr(obj, child.name(), value)
    return config
