# Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`load_opendrive`](../../../vdsim/trajectory/opendrive.py#L84) | – | [Import von GPS- und OpenDRIVE-Daten](theory.md#trajectory_import) | [ASAM OpenDRIVE](../references.md#asam_opendrive) | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`lap_time`](../../../vdsim/trajectory/speed_profile.py#L29) | – | [GGV-begrenztes Geschwindigkeitsprofil](theory.md#ggv_speed_profile) | – | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`speed_profile`](../../../vdsim/trajectory/speed_profile.py#L6) | – | [GGV-begrenztes Geschwindigkeitsprofil](theory.md#ggv_speed_profile) | [Kapania et al. (2016)](../references.md#kapania2016) | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`Trajectory.project`](../../../vdsim/trajectory/trajectory.py#L116) | – | [Projektion auf die Polylinie](theory.md#polyline_projection) | – | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`PathBuilder.build`](../../../vdsim/trajectory/trajectory_generator.py#L75) | – | [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction) | – | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`PathBuilder.turn`](../../../vdsim/trajectory/trajectory_generator.py#L58) | – | [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction) | – | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`racing_line`](../../../vdsim/trajectory/trajectory_generator.py#L406) | – | [Ideallinie mit minimaler Krümmung](theory.md#racing_line) | [Braghin et al. (2008)](../references.md#braghin2008) | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`geodetic_to_local`](../../../vdsim/trajectory/trajectory_loader.py#L17) | – | [Import von GPS- und OpenDRIVE-Daten](theory.md#trajectory_import) | – | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |
| [`WaypointEditor.to_trajectory`](../../../vdsim/trajectory/waypoint_editor.py#L72) | – | [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction) | – | [test_trajectory.py](../../../tests/test_trajectory.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `load_opendrive`

- **Warum:** Referenzen aus Messfahrten (GPX, NMEA, CSV mit lat/lon), MATLAB, ROS-Pfaden und Straßenkarten (OpenDRIVE).
- **Theorie:** [Import von GPS- und OpenDRIVE-Daten](theory.md#trajectory_import)
- **Annahmen:** Kugelerde mit $R_E$ = 6 371 km; Ausdehnung wenige Kilometer.
- **Quelle:** [ASAM OpenDRIVE](../references.md#asam_opendrive)

### `lap_time`

- **Warum:** Höchste fahrbare Geschwindigkeit entlang eines Pfads unter Quer- und Längsbeschleunigungsgrenzen.
- **Theorie:** [GGV-begrenztes Geschwindigkeitsprofil](theory.md#ggv_speed_profile)
- **Annahmen:** Punktmasse, konstante Grenzen (kein Abtrieb, keine Antriebsleistungsgrenze).
- **Quelle:** –

### `speed_profile`

- **Warum:** Höchste fahrbare Geschwindigkeit entlang eines Pfads unter Quer- und Längsbeschleunigungsgrenzen.
- **Theorie:** [GGV-begrenztes Geschwindigkeitsprofil](theory.md#ggv_speed_profile)
- **Annahmen:** Punktmasse, konstante Grenzen (kein Abtrieb, keine Antriebsleistungsgrenze).
- **Quelle:** [Kapania et al. (2016)](../references.md#kapania2016)

### `Trajectory.project`

- **Warum:** Lotfußpunkt, Bogenlänge, Querablage, Kurswinkel und Krümmung der Referenz für jede Fahrzeugposition.
- **Theorie:** [Projektion auf die Polylinie](theory.md#polyline_projection)
- **Annahmen:** Suche im Fenster ±60 Stützstellen um den letzten Index; globale Suche nur, wenn der lokale Abstand > 3 m und die globale Lösung mindestens 1 m näher ist.
- **Quelle:** –

### `PathBuilder.build`

- **Warum:** Glatte, fahrbare Referenzpfade aus Geraden, Kreisbögen, Klothoiden und Spurversätzen; Eckenverrundung im Wegpunkt-Editor.
- **Theorie:** [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction)
- **Annahmen:** Ebene Fahrbahn; Integration mit der Trapezregel auf einem um den Faktor 8 verfeinerten Raster.
- **Quelle:** –

### `PathBuilder.turn`

- **Warum:** Glatte, fahrbare Referenzpfade aus Geraden, Kreisbögen, Klothoiden und Spurversätzen; Eckenverrundung im Wegpunkt-Editor.
- **Theorie:** [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction)
- **Annahmen:** Ebene Fahrbahn; Integration mit der Trapezregel auf einem um den Faktor 8 verfeinerten Raster.
- **Quelle:** –

### `racing_line`

- **Warum:** Linie innerhalb der Streckenbreite, die die Krümmung minimiert und damit höhere Kurvengeschwindigkeiten erlaubt.
- **Theorie:** [Ideallinie mit minimaler Krümmung](theory.md#racing_line)
- **Annahmen:** Geschlossener Rundkurs, konstante Breite, Krümmung als Ersatz für die Rundenzeit.
- **Quelle:** [Braghin et al. (2008)](../references.md#braghin2008)

### `geodetic_to_local`

- **Warum:** Referenzen aus Messfahrten (GPX, NMEA, CSV mit lat/lon), MATLAB, ROS-Pfaden und Straßenkarten (OpenDRIVE).
- **Theorie:** [Import von GPS- und OpenDRIVE-Daten](theory.md#trajectory_import)
- **Annahmen:** Kugelerde mit $R_E$ = 6 371 km; Ausdehnung wenige Kilometer.
- **Quelle:** –

### `WaypointEditor.to_trajectory`

- **Warum:** Glatte, fahrbare Referenzpfade aus Geraden, Kreisbögen, Klothoiden und Spurversätzen; Eckenverrundung im Wegpunkt-Editor.
- **Theorie:** [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction)
- **Annahmen:** Ebene Fahrbahn; Integration mit der Trapezregel auf einem um den Faktor 8 verfeinerten Raster.
- **Quelle:** –
