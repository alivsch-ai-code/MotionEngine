# Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.trajectory` · Quellcode: [vdsim/trajectory/](../../../vdsim/trajectory) · Paketdoku: [vdsim/trajectory/docs/](../../../vdsim/trajectory/docs)

## Übersicht

**Referenzpfade mit Geschwindigkeitsprofil – Manöver-Generator (ISO-Tests, Fahrmanöver, Strecken), Import aus sieben Formaten, Wegpunkt-Editor, Ideallinie und GGV-Geschwindigkeitsprofil.**

Jeder Versuch braucht eine Referenz: einen Pfad (x, y, Kurswinkel, Krümmung über der Bogenlänge) mit
Sollgeschwindigkeit, bei offenen Manövern eine Lenk- oder Beschleunigungstabelle. Das Paket erzeugt diese
Referenzen reproduzierbar aus Normen und Parametern oder importiert sie aus Messungen und Karten.

Paket-Docstring:

```text
Trajectory management: trajectory model, maneuver generator, importers, waypoint editor, speed profiles.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 7 |
| Komponenten | 26 |
| Verfahren/Konzepte | 7 |
| @trace-Einträge | 9 |
| Tests | 6 |
| Beispiele | 1 |

## Architektur

- `trajectory.py`: `Trajectory` (Polylinie, Kurswinkel, Krümmung, Geschwindigkeit, Pylonen, Begrenzungen,
  Tabellen), `Projection`, Projektion mit Suchhinweis, Serialisierung (JSON/CSV).
- `trajectory_generator.py`: `PathBuilder` (Gerade, Bogen, Klothoide, Kurve mit Übergang, Versatz),
  alle Manöver mit `@maneuver(...)`, `racing_line()`, `generate(name, **params)`.
- `speed_profile.py`: `speed_profile()` (GGV-begrenzt) und `lap_time()`.
- `trajectory_loader.py`: CSV, JSON, GPX, NMEA, MATLAB, ROS nav_msgs/Path, OpenDRIVE (Registry „trajectory_loader“).
- `opendrive.py`: Referenzlinie und Fahrstreifenmitten aus .xodr.
- `waypoint_editor.py`: Wegpunktmodell mit Eckradien (Fillets), Rückgängig, JSON.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.trajectory`](../../../vdsim/trajectory/__init__.py) | 11 | – | Trajectory management: trajectory model, maneuver generator, importers, waypoint editor, speed profiles. |
| [`vdsim.trajectory.opendrive`](../../../vdsim/trajectory/opendrive.py) | 113 | – | OpenDRIVE (.xodr) import: reference line of a road (line, arc, spiral, poly3, paramPoly3) and lane centers. |
| [`vdsim.trajectory.speed_profile`](../../../vdsim/trajectory/speed_profile.py) | 32 | – | GGV-limited speed profile along a path (forward/backward pass with a friction ellipse). |
| [`vdsim.trajectory.trajectory`](../../../vdsim/trajectory/trajectory.py) | 187 | Projection, Trajectory | Reference trajectory: path (x, y, psi, kappa over arc length s) plus speed profile. |
| [`vdsim.trajectory.trajectory_generator`](../../../vdsim/trajectory/trajectory_generator.py) | 495 | PathBuilder | Maneuver generator: ISO test maneuvers, standard maneuvers, road types and custom test cycles. |
| [`vdsim.trajectory.trajectory_loader`](../../../vdsim/trajectory/trajectory_loader.py) | 204 | – | Trajectory import: CSV, JSON, GPS (CSV/GPX/NMEA), MATLAB, ROS nav_msgs/Path, OpenDRIVE. |
| [`vdsim.trajectory.waypoint_editor`](../../../vdsim/trajectory/waypoint_editor.py) | 145 | Waypoint, WaypointEditor | Waypoint editor (data model): edit waypoints, corner radii and speeds, build a trajectory. |

### Abhängigkeiten

