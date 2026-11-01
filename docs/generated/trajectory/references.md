# Trajektorien – Manöver, Import, Editor, Geschwindigkeitsprofile – Quellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · **Quellen** · [Rückverfolgbarkeit](traceability.md)


| Zitat | Quelle | Typ | Verwendet in |
|---|---|---|---|
| [ASAM OpenDRIVE](../references.md#asam_opendrive) | ASAM e.V.: ASAM OpenDRIVE – Format zur Beschreibung von Straßennetzen. https://www.asam.net/standards/detail/opendrive/. | Industriestandard | load_opendrive (module.yaml), module.yaml, theory.md, trajectory_loader/opendrive |
| [Braghin et al. (2008)](../references.md#braghin2008) | Braghin, F.; Cheli, F.; Melzi, S.; Sabbioni, E. (2008): Race driver model. In: Computers & Structures 86(13-14). | Fachartikel | maneuver/race_track, module.yaml, racing_line (module.yaml), theory.md |
| [de Boor (2001)](../references.md#deboor2001) | de Boor, C. (2001): A Practical Guide to Splines. revised edition. Springer (Applied Mathematical Sciences 27). | Fachbuch | theory.md |
| [FMVSS No. 126 (49 CFR 571.126) (2007)](../references.md#fmvss126) | National Highway Traffic Safety Administration (NHTSA) (2007): FMVSS No. 126 (49 CFR 571.126): Electronic Stability Control Systems for Light Vehicles. | Industriestandard | maneuver/sine_with_dwell, module.yaml |
| [ISO 3888-1:2018 (2018)](../references.md#iso3888_1) | International Organization for Standardization (2018): ISO 3888-1:2018: Passenger cars — Test track for a severe lane-change manoeuvre — Part 1 Double lane-change. | Norm | maneuver/iso_double_lane_change, module.yaml |
| [ISO 3888-2:2011 (2011)](../references.md#iso3888_2) | International Organization for Standardization (2011): ISO 3888-2:2011: Passenger cars — Test track for a severe lane-change manoeuvre — Part 2 Obstacle avoidance. | Norm | maneuver/iso_obstacle_avoidance, module.yaml |
| [ISO 4138:2021 (2021)](../references.md#iso4138) | International Organization for Standardization (2021): ISO 4138:2021: Passenger cars — Steady-state circular driving behaviour — Open-loop test methods. | Norm | maneuver/circle, maneuver/ramp_steer, module.yaml |
| [ISO 7401:2011 (2011)](../references.md#iso7401) | International Organization for Standardization (2011): ISO 7401:2011: Road vehicles — Lateral transient response test methods — Open-loop test methods. | Norm | maneuver/frequency_sweep, maneuver/step_steer, module.yaml |
| [ISO 7975:2019 (2019)](../references.md#iso7975) | International Organization for Standardization (2019): ISO 7975:2019: Passenger cars — Braking in a turn — Open-loop test method. | Norm | maneuver/brake_in_turn, module.yaml |
| [Kapania et al. (2016)](../references.md#kapania2016) | Kapania, N. R.; Subosits, J.; Gerdes, J. C. (2016): A Sequential Two-Step Algorithm for Fast Generation of Vehicle Racing Trajectories. In: Journal of Dynamic Systems, Measurement, and Control 138(9). | Fachartikel | maneuver/race_track, module.yaml, speed_profile (module.yaml), theory.md |
| [Milliken und Milliken (1995)](../references.md#milliken1995) | Milliken, W. F.; Milliken, D. L. (1995): Race Car Vehicle Dynamics. SAE International. | Fachbuch | module.yaml, theory.md |
| [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | Mitschke, M.; Wallentowitz, H. (2014): Dynamik der Kraftfahrzeuge. 5. Auflage. Springer Vieweg. | Fachbuch | theory.md |
