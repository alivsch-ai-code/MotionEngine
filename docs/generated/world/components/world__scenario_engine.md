# Szenario-Engine

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [world](../index.md) · `world/scenario_engine` · Version 1.0.0

**Simuliert die Verkehrsteilnehmer eines Szenarios und liefert die Ground Truth (WorldState).**

## Zweck

Reproduzierbare Testszenarien für die gesamte Wirkkette: Akteure mit IDM/MOBIL, skriptbaren Triggern, Ampeln, Kollisions- und Off-Road-Erkennung sowie Störungsereignissen.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `world` |
| Name | `scenario_engine` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.world.engine.ScenarioEngine`](../../../../vdsim/world/engine.py#L37) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | wahrer Fahrzeugzustand | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `world` | `WorldState` | – | Ground Truth | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `max_dt` | max. Teilschritt der Akteure | s | 0.05 | 0.005 | 0.5 |
| `collision_margin` | Sicherheitszuschlag Kollisionsprüfung | m | 0 | 0 | 2 |
| `offroad_tolerance` | Toleranz Fahrbahnrand | m | 0.3 | 0 | 3 |
| `detect_offroad` | Off-Road-Erkennung | – | True | – | – |
| `ego_length` | Ego-Länge (ohne Fahrzeugkonfiguration) | m | 4.8 | 1 | 20 |
| `ego_width` | Ego-Breite (ohne Fahrzeugkonfiguration) | m | 1.85 | 0.5 | 3 |
| `ego_center_auto` | Mittelpunkt aus Radstand und Schwerpunktlage | – | True | – | – |
| `ego_center_offset` | Mittelpunkt vor dem Schwerpunkt (manuell) | m | 0 | -3 | 3 |
| `goal_radius` | Zielradius (Ereignis goal_reached) | m | 3 | 0.1 | 50 |

## Theorie

Synchrones Update aller Akteure (Beschleunigungen aus dem Zustand zur Zeit t, dann Integration mit Teilschritten $h \le h_{max}$). Kollisionen zwischen orientierten Rechtecken mit dem Trennachsensatz (SAT).

## Verfahren

[Idm](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Mobil](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Sat collision](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Scenario engine](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Ego-Umriss als Rechteck; Mittelpunkt in der Mitte zwischen den Achsen (Überhänge gleich)
- Akteure reagieren auf das Ego über IDM, sofern es ihre Spur belegt

## Einschränkungen

- keine Fahrzeugdynamik der Akteure (kinematische Bewegung entlang der Spur)
- Störungen wie die Seitenwindböe werden nur als Ereignis gemeldet, nicht selbst eingeprägt

## Validierung

- tests/world/test_world_engine.py
- tests/world/test_world_actors.py

## Quellen

[asam_openscenario (fehlt in docs/references)](../../references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](../../references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](../../references.md#kesting2007), [treiber2000 (fehlt in docs/references)](../../references.md#treiber2000), [Werling (2011)](../../references.md#werling2011)

## Erweiterungspunkte

- neue Szenariotypen über @scenario_type in vdsim.world.library
- neue Akteurtypen als Unterklasse von vdsim.world.actors.Actor

## Verwendung

Tests: [tests/behavior/test_behavior_rule_based.py](../../../../tests/behavior/test_behavior_rule_based.py), [tests/world/test_world_scenarios.py](../../../../tests/world/test_world_scenarios.py)
