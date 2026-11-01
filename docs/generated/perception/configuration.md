# perception – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.perception` gibt es noch keine handgeschriebene Dokumentation (`vdsim/perception/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init perception`


## Konfigurationsmöglichkeiten (Paketdoku)

_Keine Einträge in module.yaml._

## Parameter von [Objektsensor (Reichweite, Rauschen, Latenz)](components/perception__object_sensor.md)

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

## Parametersatz `ObjectSensorParams` (`vdsim.perception.sensor`)

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
