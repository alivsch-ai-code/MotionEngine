# Fahrzeuganalyse – linear und quasi-statisch – Quellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · **Quellen** · [Rückverfolgbarkeit](traceability.md)


| Zitat | Quelle | Typ | Verwendet in |
|---|---|---|---|
| [ISO 4138:2021 (2021)](../references.md#iso4138) | International Organization for Standardization (2021): ISO 4138:2021: Passenger cars — Steady-state circular driving behaviour — Open-loop test methods. | Norm | module.yaml, theory.md |
| [Milliken und Milliken (1995)](../references.md#milliken1995) | Milliken, W. F.; Milliken, D. L. (1995): Race Car Vehicle Dynamics. SAE International. | Fachbuch | QuasiStaticAnalysis.roll_gradient (module.yaml), QuasiStaticAnalysis.wheel_loads (module.yaml), module.yaml, theory.md |
| [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | Mitschke, M.; Wallentowitz, H. (2014): Dynamik der Kraftfahrzeuge. 5. Auflage. Springer Vieweg. | Fachbuch | LinearSingleTrackAnalysis.characteristic_speed (module.yaml), LinearSingleTrackAnalysis.critical_speed (module.yaml), LinearSingleTrackAnalysis.steady_state_gains (module.yaml), QuasiStaticAnalysis.ackermann_angles (module.yaml), module.yaml, theory.md |
| [Rajamani (2012)](../references.md#rajamani2012) | Rajamani, R. (2012): Vehicle Dynamics and Control. Springer, 2. Auflage. DOI 10.1007/978-1-4614-1433-9. | Fachbuch | LinearSingleTrackAnalysis.eigen (module.yaml), module.yaml, theory.md |
