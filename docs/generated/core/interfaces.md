# Kern – Konventionen, Parameter, Schnittstellen, Registry – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Datentypen

### `VehicleConfig`

vollständiger Fahrzeugparametersatz

Definiert in `vdsim.core.parameters.VehicleConfig`.

| Feld | Typ | Default |
|---|---|---|
| `vehicle` | VehicleParameters | field(default_factory=VehicleParameters) |
| `tires` | TireParameters | field(default_factory=TireParameters) |
| `chassis` | ChassisParameters | field(default_factory=ChassisParameters) |
| `powertrain` | PowertrainParameters | field(default_factory=PowertrainParameters) |
| `brakes` | BrakeParameters | field(default_factory=BrakeParameters) |
| `systems` | ControlSystemsParameters | field(default_factory=ControlSystemsParameters) |

## Öffentliche API

### `vdsim.core.interfaces`

| Name | Art | Beschreibung |
|---|---|---|
| [`TireModel`](../../../vdsim/core/interfaces.py#L14) | Klasse | – |
| [`VehicleModel`](../../../vdsim/core/interfaces.py#L23) | Klasse | – |
| [`LateralController`](../../../vdsim/core/interfaces.py#L48) | Klasse | – |
| [`LongitudinalController`](../../../vdsim/core/interfaces.py#L60) | Klasse | – |
| [`ChassisSystem`](../../../vdsim/core/interfaces.py#L72) | Klasse | – |
| [`Sensor`](../../../vdsim/core/interfaces.py#L84) | Klasse | – |

### `vdsim.core.logging_setup`

| Name | Art | Beschreibung |
|---|---|---|
| [`setup_logging(level, log_dir)`](../../../vdsim/core/logging_setup.py#L10) | Funktion | – |
| [`get_logger(name)`](../../../vdsim/core/logging_setup.py#L29) | Funktion | – |

### `vdsim.core.parameters`

| Name | Art | Beschreibung |
|---|---|---|
| [`VehicleParameters`](../../../vdsim/core/parameters.py#L26) | Klasse | – |
| [`TireParameters`](../../../vdsim/core/parameters.py#L61) | Klasse | – |
| [`ChassisParameters`](../../../vdsim/core/parameters.py#L82) | Klasse | – |
| [`PowertrainParameters`](../../../vdsim/core/parameters.py#L116) | Klasse | – |
| [`BrakeParameters`](../../../vdsim/core/parameters.py#L143) | Klasse | – |
| [`ControlSystemsParameters`](../../../vdsim/core/parameters.py#L151) | Klasse | – |
| [`VehicleConfig`](../../../vdsim/core/parameters.py#L174) | Klasse | – |
| [`param(default, unit, label, **limits)`](../../../vdsim/core/parameters.py#L17) | Funktion | Dataclass field with GUI metadata (label, unit, optional min/max/step) |
| [`from_dict(data)`](../../../vdsim/core/parameters.py#L200) | Funktion | Build a (nested) dataclass from a dict; unknown keys are reported, missing keys keep defaults |
| [`field_info(obj)`](../../../vdsim/core/parameters.py#L215) | Funktion | (name, value, metadata) of all fields of a parameter dataclass, for GUIs and reports |
| [`load_vehicle_preset(name_or_path, preset_dir)`](../../../vdsim/core/parameters.py#L220) | Funktion | Load a vehicle preset by file path or by name from configs/vehicles |
| [`default_config_dir()`](../../../vdsim/core/parameters.py#L229) | Funktion | – |

### `vdsim.core.registry`

| Name | Art | Beschreibung |
|---|---|---|
| [`register(kind, name)`](../../../vdsim/core/registry.py#L26) | Funktion | – |
| [`get(kind, name)`](../../../vdsim/core/registry.py#L38) | Funktion | – |
| [`create(kind, name, *args, **kwargs)`](../../../vdsim/core/registry.py#L46) | Funktion | – |
| [`available(kind)`](../../../vdsim/core/registry.py#L50) | Funktion | – |
