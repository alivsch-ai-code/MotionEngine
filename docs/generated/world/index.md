# world

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.world` gibt es noch keine handgeschriebene Dokumentation (`vdsim/world/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init world`


`vdsim.world` · Quellcode: [vdsim/world/](../../../vdsim/world)

## Übersicht

Paket-Docstring:

```text
Scenario world of the automated-driving platform: road network, traffic participants, scenario engine.

road            Lane, RoadNetwork (stop lines, traffic lights, conflict zones, parking, corridors)
road_builders   highway (merge / exit), rural road, urban street, intersection, roundabout, ring road
traffic_models  IDM (Treiber 2000), MOBIL (Kesting 2007)
actors          vehicles, trucks, cyclists, pedestrians, static obstacles, triggers, TrafficSimulator
collision       SAT collision detection
scenario        ADScenario (JSON), ScenarioInstance, build_scenario, list_ad_scenarios
library         scenario types (Werling 5.3 test scenarios and more)
engine          component "world/scenario_engine"
render          top-view rendering (matplotlib)
ego_stub        kinematic ego stand-in for tests without planner
```

| Kennzahl | Anzahl |
|---|---|
| Module | 11 |
| Komponenten | 1 |
| Verfahren/Konzepte | 6 |
| @trace-Einträge | 6 |
| Tests | 5 |
| Beispiele | 0 |

## Architektur

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.world`](../../../vdsim/world/__init__.py) | 36 | – | Scenario world of the automated-driving platform: road network, traffic participants, scenario engine. |
| [`vdsim.world.actors`](../../../vdsim/world/actors.py) | 767 | Trigger, ScriptAction, Actor, LaneVehicle, Truck, Cyclist | Traffic participants and their deterministic simulation. |
| [`vdsim.world.collision`](../../../vdsim/world/collision.py) | 81 | – | Collision detection between oriented rectangles with the separating axis theorem (SAT). |
| [`vdsim.world.ego_stub`](../../../vdsim/world/ego_stub.py) | 89 | KinematicEgoStub | Kinematic ego stand-in for tests and examples without trajectory planner and controller. |
| [`vdsim.world.engine`](../../../vdsim/world/engine.py) | 174 | ScenarioEngineParams, ScenarioEngine | Scenario engine: world component "world/scenario_engine" (layer ScenarioWorld). |
| [`vdsim.world.library`](../../../vdsim/world/library.py) | 390 | – | Scenario library of the automated-driving platform (registered scenario types). |
| [`vdsim.world.render`](../../../vdsim/world/render.py) | 132 | – | Top-view rendering of road networks, traffic participants and the ego vehicle (matplotlib). |
| [`vdsim.world.road`](../../../vdsim/world/road.py) | 639 | Lane, LaneLocation, StopLine, TrafficLight, ConflictZone, ParkingSpot | Road network of the automated-driving scenarios: lanes, traffic control and drivable areas. |
| [`vdsim.world.road_builders`](../../../vdsim/world/road_builders.py) | 377 | – | Builders for typical road networks (highway, rural road, urban street, intersection, roundabout, ring road). |
| [`vdsim.world.scenario`](../../../vdsim/world/scenario.py) | 269 | ScenarioType, ADScenario, ScenarioInstance | AD scenario specification (JSON), scenario-type registry and scenario instances. |
| [`vdsim.world.traffic_models`](../../../vdsim/world/traffic_models.py) | 95 | IDMParams, MOBILParams | Microscopic traffic models: Intelligent Driver Model and MOBIL lane-change model. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [geometry](../geometry/index.md)
- genutzt von: [ad](../ad/index.md), [api](../api/index.md), [behavior](../behavior/index.md), [gui](../gui/index.md), [perception](../perception/index.md)
- externe Bibliotheken: `__future__`, `bisect`, `copy`, `dataclasses`, `json`, `matplotlib`, `numpy`, `pathlib`, `scipy`

## Designentscheidungen

_Noch nicht dokumentiert._

## Implementierung

_Keine Implementierungshinweise in module.yaml._

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`world/scenario_engine`](components/world__scenario_engine.md) | Szenario-Engine | 1.0.0 | Simuliert die Verkehrsteilnehmer eines Szenarios und liefert die Ground Truth (WorldState). |

### Verfahren und Konzepte

- [Box restriction](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Continuous curvature road](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Idm](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Mobil](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Sat collision](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Scenario engine](../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Erweiterungspunkte

_Keine angegeben._
