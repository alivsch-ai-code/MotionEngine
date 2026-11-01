# Objektsensor (Reichweite, Rauschen, Latenz)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [perception](../index.md) · `perception/object_sensor` · Version 1.0.0

**Erzeugt aus der Ground Truth eine gestörte Objektliste und eine Eigenzustandsschätzung.**

## Zweck

Realistischere Eingangsdaten für Prädiktion und Verhalten: begrenzte Sicht, Verdeckung, Messrauschen, Fehldetektionen und Latenz; reproduzierbar über den Szenario-Seed.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `perception` |
| Name | `object_sensor` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.perception.sensor.ObjectSensor`](../../../../vdsim/perception/sensor.py#L93) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `world` | `WorldState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego_estimate` | `EgoState` | – | geschätzter Eigenzustand | – |
| `objects` | `ObjectList` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `range` | Reichweite | m | 150 | 1 | 1000 |
| `fov_deg` | Öffnungswinkel | ° | 360 | 1 | 360 |
| `heading_offset_deg` | Ausrichtung des Sensors (0 = nach vorn) | ° | 0 | -180 | 180 |
| `mount_x` | Einbauort vor dem Schwerpunkt | m | 0 | -5 | 5 |
| `cycle_time` | Messzyklus | s | 0.1 | 0 | 1 |
| `latency` | Latenz | s | 0 | 0 | 2 |
| `detection_probability` | Erkennungswahrscheinlichkeit | - | 1 | 0 | 1 |
| `occlusion` | einfache Verdeckung | – | False | – | – |
| `occlusion_fraction` | verdeckter Winkelanteil für Nichterkennung | - | 0.75 | 0.05 | 1 |
| `occlusion_rays` | Strahlen pro Objekt (Verdeckung) | - | 9 | 3 | 50 |
| `range_sigma` | Entfernungsrauschen σ_r | m | 0 | 0 | 5 |
| `azimuth_sigma_deg` | Winkelrauschen σ_φ | ° | 0 | 0 | 10 |
| `pos_sigma` | Positionsrauschen σ_xy | m | 0 | 0 | 5 |
| `vel_sigma` | Geschwindigkeitsrauschen σ_v | m/s | 0 | 0 | 5 |
| `heading_sigma_deg` | Orientierungsrauschen σ_ψ | ° | 0 | 0 | 30 |
| `accel_sigma` | Beschleunigungsrauschen σ_a | m/s² | 0 | 0 | 5 |
| `ego_pos_sigma` | Lokalisierungsrauschen Position | m | 0 | 0 | 5 |
| `ego_heading_sigma_deg` | Lokalisierungsrauschen Gierwinkel | ° | 0 | 0 | 10 |
| `ego_vel_sigma` | Rauschen Eigengeschwindigkeit | m/s | 0 | 0 | 2 |
| `update_frenet` | s, d nach Rauschen neu auf die Spur projizieren | – | True | – | – |

## Theorie

Polares Messmodell: $r_m = r + n_r$, $\varphi_m = \varphi + n_\varphi$ mit $n \sim \mathcal{N}(0, \sigma^2)$, zusätzlich additives Rauschen auf Position, Geschwindigkeit, Orientierung und Beschleunigung. Ein Objekt ist sichtbar, wenn ein Eckpunkt in Reichweite liegt, es den Öffnungswinkel schneidet und nicht überwiegend von näheren Objekten abgeschattet wird.

## Verfahren

[Sensor model](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Objekte als Rechtecke, Verdeckung nur in der Ebene (keine Höheninformation)
- Rauschen weiß und normalverteilt, Objekte unabhängig

## Einschränkungen

- kein Tracking, keine Falschalarme (Geisterobjekte)
- keine Sensorfusion mehrerer Sensoren

## Validierung

- tests/perception/test_perception_sensor.py

## Quellen

[bar_shalom2001 (fehlt in docs/references)](../../references.md#bar_shalom2001)

## Erweiterungspunkte

- weitere Sensoren als eigene Komponente der Ebene perception

## Verwendung

Tests: [tests/perception/test_perception_sensor.py](../../../../tests/perception/test_perception_sensor.py)
