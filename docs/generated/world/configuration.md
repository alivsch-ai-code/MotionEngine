# world – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.world` gibt es noch keine handgeschriebene Dokumentation (`vdsim/world/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init world`


## Konfigurationsmöglichkeiten (Paketdoku)

_Keine Einträge in module.yaml._

## Parameter von [Szenario-Engine](components/world__scenario_engine.md)

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

## Parametersatz `ScenarioEngineParams` (`vdsim.world.engine`)

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

## Parametersatz `IDMParams` (`vdsim.world.traffic_models`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `v0` | Wunschgeschwindigkeit v0 | m/s | 30 | 0 | 70 |
| `T` | Folgezeitlücke T | s | 1.4 | 0.1 | 5 |
| `s0` | Mindestabstand s0 | m | 2 | 0 | 20 |
| `a` | Maximalbeschleunigung a | m/s² | 1.2 | 0.1 | 6 |
| `b` | komfortable Verzögerung b | m/s² | 2 | 0.1 | 9 |
| `delta` | Beschleunigungsexponent δ | - | 4 | 1 | 10 |
| `b_max` | maximale Verzögerung (Begrenzung) | m/s² | 9 | 1 | 12 |

## Parametersatz `MOBILParams` (`vdsim.world.traffic_models`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `politeness` | Höflichkeitsfaktor p | - | 0.3 | 0 | 1 |
| `threshold` | Wechselschwelle Δa_th | m/s² | 0.2 | 0 | 2 |
| `bias_right` | Rechtsfahrgebot a_bias | m/s² | 0.3 | 0 | 2 |
| `b_safe` | sichere Verzögerung b_safe | m/s² | 4 | 0.5 | 9 |
| `interval` | Entscheidungsintervall | s | 1 | 0.1 | 10 |
| `duration` | Dauer der Querbewegung | s | 4 | 1 | 10 |
| `cooldown` | Sperrzeit nach Spurwechsel | s | 4 | 0 | 30 |