- nutzt: [core](../core/index.md)
- genutzt von: [core](../core/index.md), [gui](../gui/index.md), [knowledge](../knowledge/index.md), [simulation](../simulation/index.md)
- externe Bibliotheken: `csv`, `dataclasses`, `datetime`, `json`, `numpy`, `pathlib`, `scipy`, `xml`, `yaml`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Pfade aus Krümmungssegmenten integrieren (fein abgetastet, trapezförmig) | glatte Krümmungsverläufe (Klothoiden), Kurswinkeländerung exakt gleich Integral der Krümmung | Splines durch Stützpunkte (Krümmung schwer kontrollierbar) |
| Manöver als registrierte Funktionen mit deutschen Parameterbeschriftungen | GUI baut Parametermasken automatisch; neue Manöver ohne GUI-Änderung | – |
| Projektion mit Suchfenster um den letzten Index, globale Suche nur bei Verlust der Bahn | Start/Ziel geschlossener Strecken und Kreuzungen (Acht) werden nicht verwechselt | – |

## Implementierung

- Krümmung der Polylinie als Ableitung des gemittelten Kurswinkels nach der Bogenlänge; der PathBuilder überschreibt sie mit der exakten Segmentkrümmung.
- ISO-Doppelspurwechsel: Gassenbreiten 1,1 b + 0,25, 1,2 b + 0,25, 1,3 b + 0,25 (b = Fahrzeugbreite); Referenzlinie innerhalb der Gassen über eine Glättung (lsq_linear).

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`maneuver/acceleration`](components/maneuver__acceleration.md) | Beschleunigen (0-100 km/h) | legacy | Volllastbeschleunigung aus dem Stand |
| [`maneuver/brake_in_turn`](components/maneuver__brake_in_turn.md) | Bremsen in der Kurve (ISO 7975) | legacy | Stationäre Kreisfahrt, dann Bremsung mit konstanter Verzögerung |
| [`maneuver/braking`](components/maneuver__braking.md) | Bremsen (Geradeaus) | legacy | Bremsung aus konstanter Geschwindigkeit |
| [`maneuver/circle`](components/maneuver__circle.md) | Kreisfahrt (ISO 4138) | legacy | Stationäre Kreisfahrt mit langsam steigender Geschwindigkeit (Eigenlenkgradient) |
| [`maneuver/city`](components/maneuver__city.md) | Stadtverkehr | legacy | Innerstädtischer Rundkurs mit Abbiegevorgängen |
| [`maneuver/custom`](components/maneuver__custom.md) | Kundenspezifischer Testzyklus | legacy | Segmentliste als JSON: [["straight", L, v_kmh], ["arc", R, Winkel°, v_kmh], ["clothoid", L, kappa_end, v_kmh], ["offset", L, Versatz, v_kmh]] |
| [`maneuver/emergency_evasion`](components/maneuver__emergency_evasion.md) | Notausweichen | legacy | Schnelles Ausweichen um ein Hindernis und Rückkehr in die Spur |
| [`maneuver/figure_eight`](components/maneuver__figure_eight.md) | Acht | legacy | Liegende Acht aus zwei Kreisen |
| [`maneuver/frequency_sweep`](components/maneuver__frequency_sweep.md) | Frequenzgang (Sinus-Sweep) | legacy | Lenk-Sweep zur Bestimmung des Frequenzgangs (ISO 7401) |
| [`maneuver/highway`](components/maneuver__highway.md) | Autobahnfahrt | legacy | Autobahn mit Klothoiden-Kurven und Spurwechsel |
| [`maneuver/iso_double_lane_change`](components/maneuver__iso_double_lane_change.md) | ISO-Doppelspurwechsel (ISO 3888-1) | legacy | Doppelter Spurwechsel mit Pylonengassen nach ISO 3888-1 (Versatz 3,5 m) |
| [`maneuver/iso_obstacle_avoidance`](components/maneuver__iso_obstacle_avoidance.md) | ISO-Ausweichtest (ISO 3888-2) | legacy | Ausweichmanöver nach ISO 3888-2 ("Elchtest") |
| [`maneuver/lane_change`](components/maneuver__lane_change.md) | Spurwechsel | legacy | Einfacher Spurwechsel mit sinusförmiger Krümmung (Kurswinkel am Ende 0) |
| [`maneuver/race_track`](components/maneuver__race_track.md) | Rennstrecke (Ideallinie) | legacy | Rundkurs mit berechneter Ideallinie (minimale Krümmung) und GGV-Geschwindigkeitsprofil |
| [`maneuver/ramp_steer`](components/maneuver__ramp_steer.md) | Lenkwinkelrampe (ISO 4138) | legacy | Langsam steigender Lenkwinkel bei konstanter Geschwindigkeit |
| [`maneuver/sine_with_dwell`](components/maneuver__sine_with_dwell.md) | Sinus mit Haltezeit (FMVSS 126) | legacy | ESC-Prüfmanöver: 0,7-Hz-Sinus mit 500 ms Haltezeit |
| [`maneuver/slalom`](components/maneuver__slalom.md) | Slalom | legacy | cones at x_i = pre + spacing * (i + 0.5); full lateral amplitude from half a spacing before the first to half a spacing after the last cone, smooth ramps outside |
| [`maneuver/step_steer`](components/maneuver__step_steer.md) | Lenkwinkelsprung (ISO 7401) | legacy | Sprungförmige Lenkeingabe bei konstanter Geschwindigkeit |
| [`maneuver/straight`](components/maneuver__straight.md) | Geradeausfahrt | legacy | Gerade Strecke mit konstanter Geschwindigkeit |
| [`trajectory_loader/csv`](components/trajectory_loader__csv.md) | – | legacy | – |
| [`trajectory_loader/gpx`](components/trajectory_loader__gpx.md) | – | legacy | – |
| [`trajectory_loader/json`](components/trajectory_loader__json.md) | – | legacy | – |
| [`trajectory_loader/matlab`](components/trajectory_loader__matlab.md) | – | legacy | .mat (v5/v7) with variables x, y[, v] or a struct with these fields, or an N x 2/3 matrix |
| [`trajectory_loader/nmea`](components/trajectory_loader__nmea.md) | – | legacy | $GPRMC / $GNRMC sentences (position + speed over ground) |
| [`trajectory_loader/opendrive`](components/trajectory_loader__opendrive.md) | – | legacy | – |
| [`trajectory_loader/ros`](components/trajectory_loader__ros.md) | – | legacy | nav_msgs/Path as YAML (rostopic echo / ros2 topic echo) or JSON |

