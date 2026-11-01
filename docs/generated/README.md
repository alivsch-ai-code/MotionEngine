# vdsim – generierte Dokumentation

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Einstieg in die automatisch erzeugte Dokumentation aller Pakete. Bedienung und Konzept: [docs/KNOWLEDGE.md](../KNOWLEDGE.md). Interaktiver Wissensgraph: [knowledge_graph.html](knowledge_graph.html), GUI: `python -m vdsim.knowledge.gui`.

## Pakete

| Paket | Titel | Kurzfassung | Komponenten | Konzepte | Traces | Tests | Doku |
|---|---|---|---|---|---|---|---|
| [actuators](actuators/index.md) | Aktorik – Latenzkette, Lenkaktor, Kennlinienfehler | Bildet die Wirkkette zwischen Planer und Fahrzeug nach – Totzeiten, PT1-Verzögerung, verfälschte Aktuator-Kennlinie, Ratenbegrenzung und Rückkanal-Korrektur. | 0 | 3 | 6 | 2 | handgeschrieben + Theorie |
| [ad](ad/index.md) | – | Integration of the automated-driving stack: stack definition, graph assembly, runner, results. | 0 | 0 | 0 | 3 | Stub |
| [analysis](analysis/index.md) | Fahrzeuganalyse – linear und quasi-statisch | Kennwerte eines Fahrzeugs ohne Simulation – Eigenlenkgradient, Verstärkungen, Eigenwerte, Frequenzgang, Radlasten, Wankgradient, Rollachse, Lenkkinematik. | 0 | 4 | 9 | 3 | handgeschrieben + Theorie |
| [api](api/index.md) | – | Public Python API of the platform (API first: CLI, REST server and GUI use these functions). | 0 | 0 | 0 | 2 | Stub |
| [behavior](behavior/index.md) | – | Behavior planning layer: rule-based state machine (lane keeping/change, merging, overtaking, junctions, parking). | 1 | 5 | 2 | 1 | Stub |
| [controllers](controllers/index.md) | Regler, Fahrerassistenz und Fahrwerksregelsysteme | Bahnführung (Stanley, Pure Pursuit, MPC), Längsführung (PI, ACC, AEB), Spurhalteassistent, Rückkanal-Schätzer sowie ABS, ASR, ESP, Torque Vectoring, Hinterachslenkung und aktives Fahrwerk. | 16 | 15 | 18 | 5 | handgeschrieben + Theorie |
| [core](core/index.md) | Kern – Konventionen, Parameter, Schnittstellen, Registry | Gemeinsame Grundlage aller Fahrdynamik-Pakete – Einheiten und Vorzeichen, Parametersätze mit Metadaten, abstrakte Schnittstellen und die klassische Plugin-Registry. | 0 | 2 | 3 | 6 | handgeschrieben + Theorie |
| [framework](framework/index.md) | Komponenten-Framework der AD-Plattform | Komponentenmodell mit typisierten Ports, versionierte Plugin-Registry, Dependency Injection, Laufzeitkontext, Signaltypen mit Codecs und Rückverfolgbarkeits-Metadaten. | 0 | 6 | 11 | 19 | handgeschrieben + Theorie |
| [geometry](geometry/index.md) | Geometrie – Referenzkurven und Frenet-Koordinaten | Glatte Referenzkurve r(s) mit Projektion und geschlossener Frenet-Transformation nach Werling (2011), Anhang A. | 0 | 4 | 6 | 6 | handgeschrieben + Theorie |
| [gui](gui/index.md) | Desktop-Anwendung (PySide6) | Hauptfenster mit andockbaren Panels für Szenario, Fahrzeugparameter, Live-Ansicht, Analyse, Kennwerte, Laufvergleich, Trajektorien-Editor und Protokoll. | 0 | 4 | 0 | 6 | handgeschrieben |
| [knowledge](knowledge/index.md) | Wissens-, Dokumentations- und Rückverfolgbarkeitssystem | Sammelt Wissen aus Code und Doku, erzeugt die Paketdokumentation, verknüpft Implementierung, Theorie, Quellen und Tests und stellt alles als Wissensgraph und Wissensbrowser bereit. | 0 | 3 | 6 | 7 | handgeschrieben + Theorie |
| [lane_change](lane_change/index.md) | Spurwechsel-Latenzstudie | Ursprüngliche Studie – Spurwechsel bei 120 km/h mit kinematischem Einspurmodell, verfälschter Aktuator-Kennlinie, Latenzkette und Rückkanal-Korrektur der Soll-Krümmung. | 0 | 7 | 4 | 1 | handgeschrieben + Theorie |
| [matlab](matlab/index.md) | MATLAB-Integration (Import, Interpreter, Analyse, Konvertierung) | Importiert MATLAB-Regler- und Simulationscode, führt die originale Logik ohne MATLAB aus, analysiert die Regelstruktur und übersetzt nach Python, C++17 und Rust. | 0 | 8 | 7 | 5 | handgeschrieben |
| [perception](perception/index.md) | – | Perception layer: object sensor model (range, field of view, occlusion, noise, latency) and ground truth. | 2 | 1 | 1 | 1 | Stub |
| [planning](planning/index.md) | Trajektorienplanung nach Werling | Zeitlich konsistente, sampling-basierte Trajektorienplanung in Frenet-Koordinaten mit kombinierter Quer- und Längsoptimierung, Kollisionsprüfung und Bi-level-Stabilisierung (Werling 2011, Kap. | 26 | 25 | 29 | 7 | handgeschrieben + Theorie |
| [powertrain](powertrain/index.md) | Antriebsstrang, Bremse und Längsaktuierung | Setzt eine Beschleunigungsanforderung in Antriebs- und Bremsmomente je Rad um – mit Verbrennungsmotor und Automatikgetriebe oder E-Motor, Bremskraftverteilung (EBV), Rekuperation und Energiebilanz. | 0 | 4 | 5 | 2 | handgeschrieben + Theorie |
| [prediction](prediction/index.md) | – | Prediction layer: constant acceleration in Frenet coordinates (Werling 3.5.2), constant velocity, lane following. | 3 | 5 | 2 | 2 | Stub |
| [reporting](reporting/index.md) | Auswertung und Berichte | Automatische Kennwerte (Fahrdynamik, Bahnführung, Komfort nach ISO 2631, Energie, Normtest-Kriterien), Laufvergleich, PDF-Bericht und Engineering Summary. | 0 | 4 | 9 | 2 | handgeschrieben + Theorie |
| [research](research/index.md) | Forschungsmodus | Kennwerte, Sicherheitsmetriken, Batch-Simulation, Parameter-Sweeps, Monte Carlo, Controller- und Planer-Vergleiche sowie Laufzeit-Benchmarking. | 0 | 5 | 5 | 1 | handgeschrieben + Theorie |
| [runtime](runtime/index.md) | Laufzeitumgebung – Graph, Executor, Debugging, Versionierung, Custom Nodes | Führt Komponentengraphen der offenen Fahrzeugarchitektur deterministisch und mehrratig aus und bindet Custom Nodes in Python, Rust und C++ mit Hot Reload ein. | 19 | 8 | 2 | 5 | handgeschrieben + Theorie |
| [simulation](simulation/index.md) | Simulationskern – Löser, Regelkreis, Szenarien, Ergebnisse | Schließt den Regelkreis Referenz → Regler → Aktorik → Regelsysteme → Fahrzeugmodell, integriert die Bewegungsgleichungen und zeichnet alle Signale auf. | 0 | 4 | 7 | 6 | handgeschrieben + Theorie |
| [stabilization](stabilization/index.md) | Trajektorienstabilisierung nach Werling und Fahrzeugebenen | Setzt Solltrajektorien mit den drei Werling-Trackingreglern (Bi-level-Stabilisierung) oder klassischen Reglern in Lenkrate/Lenkwinkel und Längskraft/Beschleunigung um und stellt Vehicle Dynamics, Actuators und Vehicle Plant bereit. | 17 | 29 | 28 | 6 | handgeschrieben + Theorie |
| [tire_models](tire_models/index.md) | Reifenmodelle | Stationäre Reifenkraftmodelle – linear mit Reibkreis, Pacejka Magic Formula mit kombiniertem Schlupf und Bürstenmodell. | 4 | 5 | 7 | 3 | handgeschrieben + Theorie |
| [trajectory](trajectory/index.md) | Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile | Referenzpfade mit Geschwindigkeitsprofil – Manöver-Generator (ISO-Tests, Fahrmanöver, Strecken), Import aus sieben Formaten, Wegpunkt-Editor, Ideallinie und GGV-Geschwindigkeitsprofil. | 26 | 7 | 9 | 6 | handgeschrieben + Theorie |
| [vehicle_models](vehicle_models/index.md) | Fahrzeugmodelle | Bewegungsgleichungen vom kinematischen Einspurmodell bis zum Mehrkörpermodell mit 24 Zuständen. | 7 | 10 | 15 | 8 | handgeschrieben + Theorie |
| [visualization](visualization/index.md) | Visualisierung | matplotlib-Diagramme (Pfad, Zustandsgrößen, Reifen, Pacejka-Kurven, GGV, Bode, Heatmaps, Energie, Vergleich), Echtzeit-Widgets (Draufsicht, Signal-Scope, Kacheln, 3D) und Draufsicht-Animation. | 0 | 0 | 0 | 1 | handgeschrieben |
| [world](world/index.md) | – | Scenario world of the automated-driving platform: road network, traffic participants, scenario engine. | 1 | 6 | 6 | 5 | Stub |

## Verfahren und Konzepte

| Verfahren | ID | Paket | Implementierungen | Quellen | dokumentiert |
|---|---|---|---|---|---|
| [Absolutes Endzeitraster](planning/theory.md#absolute_time_grid) | `absolute_time_grid` | planning | 3 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Acc](README.md#konzepte-ohne-dokumentation) | `acc` | – | 2 | [Rajamani (2012)](references.md#rajamani2012) | nein |
| [Abstandsregeltempomat und Notbremsassistent](controllers/theory.md#acc_aeb) | `acc_aeb` | controllers | 4 | [Rajamani (2012)](references.md#rajamani2012) | ja |
| [Ackermann-Lenkgeometrie und Wendekreis](analysis/theory.md#ackermann_steering) | `ackermann_steering` | analysis | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [Aktives Fahrwerk: Wankstabilisierung und Skyhook](controllers/theory.md#active_suspension) | `active_suspension` | controllers | 4 | [Karnopp et al. (1974)](references.md#karnopp1974), [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [Algebraische Schleifen](runtime/theory.md#algebraic_loop) | `algebraic_loop` | runtime | 0 | [Lee und Seshia (2017)](references.md#lee_seshia2017), [MathWorks (2024)](references.md#simulink_exec), [Werling (2011)](references.md#werling2011) | ja |
| [Anti windup](README.md#konzepte-ohne-dokumentation) | `anti_windup` | – | 3 | [Åström und Hägglund (2006)](references.md#astrom2006), [Werling (2011)](references.md#werling2011) | nein |
| [Backstepping](README.md#konzepte-ohne-dokumentation) | `backstepping` | – | 1 | [Khalil (2002)](references.md#khalil2002), [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011) | nein |
| [Behavior state machine](README.md#konzepte-ohne-dokumentation) | `behavior_state_machine` | – | 1 | [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [stvo (fehlt in docs/references)](references.md#stvo), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | nein |
| [Zeitliche Konsistenz (Bellman-Prinzip)](planning/theory.md#bellman_principle) | `bellman_principle` | planning | 4 | [Bellman (1957)](references.md#bellman1957), [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Bi-level-Stabilisierung (Planerseite)](planning/theory.md#bilevel_stabilization) | `bilevel_stabilization` | planning | 3 | [Werling et al. (2010)](references.md#werling2010icra), [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Box restriction](README.md#konzepte-ohne-dokumentation) | `box_restriction` | – | 2 | [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [stvo (fehlt in docs/references)](references.md#stvo), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | nein |
| [Bürstenmodell](tire_models/theory.md#brush_model) | `brush_model` | tire_models | 2 | [Pacejka (2012)](references.md#pacejka2012) | ja |
| [C-ABI der nativen Custom Nodes](runtime/theory.md#c_abi) | `c_abi` | runtime | 0 | [Project (2024)](references.md#cargo_book), [Microsoft (2024)](references.md#msvc_dll), [Foundation (2024)](references.md#python_ctypes), [Project (2024)](references.md#rust_ffi) | ja |
| [Ca prediction](README.md#konzepte-ohne-dokumentation) | `ca_prediction` | – | 2 | [Werling (2011)](references.md#werling2011) | nein |
| [Kombination und Rücktransformation](planning/theory.md#candidate_combination) | `candidate_combination` | planning | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Klassische Trackingregler](stabilization/theory.md#classic_tracking) | `classic_tracking` | stabilization | 0 | [Åström und Hägglund (2006)](references.md#astrom2006), [Borrelli et al. (2017)](references.md#borrelli2017), [Hoffmann et al. (2007)](references.md#hoffmann2007), [Rajamani (2012)](references.md#rajamani2012), [Snider (2009)](references.md#snider2009), [Stellato et al. (2020)](references.md#stellato2020) | ja |
| [Kollisionsprüfung mit Kreisen](planning/theory.md#collision_circles) | `collision_circles` | planning | 2 | [Werling (2011)](references.md#werling2011), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Kombinierter Schlupf (Gewichtungsfunktionen)](tire_models/theory.md#combined_slip) | `combined_slip` | tire_models | 2 | [Pacejka (2012)](references.md#pacejka2012) | ja |
| [Komponentenmodell mit typisierten Ports](framework/theory.md#component_model) | `component_model` | framework | 2 | [Martin (2017)](references.md#martin2017), [Werling (2011)](references.md#werling2011) | ja |
| [Composite](README.md#konzepte-ohne-dokumentation) | `composite` | – | 1 | [Rajamani (2012)](references.md#rajamani2012) | nein |
| [Versionierungsmodell](runtime/theory.md#content_addressed_versioning) | `content_addressed_versioning` | runtime | 0 | [Chacon und Straub (2014)](references.md#git_book) | ja |
| [Continuous curvature road](README.md#konzepte-ohne-dokumentation) | `continuous_curvature_road` | – | 2 | [Werling (2011)](references.md#werling2011) | nein |
| [Zielmannigfaltigkeit und Endkosten](planning/theory.md#continuous_manifold) | `continuous_manifold` | planning | 3 | [Bryson und Ho (1975)](references.md#bryson1975), [Werling (2011)](references.md#werling2011) | ja |
| [Stoßfreie Reglerumschaltung](stabilization/theory.md#controller_switching) | `controller_switching` | stabilization | 2 | [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011) | ja |
| [Korridor-Restriktion](planning/theory.md#corridor_constraint) | `corridor_constraint` | planning | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Rückkanal-Korrektur des Krümmungsfehlers](controllers/theory.md#curvature_feedback_correction) | `curvature_feedback_correction` | controllers | 1 | [Ljung (1999)](references.md#ljung1999), [Smith (1957)](references.md#smith1957) | ja |
| [Projektion auf die Referenzkurve](geometry/theory.md#curve_projection) | `curve_projection` | geometry | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Cv prediction](README.md#konzepte-ohne-dokumentation) | `cv_prediction` | – | 1 | – | nein |
| [Dependency Injection und Laufzeitkontext](framework/theory.md#dependency_injection) | `dependency_injection` | framework | 1 | [Fowler (2004)](references.md#fowler2004), [Martin (2017)](references.md#martin2017) | ja |
| [Desm](README.md#konzepte-ohne-dokumentation) | `desm` | – | 3 | [Werling (2011)](references.md#werling2011) | nein |
| [Determinismus](runtime/theory.md#deterministic_execution) | `deterministic_execution` | runtime | 0 | [Edwards und Lee (2003)](references.md#edwards_lee2003), [Lee und Seshia (2017)](references.md#lee_seshia2017) | ja |
| [Deterministische Zufallszahlen und Reproduzierbarkeit](framework/theory.md#deterministic_seeding) | `deterministic_seeding` | framework | 3 | [Martin (2017)](references.md#martin2017) | ja |
| [Diskrete Grundblöcke](runtime/theory.md#discrete_blocks) | `discrete_blocks` | runtime | 4 | [Lee und Seshia (2017)](references.md#lee_seshia2017), [MathWorks (2024)](references.md#simulink_exec) | ja |
| [Zweispurmodell mit Wanken und Raddrehung](vehicle_models/theory.md#double_track) | `double_track` | vehicle_models | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Pacejka (2012)](references.md#pacejka2012), [Schramm et al. (2018)](references.md#schramm2018) | ja |
| [Antriebsgrenzen von Motor und Getriebe](powertrain/theory.md#drive_torque_limits) | `drive_torque_limits` | powertrain | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [Fahrwiderstände](vehicle_models/theory.md#driving_resistances) | `driving_resistances` | vehicle_models | 7 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Pacejka (2012)](references.md#pacejka2012), [Rajamani (2012)](references.md#rajamani2012), [Schramm et al. (2018)](references.md#schramm2018) | ja |
| [Dynamic reference transform](README.md#konzepte-ohne-dokumentation) | `dynamic_reference_transform` | – | 3 | [Isidori (1995)](references.md#isidori1995), [Khalil (2002)](references.md#khalil2002), [Pacejka (2012)](references.md#pacejka2012), [Werling (2011)](references.md#werling2011) | nein |
| [Energiebilanz](powertrain/theory.md#energy_balance) | `energy_balance` | powertrain | 1 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [ESP – Gierratenregelung durch Einzelradbremsung](controllers/theory.md#esp_yaw_control) | `esp_yaw_control` | controllers | 3 | [Rajamani (2012)](references.md#rajamani2012), [Reif (2010)](references.md#reif2010), [van Zanten et al. (1995)](references.md#vanzanten1995) | ja |
| [Exakte E/A-Linearisierung für schnelle Fahrt](stabilization/theory.md#exact_io_linearization) | `exact_io_linearization` | stabilization | 3 | [Isidori (1995)](references.md#isidori1995), [Khalil (2002)](references.md#khalil2002), [Pacejka (2012)](references.md#pacejka2012), [Werling (2011)](references.md#werling2011) | ja |
| [Rückfallebene](planning/theory.md#fallback) | `fallback` | planning | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Feedforward](README.md#konzepte-ohne-dokumentation) | `feedforward` | – | 1 | [Åström und Hägglund (2006)](references.md#astrom2006), [Werling (2011)](references.md#werling2011) | nein |
| [Flat reference transform](README.md#konzepte-ohne-dokumentation) | `flat_reference_transform` | – | 2 | [Isidori (1995)](references.md#isidori1995), [Khalil (2002)](references.md#khalil2002), [Werling (2011)](references.md#werling2011) | nein |
| [Folgemodus](planning/theory.md#following_mode) | `following_mode` | planning | 2 | [Werling (2011)](references.md#werling2011) | ja |
| [Kräftebasiertes Graphlayout](knowledge/theory.md#force_directed_layout) | `force_directed_layout` | knowledge | 1 | [Fruchterman und Reingold (1991)](references.md#fruchterman1991) | ja |
| [Frenet frame](README.md#konzepte-ohne-dokumentation) | `frenet_frame` | – | 1 | [Werling (2011)](references.md#werling2011) | nein |
| [Frenet-Transformation in geschlossener Form](geometry/theory.md#frenet_transformation) | `frenet_transformation` | geometry | 3 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011) | ja |
| [Frequenzgang aus dem Sinus-Sweep](reporting/theory.md#frequency_response_estimation) | `frequency_response_estimation` | reporting | 2 | [ISO 7401:2011 (2011)](references.md#iso7401), [Welch (1967)](references.md#welch1967) | ja |
| [Reibwertausnutzung und Stabilitätsreserve](reporting/theory.md#friction_utilization) | `friction_utilization` | reporting | 1 | [Milliken und Milliken (1995)](references.md#milliken1995) | ja |
| [Vollfaktorieller Versuchsplan](research/theory.md#full_factorial_design) | `full_factorial_design` | research | 1 | [Montgomery (2017)](references.md#montgomery2017) | ja |
| [GGV-begrenztes Geschwindigkeitsprofil](trajectory/theory.md#ggv_speed_profile) | `ggv_speed_profile` | trajectory | 5 | [Braghin et al. (2008)](references.md#braghin2008), [Kapania et al. (2016)](references.md#kapania2016), [Milliken und Milliken (1995)](references.md#milliken1995) | ja |
| [Hazard indicator](README.md#konzepte-ohne-dokumentation) | `hazard_indicator` | – | 1 | [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [stvo (fehlt in docs/references)](references.md#stvo), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | nein |
| [Hermite-interpolierte Referenzkurve](geometry/theory.md#hermite_reference_curve) | `hermite_reference_curve` | geometry | 1 | [de Boor (2001)](references.md#deboor2001) | ja |
| [Hot Reload](runtime/theory.md#hot_reload) | `hot_reload` | runtime | 0 | [Microsoft (2024)](references.md#msvc_dll), [Foundation (2024)](references.md#python_ctypes), [Project (2024)](references.md#rust_ffi) | ja |
| [Ideale Bremskraftverteilung (EBV)](powertrain/theory.md#ideal_brake_distribution) | `ideal_brake_distribution` | powertrain | 1 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Reif (2010)](references.md#reif2010) | ja |
| [Idm](README.md#konzepte-ohne-dokumentation) | `idm` | – | 2 | [asam_openscenario (fehlt in docs/references)](references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | nein |
| [Invariant tracking error](README.md#konzepte-ohne-dokumentation) | `invariant_tracking_error` | – | 4 | [Khalil (2002)](references.md#khalil2002), [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011) | nein |
| [Komfortbewertung nach ISO 2631-1](reporting/theory.md#iso2631_comfort) | `iso2631_comfort` | reporting | 2 | [ISO 2631-1:1997 (1997)](references.md#iso2631_1) | ja |
| [Fahrbahnprofil nach ISO 8608](simulation/theory.md#iso8608_road_profile) | `iso8608_road_profile` | simulation | 1 | [ISO 8608:2016 (2016)](references.md#iso8608) | ja |
| [Koordinatensysteme, Vorzeichen und Schlupfdefinition](core/theory.md#iso8855_conventions) | `iso8855_conventions` | core | 1 | [ISO 8855:2011 (2011)](references.md#iso8855), [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [Kennwerte der Normversuche](reporting/theory.md#iso_test_kpis) | `iso_test_kpis` | reporting | 5 | [FMVSS No. 126 (49 CFR 571.126) (2007)](references.md#fmvss126), [ISO 3888-1:2018 (2018)](references.md#iso3888_1), [ISO 3888-2:2011 (2011)](references.md#iso3888_2), [ISO 4138:2021 (2021)](references.md#iso4138), [ISO 7401:2011 (2011)](references.md#iso7401), [ISO 7975:2019 (2019)](references.md#iso7975), [UN-ECE-Regelung Nr. 13-H](references.md#unece_r13h) | ja |
| [Dynamisches Einspurmodell mit isotropem Reifen](stabilization/theory.md#isotropic_tire) | `isotropic_tire` | stabilization | 3 | [Isidori (1995)](references.md#isidori1995), [Khalil (2002)](references.md#khalil2002), [Pacejka (2012)](references.md#pacejka2012), [Werling (2011)](references.md#werling2011) | ja |
| [Ruckintegral in geschlossener Form](planning/theory.md#jerk_integral) | `jerk_integral` | planning | 2 | [Werling (2011)](references.md#werling2011) | ja |
| [Erweitertes kinematisches Einspurmodell](stabilization/theory.md#kesm) | `kesm` | stabilization | 3 | [Khalil (2002)](references.md#khalil2002), [Rajamani (2012)](references.md#rajamani2012), [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011) | ja |
| [Kinematisches Einspurmodell](vehicle_models/theory.md#kinematic_bicycle) | `kinematic_bicycle` | vehicle_models | 4 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Rajamani (2012)](references.md#rajamani2012) | ja |
| [Fahrphysikalische Restriktionen](planning/theory.md#kinematic_constraints) | `kinematic_constraints` | planning | 2 | [Kamm (1936)](references.md#kamm1936), [Mitschke und Wallentowitz (2004)](references.md#mitschke2004), [Werling (2011)](references.md#werling2011) | ja |
| [Graphmodell des Wissens](knowledge/theory.md#knowledge_graph_model) | `knowledge_graph_model` | knowledge | 3 | [Gotel und Finkelstein (1994)](references.md#gotel1994) | ja |
| [Korrekturstudie](lane_change/theory.md#lane_change_correction_study) | `lane_change_correction_study` | lane_change | 1 | [Ljung (1999)](references.md#ljung1999), [Smith (1957)](references.md#smith1957) | ja |
| [Krümmungsprofil des Spurwechsels](lane_change/theory.md#lane_change_curvature_profile) | `lane_change_curvature_profile` | lane_change | 2 | [Rajamani (2012)](references.md#rajamani2012) | ja |
| [Lane following prediction](README.md#konzepte-ohne-dokumentation) | `lane_following_prediction` | – | 1 | [Werling (2011)](references.md#werling2011) | nein |
| [Spurhalteassistent mit Fahrermodell](controllers/theory.md#lane_keeping_assist) | `lane_keeping_assist` | controllers | 2 | [Rajamani (2012)](references.md#rajamani2012) | ja |
| [Latenzkette aus Totzeit und PT1](actuators/theory.md#latency_chain) | `latency_chain` | actuators | 3 | [comma.ai](references.md#openpilot), [Smith (1957)](references.md#smith1957) | ja |
| [Umlauflatenz der Wirkkette](lane_change/theory.md#latency_round_trip) | `latency_round_trip` | lane_change | 1 | [comma.ai](references.md#openpilot) | ja |
| [Lateral intent](README.md#konzepte-ohne-dokumentation) | `lateral_intent` | – | 2 | [Werling (2011)](references.md#werling2011) | nein |
| [Querkandidaten d(t) und d(s)](planning/theory.md#lateral_sampling) | `lateral_sampling` | planning | 2 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Lazy-Auswahl](planning/theory.md#lazy_selection) | `lazy_selection` | planning | 2 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Lineares Einspurmodell](vehicle_models/theory.md#linear_bicycle) | `linear_bicycle` | vehicle_models | 4 | [Borrelli et al. (2017)](references.md#borrelli2017), [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Rajamani (2012)](references.md#rajamani2012), [Stark und Parker (1995)](references.md#stark1995) | ja |
| [Lineare Stabilitäts- und Frequenzganganalyse](analysis/theory.md#linear_stability_analysis) | `linear_stability_analysis` | analysis | 3 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Rajamani (2012)](references.md#rajamani2012) | ja |
| [Lineares Reifenmodell mit Reibkreis](tire_models/theory.md#linear_tire) | `linear_tire` | tire_models | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Pacejka (2012)](references.md#pacejka2012) | ja |
| [Einrasten auf der Referenz](planning/theory.md#lock_in) | `lock_in` | planning | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Längskandidaten](planning/theory.md#longitudinal_sampling) | `longitudinal_sampling` | planning | 2 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Lqr lateral](README.md#konzepte-ohne-dokumentation) | `lqr_lateral` | – | 3 | [Rajamani (2012)](references.md#rajamani2012) | nein |
| [Lyapunov-Tracking ohne Orientierungsstabilisierung](stabilization/theory.md#lyapunov_center) | `lyapunov_center` | stabilization | 3 | [Isidori (1995)](references.md#isidori1995), [Khalil (2002)](references.md#khalil2002), [Werling (2011)](references.md#werling2011) | ja |
| [Lyapunov-Tracking mit Orientierungsstabilisierung](stabilization/theory.md#lyapunov_orientation) | `lyapunov_orientation` | stabilization | 4 | [Khalil (2002)](references.md#khalil2002), [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011) | ja |
| [Pacejka Magic Formula](tire_models/theory.md#magic_formula) | `magic_formula` | tire_models | 3 | [Pacejka (2012)](references.md#pacejka2012), [Schramm et al. (2018)](references.md#schramm2018) | ja |
| [Matlab analysis](README.md#konzepte-ohne-dokumentation) | `matlab_analysis` | – | 1 | [Aho et al. (2006)](references.md#aho2006) | nein |
| [Matlab codegen](README.md#konzepte-ohne-dokumentation) | `matlab_codegen` | – | 1 | [Aho et al. (2006)](references.md#aho2006) | nein |
| [Matlab codegen verification](README.md#konzepte-ohne-dokumentation) | `matlab_codegen_verification` | – | 1 | [MathWorks und Inc. (2024)](references.md#mathworks_matlab) | nein |
| [Matlab control structure](README.md#konzepte-ohne-dokumentation) | `matlab_control_structure` | – | 1 | [Werling (2011)](references.md#werling2011) | nein |
| [Matlab import](README.md#konzepte-ohne-dokumentation) | `matlab_import` | – | 0 | – | nein |
| [Matlab interpreter](README.md#konzepte-ohne-dokumentation) | `matlab_interpreter` | – | 1 | [MathWorks und Inc. (2024)](references.md#mathworks_matlab) | nein |
| [Matlab parser](README.md#konzepte-ohne-dokumentation) | `matlab_parser` | – | 1 | [Aho et al. (2006)](references.md#aho2006) | nein |
| [Matlab type inference](README.md#konzepte-ohne-dokumentation) | `matlab_type_inference` | – | 1 | [Aho et al. (2006)](references.md#aho2006) | nein |
| [Einfädeln](planning/theory.md#merging_mode) | `merging_mode` | planning | 3 | [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [stvo (fehlt in docs/references)](references.md#stvo), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | ja |
| [Mobil](README.md#konzepte-ohne-dokumentation) | `mobil` | – | 4 | [asam_openscenario (fehlt in docs/references)](references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [stvo (fehlt in docs/references)](references.md#stvo), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | nein |
| [Monte-Carlo-Simulation und Sensitivität](research/theory.md#monte_carlo) | `monte_carlo` | research | 1 | [Saltelli et al. (2008)](references.md#saltelli2008) | ja |
| [Bewegungsprädiktion für die Reinitialisierung](planning/theory.md#motion_prediction) | `motion_prediction` | planning | 3 | [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011) | ja |
| [Mpc lateral](README.md#konzepte-ohne-dokumentation) | `mpc_lateral` | – | 2 | [Borrelli et al. (2017)](references.md#borrelli2017), [Rajamani (2012)](references.md#rajamani2012), [Werling (2011)](references.md#werling2011) | nein |
| [Mehrzielige Kostenfunktion](planning/theory.md#multi_objective_cost) | `multi_objective_cost` | planning | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Mehrkörpermodell mit Vertikaldynamik](vehicle_models/theory.md#multibody) | `multibody` | vehicle_models | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Schramm et al. (2018)](references.md#schramm2018) | ja |
| [Multi-Rate und Halteglied](runtime/theory.md#multirate_zoh) | `multirate_zoh` | runtime | 0 | [Lee und Seshia (2017)](references.md#lee_seshia2017), [MathWorks (2024)](references.md#simulink_exec) | ja |
| [Nichtlineares Einspurmodell](vehicle_models/theory.md#nonlinear_bicycle) | `nonlinear_bicycle` | vehicle_models | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Pacejka (2012)](references.md#pacejka2012) | ja |
| [Parameterschema und klassische Registry](core/theory.md#parameter_schema) | `parameter_schema` | core | 2 | [Martin (2017)](references.md#martin2017) | ja |
| [Pfadkonstruktion aus Krümmungssegmenten](trajectory/theory.md#path_construction) | `path_construction` | trajectory | 9 | [ISO 3888-1:2018 (2018)](references.md#iso3888_1), [ISO 3888-2:2011 (2011)](references.md#iso3888_2), [ISO 4138:2021 (2021)](references.md#iso4138), [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [Modellprädiktive Bahnregelung (lineare MPC)](controllers/theory.md#path_mpc) | `path_mpc` | controllers | 3 | [Borrelli et al. (2017)](references.md#borrelli2017), [Rajamani (2012)](references.md#rajamani2012), [Stark und Parker (1995)](references.md#stark1995) | ja |
| [Pid](README.md#konzepte-ohne-dokumentation) | `pid` | – | 3 | [Åström und Hägglund (2006)](references.md#astrom2006) | nein |
| [Versionierte Plugin-Registry](framework/theory.md#plugin_registry) | `plugin_registry` | framework | 2 | [Preston-Werner](references.md#semver2) | ja |
| [Projektion auf die Polylinie](trajectory/theory.md#polyline_projection) | `polyline_projection` | trajectory | 1 | [de Boor (2001)](references.md#deboor2001) | ja |
| [Pure Pursuit](controllers/theory.md#pure_pursuit) | `pure_pursuit` | controllers | 5 | [Coulter (1992)](references.md#coulter1992), [Rajamani (2012)](references.md#rajamani2012), [Snider (2009)](references.md#snider2009) | ja |
| [Quartische Optimalpolynome](planning/theory.md#quartic_polynomial) | `quartic_polynomial` | planning | 2 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Quasi-statische Radlasten und Wankgradient](analysis/theory.md#quasi_static_wheel_loads) | `quasi_static_wheel_loads` | analysis | 2 | [Milliken und Milliken (1995)](references.md#milliken1995), [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [Quintische Optimalpolynome](planning/theory.md#quintic_polynomial) | `quintic_polynomial` | planning | 2 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Ideallinie mit minimaler Krümmung](trajectory/theory.md#racing_line) | `racing_line` | trajectory | 2 | [Braghin et al. (2008)](references.md#braghin2008), [Kapania et al. (2016)](references.md#kapania2016) | ja |
| [Hinterachslenkung](controllers/theory.md#rear_axle_steering) | `rear_axle_steering` | controllers | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014) | ja |
| [Abstand orientierter Rechtecke](research/theory.md#rectangle_distance) | `rectangle_distance` | research | 1 | [Ericson (2004)](references.md#ericson2004) | ja |
| [Referenzpunkt und Geschwindigkeitsregime](planning/theory.md#reference_point) | `reference_point` | planning | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Rekuperation und Bremsmischung](powertrain/theory.md#regenerative_braking) | `regenerative_braking` | powertrain | 1 | [Reif (2010)](references.md#reif2010) | ja |
| [Reinitialisierung und Bewegungsprädiktion](stabilization/theory.md#reinitialization_trigger) | `reinitialization_trigger` | stabilization | 2 | [Werling et al. (2010)](references.md#werling2010tro), [Werling (2011)](references.md#werling2011) | ja |
| [Ablösestrategie](planning/theory.md#replacement_strategy) | `replacement_strategy` | planning | 2 | [Werling et al. (2010)](references.md#werling2010icra), [Werling (2011)](references.md#werling2011), [Werling et al. (2012)](references.md#werling2012ijrr), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4)](simulation/theory.md#runge_kutta) | `runge_kutta` | simulation | 4 | [Butcher (2016)](references.md#butcher2016), [Hairer et al. (1993)](references.md#hairer1993), [Virtanen et al. (2020)](references.md#virtanen2020) | ja |
| [Rampe des Sicherheitsabstands](planning/theory.md#safety_margin_ramp) | `safety_margin_ramp` | planning | 2 | [Werling (2011)](references.md#werling2011), [Ziegler und Stiller (2010)](references.md#ziegler2010iv) | ja |
| [Abschätzung des Sampling-Horizonts](planning/theory.md#sampling_horizon) | `sampling_horizon` | planning | 1 | [Werling (2011)](references.md#werling2011) | ja |
| [Sat collision](README.md#konzepte-ohne-dokumentation) | `sat_collision` | – | 2 | [asam_openscenario (fehlt in docs/references)](references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | nein |
| [Scenario engine](README.md#konzepte-ohne-dokumentation) | `scenario_engine` | – | 1 | [asam_openscenario (fehlt in docs/references)](references.md#asam_openscenario), [gottschalk1996 (fehlt in docs/references)](references.md#gottschalk1996), [kesting2007 (fehlt in docs/references)](references.md#kesting2007), [treiber2000 (fehlt in docs/references)](references.md#treiber2000), [Werling (2011)](references.md#werling2011) | nein |
| [Sensor model](README.md#konzepte-ohne-dokumentation) | `sensor_model` | – | 3 | [bar_shalom2001 (fehlt in docs/references)](references.md#bar_shalom2001), [vdsim (fehlt in docs/references)](references.md#vdsim) | nein |
| [Signaltypen und Codecs](framework/theory.md#signal_type_system) | `signal_type_system` | framework | 2 | [Martin (2017)](references.md#martin2017) | ja |
| [Ablauf eines Simulationsschritts](simulation/theory.md#simulation_loop) | `simulation_loop` | simulation | 1 | [Hairer et al. (1993)](references.md#hairer1993) | ja |
| [Glatte Krümmungsübergänge](geometry/theory.md#smooth_curvature_profile) | `smooth_curvature_profile` | geometry | 2 | [Werling (2011)](references.md#werling2011) | ja |
| [Geschwindigkeitsregelung (PI mit Vorsteuerung)](controllers/theory.md#speed_control) | `speed_control` | controllers | 2 | [Rajamani (2012)](references.md#rajamani2012) | ja |
| [Split-Range-Längskraftumsetzung](stabilization/theory.md#split_range) | `split_range` | stabilization | 2 | [Åström und Hägglund (2006)](references.md#astrom2006), [Werling (2011)](references.md#werling2011) | ja |
| [Stabilitätsbegrenzte Teilschritte (stable_dt)](simulation/theory.md#stable_substeps) | `stable_substeps` | simulation | 3 | [Hairer et al. (1993)](references.md#hairer1993), [Hairer und Wanner (1996)](references.md#hairer1996) | ja |
| [Stanley](README.md#konzepte-ohne-dokumentation) | `stanley` | – | 2 | [Hoffmann et al. (2007)](references.md#hoffmann2007), [Snider (2009)](references.md#snider2009) | nein |
| [Stanley-Bahnregler](controllers/theory.md#stanley_controller) | `stanley_controller` | controllers | 2 | [Hoffmann et al. (2007)](references.md#hoffmann2007), [Snider (2009)](references.md#snider2009), [Thrun et al. (2006)](references.md#thrun2006) | ja |
| [Steering actuator](README.md#konzepte-ohne-dokumentation) | `steering_actuator` | – | 1 | [Werling (2011)](references.md#werling2011) | nein |
| [Wirkkette des Lenkaktors](actuators/theory.md#steering_actuator_chain) | `steering_actuator_chain` | actuators | 1 | [Ljung (1999)](references.md#ljung1999), [comma.ai](references.md#openpilot) | ja |
| [Kennlinienfehler des Lenkaktors](actuators/theory.md#steering_characteristic_error) | `steering_characteristic_error` | actuators | 2 | [Ljung (1999)](references.md#ljung1999) | ja |
| [Surrogate Safety Measures](research/theory.md#surrogate_safety_measures) | `surrogate_safety_measures` | research | 1 | [Allen et al. (1978)](references.md#allen1978), [Hayward (1972)](references.md#hayward1972), [Vogel (2003)](references.md#vogel2003) | ja |
| [Ausführungsmodell und Zeitdiskretisierung](runtime/theory.md#synchronous_dataflow) | `synchronous_dataflow` | runtime | 0 | [Edwards und Lee (2003)](references.md#edwards_lee2003), [Lee und Seshia (2017)](references.md#lee_seshia2017), [MathWorks (2024)](references.md#simulink_exec) | ja |
| [Torque Vectoring](controllers/theory.md#torque_vectoring) | `torque_vectoring` | controllers | 2 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Rajamani (2012)](references.md#rajamani2012) | ja |
| [Rückverfolgbarkeitsmodell](knowledge/theory.md#traceability_model) | `traceability_model` | knowledge | 3 | [Gotel und Finkelstein (1994)](references.md#gotel1994), [ISO 26262:2018 (2018)](references.md#iso26262) | ja |
| [Import von GPS- und OpenDRIVE-Daten](trajectory/theory.md#trajectory_import) | `trajectory_import` | trajectory | 5 | [ASAM OpenDRIVE](references.md#asam_opendrive) | ja |
| [Eigenlenkgradient und charakteristische Geschwindigkeit](analysis/theory.md#understeer_gradient) | `understeer_gradient` | analysis | 5 | [ISO 4138:2021 (2021)](references.md#iso4138), [Milliken und Milliken (1995)](references.md#milliken1995), [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Rajamani (2012)](references.md#rajamani2012), [Reif (2010)](references.md#reif2010), [van Zanten et al. (1995)](references.md#vanzanten1995) | ja |
| [Vehicle plant](README.md#konzepte-ohne-dokumentation) | `vehicle_plant` | – | 1 | [Werling (2011)](references.md#werling2011) | nein |
| [Schlupfregelung ABS und ASR](controllers/theory.md#wheel_slip_control) | `wheel_slip_control` | controllers | 4 | [Mitschke und Wallentowitz (2014)](references.md#mitschke2014), [Reif (2010)](references.md#reif2010) | ja |
| [Zero dynamics desm](README.md#konzepte-ohne-dokumentation) | `zero_dynamics_desm` | – | 3 | [Isidori (1995)](references.md#isidori1995), [Khalil (2002)](references.md#khalil2002), [Pacejka (2012)](references.md#pacejka2012), [Werling (2011)](references.md#werling2011) | nein |
| [Zero dynamics kesm](README.md#konzepte-ohne-dokumentation) | `zero_dynamics_kesm` | – | 1 | [Isidori (1995)](references.md#isidori1995), [Khalil (2002)](references.md#khalil2002), [Werling (2011)](references.md#werling2011) | nein |

### Konzepte ohne Dokumentation {#konzepte-ohne-dokumentation}

`acc`, `anti_windup`, `backstepping`, `behavior_state_machine`, `box_restriction`, `ca_prediction`, `composite`, `continuous_curvature_road`, `cv_prediction`, `desm`, `dynamic_reference_transform`, `feedforward`, `flat_reference_transform`, `frenet_frame`, `hazard_indicator`, `idm`, `invariant_tracking_error`, `lane_following_prediction`, `lateral_intent`, `lqr_lateral`, `matlab_analysis`, `matlab_codegen`, `matlab_codegen_verification`, `matlab_control_structure`, `matlab_import`, `matlab_interpreter`, `matlab_parser`, `matlab_type_inference`, `mobil`, `mpc_lateral`, `pid`, `sat_collision`, `scenario_engine`, `sensor_model`, `stanley`, `steering_actuator`, `vehicle_plant`, `zero_dynamics_desm`, `zero_dynamics_kesm`

## Wissensgraph

3201 Knoten, 6003 Kanten.

| Knotentyp | Anzahl |
|---|---|
| Klasse | 497 |
| Komponente | 110 |
| Verfahren/Konzept | 147 |
| Konfiguration | 52 |
| Datentyp | 24 |
| Dokument | 189 |
| Beispiel | 31 |
| Funktion | 1769 |
| Modell | 12 |
| Modul | 217 |
| Paket | 27 |
| Quelle | 78 |
| Test | 48 |

| Kantentyp | Anzahl |
|---|---|
| zitiert | 570 |
| konfiguriert durch | 128 |
| konsumiert | 137 |
| enthält | 2732 |
| dokumentiert durch | 297 |
| Beispiel für | 129 |
| implementiert | 446 |
| importiert | 672 |
| erzeugt | 117 |
| verwandt mit | 151 |
| Unterklasse von | 191 |
| getestet durch | 433 |

## Weitere Seiten

- [Rückverfolgbarkeitsmatrix](traceability_matrix.md)
- [Literaturverzeichnis](references.md) und [BibTeX](references.bib)
- [Prüfbericht (Referenzen, Hinweise des Sammlers)](report.md)
- [Wissensgraph (HTML)](knowledge_graph.html), [JSON](knowledge_graph.json)
