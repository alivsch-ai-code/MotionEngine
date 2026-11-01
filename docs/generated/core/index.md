# Kern – Konventionen, Parameter, Schnittstellen, Registry

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.core` · Quellcode: [vdsim/core/](../../../vdsim/core) · Paketdoku: [vdsim/core/docs/](../../../vdsim/core/docs)

## Übersicht

**Gemeinsame Grundlage aller Fahrdynamik-Pakete – Einheiten und Vorzeichen, Parametersätze mit Metadaten, abstrakte Schnittstellen und die klassische Plugin-Registry.**

Ohne verbindliche Konventionen sind Fahrzeugmodelle, Reifenmodelle, Regler und Auswertung nicht
austauschbar. `vdsim.core` legt deshalb ein einziges Einheiten- und Vorzeichensystem (ISO 8855) fest,
beschreibt alle Fahrzeugparameter als Datenklassen mit Bezeichnung, Einheit und Grenzen und definiert die
Schnittstellen `TireModel`, `VehicleModel`, `LateralController`, `LongitudinalController`, `ChassisSystem`
und `Sensor`. Szenarien, Kommandozeile und GUI wählen Komponenten nur über Namen aus der Registry.

Paket-Docstring:

```text
Core layer: conventions, parameters, interfaces, plugin registry and logging.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 6 |
| Komponenten | 0 |
| Verfahren/Konzepte | 2 |
| @trace-Einträge | 3 |
| Tests | 6 |
| Beispiele | 13 |

## Architektur

- `conventions.py`: Radreihenfolge FL/FR/RL/RR, Erdbeschleunigung `G`, Luftdichte; Vorzeichen im Docstring.
- `parameters.py`: `param()` erzeugt Datenklassen-Felder mit Metadaten (`unit`, `label`, `min`, `max`).
  `VehicleConfig` bündelt `VehicleParameters`, `TireParameters`, `ChassisParameters`,
  `PowertrainParameters`, `BrakeParameters` und `ControlSystemsParameters`; JSON-Import/-Export und Presets
  aus `configs/vehicles/`.
- `interfaces.py`: abstrakte Basisklassen der Schichten (siehe docs/ARCHITECTURE.md, Abschnitt 4).
- `registry.py`: `register(kind, name)`, `get`, `create`, `available`; die eingebauten Plugins werden beim
  ersten Zugriff durch Import von `controllers`, `tire_models`, `trajectory` und `vehicle_models` registriert.
- `logging_setup.py`: Konsole und rotierende Logdatei `logs/vdsim.log`.
Der Kern hängt von keinem anderen vdsim-Paket ab (ausgenommen der verzögerte Import der Plugins).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.core`](../../../vdsim/core/__init__.py) | 2 | – | Core layer: conventions, parameters, interfaces, plugin registry and logging. |
| [`vdsim.core.conventions`](../../../vdsim/core/conventions.py) | 22 | – | Units and sign conventions used throughout vdsim (ISO 8855). |
| [`vdsim.core.interfaces`](../../../vdsim/core/interfaces.py) | 88 | TireModel, VehicleModel, LateralController, LongitudinalController, ChassisSystem, Sensor | Abstract interfaces between the layers. |
| [`vdsim.core.logging_setup`](../../../vdsim/core/logging_setup.py) | 31 | – | Central logging configuration (console + rotating log file). |
| [`vdsim.core.parameters`](../../../vdsim/core/parameters.py) | 231 | VehicleParameters, TireParameters, ChassisParameters, PowertrainParameters, BrakeParameters, ControlSystemsParameters | Parameter sets of the vehicle, tires, chassis, powertrain, brakes and control systems. |
| [`vdsim.core.registry`](../../../vdsim/core/registry.py) | 65 | – | Plugin registry: models, controllers, maneuvers and importers register by name. |

### Abhängigkeiten

- nutzt: [controllers](../controllers/index.md), [tire_models](../tire_models/index.md), [trajectory](../trajectory/index.md), [vehicle_models](../vehicle_models/index.md)
- genutzt von: [ad](../ad/index.md), [analysis](../analysis/index.md), [behavior](../behavior/index.md), [controllers](../controllers/index.md), [framework](../framework/index.md), [gui](../gui/index.md), [knowledge](../knowledge/index.md), [matlab](../matlab/index.md), [perception](../perception/index.md), [planning](../planning/index.md), [powertrain](../powertrain/index.md), [prediction](../prediction/index.md), [reporting](../reporting/index.md), [runtime](../runtime/index.md), [simulation](../simulation/index.md), [stabilization](../stabilization/index.md), [tire_models](../tire_models/index.md), [trajectory](../trajectory/index.md), [vehicle_models](../vehicle_models/index.md), [visualization](../visualization/index.md), [world](../world/index.md)
- externe Bibliotheken: `abc`, `collections`, `dataclasses`, `json`, `logging`, `numpy`, `pathlib`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| SI-Einheiten intern, Grad und km/h nur an GUI und Bericht | vermeidet Umrechnungsfehler zwischen Modellen; jede Gleichung im Code ist direkt in SI lesbar | gemischte Einheiten je Modul (fehleranfällig) |
| Parameter-Metadaten im Datenklassen-Feld (param()) | GUI-Masken, JSON, Bericht und generierte Doku entstehen aus einer einzigen Quelle | separate Schema-Dateien (laufen auseinander) |
| Registry über Namen statt direkter Importe | Szenarien (JSON) und GUI kennen nur Strings; neue Modelle brauchen keine Änderung am Simulator | Fabrikfunktionen mit if/else-Kaskaden |

## Implementierung

- `from_dict` baut verschachtelte Datenklassen aus JSON auf, unbekannte Schlüssel erzeugen eine Warnung statt eines Fehlers.
- `param()` legt Listen-Defaults über `default_factory` an, damit Instanzen sich keine Listen teilen.
- Die klassische Registry (`vdsim.core.registry`) ist unversioniert; versionierte Komponenten der AD-Plattform nutzen `vdsim.framework.plugins`.

### Verfahren und Konzepte

- [Koordinatensysteme, Vorzeichen und Schlupfdefinition](theory.md#iso8855_conventions)
- [Parameterschema und klassische Registry](theory.md#parameter_schema)

## Erweiterungspunkte

- Neues Plugin mit "@register(kind, name)" für die Arten vehicle_model, tire_model, lateral_controller, longitudinal_controller, chassis_system, maneuver, trajectory_loader
- Neuer Parameter als Feld "param(default, unit, label, min=, max=)" in der passenden Datenklasse; erscheint automatisch in GUI, JSON, Bericht und generierter Doku

## Verwandte Module

[framework](../framework/index.md), [vehicle_models](../vehicle_models/index.md), [tire_models](../tire_models/index.md), [simulation](../simulation/index.md)

## Hauptquellen

[ISO 8855:2011 (2011)](../references.md#iso8855)