### Verfahren und Konzepte

- [Frequenzgang aus dem Sinus-Sweep](../reporting/theory.md#frequency_response_estimation)
- [GGV-begrenztes Geschwindigkeitsprofil](theory.md#ggv_speed_profile)
- [Krümmungsprofil des Spurwechsels](../lane_change/theory.md#lane_change_curvature_profile)
- [Pfadkonstruktion aus Krümmungssegmenten](theory.md#path_construction)
- [Projektion auf die Polylinie](theory.md#polyline_projection)
- [Ideallinie mit minimaler Krümmung](theory.md#racing_line)
- [Import von GPS- und OpenDRIVE-Daten](theory.md#trajectory_import)

## Erweiterungspunkte

- Neues Manöver mit "@maneuver(name, label, category, description, param=(Bezeichnung, Einheit))"
- Neues Importformat mit "@register('trajectory_loader', name)" und Eintrag in EXTENSIONS

## Verwandte Module

[geometry](../geometry/index.md), [simulation](../simulation/index.md), [controllers](../controllers/index.md), [gui](../gui/index.md)

## Hauptquellen

[ASAM OpenDRIVE](../references.md#asam_opendrive), [Braghin et al. (2008)](../references.md#braghin2008), [FMVSS No. 126 (49 CFR 571.126) (2007)](../references.md#fmvss126), [ISO 3888-1:2018 (2018)](../references.md#iso3888_1), [ISO 3888-2:2011 (2011)](../references.md#iso3888_2), [ISO 4138:2021 (2021)](../references.md#iso4138), [ISO 7401:2011 (2011)](../references.md#iso7401), [ISO 7975:2019 (2019)](../references.md#iso7975), [Kapania et al. (2016)](../references.md#kapania2016), [Milliken und Milliken (1995)](../references.md#milliken1995)
